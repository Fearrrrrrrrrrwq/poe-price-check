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
import shutil
import subprocess
import sys
import zipfile

from paths import APP_VERSION

HERE = pathlib.Path(__file__).resolve().parent
SITE_URL = "https://poepricecheck.eu"

APP_NAME = "PoE Price Check.app"
ARCHIVE_NAME = f"poe-price-check-{APP_VERSION}-macos.zip"
README_NAME = "CZYTAJ-TO.txt"


def readme() -> str:
    """Instrukcja w archiwum - siostrzana package.readme(), ale macOS ma inna
    przeszkode niz SmartScreen: Gatekeeper (brak podpisu/notaryzacji, konto
    deweloperskie Apple kosztuje 99 USD/rok) i uprawnienie Accessibility, bez
    ktorego globalny skrot i przelaczanie okna z grą nie zadziala w ogole.

    Bez checksumy w srodku - w odroznieniu od Windows nie ma tu jednego pliku
    binarnego do zsumowania (.app to drzewo wielu plikow), a suma calego
    archiwum ZIP nie moze byc zapisana we WLASNYM wnetrzu bez samoodwolania.
    Checksuma archiwum idzie wiec tylko do RELEASE-NOTES-MAC.md, czyli poza
    plik, ktory sam opisuje."""
    return "\r\n".join([
        f"PoE Price Check {APP_VERSION} (macOS - EKSPERYMENTALNE / EXPERIMENTAL)",
        SITE_URL,
        "",
        "=" * 66,
        "PIERWSZE URUCHOMIENIE / FIRST RUN",
        "=" * 66,
        "",
        f"[PL] Przenies '{APP_NAME}' do folderu Aplikacje. Zwykle podwojne",
        "     klikniecie pokaze tylko 'nie mozna otworzyc, bo pochodzi od",
        "     niezidentyfikowanego dewelopera' z samym przyciskiem Anuluj -",
        "     aplikacja nie jest podpisana ani notaryzowana (konto",
        "     deweloperskie Apple kosztuje 99 USD/rok, a program jest darmowy).",
        "",
        "     Zeby uruchomic:  kliknij prawym na aplikacje -> Otworz -> Otworz",
        "     (wystarczy raz - kolejne uruchomienia dzialaja normalnie).",
        "",
        "     Nastepnie system zapyta o uprawnienie DOSTEPNOSC (Accessibility)",
        "     dla programu - to WYMAGANE, bez niego globalny skrot klawiszowy",
        "     i przelaczanie sie z powrotem do gry nie zadziala. Jesli system",
        "     nie zapyta sam: Ustawienia systemowe -> Prywatnosc i ochrona ->",
        "     Dostepnosc -> dodaj recznie.",
        "",
        f"[EN] Move '{APP_NAME}' to Applications. A normal double-click will "
        "just",
        "     show 'cannot be opened because it is from an unidentified",
        "     developer' with only a Cancel button - the app isn't code-signed",
        "     or notarized (an Apple developer account costs $99/year and this",
        "     tool is free).",
        "",
        "     To run it:  right-click the app -> Open -> Open",
        "     (only needed once - later launches work normally).",
        "",
        "     macOS will then ask for ACCESSIBILITY permission for the app -",
        "     this is REQUIRED, without it the global hotkey and switching",
        "     focus back to the game won't work. If it doesn't ask on its",
        "     own: System Settings -> Privacy & Security -> Accessibility ->",
        "     add it manually.",
        "",
        "=" * 66,
        "",
        "Reszte konfiguracji poprowadzi kreator w aplikacji.",
        "The app's setup wizard will guide you through the rest.",
        "",
        "To wsparcie jest eksperymentalne i nieprzetestowane na szeroka skale -",
        "jesli cos nie dziala, zglos na GitHubie albo Discordzie (linki na",
        "stronie). This support is experimental and not widely tested yet -",
        "if something breaks, please report it on GitHub or Discord (links",
        "on the website).",
        "",
        f"Kod zrodlowy / source: {SITE_URL}",
        "",
        f"Suma kontrolna {ARCHIVE_NAME} (SHA-256) jest w opisie wydania na",
        "GitHubie, obok tego pliku - nie tutaj, bo to archiwum nie moze",
        "zawierac sumy samego siebie.",
        f"Checksum for {ARCHIVE_NAME} (SHA-256) is in the GitHub release notes",
        "next to this file, not here - this archive can't contain its own hash.",
        "",
        "This product isn't affiliated with or endorsed by "
        "Grinding Gear Games in any way.",
        "",
    ])


