"""Wdrozenie na Cloudflare Pages jednym poleceniem.

Wykonuje wszystko poza tym, czego zrobic za Ciebie nie mozna: logowaniem do
Twojego konta Cloudflare i wyborem hasla administratora.

    npx wrangler login                        <- to musisz zrobic sam, raz
    python deploy.py --domain poe.example.pl

Skrypt jest idempotentny - mozna go uruchamiac wielokrotnie. Istniejacej bazy
ani projektu nie zaklada drugi raz, a identyfikator bazy sam wpisuje do
wrangler.toml (w oba miejsca, bo latwo zapomniec o sekcji podgladu).
"""

import argparse
import json
import os
import pathlib
import re
import secrets
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
CONFIG = HERE / "wrangler.toml"
TOKEN_FILE = HERE / ".setup-token"
SALT_MARK = HERE / ".salt-set"

DB_NAME = "poe-price-check"
PROJECT = "poe-price-check"
BRANCH = "main"

NPX = shutil.which("npx") or shutil.which("npx.cmd")

# Wrangler wypisuje emoji, a polska konsola Windows stoi na cp1250 i wywraca
# sie na pierwszym znaku spoza tablicy. Przestawiamy wyjscie na UTF-8
# z podmiana zamiast bledu.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def say(step: str, text: str) -> None:
    print(f"\n[{step}] {text}", flush=True)


