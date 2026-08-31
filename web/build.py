"""Generator statycznej strony poe-price-check.

Kazdy jezyk dostaje WLASNY adres (/pl/, /en/ ...) z hreflang. Przelaczanie jezyka
wylacznie po stronie przegladarki byloby dla wyszukiwarek niewidoczne - zostalaby
zaindeksowana jedna wersja i tyle.

Uruchomienie:  python web/build.py
Wynik:         web/dist/  - gotowe do wrzucenia na Cloudflare Pages / Netlify / GitHub Pages
"""

import hashlib
import html
import json
import os
import pathlib
import shutil
import subprocess
import sys
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from content import C, DEFAULT, LANGS, LOCALES
from privacy_content import PRIVACY
# Wersja i sklejanie archiwum siedza w package.py, zeby plik ze strony
# i plik z wydania na GitHubie byly identyczne.
from package import APP_VERSION, ARCHIVE_NAME

HERE = pathlib.Path(__file__).parent
DIST = HERE / "dist"

# --- do zmiany przed wdrozeniem ---------------------------------------------
#
# Adres witryny wchodzi w canonical, hreflang, sitemap i og:image, wiec musi
# byc TEN, pod ktorym strona naprawde stoi. Zla wartosc nie wywala niczego -
# po prostu wyszukiwarki zaindeksuja nieistniejace adresy.
#
# Da sie go podac zmienna srodowiskowa, zeby nie edytowac kodu przy kazdym
# wdrozeniu:  SITE_URL=https://poe.twojadomena.pl python build.py
SITE_URL = os.environ.get("SITE_URL", "https://poe-price-check.pages.dev").rstrip("/")
# Adres repozytorium. Puste = przycisk "kod zrodlowy" w ogole sie nie pokaze -
# lepiej go nie miec niz miec taki, ktory prowadzi w 404.
SOURCE_URL = os.environ.get(
    "SOURCE_URL", "https://github.com/Fearrrrrrrrrrwq/poe-price-check")

# Zaproszenie na Discorda. Puste = przycisk w ogole sie nie pokaze, tak samo jak
# przy adresie repozytorium - lepiej go nie miec niz miec martwy.
#
# Zaproszenia Discorda potrafia wygasnac. To jest ustawione jako bezterminowe,
# ale gdyby kiedys przestalo dzialac, podmiana idzie tutaj albo zmienna
# srodowiskowa DISCORD_URL - bez szukania po szablonach stron.
DISCORD_URL = os.environ.get(
    "DISCORD_URL", "https://discord.gg/FjAnFqGNh4")

# Pobieranie prowadzi do artefaktu z wydania na GitHubie, a nie do kopii
# trzymanej tutaj.
#
# Powod jest konkretny: PyInstaller nie buduje bajt w bajt powtarzalnie, wiec
# plik zbudowany lokalnie ma inna sume kontrolna niz ten z CI. Trzymanie
# wlasnej kopii oznaczalo dwa rozne binaria pod ta sama wersja - a suma
# kontrolna, ktora sie nie zgadza, jest gorsza niz jej brak.
#
# Skutek uboczny na plus: github.com ma reputacje, ktorej swieza domena nie ma,
# wiec przegladarki rzadziej strasza przy pobieraniu.
DOWNLOAD_FILE = ARCHIVE_NAME
DOWNLOAD_URL = os.environ.get(
    "DOWNLOAD_URL",
    f"{SOURCE_URL}/releases/download/v{APP_VERSION}/{ARCHIVE_NAME}")

# Wpis na liste preload jest praktycznie nieodwracalny - wykreslenie trwa
# miesiacami, a do tego czasu przegladarki odmawiaja polaczenia po http z cala
# domena. Dlatego domyslnie go NIE wysylamy. Wlacz swiadomie, gdy strona
# jest juz stabilna:  HSTS_PRELOAD=1 python build.py
HSTS_PRELOAD = os.environ.get("HSTS_PRELOAD") == "1"


def esc(text: str) -> str:
    return html.escape(text, quote=True)


_ASSET_HASHES: dict[str, str] = {}


def asset(name: str) -> str:
    """Adres zasobu ze znacznikiem tresci: /assets/style.css?v=a1b2c3d4.

    Bez tego po zmianie wygladu przegladarki przez kilka godzin serwuja stary
    arkusz z pamieci podrecznej - zmiana adresu jest jedynym pewnym sposobem,
    zeby pobraly nowy. Znacznik liczymy z zawartosci pliku, wiec zmienia sie
    dokladnie wtedy, gdy zmieni sie plik.
    """
    if name not in _ASSET_HASHES:
        path = HERE / "assets" / name
        if not path.exists():          # ikona lezy poziom wyzej
            path = HERE.parent / name
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:8]
        _ASSET_HASHES[name] = digest
    return f"/assets/{name}?v={_ASSET_HASHES[name]}"


