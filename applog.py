"""Wyjscie diagnostyczne: plik logu w trybie okienkowym, konsola w trybach testowych.

Program jest budowany jako aplikacja okienkowa, wiec nie ma konsoli - a to znaczy,
ze sys.stdout jest None i kazdy print by sie wywrocil. Dlatego przy starcie ZAWSZE
podstawiamy jedno albo drugie.
"""

import ctypes
import os
import sys
from datetime import datetime

from paths import APP_DIR, APP_VERSION

LOG_PATH = APP_DIR / "poe-price-check.log"
MAX_LOG_BYTES = 1_000_000

ATTACH_PARENT_PROCESS = -1


def attach_console() -> bool:
    """Podpina okno konsoli - dla trybow diagnostycznych uruchamianych z terminala.

    Najpierw probujemy dolaczyc sie do konsoli rodzica (uzytkownik odpalil nas
    z wiersza polecen), a dopiero gdy jej nie ma - tworzymy wlasna.
    """
    try:
        kernel32 = ctypes.windll.kernel32
        if not kernel32.AttachConsole(ATTACH_PARENT_PROCESS):
            if not kernel32.AllocConsole():
                return False
        sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1)
        sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1)
        return True
    except (OSError, AttributeError):
        return False


def log_to_file() -> None:
    """Przekierowuje wyjscie do pliku obok programu."""
    try:
        if LOG_PATH.exists() and LOG_PATH.stat().st_size > MAX_LOG_BYTES:
            LOG_PATH.unlink()  # nie zbieramy logow w nieskonczonosc
        stream = open(LOG_PATH, "a", encoding="utf-8", errors="replace", buffering=1)
    except OSError:
        # Katalog tylko do odczytu - lepiej stracic logi niz nie wystartowac.
        stream = open(os.devnull, "w", encoding="utf-8")

    sys.stdout = stream
    sys.stderr = stream
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'=' * 60}\n{stamp}  poe-price-check {APP_VERSION}\n{'=' * 60}")


def setup(has_cli_args: bool) -> None:
    if has_cli_args:
        if attach_console():
            return
    log_to_file()
