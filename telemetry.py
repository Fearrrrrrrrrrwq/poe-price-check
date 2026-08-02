"""Anonimowy licznik uzyc. Odpowiada na jedno pytanie: ilu ludzi tego uzywa.

Zasady, ktore nie podlegaja negocjacji:
  * nie wysylamy NICZEGO o przedmiotach, cenach, kontach ani wynikach wyszukiwania,
  * nie wysylamy gdoc_id ani POESESSID - to sa dane dostepowe uzytkownika,
  * identyfikator instalacji jest losowy i nie da sie go powiazac z osoba,
  * bez adresu zbiorczego w config.json telemetria w ogole nie startuje,
  * awaria wysylki nigdy nie moze zaklocic dzialania programu.

Wysylka leci w watku demona z krotkim timeoutem i polyka wszystkie wyjatki.
"""

import platform
import threading
import time
import uuid

import requests

import i18n

HEARTBEAT_SECONDS = 6 * 3600  # sygnal zycia co 6 godzin dzialania
SEND_TIMEOUT = 8


class Telemetry:
    """Licznik uzyc. Bez skonfigurowanego adresu jest calkowicie bierny."""

    def __init__(self, config: dict, save_config, version: str) -> None:
        self.url = (config.get("telemetry_url") or "").strip()
        self.enabled = bool(self.url) and config.get("telemetry", True)
        self.version = version
        self.league = ""
        self.transport = config.get("transport", "gdoc")

        self._checks = 0
        self._failures = 0
        self._lock = threading.Lock()
        self._started = time.monotonic()
        self._stop = threading.Event()

        # Identyfikator instalacji: losowy, tworzony raz i zapisywany lokalnie.
        # Nie ma zwiazku z kontem, nickiem ani sprzetem.
        self.install_id = config.get("install_id") or ""
        if self.enabled and not self.install_id:
            self.install_id = uuid.uuid4().hex
            config["install_id"] = self.install_id
            try:
                save_config(config)
            except Exception:  # noqa: BLE001 - brak zapisu nie moze nic zepsuc
                pass

    # ------------------------------------------------------------- liczniki

    def record_check(self, ok: bool) -> None:
        """Zlicza wycene. NIE zapisuje, czego dotyczyla."""
        if not self.enabled:
            return
        with self._lock:
            if ok:
                self._checks += 1
            else:
                self._failures += 1

    def set_league(self, league: str) -> None:
        self.league = league

    # -------------------------------------------------------------- wysylka

    def _payload(self) -> dict:
        with self._lock:
            checks, failures = self._checks, self._failures
            self._checks = self._failures = 0
        return {
            "id": self.install_id,
            "version": self.version,
            "os": f"{platform.system()} {platform.release()}",
            "league": self.league,
            "language": i18n.current(),
            "transport": self.transport,
            "checks": checks,
            "failures": failures,
            "uptime_min": int((time.monotonic() - self._started) / 60),
        }

    def _send(self) -> None:
        try:
            requests.post(self.url, json=self._payload(), timeout=SEND_TIMEOUT)
        except Exception:  # noqa: BLE001 - telemetria nigdy nie przerywa pracy
            pass

    def _loop(self) -> None:
        self._send()  # sygnal startu
        while not self._stop.wait(HEARTBEAT_SECONDS):
            self._send()

    def start(self) -> None:
        if not self.enabled:
            return
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self) -> None:
        """Ostatni sygnal przy zamykaniu, zeby nie zgubic licznika z sesji."""
        if not self.enabled:
            return
        self._stop.set()
        self._send()

    # ------------------------------------------------------------ komunikat

    def notice(self) -> str:
        if not self.url:
            return ""
        if not self.enabled:
            return "Telemetria: wylaczona."
        return (
            "Telemetria: wysylam anonimowy licznik uzyc (wersja, liga, liczba wycen).\n"
            "            Zadnych przedmiotow, cen ani danych konta. Wylaczysz przez\n"
            '            "telemetry": false w config.json.'
        )
