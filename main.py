"""Price check dla Path of Exile 1 przy grze przez Boosteroida.

Uruchomienie:
    python main.py                 - normalna praca (skrot globalny)
    python main.py --paste         - wycen to, co masz w LOKALNYM schowku
    python main.py --test-read     - sprawdz sam odczyt dokumentu-mostu
    python main.py --test-sequence - wykonaj pelna sekwencje i pokaz co przyszlo
    python main.py --leagues       - wypisz dostepne ligi
"""

import argparse
import json
import queue
import shutil
import sys
import threading
import time
import traceback
from dataclasses import fields

import applog
import hotkeys
import i18n
from bridge import BoosteroidBridge, BridgeError, BridgeTiming, make_transport
from i18n import t
from item_parser import ItemParseError, parse_item
from overlay import ResultWindow
from paths import APP_DIR, APP_VERSION, resource_path
from setup_window import SetupWindow, needs_setup
from status_window import StatusWindow
from telemetry import Telemetry
from trade_api import TradeClient, TradeError
from updater import UpdateCheck
from winutil import (
    describe_foreground,
    foreground_hwnd,
    hwnd_is_own_process,
    is_admin,
    read_clipboard_text,
    set_foreground,
)

CONFIG_PATH = APP_DIR / "config.json"

PERMANENT_LEAGUES = {"Standard", "Hardcore", "Ruthless", "Hardcore Ruthless"}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        # Pierwsze uruchomienie: rozpakuj wzorzec obok programu. Uzupelnieniem
        # zajmie sie kreator, nie komunikat w konsoli.
        example = resource_path("config.example.json")
        if not example.exists():
            raise SystemExit(f"Brak {CONFIG_PATH} i brak wzorca do rozpakowania.")
        shutil.copyfile(example, CONFIG_PATH)
    try:
        # utf-8-sig, a nie utf-8: Notatnik i PowerShell zapisuja UTF-8 z BOM-em,
        # a config jest plikiem, ktory uzytkownik edytuje recznie.
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Blad skladni w {CONFIG_PATH}: {exc}")


