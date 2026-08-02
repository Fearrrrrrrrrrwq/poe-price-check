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
import zipfile
from datetime import date

from content import C, DEFAULT, LANGS, LOCALES

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
APP_VERSION = "1.0.0"

# Plik do pobrania serwujemy z wlasnej domeny. Cloudflare Pages przyjmuje pliki
# do 25 MB, a nasz ma ~16 MB, wiec nie trzeba osobnego hostingu ani wydania
# na GitHubie. Nazwa zawiera wersje, zeby dalo sie odroznic, co ktos pobral.
#
# Wydajemy ZIP, a nie samo .exe: przegladarki blokuja pobieranie niepodpisanych
# plikow wykonywalnych z nowych domen znacznie ostrzej niz archiwow. Samego
# SmartScreena przy uruchomieniu to NIE zalatwia - Windows przenosi znacznik
# pochodzenia takze na pliki wypakowane - dlatego w srodku jest instrukcja.
DOWNLOAD_FILE = f"poe-price-check-{APP_VERSION}.zip"

# Sciezka do gotowego .exe, ktory build.py spakuje do dist/download/.
EXE_PATH = pathlib.Path(os.environ.get(
    "EXE_PATH", HERE.parent / "dist" / "poe-price-check.exe"))

# Znacznik tresci w adresie pobierania - z tego samego powodu co przy stylach.
# Nazwa pliku nie zmienia sie miedzy poprawkami tej samej wersji, wiec bez tego
# Cloudflare przez cztery godziny serwuje poprzedni build. Raz juz sie zdarzylo,
# ze opublikowana paczka miala stara zawartosc mimo poprawnego wdrozenia.
# Znacznik nie wplywa na nazwe, pod ktora plik sie zapisze u uzytkownika.
EXE_HASH = (hashlib.sha256(EXE_PATH.read_bytes()).hexdigest()[:8]
            if EXE_PATH.exists() else "")
DOWNLOAD_URL = os.environ.get(
    "DOWNLOAD_URL",
    f"/download/{DOWNLOAD_FILE}" + (f"?v={EXE_HASH}" if EXE_HASH else ""))

# Adres repozytorium. Puste = przycisk "kod zrodlowy" w ogole sie nie pokaze -
# lepiej go nie miec niz miec taki, ktory prowadzi w 404.
SOURCE_URL = os.environ.get("SOURCE_URL", "")

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
    }
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


def readme(checksum: str) -> str:
    """Instrukcja w archiwum.

    Wlasciwa przeszkoda nie jest pobranie, tylko okno SmartScreena przy
    pierwszym uruchomieniu - ludzie w tym miejscu rezygnuja, bo nie wiedza,
    ze przycisk "Wiecej informacji" w ogole tam jest. Po angielsku i polsku,
    bo to dwie najwieksze grupy; reszte prowadzi kreator w aplikacji.
    """
    return "\r\n".join([
        "PoE Price Check " + APP_VERSION,
        SITE_URL,
        "",
        "=" * 66,
        "PIERWSZE URUCHOMIENIE / FIRST RUN",
        "=" * 66,
        "",
        "[PL] Windows pokaze okno 'System Windows ochronil Twoj komputer'.",
        "     To normalne: program nie ma podpisu cyfrowego, bo certyfikat",
        "     kosztuje kilka tysiecy zlotych rocznie, a aplikacja jest darmowa.",
        "",
        "     Zeby uruchomic:  Wiecej informacji  ->  Uruchom mimo to",
        "",
        "[EN] Windows will show 'Windows protected your PC'. That is expected:",
        "     the program is not code-signed, because a certificate costs",
        "     hundreds of euros a year and this tool is free.",
        "",
        "     To run it:  More info  ->  Run anyway",
        "",
        "=" * 66,
        "",
        "Reszte konfiguracji poprowadzi kreator w aplikacji.",
        "The app's setup wizard will guide you through the rest.",
        "",
        "Suma kontrolna / checksum (SHA-256) poe-price-check.exe:",
        checksum,
        "",
        "This product isn't affiliated with or endorsed by "
        "Grinding Gear Games in any way.",
        "",
    ])


def source_button(t: dict) -> str:
    """Przycisk z kodem zrodlowym - tylko gdy jest dokad kierowac."""
    if not SOURCE_URL:
        return ""
    return (f'<a class="btn" href="{SOURCE_URL}" rel="noopener noreferrer">'
            f'{esc(t["download_alt"])}</a>')


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
          <a class="btn primary" href="{DOWNLOAD_URL}" download>{esc(t["hero_cta"])}</a>
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
        <a class="btn primary" href="{DOWNLOAD_URL}" download>{esc(t['download_cta'])}</a>
        {source_button(t)}
      </p>
    </div>
  </section>
