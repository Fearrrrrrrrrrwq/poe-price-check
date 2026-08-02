"""Most miedzy sesja Boosteroida a lokalnym PC.

Schowek w Boosteroidzie dziala tylko w kierunku lokalnie -> chmura, wiec tekstu
przedmiotu nie da sie odczytac wprost. Obejscie: w sesji chmurowej trzymamy
otwarty w przegladarce Steam Overlay publiczny dokument Google. Skrypt wysyla do
Boosteroida sekwencje klawiszy, ktora kopiuje przedmiot i wkleja go do dokumentu,
a lokalnie odczytujemy ten sam dokument przez HTTP.

Sekwencja wykonywana jest "w ciemno" - nie widzimy stanu maszyny w chmurze, wiec
opoznienia z config.json trzeba dobrac do wlasnego lacza.
"""

import threading
import time
from dataclasses import dataclass

import keyboard
import requests

from winutil import describe_foreground

GDOC_EXPORT = "https://docs.google.com/document/d/{doc_id}/export?format=txt"


class BridgeError(RuntimeError):
    pass


@dataclass
class BridgeTiming:
    after_copy_ms: int = 250
    overlay_open_ms: int = 1500
    after_select_ms: int = 150
    after_paste_ms: int = 200  # tylko chwila na ustabilizowanie, reszta to juz odpytywanie
    after_close_ms: int = 200
    overlay_poll_s: float = 4.0  # jak dlugo czekac na tekst przy OTWARTYM overlayu
    poll_timeout_s: float = 12.0  # laczny budzet na doczekanie sie tekstu
    poll_interval_s: float = 0.25
    key_hold_ms: int = 60


def send_combo(combo: str, hold_ms: int = 80) -> None:
    """Wysyla kombinacje klawiszy z jawnymi pauzami miedzy krokami.

    keyboard.send("ctrl+c") wciska i puszcza cala kombinacje w zerowym czasie.
    Klient Boosteroida probkuje wejscie i potrafi zgubic modyfikator - do chmury
    dociera samo 'c', bez trzymanego Ctrl. Rozbicie na press/pauza/release z
    zauwazalnym przytrzymaniem rozwiazuje to.
    """
    parts = [part.strip().lower() for part in combo.split("+") if part.strip()]
    if not parts:
        return
    hold = hold_ms / 1000.0

    sequence = [(keyboard.press, part) for part in parts]
    sequence += [(keyboard.release, part) for part in reversed(parts)]

    last = len(sequence) - 1
    for index, (action, part) in enumerate(sequence):
        action(part)
        if index != last:  # po ostatnim zwolnieniu nie ma na co czekac
            time.sleep(hold)


class Transport:
    """Odczyt tekstu zapisanego po stronie chmury."""

    def read(self) -> str:
        raise NotImplementedError


class GoogleDocTransport(Transport):
    """Publiczny dokument Google, eksportowany jako czysty tekst.

    Dokument musi byc udostepniony jako "Kazdy uzytkownik, ktory ma link" z
    prawem edycji - inaczej sesja w chmurze nie wklei do niego tresci.
    """

    def __init__(self, doc_id: str) -> None:
        if not doc_id:
            raise BridgeError("Brak doc_id w config.json.")
        self.doc_id = doc_id
        self.session = requests.Session()

    def read(self) -> str:
        url = GDOC_EXPORT.format(doc_id=self.doc_id)
        try:
            response = self.session.get(url, timeout=15, allow_redirects=True)
        except requests.RequestException as exc:
            raise BridgeError(
                f"Brak polaczenia z Google Docs ({type(exc).__name__})."
            ) from exc
        if response.status_code in (401, 403, 404):
            raise BridgeError(
                f"Nie moge odczytac dokumentu ({response.status_code}). Sprawdz, czy "
                "jest udostepniony jako 'Kazdy uzytkownik, ktory ma link'."
            )
        response.raise_for_status()
        # Google potrafi oddac tekst z BOM-em i twardymi znakami niedzielacymi.
        text = response.content.decode("utf-8-sig", errors="replace")
        return text.replace(" ", " ").replace("\r\n", "\n").strip()


