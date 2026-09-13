"""Strony narzedzi: regexy PoE1/PoE2 i Economy - w kazdym jezyku strony.

Adresy: angielska wersja zostaje pod dotychczasowym adresem (/tools/poe2-regex/,
/economy/ - te sa juz w indeksie Google), pozostale jezyki dostaja prefiks
(/pl/tools/poe2-regex/). Wszystkie wersje wskazuja na siebie hreflangiem.

Tlumaczymy interfejs i opisy (tools/tool_i18n.py). Nazwy modow, wlasciwosci,
kategorii i przedmiotow zostaja po angielsku - regex dopasowuje tekst
angielskiego klienta gry, a ceny maja angielskie nazwy z poe.ninja.

Tresc listy modow i opisy renderujemy po stronie serwera - wyszukiwarka widzi je
bez uruchamiania skryptow. Teksty potrzebne skryptom ida w <script
type="application/json" id="i18n">.

Funkcje przyjmuja pomocnikow z build.py (esc, asset, adres witryny), zeby nie
importowac build.py z powrotem.
"""

import json
import pathlib

from content import DEFAULT, LANGS
from tools.tool_i18n import texts

HERE = pathlib.Path(__file__).resolve().parent
REGEX_DATA = HERE.parent / "assets" / "regex-data.json"
MAP_REGEX_DATA = HERE.parent / "assets" / "map-regex-data.json"

# (adres angielski, klucz etykiety)
NAV = (
    ("/tools/poe-map-regex/", "nav_poe1"),
    ("/tools/poe2-regex/", "nav_poe2"),
    ("/tools/poe2-instill/", "nav_instill"),
    ("/economy/", "nav_economy"),
)
TOOL_PATHS = ("/tools/poe-map-regex/", "/tools/poe2-regex/", "/tools/poe2-instill/",
              "/economy/", "/economy/poe1/")

# Klucze, ktore czytaja skrypty stron (reszta jest juz w HTML).
REGEX_JS_KEYS = ("copy", "copied", "copy_link", "link_in_bar", "picked")
INSTILL_JS_KEYS = ("in_pick", "in_none", "in_count", "in_count_of")
ECONOMY_JS_KEYS = ("ec_history_loading", "ec_history_short", "ec_history_error", "ec_now", "ec_low",
                   "ec_high", "ec_since", "ec_show_table", "ec_day", "ec_price_unit", "ec_chart_aria",
                   "ec_low_tag", "ec_results", "ec_no_results", "ec_for_query", "ec_top", "ec_searching",
                   "ec_click_row", "ec_items", "ec_updated", "ec_prices_error", "ec_leagues_error",
                   "ec_search", "ec_loading", "ec_col_volume", "ec_col_listed", "ec_col_vol_listed")


def tool_url(lang: str, path: str) -> str:
    """Adres narzedzia w danym jezyku (angielski bez prefiksu)."""
    return path if lang == DEFAULT else f"/{lang}{path}"


def _shell(*, lang, esc, asset, site_url, path, title, description, body, script,
           json_ld="", js_text=None) -> str:
    t = texts(lang)
    current = ' aria-current="page"'
    nav = f'<a href="/{lang}/">{esc(t["nav_home"])}</a>' + "".join(
        f'<a href="{tool_url(lang, href)}"{current if href == path else ""}>{esc(t[key])}</a>'
        for href, key in NAV)
    alternates = "\n  ".join(
        f'<link rel="alternate" hreflang="{code}" href="{site_url}{tool_url(code, path)}">'
        for code in LANGS)
    alternates += f'\n  <link rel="alternate" hreflang="x-default" href="{site_url}{path}">'
    active = ' aria-current="true"'
    langs = "".join(
        f'<a href="{tool_url(code, path)}" hreflang="{code}" lang="{code}"'
        f'{active if code == lang else ""}>{esc(label)}</a>'
        for code, label in LANGS.items())
    i18n = ""
    if js_text:
        payload = json.dumps({k: t[k] for k in js_text}, ensure_ascii=False).replace("</", "<\\/")
        i18n = f'<script type="application/json" id="i18n">{payload}</script>'
    url = site_url + tool_url(lang, path)
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <link rel="canonical" href="{url}">
  {alternates}
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="PoE Price Check">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{site_url}/assets/og.png">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="{asset('icon.png')}" type="image/png">
  <link rel="stylesheet" href="{asset('style.css')}">
  <link rel="stylesheet" href="{asset('tools.css')}">
  <script src="{asset('hit.js')}" defer></script>
  <script src="{asset(script)}" defer></script>
  {json_ld}
