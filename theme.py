"""Wspolny jezyk wizualny: kolory, czcionki, odstepy, ikona.

Trzymane w jednym miejscu, zeby okno wyceny i kreator pierwszego uruchomienia
wygladaly jak jeden program, a nie dwa rozne narzedzia.
"""

import ctypes
import sys
import tkinter as tk

from paths import resource_path

# DwmSetWindowAttribute: 20 na Win11 i Win10 2004+, 19 na starszych kompilacjach.
_DARK_MODE_ATTRIBUTES = (20, 19)
_DWMWA_CAPTION_COLOR = 35        # Win11 22000+; pozwala dobrac kolor belki dokladnie
_DWMWA_CORNER_PREFERENCE = 33    # Win11 22000+; zaokraglone rogi calego okna
_DWMWCP_ROUND = 2

# --- kolory -------------------------------------------------------------
#
# "Obsydian i zloto": tlo niemal czarne (nie brazowe jak poprzednio), karty
# odrozniaja sie samym jasniejszym wypelnieniem, bez ramek - to jest ten
# sam trik co w nowoczesnych ciemnych panelach (Linear, Vercel, GitHub):
# kontrast tla robi robote za bordery, wiec interfejs nie tnie sie na
# kwadraciki. Zloto zostaje, bo pasuje tematycznie (divine/exalted), ale
# jest bardziej nasycone - mniej "pergamin", wiecej "premium".
BG = "#0c0a07"           # tlo okna
BG_PANEL = "#1a160f"     # karty - jasniejsze o dwa stopnie od tla
BG_ROW = "#221d14"       # co drugi wiersz w tabelach
BG_ROW_HOVER = "#2a2318"  # wiersz pod kursorem
BG_INPUT = "#070604"     # pola do wpisywania
BORDER = "#2a2416"       # tylko tam, gdzie potrzebna wyrazna krawedz (pola, tabele)

FG = "#e8dcc0"           # tekst podstawowy - cieplejszy, wyzszy kontrast
FG_MUTED = "#8f826a"     # opisy, etykiety kolumn
FG_TITLE = "#f7deab"     # nazwa przedmiotu
FG_ACCENT = "#d9ad2e"    # akcent zlota - bardziej nasycony niz poprzednio
FG_ACCENT_HOVER = "#f0c33e"
FG_OK = "#6fcf7d"        # stan pozytywny
FG_WARN = "#e3a53f"      # ostrzezenie
FG_ERROR = "#e2685a"     # blad

# --- typografia -----------------------------------------------------------
#
# Consolas, nie cos nowszego (Cascadia Mono itp.) - jedyny monospace
# gwarantowany na kazdym Windows od Visty, bez ryzyka cichego przelaczenia
# sie na czcionke domyslna na maszynie, gdzie czegos nowszego nie ma.
FONT_TITLE = ("Segoe UI Semibold", 14)
FONT_HEAD = ("Segoe UI Semibold", 10)
FONT_BODY = ("Segoe UI", 9)
FONT_SMALL = ("Segoe UI", 8)
FONT_LABEL = ("Segoe UI", 8)
FONT_PRICE = ("Consolas", 10)
FONT_BADGE = ("Consolas", 8, "bold")
FONT_BIG = ("Segoe UI Semibold", 20)

# --- odstepy ----------------------------------------------------------------
PAD = 14    # margines okna
GAP = 10    # odstep miedzy sekcjami
TIGHT = 4   # odstep wewnatrz sekcji


def _hwnd_of(window: tk.Misc) -> int:
    """Uchwyt okna widziany przez Windows.

    winfo_id() oddaje uchwyt wewnetrznego okna Tk - belka tytulu nalezy do jego
    rodzica, wiec bez tego kroku DWM nie ma czego pomalowac.
    """
    window.update_idletasks()
    return ctypes.windll.user32.GetParent(window.winfo_id()) or window.winfo_id()


def dark_titlebar(window: tk.Misc) -> None:
    """Przestawia belke tytulu na ciemna.

    Bez tego nad ciemna aplikacja wisi jasny pasek Windows - najbardziej rzucajaca
    sie w oczy oznaka, ze to nie jest zaprojektowany program.

    Windows-only: DWM to mechanizm kompozytora okien Windows, macOS nie ma
    odpowiednika (tam belka tytulu sama podaza za trybem ciemnym systemu).
    """
    if sys.platform != "win32":
        return
    try:
        hwnd = _hwnd_of(window)
        enabled = ctypes.c_int(1)
        for attribute in _DARK_MODE_ATTRIBUTES:
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(enabled), ctypes.sizeof(enabled))
            if result == 0:
                break

        # Na Windows 11 mozemy dobrac odcien belki do tla aplikacji. Kolor idzie
        # jako 0x00BBGGRR, czyli odwrotnie niz w zapisie HTML.
        red, green, blue = (int(BG[i:i + 2], 16) for i in (1, 3, 5))
        colour = ctypes.c_int((blue << 16) | (green << 8) | red)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, _DWMWA_CAPTION_COLOR, ctypes.byref(colour), ctypes.sizeof(colour))

        # Zaokraglone rogi calego okna - natywny mechanizm kompozytora Win11,
        # nie rysunek. Na starszym Windows DwmSetWindowAttribute po prostu
        # zwroci blad dla tej stalej, co i tak lapiemy w except nizej -
        # okno zostaje kwadratowe, tak jak zawsze bylo.
        preference = ctypes.c_int(_DWMWCP_ROUND)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, _DWMWA_CORNER_PREFERENCE, ctypes.byref(preference),
            ctypes.sizeof(preference))
    except Exception:  # noqa: BLE001 - wyglad belki nie moze przerwac startu
        pass


