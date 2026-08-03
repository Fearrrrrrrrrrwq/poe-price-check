"""Okno glowne - widoczny dowod, ze program dziala.

Bez niego po konfiguracji zostawal sam proces w tle: uzytkownik nie wiedzial,
czy aplikacja wystartowala, jakie ma skroty ani jak ja zamknac.
"""

import tkinter as tk
import webbrowser

import theme
from i18n import t
from paths import APP_VERSION
from theme import (BG, BG_PANEL, FG, FG_ACCENT, FG_MUTED, FG_OK, FG_TITLE,
                   FONT_BIG, FONT_BODY, FONT_LABEL, FONT_SMALL, FONT_TITLE,
                   GAP, PAD, TIGHT)


# Zaproszenie na Discorda. To jest adres ZAPASOWY - wlasciwy przychodzi z
# version.json, wiec wygasle zaproszenie da sie podmienic samym wdrozeniem
# strony, bez zmuszania ludzi do pobrania nowej wersji programu.
DISCORD_URL = "https://discord.gg/FjAnFqGNh4"


class StatusWindow:
    """Glowne okno aplikacji. Trzyma obiekt Tk, reszta okien jest podrzedna."""

    def __init__(self, league: str, hotkeys: dict, on_quit=None) -> None:
        self.on_quit = on_quit
        self._checks = 0
        self._discord_url = DISCORD_URL

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

        self.state = tk.Label(state_card.body, text=t("app.league_bridge", league=league),
                              font=FONT_SMALL, fg=FG_MUTED, bg=BG_PANEL, anchor="w")
        self.state.pack(fill="x", padx=12, pady=(1, 11))

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
        theme.keycap(main_card.body, hotkeys.get("hotkey", "ctrl+d")).pack(
            anchor="w", padx=12, pady=(12, 0))
        tk.Label(main_card.body, text=t("app.price_check"), font=FONT_LABEL,
                 fg=FG_MUTED, bg=BG_PANEL, anchor="w").pack(fill="x", padx=12,
                                                            pady=(5, 11))

        # --- pozostale skroty ------------------------------------------------
        tk.Label(outer, text=t("app.other_hotkeys"), font=FONT_LABEL, fg=FG_MUTED,
                 bg=BG, anchor="w").pack(fill="x", pady=(0, TIGHT + 1))
        for key, description in (
            (hotkeys.get("local", "ctrl+alt+d"), t("app.hk_clipboard")),
            ("Esc", t("app.hk_close")),
            (hotkeys.get("quit", "ctrl+alt+q"), t("app.hk_quit")),
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

        Program niczego nie pobiera ani nie podmienia sam - przycisk tylko
        otwiera strone wydania w przegladarce. Patrz updater.py.
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
