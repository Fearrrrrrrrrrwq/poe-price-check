"""Zaklada konto administratora panelu.

    python setup_admin.py

Token startowy czyta z pliku .setup-token, a login i haslo pyta na miejscu -
haslo nie pojawia sie na ekranie, w historii powloki ani w zadnym logu.
Po zalozeniu konta endpoint /api/setup przestaje cokolwiek robic.
"""

import getpass
import json
import pathlib
import sys
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).parent
TOKEN_FILE = HERE / ".setup-token"
SITE = sys.argv[1] if len(sys.argv) > 1 else "https://poepricecheck.eu"
MIN_PASSWORD = 12

if not TOKEN_FILE.exists():
    sys.exit(f"Brak pliku {TOKEN_FILE.name}. Uruchom najpierw deploy.py.")

token = TOKEN_FILE.read_text(encoding="utf-8").strip()

login = input("Login administratora [admin]: ").strip() or "admin"

password = getpass.getpass(f"Haslo (min. {MIN_PASSWORD} znakow): ")
if len(password) < MIN_PASSWORD:
    sys.exit(f"Za krotkie - potrzeba co najmniej {MIN_PASSWORD} znakow.")
if password != getpass.getpass("Powtorz haslo: "):
    sys.exit("Hasla sie roznia.")

request = urllib.request.Request(
    f"{SITE.rstrip('/')}/api/setup",
    method="POST",
    data=json.dumps({"token": token, "login": login, "password": password}).encode(),
    headers={
        "Content-Type": "application/json",
        # Bez tego leci "Python-urllib/3.x", a ochrona Cloudflare odrzuca taka
        # sygnature z bledem 1010, zanim zapytanie w ogole dojdzie do naszego kodu.
        "User-Agent": "poe-price-check-setup/1.0",
    },
)

try:
    with urllib.request.urlopen(request, timeout=30) as response:
        status, raw = response.status, response.read()
except urllib.error.HTTPError as error:
    status, raw = error.code, error.read()
except urllib.error.URLError as error:
    sys.exit(f"Brak polaczenia z {SITE}: {error.reason}")

try:
    answer = json.loads(raw or b"{}")
except json.JSONDecodeError:
    # Odpowiedz nie od naszego kodu - najczesciej strona bledu Cloudflare.
    # Pokazujemy ja wprost, zamiast wywracac sie na parsowaniu.
    sys.exit(f"Serwer odpowiedzial {status}, ale nie JSON-em:\n"
             f"{raw[:400].decode('utf-8', 'replace').strip()}")

if answer.get("ok"):
    print(f"\nKonto '{answer['login']}' zalozone.")
    print(f"Zaloguj sie: {SITE.rstrip('/')}/admin/")
    print("Token startowy stracil waznosc - mozesz skasowac .setup-token.")
else:
    problems = {
        "already_done": "Konto juz istnieje - tym endpointem nic nie nadpiszesz.",
        "bad_token": "Token sie nie zgadza. Czy po jego zmianie bylo wdrozenie?",
        "setup_disabled": "Brak sekretu SETUP_TOKEN w projekcie Pages.",
        "weak_password": "Haslo za krotkie.",
    }
    sys.exit(problems.get(answer.get("error"), f"Nieoczekiwana odpowiedz: {answer}"))
