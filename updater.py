"""Sprawdzenie nowej wersji + opcjonalna cicha auto-aktualizacja (Windows).

Program dziala czesto z prawami administratora (globalny hook klawiatury), a
proces, ktory sam sobie sciaga i podmienia .exe, to dokladnie wzorzec, na
ktory reaguja antywirusy - a build i tak juz nie jest podpisany cyfrowo (patrz
SIGNING-POLICY.md), wiec kazdy dodatkowy powod do podejrzliwosci kosztuje.
Dlatego auto-aktualizacja jest zabezpieczona na kilku poziomach:

- dziala TYLKO na spakowanym (frozen) buildzie Windows - w dev-runie z
  Pythona sys.executable to interpreter, nie nasz .exe, wiec podmiana
  niczego by nie dala i moglaby tylko zaszkodzic.
- pobrane archiwum jest weryfikowane sumą SHA-256 opublikowana WEWNATRZ TEGO
  SAMEGO archiwum (CZYTAJ-TO.txt, patrz package.py) - chroni przed uciete/
  uszkodzone pobranie, nie przed podmiane calego wydania (to i tak ten sam
  serwer/HTTPS co reszta programu).
- podmiana pliku i restart ida przez maly .bat, ktory czeka az NASZ proces
  faktycznie sie skonczy (PID znika z tasklist), dopiero wtedy przenosi
  nowy plik na miejsce starego i odpala go ponownie - .exe nie da sie
  nadpisac, dopoki dziala.
- kazdy blad na dowolnym etapie (siec, zly zip, zla suma, brak uprawnien do
  zapisu) po cichu spada z powrotem do starego zachowania: sam banner z
  linkiem do strony wydania, klikniecie = swiadoma decyzja uzytkownika.

Sprawdzenie wersji leci w watku demona i polyka wszystkie wyjatki: brak sieci
nie moze opoznic startu ani wywalic programu.
"""

import hashlib
import io
import os
import re
import subprocess
import sys
import threading
import zipfile
from pathlib import Path

import requests

# Adres pliku z wersja. Skladany z telemetry_url, zeby nie trzymac drugiego
# adresu w config.json - kto postawi wlasna kopie strony, dostanie i jedno,
# i drugie bez dodatkowej konfiguracji.
DEFAULT_MANIFEST = "https://poepricecheck.eu/version.json"
TIMEOUT = 6
DOWNLOAD_TIMEOUT = 60

VERSION_RE = re.compile(r"^\d+(?:\.\d+)*$")
EXE_NAME = "poe-price-check.exe"
CHECKSUM_RE = re.compile(
    rf"SHA-256\)\s*{re.escape(EXE_NAME)}:\r?\n([0-9a-f]{{64}})"
)


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


def _download_and_verify(download_url: str, user_agent: str) -> bytes | None:
    """Sciaga archiwum wydania, zwraca bajty .exe po udanej weryfikacji sumy,
    albo None przy jakimkolwiek problemie (brak sieci, zly zip, zla suma)."""
    try:
        headers = {}
        if user_agent:
            headers["User-Agent"] = user_agent
        response = requests.get(
            download_url, headers=headers, timeout=DOWNLOAD_TIMEOUT
        )
        response.raise_for_status()
    except requests.RequestException:
        return None
    try:
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            exe_bytes = archive.read(EXE_NAME)
            readme = archive.read("CZYTAJ-TO.txt").decode(
                "utf-8", errors="replace"
            )
    except (zipfile.BadZipFile, KeyError):
        return None
    match = CHECKSUM_RE.search(readme)
    if not match or hashlib.sha256(exe_bytes).hexdigest() != match.group(1):
        return None
    return exe_bytes