</head>
<body class="tool-page">
<a class="skip" href="#main">{esc(t["skip"])}</a>
<header class="topbar">
  <div class="wrap wide bar">
    <a class="brand" href="/{lang}/"><img src="{asset('icon.png')}" alt="" width="24" height="24">PoE Price Check</a>
    <nav aria-label="{esc(t["nav_aria"])}">{nav}</nav>
  </div>
</header>
<main id="main">
{body}
</main>
{i18n}
<footer>
  <div class="wrap wide">
    <p class="footer-cta"><a href="/{lang}/">PoE Price Check</a> — {esc(t["footer_cta"])}</p>
    <nav class="langs" aria-label="{esc(t["lang_aria"])}">{langs}</nav>
    <p class="disclaimer">{esc(t["disclaimer"])}</p>
  </div>
</footer>
</body>
</html>
"""


def _faq(t: dict, esc, prefix: str, count: int) -> tuple[str, str]:
    pairs = [(t[f"{prefix}_q{n}"], t[f"{prefix}_a{n}"]) for n in range(1, count + 1)]
    html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in pairs)
    return html, _faq_ld(pairs)


def _faq_ld(pairs) -> str:
    return ('<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in pairs],
    }, ensure_ascii=False).replace("</", "<\\/") + "</script>")


def _how(t: dict, esc, example_code: str, example_text: str) -> str:
    code = lambda s: f"<code>{esc(s)}</code>"  # noqa: E731
    return "".join(f"<li>{item}</li>" for item in (
        t["how1_html"].format(code=code('"regen"')),
        t["how2_html"].format(bar=code("|"), code=code('"enfee|vulne"')),
        t["how3_html"].format(bang=code("!"), code=code('"!regen|be le"')),
        t["how4_html"].format(code=code(example_code), example=esc(example_text)),
    ))


# --------------------------------------------------------------- regex builder

def _mod_list(pool: list[dict], esc, kind: str, t: dict) -> str:
    rows = []
    for mod in pool:
        also = (f' <span class="also" title="{esc(t["also_title"].format(n=mod["also"]))}">'
                f'+{mod["also"]}</span>') if mod.get("also") else ""
        t17 = mod.get("t17")
        badge = f' <span class="tag-t17" title="{esc(t["t17_title"])}">T17</span>' if t17 else ""
        rows.append(
            f'<li data-frag="{esc(mod["frag"])}"{" data-t17" if t17 else ""}>'
            f'<span class="mod-text">{esc(mod["text"])}{badge}{also}</span>'
            f'<span class="seg" role="group" aria-label="{esc(mod["text"])}">'
            f'<button type="button" data-set="want">{esc(t["want"])}</button>'
            f'<button type="button" data-set="avoid">{esc(t["avoid"])}</button></span></li>')
    return (f'<ul class="mods" data-kind="{kind}">' + "".join(rows) + "</ul>")


def _threshold_rows(items: list[dict], esc, kind: str, t: dict) -> str:
    rows = []
    for it in items:
        label = it["label"]
        if it.get("group") == "job" and label.endswith(" level"):
            label = t["job_label"].format(job=label[: -len(" level")])
        # def None = prog "jest/nie ma" (np. "Adds # to # Fire Damage") - bez pola liczby.
        number = ("" if it["def"] is None else
                  f'<input type="number" min="0" max="9999" value="{int(it["def"])}" '
                  f'data-role="n" aria-label="{esc(t["minimum_aria"].format(label=label))}">')
        ident = f' data-id="{esc(it["id"])}"' if it.get("id") else ""
        rows.append(
            f'<label class="thr" data-re="{esc(it["re"])}"{ident}>'
            f'<input type="checkbox" data-role="on"> '
            f'<span>{esc(label)}</span>{number}</label>')
    return f'<div class="thresholds" data-kind="{kind}">' + "".join(rows) + "</div>"


def _tabs(t: dict, esc, tabs: tuple) -> str:
    buttons = []
    for i, (kind, key) in enumerate(tabs):
        first = i == 0
        buttons.append(f'<button type="button" role="tab" id="tab-{kind}" aria-controls="panel-{kind}" '
                       f'aria-selected="{"true" if first else "false"}" tabindex="{0 if first else -1}">'
                       f'{esc(t[key])}</button>')
    return (f'<div class="tool-tabs" role="tablist" aria-label="{esc(t["item_type_aria"])}">'
            + "".join(buttons) + "</div>")


def _panel(kind: str, content: str, first: bool = False) -> str:
    hidden = "" if first else " hidden"
    return (f'<div class="tool-panel" id="panel-{kind}" role="tabpanel" '
            f'aria-labelledby="tab-{kind}"{hidden}>{content}</div>')


def _list_tools(t: dict, esc, extra: str = "") -> str:
    return (f'<div class="list-tools"><input type="search" class="filter" '
            f'placeholder="{esc(t["filter"])}" aria-label="{esc(t["filter"])}">'
            f'{extra}<span class="picked" aria-live="polite"></span></div>')


def _out_card(t: dict, esc, *, store: str, placeholder: str, legend: str, note: str) -> str:
    store_attr = f' data-store="{store}"' if store else ""
    return f"""
    <aside class="tool-out" aria-label="{esc(t["generated_aria"])}">
      <div class="out-card">
        <div class="out-head">
          <h2>{esc(t["your_regex"])}</h2>
          <span class="counter" aria-live="polite"><b>0</b> / 250</span>
        </div>
        <textarea id="regex-out"{store_attr} readonly spellcheck="false" rows="5"
          placeholder="{esc(placeholder)}"></textarea>
        <div class="out-actions">
          <button type="button" class="btn primary" id="regex-copy" disabled>{esc(t["copy"])}</button>
          <button type="button" class="btn" id="regex-share" disabled>{esc(t["copy_link"])}</button>
          <button type="button" class="btn" id="regex-clear">{esc(t["clear"])}</button>
        </div>
        <fieldset class="mode">
          <legend>{esc(legend)}</legend>
          <label><input type="radio" name="mode" value="any" checked> {esc(t["mode_any"])}</label>
          <label><input type="radio" name="mode" value="all"> {esc(t["mode_all"])}</label>
        </fieldset>
        <p class="note small">{esc(note)} {esc(t["english_only"])}</p>
      </div>
    </aside>"""


def regex_page(lang: str, *, esc, asset, site_url) -> str:
    t = texts(lang)
    data = json.loads(REGEX_DATA.read_text(encoding="utf-8"))
    faq, faq_ld = _faq(t, esc, "r2", 4)
    note = lambda key, **kw: t[key].format(want=esc(t["want"]), avoid=esc(t["avoid"]), **kw)  # noqa: E731

    waystone = _panel("waystone", (
        f'<p class="note">{note("r2_waystone_note_html", n=len(data["waystone"]))}</p>'
        f'<h3 class="sub">{esc(t["min_values"])}</h3>'
        + _threshold_rows(data["waystoneProps"], esc, "waystone", t)
        + f'<h3 class="sub">{esc(t["modifiers"])}</h3>'
        + _list_tools(t, esc) + _mod_list(data["waystone"], esc, "waystone", t)), first=True)
    tablet = _panel("tablet", (
        f'<p class="note">{esc(t["r2_tablet_note"].format(n=len(data["tablet"])))}</p>'
        + _list_tools(t, esc) + _mod_list(data["tablet"], esc, "tablet", t)))
    vendor = _panel("vendor", (
        f'<p class="note">{esc(t["r2_vendor_note"])}</p>'
        + _threshold_rows(data["vendor"], esc, "vendor", t)))

    how = _how(t, esc, '"tier 1[5-6]\\)" "!regen"', t["r2_how_example"])
    body = f"""
