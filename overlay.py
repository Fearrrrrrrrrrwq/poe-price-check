"""Panel wyceny.

Uklad idzie za tym, po co sie ten program uruchamia: najpierw ODPOWIEDZ
(szacowana wartosc), potem narzedzia do jej doprecyzowania (mody, wlasciwosci),
a na koncu material dowodowy (lista ofert).
"""

import tkinter as tk
import webbrowser

import theme
from i18n import t
from theme import (BG, BG_INPUT, BG_PANEL, BG_ROW, BG_ROW_HOVER, BORDER, FG,
                   FG_ACCENT, FG_ERROR, FG_MUTED, FG_OK, FG_TITLE, FG_WARN,
                   FONT_BADGE, FONT_BIG, FONT_BODY, FONT_HEAD, FONT_LABEL,
                   FONT_PRICE, FONT_SMALL, FONT_TITLE, GAP, PAD, TIGHT)
from winutil import window_is_foreground


class _ModRow:
    """Wiersz moda - klikalny w calosci, nie tylko w sam znacznik."""

    def __init__(self, parent: tk.Widget, option, row_bg: str) -> None:
        self.option = option
        self.row_bg = row_bg
        self.searchable = option.searchable
        is_pseudo = option.mod.kind == "pseudo"
        self._badge_colour = FG_ACCENT if is_pseudo else FG_MUTED

        self.frame = tk.Frame(parent, bg=row_bg,
                              cursor="hand2" if self.searchable else "arrow")
        self.frame.pack(fill="x")

        self.check = tk.Label(self.frame, width=2, font=FONT_SMALL, bg=row_bg)
        self.check.pack(side="left", padx=(6, 2), pady=3)

        self.badge = tk.Label(self.frame, text=option.badge() or "", font=FONT_BADGE,
                              bg=row_bg, width=7, anchor="w")
        self.badge.pack(side="left")

        # Prog trzymamy w stalej kolumnie po prawej - inaczej wartosci wisza
        # w roznych miejscach i wiersze wygladaja na rozjechane.
        self.min_var = tk.StringVar(
            value="" if option.min_value is None else _fmt_number(option.min_value))
        if self.searchable:
            self.entry = tk.Entry(
                self.frame, textvariable=self.min_var, width=6, font=FONT_SMALL,
                bg=BG_INPUT, fg=FG, insertbackground=FG, relief="flat",
                justify="right", highlightthickness=1, highlightbackground=BORDER,
                highlightcolor=FG_ACCENT)
            self.entry.pack(side="right", padx=(GAP, 8), pady=2)
        else:
            self.entry = None
            tk.Label(self.frame, text=t("res.not_tradeable"), font=FONT_LABEL, fg=FG_MUTED,
                     bg=row_bg).pack(side="right", padx=(GAP, 8))

        self.text = tk.Label(self.frame, text=option.label(), font=FONT_BODY,
                             bg=row_bg, anchor="w", justify="left")
        self.text.pack(side="left", fill="x", expand=True)

        if self.searchable:
            for widget in (self.frame, self.check, self.badge, self.text):
                widget.bind("<Button-1>", self._on_click)
                widget.bind("<Enter>", self._on_enter)
                widget.bind("<Leave>", self._on_leave)
        self._refresh()

    def _on_click(self, _event=None) -> str:
        self.option.enabled = not self.option.enabled
        self._refresh()
        return "break"

    def _on_enter(self, _event=None) -> None:
        self._paint(BG_ROW_HOVER)

    def _on_leave(self, _event=None) -> None:
        self._paint(self.row_bg)

    def _paint(self, bg: str) -> None:
        """Podswietlenie calego klikalnego wiersza pod kursorem - bez tego
        wiersze wygladaja martwo, mimo ze cale sa klikalne."""
        self.frame.config(bg=bg)
        self.text.config(bg=bg)
        self.badge.config(bg=bg)
        if not self.option.enabled:
            self.check.config(bg=bg)

    def _refresh(self) -> None:
        if not self.searchable:
            self.check.config(text="", bg=self.row_bg)
            self.text.config(fg=FG_MUTED)
            self.badge.config(fg=FG_MUTED)
            return
        on = self.option.enabled
        self.check.config(text="✔" if on else "", fg=BG if on else FG_MUTED,
                          bg=FG_ACCENT if on else self.row_bg)
        self.text.config(fg=FG if on else FG_MUTED)
        self.badge.config(fg=self._badge_colour if on else FG_MUTED)
        if self.entry is not None:
            self.entry.config(fg=FG if on else FG_MUTED)

    def set_enabled(self, enabled: bool) -> None:
        if self.searchable:
            self.option.enabled = enabled
            self._refresh()

    def widen(self, factor: float = 0.9) -> None:
        if not self.searchable:
            return
        raw = self.min_var.get().strip().replace(",", ".")
        try:
            self.min_var.set(_fmt_number(float(raw) * factor))
        except ValueError:
            pass

    def collect(self):
        if not self.searchable:
            return self.option
        raw = self.min_var.get().strip().replace(",", ".")
        try:
            self.option.min_value = float(raw) if raw else None
        except ValueError:
            pass  # smiec w polu - zostaje poprzedni prog
        return self.option


