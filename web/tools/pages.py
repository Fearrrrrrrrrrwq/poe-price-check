"""Strony narzedzi: PoE2 Regex Builder i Economy.

Po angielsku celowo: regex dopasowuje doslowny tekst angielskiego klienta gry,
a gracze szukaja tych narzedzi angielskimi frazami ("poe2 waystone regex",
"poe2 currency prices"). Tresc listy modow i opisy renderujemy po stronie
serwera - wyszukiwarka widzi je bez uruchamiania skryptow.

Funkcje przyjmuja pomocnikow z build.py (esc, asset, adres witryny), zeby nie
importowac build.py z powrotem.
"""

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
REGEX_DATA = HERE.parent / "assets" / "regex-data.json"

NAV = (
    ("/en/", "Price Checker"),
    ("/tools/poe2-regex/", "PoE2 Regex"),
    ("/tools/poe2-instill/", "PoE2 Instill"),
    ("/economy/", "Economy"),
)


def _shell(*, esc, asset, site_url, path, title, description, body, script,
           json_ld="") -> str:
    current = ' aria-current="page"'
    nav = "".join(
        f'<a href="{href}"{current if href == path else ""}>{esc(label)}</a>'
        for href, label in NAV)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <link rel="canonical" href="{site_url}{path}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="PoE Price Check">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{site_url}{path}">
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
<a class="skip" href="#main">Skip to content</a>
<header class="topbar">
  <div class="wrap wide bar">
    <a class="brand" href="/en/"><img src="{asset('icon.png')}" alt="" width="24" height="24">PoE Price Check</a>
    <nav aria-label="Tools">{nav}</nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer>
  <div class="wrap wide">
    <p class="footer-cta"><a href="/en/">PoE Price Check</a> — price check items in Path of Exile 1 &amp; 2, also on cloud gaming (Boosteroid).</p>
    <p class="disclaimer">Not affiliated with or endorsed by Grinding Gear Games.</p>
  </div>
</footer>
</body>
</html>
"""


def _faq_ld(pairs) -> str:
    return ('<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in pairs],
    }, ensure_ascii=False) + "</script>")


# --------------------------------------------------------------- regex builder

REGEX_FAQ = (
    ("How do I use regex in Path of Exile 2?",
     "Open your stash, a vendor window or the map device, click the search box, "
     "paste the generated text and matching items get highlighted. Everything in "
     "quotes is a regular expression; a leading ! means \"does not match\"."),
    ("Why is there a 250 character limit?",
     "The in-game search box accepts at most 250 characters. The builder uses the "
     "shortest fragment of each modifier that no other modifier contains, so you can "
     "fit many more mods into the limit than with full modifier texts."),
    ("Does it work with the game in another language?",
     "No. Search matches the item text the client displays, and the modifier texts "
     "here are English. Switch the client to English or adapt the fragments."),
    ("Are the modifier lists up to date?",
     "Waystone modifiers come from the game's own stat data and tablet modifiers "
     "from the official trade site's stat list, regenerated with each site update."),
)


def _mod_list(pool: list[dict], esc, kind: str) -> str:
    rows = []
    for mod in pool:
        also = (f' <span class="also" title="Also matches {mod["also"]} longer modifier(s) '
                f'containing this text">+{mod["also"]}</span>') if mod.get("also") else ""
        rows.append(
            f'<li data-frag="{esc(mod["frag"])}">'
            f'<span class="mod-text">{esc(mod["text"])}{also}</span>'
            f'<span class="seg" role="group" aria-label="{esc(mod["text"])}">'
            f'<button type="button" data-set="want">Want</button>'
            f'<button type="button" data-set="avoid">Avoid</button></span></li>')
    return (f'<ul class="mods" data-kind="{kind}">' + "".join(rows) + "</ul>")


def _threshold_rows(items: list[dict], esc, kind: str) -> str:
    rows = []
    for it in items:
        rows.append(
            f'<label class="thr" data-re="{esc(it["re"])}">'
            f'<input type="checkbox" data-role="on"> '
            f'<span>{esc(it["label"])}</span>'
            f'<input type="number" min="0" max="9999" value="{int(it["def"])}" '
            f'data-role="n" aria-label="{esc(it["label"])} minimum"></label>')
    return f'<div class="thresholds" data-kind="{kind}">' + "".join(rows) + "</div>"


def regex_page(*, esc, asset, site_url) -> str:
    data = json.loads(REGEX_DATA.read_text(encoding="utf-8"))
    faq = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>"
                  for q, a in REGEX_FAQ)

    def panel(kind, intro, mods_html, extra=""):
        hidden = "" if kind == "waystone" else " hidden"
        return (f'<div class="tool-panel" id="panel-{kind}" role="tabpanel" '
                f'aria-labelledby="tab-{kind}"{hidden}>'
                f'<p class="note">{intro}</p>{extra}'
                f'<div class="list-tools"><input type="search" class="filter" '
                f'placeholder="Filter modifiers…" aria-label="Filter modifiers">'
                f'<span class="picked" aria-live="polite"></span></div>'
                f'{mods_html}</div>')

    waystone_extra = ('<h3 class="sub">Minimum values</h3>'
                      + _threshold_rows(data["waystoneProps"], esc, "waystone")
                      + '<h3 class="sub">Modifiers</h3>')
    body = f"""
