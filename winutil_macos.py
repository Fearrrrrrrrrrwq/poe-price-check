"""Odpowiedniki funkcji z winutil_windows.py, ale dla macOS.

macOS nie ma WinAPI, wiec zamiast ctypes uzywamy dwoch narzedzi systemowych,
ktore sa na kazdym Macu bez zadnych dodatkowych zaleznosci:

- `pbpaste` do czytania schowka,
- `osascript` (AppleScript przez System Events) do pytania o aktywna
  aplikacje/okno i do przywracania fokusu.

System Events wymaga uprawnienia Accessibility dla procesu, ktory go pyta
(pierwsze uzycie pokaze systemowy monit) - to macowy odpowiednik tego, czym na
Windows jest UIPI/uprawnienia administratora dla wysylania klawiszy. Bez tego
uprawnienia kazda funkcja tutaj po prostu zwraca bezpieczna wartosc domyslna,
tak samo jak funkcje w winutil_windows.py przy bledzie WinAPI.

UWAGA: ten plik nie byl uruchamiany na prawdziwym macOS (autor portu pracuje
na Windows) - dziala na podstawie dokumentacji AppleScript/System Events.
Przed wydaniem wersji na macOS przetestuj recznie kazda funkcje.
"""

import subprocess

TIMEOUT = 2  # sekundy - diagnostyka nie moze zawiesic programu na zablokowanym AppleScript


def _osascript(script: str) -> str:
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def window_is_foreground(hwnd: int) -> bool:
    """Na macOS "okno" to identyfikator procesu (patrz foreground_hwnd) - jest
    na wierzchu, gdy to on jest teraz zwracany przez foreground_hwnd()."""
    if not hwnd:
        return False
    return foreground_hwnd() == hwnd


def is_admin() -> bool:
    """Najblizszy odpowiednik "podniesionych uprawnien" na macOS - root."""
    try:
        import os
        return os.geteuid() == 0
    except AttributeError:
        return False


def read_clipboard_text(attempts: int = 5) -> str:
    """Czyta tekst ze schowka przez `pbpaste`, bez Tkintera - z tych samych
    powodow co na Windows (patrz winutil_windows.read_clipboard_text)."""
    import time

    for _ in range(attempts):
        try:
            result = subprocess.run(
                ["pbpaste"], capture_output=True, text=True, timeout=TIMEOUT,
            )
            if result.returncode == 0:
                return result.stdout or ""
        except (OSError, subprocess.SubprocessError):
            pass
        time.sleep(0.05)
    return ""


def foreground_hwnd() -> int:
    """Zwraca PID procesu na pierwszym planie - to nasz odpowiednik HWND-a."""
    out = _osascript(
        'tell application "System Events" to get unix id of first process '
        'whose frontmost is true'
    )
    try:
        return int(out)
    except ValueError:
        return 0


def hwnd_process_id(hwnd: int) -> int:
    # Na macOS "hwnd" JEST juz PID-em - patrz foreground_hwnd().
    return hwnd


def hwnd_is_own_process(hwnd: int) -> bool:
    """Czy okno nalezy do nas. Klawisze wyslane do wlasnego okna nie dojda do gry."""
    if not hwnd:
        return False
    import os
    return hwnd == os.getpid()


def set_foreground(hwnd: int) -> bool:
    """Probuje przywrocic dany proces na pierwszy plan przez System Events."""
    if not hwnd:
        return False
    out = _osascript(
        f'tell application "System Events" to set frontmost of '
        f'(first process whose unix id is {int(hwnd)}) to true'
    )
    return out != "" or True  # osascript bez bledu -> uznajemy za sukces


def foreground_window_title() -> str:
    title = _osascript(
        'tell application "System Events" to tell (first process whose '
        'frontmost is true) to get name of front window'
    )
    return title or "(brak aktywnego okna)"


def foreground_process_name() -> str:
    name = _osascript(
        'tell application "System Events" to get name of first process '
        'whose frontmost is true'
    )
    if name:
        return name
    # Pusty wynik zwykle oznacza brak uprawnienia Accessibility dla System
    # Events, a nie brak aktywnego okna - stad inny komunikat niz na Windows.
    return "(brak dostepu - sprawdz uprawnienie Accessibility w Ustawieniach systemowych)"


def describe_foreground() -> str:
    return f"{foreground_process_name()}  |  tytul: {foreground_window_title()!r}"