def hreflangs(current: str) -> str:
    """Linki alternatywne - bez nich Google uzna wersje jezykowe za duplikaty."""
    rows = [f'<link rel="alternate" hreflang="{code}" '
            f'href="{SITE_URL}/{code}/">' for code in LANGS]
    rows.append(f'<link rel="alternate" hreflang="x-default" '
                f'href="{SITE_URL}/{DEFAULT}/">')
    return "\n  ".join(rows)


def json_ld(lang: str, t: dict) -> str:
    """Dane strukturalne: aplikacja + FAQ. FAQ potrafi dac wynik rozszerzony."""
    app = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "PoE Price Check",
        "applicationCategory": "UtilitiesApplication",
        "operatingSystem": "Windows 10, Windows 11",
        "softwareVersion": APP_VERSION,
        "inLanguage": list(LANGS),
        "description": t["description"],
        "url": f"{SITE_URL}/{lang}/",
        "downloadUrl": DOWNLOAD_URL,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "license": "https://opensource.org/licenses/MIT",
    }
    if SOURCE_URL:
        app["codeRepository"] = SOURCE_URL
    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": t[f"faq_{n}_q"],
             "acceptedAnswer": {"@type": "Answer", "text": t[f"faq_{n}_a"]}}
            for n in (1, 2, 3, 4)
        ],
    }
    return "\n".join(
        f'<script type="application/ld+json">{json.dumps(item, ensure_ascii=False)}</script>'
        for item in (app, faq))


def source_button(t: dict) -> str:
    """Przycisk z kodem zrodlowym - tylko gdy jest dokad kierowac."""
    if not SOURCE_URL:
        return ""
    return (f'<a class="btn" href="{SOURCE_URL}" rel="noopener noreferrer">'
            f'{esc(t["download_alt"])}</a>')


def mac_button(t: dict) -> str:
    """Przycisk macOS - nie ma gotowej paczki .app, wiec kieruje do sekcji
    'macOS (experimental)' w README na GitHubie zamiast do pobrania binarki."""
    if not SOURCE_URL:
        return ""
    return (f'<a class="btn" href="{SOURCE_URL}#macos-experimental" '
            f'rel="noopener noreferrer">{esc(t["download_mac_cta"])}</a>')


# Znak Discorda wklejony wprost w HTML, a nie jako <img>. Powod jest taki sam
# jak przy reszcie zasobow: to jedno zapytanie mniej, ikona nie mrugnie przed
# zaladowaniem, a CSP nie musi dopuszczac zadnego zewnetrznego zrodla.
DISCORD_MARK = (
    '<svg class="ico" viewBox="0 0 24 18" width="18" height="14" aria-hidden="true"'
    ' focusable="false"><path fill="currentColor" d="M20.3 1.6A19.8 19.8 0 0 0 15.4.1'
    'a13.8 13.8 0 0 0-.6 1.3 18.3 18.3 0 0 0-5.5 0A13.6 13.6 0 0 0 8.6.1'
    ' 19.7 19.7 0 0 0 3.7 1.6C.6 6.2-.3 10.7.2 15.1a19.9 19.9 0 0 0 6 3'
    'c.5-.7.9-1.4 1.3-2.1a13 13 0 0 1-2-1c.2-.1.4-.3.5-.4a14.2 14.2 0 0 0 12.2 0'
    'l.5.4c-.6.4-1.3.7-2 1 .4.7.8 1.4 1.3 2.1a19.8 19.8 0 0 0 6-3'
    'c.6-5.1-.9-9.6-3.7-13.5ZM8.0 12.4c-1.2 0-2.2-1.1-2.2-2.4S6.8 7.6 8 7.6'
    's2.2 1.1 2.2 2.4-1 2.4-2.2 2.4Zm8 0c-1.2 0-2.2-1.1-2.2-2.4s1-2.4 2.2-2.4'
    ' 2.2 1.1 2.2 2.4-1 2.4-2.2 2.4Z"/></svg>')


def discord_button(t: dict, primary: bool = False) -> str:
    """Przycisk zaproszenia na Discorda - tylko gdy jest dokad kierowac."""
    if not DISCORD_URL:
        return ""
    css = "btn discord primary" if primary else "btn discord"
    return (f'<a class="{css}" href="{DISCORD_URL}" target="_blank"'
            f' rel="noopener noreferrer">{DISCORD_MARK}'
            f'<span>{esc(t["discord_cta"])}</span></a>')


def lang_switch(current: str) -> str:
    items = []
    for code, label in LANGS.items():
        active = ' aria-current="true"' if code == current else ""
        items.append(f'<a href="/{code}/" hreflang="{code}" lang="{code}"{active}>'
                     f'{esc(label)}</a>')
    return "".join(items)


