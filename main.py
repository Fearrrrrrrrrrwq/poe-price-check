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
import webbrowser
from dataclasses import fields

import applog
import hotkeys
import i18n
from bridge import BoosteroidBridge, BridgeError, BridgeTiming, make_transport, send_combo
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
    game = config.get("game_version", "poe1")
    league = config.get("league", "auto")
    leagues: list[str] | None = None
    if league and league != "auto":
        # Nazwa ligi wpisana na sztywno w configu moze pochodzic sprzed
        # przelaczenia wersji gry (np. "Allflame" zostaje w configu, ktos
        # zmienia game_version na poe2, a "Allflame" nigdy nie istnialo w
        # PoE2) - wysylanie jej pod /api/trade2/ konczy sie HTTP 400
        # "Invalid query", ktore wyglada jak awaria programu, a jest tylko
        # nieaktualnym ustawieniem. Zamiast slepo ufac configowi, sprawdzamy
        # liste prawdziwych lig danej gry i dopiero wtedy uznajemy ja za dobra.
        try:
            leagues = TradeClient.fetch_leagues(config["user_agent"], game=game)
        except TradeError:
            return league  # brak sieci - lepiej sprobowac niz od razu poddac sie
        if league in leagues:
            return league
        print(f"[uwaga] liga '{league}' z configu nie istnieje w {game.upper()} - "
              "dobieram automatycznie.")
    if leagues is None:
        leagues = TradeClient.fetch_leagues(config["user_agent"], game=game)
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
        self.events: queue.Queue[tuple] = queue.Queue()
        self.client = self._build_client(league, config.get("game_version", "poe1"))
        self.timing = build_timing(config.get("timing", {}))
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

    def _build_client(self, league: str, game: str) -> TradeClient:
        return TradeClient(
            league=league,
            user_agent=self.config["user_agent"],
            poesessid=self.config.get("poesessid", ""),
            status=self.config.get("search_status", "any"),
            # Limity GGG potrafia wymusic kilkanascie sekund przerwy. Bez tego
            # komunikatu okno po prostu zamiera i wyglada na zawieszone.
            on_wait=lambda left: self.events.put(
                ("status", t("res.rate_wait", n=left))),
            game=game,
        )

    def switch_game(self, game: str, league: str) -> None:
        """Podmienia TradeClient na nowa gre/lige w locie - bez restartu i
        bez kasowania configu (patrz status_window.game_switched()). Stary
        klient (z jego cache statystyk/baz danych) po prostu odpada, nowy
        buduje swoj wlasny - oba sa juz i tak rozdzielone cache'em per gra
        (patrz trade_api.TradeClient._cached).
        """
        self.client = self._build_client(league, game)
        self.config["game_version"] = game
        self.config["league"] = league
        # Poprzedni przedmiot pochodzi z innej gry - powtorzenie wyszukiwania
        # (np. po zmianie filtrow w oknie) musialoby isc przez slownik
        # statystyk gry, z ktorej NIE pochodzi ten przedmiot.
        self._last_item = None
        self._last_unmatched = 0

    def copy_combo(self) -> str:
        """Kombinacja kopiujaca przedmiot w grze.

        PoE1 od 3.29 kopiuje ZAWSZE w formacie zaawansowanym (adnotacje
        { Prefix Modifier ... } z rodzajem moda i tierem) - wystarczy zwykle
        Ctrl+C. PoE2 daje ten format tylko z klawiszem "pokaz szczegoly modow"
        (domyslnie Alt), stad Ctrl+Alt+C. Tak samo robia Awakened PoE Trade i
        Exiled Exchange 2. "copy_combo" w configu nadpisuje oba.
        """
        explicit = self.config.get("copy_combo")
        if explicit:
            return explicit
        return "ctrl+alt+c" if self.client.game == "poe2" else "ctrl+c"

    @property
    def bridge(self) -> BoosteroidBridge:
        """Most budujemy dopiero przy pierwszym uzyciu - tryb --paste go nie potrzebuje."""
        if self._bridge is None:
            self._bridge = BoosteroidBridge(
                transport=make_transport(self.config),
                timing=self.timing,
                overlay_hotkey=self.config.get("overlay_hotkey", "shift+tab"),
                copy_combo=self.copy_combo(),
            )
        # Gre mozna przelaczyc w locie - kombinacja idzie za nia.
        self._bridge.copy_combo = self.copy_combo()
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

    def research(self, options: list, properties: list,
                any_base: bool = False) -> None:
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
                    options, self._last_unmatched, properties, any_base=any_base,
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

    def check_ceiling(self, item) -> None:
        """Otwiera w przegladarce "sufit" tej bazy - patrz
        TradeClient.craft_ceiling_url(). Nie idzie przez self._busy: to
        lekka, poboczna akcja (jeden POST bez pobierania ofert), nie musi
        czekac na trwajaca wycene ani jej blokowac.
        """
        def job() -> None:
            try:
                url = self.client.craft_ceiling_url(item)
                webbrowser.open(url)
            except (TradeError, BridgeError) as exc:
                self.events.put(("error", str(exc)))
            except Exception as exc:  # noqa: BLE001 - poboczna akcja nie moze ubic programu
                traceback.print_exc()
                self.events.put(("error", f"{type(exc).__name__}: {exc}"))

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

    def _run_job(self, use_bridge: bool, auto_copy: bool = False) -> None:
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
                if auto_copy:
                    # Glowny skrot w trybie lokalnym (checkbox "Uruchom dla
                    # Boosteroid" odznaczony) ma dzialac tak samo wygodnie jak
                    # tryb mostu - najedz i wcisnij, bez recznego Ctrl+C przed
                    # kazda wycena. local_clipboard_hotkey (Ctrl+Alt+D) tego
                    # NIE dostaje - jego sens to wycena tego, co juz jest w
                    # schowku (np. wklejone spoza gry), a nie odswiezanie go.
                    #
                    # _yield_focus_to_game() JEST tu konieczne, nie kosmetyka:
                    # po pierwszej wycenie fokus ma nasze okno wyniku, wiec bez
                    # oddania go z powrotem grze synteyczny Ctrl+C lecialby w
                    # nasz panel, schowek nigdy by sie nie odswiezal i kazda
                    # kolejna wycena czytalaby ten sam, stary tekst - dokladnie
                    # to zglosil tester.
                    self._yield_focus_to_game()
                    # Ta sama kombinacja i ten sam sposob wysylania co w trybie
                    # mostu: modyfikatory WCISNIETE z przytrzymaniem, dopiero
                    # potem C. hotkeys.send() wciska wszystko w zerowym czasie -
                    # dla Ctrl+C gra to lapala, ale Ctrl+Alt+C (PoE2) gubila
                    # i schowek zostawal pusty. Exiled Exchange 2 z tego samego
                    # powodu puszcza modyfikatory z opoznieniem.
                    send_combo(self.copy_combo(), self.timing.key_hold_ms)
                    # Ten sam odstep co po Ctrl+C w trybie mostu
                    # (timing.after_copy_ms, domyslnie 250ms) - lokalny
                    # schowek jest szybszy niz Boosteroid, ale gra wciaz
                    # potrzebuje chwili, zeby go wypelnic.
                    time.sleep(self.timing.after_copy_ms / 1000)
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

    def trigger(self, use_bridge: bool = True, auto_copy: bool = False) -> None:
        threading.Thread(target=self._run_job, args=(use_bridge, auto_copy),
                         daemon=True).start()


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
        restarting = False
        try:
            if updates is not None and status is not None:
                status.set_discord(updates.discord())
                found = updates.result()
                if found:
                    status.show_update(found["version"], found["url"])
                pending_version = updates.restart_pending()
                if pending_version:
                    # Nowy .exe juz lezy obok starego, a .bat czeka tylko na
                    # zamkniecie TEGO procesu (patrz updater._apply_update) -
                    # window.root.quit() konczy mainloop tak samo jak przycisk
                    # "Zakoncz", program zamyka sie normalnie, .bat dokonczy
                    # podmiane i odpali nowa wersje sam.
                    status.show_restarting(pending_version)
                    window.root.after(1200, status.root.quit)
                    restarting = True
        except Exception:  # noqa: BLE001 - powiadomienie nie moze ubic pompy
            traceback.print_exc()
        if not restarting:
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

    # status.boosteroid_mode czytany W CHWILI wcisniecia skrotu, nie raz przy
    # starcie - przelacznik w oknie dziala od razu, bez restartu programu.
    # auto_copy=True w trybie lokalnym: glowny skrot ma dzialac "najedz i
    # wcisnij", tak samo wygodnie jak tryb mostu, gdzie kopiowanie tez robi
    # program. Wyodrebnione do nazwanej funkcji (nie lambda w miejscu
    # rejestracji), zeby _change_hotkey() mogla ja ponownie przypiac pod
    # nowa kombinacja bez duplikowania ciala.
    def _price_check_hotkey() -> None:
        checker.trigger(use_bridge=status.boosteroid_mode,
                        auto_copy=not status.boosteroid_mode)

    def _change_hotkey(new_combo: str) -> bool:
        """Podmienia glowny skrot na zywo, bez restartu. True = udalo sie.

        Nowa kombinacja rejestruje sie PRZED usunieciem starej - jesli sie
        nie uda (zajety kod klawisza, zly format), stary skrot dalej dziala
        zamiast zostawic uzytkownika bez zadnego dzialajacego skrotu.
        """
        nonlocal hotkey
        new_combo = "+".join(
            part.strip().lower() for part in new_combo.split("+") if part.strip()
        )
        if not new_combo or new_combo == hotkey:
            return False
        if new_combo in (local_hotkey, quit_hotkey):
            return False  # kolidowalby z innym juz zajetym skrotem
        try:
            hotkeys.add_hotkey(new_combo, _price_check_hotkey)
        except Exception:  # noqa: BLE001 - zly format/zajety kod klawisza
            return False
        hotkeys.remove_hotkey(hotkey)
        hotkey = new_combo
        config["hotkey"] = new_combo
        save_config(config)
        print(f"  {hotkey:<12} wycen przedmiot pod kursorem (przez Boosteroida) [zmieniono]")
        return True

    def _change_game(new_game: str) -> None:
        """Przelacza PoE1/PoE2 bez restartu i bez kasowania configu.

        resolve_league() robi zapytanie sieciowe (lista lig danej gry), wiec
        leci w watku w tle - inaczej klikniecie przycisku na chwile
        zamrozaloby cale okno. Wynik wraca do watku Tk przez status.root.after,
        tak jak weryfikacja dokumentu w kreatorze (patrz setup_window._verify).
        """
        def job() -> None:
            try:
                new_league = resolve_league({**config, "game_version": new_game,
                                             "league": "auto"})
                checker.switch_game(new_game, new_league)
                save_config(config)
            except TradeError as exc:
                status.root.after(0, status.game_switch_failed, str(exc))
                return
            except Exception as exc:  # noqa: BLE001 - przelacznik nie moze ubic programu
                traceback.print_exc()
                status.root.after(0, status.game_switch_failed,
                                  f"{type(exc).__name__}: {exc}")
                return
            print(f"[gra] przelaczono na {new_game} - liga {new_league}")
            status.root.after(0, status.game_switched, new_game, new_league)

        threading.Thread(target=job, daemon=True).start()

    chat_macros: dict[str, str] = config.get("chat_macros", {"f5": "/hideout"})
    status = StatusWindow(
        league=league,
        hotkeys={"hotkey": hotkey, "local": local_hotkey, "quit": quit_hotkey,
                "macros": chat_macros},
        on_quit=telemetry.stop,
        boosteroid_mode=bool(config.get("boosteroid_mode", True)),
        on_boosteroid_mode_change=_save_boosteroid_mode,
        on_hotkey_change=_change_hotkey,
        game_version=config.get("game_version", "poe1"),
        on_game_change=_change_game,
    )
    # Okno wyniku jest podrzedne wobec glownego - jeden obiekt Tk na proces.
    window = ResultWindow(
        parent=status.root,
        on_search=checker.research,
        on_craft_check=checker.check_ceiling,
        close_on_focus_loss=config.get("close_on_focus_loss", True),
    )

    hotkeys.add_hotkey(hotkey, _price_check_hotkey)
    hotkeys.add_hotkey(local_hotkey, lambda: checker.trigger(use_bridge=False))
    # Skrot leci z watku biblioteki keyboard, a Tk wolno dotykac tylko z watku
    # glownego - dlatego zamkniecie przekazujemy przez kolejke zdarzen Tk.
    hotkeys.add_hotkey(quit_hotkey, lambda: status.root.after(0, status.root.quit))

    # Makra czatu (np. F5 -> /hideout) - w odroznieniu od price checka nie
    # potrzebuja mostu: klawisze (w odroznieniu od schowka) i tak leca live
    # do sesji w chmurze, wiec samo "Enter, wpisz komende, Enter" dziala
    # identycznie lokalnie i na Boosteroidzie. Malutkie opoznienia, zeby gra
    # zdazyla otworzyc pole czatu, zanim zaczniemy pisac.
    def _chat_macro(command: str) -> None:
        hotkeys.send("enter")
        time.sleep(0.1)
        hotkeys.write(command)
        time.sleep(0.05)
        hotkeys.send("enter")

    for macro_key, macro_command in chat_macros.items():
        hotkeys.add_hotkey(macro_key, lambda cmd=macro_command: _chat_macro(cmd))

    print(f"  {hotkey:<12} wycen przedmiot pod kursorem (przez Boosteroida)")
    print(f"  {local_hotkey:<12} wycen zawartosc lokalnego schowka")
    print(f"  {quit_hotkey:<12} wyjscie")
    for macro_key, macro_command in chat_macros.items():
        print(f"  {macro_key:<12} wysyla '{macro_command}' na czacie")
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
    parser = argparse.ArgumentParser(
        description="Price check dla Path of Exile 1/2 przez Boosteroida")
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
        game = config.get("game_version", "poe1")
        for name in TradeClient.fetch_leagues(config["user_agent"], game=game):
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