class AppsScriptTransport(Transport):
    """Zapasowy transport: wlasny web app w Google Apps Script.

    Lzejszy od edytora Dokumentow - przydaje sie, gdy przegladarka Steam Overlay
    nie udzwignie pelnego Google Docs. Kod web appa jest w bridge_appsscript.gs.
    """

    def __init__(self, exec_url: str) -> None:
        if not exec_url:
            raise BridgeError("Brak appsscript_url w config.json.")
        self.exec_url = exec_url
        self.session = requests.Session()

    def read(self) -> str:
        try:
            response = self.session.get(
                self.exec_url, params={"r": "1"}, timeout=15, allow_redirects=True
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise BridgeError(
                f"Nie moge odczytac web appa ({type(exc).__name__}). "
                "Sprawdz 'appsscript_url' i czy wdrozenie ma dostep 'Wszyscy'."
            ) from exc
        return response.text.replace("\r\n", "\n").strip()


def make_transport(config: dict) -> Transport:
    kind = config.get("transport", "gdoc")
    if kind == "gdoc":
        return GoogleDocTransport(config.get("gdoc_id", ""))
    if kind == "appsscript":
        return AppsScriptTransport(config.get("appsscript_url", ""))
    raise BridgeError(f"Nieznany transport: {kind!r} (uzyj 'gdoc' albo 'appsscript').")


MODIFIERS = ("ctrl", "shift", "alt", "windows")


def _clear_modifiers(timeout: float = 2.0) -> None:
    """Doprowadza do stanu, w ktorym zaden modyfikator nie jest wcisniety.

    Bez tego 'shift+tab' wyslane przy trzymanym Ctrl staje sie Ctrl+Shift+Tab
    i overlay sie nie otwiera. Najpierw czekamy, az uzytkownik sam puisci skrot,
    a jesli po czasie cos nadal wisi - zwalniamy to sila.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not any(keyboard.is_pressed(key) for key in MODIFIERS):
            return
        time.sleep(0.02)

    for key in MODIFIERS:
        try:
            keyboard.release(key)
        except Exception:  # noqa: BLE001 - zwalnianie na sile bywa zawodne
            pass


class BoosteroidBridge:
    """Wysyla do okna Boosteroida sekwencje: kopiuj -> overlay -> wklej -> zamknij."""

    def __init__(self, transport: Transport, timing: BridgeTiming, overlay_hotkey: str) -> None:
        self.transport = transport
        self.timing = timing
        self.overlay_hotkey = overlay_hotkey
        self._last_read_error: Exception | None = None

    def _sleep_ms(self, milliseconds: int) -> None:
        time.sleep(milliseconds / 1000.0)

    def _safe_read(self) -> str:
        self._reads = getattr(self, "_reads", 0) + 1
        try:
            return self.transport.read()
        except Exception as exc:  # noqa: BLE001 - chwilowy blad sieci nie przerywa sekwencji
            # Zapamietujemy powod. Bez tego zle udostepniony dokument (403/404)
            # wygladalby po prostu na pusty, a to zupelnie inna diagnoza.
            self._last_read_error = exc
            return ""

    # Odstep rosnie po kazdym nietrafionym odczycie.
    #
    # Staly odstep 0,25 s oznaczal do 48 zapytan do Google na JEDNA wycene,
    # czyli blisko 600 po kilkunastu. Google zaczyna wtedy dlawic endpoint
    # eksportu, odczyty zwalniaja, tekst nie zdaza w oknie z otwartym overlayem,
    # wycena wpada w druga faze i generuje jeszcze wiecej zapytan. Samo sie
    # napedza - stad "po kilkunastu sprawdzeniach zaczyna mulic".
    #
    # Tekst prawie zawsze dociera ponizej sekundy, wiec pierwsze odczyty sa
    # gestsze niz dotad (szybsza sciezka typowa), a rzadsze dopiero pozniej,
    # gdy i tak cos poszlo nie tak.
    POLL_BACKOFF = 1.5
    POLL_MAX_INTERVAL = 1.5

    def _poll_until_changed(self, before: str, budget_s: float) -> tuple[str, bool]:
        """Odpytuje dokument, dopoki tresc sie nie zmieni albo nie wyjdzie czas."""
        deadline = time.monotonic() + budget_s
        interval = self.timing.poll_interval_s
        last = before
        while time.monotonic() < deadline:
            current = self._safe_read()
            if current and current != before:
                return current, True
            last = current
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(interval, remaining))
            interval = min(interval * self.POLL_BACKOFF, self.POLL_MAX_INTERVAL)
        return last, False

    def grab_item_text(self, verbose: bool = False) -> tuple[str, bool]:
        """Zwraca (tekst przedmiotu, czy tresc dokumentu faktycznie sie zmienila).

        Zamiast czekac sztywno po wklejeniu, odpytujemy dokument i zamykamy
        overlay dokladnie w chwili, gdy tekst dotrze. Dzieki temu sekwencja trwa
        tyle, ile naprawde potrzeba, a nie tyle, ile zalozylismy z zapasem.
        """
        _clear_modifiers()
        self._reads = 0
        timing = self.timing
        started = time.monotonic()
        self._last_read_error = None

        # Znaczniki czasu ida do logu ZAWSZE, nie tylko w trybie diagnostycznym.
        # Skarga "wyszukanie trwa dlugo" jest nie do zdiagnozowania bez wiedzy,
        # ktora faza urosla: sekwencja klawiszy czy odpytywanie dokumentu.
        # W buildzie okienkowym log i tak idzie do pliku, wiec nic to nie kosztuje.
        def stamp(label: str) -> None:
            print(f"  [{(time.monotonic() - started) * 1000:6.0f} ms] {label}")

        # Odczyt stanu "przed" nie zalezy od klawiszy, wiec leci rownolegle
        # z kopiowaniem i otwieraniem overlaya - inaczej kosztowalby osobna
        # rundu do Google w czasie, gdy i tak tylko czekamy.
        before_box: list[str] = []
        reader = threading.Thread(
            target=lambda: before_box.append(self._safe_read()), daemon=True
        )
        reader.start()

        if verbose:
            print(f"  okno na wierzchu: {describe_foreground()}")

        stamp("ctrl+c - kopiuje przedmiot spod kursora")
        send_combo("ctrl+c", timing.key_hold_ms)
        self._sleep_ms(timing.after_copy_ms)

        stamp(f"{self.overlay_hotkey} - otwieram Steam Overlay")
        send_combo(self.overlay_hotkey, timing.key_hold_ms)
        self._sleep_ms(timing.overlay_open_ms)

        stamp("ctrl+a - zaznaczam poprzednia tresc")
        send_combo("ctrl+a", timing.key_hold_ms)
        self._sleep_ms(timing.after_select_ms)

        stamp("ctrl+v - wklejam przedmiot")
        send_combo("ctrl+v", timing.key_hold_ms)
        self._sleep_ms(timing.after_paste_ms)

        reader.join(timeout=5.0)
        before_known = bool(before_box)
        before = before_box[0] if before_box else ""
        stamp(f"stan przed sekwencja: {len(before)} znakow"
              if before_known else "stanu przed sekwencja NIE znamy (odczyt nie zdazyl)")

        # Faza 1: czekamy na tekst przy otwartym overlayu, ale nie w nieskonczonosc -
        # przy awarii nie chcemy zaslaniac gry przez caly timeout.
        text, changed = self._poll_until_changed(before, timing.overlay_poll_s)
        stamp("tekst dotarl" if changed else "brak zmiany, zamykam overlay mimo to")

        send_combo(self.overlay_hotkey, timing.key_hold_ms)
        self._sleep_ms(timing.after_close_ms)
        stamp("overlay zamkniety")

        # Faza 2: jesli jeszcze nie dotarl, dociagamy juz w tle, z gra na wierzchu.
        if not changed:
            remaining = timing.poll_timeout_s - timing.overlay_poll_s
            if remaining > 0:
                text, changed = self._poll_until_changed(before, remaining)
                stamp("tekst dotarl po zamknieciu" if changed else "timeout")

        # Nie znamy stanu sprzed sekwencji, wiec nie wolno twierdzic, ze tresc
        # jest nowa - przy pustym "before" kazdy niepusty dokument wygladalby na
        # swiezy, nawet gdyby siedzial w nim poprzedni przedmiot.
        if not before_known:
            changed = False

        stamp(f"KONIEC: {self._reads} odczytow dokumentu, "
              f"{'tresc nowa' if changed else 'BEZ ZMIANY'}")

        if not text and self._last_read_error is not None:
            raise BridgeError(str(self._last_read_error))

        return text, changed