def build_archive(app: pathlib.Path, out_dir: pathlib.Path) -> tuple[pathlib.Path, str]:
    """Pakuje .app + CZYTAJ-TO.txt przez ditto. Zwraca (sciezka do archiwum,
    suma SHA-256 archiwum).

    .app to FOLDER, nie plik - zwykly zipfile.ZipFile psuje czasem uprawnienia
    wykonywalnosci i resource forki. `ditto` to natywne narzedzie macOS
    zrobione dokladnie do tego (uzywane m.in. przez sam Finder przy
    "Compress"), wiec zamiast reczne stitchowanie zipa, wolimy podprocesem
    wywolac ditto - jest tylko na macOS, ale ten skrypt i tak ma sens
    wylacznie tam.

    Zeby archiwum mialo .app I CZYTAJ-TO.txt obok siebie na najwyzszym
    poziomie (a nie .app zagniezdzone w dodatkowym folderze), najpierw
    kopiujemy oba do wspolnego katalogu tymczasowego, a dopiero jego
    ZAWARTOSC (nie sam katalog) pakujemy przez ditto z cwd ustawionym na ten
    katalog - stąd zrodlo "." zamiast sciezki i BEZ --keepParent.

    Suma liczona jest z ARCHIWUM, nie z pojedynczego pliku wewnatrz - .app to
    drzewo wielu plikow, wiec nie ma tu jednego binarium do zsumowania tak
    jak przy .exe. CZYTAJ-TO.txt (patrz readme()) celowo NIE zawiera tej
    sumy - nie da sie wpisac do pliku sumy archiwum, ktore ten plik zawiera,
    bez samoodwolania. Suma trafia tylko do RELEASE-NOTES-MAC.md, poza zip.
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

    stage = out_dir / "_mac_stage"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    copy = subprocess.run(
        ["ditto", str(app), str(stage / APP_NAME)],
        capture_output=True, text=True,
    )
    if copy.returncode != 0:
        raise SystemExit(f"ditto (kopiowanie .app) sie nie powiodlo:\n{copy.stderr}")

    (stage / README_NAME).write_text(readme(), encoding="utf-8")

    zip_result = subprocess.run(
        ["ditto", "-c", "-k", "--sequesterRsrc", ".", str(archive)],
        capture_output=True, text=True, cwd=str(stage),
    )
    if zip_result.returncode != 0:
        raise SystemExit(f"ditto (pakowanie) sie nie powiodlo:\n{zip_result.stderr}")

    shutil.rmtree(stage)

    # Sprawdzenie tuz po zapisie, a nie w konfiguracji CI - jak w package.py,
    # zeby ta sama kontrola dzialala lokalnie i nie dalo sie wydac
    # niekompletnej paczki. zipfile czyta archiwum ditto bez problemu, mimo
    # ze nie ono go tworzylo - to zwykly format ZIP.
    with zipfile.ZipFile(archive) as check:
        names = check.namelist()
        has_app = any(name.startswith(f"{APP_NAME}/") for name in names)
        has_readme = README_NAME in names
        if not has_app or not has_readme:
            raise SystemExit(f"Archiwum niekompletne: {names}")
        if check.testzip() is not None:
            raise SystemExit("Archiwum uszkodzone.")

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
