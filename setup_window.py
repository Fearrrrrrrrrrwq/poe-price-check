"""Kreator pierwszego uruchomienia.

Dwie strony, bo konfiguracja ma dwie polowy i obie sa obowiazkowe:
dokument-most po stronie Google i nakladka Steam po stronie Boosteroida.
Pominiecie drugiej konczy sie tym, ze program dziala, ale nic nie znajduje -
najgorszy mozliwy rodzaj awarii, bo wyglada na blad programu.
"""

import re
import threading
import tkinter as tk
import webbrowser
from tkinter import ttk

import i18n
import theme
from i18n import LANGUAGES, t
from theme import (BG, BG_PANEL, FG, FG_ACCENT, FG_ERROR, FG_MUTED, FG_OK,
                   FG_TITLE, FONT_BIG, FONT_BODY, FONT_HEAD, FONT_LABEL,
                   FONT_SMALL, GAP, PAD, TIGHT)

DOC_ID_RE = re.compile(r"/document/d/([A-Za-z0-9_-]{20,})")
BARE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{20,}$")
DOC_URL = "https://docs.google.com/document/d/{doc_id}/edit"

WRAP = 452


def extract_doc_id(text: str) -> str:
    """Wyciaga identyfikator z pelnego adresu albo przyjmuje samo ID.

    Ludzie wklejaja caly link z paska adresu, nie fragment miedzy /d/ a /edit -
    wymaganie samego ID bylo pierwszym miejscem, gdzie sie mylili.
    """
    text = (text or "").strip()
    match = DOC_ID_RE.search(text)
    if match:
        return match.group(1)
    return text if BARE_ID_RE.match(text) else ""


