"""Cienkie opakowanie na biblioteke `keyboard` - dziala tylko na Windows.

Nie zmienia zadnego zachowania wzgledem tego, jak `main.py`/`bridge.py`
uzywaly `keyboard` bezposrednio wczesniej - to czysta delegacja, zeby oba
pliki mogly importowac wspolny interfejs `hotkeys` niezaleznie od platformy
(patrz hotkeys.py i hotkeys_macos.py - macOS potrzebuje zupelnie innej
implementacji, bo `keyboard` tam nie dziala, patrz docstring hotkeys_macos.py).
"""

import keyboard as _keyboard

# Uchwyty z add_hotkey trzymane per kombinacja - remove_hotkey() woli je od
# ponownego parsowania stringa przez _keyboard, ktore przy niestandardowej
# kolejnosci modyfikatorow moglo trafic w inny wewnetrzny klucz niz ten,
# ktorym program faktycznie zarejestrowal skrot.
_handlers: dict[str, object] = {}


def add_hotkey(combo: str, callback) -> None:
    _handlers[combo] = _keyboard.add_hotkey(combo, callback)


def remove_hotkey(combo: str) -> None:
    handler = _handlers.pop(combo, None)
    if handler is not None:
        _keyboard.remove_hotkey(handler)


def send(combo: str) -> None:
    _keyboard.send(combo)


def write(text: str) -> None:
    """Wpisuje tekst znak po znaku - do makr czatu ('/hideout' itp.), nie do
    skrotow (te ida przez send())."""
    _keyboard.write(text)


def press(key: str) -> None:
    _keyboard.press(key)


def release(key: str) -> None:
    _keyboard.release(key)


def is_pressed(key: str) -> bool:
    return _keyboard.is_pressed(key)
