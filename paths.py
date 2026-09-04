"""Sciezki dzialajace tak samo z poziomu .py i ze spakowanego buildu.

W buildzie PyInstallera (--onefile) __file__ wskazuje na tymczasowy katalog
rozpakowania w %TEMP%, ktory znika po zamknieciu programu. Pliki, ktore maja
przetrwac (config, cache, log), musza isc gdzie indziej - a "gdzie indziej"
oznacza cos innego na kazdym systemie, patrz app_dir().
"""

import sys
from pathlib import Path

APP_VERSION = "1.7.0"


def app_dir() -> Path:
    """Katalog na dane uzytkownika: config, cache slownika statystyk, log.

    Windows: obok .exe. To zwykly luzny plik, wiec katalog obok niego jest
    zawsze zapisywalny i to jedyne miejsce, ktore user w ogole widzi.

    macOS: NIGDY obok pliku wykonywalnego wewnatrz .app - to bylby zapis
    do wnetrza paczki aplikacji (Contents/MacOS/), co jest zle z dwoch
    powodow:
      1. Gatekeeper potrafi otworzyc niepodpisana .app z losowej, TYLKO DO
         ODCZYTU sciezki (App Translocation), jesli zostanie uruchomiona
         zanim uzytkownik przeniesie ja z Pobranych/DMG. Kazda proba zapisu
         (pierwsze uruchomienie: config.json kopiowany z wzorca) wywala
         program bez sladu w interfejsie - okno miga i znika, bo to
         aplikacja okienkowa bez konsoli (patrz applog.py).
      2. Nawet gdy zapis by sie udal, dane uzytkownika wewnatrz paczki
         aplikacji znikaja przy kazdej aktualizacji/reinstalacji - na
         macOS na dane uzytkownika jest osobne, zwyczajowe miejsce.
    Dlatego na macOS uzywamy ~/Library/Application Support/, tak jak robi
    to kazda inna aplikacja kakao/macOS.

    Uruchomienie z Pythona (bez frozen): obok zrodel, dla wygody dewelopera
    - tak samo na obu systemach.
    """
    if getattr(sys, "frozen", False):
        if sys.platform == "darwin":
            support = Path.home() / "Library" / "Application Support" / "PoE Price Check"
            support.mkdir(parents=True, exist_ok=True)
            return support
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_path(name: str) -> Path:
    """Plik dolaczony do buildu, tylko do odczytu."""
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        return Path(bundle) / name
    return Path(__file__).resolve().parent / name


APP_DIR = app_dir()