def page(lang: str) -> str:
    t = C[lang]
    title, lead = t["hero_title"].split("\n", 1)

    features = "".join(
        f'<article class="feature"><h3>{esc(t[f"f{n}_t"])}</h3>'
        f'<p>{esc(t[f"f{n}_b"])}</p></article>' for n in (1, 2, 3, 4))

    steps = "".join(
        f'<li><span class="num">{n}</span><h3>{esc(t[f"how_{n}_t"])}</h3>'
        f'<p>{esc(t[f"how_{n}_b"])}</p></li>' for n in (1, 2, 3))

    faq = "".join(
        f'<details><summary>{esc(t[f"faq_{n}_q"])}</summary>'
        f'<p>{esc(t[f"faq_{n}_a"])}</p></details>' for n in (1, 2, 3, 4))

    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{t['dir']}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(t['title'])}</title>
  <meta name="description" content="{esc(t['description'])}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <link rel="canonical" href="{SITE_URL}/{lang}/">
  {hreflangs(lang)}
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="PoE Price Check">
  <meta property="og:title" content="{esc(t['title'])}">
  <meta property="og:description" content="{esc(t['description'])}">
  <meta property="og:url" content="{SITE_URL}/{lang}/">
  <meta property="og:image" content="{SITE_URL}/assets/og.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{esc(t['shot_result_alt'])}">
  <meta property="og:locale" content="{LOCALES[lang]}">
  {"".join(f'<meta property="og:locale:alternate" content="{LOCALES[o]}">'
           for o in LANGS if o != lang)}
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(t['title'])}">
  <meta name="twitter:description" content="{esc(t['description'])}">
  <meta name="twitter:image" content="{SITE_URL}/assets/og.png">
  <link rel="icon" href="{asset('icon.png')}" type="image/png">
  <link rel="stylesheet" href="{asset('style.css')}">
  <script src="{asset('hit.js')}" defer></script>
  <script async src="https://fundingchoicesmessages.google.com/i/pub-6223562686562496?ers=1"></script>
  <script>(function() {{function signalGooglefcPresent() {{if (!window.frames['googlefcPresent']) {{if (document.body) {{const iframe = document.createElement('iframe'); iframe.style = 'width: 0; height: 0; border: none; z-index: -1000; left: -1000px; top: -1000px;'; iframe.style.display = 'none'; iframe.name = 'googlefcPresent'; document.body.appendChild(iframe);}} else {{setTimeout(signalGooglefcPresent, 0);}}}}}} signalGooglefcPresent();}})();</script>
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6223562686562496"
     crossorigin="anonymous"></script>
  {json_ld(lang, t)}
</head>
<body>
<a class="skip" href="#main">{esc(t['skip'])}</a>

<header class="topbar">
  <div class="wrap bar">
    <a class="brand" href="/{lang}/"><img src="{asset('icon.png')}" alt="" width="24" height="24">PoE Price Check</a>
    <nav aria-label="{esc(t['nav_how'])}">
      <a href="#how">{esc(t['nav_how'])}</a>
      <a href="#features">{esc(t['nav_features'])}</a>
      <a href="#faq">{esc(t['nav_faq'])}</a>
      <a class="cta" href="#download">{esc(t['nav_download'])}</a>
    </nav>
  </div>
</header>

<main id="main">
  <section class="hero">
    <div class="wrap hero-grid">
      <div>
        <p class="badge">{esc(t['hero_badge'])}</p>
        <h1>{esc(title)}<span>{esc(lead)}</span></h1>
        <p class="lead">{esc(t['hero_lead'])}</p>
        <p class="actions">
          <a class="btn primary" href="{DOWNLOAD_URL}" rel="noopener noreferrer">{esc(t["hero_cta"])}</a>
          <span class="note">{esc(t['hero_note'])}</span>
        </p>
      </div>
      <figure class="shot hero-shot">
        <img src="{asset('app-result.png')}" width="462" height="679"
             alt="{esc(t['shot_result_alt'])}" fetchpriority="high">
      </figure>
    </div>
  </section>

  <section class="band">
    <div class="wrap narrow">
      <p class="eyebrow">{esc(t['eyebrow_problem'])}</p>
      <h2>{esc(t['problem_title'])}</h2>
      <p class="body-text">{esc(t['problem_body'])}</p>
      <p class="solution">{esc(t['problem_solution'])}</p>
    </div>
  </section>

  <section id="how">
    <div class="wrap">
      <p class="eyebrow">{esc(t['eyebrow_how'])}</p>
      <h2>{esc(t['how_title'])}</h2>
      <ol class="steps">{steps}</ol>
    </div>
  </section>

  <section class="band" id="features">
    <div class="wrap">
      <p class="eyebrow">{esc(t['eyebrow_features'])}</p>
      <h2>{esc(t['features_title'])}</h2>
      <div class="features">{features}</div>
    </div>
  </section>

  <section>
    <div class="wrap split">
      <div>
        <h2>{esc(t['privacy_title'])}</h2>
        <p class="privacy-note">{esc(t['privacy_body'])}</p>
      </div>
      <figure class="shot shot-small">
        <img src="{asset('app-status.png')}" width="304" height="411"
             alt="{esc(t['shot_status_alt'])}" loading="lazy">
      </figure>
    </div>
  </section>

  <section class="band" id="faq">
    <div class="wrap narrow">
      <p class="eyebrow">{esc(t['eyebrow_faq'])}</p>
      <h2>{esc(t['faq_title'])}</h2>
      {faq}
    </div>
  </section>

  <section class="download" id="download">
    <div class="wrap narrow">
      <h2>{esc(t['download_title'])}</h2>
      <p class="body-text">{esc(t['download_body'])}</p>
      <p class="actions">
        <a class="btn primary" href="{DOWNLOAD_URL}" rel="noopener noreferrer">{esc(t['download_cta'])}</a>
        {mac_button(t)}
        {discord_button(t)}
        {source_button(t)}
      </p>
      <p class="note">{esc(t['download_mac_note'])}</p>
      <p class="note discord-note">{esc(t['discord_body'])}</p>
    </div>
  </section>
