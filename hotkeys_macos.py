"""macOS hotkeys - TRZECIA wersja tego pliku. Historia jest wazna, zeby nie
wrocic do jednego z dwoch juz wykluczonych bledow:

1. `keyboard` (pierwsza wersja) - crashowala NATYCHMIAST. Biblioteka na
   macOS wymaga roota do niskopoziomowego przechwytywania klawiszy i ma
   dziurawa tabele mapowania (nie rozpoznawala nawet zwyklego 'd').
   Zdiagnozowane z logu pierwszego crasha zgloszonego przez testera.

2. `pynput` (druga wersja) - program zyl DLUZEJ (13 sekund zamiast
   milisekundy), ale crashowal natywnie (EXC_BREAKPOINT/SIGTRAP,
   dispatch_assert_queue_fail) przy PIERWSZYM realnym zdarzeniu klawiatury.
   Przyczyna, potwierdzona crash logiem od testera i realnymi zgloszeniami
   w repo pynput na GitHubie: pynput na macOS musi dla KAZDEGO zdarzenia
   klawiatury zapytac HIToolbox (Text Services Manager) "jaki znak
   odpowiada temu kodowi w biezacym ukladzie klawiatury" - i robi to z
   WLASNEGO watku w tle. Nowszy macOS (26.6.2 w logu testera) twardo
   asercjuje, ze HIToolbox/TSM wolno pytac TYLKO z glownego watku, i zabija
   caly proces zamiast tylko ostrzec. To problem SYSTEMOWY calej
   biblioteki na tej platformie, nie cos do naprawienia parametrem.

TA (trzecia) wersja w ogole nie dotyka HIToolbox, bo pracuje wylacznie na
surowych kodach klawiszy (virtual keycode), nigdy na znakach:

1. Skroty GLOBALNE (add_hotkey) - `quickmachotkey`, wiazanie PyObJC na
   stary, ale wciaz w pelni wspierany Carbon Event Manager
   (RegisterEventHotKey). Rejestruje JEDEN konkretny kod klawisza + maske
   modyfikatorow i dostaje callback TYLKO gdy dokladnie ta kombinacja
   zostanie wcisnieta - w odroznieniu od pynput/keyboard NIE przechwytuje
   i nie klasyfikuje kazdego zdarzenia klawiatury w systemie, wiec nigdy
   nie musi pytac o uklad klawiatury.

2. Wysylanie/trzymanie klawiszy W GRZE (send/press/release) oraz
   is_pressed() - bezposrednio przez ctypes do CoreGraphics/Quartz
   (CGEventCreateKeyboardEvent + CGEventPost + CGEventSourceFlagsState).
   Zero nowej ciezkiej zaleznosci - ctypes jest w standardowej bibliotece,
   dokladnie jak w winutil_windows.py.

Tabela kodow klawiszy nizej to STALA czesc API systemu od Mac OS X 10.0
(Carbon Events.h) - zweryfikowana w dokumentacji Apple i w zrodlach
produkcyjnych narzedzi zdalnego sterowania (m.in. enigo/RustDesk), nie
wymyslona na poczekaniu.

UWAGA (jak reszta portu macOS): pisane i sprawdzone skladniowo na Windows,
bez dostepu do prawdziwego Maca. Najwiekszy pojedynczy punkt niepewnosci:
Carbon Event Manager powinien dostarczac callback skrotu przez ta sama
petle zdarzen, ktora juz napedza Tkinter (Tk na macOS jest w calosci
oparte o Cocoa/NSApplication, wiec root.mainloop() juz pompuje realny
run loop) - a nie tylko przez AppHelper.runEventLoop() z przykladu w
dokumentacji quickmachotkey. To zalozenie oparte na tym, jak dziala Carbon
Event Manager, ale NIEPOTWIERDZONE na prawdziwym sprzecie - jesli skroty
w ogole nie beda sie odpalac (w odroznieniu od crashowania), to jest
pierwsze miejsce do sprawdzenia.
"""

import ctypes
import ctypes.util

from quickmachotkey import mask, quickHotKey
from quickmachotkey.constants import cmdKey, controlKey, optionKey, shiftKey