def save_config(config: dict) -> None:
    """Zapisuje config z powrotem. Uzywane do zapamietania identyfikatora instalacji."""
    CONFIG_PATH.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def configure_console() -> None:
    """Przestawia konsole na UTF-8.

    Domyslnie jest to cp1250, a nicki graczy potrafia zawierac znaki spoza tej
    strony kodowej - wtedy zwykly print wywala UnicodeEncodeError i kladzie caly
    program. errors='replace' to dodatkowa siatka, gdyby terminal nie udzwignal.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def build_timing(timing_cfg: dict) -> BridgeTiming:
    """Buduje BridgeTiming, ignorujac klucze, ktorych ta wersja nie zna.

    Config zyje obok programu i bywa nowszy albo starszy od binarki. Nieznany
    klucz ma byc ostrzezeniem, a nie wywroceniem calego programu.
    """
    if not timing_cfg:
        return BridgeTiming()

    known = {field.name for field in fields(BridgeTiming)}
    unknown = sorted(set(timing_cfg) - known)
    if unknown:
        print(f"[uwaga] nieznane klucze w sekcji 'timing': {', '.join(unknown)} - pomijam.")

    accepted = {key: value for key, value in timing_cfg.items() if key in known}
    try:
        return BridgeTiming(**accepted)
    except (TypeError, ValueError) as exc:
        print(f"[uwaga] sekcja 'timing' jest niepoprawna ({exc}) - uzywam domyslnych.")
        return BridgeTiming()


def resolve_league(config: dict) -> str:
    league = config.get("league", "auto")
    if league and league != "auto":
        return league
    leagues = TradeClient.fetch_leagues(config["user_agent"])
    for name in leagues:
        if name not in PERMANENT_LEAGUES and not name.startswith(("SSF", "HC ", "Hardcore", "Ruthless")):
            return name
    return "Standard"


def read_local_clipboard() -> str:
    return read_clipboard_text()


class PriceChecker:
    """Spina most, parser i API trade'a; wyniki oddaje przez kolejke do GUI."""

    def __init__(self, config: dict, league: str, telemetry: Telemetry | None = None) -> None:
        self.config = config
        self.telemetry = telemetry or Telemetry({}, lambda _cfg: None, APP_VERSION)
        self.client = TradeClient(
            league=league,
            user_agent=config["user_agent"],
            poesessid=config.get("poesessid", ""),
            status=config.get("search_status", "any"),
            # Limity GGG potrafia wymusic kilkanascie sekund przerwy. Bez tego
            # komunikatu okno po prostu zamiera i wyglada na zawieszone.
            on_wait=lambda left: self.events.put(
                ("status", t("res.rate_wait", n=left))),
        )
        self.timing = build_timing(config.get("timing", {}))
        self.events: queue.Queue[tuple] = queue.Queue()
        self._busy = threading.Lock()
        self._bridge: BoosteroidBridge | None = None
        # Ostatnio wyceniany przedmiot - potrzebny, gdy uzytkownik zmieni filtry
        # w oknie i poprosi o powtorzenie wyszukiwania.
        self._last_item = None
        self._last_unmatched = 0
        # Okno gry zapamietane z chwili, gdy bylo na pierwszym planie. Po pierwszej
        # wycenie fokus ma nasz panel, a wtedy klawisze sekwencji trafialyby w niego
        # zamiast do Boosteroida.
        self._game_hwnd = 0
        self.checks_done = 0  # licznik pokazywany w oknie glownym

    @property
    def bridge(self) -> BoosteroidBridge:
        """Most budujemy dopiero przy pierwszym uzyciu - tryb --paste go nie potrzebuje."""
        if self._bridge is None:
            self._bridge = BoosteroidBridge(
                transport=make_transport(self.config),
                timing=self.timing,
                overlay_hotkey=self.config.get("overlay_hotkey", "shift+tab"),
            )
        return self._bridge

    def warm_up(self) -> None:
        """Pobiera slownik statystyk zanim padnie pierwszy skrot."""
        self.client.stat_index()

    # --------------------------------------------------------------- robota

    def check_from_text(self, raw: str, changed: bool = True) -> None:
        item = parse_item(raw)
        self.events.put(("status", f"Szukam: {item.display_name()}"))
        options, unmatched = self.client.analyze_mods(item)
        properties = self.client.property_options(item)
        self._last_item = item
        self._last_unmatched = len(unmatched)
        result = self.client.price_check(
            item, self.config.get("max_listings", 10), options, len(unmatched),
            properties,
        )
        if result.is_exchange:
            # Waluta i karty nie maja modow do filtrowania - lista opcji byla by
            # samym szumem z linii opisowych.
            options, properties = [], []
        self.events.put(("result", item, result, options, properties, changed))

    def research(self, options: list, properties: list) -> None:
        """Powtarza wyszukiwanie po zmianie filtrow w oknie."""
        if self._last_item is None:
            return

        def job() -> None:
            if not self._busy.acquire(blocking=False):
                return
            try:
                self.events.put(("status", "Szukam ponownie..."))
                result = self.client.price_check(
                    self._last_item, self.config.get("max_listings", 10),
                    options, self._last_unmatched, properties,
                )
                self.events.put((
                    "result", self._last_item, result, options, properties, True,
                ))
            except (TradeError, BridgeError) as exc:
                self.events.put(("error", str(exc)))
            except Exception as exc:  # noqa: BLE001 - okno nie moze umrzec na kliknieciu
                traceback.print_exc()
                self.events.put(("error", f"{type(exc).__name__}: {exc}"))
            finally:
                self._busy.release()

        threading.Thread(target=job, daemon=True).start()

    def _yield_focus_to_game(self) -> None:
        """Chowa panel i oddaje pierwszy plan grze przed wyslaniem klawiszy.

        Bez tego druga wycena z rzedu wysyla ctrl+c / f7 / ctrl+v do wlasnego
        panelu, ktory po pierwszej wycenie ma fokus - do chmury nie dociera nic,
        a program czeka pelny timeout na zmiane dokumentu.
        """
        current = foreground_hwnd()
        if current and not hwnd_is_own_process(current):
            self._game_hwnd = current  # gra jest na wierzchu, nic nie trzeba robic
            return

        self.events.put(("hide",))
        time.sleep(0.12)  # daj oknu zniknac, zanim odbierzemy mu fokus
        if self._game_hwnd:
            set_foreground(self._game_hwnd)
            time.sleep(0.15)

    def _run_job(self, use_bridge: bool) -> None:
        if not self._busy.acquire(blocking=False):
            return  # poprzednie sprawdzenie jeszcze trwa
        try:
            if use_bridge:
                self._yield_focus_to_game()
                # Zadnego komunikatu przed sekwencja: pokazanie panelu odebraloby
                # grze pierwszy plan i klawisze poszlyby w nasze okno.
                raw, changed = self.bridge.grab_item_text()
                if not raw:
                    # Most nie oddal tekstu - to jest nieudana wycena, a nie
                    # zdarzenie neutralne. Wczesniej wychodzilo sie stad bez
                    # zliczenia czegokolwiek, wiec najczestsza awaria calego
                    # obejscia przez Boosteroida byla w statystykach niewidoczna.
                    self.telemetry.record_check(ok=False, kind="most_pusty")
                    self.events.put((
                        "error",
                        t("err.bridge_empty"),
                    ))
                    return
            else:
                raw, changed = read_local_clipboard(), True
                if not raw:
                    self.telemetry.record_check(ok=False, kind="schowek_pusty")
                    self.events.put(("error", t("err.clipboard_empty")))
                    return
            self.check_from_text(raw, changed)
            self.checks_done += 1
            # Licznik zasobow do logu - patrz applog.resource_snapshot().
            print(f"[zasoby] wycena {self.checks_done}: {applog.resource_snapshot()}")
            self.telemetry.record_check(ok=True)
        except ItemParseError as exc:
            # Etykieta idzie z wyjatku - patrz ItemParseError.kind.
            self.telemetry.record_check(ok=False, kind=getattr(exc, "kind", ""))
            self.events.put(("error", t("err.item_unknown", error=exc)))
        except (BridgeError, TradeError) as exc:
            # Etykieta idzie z samego wyjatku - patrz TradeError.kind.
            self.telemetry.record_check(ok=False, kind=getattr(exc, "kind", ""))
            self.events.put(("error", str(exc)))
        except Exception as exc:  # noqa: BLE001 - petla nie moze umrzec na skrocie
            # Nazwa klasy wystarczy do rozpoznania, a nie niesie zadnej tresci.
            self.telemetry.record_check(ok=False, kind=type(exc).__name__[:24])
            traceback.print_exc()
            self.events.put(("error", f"{type(exc).__name__}: {exc}"))
        finally:
            self._busy.release()

    def trigger(self, use_bridge: bool = True) -> None:
        threading.Thread(target=self._run_job, args=(use_bridge,), daemon=True).start()