</main>

<footer>
  <div class="wrap">
    <nav class="langs" aria-label="{esc(t['footer_lang'])}">{lang_switch(lang)}</nav>
    <p class="footer-cta">{discord_button(t)}</p>
    <p class="disclaimer">{esc(t['footer_disclaimer'])}</p>
    <p class="disclaimer"><a href="{SOURCE_URL}/blob/main/SIGNING-POLICY.md"
       rel="noopener noreferrer">Code signing policy</a>
       &middot; <a href="/{lang}/privacy/">{esc(PRIVACY[lang]['title'])}</a></p>
  </div>
</footer>
</body>
</html>
"""


def privacy_page(lang: str) -> str:
    p = PRIVACY[lang]
    t = C[lang]
    sections = "".join(
        f"<section><h2>{esc(heading)}</h2>"
        + "".join(f"<p>{esc(para)}</p>" for para in paras)
        + "</section>"
        for heading, paras in p["sections"])
    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{t['dir']}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(p['title'])} - PoE Price Check</title>
  <meta name="description" content="{esc(p['description'])}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{SITE_URL}/{lang}/privacy/">
  <link rel="icon" href="{asset('icon.png')}" type="image/png">
  <link rel="stylesheet" href="{asset('style.css')}">
</head>
<body>
<main class="wrap narrow legal">
  <p><a href="/{lang}/">{esc(p['back'])}</a></p>
  <h1>{esc(p['title'])}</h1>
  <p class="note">{esc(p['updated'])}</p>
  {sections}
</main>
<footer>
  <div class="wrap">
    <nav class="langs" aria-label="{esc(t['footer_lang'])}">{lang_switch(lang)}</nav>
  </div>
</footer>
</body>
</html>
"""


def root_redirect() -> str:
    """Strona wejsciowa: kieruje na jezyk przegladarki.

    Wersje jezykowe sa wypisane takze w <noscript> i w hreflang, wiec robot
    dojdzie wszedzie nawet bez wykonywania skryptu.
    """
    links = "".join(f'<li><a href="/{code}/" hreflang="{code}">{esc(label)}</a></li>'
                    for code, label in LANGS.items())
    return f"""<!DOCTYPE html>
<html lang="{DEFAULT}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PoE Price Check</title>
  <meta name="description" content="{esc(C[DEFAULT]['description'])}">
  <link rel="canonical" href="{SITE_URL}/{DEFAULT}/">
  {hreflangs(DEFAULT)}
  <link rel="icon" href="{asset('icon.png')}" type="image/png">
  <link rel="stylesheet" href="{asset('style.css')}">
  <script src="{asset('lang.js')}" defer></script>
  <script src="{asset('hit.js')}" defer></script>
  <script async src="https://fundingchoicesmessages.google.com/i/pub-6223562686562496?ers=1"></script>
  <script>(function() {{function signalGooglefcPresent() {{if (!window.frames['googlefcPresent']) {{if (document.body) {{const iframe = document.createElement('iframe'); iframe.style = 'width: 0; height: 0; border: none; z-index: -1000; left: -1000px; top: -1000px;'; iframe.style.display = 'none'; iframe.name = 'googlefcPresent'; document.body.appendChild(iframe);}} else {{setTimeout(signalGooglefcPresent, 0);}}}}}} signalGooglefcPresent();}})();</script>
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6223562686562496"
     crossorigin="anonymous"></script>
</head>
<body class="centre">
  <main class="wrap">
    <h1>PoE Price Check</h1>
    <p class="lead">{esc(C[DEFAULT]['hero_lead'])}</p>
    <noscript><p>{esc(C[DEFAULT]['footer_lang'])}:</p></noscript>
    <ul class="langlist">{links}</ul>
  </main>
</body>
</html>
"""


