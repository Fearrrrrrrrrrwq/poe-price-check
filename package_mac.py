"""Sklada archiwum wydania z gotowego 'PoE Price Check.app' (macOS).

Siostrzany skrypt package.py (Windows), ale prostszy - nie ma tu strony
www.poepricecheck.eu (przycisk macOS kieruje do README na GitHubie, nie do
pliku), wiec nie obowiazuje limit 25 MB Cloudflare Pages. Jedyny odbiorca
tego archiwum to GitHub Releases.

.app to FOLDER, nie plik - zwykly zipfile.ZipFile psuje czasem uprawnienia
wykonywalnosci i resource forki. `ditto` to natywne narzedzie macOS zrobione
dokladnie do tego (uzywane m.in. przez sam Finder przy "Compress"), wiec
zamiast reczne stitchowanie zipa, wolimy podprocesem wywolac ditto - jest
tylko na macOS, ale ten skrypt i tak ma sens wylacznie tam.

Uruchomienie:  python package_mac.py
Wynik:         dist/poe-price-check-<wersja>-macos.zip
"""

import hashlib
import pathlib
import subprocess
import sys

from paths import APP_VERSION

HERE = pathlib.Path(__file__).resolve().parent
SITE_URL = "https://poepricecheck.eu"

APP_NAME = "PoE Price Check.app"
ARCHIVE_NAME = f"poe-price-check-{APP_VERSION}-macos.zip"


def build_archive(app: pathlib.Path, out_dir: pathlib.Path) -> tuple[pathlib.Path, str]:
    """Pakuje .app przez ditto. Zwraca (sciezka do archiwum, suma SHA-256 archiwum).

    Suma liczona jest z ARCHIWUM, nie z pojedynczego pliku wewnatrz - .app to
    drzewo wielu plikow, wiec nie ma tu jednego binarium do zsumowania tak
    jak przy .exe.
    """
    if not app.exists():
        raise SystemExit(
            f"Nie znalazlem {app}.\n"
            f"Zbuduj go najpierw:  python -m PyInstaller --noconfirm "
            f"poe-price-check-mac.spec")

    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / ARCHIVE_NAME
    if archive.exists():
        archive.unlink()

    result = subprocess.run(
        ["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent",
         str(app), str(archive)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"ditto sie nie powiodlo:\n{result.stderr}")

    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    return archive, checksum


def release_notes(version: str, checksum: str) -> str:
    return "\n".join([
        f"Pobierz **{ARCHIVE_NAME}**, rozpakuj i przenies "
        f"**{APP_NAME}** do Aplikacji.",
        "",
        "macOS pokaze ostrzezenie Gatekeepera, bo aplikacja nie jest podpisana",
        "ani notaryzowana (brak konta deweloperskiego Apple - 99 USD/rok):",
        "**kliknij prawym na aplikacje -> Otworz -> Otworz** (zamiast zwyklego",
        "podwojnego kliknięcia, ktore samo pokaze tylko przycisk Anuluj).",
        "",
        "Wsparcie macOS jest EKSPERYMENTALNE - patrz sekcja 'macOS "
        "(experimental)' w README.",
        "",
        f"Suma kontrolna archiwum (SHA-256):",
        "",
        "```",
        checksum,
        "```",
        "",
        f"Zbudowane automatycznie z tagu {version} przez GitHub Actions "
        f"(macos-latest runner).",
        "",
    ])


def main() -> None:
    app = HERE / "dist" / APP_NAME
    archive, checksum = build_archive(app, HERE / "dist")
    size_mb = archive.stat().st_size / 1048576

    print(f"archiwum : {archive.name} ({size_mb:.1f} MB)")
    print(f"sha256   : {checksum}")

    notes = HERE / "dist" / "RELEASE-NOTES-MAC.md"
    notes.write_text(release_notes(f"v{APP_VERSION}", checksum), encoding="utf-8")
    print(f"opis     : {notes.name}")

    if len(sys.argv) > 1:
        pathlib.Path(sys.argv[1]).write_text(
            f"archive={archive}\nsha256={checksum}\nnotes={notes}\n",
            encoding="utf-8")


if __name__ == "__main__":
    main()