def pump_events(window: ResultWindow, checker: PriceChecker, status=None,
                updates=None) -> None:
    # Cokolwiek by tu nie poszlo nie tak, petla MUSI zostac przeplanowana.
    # Wyjatek, ktory sie z niej wymknie, ubija pompe zdarzen na zawsze i program
    # przestaje reagowac na skroty, wygladajac przy tym na zawieszony.
    try:
        while True:
            event = checker.events.get_nowait()
            kind = event[0]
            if status is not None:
                status.flash()  # widac, ze program wlasnie cos robi
                status.set_checks(checker.checks_done)
            if kind == "hide":
                window.hide()
            elif kind == "status":
                window.show_status(event[1])
            elif kind == "error":
                window.show_error(event[1])
            elif kind == "result":
                _, item, result, options, properties, changed = event
                window.show_result(item, result, options=options,
                                   properties=properties, stale=not changed)
                if not changed:
                    print("[uwaga] tresc dokumentu sie nie zmienila - to zapewne "
                          "POPRZEDNI przedmiot. Uruchom --test-sequence.")
    except queue.Empty:
        pass
    except Exception:  # noqa: BLE001 - patrz komentarz wyzej
        traceback.print_exc()
    finally:
        # Sprawdzenie wersji konczy sie w watku w tle, a widgetow Tk nie wolno
        # tworzyc spoza watku glownego - dlatego wynik odbieramy tutaj.
        # show_update() sam pilnuje, zeby pokazac pasek tylko raz, wiec nawet
        # gdyby sie wywrocil, kolejne obroty petli tego nie powtorza.
        try:
            if updates is not None and status is not None:
                status.set_discord(updates.discord())
                found = updates.result()
                if found:
                    status.show_update(found["version"], found["url"])
        except Exception:  # noqa: BLE001 - powiadomienie nie moze ubic pompy
            traceback.print_exc()
        window.root.after(60, pump_events, window, checker, status, updates)