def admin_page() -> str:
    """Panel administracyjny.

    Nie ma tu formularza logowania ani niczego, co sprawdzaloby dostep - robi
    to funkcja brzegowa w functions/admin/_middleware.js. Bez waznej sesji ta
    strona w ogole nie zostanie wydana, wiec panel moze zakladac, ze ktos, kto
    ja oglada, jest juz zalogowany.
    """
    tiles = [
        ("users_today", "Użytkownicy dziś", "users_new_today", "nowych"),
        ("users_week", "Użytkownicy 7 dni", "", ""),
        ("users_month", "Użytkownicy 30 dni", "", ""),
        ("users_total", "Instalacje łącznie", "", ""),
        ("checks", "Wyceny łącznie", "checks_per_user", "na instalację"),
        ("failure_rate", "Błędy 7 dni", "failure_delta", "wobec poprzednich"),
        ("retention", "Wracający", "users_returning", "instalacji"),
        ("avg_session", "Sesja średnio", "", "minut"),
    ]
    tile_html = "".join(
        f'<div class="tile"><span class="tile-label">{esc(label)}</span>'
        f'<b data-tile="{key}">–</b>'
        f'<span class="tile-note" data-note="{sub}">{esc(sub_label)}</span></div>'
        for key, label, sub, sub_label in tiles)

    ranges = "".join(
        f'<button type="button" class="btn range" data-days="{n}"'
        f'{" aria-pressed=\"true\"" if n == 14 else " aria-pressed=\"false\""}>'
        f'{n} dni</button>' for n in (7, 14, 30, 90))

    # Rodzaje bledow ida pierwsze i przez cala szerokosc: to jedyna karta,
    # ktora odpowiada na pytanie "co sie psuje", a nie "kto uzywa".
    splits = (
        '<section class="card wide"><h2>Rodzaje błędów (7 dni)</h2>'
        '<div class="bars" data-bars="errors"></div></section>'
    ) + "".join(
        f'<section class="card"><h2>{esc(label)}</h2>'
        f'<div class="bars" data-bars="{key}"></div></section>'
        for key, label in [("versions", "Wersje"), ("languages", "Języki"),
                           ("leagues", "Ligi"), ("systems", "Systemy"),
                           ("transports", "Transport")])

    web_tiles = [
        ("views_today", "Odsłony dziś", "visitors_today", "unikalnych"),
        ("views_week", "Odsłony 7 dni", "visitors_week", "unikalnych"),
        ("views_month", "Odsłony 30 dni", "visitors_month", "unikalnych"),
        ("views_total", "Odsłony łącznie", "per_visitor", "na odwiedzającego"),
    ]
    web_tile_html = "".join(
        f'<div class="tile"><span class="tile-label">{esc(label)}</span>'
        f'<b data-tile="{key}">–</b>'
        f'<span class="tile-note" data-note="{sub}">{esc(sub_label)}</span></div>'
        for key, label, sub, sub_label in web_tiles)

    web_splits = "".join(
        f'<section class="card"><h2>{esc(label)}</h2>'
        f'<div class="bars" data-bars="{key}"></div></section>'
        for key, label in [("pages", "Podstrony"), ("referrers", "Skąd przyszli"),
                           ("countries", "Kraje"), ("languages", "Wersje językowe"),
                           ("devices", "Urządzenia")])

    return f"""<!DOCTYPE html>
<html lang="{DEFAULT}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Panel - PoE Price Check</title>
  <meta name="robots" content="noindex, nofollow, noarchive">
  <link rel="icon" href="{asset('icon.png')}" type="image/png">
  <link rel="stylesheet" href="{asset('style.css')}">
  <script src="{asset('admin.js')}" defer></script>
</head>
<body>
<header class="topbar">
  <div class="wrap bar">
    <span class="brand"><img src="{asset('icon.png')}" alt="" width="24" height="24">Panel statystyk</span>
    <nav>
      <span class="note" id="updated" aria-live="polite"></span>
      <span class="note" id="who"></span>
      <button type="button" class="btn" id="refresh">Odśwież</button>
      <button type="button" class="btn" id="logout">Wyloguj</button>
    </nav>
  </div>
</header>

<main class="wrap wide admin">

  <div id="board">
    <div class="toolbar">
      <div class="tabs" role="tablist">
        <button type="button" class="tab" role="tab" data-tab="app"
                aria-selected="true">Aplikacja</button>
        <button type="button" class="tab" role="tab" data-tab="web"
                aria-selected="false">Strona</button>
      </div>
      <div class="ranges" role="group" aria-label="Zakres dni">{ranges}</div>
    </div>

    <div class="panel" data-panel="app" role="tabpanel">
      <div id="alert" class="alert" role="status" hidden></div>

      <div class="tiles">{tile_html}</div>

      <section class="card">
        <h2>Użytkownicy dziennie</h2>
        <p class="legend"><span class="key key-users"></span>aktywni
           <span class="key key-fresh"></span>nowi</p>
        <div class="chart" data-chart="users"></div>
      </section>

      <section class="card">
        <h2>Wyceny dziennie</h2>
        <p class="legend"><span class="key key-checks"></span>udane
           <span class="key key-fail"></span>nieudane</p>
        <div class="chart" data-chart="checks"></div>
      </section>

      <div class="splits">{splits}</div>
    </div>

    <div class="panel" data-panel="web" role="tabpanel" hidden>
      <div class="tiles">{web_tile_html}</div>

      <section class="card">
        <h2>Ruch dzienny</h2>
        <p class="legend"><span class="key key-users"></span>odsłony
           <span class="key key-fresh"></span>unikalni</p>
        <div class="chart" data-chart="traffic"></div>
      </section>

      <div class="splits">{web_splits}</div>

      <p class="note">
        Bez ciasteczek i bez zapisywania adresów IP. Unikalne wejścia liczymy
        skrótem, który zmienia się każdej doby, więc nikogo nie da się śledzić
        między dniami. Ustawienie „Do Not Track” w przeglądarce jest respektowane.
      </p>
    </div>

    <p class="actions">
      <button type="button" class="btn" id="csv">Pobierz CSV</button>
    </p>
    <p class="note" id="meta"></p>

    <section class="card">
      <h2>Zmiana hasła</h2>
      <form id="password" class="gate" autocomplete="off">
        <div class="field">
          <label for="current">Obecne hasło</label>
          <input id="current" type="password" required
                 autocomplete="current-password">
        </div>
        <div class="field">
          <label for="next">Nowe hasło</label>
          <input id="next" type="password" required minlength="12"
                 autocomplete="new-password">
        </div>
        <button type="submit" class="btn primary">Zmień hasło</button>
        <p class="note" id="password-note">
          Co najmniej 12 znaków. Zmiana wylogowuje wszystkie inne sesje.
        </p>
      </form>
    </section>
  </div>

</main>
</body>
</html>
"""


