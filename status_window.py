"""Okno glowne - widoczny dowod, ze program dziala.

Bez niego po konfiguracji zostawal sam proces w tle: uzytkownik nie wiedzial,
czy aplikacja wystartowala, jakie ma skroty ani jak ja zamknac.
"""

import tkinter as tk
import webbrowser

import theme
from i18n import t
from paths import APP_VERSION
from theme import (BG, BG_PANEL, FG, FG_ACCENT, FG_ERROR, FG_MUTED, FG_OK,
                   FG_TITLE, FONT_BIG, FONT_BODY, FONT_LABEL, FONT_SMALL,
                   FONT_TITLE, GAP, PAD, TIGHT)


# Zaproszenie na Discorda. To jest adres ZAPASOWY - wlasciwy przychodzi z
# version.json, wiec wygasle zaproszenie da sie podmienic samym wdrozeniem
# strony, bez zmuszania ludzi do pobrania nowej wersji programu.
DISCORD_URL = "https://discord.gg/FjAnFqGNh4"


class StatusWindow:
    """Glowne okno aplikacji. Trzyma obiekt Tk, reszta okien jest podrzedna."""

    def __init__(self, league: str, hotkeys: dict, on_quit=None,
                 boosteroid_mode: bool = True, on_boosteroid_mode_change=None,
                 on_hotkey_change=None, game_version: str = "poe1",
                 on_game_change=None) -> None:
        self.on_quit = on_quit
        self._checks = 0
        self._discord_url = DISCORD_URL
        self._league = league
        self._main_hotkey = hotkeys.get("hotkey", "ctrl+d")
        # Zwykly atrybut, nie tk.BooleanVar - musi byc bezpiecznie czytelny z
        # watku skrotu (hotkeys_windows/hotkeys_macos wolaja callback poza
        # watkiem Tk), a odczyt atrybutu w CPythonie jest atomowy dzieki GIL.
        # Pisany jest tylko z watku glownego (komenda checkboxa).
        self.boosteroid_mode = boosteroid_mode
        self._on_boosteroid_mode_change = on_boosteroid_mode_change
        # Wywolywane z UI edycji glownego skrotu - main.py rejestruje nowa
        # kombinacje, usuwa stara i zapisuje config, zwracajac True/False.
        # Bez tego zmiana skrotu wymagalaby edycji config.json na piechote
        # i restartu programu.
        self._on_hotkey_change = on_hotkey_change
        self._hotkey_editing = False
        # Wersja gry - przelaczana w locie zamiast tylko raz w kreatorze,
        # zeby ktos testujacy oba tryby nie musial kasowac configu za kazdym
        # razem. Zmiana leci w tle (main.py: nowy TradeClient + nowa liga,
        # patrz resolve_league) - stad game_switching()/game_switched()/
        # game_switch_failed() zamiast prostego, synchronicznego callbacka.
        self.game_version = game_version
        self._on_game_change = on_game_change
        self._game_switching = False

        self.root = tk.Tk()
        self.root.title("PoE Price Check")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        theme.apply_icon(self.root)
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

        outer = tk.Frame(self.root, bg=BG, padx=PAD + 4, pady=PAD + 2)
        outer.pack(fill="both", expand=True)

        # --- naglowek -----------------------------------------------------
        head = tk.Frame(outer, bg=BG)
        head.pack(fill="x")
        tk.Label(head, text="PoE Price Check", font=FONT_TITLE, fg=FG_TITLE,
                 bg=BG).pack(side="left")
        tk.Label(head, text=f"v{APP_VERSION}", font=FONT_LABEL, fg=FG_MUTED,
                 bg=BG).pack(side="right", pady=(6, 0))

        # --- pasek aktualizacji ---------------------------------------------
        # Tworzony od razu, ale nie pokazywany: sprawdzenie wersji leci w tle
        # i konczy sie juz po zbudowaniu okna. Dokladanie widgetu pozniej
        # przestawialoby uklad i zmienialo rozmiar okna w trakcie pracy.
        self._update_holder = tk.Frame(outer, bg=BG)
        self._update_info: dict | None = None

        # --- kafelek stanu -------------------------------------------------
        state_card = theme.card(outer, accent=FG_OK)
        state_card.pack(fill="x", pady=(GAP + 2, GAP))
        self._first_card = state_card

        line = tk.Frame(state_card.body, bg=BG_PANEL)
        line.pack(fill="x", padx=12, pady=(10, 0))
        self.dot = tk.Label(line, text="●", font=("Segoe UI", 10), fg=FG_OK,
                            bg=BG_PANEL)
        self.dot.pack(side="left")
        tk.Label(line, text=t("app.running"), font=FONT_BODY, fg=FG,
                 bg=BG_PANEL).pack(side="left", padx=(6, 0))

        self.state = tk.Label(state_card.body, text=self._state_text(),
                              font=FONT_SMALL, fg=FG_MUTED, bg=BG_PANEL, anchor="w")
        self.state.pack(fill="x", padx=12, pady=(1, 11))

        # --- wybor wersji gry -------------------------------------------------
        game_row = tk.Frame(outer, bg=BG)
        game_row.pack(fill="x", pady=(0, GAP))
        tk.Label(game_row, text=t("app.game_label"), font=FONT_LABEL, fg=FG_MUTED,
                 bg=BG).pack(side="left", padx=(0, GAP))
        self._game_buttons = tk.Frame(game_row, bg=BG)
        self._game_buttons.pack(side="left")
        self._game_status = tk.Label(game_row, text="", font=FONT_LABEL,
                                     fg=FG_MUTED, bg=BG)
        self._game_status.pack(side="left", padx=(GAP, 0))
        self._render_game_buttons()

        # --- licznik obok glownego skrotu ------------------------------------
        stats = tk.Frame(outer, bg=BG)
        stats.pack(fill="x", pady=(0, GAP + 2))

        counter_card = theme.card(stats)
        counter_card.pack(side="left", fill="both", expand=True)
        self.counter = tk.Label(counter_card.body, text="0", font=FONT_BIG,
                                fg=FG_TITLE, bg=BG_PANEL, anchor="w")
        self.counter.pack(fill="x", padx=12, pady=(9, 0))
        tk.Label(counter_card.body, text=t("app.checks"), font=FONT_LABEL,
                 fg=FG_MUTED, bg=BG_PANEL, anchor="w").pack(fill="x", padx=12,
                                                            pady=(0, 11))

        main_card = theme.card(stats, accent=FG_ACCENT)
        main_card.pack(side="left", fill="both", expand=True, padx=(GAP, 0))
        key_row = tk.Frame(main_card.body, bg=BG_PANEL)
        key_row.pack(fill="x", padx=12, pady=(12, 0))
        self._hotkey_keycap = theme.keycap(key_row, self._main_hotkey)
        self._hotkey_keycap.pack(side="left")
        # Olowek do edycji skrotu - tylko gdy main.py w ogole podal callback
        # (tryby uzycia programu bez petli Tk, np. --paste, go nie potrzebuja).
        if self._on_hotkey_change is not None:
            edit_btn = tk.Label(key_row, text="✎", font=FONT_LABEL, fg=FG_MUTED,
                                bg=BG_PANEL, cursor="hand2")
            edit_btn.pack(side="left", padx=(6, 0))
            edit_btn.bind("<Button-1>", lambda _e: self._toggle_hotkey_edit())
        tk.Label(main_card.body, text=t("app.price_check"), font=FONT_LABEL,
                 fg=FG_MUTED, bg=BG_PANEL, anchor="w").pack(fill="x", padx=12,
                                                            pady=(5, 11))

        # --- edycja glownego skrotu (schowana, dopoki ktos nie kliknie olowka) --
        self._hotkey_edit_row = tk.Frame(outer, bg=BG)
        self._hotkey_var = tk.StringVar(value=self._main_hotkey)
        theme.entry(self._hotkey_edit_row, self._hotkey_var, width=14).pack(
            side="left")
        theme.button(self._hotkey_edit_row, t("app.hk_save"),
                     self._save_hotkey_edit, primary=True).pack(
            side="left", padx=(TIGHT + 2, 0))
        theme.button(self._hotkey_edit_row, t("app.hk_cancel"),
                     self._cancel_hotkey_edit).pack(side="left", padx=(TIGHT, 0))
        self._hotkey_error = tk.Label(outer, text="", font=FONT_LABEL,
                                      fg=FG_ERROR, bg=BG, anchor="w",
                                      justify="left", wraplength=300)

        # --- przelacznik trybu Boosteroid --------------------------------
        #
        # Bez tego trzeba bylo pamietac dwa rozne skroty (glowny - przez
        # most, i local_clipboard_hotkey - bez mostu). Ten przelacznik
        # zmienia zachowanie GLOWNEGO skrotu w locie, bez restartu programu -
        # main.py czyta status.boosteroid_mode w momencie kazdego wcisniecia,
        # nie raz przy starcie.
        toggle_row = tk.Frame(outer, bg=BG)
        toggle_row.pack(fill="x", pady=(0, TIGHT))
        self._boosteroid_var = tk.BooleanVar(value=self.boosteroid_mode)
        theme.checkbox(
            toggle_row, t("app.boosteroid_toggle"), self._boosteroid_var,
            command=self._on_toggle_boosteroid,
        ).pack(anchor="w")
        self._toggle_note = tk.Label(
            outer, text=t("app.boosteroid_toggle_note", hotkey=self._main_hotkey),
            font=FONT_LABEL, fg=FG_MUTED, bg=BG, anchor="w", justify="left",
            wraplength=300)
        self._toggle_note.pack(fill="x", pady=(0, GAP + 2))

        # --- pozostale skroty ------------------------------------------------
        tk.Label(outer, text=t("app.other_hotkeys"), font=FONT_LABEL, fg=FG_MUTED,
                 bg=BG, anchor="w").pack(fill="x", pady=(0, TIGHT + 1))
        # Makra czatu (np. F5 -> /hideout) dochodza z configu, wiec lista nie
        # jest stala jak reszta - ktos moze ich miec zero albo pieć.
        macro_rows = [
            (key, command) for key, command in hotkeys.get("macros", {}).items()
        ]
        for key, description in (
            (hotkeys.get("local", "ctrl+alt+d"), t("app.hk_clipboard")),
            ("Esc", t("app.hk_close")),
            (hotkeys.get("quit", "ctrl+alt+q"), t("app.hk_quit")),
            *macro_rows,
        ):
            row = tk.Frame(outer, bg=BG)
            row.pack(fill="x", pady=1)
            theme.keycap(row, key).pack(side="left")
            tk.Label(row, text=description, font=FONT_SMALL, fg=FG_MUTED, bg=BG,
                     anchor="w").pack(side="left", padx=(GAP + 2, 0))

        # --- stopka -----------------------------------------------------------
        footer = tk.Frame(outer, bg=BG)
        footer.pack(fill="x", pady=(GAP + 8, 0))
        tk.Label(footer, text=t("app.minimise"), font=FONT_LABEL, fg=FG_MUTED,
                 bg=BG, anchor="w", justify="left").pack(side="left")
        theme.button(footer, t("app.quit"), self._quit).pack(side="right")
        # Adres czytany dopiero w chwili klikniecia, a nie domykany teraz -
        # dzieki temu set_discord() moze go podmienic bez przebudowy przycisku.
        # Margines z LEWEJ tez, nie tylko miedzy przyciskami: przy dluzszym
        # tekscie stopki (niemiecki, portugalski) etykieta dochodzila do
        # przycisku na styk, bez ani jednego piksela przerwy.
        theme.button(footer, t("app.discord"),
                     lambda: webbrowser.open(self._discord_url)).pack(
                         side="right", padx=(GAP, TIGHT + 2))

        self.root.update_idletasks()
        self._centre()

    # -------------------------------------------------------- tryb Boosteroid

    def _state_text(self) -> str:
        key = "app.league_bridge" if self.boosteroid_mode else "app.league_local"
        return t(key, league=self._league)

    def _on_toggle_boosteroid(self) -> None:
        self.boosteroid_mode = self._boosteroid_var.get()
        self.state.config(text=self._state_text())
        if self._on_boosteroid_mode_change:
            self._on_boosteroid_mode_change(self.boosteroid_mode)

    # -------------------------------------------------------- wersja gry

    def _render_game_buttons(self) -> None:
        """Przyciski PoE1/PoE2 - odtwarzane od zera przy kazdej zmianie, bo
        theme.button() wiaze kolory hover w domkniecie przy tworzeniu (patrz
        theme.py) i samo .config(bg=...) pozniej zostawialoby stary hover."""
        for child in self._game_buttons.winfo_children():
            child.destroy()
        state = "disabled" if self._game_switching else "normal"
        for game, label in (("poe1", "PoE 1"), ("poe2", "PoE 2")):
            btn = theme.button(
                self._game_buttons, label, lambda g=game: self._pick_game(g),
                primary=(self.game_version == game),
            )
            btn.config(state=state)
            btn.pack(side="left", padx=(0 if game == "poe1" else TIGHT, 0))

    def _pick_game(self, game: str) -> None:
        if self._game_switching or game == self.game_version:
            return
        if self._on_game_change is None:
            return
        self._game_switching = True
        self._render_game_buttons()
        self._game_status.config(text=t("app.game_switching"), fg=FG_MUTED)
        self._on_game_change(game)

    def game_switched(self, game: str, league: str) -> None:
        """Wolac z watku Tk po udanej zmianie gry (patrz main.py)."""
        self.game_version = game
        self._league = league
        self._game_switching = False
        self.state.config(text=self._state_text())
        self._game_status.config(text="")
        self._render_game_buttons()

    def game_switch_failed(self, message: str) -> None:
        """Wolac z watku Tk, gdy zmiana gry sie nie uda - zostajemy przy
        poprzedniej, dzialajacej konfiguracji zamiast wpisywac cokolwiek."""
        self._game_switching = False
        self._game_status.config(text=message, fg=FG_ERROR)
        self._render_game_buttons()

    # ------------------------------------------------------- edycja skrotu

    def _toggle_hotkey_edit(self) -> None:
        if self._hotkey_editing:
            self._cancel_hotkey_edit()
            return
        self._hotkey_var.set(self._main_hotkey)
        self._hotkey_error.config(text="")
        self._hotkey_edit_row.pack(fill="x", pady=(0, GAP))
        self._hotkey_editing = True
        self.root.update_idletasks()
        self._centre()

    def _cancel_hotkey_edit(self) -> None:
        self._hotkey_edit_row.pack_forget()
        self._hotkey_error.pack_forget()
        self._hotkey_error.config(text="")
        self._hotkey_editing = False
        self.root.update_idletasks()
        self._centre()

    def _save_hotkey_edit(self) -> None:
        if self._on_hotkey_change is None:
            return
        new_combo = self._hotkey_var.get()
        if not self._on_hotkey_change(new_combo):
            self._hotkey_error.config(text=t("app.hk_invalid"))
            self._hotkey_error.pack(fill="x", before=self._hotkey_edit_row,
                                    pady=(0, TIGHT))
            self.root.update_idletasks()
            self._centre()
            return
        self._main_hotkey = "+".join(
            part.strip().lower() for part in new_combo.split("+") if part.strip()
        )
        self._hotkey_keycap.config(text=self._main_hotkey.upper())
        self._toggle_note.config(
            text=t("app.boosteroid_toggle_note", hotkey=self._main_hotkey))
        self._cancel_hotkey_edit()

    # ---------------------------------------------------------------- widok

    def _centre(self) -> None:
        width, height = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 3
        self.root.geometry(f"+{x}+{y}")

    def set_discord(self, url: str) -> None:
        """Podmienia adres zaproszenia na ten podany przez strone."""
        if url:
            self._discord_url = url

    def show_update(self, version: str, url: str) -> None:
        """Pokazuje pasek 'jest nowsza wersja'. Wywolywac tylko z watku Tk.

        To jest FALLBACK: kiedy auto-aktualizacja (updater.py) sie uda,
        program zamyka sie i restartuje sam, ten pasek nigdy sie nie pokaze.
        Widac go tylko gdy cicha podmiana z jakiegokolwiek powodu nie wyszla
        (inny system niz Windows, dev-run z Pythona, wylaczone w configu,
        problem z siecia/suma kontrolna) - wtedy przycisk otwiera strone
        wydania w przegladarce, pobranie zostaje swiadoma decyzja czlowieka.
        """
        if self._update_info is not None:
            return  # pasek juz wisi, drugi raz nie ma czego pokazywac
        self._update_info = {"version": version, "url": url}

        card = theme.card(self._update_holder, accent=FG_ACCENT)
        card.pack(fill="x")
        row = tk.Frame(card.body, bg=BG_PANEL)
        row.pack(fill="x", padx=12, pady=10)

        labels = tk.Frame(row, bg=BG_PANEL)
        labels.pack(side="left", fill="x", expand=True)
        tk.Label(labels, text=t("update.available", version=version),
                 font=FONT_BODY, fg=FG_TITLE, bg=BG_PANEL, anchor="w").pack(fill="x")
        tk.Label(labels, text=t("update.current", version=APP_VERSION),
                 font=FONT_LABEL, fg=FG_MUTED, bg=BG_PANEL, anchor="w").pack(fill="x")

        if url:
            theme.button(row, t("update.open"),
                         lambda: webbrowser.open(url)).pack(side="right", padx=(GAP, 0))

        # Pasek wchodzi na gore, nad kafelek stanu - inaczej ginie na dole okna.
        self._update_holder.pack(fill="x", pady=(GAP + 2, 0), before=self._first_card)
        self.root.update_idletasks()
        self._centre()

    def show_restarting(self, version: str) -> None:
        """Program wlasnie zamyka sie, zeby .bat mogl podmienic .exe i odpalic
        go ponownie (patrz updater._apply_update) - to jedyna informacja,
        jaka uzytkownik dostaje w tej chwili, wiec ma byc jednoznaczna."""
        self.state.config(text=t("update.restarting", version=version))
        self.dot.config(fg=FG_ACCENT)

    def set_checks(self, count: int) -> None:
        if count != self._checks:
            self._checks = count
            self.counter.config(text=str(count))

    def flash(self) -> None:
        """Mrugniecie wskaznikiem - widac, ze program wlasnie cos robi."""
        self.dot.config(fg=FG_TITLE)
        self.root.after(250, lambda: self.dot.config(fg=FG_OK))

    def _quit(self) -> None:
        if self.on_quit:
            self.on_quit()
        self.root.quit()