def run_gui(config: dict, league: str) -> int:
    telemetry = Telemetry(config, save_config, APP_VERSION)
    telemetry.set_league(league)
    checker = PriceChecker(config, league, telemetry)

    print(f"poe-price-check {APP_VERSION}")
    print(f"Liga: {league}")
    if telemetry.notice():
        print(telemetry.notice())
    if sys.platform == "win32" and not is_admin():
        print("[uwaga] Program NIE dziala jako administrator. Jesli klawisze nie beda")
        print("        docieraly do Boosteroida, uruchom go z prawami administratora.")
    elif sys.platform == "darwin":
        print("[uwaga] Na macOS System Events (uzywany do przelaczania okien i")
        print("        odczytu okna na wierzchu) wymaga uprawnienia Accessibility.")
        print("        Ustawienia systemowe -> Prywatnosc i ochrona -> Dostepnosc.")
    print("Pobieram slownik statystyk...")
    checker.warm_up()

    hotkey = config.get("hotkey", "ctrl+d")
    local_hotkey = config.get("local_clipboard_hotkey", "ctrl+alt+d")
    quit_hotkey = config.get("quit_hotkey", "ctrl+alt+q")

    def _save_boosteroid_mode(enabled: bool) -> None:
        config["boosteroid_mode"] = enabled
        save_config(config)

    status = StatusWindow(
        league=league,
        hotkeys={"hotkey": hotkey, "local": local_hotkey, "quit": quit_hotkey},
        on_quit=telemetry.stop,
        boosteroid_mode=bool(config.get("boosteroid_mode", True)),
        on_boosteroid_mode_change=_save_boosteroid_mode,
    )
    # Okno wyniku jest podrzedne wobec glownego - jeden obiekt Tk na proces.
    window = ResultWindow(
        parent=status.root,
        on_search=checker.research,
        close_on_focus_loss=config.get("close_on_focus_loss", True),
    )

    # status.boosteroid_mode czytany W CHWILI wcisniecia skrotu, nie raz przy
    # starcie - przelacznik w oknie dziala od razu, bez restartu programu.
    hotkeys.add_hotkey(hotkey, lambda: checker.trigger(use_bridge=status.boosteroid_mode))
    hotkeys.add_hotkey(local_hotkey, lambda: checker.trigger(use_bridge=False))
    # Skrot leci z watku biblioteki keyboard, a Tk wolno dotykac tylko z watku
    # glownego - dlatego zamkniecie przekazujemy przez kolejke zdarzen Tk.
    hotkeys.add_hotkey(quit_hotkey, lambda: status.root.after(0, status.root.quit))

    print(f"  {hotkey:<12} wycen przedmiot pod kursorem (przez Boosteroida)")
    print(f"  {local_hotkey:<12} wycen zawartosc lokalnego schowka")
    print(f"  {quit_hotkey:<12} wyjscie")
    print("Gotowe.")

    updates = UpdateCheck(config, APP_VERSION, config.get("user_agent", ""))
    updates.start()

    telemetry.start()
    status.root.after(60, pump_events, window, checker, status, updates)
    status.root.mainloop()
    telemetry.stop()  # ostatni sygnal, zeby nie zgubic licznika z tej sesji
    return 0


