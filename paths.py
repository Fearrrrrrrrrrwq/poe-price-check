"""Sciezki dzialajace tak samo z poziomu .py i ze spakowanego .exe.

W buildzie PyInstallera (--onefile) __file__ wskazuje na tymczasowy katalog
rozpakowania w %TEMP%, ktory znika po zamknieciu programu. Pliki, ktore maja
przetrwac (config, cache), musza isc obok samego .exe.
"""

import sys
from pathlib import Path

APP_VERSION = "1.1.1"


def app_dir() -> Path:
    """Katalog aplikacji: obok .exe w buildzie, obok zrodel przy uruchomieniu z Pythona."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_path(name: str) -> Path:
    """Plik dolaczony do buildu, tylko do odczytu."""
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        return Path(bundle) / name
    return Path(__file__).resolve().parent / name


APP_DIR = app_dir()