class _PropRow:
    """Wiersz wlasciwosci z suwakiem i wartoscia w stalej kolumnie."""

    def __init__(self, parent: tk.Widget, option, row_bg: str) -> None:
        self.option = option
        self.row_bg = row_bg
        self._ready = False

        self.frame = tk.Frame(parent, bg=row_bg)
        self.frame.pack(fill="x")

        self.check = tk.Label(self.frame, width=2, font=FONT_SMALL, bg=row_bg,
                              cursor="hand2")
        self.check.pack(side="left", padx=(6, 2), pady=3)

        self.label = tk.Label(self.frame, text=option.label, font=FONT_BODY,
                              bg=row_bg, anchor="w", width=17, cursor="hand2")
        self.label.pack(side="left")

        self.value = tk.Label(self.frame, text=str(option.value), font=FONT_PRICE,
                              bg=row_bg, width=4, anchor="e")
        self.value.pack(side="right", padx=(GAP, 10))

        self.var = tk.IntVar(value=option.value)
        # UWAGA: w tk.Scale uchwyt ma kolor 'bg' widzetu. Ustawienie go na kolor
        # wiersza czynilo suwak niewidocznym - uchwyt musi byc w kolorze akcentu.
        self.scale = tk.Scale(
            self.frame, from_=option.minimum, to=option.maximum, orient="horizontal",
            variable=self.var, showvalue=0, bg=FG_ACCENT, troughcolor=BG_INPUT,
            activebackground=FG_TITLE, highlightthickness=0, bd=0,
            sliderrelief="flat", sliderlength=16, width=8)
        self.scale.pack(side="left", fill="x", expand=True, padx=(GAP, 0))

        for widget in (self.check, self.label):
            widget.bind("<Button-1>", self._on_click)
        self._refresh()
        # Dopiero teraz - inaczej samo zbudowanie suwaka wlaczyloby filtr.
        self.scale.config(command=self._on_slide)
        self._ready = True

    def _on_slide(self, value: str) -> None:
        self.value.config(text=str(int(float(value))))
        # Ruszenie suwakiem samo wlacza filtr - inaczej latwo przestawic wartosc
        # i zachodzic w glowe, czemu wynik sie nie zmienil.
        if self._ready and not self.option.enabled:
            self.option.enabled = True
            self._refresh()

    def _on_click(self, _event=None) -> str:
        self.option.enabled = not self.option.enabled
        self._refresh()
        return "break"

    def _refresh(self) -> None:
        on = self.option.enabled
        self.check.config(text="✔" if on else "", fg=BG if on else FG_MUTED,
                          bg=FG_ACCENT if on else self.row_bg)
        self.label.config(fg=FG if on else FG_MUTED)
        self.value.config(fg=FG_TITLE if on else FG_MUTED)
        self.scale.config(bg=FG_ACCENT if on else BORDER,
                          troughcolor=BG_INPUT if on else BG_PANEL)

    def set_enabled(self, enabled: bool) -> None:
        self.option.enabled = enabled
        self._refresh()

    def collect(self):
        self.option.value = int(self.var.get())
        return self.option