def main() -> int:
    # Program jest okienkowy, wiec konsola istnieje tylko dla trybow testowych.
    # Bez tego sys.stdout byloby None i pierwszy print wywrocilby wszystko.
    applog.setup(has_cli_args=len(sys.argv) > 1)
    configure_console()
    parser = argparse.ArgumentParser(description="PoE1 price check przez Boosteroida")
    parser.add_argument("--paste", action="store_true",
                        help="wycen zawartosc lokalnego schowka i zakoncz")
    parser.add_argument("--test-read", action="store_true",
                        help="odczytaj dokument-most i wypisz jego tresc")
    parser.add_argument("--test-sequence", action="store_true",
                        help="wykonaj pelna sekwencje klawiszy i pokaz wynik")
    parser.add_argument("--leagues", action="store_true", help="wypisz ligi")
    parser.add_argument("--test-keys", action="store_true",
                        help="sprawdz, czy syntetyczne klawisze docieraja do Boosteroida")
    args = parser.parse_args()

    config = load_config()
    # Jezyk z configu, a przy pierwszym uruchomieniu z ustawien Windows -
    # uzytkownik ma zobaczyc swoj jezyk, zanim cokolwiek kliknie.
    i18n.set_language(config.get("language") or i18n.detect_default())

    if args.leagues:
        for name in TradeClient.fetch_leagues(config["user_agent"]):
            print(name)
        return 0

    if args.test_keys:
        import time

        overlay_hotkey = config.get("overlay_hotkey", "shift+tab")
        print("=" * 64)
        print("TEST: czy nasze klawisze w ogole docieraja do sesji Boosteroida")
        print("=" * 64)
        print(f"Uprawnienia administratora: {'TAK' if is_admin() else 'NIE'}")
        if sys.platform == "win32" and not is_admin():
            print("  ^ jesli test wypadnie negatywnie, uruchom program jako administrator:")
            print("    prawy przycisk na .exe -> 'Uruchom jako administrator'")
        elif sys.platform == "darwin":
            print("  ^ jesli test wypadnie negatywnie, sprawdz uprawnienie Accessibility")
            print("    dla Terminala/Pythona w Ustawieniach systemowych.")
        print()
        print("Przelacz sie teraz na okno Boosteroida i PATRZ NA EKRAN GRY.")

        def countdown(seconds: int) -> None:
            for remaining in range(seconds, 0, -1):
                print(f"  ...{remaining} ", end="\r", flush=True)
                time.sleep(1)
            print(" " * 20, end="\r")

        countdown(8)
        print(f"okno na wierzchu: {describe_foreground()}\n")

        print("[A] wysylam 'i' - w PoE to przelacza ekwipunek.")
        hotkeys.send("i")
        time.sleep(3)
        print("    Czy ekwipunek sie przelaczyl?\n")

        print(f"[B] wysylam '{overlay_hotkey}' - to powinno otworzyc Steam Overlay.")
        hotkeys.send(overlay_hotkey)
        time.sleep(3)
        print("    Czy overlay sie otworzyl?\n")

        print("-" * 64)
        print("JAK CZYTAC WYNIK:")
        print("  [A] nie, [B] nie -> klawisze nie docieraja w ogole. Uruchom jako")
        print("                      administrator. Jesli nadal nie - klient Boosteroida")
        print("                      ignoruje syntetyczne wejscie i ta droga odpada.")
        print("  [A] tak, [B] nie -> klawisze docieraja do gry, ale Steam Overlay nie")
        print("                      reaguje. Sprawdz skrot overlaya w Steamie i ustaw")
        print("                      go w config.json jako 'overlay_hotkey'.")
        print("  [A] tak, [B] tak -> wejscie dziala, problem jest w czasach albo w tym,")
        print("                      gdzie stoi kursor w dokumencie.")
        return 0

    if args.test_read:
        transport = make_transport(config)
        text = transport.read()
        print(f"--- {len(text)} znakow ---")
        print(text or "(pusto)")
        return 0

    league = resolve_league(config)

    if args.test_sequence:
        import time

        checker = PriceChecker(config, league)
        print("Przelacz sie na okno Boosteroida i najedz kursorem na przedmiot.")
        print("PATRZ NA EKRAN GRY - zobaczysz, ktory krok nie przechodzi.\n")
        for remaining in range(8, 0, -1):
            print(f"  start za {remaining}...", end="\r", flush=True)
            time.sleep(1)
        print(" " * 30, end="\r")

        raw, changed = checker.bridge.grab_item_text(verbose=True)

        print(f"\nDokument PO sekwencji: {len(raw)} znakow")
        print("-" * 60)
        print(raw or "(pusto)")
        print("-" * 60)
        if changed:
            print("WYNIK: OK - dokument zostal nadpisany nowym przedmiotem.")
        elif not raw:
            print("WYNIK: dokument jest PUSTY. Nic sie do niego nie zapisalo -\n"
                  "       sprawdz krok [2] (czy overlay sie otworzyl) i [4] (czy kursor\n"
                  "       stoi w tresci dokumentu, a nie w pasku adresu).")
        else:
            print("WYNIK: dokument sie NIE zmienil - zostala w nim stara tresc.\n"
                  "       Jesli na ekranie gry overlay sie NIE otworzyl -> problem z krokiem [2]:\n"
                  "         zwieksz 'overlay_open_ms', sprawdz skrot 'overlay_hotkey'.\n"
                  "       Jesli overlay sie otworzyl, ale tekst nie wskoczyl -> krok [3]/[4]:\n"
                  "         kliknij raz w tresc dokumentu i zwieksz 'after_paste_ms'.")
        return 0

    if not args.paste and needs_setup(config):
        # Kreator zamiast komunikatu "uzupelnij gdoc_id" - uzytkownik dostal sam
        # plik .exe i nie ma powodu wiedziec, czym jest plik konfiguracyjny.
        window = SetupWindow(config)
        if not window.run():
            return 0
        save_config(config)

    if args.paste:
        raw = read_local_clipboard()
        if not raw:
            print("Lokalny schowek jest pusty.")
            return 1
        checker = PriceChecker(config, league)
        item = parse_item(raw)
        result = checker.client.price_check(item, config.get("max_listings", 10))
        print(f"{item.display_name()}  [{item.rarity}]  liga {result.league}")
        print(f"mody w filtrze: {result.mods_used}"
              + (f"  (nierozpoznane: {result.mods_unmatched})" if result.mods_unmatched else ""))
        if result.total == 0 and result.mods_used:
            print("UWAGA: nikt nie wystawil przedmiotu z takim zestawem modow.")
        print(f"ofert: {result.total}")
        for listing in result.listings:
            print(f"  {listing.price_text():>16}  {listing.account}")
        print(result.browser_url())
        return 0

    return run_gui(config, league)


if __name__ == "__main__":
    # Limit zapytan czy zerwana siec to normalne sytuacje, a nie awaria programu -
    # maja wygladac jak komunikat, a nie jak traceback.
    try:
        sys.exit(main())
    except (TradeError, BridgeError) as exc:
        print(f"\nBlad: {exc}")
        sys.exit(1)
    except ItemParseError as exc:
        print(f"\nNie rozpoznaje przedmiotu: {exc}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nPrzerwane.")
        sys.exit(130)