</main>

<footer>
  <div class="wrap">
    <nav class="langs" aria-label="{esc(t['footer_lang'])}">{lang_switch(lang)}</nav>
    <p class="disclaimer">{esc(t['footer_disclaimer'])}</p>
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

    splits = "".join(
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


def sitemap() -> str:
    today = date.today().isoformat()
    entries = []
    for code in LANGS:
        alts = "".join(
            f'<xhtml:link rel="alternate" hreflang="{other}" '
            f'href="{SITE_URL}/{other}/"/>' for other in LANGS)
        entries.append(
            f"<url><loc>{SITE_URL}/{code}/</loc><lastmod>{today}</lastmod>"
            f"<changefreq>weekly</changefreq><priority>"
            f"{'1.0' if code == DEFAULT else '0.9'}</priority>{alts}</url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(entries) + "\n</urlset>\n")


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
        "  Content-Security-Policy: default-src 'none'; script-src 'self'; "
        "style-src 'self'; img-src 'self' data:; font-src 'self'; "
        "connect-src 'self'; form-action 'self'; base-uri 'none'; "
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

    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets").mkdir(parents=True)

    for code in LANGS:
        target = DIST / code
        target.mkdir()
        (target / "index.html").write_text(page(code), encoding="utf-8")

    (DIST / "index.html").write_text(root_redirect(), encoding="utf-8")
    (DIST / "admin").mkdir()
    (DIST / "admin" / "index.html").write_text(admin_page(), encoding="utf-8")
    (DIST / "admin" / "login").mkdir()
    (DIST / "admin" / "login" / "index.html").write_text(
        admin_login_page(), encoding="utf-8")
    (DIST / "404.html").write_text(not_found_page(), encoding="utf-8")
    (DIST / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    (DIST / "robots.txt").write_text(robots(), encoding="utf-8")
    (DIST / "_headers").write_text(headers(), encoding="utf-8")

    # Kopiujemy caly katalog zasobow - zrzuty ekranu dochodza i znikaja, a lista
    # nazw wpisana na sztywno cicho gubila by nowe pliki.
    for path in sorted((HERE / "assets").iterdir()):
        if path.is_file():
            shutil.copy(path, DIST / "assets" / path.name)
    icon = HERE.parent / "icon.png"
    if icon.exists():
        shutil.copy(icon, DIST / "assets" / "icon.png")

    # Plik do pobrania. Bez niego strona reklamowalaby cos, czego nie ma -
    # dlatego mowimy o tym glosno, a nie po cichu pomijamy.
    if EXE_PATH.exists():
        (DIST / "download").mkdir()
        archive = DIST / "download" / DOWNLOAD_FILE
        checksum = hashlib.sha256(EXE_PATH.read_bytes()).hexdigest()

        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
            bundle.write(EXE_PATH, "poe-price-check.exe")
            bundle.writestr("CZYTAJ-TO.txt", readme(checksum))

        size_mb = archive.stat().st_size / 1048576
        if size_mb > 25:
            raise SystemExit(
                f"Archiwum ma {size_mb:.1f} MB, a Cloudflare Pages przyjmuje "
                f"najwyzej 25 MB. Potrzebny bedzie osobny hosting i DOWNLOAD_URL "
                f"wskazujacy na niego.")

        print(f"dolaczono plik do pobrania: {DOWNLOAD_FILE} ({size_mb:.1f} MB)")
        print(f"  suma SHA-256 pliku .exe: {checksum}")
    else:
        print(f"[uwaga] nie znalazlem {EXE_PATH} - przycisk pobierania "
              f"bedzie prowadzil donikad.\n"
              f"        Zbuduj go: python -m PyInstaller --noconfirm "
              f"poe-price-check.spec")

    if SITE_URL.endswith(".pages.dev"):
        print("[uwaga] SITE_URL wskazuje na adres testowy Cloudflare.\n"
              "        Przed wdrozeniem na wlasna domene zbuduj z jej adresem:\n"
              "        SITE_URL=https://poe.twojadomena.pl python build.py")

    pages = len(LANGS) + 3  # jezyki + strona wejsciowa + panel + logowanie
    print(f"zbudowano {pages} stron w {DIST}")
    for path in sorted(DIST.rglob("*")):
        if path.is_file():
            print(f"  {path.relative_to(DIST)}  ({path.stat().st_size} B)")


if __name__ == "__main__":
    build()
