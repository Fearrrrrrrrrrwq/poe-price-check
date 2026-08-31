"""Dyspozytor platformowy: wybiera implementacje wg systemu operacyjnego.

Ten plik sam nie zawiera zadnej logiki systemowej - to wlasciwosc, nie
przeoczenie. Kod ktory czyta ctypes.windll POZA funkcja (na poziomie modulu)
wywroci sie przy imporcie na kazdym systemie innym niz Windows, wiec te
wywolania musza siedziec w osobnych plikach, importowanych dopiero tutaj,
warunkowo.
"""

import sys

if sys.platform == "darwin":
    from winutil_macos import (
        describe_foreground,
        foreground_hwnd,
        foreground_process_name,
        foreground_window_title,
        hwnd_is_own_process,
        hwnd_process_id,
        is_admin,
        read_clipboard_text,
        set_foreground,
        window_is_foreground,
    )
elif sys.platform.startswith("win"):
    from winutil_windows import (
        describe_foreground,
        foreground_hwnd,
        foreground_process_name,
        foreground_window_title,
        hwnd_is_own_process,
        hwnd_process_id,
        is_admin,
        read_clipboard_text,
        set_foreground,
        window_is_foreground,
    )
else:
    raise SystemExit(
        f"poe-price-check nie wspiera systemu {sys.platform!r}. "
        f"Obslugiwane: Windows i macOS."
    )

__all__ = [
    "describe_foreground",
    "foreground_hwnd",
    "foreground_process_name",
    "foreground_window_title",
    "hwnd_is_own_process",
    "hwnd_process_id",
    "is_admin",
    "read_clipboard_text",
    "set_foreground",
    "window_is_foreground",
]