<section class="tool-hero">
  <div class="wrap wide">
    <p class="eyebrow">Path of Exile 2 · {esc(t["free_tool"])}</p>
    <h1>{esc(t["r2_h1"])}</h1>
    <p class="lead">{esc(t["r2_lead"])}</p>
  </div>
</section>

<section class="tool">
  <div class="wrap wide tool-grid">
    <div class="tool-main">
      {_tabs(t, esc, (("waystone", "tab_waystones"), ("tablet", "tab_tablets"), ("vendor", "tab_vendor")))}
      {waystone}
      {tablet}
      {vendor}
    </div>
{_out_card(t, esc, store="", placeholder=t["r2_placeholder"], legend=t["mode_legend"], note=t["r2_paste"])}
  </div>
</section>

<section class="band">
  <div class="wrap narrow">
    <h2>{esc(t["r2_how_title"])}</h2>
    <ol class="how">{how}</ol>
    <h2 id="faq">{esc(t["faq"])}</h2>
    <div class="faq">{faq}</div>
    <p class="note">{esc(t["data_generated"].format(date=data["generated"]))}</p>
  </div>
</section>
"""
    return _shell(lang=lang, esc=esc, asset=asset, site_url=site_url, path="/tools/poe2-regex/",
                  title=t["r2_title"], description=t["r2_desc"], body=body, script="regex.js",
                  json_ld=faq_ld, js_text=REGEX_JS_KEYS)


# ------------------------------------------------------------ PoE1 regex

# Szybkie zestawy "Avoid" - dopasowanie po tekscie moda, zeby przetrwaly
# regeneracje danych (fragmenty sie zmieniaja, teksty nie).
MAP_PRESETS = (
    ("preset_regen", ("cannot regenerate", "less recovery rate of life")),
    ("preset_leech", ("cannot be leeched", "recovery per second from leech")),
    ("preset_curses", ("are cursed with", "less effect of curses")),
    ("preset_maxres", ("maximum resistances",)),
    ("preset_thorns", ("thorns reflecting",)),
    ("preset_block", ("cannot block", "reduced chance to block")),
    ("preset_flasks", ("effect of flasks", "meteor when they use a flask")),
)


def map_regex_page(lang: str, *, esc, asset, site_url) -> str:
    t = texts(lang)
    data = json.loads(MAP_REGEX_DATA.read_text(encoding="utf-8"))
    pool = data["maps"]["mods"]
    faq, faq_ld = _faq(t, esc, "r1", 8)
    presets = []
    for key, keys in MAP_PRESETS:
        frags = [m["frag"] for m in pool if any(k in m["text"].lower() for k in keys)]
        if frags:
            presets.append(f'<button type="button" data-set="avoid" data-frags="{esc(json.dumps(frags))}" '
                           f'title="{esc(t["preset_count"].format(n=len(frags)))}">{esc(t[key])}</button>')
    t17_count = sum(1 for m in pool if m.get("t17"))

    def grouped(mods, kind, titles):
        html = ""
        for group, key in titles:
            part = [m for m in mods if m.get("group", "mod") == group]
            if part:
                html += (f'<h3 class="sub">{esc(t[key])} <span class="count">{len(part)}</span></h3>'
                         + _mod_list(part, esc, kind, t))
        return html

    heist_props = [p for p in data["heist"]["props"] if p.get("group") != "job"]
    heist_jobs = [p for p in data["heist"]["props"] if p.get("group") == "job"]
    heist_mods = data["heist"]["mods"]
    want_avoid = dict(want=esc(t["want"]), avoid=esc(t["avoid"]))

    maps_panel = _panel("maps", f"""
        <h3 class="sub">{esc(t["min_values"])}</h3>
        {_threshold_rows(data["maps"]["props"], esc, "maps", t)}
        <h3 class="sub">{esc(t["modifiers"])}</h3>
        <p class="note">{t["r1_maps_note_html"].format(n=len(pool), **want_avoid)}</p>
        <div class="presets" role="group" aria-label="{esc(t["quick_avoid_aria"])}"><span>{esc(t["quick_avoid"])}</span>{"".join(presets)}</div>
        {_list_tools(t, esc, f'<label class="field-inline"><input type="checkbox" id="hide-t17"> {esc(t["hide_t17"].format(n=t17_count))}</label>')}
        {_mod_list(pool, esc, "maps", t)}""", first=True)

    link_opts = f'<option value="0">{esc(t["link_any"])}</option>' + "".join(
        f'<option value="{n}">{esc(t["link_n"].format(n=n))}</option>' for n in range(2, 7))
    colour_inputs = "".join(
        f'<label class="sock-colour {c}"><span>{esc(t[key])}</span>'
        f'<input type="number" min="0" max="6" value="0" data-role="{c}" '
        f'aria-label="{esc(t["colour_aria"].format(colour=t[key]))}"></label>'
        for c, key in (("r", "red"), ("g", "green"), ("b", "blue")))
    vendor_panel = _panel("vendor", f"""
        <p class="note">{esc(t["r1_vendor_note"])}</p>
        <h3 class="sub">{esc(t["sockets"])}</h3>
        <div class="sockets">
          <label class="field-inline">{esc(t["linked_group"])} <select data-role="links" aria-label="{esc(t["linked_aria"])}">{link_opts}</select></label>
          {colour_inputs}
          <p class="note small">{esc(t["sockets_note"])}</p>
        </div>
        <h3 class="sub">{esc(t["stats"])}</h3>
        {_threshold_rows(data["vendor"]["props"], esc, "vendor", t)}""")

    heist_panel = _panel("heist", f"""
        <p class="note">{esc(t["r1_heist_note"])}</p>
        <h3 class="sub">{esc(t["min_values"])}</h3>
        {_threshold_rows(heist_props, esc, "heist", t)}
        <h3 class="sub">{esc(t["job_title"])}</h3>
        <p class="note small">{esc(t["job_note"])}</p>
        {_threshold_rows(heist_jobs, esc, "heist", t)}
        <h3 class="sub">{esc(t["modifiers"])} <span class="count">{len(heist_mods)}</span></h3>
        {_list_tools(t, esc)}
        {_mod_list(heist_mods, esc, "heist", t)}""")

    logbook_panel = _panel("logbook", f"""
        <p class="note">{esc(t["r1_logbook_note"])}</p>
        <h3 class="sub">{esc(t["min_values"])}</h3>
        {_threshold_rows(data["logbook"]["props"], esc, "logbook", t)}
        {_list_tools(t, esc)}
        {grouped(data["logbook"]["mods"], "logbook", (("faction", "factions"), ("bonus", "bonuses"), ("mod", "modifiers")))}""")

    tabs = _tabs(t, esc, (("maps", "tab_maps"), ("vendor", "tab_vendor"), ("heist", "tab_heist"),
                          ("logbook", "tab_logbooks")))
    how = _how(t, esc, '"quantity: .(9\\d|\\d\\d\\d)%" "!regen"', t["r1_how_example"])
    body = f"""
