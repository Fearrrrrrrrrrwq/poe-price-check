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


def resource_snapshot() -> str:
    """Licznik zasobow procesu - do wykrycia, co narasta miedzy wycenami.

    Objaw "po kilkunastu sprawdzeniach zaczyna mulic, restart pomaga" oznacza,
    ze cos rosnie wewnatrz procesu. Zamiast zgadywac, ktory to zasob, zapisujemy
    je wszystkie przy kazdej wycenie - roznica miedzy pierwszym a dwudziestym
    wpisem pokazuje winowajce od razu.
    """
    import ctypes
    import gc
    import threading

    bits = [f"watki={threading.active_count()}",
            f"obiekty={len(gc.get_objects())}"]

    try:  # pamiec i uchwyty - tylko Windows
        # Bez zadeklarowanego restype ctypes traktuje uchwyt jak c_int i obcina
        # go na 64 bitach - wywolania cicho zwracaja zero zamiast danych.
        ctypes.windll.kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        handle = ctypes.windll.kernel32.GetCurrentProcess()

        class _Mem(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_uint32), ("PageFaultCount", ctypes.c_uint32),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]

        info = _Mem()
        info.cb = ctypes.sizeof(info)
        # Na nowszym Windowsie te funkcje wystawia kernel32 (K32-), a nie psapi.
        get_mem = getattr(ctypes.windll.kernel32, "K32GetProcessMemoryInfo", None)
        if get_mem is not None:
            get_mem.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32]
        if get_mem is None:
            get_mem = ctypes.windll.psapi.GetProcessMemoryInfo
        if get_mem(handle, ctypes.byref(info), info.cb):
            bits.append(f"pamiec={info.WorkingSetSize // 1048576}MB")

        ctypes.windll.kernel32.GetProcessHandleCount.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
        count = ctypes.c_uint32()
        if ctypes.windll.kernel32.GetProcessHandleCount(handle, ctypes.byref(count)):
            bits.append(f"uchwyty={count.value}")

        ctypes.windll.user32.GetGuiResources.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        gdi = ctypes.windll.user32.GetGuiResources(handle, 0)   # obiekty GDI
        usr = ctypes.windll.user32.GetGuiResources(handle, 1)   # obiekty USER
        bits.append(f"gdi={gdi}")
        bits.append(f"user={usr}")
    except Exception:  # noqa: BLE001 - diagnostyka nie moze nic zepsuc
        pass

    try:
        import keyboard
        bits.append(f"kb_hooki={len(getattr(keyboard, '_hooks', {}) or {})}")
        listener = getattr(keyboard, '_listener', None)
        if listener is not None:
            bits.append(f"kb_kolejka={listener.queue.qsize()}")
            bits.append(f"kb_wcisniete={len(getattr(listener, 'active_modifiers', ()) or ())}")
    except Exception:  # noqa: BLE001
        pass

    return "  ".join(bits)
