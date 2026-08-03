"""Sprawdzenie, czy jest nowsza wersja - bez samoczynnej podmiany plikow.

Program NIE aktualizuje sie sam i nie pobiera niczego w tle. Powod jest
praktyczny: aplikacja bywa uruchamiana z prawami administratora, a proces,
ktory sam sobie sciaga i podmienia .exe, to dokladnie ten wzorzec, na ktory
reaguja antywirusy. Zamiast tego pokazujemy informacje i otwieramy strone
wydania w przegladarce - pobranie zostaje swiadoma decyzja uzytkownika.

Sprawdzenie leci w watku demona i polyka wszystkie wyjatki: brak sieci nie
moze opoznic startu ani wywalic programu.
"""

import re
import threading

import requests

# Adres pliku z wersja. Skladany z telemetry_url, zeby nie trzymac drugiego
# adresu w config.json - kto postawi wlasna kopie strony, dostanie i jedno,
# i drugie bez dodatkowej konfiguracji.
DEFAULT_MANIFEST = "https://poepricecheck.eu/version.json"
TIMEOUT = 6

VERSION_RE = re.compile(r"^\d+(?:\.\d+)*$")


def parse_version(text: str) -> tuple[int, ...]:
    """'1.0.10' -> (1, 0, 10). Nierozpoznany zapis daje pusta krotke.

    Porownanie tekstowe nie wchodzi w gre: '1.0.9' > '1.0.10' przy zwyklym
    porownaniu napisow, wiec dziesiata poprawka nigdy by sie nie pokazala.
    """
    text = (text or "").strip().lstrip("v")
    if not VERSION_RE.match(text):
        return ()
    return tuple(int(part) for part in text.split("."))


def is_newer(candidate: str, current: str) -> bool:
    """Czy candidate jest nowsza niz current."""
    new, old = parse_version(candidate), parse_version(current)
    if not new or not old:
        return False
    # Rozne dlugosci: 1.1 i 1.1.0 to ta sama wersja, wiec dopelniamy zerami.
    length = max(len(new), len(old))
    new += (0,) * (length - len(new))
    old += (0,) * (length - len(old))
    return new > old


def manifest_url(config: dict) -> str:
    """Adres version.json wyprowadzony z telemetry_url albo domyslny."""
    explicit = (config.get("update_url") or "").strip()
    if explicit:
        return explicit
    telemetry = (config.get("telemetry_url") or "").strip()
    if "/api/" in telemetry:
        return telemetry.split("/api/", 1)[0] + "/version.json"
    return DEFAULT_MANIFEST


class UpdateCheck:
    """Jednorazowe sprawdzenie wersji w tle.

    Wynik odbiera sie przez result() - zwraca None, dopoki nie ma odpowiedzi
    albo gdy nic nowego nie ma.
    """

    def __init__(self, config: dict, current: str, user_agent: str = "") -> None:
        self.url = manifest_url(config)
        self.current = current
        self.user_agent = user_agent
        self.enabled = config.get("update_check", True) and bool(self.url)
        self._result: dict | None = None
        self._manifest: dict = {}
        self._lock = threading.Lock()

    def _fetch(self) -> None:
        try:
            headers = {"Accept": "application/json"}
            if self.user_agent:
                headers["User-Agent"] = self.user_agent
            response = requests.get(self.url, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except Exception:  # noqa: BLE001 - brak sieci to nie awaria programu
            return
        if not isinstance(data, dict):
            return
        with self._lock:
            self._manifest = data

        version = str(data.get("version", ""))
        if not is_newer(version, self.current):
            return
        with self._lock:
            self._result = {
                "version": version,
                # Do przegladarki podajemy strone wydania, a nie bezposredni
                # link do pliku - kliknieciem w link nie powinno startowac
                # pobieranie, ktorego uzytkownik sie nie spodziewa.
                "url": str(data.get("notes") or data.get("page") or ""),
            }
        print(f"[aktualizacja] dostepna wersja {version} (masz {self.current})")

    def start(self) -> None:
        if not self.enabled:
            return
        threading.Thread(target=self._fetch, daemon=True).start()

    def result(self) -> dict | None:
        with self._lock:
            return self._result

    def discord(self) -> str:
        """Adres zaproszenia podany przez strone, albo pusty tekst.

        Aplikacja ma wbudowany adres zapasowy - ten sluzy tylko do podmiany,
        gdyby zaproszenie wygaslo juz po wydaniu wersji.
        """
        with self._lock:
            url = str(self._manifest.get("discord", "") or "")
        # Tylko https i tylko domena Discorda: manifest przychodzi z sieci, a
        # przycisk otwiera przegladarke. Bez tego podmieniony plik na serwerze
        # posrednim mogl by kierowac ludzi gdziekolwiek.
        if url.startswith(("https://discord.gg/", "https://discord.com/invite/")):
            return url
        return ""