# --- surowe kody klawiszy (Carbon virtual keycodes, ANSI-US) ---------------
#
# Fizyczna pozycja klawisza, nie jego etykieta w danym ukladzie - dokladnie
# tego tu potrzeba, i dlatego to podejscie omija caly problem z pynput.
_VK: dict[str, int] = {
    "a": 0x00, "s": 0x01, "d": 0x02, "f": 0x03, "h": 0x04, "g": 0x05,
    "z": 0x06, "x": 0x07, "c": 0x08, "v": 0x09, "b": 0x0B, "q": 0x0C,
    "w": 0x0D, "e": 0x0E, "r": 0x0F, "y": 0x10, "t": 0x11, "o": 0x1F,
    "u": 0x20, "i": 0x22, "p": 0x23, "l": 0x25, "j": 0x26, "k": 0x28,
    "n": 0x2D, "m": 0x2E,
    "1": 0x12, "2": 0x13, "3": 0x14, "4": 0x15, "5": 0x17, "6": 0x16,
    "7": 0x1A, "8": 0x1C, "9": 0x19, "0": 0x1D,
    "f1": 0x7A, "f2": 0x78, "f3": 0x63, "f4": 0x76, "f5": 0x60, "f6": 0x61,
    "f7": 0x62, "f8": 0x64, "f9": 0x65, "f10": 0x6D, "f11": 0x67, "f12": 0x6F,
    "tab": 0x30, "enter": 0x24, "return": 0x24, "esc": 0x35, "escape": 0x35,
    "space": 0x31, "backspace": 0x33, "delete": 0x75,
    "left": 0x7B, "right": 0x7C, "up": 0x7E, "down": 0x7D,
    # Modyfikatory - traktowane jak kazdy inny klawisz, bo bridge.py
    # wysyla je jako osobne zdarzenia keyDown/keyUp, nie jako maske
    # (patrz send_combo() w bridge.py - trzymanie z jawna pauza).
    "cmd": 0x37, "windows": 0x37,
    "shift": 0x38, "alt": 0x3A, "ctrl": 0x3B,
}


def _vk_for(name: str) -> int:
    name = name.strip().lower()
    if name in _VK:
        return _VK[name]
    raise ValueError(f"Nieznany klawisz: {name!r}")


# --- rejestracja skrotow globalnych (Carbon RegisterEventHotKey) -----------
#
# Carbon EventModifiers to INNA przestrzen bitowa niz CGEventFlags nizej -
# nie mylic. Wartosci biora sie z quickmachotkey.constants, nie sa wpisane
# na sztywno - to jedyne miejsce, gdzie ufamy cudzej tabeli zamiast wlasnej
# zweryfikowanej.
_MODIFIER_BIT = {
    "ctrl": controlKey, "control": controlKey,
    "alt": optionKey,
    "shift": shiftKey,
    "windows": cmdKey, "cmd": cmdKey,
}

# Referencje trzymane, zeby PyObjC/Carbon nie zwolnily rejestracji hotkeya
# po tym, jak lokalna zmienna w add_hotkey() wyjdzie poza zasieg.
_registered: list = []


def add_hotkey(combo: str, callback) -> None:
    parts = [p.strip().lower() for p in combo.split("+") if p.strip()]
    if not parts:
        return
    *modifier_names, main_key = parts
    virtual_key = _vk_for(main_key)
    try:
        modifier_mask = mask(*(_MODIFIER_BIT[name] for name in modifier_names))
    except KeyError as exc:
        raise ValueError(f"Nieznany modyfikator w skrocie {combo!r}: {exc}") from exc

    handler = quickHotKey(virtualKey=virtual_key, modifierMask=modifier_mask)(
        lambda: callback()
    )
    _registered.append(handler)


# --- wysylanie/trzymanie klawiszy (CGEvent, bezposrednio przez ctypes) -----

_cg = ctypes.CDLL(ctypes.util.find_library("CoreGraphics"))
_cg.CGEventCreateKeyboardEvent.restype = ctypes.c_void_p
_cg.CGEventCreateKeyboardEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_bool]
_cg.CGEventPost.restype = None
_cg.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
_cg.CGEventSourceFlagsState.restype = ctypes.c_uint64
_cg.CGEventSourceFlagsState.argtypes = [ctypes.c_int32]

_cf = ctypes.CDLL(ctypes.util.find_library("CoreFoundation"))
_cf.CFRelease.restype = None
_cf.CFRelease.argtypes = [ctypes.c_void_p]

_HID_EVENT_TAP = 0          # kCGHIDEventTap - jak od prawdziwej klawiatury
_HID_SYSTEM_STATE = 1       # kCGEventSourceStateHIDSystemState

_MODIFIER_FLAG = {
    "shift": 0x00020000,    # kCGEventFlagMaskShift
    "ctrl": 0x00040000,     # kCGEventFlagMaskControl
    "alt": 0x00080000,      # kCGEventFlagMaskAlternate
    "windows": 0x00100000,  # kCGEventFlagMaskCommand
    "cmd": 0x00100000,
}


def _post_key(virtual_key: int, key_down: bool) -> None:
    event = _cg.CGEventCreateKeyboardEvent(None, virtual_key, key_down)
    if not event:
        return
    try:
        _cg.CGEventPost(_HID_EVENT_TAP, event)
    finally:
        _cf.CFRelease(event)


def press(key: str) -> None:
    _post_key(_vk_for(key), True)


def release(key: str) -> None:
    try:
        virtual_key = _vk_for(key)
    except ValueError:
        return
    _post_key(virtual_key, False)


def send(combo: str) -> None:
    parts = [p.strip().lower() for p in combo.split("+") if p.strip()]
    keys = [_vk_for(part) for part in parts]
    for virtual_key in keys:
        _post_key(virtual_key, True)
    for virtual_key in reversed(keys):
        _post_key(virtual_key, False)


def is_pressed(key: str) -> bool:
    flag = _MODIFIER_FLAG.get(key.strip().lower())
    if flag is None:
        return False
    current = _cg.CGEventSourceFlagsState(_HID_SYSTEM_STATE)
    return bool(current & flag)
