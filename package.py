"""Sklada archiwum do wydania z gotowego .exe.

Jedyne miejsce, gdzie powstaje paczka. Uzywaja go dwa procesy - budowanie
strony (web/build.py) i wydanie w CI - wiec plik ze strony i plik z wydania
na GitHubie sa identyczne co do bajtu. Gdyby kazdy sklejal archiwum po swojemu,
predzej czy pozniej roznilyby sie zawartoscia.

Uruchomienie:  python package.py
Wynik:         dist/poe-price-check-<wersja>.zip
"""

import hashlib
import pathlib
import sys
import zipfile

from paths import APP_VERSION

HERE = pathlib.Path(__file__).resolve().parent
SITE_URL = "https://poepricecheck.eu"

ARCHIVE_NAME = f"poe-price-check-{APP_VERSION}.zip"
EXE_NAME = "poe-price-check.exe"

# Cloudflare Pages nie przyjmuje pojedynczych plikow wiekszych niz tyle.
MAX_MB = 25


def readme(checksum: str) -> str:
    """Instrukcja w archiwum.

    Wlasciwa przeszkoda nie jest pobranie, tylko okno SmartScreena przy
    pierwszym uruchomieniu - ludzie w tym miejscu rezygnuja, bo nie wiedza,
    ze przycisk "Wiecej informacji" w ogole tam jest. Po angielsku i polsku,
    bo to dwie najwieksze grupy; reszte prowadzi kreator w aplikacji.
    """
    return "\r\n".join([
        f"PoE Price Check {APP_VERSION}",
        SITE_URL,
        "",
        "=" * 66,
        "PIERWSZE URUCHOMIENIE / FIRST RUN",
        "=" * 66,
        "",
        "[PL] Windows pokaze okno 'System Windows ochronil Twoj komputer'.",
        "     To normalne: program nie ma podpisu cyfrowego, bo certyfikat",
        "     kosztuje kilkaset euro rocznie, a aplikacja jest darmowa.",
        "",
        "     Zeby uruchomic:  Wiecej informacji  ->  Uruchom mimo to",
        "",
        "[EN] Windows will show 'Windows protected your PC'. That is expected:",
        "     the program is not code-signed, because a certificate costs",
        "     hundreds of euros a year and this tool is free.",
        "",
        "     To run it:  More info  ->  Run anyway",
        "",
        "=" * 66,
        "",
        "Reszte konfiguracji poprowadzi kreator w aplikacji.",
        "The app's setup wizard will guide you through the rest.",
        "",
        f"Kod zrodlowy / source: {SITE_URL}",
        "",
        f"Suma kontrolna / checksum (SHA-256) {EXE_NAME}:",
        checksum,
        "",
        "This product isn't affiliated with or endorsed by "
        "Grinding Gear Games in any way.",
        "",
    ])


def build_archive(exe: pathlib.Path, out_dir: pathlib.Path) -> tuple[pathlib.Path, str]:
    """Pakuje .exe wraz z instrukcja. Zwraca (sciezka do archiwum, suma exe)."""
    if not exe.exists():
        raise SystemExit(
            f"Nie znalazlem {exe}.\n"
            f"Zbuduj go najpierw:  python -m PyInstaller --noconfirm "
            f"poe-price-check.spec")

    checksum = hashlib.sha256(exe.read_bytes()).hexdigest()
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / ARCHIVE_NAME

    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(exe, EXE_NAME)
        bundle.writestr("CZYTAJ-TO.txt", readme(checksum))

    size_mb = archive.stat().st_size / 1048576
    if size_mb > MAX_MB:
        raise SystemExit(
            f"Archiwum ma {size_mb:.1f} MB, a Cloudflare Pages przyjmuje "
            f"najwyzej {MAX_MB} MB. Potrzebny bedzie osobny hosting.")

    return archive, checksum


def main() -> None:
    exe = HERE / "dist" / EXE_NAME
    archive, checksum = build_archive(exe, HERE / "dist")
    size_mb = archive.stat().st_size / 1048576

    print(f"archiwum : {archive.name} ({size_mb:.1f} MB)")
    print(f"sha256   : {checksum}")

    # CI potrzebuje tych wartosci w kolejnych krokach.
    summary = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if summary:
        summary.write_text(f"archive={archive}\nsha256={checksum}\n",
                           encoding="utf-8")


if __name__ == "__main__":
    main()
