"""Drobne zapytania do WinAPI potrzebne do diagnozy wysylania klawiszy.

Kluczowe pytanie przy Boosteroidzie brzmi: czy nasze syntetyczne klawisze w ogole
docieraja do okna streamu. Windows potrafi je po cichu blokowac (UIPI), gdy okno
docelowe dziala z wyzszymi uprawnieniami niz nasz proces.
"""

import ctypes
import time
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
GA_ROOT = 2

user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetAncestor.restype = wintypes.HWND
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]


def window_is_foreground(hwnd: int) -> bool:
    """Czy okno o podanym uchwycie jest aktualnie na wierzchu.

    Tk nie potrafi tego powiedziec: focus_displayof() zwraca wlasne okno nawet
    wtedy, gdy aplikacja dawno stracila fokus, a nawet gdy okno jest schowane.
    Pytamy wiec system. winfo_id() oddaje uchwyt wewnetrznego okna Tk, wiec
    najpierw wspinamy sie do okna nadrzednego.
    """
    if not hwnd:
        return False
    try:
        root = user32.GetAncestor(wintypes.HWND(hwnd), GA_ROOT) or hwnd
        return int(user32.GetForegroundWindow() or 0) == int(root)
    except Exception:  # noqa: BLE001 - to tylko podpowiedz dla interfejsu
        return True  # przy watpliwosci nie chowamy okna


def is_admin() -> bool:
    """Czy nasz proces dziala z podniesionymi uprawnieniami."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:  # noqa: BLE001 - diagnostyka nie moze wywrocic programu
        return False


CF_UNICODETEXT = 13

kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
user32.GetClipboardData.restype = ctypes.c_void_p
user32.GetClipboardData.argtypes = [wintypes.UINT]


def read_clipboard_text(attempts: int = 5) -> str:
    """Czyta tekst ze schowka przez WinAPI, bez Tkintera.

    Tkinter odpada: czytanie schowka przez tk.Tk() tworzyloby DRUGI obiekt Tk
    w procesie, ktory ma juz okno panelu, i to z watku roboczego. Tkinter nie
    jest bezpieczny watkowo - to prosta droga do zawieszenia albo wywrotki.

    Schowek bywa chwilowo zajety przez inna aplikacje, wiec probujemy kilka razy.
    """
    for _ in range(attempts):
        if user32.OpenClipboard(None):
            try:
                handle = user32.GetClipboardData(CF_UNICODETEXT)
                if not handle:
                    return ""
                pointer = kernel32.GlobalLock(handle)
                if not pointer:
                    return ""
                try:
                    return ctypes.c_wchar_p(pointer).value or ""
                finally:
                    kernel32.GlobalUnlock(handle)
            finally:
                user32.CloseClipboard()
        time.sleep(0.05)
    return ""


def foreground_hwnd() -> int:
    return int(user32.GetForegroundWindow() or 0)


def hwnd_process_id(hwnd: int) -> int:
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
    return int(pid.value)


def hwnd_is_own_process(hwnd: int) -> bool:
    """Czy okno nalezy do nas. Klawisze wyslane do wlasnego okna nie dojda do gry."""
    if not hwnd:
        return False
    return hwnd_process_id(hwnd) == int(kernel32.GetCurrentProcessId())


def set_foreground(hwnd: int) -> bool:
    """Probuje wyniesc okno na pierwszy plan.

    Windows ogranicza te operacje, ale proces, ktory przed chwila dostal wejscie
    z klawiatury (a my wlasnie obsluzylismy skrot), zwykle ma do niej prawo.
    """
    if not hwnd:
        return False
    try:
        return bool(user32.SetForegroundWindow(wintypes.HWND(hwnd)))
    except Exception:  # noqa: BLE001 - nieudane przywrocenie nie moze przerwac wyceny
        return False


def foreground_window_title() -> str:
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return "(brak aktywnego okna)"
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value or "(okno bez tytulu)"


def foreground_process_name() -> str:
    """Nazwa pliku .exe okna na wierzchu, albo powod niepowodzenia."""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return "(brak)"

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return "(nieznany pid)"

    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        # Brak dostepu do procesu to sam w sobie sygnal: okno na wierzchu
        # dziala najpewniej z wyzszymi uprawnieniami niz my.
        return "(brak dostepu do procesu - podejrzenie podniesionych uprawnien)"

    try:
        size = wintypes.DWORD(1024)
        buffer = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return buffer.value.rsplit("\\", 1)[-1]
        return "(nie udalo sie odczytac nazwy)"
    finally:
        kernel32.CloseHandle(handle)


def describe_foreground() -> str:
    return f"{foreground_process_name()}  |  tytul: {foreground_window_title()!r}"