<section class="tool-hero">
  <div class="wrap wide">
    <p class="eyebrow">Path of Exile 2 · free tool</p>
    <h1>PoE2 Regex Builder</h1>
    <p class="lead">Build stash and vendor search strings for Waystones, Precursor
    Tablets and vendor items. Pick what you want and what to avoid, copy, paste
    into the in-game search.</p>
  </div>
</section>

<section class="tool">
  <div class="wrap wide tool-grid">
    <div class="tool-main">
      <div class="tool-tabs" role="tablist" aria-label="Item type">
        <button type="button" role="tab" id="tab-waystone" aria-controls="panel-waystone" aria-selected="true">Waystones</button>
        <button type="button" role="tab" id="tab-tablet" aria-controls="panel-tablet" aria-selected="false">Tablets</button>
        <button type="button" role="tab" id="tab-vendor" aria-controls="panel-vendor" aria-selected="false">Vendor</button>
      </div>
      {panel("waystone", f"{len(data['waystone'])} Waystone modifiers. <b>Want</b> highlights maps that have them, <b>Avoid</b> hides maps with them.", _mod_list(data["waystone"], esc, "waystone"), waystone_extra)}
      {panel("tablet", f"{len(data['tablet'])} Precursor Tablet modifiers.", _mod_list(data["tablet"], esc, "tablet"))}
      <div class="tool-panel" id="panel-vendor" role="tabpanel" aria-labelledby="tab-vendor" hidden>
        <p class="note">Tick the stats you are shopping for and set a minimum. Useful for
        levelling: movement speed boots, +skill level weapons, resistances.</p>
        {_threshold_rows(data["vendor"], esc, "vendor")}
      </div>
    </div>

    <aside class="tool-out" aria-label="Generated regex">
      <div class="out-card">
        <div class="out-head">
          <h2>Your regex</h2>
          <span class="counter" aria-live="polite"><b>0</b> / 250</span>
        </div>
        <textarea id="regex-out" readonly spellcheck="false" rows="5"
          placeholder="Pick modifiers to build a search string"></textarea>
        <div class="out-actions">
          <button type="button" class="btn primary" id="regex-copy" disabled>Copy</button>
          <button type="button" class="btn" id="regex-clear">Clear</button>
        </div>
        <fieldset class="mode">
          <legend>Wanted modifiers must match</legend>
          <label><input type="radio" name="mode" value="any" checked> any of them</label>
          <label><input type="radio" name="mode" value="all"> all of them</label>
        </fieldset>
        <p class="note small">Paste into the stash, vendor or map device search box.
        Only works with the English game client.</p>
      </div>
    </aside>
  </div>
</section>

<section class="band">
  <div class="wrap narrow">
    <h2>How PoE2 search regex works</h2>
    <ol class="how">
      <li><b>Quoted text is a pattern.</b> <code>"pack size"</code> highlights every item whose text contains it.</li>
      <li><b><code>|</code> means “or”.</b> <code>"mag|monster life"</code> matches either modifier.</li>
      <li><b>A leading <code>!</code> negates.</b> <code>"!regen|reflect"</code> hides items with any of them.</li>
      <li><b>Space-separated patterns must all match.</b> <code>"tier 1[5-6]\\)" "!regen"</code> — tier 15+ without the mod.</li>
    </ol>
    <h2 id="faq">FAQ</h2>
    <div class="faq">{faq}</div>
    <p class="note">Modifier data generated {esc(data["generated"])}.</p>
  </div>
