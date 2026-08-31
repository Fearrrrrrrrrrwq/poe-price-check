"""Odpowiednik hotkeys_windows.py, ale przez `pynput` zamiast `keyboard`.

DLACZEGO NIE `keyboard` NA macOS - to nie jest teoria, to zgloszony i
zdiagnozowany crash (2026-08 od pierwszego testera na Macu):

  OSError: Error 13 - Must be run as administrator
  ValueError: Key 'd' is not mapped to any known key

Backend `keyboard` na macOS wymaga roota do niskopoziomowego przechwytywania
klawiszy (nie tylko uprawnienia Accessibility, ktore juz i tak trzeba
przyznac calej aplikacji - patrz main.py), a jego tabela mapowania klawiszy
na macOS jest dziurawa (nie rozpoznaje nawet zwyklego 'd'). To nie jest
kwestia konfiguracji - biblioteka jest tam po prostu zepsuta.

`pynput` uzywa tego samego mechanizmu co macOS-owe menu-bar apps i skrypty
Automatora (Quartz Event Taps / NSEvent global monitor) i dziala z samym
uprawnieniem Accessibility, bez roota.

Dwie rozne role, dwa rozne mechanizmy pynput:

1. Skroty GLOBALNE (add_hotkey) - `pynput.keyboard.GlobalHotKeys`. Buduje
   sie ZE WSZYSTKICH combo naraz (nie da sie dolozyc jednego do juz
   dzialajacego), wiec kazde wywolanie add_hotkey() tutaj zatrzymuje stary
   listener i odpala nowy z pelna, zaktualizowana mapa. main.py wola
   add_hotkey() trzy razy pod rzad przy starcie, wiec restart 2x jest bez
   znaczenia - nikt tego nie robi w petli.

2. Wysylanie/trzymanie klawiszy W GRZE (send/press/release, uzywane przez
   bridge.py do wpisywania sekwencji Ctrl+C/Ctrl+V do Boosteroida) -
   `pynput.keyboard.Controller`, ktory syntetyzuje zdarzenia klawiatury tak
   jak keyboard.send()/press()/release() na Windows.

is_pressed() nie ma odpowiednika w pynput (nie ma trybu "zapytaj o biezacy
stan") - trzymamy wiec wlasny, stale dzialajacy w tle Listener, ktory tylko
sledzi modyfikatory (ctrl/alt/shift/cmd) w zwyklym secie. Uzywane tylko przez
bridge._clear_modifiers() do sprawdzenia, czy user trzyma jeszcze jakis
modyfikator przed wyslaniem sekwencji.

UWAGA: pisane i skladniowo sprawdzone na Windows, bez dostepu do prawdziwego
macOS - dziala na podstawie dokumentacji pynput. Wymaga potwierdzenia przez
kogos z Makiem, tak jak reszta portu.
"""

from pynput.keyboard import Controller, GlobalHotKeys, Key, KeyCode, Listener

# Nazwa u nas -> klawisz pynput. Jedno zrodlo prawdy dla press()/release()/
# send() ORAZ dla konwersji combo na skladnie GlobalHotKeys (<ctrl>+<alt>+d) -
# patrz _bracket_name_for().
_SPECIAL: dict[str, Key] = {
    "ctrl": Key.ctrl, "control": Key.ctrl,
    "alt": Key.alt,
    "shift": Key.shift,
    # "windows" to nazwa z configu/Windows-owego slownika klawiszy - na
    # macOS nie ma klawisza Windows, najblizszy fizyczny odpowiednik to Cmd.
    "windows": Key.cmd, "cmd": Key.cmd,
    "tab": Key.tab,
    "enter": Key.enter, "return": Key.enter,
    "esc": Key.esc, "escape": Key.esc,
    "space": Key.space,
    "backspace": Key.backspace,
    "delete": Key.delete,
    "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
    **{f"f{n}": getattr(Key, f"f{n}") for n in range(1, 21) if hasattr(Key, f"f{n}")},
}