class SetupWindow:
    """Kreator konfiguracji. `run()` zwraca True, gdy zapisano ustawienia."""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.saved = False
        self.page = 0
        self._link_value = config.get("gdoc_id", "")

        self.root = tk.Tk()
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        theme.apply_icon(self.root)
        self.root.protocol("WM_DELETE_WINDOW", self._skip)

        self.outer = tk.Frame(self.root, bg=BG, padx=PAD + 6, pady=PAD)
        self.outer.pack(fill="both", expand=True)

        # --- wybor jezyka: pierwsza rzecz, jaka widzi uzytkownik -----------
        top = tk.Frame(self.outer, bg=BG)
        top.pack(fill="x", pady=(0, GAP))
        tk.Label(top, text="🌐", font=("Segoe UI", 10), fg=FG_MUTED,
                 bg=BG).pack(side="left")
        self.lang = tk.StringVar(value=LANGUAGES.get(i18n.current(), "English"))
        picker = ttk.Combobox(top, textvariable=self.lang, state="readonly",
                              values=list(LANGUAGES.values()), width=16,
                              font=FONT_SMALL)
        picker.pack(side="left", padx=(6, 0))
        picker.bind("<<ComboboxSelected>>", self._change_language)

        self.body = tk.Frame(self.outer, bg=BG)
        self.body.pack(fill="both", expand=True)

        nav = tk.Frame(self.outer, bg=BG)
        nav.pack(fill="x", pady=(GAP + 6, 0))
        self.progress = tk.Label(nav, text="", font=FONT_LABEL, fg=FG_MUTED, bg=BG)
        self.progress.pack(side="left")
        self.next_btn = theme.button(nav, "", self._next, primary=True)
        self.next_btn.pack(side="right")
        self.back_btn = theme.button(nav, "", self._back)

        self._render()

    # ------------------------------------------------------------- budulec

    def _clear_body(self) -> None:
        for child in self.body.winfo_children():
            child.destroy()

    def _heading(self, text: str, subtitle: str) -> None:
        tk.Label(self.body, text=text, font=FONT_BIG, fg=FG_TITLE, bg=BG,
                 anchor="w").pack(fill="x")
        tk.Label(self.body, text=subtitle, font=FONT_BODY, fg=FG_MUTED, bg=BG,
                 anchor="w", justify="left", wraplength=WRAP).pack(
            fill="x", pady=(TIGHT, GAP + 6))

    def _step(self, number: str, title: str) -> tk.Frame:
        row = tk.Frame(self.body, bg=BG)
        row.pack(fill="x", pady=(0, 2))
        tk.Label(row, text=number, font=FONT_HEAD, fg=BG, bg=FG_ACCENT,
                 width=3).pack(side="left")
        tk.Label(row, text=title, font=FONT_HEAD, fg=FG, bg=BG,
                 anchor="w").pack(side="left", padx=(10, 0))
        holder = tk.Frame(self.body, bg=BG)
        holder.pack(fill="x", padx=(22, 0), pady=(0, GAP + 2))
        return holder

    def _note(self, parent: tk.Widget, text: str) -> None:
        tk.Label(parent, text=text, font=FONT_SMALL, fg=FG_MUTED, bg=BG,
                 anchor="w", justify="left", wraplength=WRAP - 22).pack(
            fill="x", pady=(0, TIGHT))

    def _why(self, parent: tk.Widget, text: str) -> None:
        """Wyjasnienie 'dlaczego' - bez niego krok wyglada na kaprys."""
        tk.Label(parent, text=text, font=FONT_LABEL, fg=FG_ACCENT, bg=BG,
                 anchor="w", justify="left", wraplength=WRAP - 22).pack(fill="x")

    # -------------------------------------------------------------- strony

    def _render(self) -> None:
        self.root.title(t("setup.title"))
        self._clear_body()
        (self._page_document if self.page == 0 else self._page_steam)()
        self.progress.config(text=t("setup.step_of", n=self.page + 1))
        self.next_btn.config(text=t("setup.next") if self.page == 0
                             else t("setup.finish"))
        self.back_btn.config(text=t("setup.back"))
        if self.page == 0:
            self.back_btn.pack_forget()
        else:
            self.back_btn.pack(side="right", padx=(0, GAP))
        self.root.update_idletasks()
        self._centre()

    def _page_document(self) -> None:
        self._heading(t("setup.p1_title"), t("setup.p1_intro"))

        step = self._step("1", t("setup.p1_s1"))
        self._note(step, t("setup.p1_s1_note"))
        self._why(step, t("setup.p1_s1_why"))
        theme.button(step, t("setup.p1_s1_btn"), self._open_docs).pack(
            anchor="w", pady=(TIGHT, 0))

        step = self._step("2", t("setup.p1_s2"))
        row = tk.Frame(step, bg=BG)
        row.pack(fill="x")
        self.link = tk.StringVar(value=self._link_value)
        self.link.trace_add("write", lambda *_: setattr(self, "_link_value",
                                                        self.link.get()))
        theme.entry(row, self.link, width=44).pack(side="left", fill="x", expand=True)
        theme.button(row, t("setup.verify"), self._verify).pack(side="left",
                                                                padx=(GAP, 0))
        self.status = tk.Label(step, text="", font=FONT_SMALL, fg=FG_MUTED, bg=BG,
                               anchor="w", justify="left", wraplength=WRAP - 22)
        self.status.pack(fill="x", pady=(TIGHT, 0))

    def _page_steam(self) -> None:
        self._heading(t("setup.p2_title"), t("setup.p2_intro"))

        step = self._step("1", t("setup.p2_s1"))
        self._note(step, t("setup.p2_s1_note"))
        self._why(step, t("setup.p2_s1_why"))

        step = self._step("2", t("setup.p2_s2"))
        self._note(step, t("setup.p2_s2_note"))
        row = tk.Frame(step, bg=BG)
        row.pack(fill="x", pady=(TIGHT, 0))
        self.url_var = tk.StringVar(value=self._doc_url())
        url_entry = theme.entry(row, self.url_var, width=44)
        url_entry.pack(side="left", fill="x", expand=True)
        url_entry.config(state="readonly", readonlybackground=BG_PANEL)
        theme.button(row, t("setup.p2_copy"), self._copy_url).pack(side="left",
                                                                   padx=(GAP, 0))
        self.copy_status = tk.Label(step, text="", font=FONT_SMALL, fg=FG_OK, bg=BG,
                                    anchor="w")
        self.copy_status.pack(fill="x", pady=(2, 0))

        step = self._step("3", t("setup.p2_s3"))
        self._note(step, t("setup.p2_s3_note"))
        self._why(step, t("setup.p2_s3_why"))

    # -------------------------------------------------------------- akcje

    def _change_language(self, _event=None) -> None:
        for code, name in LANGUAGES.items():
            if name == self.lang.get():
                i18n.set_language(code)
                self.config["language"] = code
                break
        self._render()

    def _doc_url(self) -> str:
        doc_id = extract_doc_id(self._link_value)
        return DOC_URL.format(doc_id=doc_id) if doc_id else ""

    def _copy_url(self) -> None:
        url = self.url_var.get()
        if not url:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self.copy_status.config(text=t("setup.p2_copied"))

    def _open_docs(self) -> None:
        webbrowser.open("https://docs.new")

    def _set_status(self, text: str, colour: str) -> None:
        self.status.config(text=text, fg=colour)

    def _verify(self) -> None:
        doc_id = extract_doc_id(self.link.get())
        if not doc_id:
            self._set_status(t("setup.st_bad_link"), FG_ERROR)
            return
        self._set_status(t("setup.st_checking"), FG_MUTED)

        def job() -> None:
            # Import lokalny: kreator ma sie otworzyc natychmiast, a bridge
            # ciagnie za soba requests.
            from bridge import BridgeError, GoogleDocTransport
            try:
                GoogleDocTransport(doc_id).read()
            except BridgeError as exc:
                self.root.after(0, self._set_status, str(exc), FG_ERROR)
            except Exception as exc:  # noqa: BLE001
                self.root.after(0, self._set_status,
                                t("setup.st_failed", error=exc), FG_ERROR)
            else:
                self.root.after(0, self._set_status, t("setup.st_ok"), FG_OK)

        threading.Thread(target=job, daemon=True).start()

    def _next(self) -> None:
        if self.page == 0:
            if not extract_doc_id(self._link_value):
                self._set_status(t("setup.st_need_link"), FG_ERROR)
                return
            self.page = 1
            self._render()
            return
        self.config["gdoc_id"] = extract_doc_id(self._link_value)
        self.config["overlay_hotkey"] = "f7"
        self.saved = True
        self.root.destroy()

    def _back(self) -> None:
        self.page = 0
        self._render()

    def _skip(self) -> None:
        self.saved = False
        self.root.destroy()

    def _centre(self) -> None:
        width, height = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 3
        self.root.geometry(f"+{x}+{y}")

    def run(self) -> bool:
        self.root.mainloop()
        return self.saved


def needs_setup(config: dict) -> bool:
    return not extract_doc_id(config.get("gdoc_id", ""))