<section class="tool-hero">
  <div class="wrap wide">
    <p class="eyebrow">Path of Exile 1 · {esc(t["free_tool"])}</p>
    <h1>{esc(t["r1_h1"])}</h1>
    <p class="lead">{esc(t["r1_lead"])}</p>
  </div>
</section>

<section class="tool">
  <div class="wrap wide tool-grid">
    <div class="tool-main">
      {tabs}
      {maps_panel}
      {vendor_panel}
      {heist_panel}
      {logbook_panel}
    </div>
{_out_card(t, esc, store="poe1-map-regex-v1", placeholder=t["r1_placeholder"], legend=t["mode_legend_poe1"], note=t["r1_apply_note"])}
  </div>
</section>

<section class="band">
  <div class="wrap narrow">
    <h2>{esc(t["r1_how_title"])}</h2>
    <ol class="how">{how}</ol>
    <h2 id="faq">{esc(t["faq"])}</h2>
    <div class="faq">{faq}</div>
    <p class="note">{esc(t["data_generated"].format(date=data["generated"]))}</p>
  </div>
</section>
"""
    return _shell(lang=lang, esc=esc, asset=asset, site_url=site_url, path="/tools/poe-map-regex/",
                  title=t["r1_title"], description=t["r1_desc"], body=body, script="regex.js",
                  json_ld=faq_ld, js_text=REGEX_JS_KEYS)


# --------------------------------------------------------------------- economy

ECONOMY = {
    "poe2": {"path": "/economy/", "name": "Path of Exile 2", "short": "PoE2"},
    "poe1": {"path": "/economy/poe1/", "name": "Path of Exile", "short": "PoE1"},
}


def economy_page(game: str, lang: str, *, esc, asset, site_url) -> str:
    t = texts(lang)
    cfg = ECONOMY[game]
    faq, faq_ld = _faq(t, esc, "ec", 6)
    on = ' class="on" aria-current="page"'
    switch = (f'<a href="{tool_url(lang, "/economy/")}"{on if game == "poe2" else ""}>PoE 2</a>'
              f'<a href="{tool_url(lang, "/economy/poe1/")}"{on if game == "poe1" else ""}>PoE 1</a>')
    source = t["ec_source_html"].format(link='<a href="https://poe.ninja" rel="noopener">poe.ninja</a>')
    body = f"""