def _apply_update(exe_bytes: bytes) -> bool:
    """Zapisuje nowy .exe obok starego i odpala .bat, ktory podmieni go
    dopiero PO zakonczeniu tego procesu (plik dziala, dopoki go nie zamkniemy).
    True = udalo sie zaplanowac restart, caller powinien teraz zamknac okno.
    """
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return False
    target = Path(sys.executable).resolve()
    staging = target.with_name(target.stem + ".new.exe")
    script = target.with_name(target.stem + ".update.bat")
    try:
        staging.write_bytes(exe_bytes)
    except OSError:
        return False

    pid = os.getpid()
    log = target.with_name(target.stem + ".update.log")
    try:
        # newline="" jest tu obowiazkowe: bez tego write_text w trybie
        # tekstowym na Windows i tak tlumaczy kazde '\n' na '\r\n', a nasz
        # string juz ma '\r\n' wpisane na sztywno - bez wylaczenia tego
        # tlumaczenia kazda linia dostawalaby podwojne zakonczenie ('\r\r\n'),
        # co cmd.exe czyta jako puste linie miedzy komendami (nieszkodliwe
        # samo w sobie, ale znak, ze plik nie jest tym, czego oczekiwalismy -
        # zlapane przy weryfikacji zawartosci wygenerowanego .bat).
        #
        # "timeout" do odczekania sekundy NIE dziala tutaj - ten konkretny
        # program w Windows wymaga prawdziwej konsoli i pod CREATE_NO_WINDOW
        # (bez konsoli) konczy sie od razu bledem "Input redirection is not
        # supported". "ping -n 2 127.0.0.1" to standardowy zamiennik w
        # batchach wlasnie z tego powodu - nie dotyka konsoli w ogole.
        #
        # Kazdy krok dopisuje sie do osobnego logu (>> "{log}" 2>&1) - bez
        # tego jedyny slad po nieudanej probie to porzucone .new.exe/.bat,
        # bez zadnej wskazowki dlaczego (a "terminal mignal i zniknal" nie
        # daje sie zdiagnozowac z poziomu Pythona, ktory juz nie zyje).
        script.write_text(
            "\r\n".join([
                "@echo off",
                f'echo [%date% %time%] start, czekam na PID {pid} > "{log}"',
                ":wait",
                f'tasklist /FI "PID eq {pid}" 2>NUL | find "{pid}" >NUL',
                "if not errorlevel 1 (",
                "  ping -n 2 127.0.0.1 >NUL",
                "  goto wait",
                ")",
                f'echo [%date% %time%] PID zniknal, przenosze plik >> "{log}"',
                f'move /Y "{staging}" "{target}" >> "{log}" 2>&1',
                f'echo [%date% %time%] move errorlevel=%errorlevel% >> "{log}"',
                f'start "" "{target}"',
                f'echo [%date% %time%] odpalono ponownie >> "{log}"',
                'del "%~f0"',
                "",
            ]),
            encoding="ascii",
            newline="",
        )
    except OSError:
        return False

    try:
        # TYLKO CREATE_NO_WINDOW - polaczenie z DETACHED_PROCESS jest wprost
        # udokumentowane przez Microsoft jako niedozwolone ("This flag cannot
        # be used with DETACHED_PROCESS") i w praktyce dawalo migajaca konsole,
        # ktora znikala, zanim .bat zdazyl cokolwiek zrobic - zamiast po cichu
        # zaplanowanego restartu.
        subprocess.Popen(
            ["cmd", "/c", str(script)],
            creationflags=subprocess.CREATE_NO_WINDOW,
            close_fds=True,
        )
    except OSError:
        return False
    return True


class UpdateCheck:
    """Sprawdzenie wersji w tle + (opcjonalnie) cicha auto-aktualizacja.

    Wynik "jest nowsza wersja, tu masz link" odbiera sie przez result().
    restart_pending() mowi, czy trwa juz podmiana pliku - w tym stanie
    main.py ma pokazac krotki komunikat i zamknac okno, zeby .bat mogl
    dokonczyc podmiane i odpalic program ponownie.
    """

    def __init__(self, config: dict, current: str, user_agent: str = "") -> None:
        self.url = manifest_url(config)
        self.current = current
        self.user_agent = user_agent
        self.enabled = config.get("update_check", True) and bool(self.url)
        # Domyslnie wlaczone razem z samym sprawdzaniem - kto chce tylko
        # baner bez cichej podmiany pliku, ustawia "auto_update": false.
        self.auto_update_wanted = config.get("auto_update", True)
        self._result: dict | None = None
        self._manifest: dict = {}
        self._restart_pending = False
        self._pending_version = ""
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
                # pobieranie, ktorego uzytkownik sie nie spodziewa. Ten sam
                # link zostaje jako fallback, gdyby auto-aktualizacja z
                # jakiegokolwiek powodu nie wyszla.
                "url": str(data.get("notes") or data.get("page") or ""),
            }
        print(f"[aktualizacja] dostepna wersja {version} (masz {self.current})")

        download_url = str(data.get("download") or "")
        if self.auto_update_wanted and download_url:
            self._try_auto_update(download_url, version)

    def _try_auto_update(self, download_url: str, version: str) -> None:
        exe_bytes = _download_and_verify(download_url, self.user_agent)
        if exe_bytes is None:
            print("[aktualizacja] auto-aktualizacja nie wyszla - zostaje link "
                  "do recznego pobrania.")
            return
        if not _apply_update(exe_bytes):
            return
        with self._lock:
            self._restart_pending = True
            self._pending_version = version
        print(f"[aktualizacja] {version} pobrana i zweryfikowana - restart "
              "po zamknieciu okna.")

    def start(self) -> None:
        if not self.enabled:
            return
        threading.Thread(target=self._fetch, daemon=True).start()

    def result(self) -> dict | None:
        with self._lock:
            return self._result

    def restart_pending(self) -> str:
        """Pusty tekst - nic, w przeciwnym razie numer wersji czekajacej na
        restart. main.py sprawdza to co obrot pompy zdarzen."""
        with self._lock:
            return self._pending_version if self._restart_pending else ""

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