class ResultWindow:
    """Okno wyniku. `on_search` dostaje (mody, wlasciwosci) i wykonuje zapytanie."""

    def __init__(self, parent=None, on_search=None,
                 close_on_focus_loss: bool = True) -> None:
        self.on_search = on_search
        self._url = ""
        self._options: list = []
        self._properties: list = []
        self._rows: list[_ModRow] = []
        self._prop_rows: list[_PropRow] = []
        self._show_hidden = False
        self._last_item = None
        self._was_focused = False
        self._styled = False

        # Okno podrzedne, nie drugi obiekt Tk - dwa rooty w jednym procesie to
        # prosta droga do zawieszen, zwlaszcza przy dostepie z watkow roboczych.
        self.root = tk.Toplevel(parent) if parent is not None else tk.Tk()
        self.root.title("PoE Price Check - wycena")
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)
        self.root.minsize(460, 0)
        self.root.withdraw()
        theme.apply_icon(self.root)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        self.root.bind("<Escape>", lambda _e: self.hide())
        if close_on_focus_loss:
            self.root.bind("<FocusIn>", self._on_focus_in)
            self.root.bind("<FocusOut>", self._on_focus_out)
            self.root.after(500, self._poll_focus)

        self.outer = tk.Frame(self.root, bg=BG, padx=PAD, pady=PAD)
        self.outer.pack(fill="both", expand=True)

        # --- naglowek ---------------------------------------------------
        self.title = tk.Label(self.outer, text="", font=FONT_TITLE, fg=FG_TITLE,
                              bg=BG, anchor="w", justify="left")
        self.title.pack(fill="x")
        self.subtitle = tk.Label(self.outer, text="", font=FONT_SMALL, fg=FG_MUTED,
                                 bg=BG, anchor="w")
        self.subtitle.pack(fill="x", pady=(1, 0))

        # --- paski stanu -------------------------------------------------
        self.craft = tk.Label(self.outer, text="", font=FONT_SMALL, bg=BG,
                              anchor="w", justify="left")
        self.notice = tk.Label(self.outer, text="", font=FONT_SMALL, bg=BG_PANEL,
                               anchor="w", justify="left", wraplength=420,
                               padx=10, pady=6)

        # --- odpowiedz ------------------------------------------------------
        #
        # To jest hero-element calego okna - po nie uruchamia sie program - wiec
        # dostaje wlasny akcent u gory zamiast zlewac sie z reszta kafelkow.
        # Bez ramki (jak wszystko od refreshu 2026): elewacje daje kontrast
        # BG_PANEL na BG.
        self.value_box = tk.Frame(self.outer, bg=BG_PANEL)
        tk.Frame(self.value_box, bg=FG_ACCENT, height=2).pack(fill="x")
        tk.Label(self.value_box, text=t("res.value").upper(), font=FONT_LABEL,
                 fg=FG_MUTED, bg=BG_PANEL, anchor="w").pack(fill="x", padx=14,
                                                            pady=(10, 0))
        self.value_main = tk.Label(self.value_box, text="", font=FONT_BIG,
                                   fg=FG_TITLE, bg=BG_PANEL, anchor="w")
        self.value_main.pack(fill="x", padx=14)
        self.value_sub = tk.Label(self.value_box, text="", font=FONT_SMALL,
                                  fg=FG_MUTED, bg=BG_PANEL, anchor="w")
        self.value_sub.pack(fill="x", padx=14, pady=(1, 12))

        # --- sekcje sterujace ---------------------------------------------
        self.mods_box, self.mods_rows = theme.section(self.outer, t("res.mods"))
        self.props_box, self.props_rows = theme.section(self.outer, t("res.props"))
        self.buttons = tk.Frame(self.outer, bg=BG)

        # --- wyniki --------------------------------------------------------
        self.results_head = tk.Frame(self.outer, bg=BG)
        self.rows = tk.Frame(self.outer, bg=BG)

        self.link = tk.Label(self.outer, text="", font=FONT_SMALL, fg=FG_ACCENT,
                             bg=BG, anchor="w", cursor="hand2")
        self.link.pack(side="bottom", fill="x", pady=(GAP, 0))
        self.link.bind("<Button-1>", lambda _e: self._open_url())

    # -------------------------------------------------------------- pomocnicze

    def _open_url(self) -> None:
        if self._url:
            webbrowser.open(self._url)

    def hide(self) -> None:
        self.root.withdraw()

    def _clear(self) -> None:
        for container in (self.mods_rows, self.props_rows, self.rows,
                          self.results_head, self.buttons):
            for child in container.winfo_children():
                child.destroy()
        for widget in (self.craft, self.notice, self.value_box, self.mods_box,
                       self.props_box, self.buttons, self.results_head, self.rows):
            widget.pack_forget()
        self._rows = []
        self._prop_rows = []

    def _present(self) -> None:
        self._was_focused = False
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        if not self._styled:
            # Okno powstaje schowane, a DWM nie ma wtedy czego pomalowac -
            # ciemna belke ustawiamy dopiero przy pierwszym pokazaniu.
            theme.dark_titlebar(self.root)
            self._styled = True

    # ------------------------------------------------------ chowanie po fokusie

    def _on_focus_in(self, _event=None) -> None:
        self._was_focused = True

    def _on_focus_out(self, _event=None) -> None:
        self.root.after(80, self._hide_if_focus_left)

    def _hide_if_focus_left(self) -> None:
        if not self.root.winfo_viewable() or not self._was_focused:
            return
        if not window_is_foreground(self.root.winfo_id()):
            self.hide()

    def _poll_focus(self) -> None:
        self._hide_if_focus_left()
        self.root.after(500, self._poll_focus)

    # ------------------------------------------------------------------ stany

    def show_status(self, text: str) -> None:
        self._clear()
        self.title.config(text=text, fg=FG)
        self.subtitle.config(text="")
        self.link.config(text="")
        self._url = ""
        self._present()

    def show_error(self, message: str) -> None:
        self._clear()
        self.title.config(text=t("res.error"), fg=FG_ERROR)
        self.subtitle.config(text="")
        self.link.config(text="")
        self._url = ""
        self.notice.config(text=message, fg=FG_ERROR)
        self.notice.pack(fill="x", pady=(GAP, 0))
        self._present()

    # ----------------------------------------------------------------- wynik

    def show_result(self, item, result, options=None, properties=None,
                    stale: bool = False) -> None:
        self._clear()
        if item is not self._last_item:
            self._show_hidden = False  # nowy przedmiot zaczyna zwiniety
            self._last_item = item
        self._options = options or []
        self._properties = properties or []

        self._render_header(item, result, stale)
        self._render_notices(item, result, stale)
        self._render_value(result)
        if self._options:
            self._render_mods()
        if self._properties:
            self._render_props()
        if self._options or self._properties:
            self._render_buttons()
        self._render_results(result)

        self._url = result.browser_url()
        self.link.config(text=t("res.open_trade"))
        self._present()

    def _render_header(self, item, result, stale: bool) -> None:
        name = item.name or item.base_type or "?"
        self.title.config(text=name, fg=FG_ERROR if stale else FG_TITLE)

        bits = []
        if item.name and item.base_type:
            bits.append(item.base_type)
        bits.append(item.rarity)
        if item.item_level:
            bits.append(f"ilvl {item.item_level}")
        if item.link_count >= 5:
            bits.append(f"{item.link_count}L")
        bits.append(result.league)
        if result.is_exchange:
            bits.append(t("res.exchange"))
        self.subtitle.config(text="  ·  ".join(bits))

    def _render_notices(self, item, result, stale: bool) -> None:
        craft = item.craft_summary()
        if craft:
            self.craft.config(text=craft, fg=FG_OK if item.can_be_modified else FG_MUTED)
            self.craft.pack(fill="x", pady=(GAP, 0))

        if stale:
            self.notice.config(
                text=t("res.stale"), fg=FG_ERROR)
            self.notice.pack(fill="x", pady=(GAP, 0))
        elif result.total == 0 and result.mods_used:
            self.notice.config(
                text=t("res.no_match"), fg=FG_WARN)
            self.notice.pack(fill="x", pady=(GAP, 0))

    def _render_value(self, result) -> None:
        """Wycena jako glowny element - to po nia uruchamia sie program."""
        summary = result.summary()
        if result.listings:
            main, _, rest = summary.partition("   ")
            self.value_main.config(text=main.strip(), fg=FG_TITLE)
            detail = rest.strip().replace("   ", "  ·  ")
            self.value_sub.config(text=f"{detail}  ·  {t('res.offers', n=result.total)}".strip(" ·"))
        else:
            self.value_main.config(text=t("res.no_offers"), fg=FG_MUTED)
            self.value_sub.config(text=t("res.loosen"))
        self.value_box.pack(fill="x", pady=(GAP, 0))

    def _render_mods(self) -> None:
        self.mods_box.pack(fill="x", pady=(GAP, 0))
        self._fill_mod_rows()

    def _fill_mod_rows(self) -> None:
        visible = [o for o in self._options if not o.hidden]
        hidden = [o for o in self._options if o.hidden]

        index = 0
        for option in visible:
            self._rows.append(_ModRow(self.mods_rows, option,
                                      BG_ROW if index % 2 else BG_PANEL))
            index += 1

        if not hidden:
            return
        active = sum(1 for o in hidden if o.enabled)
        arrow = "▴" if self._show_hidden else "▾"
        label = (f"{arrow}  {t('res.collapse')}" if self._show_hidden
                 else f"{arrow}  {t('res.show_hidden', n=len(hidden))}")
        if active and not self._show_hidden:
            label += f"  ·  {t('res.still_filtering', n=active)}"

        toggle = tk.Label(self.mods_rows, text=label, font=FONT_SMALL, fg=FG_MUTED,
                          bg=BG_PANEL, anchor="w", cursor="hand2", padx=8, pady=5)
        toggle.pack(fill="x")
        toggle.bind("<Button-1>", self._toggle_hidden)
        toggle.bind("<Enter>", lambda _e: toggle.config(fg=FG))
        toggle.bind("<Leave>", lambda _e: toggle.config(fg=FG_MUTED))

        if self._show_hidden:
            for option in hidden:
                self._rows.append(_ModRow(self.mods_rows, option,
                                          BG_ROW if index % 2 else BG_PANEL))
                index += 1

    def _toggle_hidden(self, _event=None) -> str:
        self._collect()  # przerysowanie niszczy kontrolki razem z wpisanymi progami
        self._show_hidden = not self._show_hidden
        for child in self.mods_rows.winfo_children():
            child.destroy()
        self._rows = []
        self._fill_mod_rows()
        return "break"

    def _render_props(self) -> None:
        self.props_box.pack(fill="x", pady=(GAP, 0))
        for index, option in enumerate(self._properties):
            self._prop_rows.append(_PropRow(self.props_rows, option,
                                            BG_ROW if index % 2 else BG_PANEL))

    def _render_buttons(self) -> None:
        self.buttons.pack(fill="x", pady=(GAP, 0))
        theme.button(self.buttons, t("res.search_again"), self._do_search,
                     primary=True).pack(side="left")
        for label, command in ((t("res.wider"), self._widen),
                               (t("res.all"), lambda: self._set_all(True)),
                               (t("res.none"), lambda: self._set_all(False))):
            theme.button(self.buttons, label, command).pack(side="left", padx=(TIGHT, 0))

    def _render_results(self, result) -> None:
        if not result.listings:
            return
        columns = ((t("col.price"), 13), (t("col.div"), 6),
                   (t("col.ilvl"), 5), (t("col.quality"), 4),
                   (t("col.account"), 18), (t("col.age"), 6))
        for text, width in columns:
            tk.Label(self.results_head, text=text, font=FONT_LABEL, fg=FG_MUTED,
                     bg=BG, width=width, anchor="w").pack(side="left")
        self.results_head.pack(fill="x", pady=(GAP + 2, 1))

        for index, listing in enumerate(result.listings):
            row_bg = BG_ROW if index % 2 else BG
            row = tk.Frame(self.rows, bg=row_bg)
            row.pack(fill="x")
            cells = (
                (listing.price_text(), 13, FONT_PRICE, FG),
                (listing.divine_text() or "-", 6, FONT_SMALL, FG_TITLE),
                (str(listing.item_level or "-"), 5, FONT_SMALL, FG_MUTED),
                (str(listing.quality or "-"), 4, FONT_SMALL, FG_MUTED),
                (listing.account, 18, FONT_SMALL, FG_MUTED),
                (listing.age_text(), 6, FONT_SMALL, FG_MUTED),
            )
            for text, width, font, colour in cells:
                # 'width' w Label to szerokosc MINIMALNA - dluzszy nick rozpycha
                # kolumne i rozjezdza wiersz, wiec przycinamy go sami.
                tk.Label(row, text=_ellipsis(text, width), font=font, fg=colour,
                         bg=row_bg, width=width, anchor="w").pack(side="left")
        self.rows.pack(fill="x")

    # ------------------------------------------------------------------ akcje

    def _collect(self) -> tuple[list, list]:
        for row in self._rows:
            row.collect()
        for row in self._prop_rows:
            row.collect()
        return self._options, self._properties

    def _do_search(self) -> None:
        if self.on_search:
            options, properties = self._collect()
            self.on_search(options, properties)

    def _set_all(self, enabled: bool) -> None:
        for row in self._rows:
            row.set_enabled(enabled)

    def _widen(self) -> None:
        for row in self._rows:
            row.widen()


def _fmt_number(value: float) -> str:
    return str(int(value)) if value == int(value) else f"{value:.1f}"


def _ellipsis(text: str, width: int) -> str:
    return text if len(text) <= width else text[: max(1, width - 1)] + "…"