def run(*args: str, capture: bool = False, stdin: str | None = None) -> str:
    """Wolanie wranglera. Bez capture wynik leci na ekran na zywo."""
    if not NPX:
        sys.exit("Nie znalazlem npx. Zainstaluj Node.js.")
    command = [NPX, "wrangler", *args]
    result = subprocess.run(
        command,
        input=stdin,
        capture_output=capture,
        text=True,
        cwd=HERE,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        if capture:
            print(result.stdout or "", file=sys.stderr)
            print(result.stderr or "", file=sys.stderr)
        sys.exit(f"Polecenie 'wrangler {' '.join(args)}' zwrocilo blad.")
    return (result.stdout or "").strip()


def parse_json(text: str):
    """Wrangler lubi dopisac ozdobniki przed JSON-em - bierzemy sam nawias."""
    start = min((text.find(c) for c in "[{" if text.find(c) != -1), default=-1)
    if start == -1:
        return None
    try:
        return json.loads(text[start:])
    except json.JSONDecodeError:
        return None


# --------------------------------------------------------------------- kroki

def check_login() -> None:
    say("1/8", "sprawdzam logowanie do Cloudflare")
    result = subprocess.run(
        [NPX, "wrangler", "whoami"], capture_output=True, text=True, cwd=HERE,
        encoding="utf-8", errors="replace")
    if "not authenticated" in (result.stdout + result.stderr).lower():
        sys.exit(
            "\nNie jestes zalogowany do Cloudflare.\n"
            "Uruchom raz:  npx wrangler login\n"
            "Otworzy przegladarke - potwierdz dostep i wroc tutaj.")
    for line in result.stdout.splitlines():
        if "@" in line or "Account Name" in line:
            print("  " + line.strip(" │|"))


def ensure_database() -> str:
    say("2/8", f"baza D1 '{DB_NAME}'")
    existing = parse_json(run("d1", "list", "--json", capture=True)) or []
    for row in existing:
        if row.get("name") == DB_NAME:
            print(f"  juz istnieje: {row['uuid']}")
            return row["uuid"]

    print("  zakladam nowa")
    run("d1", "create", DB_NAME, capture=True)

    refreshed = parse_json(run("d1", "list", "--json", capture=True)) or []
    for row in refreshed:
        if row.get("name") == DB_NAME:
            print(f"  utworzona: {row['uuid']}")
            return row["uuid"]
    sys.exit("Baza powstala, ale nie potrafie odczytac jej identyfikatora.")


def patch_config(database_id: str) -> None:
    say("3/8", "wpisuje identyfikator bazy do wrangler.toml")
    # Plik z prawdziwym identyfikatorem nie jest wersjonowany - kazdy ma
    # wlasna baze. Po sklonowaniu repozytorium tworzymy go z wzorca.
    if not CONFIG.exists():
        shutil.copy(HERE / "wrangler.toml.example", CONFIG)
        print("  utworzony z wrangler.toml.example")
    source = CONFIG.read_text(encoding="utf-8")
    patched, count = re.subn(
        r'database_id\s*=\s*"[^"]*"',
        f'database_id = "{database_id}"',
        source,
    )
    # Dwa wystapienia: produkcja i podglad. Jesli jest ich mniej, ktos ruszyl
    # konfiguracje i lepiej stanac, niz po cichu wdrozyc polowe.
    if count != 2:
        sys.exit(f"Spodziewalem sie dwoch wpisow database_id, znalazlem {count}.")
    if patched != source:
        CONFIG.write_text(patched, encoding="utf-8")
        print("  zaktualizowane (produkcja + podglad)")
    else:
        print("  juz aktualne")


def apply_schema() -> None:
    say("4/8", "zakladam tabele w zdalnej bazie")
    # CREATE TABLE IF NOT EXISTS - powtorne uruchomienie niczego nie kasuje.
    run("d1", "execute", DB_NAME, "--remote", "--yes", "--file=schema.sql",
        capture=True)
    print("  gotowe")


def ensure_project() -> None:
    say("5/8", f"projekt Pages '{PROJECT}'")
    listing = parse_json(run("pages", "project", "list", "--json", capture=True)) or []
    # wrangler w --json oddaje naglowki kolumn tabeli ("Project Name"), a nie
    # pola API ("name"). Sprawdzamy oba - inaczej krok "juz istnieje" nigdy sie
    # nie wykona i powtorne wdrozenie wywala sie na tworzeniu projektu.
    if any(row.get("name") == PROJECT or row.get("Project Name") == PROJECT
           for row in listing):
        print("  juz istnieje")
        return
    run("pages", "project", "create", PROJECT,
        f"--production-branch={BRANCH}", capture=True)
    print("  utworzony")


def ensure_secret() -> str | None:
    say("6/8", "sekrety projektu")

    # Sol do skrotow odwiedzin. Bez niej dalo by sie odtworzyc adres IP
    # zgadywaniem - przestrzen adresow IPv4 jest na to za mala.
    if not SALT_MARK.exists():
        run("pages", "secret", "put", "ANALYTICS_SALT", f"--project-name={PROJECT}",
            stdin=secrets.token_urlsafe(32) + "\n", capture=True)
        SALT_MARK.write_text("ustawiona", encoding="utf-8")
        print("  ANALYTICS_SALT: ustawiona")
    else:
        print("  ANALYTICS_SALT: juz ustawiona")

    if TOKEN_FILE.exists():
        print("  SETUP_TOKEN: juz ustawiony - zostawiam bez zmian")
        return None

    token = secrets.token_urlsafe(32)
    run("pages", "secret", "put", "SETUP_TOKEN", f"--project-name={PROJECT}",
        stdin=token + "\n", capture=True)

    TOKEN_FILE.write_text(token, encoding="utf-8")
    print(f"  SETUP_TOKEN: ustawiony, zapisany w {TOKEN_FILE.name} (jest w .gitignore)")
    return token


def build(site_url: str) -> None:
    say("7/8", f"buduje strone dla {site_url}")
    environment = {**os.environ, "SITE_URL": site_url}
    result = subprocess.run([sys.executable, "build.py"], cwd=HERE, env=environment,
                            capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode != 0:
        print(result.stdout, result.stderr, file=sys.stderr)
        sys.exit("Budowanie sie nie powiodlo.")
    print("  " + result.stdout.strip().splitlines()[0])

    check = subprocess.run([sys.executable, "check.py"], cwd=HERE,
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    summary = (check.stdout or "").strip().splitlines()[-1:] or ["brak wyniku"]
    print("  kontrola: " + summary[0])
    if check.returncode != 0:
        sys.exit("Kontrola strony zglosila bledy - wstrzymuje wysylke.")


def deploy() -> None:
    say("8/8", "wysylam na Cloudflare")
    run("pages", "deploy", f"--project-name={PROJECT}", f"--branch={BRANCH}")


# --------------------------------------------------------------------- start

def main() -> None:
    parser = argparse.ArgumentParser(description="Wdrozenie na Cloudflare Pages")
    parser.add_argument(
        "--domain",
        help="docelowy adres, np. poe.twojadomena.pl. Bez tego uzyje adresu "
             f"{PROJECT}.pages.dev")
    args = parser.parse_args()

    host = (args.domain or f"{PROJECT}.pages.dev").strip()
    host = re.sub(r"^https?://", "", host).strip("/")
    site_url = f"https://{host}"

    check_login()
    database_id = ensure_database()
    patch_config(database_id)
    apply_schema()
    ensure_project()
    token = ensure_secret()
    build(site_url)
    deploy()

    print("\n" + "=" * 68)
    print("Wdrozone.")
    print("=" * 68)

    if token:
        # Tokenu NIE wypisujemy. Raz juz wyladowal w transkrypcji rozmowy,
        # a endpoint /api/setup jest publiczny - kto go zobaczy, ten moze
        # zalozyc konto administratora przed wlascicielem.
        print("\nZaloz teraz konto administratora:\n")
        print(f"  python setup_admin.py {site_url}")
        print("\nSkrypt czyta token z .setup-token i zapyta o login oraz haslo")
        print("na miejscu - haslo nie pojawi sie na ekranie ani w historii powloki.")

    if args.domain:
        print(f"\nPodepnij domene {host} w panelu Cloudflare:")
        print(f"  Workers & Pages -> {PROJECT} -> Custom domains -> Set up a domain")
        print("Certyfikat wystawi sie sam, zwykle w kilka minut.")
    else:
        print(f"\nStrona stoi pod https://{PROJECT}.pages.dev")
        print("Wlasna domene podepniesz przez:  python deploy.py --domain poe.twoja.pl")

    print(f"\nPanel: {site_url}/admin/")


if __name__ == "__main__":
    main()