# Odwrotnosc _SPECIAL, do rozpoznawania zdarzen z Listenera (obiekt Key ->
# nasza nazwa). Trzy warianty modyfikatora (np. Key.ctrl_l/ctrl_r) mapujemy
# na ta sama nazwe co wersje "ogolne" - is_pressed() nie rozroznia lewy/prawy.
_MODIFIER_VARIANTS: dict[Key, str] = {
    Key.ctrl: "ctrl", Key.ctrl_l: "ctrl", Key.ctrl_r: "ctrl",
    Key.alt: "alt", Key.alt_l: "alt", Key.alt_r: "alt",
    Key.shift: "shift", Key.shift_l: "shift", Key.shift_r: "shift",
    Key.cmd: "windows", Key.cmd_l: "windows", Key.cmd_r: "windows",
}


def _key_for(name: str):
    name = name.strip().lower()
    if name in _SPECIAL:
        return _SPECIAL[name]
    if len(name) == 1:
        return KeyCode.from_char(name)
    raise ValueError(f"Nieznany klawisz: {name!r}")


def _bracket_name_for(name: str) -> str | None:
    """Nazwa w nawiasach <...>, ktorej pynput uzywa w stringach GlobalHotKeys."""
    key = _SPECIAL.get(name.strip().lower())
    return key.name if key is not None else None


def _to_pynput_combo(combo: str) -> str:
    parts = [p.strip().lower() for p in combo.split("+") if p.strip()]
    mapped = []
    for part in parts:
        bracket = _bracket_name_for(part)
        if bracket:
            mapped.append(f"<{bracket}>")
        elif len(part) == 1:
            mapped.append(part)
        else:
            raise ValueError(f"Nieznany klawisz w skrocie: {part!r}")
    return "+".join(mapped)


_controller = Controller()

_hotkey_map: dict[str, "callable"] = {}
_hotkey_listener: GlobalHotKeys | None = None


def add_hotkey(combo: str, callback) -> None:
    global _hotkey_listener
    _hotkey_map[_to_pynput_combo(combo)] = callback
    if _hotkey_listener is not None:
        _hotkey_listener.stop()
    _hotkey_listener = GlobalHotKeys(_hotkey_map)
    _hotkey_listener.daemon = True
    _hotkey_listener.start()


def send(combo: str) -> None:
    parts = [p.strip().lower() for p in combo.split("+") if p.strip()]
    keys = [_key_for(part) for part in parts]
    for key in keys:
        _controller.press(key)
    for key in reversed(keys):
        _controller.release(key)


def press(key: str) -> None:
    _controller.press(_key_for(key))


def release(key: str) -> None:
    try:
        target = _key_for(key)
    except ValueError:
        # bridge._clear_modifiers() zwalnia "windows" tak samo jak reszte
        # modyfikatorow bez sprawdzania, czy klawisz w ogole ma sens na tej
        # platformie - tu jest jedyne miejsce, gdzie to rozstrzygamy.
        return
    try:
        _controller.release(target)
    except Exception:  # noqa: BLE001 - zwalnianie na sile bywa zawodne, jak na Windows
        pass


# --- sledzenie wcisnietych modyfikatorow, pod is_pressed() -----------------
#
# pynput nie ma odpytania "czy X jest teraz wcisniety" - jedyny sposob to
# sledzic wlasne zdarzenia press/release w tle i pytac o stan wlasnego seta.

_pressed_modifiers: set[str] = set()


def _on_press(key) -> None:
    name = _MODIFIER_VARIANTS.get(key)
    if name:
        _pressed_modifiers.add(name)


def _on_release(key) -> None:
    name = _MODIFIER_VARIANTS.get(key)
    if name:
        _pressed_modifiers.discard(name)


try:
    # Import tego modulu (przez `import bridge`) dzieje sie tez w kontroli CI
    # na headless macOS runnerze bez zalogowanej sesji GUI, gdzie stworzenie
    # Listenera moze sie nie udac - to nie moze wywalic calego importu.
    # Bez dzialajacego listenera is_pressed() po prostu zawsze zwraca False,
    # co degraduje _clear_modifiers() do natychmiastowego wymuszonego
    # zwolnienia zamiast czekania - gorzej, ale nie krytycznie.
    _modifier_listener = Listener(on_press=_on_press, on_release=_on_release)
    _modifier_listener.daemon = True
    _modifier_listener.start()
except Exception:  # noqa: BLE001 - patrz komentarz wyzej
    _modifier_listener = None


def is_pressed(key: str) -> bool:
    return key.strip().lower() in _pressed_modifiers