def apply_icon(window: tk.Misc) -> None:
    """Ustawia ikone okna i ciemna belke. Brak pliku nie moze przerwac startu."""
    try:
        if sys.platform == "win32":
            window.iconbitmap(str(resource_path("icon.ico")))
        else:
            # Tk na macOS/Linux nie czyta formatu .ico przez iconbitmap -
            # potrzebuje PhotoImage, wiec bierzemy ten sam png co strona www.
            icon = tk.PhotoImage(file=str(resource_path("icon.png")))
            window.iconphoto(True, icon)
            window._icon_ref = icon  # PhotoImage znika, gdy nikt go nie trzyma
    except Exception:  # noqa: BLE001 - ikona to ozdoba, nie warunek dzialania
        pass
    dark_titlebar(window)


def button(parent: tk.Misc, text: str, command, primary: bool = False) -> tk.Button:
    """Przycisk w stylu aplikacji, z reakcja na najechanie.

    Tk nie ma stanu hover dla Button, wiec podpinamy go recznie - bez tego
    interfejs sprawia wrazenie martwego.
    """
    idle_bg = FG_ACCENT if primary else BG_ROW
    idle_fg = BG if primary else FG
    hover_bg = FG_ACCENT_HOVER if primary else BORDER

    widget = tk.Button(
        parent, text=text, command=command, font=FONT_BODY,
        bg=idle_bg, fg=idle_fg, activebackground=hover_bg, activeforeground=idle_fg,
        relief="flat", bd=0, padx=16, pady=7, cursor="hand2",
        highlightthickness=0,
    )
    widget.bind("<Enter>", lambda _e: widget.config(bg=hover_bg))
    widget.bind("<Leave>", lambda _e: widget.config(bg=idle_bg))
    return widget


def entry(parent: tk.Misc, textvariable=None, width: int = 20, **kwargs) -> tk.Entry:
    return tk.Entry(
        parent, textvariable=textvariable, width=width, font=FONT_BODY,
        bg=BG_INPUT, fg=FG, insertbackground=FG, relief="flat",
        highlightthickness=1, highlightbackground=BORDER, highlightcolor=FG_ACCENT,
        **kwargs,
    )


def checkbox(parent: tk.Misc, text: str, variable: tk.BooleanVar, command=None,
             bg: str = BG) -> tk.Checkbutton:
    """Checkbox w stylu aplikacji. Domyslny Tk na ciemnym tle jest nieczytelny
    bez recznego dobrania selectcolor (kwadracik zostaje bialy na bialym)."""
    return tk.Checkbutton(
        parent, text=text, variable=variable, command=command,
        font=FONT_BODY, fg=FG, bg=bg, activebackground=bg, activeforeground=FG,
        selectcolor=BG_INPUT, highlightthickness=0, bd=0, anchor="w",
        cursor="hand2",
    )


def keycap(parent: tk.Misc, text: str, bg: str = BG_PANEL) -> tk.Label:
    """Etykieta udajaca klawisz - czytelniejsza niz sam zolty tekst."""
    return tk.Label(
        parent, text=text.upper(), font=FONT_BADGE, fg=FG_TITLE, bg=BG_INPUT,
        padx=7, pady=3, highlightthickness=1, highlightbackground=BORDER,
    )


def card(parent: tk.Misc, accent: str | None = None) -> tk.Frame:
    """Kafelek z opcjonalnym paskiem akcentu po lewej.

    Bez ramki - elewacje robi sam kontrast BG_PANEL na BG, jak w kazdym
    wspolczesnym ciemnym panelu. Ramka na kazdym kafelku to byl ten
    "biurowy" akcent, ktorego sie tu celowo pozbywamy.
    """
    holder = tk.Frame(parent, bg=BG_PANEL, highlightthickness=0)
    if accent:
        tk.Frame(holder, bg=accent, width=3).pack(side="left", fill="y")
    body = tk.Frame(holder, bg=BG_PANEL)
    body.pack(side="left", fill="both", expand=True)
    holder.body = body  # type: ignore[attr-defined]
    return holder


def section(parent: tk.Misc, title: str) -> tuple[tk.Frame, tk.Frame]:
    """Ramka sekcji z naglowkiem. Zwraca (kontener, miejsce na tresc)."""
    box = tk.Frame(parent, bg=BG_PANEL, highlightthickness=0)
    head = tk.Frame(box, bg=BG_PANEL)
    head.pack(fill="x", padx=12, pady=(9, 4))
    tk.Frame(head, bg=FG_ACCENT, width=3, height=11).pack(side="left")
    tk.Label(head, text=title.upper(), font=FONT_LABEL, fg=FG_MUTED, bg=BG_PANEL,
             anchor="w").pack(side="left", padx=(6, 0))
    body = tk.Frame(box, bg=BG_PANEL)
    body.pack(fill="x", padx=6, pady=(0, 8))
    return box, body