<section class="tool-hero">
  <div class="wrap wide">
    <p class="eyebrow">{esc(cfg["name"])} · {esc(t["ec_live"])}</p>
    <h1>{esc(t["ec_h1"].format(game=cfg["short"]))}</h1>
    <p class="lead">{esc(t["ec_lead_" + game])}</p>
  </div>
</section>

<section class="tool econ" data-game="{game}">
  <div class="wrap wide">
    <div class="econ-bar">
      <nav class="game-switch" aria-label="{esc(t["ec_game_aria"])}">{switch}</nav>
      <label class="field-inline">{esc(t["ec_league"])}
        <select id="econ-league" aria-label="{esc(t["ec_league"])}"><option>{esc(t["ec_loading_leagues"])}</option></select>
      </label>
      <input type="search" id="econ-search" placeholder="{esc(t["ec_search"])}" aria-label="{esc(t["ec_search"])}">
      <label class="field-inline" id="econ-lowconf-wrap" hidden><input type="checkbox" id="econ-lowconf" checked> {esc(t["ec_hide_low"])}</label>
      <p class="rates" id="econ-rates" aria-live="polite"></p>
    </div>
    <div class="chips" id="econ-types" role="tablist" aria-label="{esc(t["ec_category_aria"])}"></div>
    <div class="econ-table-wrap">
      <table class="econ-table" aria-describedby="econ-status">
        <thead><tr>
          <th scope="col" data-sort="name">{esc(t["ec_col_item"])}</th>
          <th scope="col" data-sort="value" class="col-n">{esc(t["ec_col_value"])}</th>
          <th scope="col" data-sort="change24h" class="col-n">24h</th>
          <th scope="col" data-sort="change7d" class="col-n">7d</th>
          <th scope="col" data-sort="change30d" class="col-n">30d</th>
          <th scope="col" data-sort="volume" class="col-n">{esc(t["ec_col_volume"])}</th>
          <th scope="col" class="spark-col">{esc(t["ec_col_spark"])}</th>
        </tr></thead>
        <tbody id="econ-rows"></tbody>
      </table>
    </div>
    <p class="note" id="econ-status" aria-live="polite">{esc(t["ec_loading"])}</p>
    <p class="note small">{source}</p>
  </div>
</section>

<section class="band">
  <div class="wrap narrow">
    <h2 id="faq">{esc(t["faq"])}</h2>
    <div class="faq">{faq}</div>
  </div>
</section>
"""
    return _shell(lang=lang, esc=esc, asset=asset, site_url=site_url, path=cfg["path"],
                  title=t[f"ec_{game}_title"], description=t[f"ec_{game}_desc"],
                  body=body, script="economy.js", json_ld=faq_ld, js_text=ECONOMY_JS_KEYS)