def admin_login_page() -> str:
    """Strona logowania - jedyna czesc /admin/ dostepna bez sesji."""
    return f"""<!DOCTYPE html>
<html lang="{DEFAULT}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Logowanie - PoE Price Check</title>
  <meta name="robots" content="noindex, nofollow, noarchive">
  <link rel="icon" href="{asset('icon.png')}" type="image/png">
  <link rel="stylesheet" href="{asset('style.css')}">
  <script src="{asset('login.js')}" defer></script>
</head>
<body>
<header class="topbar">
  <div class="wrap bar">
    <span class="brand"><img src="{asset('icon.png')}" alt="" width="24" height="24">Panel statystyk</span>
  </div>
</header>

<main class="wrap admin">
  <form id="login" class="gate" autocomplete="on">
    <h1>Logowanie</h1>
    <div class="field">
      <label for="login-name">Login</label>
      <input id="login-name" name="login" type="text" required
             autocomplete="username" spellcheck="false" autofocus>
    </div>
    <div class="field">
      <label for="login-pass">Hasło</label>
      <input id="login-pass" name="password" type="password" required
             autocomplete="current-password">
    </div>
    <button type="submit" class="btn primary">Zaloguj</button>
    <p class="note" id="login-note">
      Sesja trwa 14 dni i jest zapisana w ciasteczku, którego nie da się
      odczytać skryptem.
    </p>
  </form>
</main>
</body>
</html>
"""


def not_found_page() -> str:
    """Strona 404. Cloudflare Pages podstawia ja sam pod nieznane adresy.

    Domyslna strona Cloudflare wyglada jak awaria calego serwisu - wlasna
    zatrzymuje czlowieka na stronie zamiast wypychac go z powrotem do wyszukiwarki.
    """
    links = "".join(f'<li><a href="/{code}/" hreflang="{code}">{esc(label)}</a></li>'
                    for code, label in LANGS.items())
    return f"""<!DOCTYPE html>
<html lang="{DEFAULT}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nie ma takiej strony - PoE Price Check</title>
  <meta name="robots" content="noindex, follow">
  <link rel="icon" href="{asset('icon.png')}" type="image/png">
  <link rel="stylesheet" href="{asset('style.css')}">
</head>
<body class="centre">
  <main class="wrap">
    <h1>404</h1>
    <p class="lead">Nie ma takiej strony. Wybierz wersję językową:</p>
    <ul class="langlist">{links}</ul>
  </main>
</body>
</html>
"""


def content_changed() -> str:
    """Data ostatniej zmiany TRESCI stron, nie data budowania.

    Wstawianie tu dzisiejszej daty przy kazdym wdrozeniu jest kuszace, ale
    Google przestaje ufac znacznikowi lastmod, ktory zawsze pokazuje "dzis"
    mimo niezmienionej tresci - i po prostu zaczyna go ignorowac.

    Bierzemy wiec date ostatniej zmiany plikow, ktore realnie ksztaltuja
    strony: tekstow i szablonu. Najpierw z gita, bo to jedyne zrodlo odporne
    na swiezy klon; gdy gita nie ma, zostaje czas modyfikacji plikow.
    """
    sources = [HERE / "content.py", HERE / "build.py"]
    try:
        stamps = []
        for path in sources:
            out = subprocess.run(
                ["git", "log", "-1", "--format=%cd", "--date=short", "--", path.name],
                cwd=HERE, capture_output=True, text=True, timeout=10)
            if out.returncode == 0 and out.stdout.strip():
                stamps.append(out.stdout.strip())
        if stamps:
            return max(stamps)
    except (OSError, subprocess.SubprocessError):
        pass
    newest = max(path.stat().st_mtime for path in sources if path.exists())
    return date.fromtimestamp(newest).isoformat()


