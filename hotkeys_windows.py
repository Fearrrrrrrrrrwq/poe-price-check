"""Cienkie opakowanie na biblioteke `keyboard` - dziala tylko na Windows.

Nie zmienia zadnego zachowania wzgledem tego, jak `main.py`/`bridge.py`
uzywaly `keyboard` bezposrednio wczesniej - to czysta delegacja, zeby oba
pliki mogly importowac wspolny interfejs `hotkeys` niezaleznie od platformy
(patrz hotkeys.py i hotkeys_macos.py - macOS potrzebuje zupelnie innej
implementacji, bo `keyboard` tam nie dziala, patrz docstring hotkeys_macos.py).
"""

import keyboard as _keyboard


def add_hotkey(combo: str, callback) -> None:
    _keyboard.add_hotkey(combo, callback)


def send(combo: str) -> None:
    _keyboard.send(combo)


def press(key: str) -> None:
    _keyboard.press(key)


def release(key: str) -> None:
    _keyboard.release(key)


def is_pressed(key: str) -> bool:
    return _keyboard.is_pressed(key)
