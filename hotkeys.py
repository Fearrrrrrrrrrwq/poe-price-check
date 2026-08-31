"""Dyspozytor platformowy dla skrotow klawiszowych - patrz winutil.py po ten
sam wzorzec i uzasadnienie (modul-poziomowy import biblioteki platformowej
NIE moze siedziec tutaj, bo zaimportowanie niewlasciwej dla systemu biblioteki
od razu wywala caly program przy starcie).

Windows: `keyboard` (jak zawsze).
macOS: `pynput` - `keyboard` tam nie dziala, patrz docstring hotkeys_macos.py
(zdiagnozowane na podstawie realnego crasha zgloszonego przez testera).
"""

import sys

if sys.platform == "darwin":
    from hotkeys_macos import add_hotkey, is_pressed, press, release, send
elif sys.platform.startswith("win"):
    from hotkeys_windows import add_hotkey, is_pressed, press, release, send
else:
    raise SystemExit(
        f"poe-price-check nie wspiera systemu {sys.platform!r}. "
        f"Obslugiwane: Windows i macOS."
    )

__all__ = ["add_hotkey", "is_pressed", "press", "release", "send"]