</section>
"""
    return _shell(esc=esc, asset=asset, site_url=site_url, path="/tools/poe2-regex/",
                  title="PoE2 Regex Builder — Waystones, Tablets & Vendor Search",
                  description=("Free Path of Exile 2 regex builder: generate stash and vendor "
                               "search strings for Waystones, Precursor Tablets and vendor items "
                               "within the 250 character limit."),
                  body=body, script="regex.js", json_ld=_faq_ld(REGEX_FAQ))


# --------------------------------------------------------------------- economy

ECONOMY = {
    "poe2": {
        "path": "/economy/", "other": "/economy/poe1/", "name": "Path of Exile 2",
        "short": "PoE2",
        "title": "PoE2 Economy — Currency, Runes & Essence Prices",
        "description": ("Live Path of Exile 2 prices: Divine and Exalted Orb rates, runes, "
                        "essences, soul cores, uncut gems — with 24h, 7 day and 30 day change."),
    },
    "poe1": {
        "path": "/economy/poe1/", "other": "/economy/", "name": "Path of Exile",
        "short": "PoE1",
        "title": "PoE Economy — Currency, Unique & Scarab Prices",
        "description": ("Live Path of Exile prices: Divine Orb rate, unique items, scarabs, essences, "
                        "divination cards — with 24h, 7 day and 30 day change and league price history."),
    },
}

ECONOMY_FAQ = (
    ("Where do these prices come from?",
     "From poe.ninja, which aggregates the currency exchange and public stash tabs. "
     "Prices refresh every 30 minutes."),
    ("What do the 24h, 7d and 30d columns mean?",
     "The price change over the last day, week and month. 24h and 7d come from "
     "poe.ninja's price history; 30d comes from daily snapshots this site keeps, so it "
     "fills in during the first month of a league."),
    ("Do I need to know which category an item is in?",
     "No. Type at least two letters of any item name in the search box and the results "
     "come from every category at once, each marked with its category."),
    ("Can I see how a price changed over the league?",
     "Yes — click any row to open its price history for the whole league, with the league low, "
     "high and the change since the league started."),
    ("What does \"low confidence\" mean for unique items?",
     "The price is based on fewer than 10 listings, so it can be far off. Those items are hidden "
     "by default; untick \"Hide low confidence\" to see them. Unique prices are only available "
     "for Path of Exile 1 — Path of Exile 2 has no public stash data."),
    ("How do I price a rare item?",
     "Currency-style items are here. For rares and uniques use the free PoE Price Check "
     "app — it reads the item under your cursor and searches the official trade site."),
)


def economy_page(game: str, *, esc, asset, site_url) -> str:
    cfg = ECONOMY[game]
    faq = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>"
                  for q, a in ECONOMY_FAQ)
    on = ' class="on" aria-current="page"'
    switch = (f'<a href="/economy/"{on if game == "poe2" else ""}>PoE 2</a>'
              f'<a href="/economy/poe1/"{on if game == "poe1" else ""}>PoE 1</a>')
    body = f"""
<section class="tool-hero">
  <div class="wrap wide">
    <p class="eyebrow">{esc(cfg["name"])} · live prices</p>
    <h1>{esc(cfg["short"])} Economy</h1>
    <p class="lead">{"Currency, unique item" if game == "poe1" else "Currency and consumable"} prices for the current league,
    with price changes over the last day, week and month — click a row for its price history.</p>
  </div>
</section>

<section class="tool econ" data-game="{game}">
  <div class="wrap wide">
    <div class="econ-bar">
      <nav class="game-switch" aria-label="Game">{switch}</nav>
      <label class="field-inline">League
        <select id="econ-league" aria-label="League"><option>Loading…</option></select>
      </label>
      <input type="search" id="econ-search" placeholder="Search all items by name…" aria-label="Search all items by name">
      <label class="field-inline" id="econ-lowconf-wrap" hidden><input type="checkbox" id="econ-lowconf" checked> Hide low confidence</label>
      <p class="rates" id="econ-rates" aria-live="polite"></p>
    </div>
    <div class="chips" id="econ-types" role="tablist" aria-label="Category"></div>
    <div class="econ-table-wrap">
      <table class="econ-table" aria-describedby="econ-status">
        <thead><tr>
          <th scope="col" data-sort="name">Item</th>
          <th scope="col" data-sort="value" class="col-n">Value</th>
          <th scope="col" data-sort="change24h" class="col-n">24h</th>
          <th scope="col" data-sort="change7d" class="col-n">7d</th>
          <th scope="col" data-sort="change30d" class="col-n">30d</th>
          <th scope="col" data-sort="volume" class="col-n">Volume</th>
          <th scope="col" class="spark-col">Last 7 days</th>
        </tr></thead>
        <tbody id="econ-rows"></tbody>
      </table>
    </div>
    <p class="note" id="econ-status" aria-live="polite">Loading prices…</p>
    <p class="note small">Prices from <a href="https://poe.ninja" rel="noopener">poe.ninja</a>, refreshed every 30 minutes.</p>
  </div>
</section>

<section class="band">
  <div class="wrap narrow">
    <h2 id="faq">FAQ</h2>
    <div class="faq">{faq}</div>
  </div>
</section>
"""
    return _shell(esc=esc, asset=asset, site_url=site_url, path=cfg["path"],
                  title=cfg["title"], description=cfg["description"],
                  body=body, script="economy.js", json_ld=_faq_ld(ECONOMY_FAQ))