def sitemap() -> str:
    changed = content_changed()
    entries = []
    for code in LANGS:
        # x-default MUSI tu byc, tak samo jak w znacznikach na stronach.
        # Bez niego sitemapa i HTML mowia co innego, a to jest dokladnie ten
        # rodzaj sprzecznosci, ktorego Google nie rozstrzyga na nasza korzysc.
        # Kazdy element w osobnej linii. Dla wyszukiwarek bez roznicy, ale
        # przegladarka nie potrafi pokazac tego pliku jako drzewa (blokuje ja
        # nasza wlasna polityka CSP) i sklejalaby wszystko w jeden ciag
        # w rodzaju ".../en/2026-08-02weekly1.0" - nie do odczytania.
        alts = "".join(
            f'  <xhtml:link rel="alternate" hreflang="{other}" '
            f'href="{SITE_URL}/{other}/"/>\n' for other in LANGS)
        alts += (f'  <xhtml:link rel="alternate" hreflang="x-default" '
                 f'href="{SITE_URL}/{DEFAULT}/"/>\n')
        entries.append(
            f"<url>\n"
            f"  <loc>{SITE_URL}/{code}/</loc>\n"
            f"  <lastmod>{changed}</lastmod>\n"
            f"  <changefreq>weekly</changefreq>\n"
            f"  <priority>{'1.0' if code == DEFAULT else '0.9'}</priority>\n"
            f"{alts}"
            f"</url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(entries) + "\n</urlset>\n")


def version_manifest() -> str:
    """Plik, po ktory siega aplikacja, zeby sprawdzic, czy jest nowsza wersja.

    Statyczny JSON, a nie endpoint w Functions: informacja o wersji nie zalezy
    od bazy, wiec nie ma powodu, zeby awaria D1 albo limit zapytan blokowaly
    powiadomienie o aktualizacji. Wersja bierze sie z APP_VERSION, czyli z tego
    samego zrodla co build aplikacji - nie da sie ich rozjechac.
    """
    return json.dumps(
        {
            "version": APP_VERSION,
            "download": DOWNLOAD_URL,
            "page": f"{SITE_URL}/pl/",
            "notes": f"{SOURCE_URL}/releases/tag/v{APP_VERSION}",
            # Aplikacja ma wbudowany adres zapasowy, ale pyta stad. Dzieki temu
            # wygasle zaproszenie podmienia sie wdrozeniem strony, bez zmuszania
            # ludzi do pobrania nowej wersji programu.
            "discord": DISCORD_URL,
        },
        indent=2,
    ) + "\n"


def robots() -> str:
    return (f"User-agent: *\nAllow: /\nDisallow: /admin/\n\n"
            f"Sitemap: {SITE_URL}/sitemap.xml\n")


def headers() -> str:
    """Naglowki bezpieczenstwa dla Cloudflare Pages.

    UWAGA na sposob dzialania pliku _headers, bo dwie rzeczy sa nieoczywiste
    i obie mnie tu kosztowaly bledy:

    1. Cloudflare stosuje WSZYSTKIE pasujace reguly, nie tylko najbardziej
       szczegolowa. Gdy strona dostanie dwie polityki CSP, przegladarka wymusza
       ich czesc wspolna - regula ogolna moze wiec tylko zaostrzyc szczegolowa,
       nigdy jej nie poluzowac.
    2. Sciezki dopasowuja sie PREFIKSEM, wiec samo "/" znaczy to samo co "/*"
       i obejmuje cala witryne. Nie da sie tym rozdzielic stron publicznych
       od panelu.

    Razem daje to jeden wniosek: CSP musi byc DOKLADNIE JEDNA, wspolna dla
    calej witryny. Wczesniej byly dwie i "connect-src 'none'" z reguly ogolnej
    kasowalo "connect-src 'self'" z reguly panelu - panel nie mogl wywolac
    wlasnego API, a logowanie konczylo sie "Failed to fetch".

    Polityka jest dobrana pod panel, bo to on ma wieksze potrzeby. Strony
    publiczne dostaja przez to connect-src 'self' zamiast 'none', ale nie robia
    zadnych zapytan, a skryptow z zewnatrz i tak pilnuje script-src 'self'.
    """
    return (
        "/*\n"
        "  Content-Security-Policy: default-src 'none'; "
        "script-src 'self' https://pagead2.googlesyndication.com "
        "https://googleads.g.doubleclick.net https://tpc.googlesyndication.com "
        "https://fundingchoicesmessages.google.com; "
        "style-src 'self'; "
        "img-src 'self' data: https://*.googlesyndication.com https://*.doubleclick.net "
        "https://*.google.com https://*.gstatic.com; "
        "font-src 'self'; "
        "connect-src 'self' https://*.googlesyndication.com https://*.doubleclick.net "
        "https://*.google.com https://fundingchoicesmessages.google.com; "
        "frame-src https://googleads.g.doubleclick.net https://tpc.googlesyndication.com "
        "https://*.safeframe.googlesyndication.com https://www.google.com "
        "https://fundingchoicesmessages.google.com; "
        "form-action 'self'; base-uri 'none'; "
        "frame-ancestors 'none'\n"
        "  X-Content-Type-Options: nosniff\n"
        "  Referrer-Policy: no-referrer\n"
        "  Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=()\n"
        "  Strict-Transport-Security: max-age=63072000; includeSubDomains"
        + ("; preload\n" if HSTS_PRELOAD else "\n") +
        "  Cross-Origin-Opener-Policy: same-origin\n"
        "  X-Frame-Options: DENY\n"
        # Ponizsze reguly dokladaja tylko naglowki spoza CSP, wiec nic sie
        # nie nakloci.
        #
        # Zasoby maja w adresie znacznik tresci (?v=...), wiec kazda zmiana
        # pliku to inny adres. Dzieki temu mozna je trzymac w pamieci
        # podrecznej bezterminowo i nikt nie zobaczy starego arkusza stylow.
        "\n/assets/*\n"
        "  Cache-Control: public, max-age=31536000, immutable\n"
        # Paczka ma stala nazwe, a zmienna zawartosc miedzy poprawkami tej samej
        # wersji. Krotki czas zycia w pamieci podrecznej plus znacznik tresci
        # w adresie sprawiaja, ze nikt nie pobierze poprzedniego buildu.
        "\n/download/*\n"
        "  Cache-Control: public, max-age=300, must-revalidate\n"
        # Po ten plik siega kazda uruchomiona aplikacja, zeby sprawdzic, czy jest
        # nowsza wersja. Dluga pamiec podreczna oznaczalaby, ze po wydaniu ludzie
        # jeszcze przez wiele godzin nie widza powiadomienia.
        "\n/version.json\n"
        "  Cache-Control: public, max-age=600, must-revalidate\n"
        "\n/admin/*\n"
        "  X-Robots-Tag: noindex, nofollow\n"
        "  Cache-Control: no-store\n"
        # Odpowiedzi API nie moga trafic do zadnego posrednika - siedza w nich
        # statystyki i stan sesji.
        "\n/api/*\n"
        "  Cache-Control: no-store\n"
        "  X-Robots-Tag: noindex, nofollow\n"
    )


def build() -> None:
    # Kontrola kompletnosci PRZED zapisem - lepiej nie zbudowac niz wypuscic dziure.
    base = set(C[DEFAULT])
    for code in LANGS:
        missing = base - set(C[code])
        extra = set(C[code]) - base
        if missing or extra:
            raise SystemExit(
                f"Tresc dla {code!r} niezgodna: brakuje {sorted(missing)}, "
                f"nadmiar {sorted(extra)}")

    privacy_base = set(PRIVACY[DEFAULT])
    for code in LANGS:
        if code not in PRIVACY:
            raise SystemExit(f"Brak polityki prywatnosci dla {code!r}")
        missing = privacy_base - set(PRIVACY[code])
        extra = set(PRIVACY[code]) - privacy_base
        if missing or extra:
            raise SystemExit(
                f"Polityka prywatnosci dla {code!r} niezgodna: "
                f"brakuje {sorted(missing)}, nadmiar {sorted(extra)}")

    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets").mkdir(parents=True)

    for code in LANGS:
        target = DIST / code
        target.mkdir()
        (target / "index.html").write_text(page(code), encoding="utf-8")
        (target / "privacy").mkdir()
        (target / "privacy" / "index.html").write_text(
            privacy_page(code), encoding="utf-8")

    (DIST / "index.html").write_text(root_redirect(), encoding="utf-8")
    (DIST / "admin").mkdir()
    (DIST / "admin" / "index.html").write_text(admin_page(), encoding="utf-8")
    (DIST / "admin" / "login").mkdir()
    (DIST / "admin" / "login" / "index.html").write_text(
        admin_login_page(), encoding="utf-8")
    (DIST / "404.html").write_text(not_found_page(), encoding="utf-8")
    (DIST / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    (DIST / "robots.txt").write_text(robots(), encoding="utf-8")
    (DIST / "ads.txt").write_text(
        "google.com, pub-6223562686562496, DIRECT, f08c47fec0942fa0\n",
        encoding="utf-8")
    (DIST / "version.json").write_text(version_manifest(), encoding="utf-8")
    (DIST / "_headers").write_text(headers(), encoding="utf-8")

    # Kopiujemy caly katalog zasobow - zrzuty ekranu dochodza i znikaja, a lista
    # nazw wpisana na sztywno cicho gubila by nowe pliki.
    for path in sorted((HERE / "assets").iterdir()):
        if path.is_file():
            shutil.copy(path, DIST / "assets" / path.name)
    icon = HERE.parent / "icon.png"
    if icon.exists():
        shutil.copy(icon, DIST / "assets" / "icon.png")

    pages = len(LANGS) + 3  # jezyki + strona wejsciowa + panel + logowanie
    print(f"zbudowano {pages} stron w {DIST}")
    for path in sorted(DIST.rglob("*")):
        if path.is_file():
            print(f"  {path.relative_to(DIST)}  ({path.stat().st_size} B)")


if __name__ == "__main__":
    build()
