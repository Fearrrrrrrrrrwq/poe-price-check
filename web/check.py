"""Kontrola wygenerowanej strony.

SEO psuje sie po cichu - brakujacy canonical albo hreflang nie rzuca bledem,
tylko po miesiacu okazuje sie, ze Google zaindeksowal jedna wersje jezykowa.
Dlatego sprawdzamy to testem, a nie okiem.
"""

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from content import DEFAULT, LANGS
from package import APP_VERSION

DIST = pathlib.Path(__file__).parent / "dist"

ok: list[bool] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    ok.append(bool(condition))
    mark = "OK " if condition else "ZLE"
    print(f"  [{mark}] {label}" + (f"  -> {detail}" if detail and not condition else ""))


def read(path: str) -> str:
    return (DIST / path).read_text(encoding="utf-8")


def headers_early() -> str:
    return read("_headers")


print("=== struktura ===")
for name in ["index.html", "robots.txt", "sitemap.xml", "_headers",
             "404.html", "admin/index.html", "assets/style.css", "assets/lang.js",
             "assets/admin.js"]:
    check(f"istnieje {name}", (DIST / name).exists())
for code in LANGS:
    check(f"istnieje {code}/index.html", (DIST / code / "index.html").exists())

# Pobieranie prowadzi do wydania na GitHubie - jedno binarium na wersje.
# Wlasna kopia oznaczalaby druga sume kontrolna pod ta sama wersja.
release_link = f"/releases/download/v{APP_VERSION}/"
check("przycisk pobierania wskazuje na wydanie",
      release_link in read(f"{DEFAULT}/index.html"))
check("strona nie hostuje wlasnej kopii", not (DIST / "download").exists())
check("brak odnosnikow do nieistniejacego repozytorium",
      not any("github.com/kacper" in read(f"{code}/index.html") for code in LANGS))

print("\n=== SEO na kazdej stronie jezykowej ===")
titles: dict[str, str] = {}
for code in LANGS:
    page = read(f"{code}/index.html")

    check(f"{code}: atrybut lang", f'<html lang="{code}"' in page)
    check(f"{code}: canonical", f'rel="canonical" href="https://' in page and
          f'/{code}/"' in page)
    check(f"{code}: description", 'name="description"' in page)
    check(f"{code}: og:locale", 'property="og:locale"' in page)

    # Komplet hreflang - kazdy jezyk musi wskazywac na WSZYSTKIE, lacznie z soba.
    missing = [other for other in LANGS if f'hreflang="{other}"' not in page]
    check(f"{code}: hreflang do wszystkich jezykow", not missing, str(missing))
    check(f"{code}: hreflang x-default", 'hreflang="x-default"' in page)

    # Dane strukturalne musza byc poprawnym JSON-em.
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                        page, re.S)
    check(f"{code}: dwa bloki danych strukturalnych", len(blocks) == 2, str(len(blocks)))
    valid = True
    for block in blocks:
        try:
            json.loads(block)
        except json.JSONDecodeError as exc:
            valid = False
            print(f"        JSON: {exc}")
    check(f"{code}: dane strukturalne parsuja sie", valid)

    match = re.search(r"<title>(.*?)</title>", page, re.S)
    titles[code] = match.group(1) if match else ""
    check(f"{code}: tytul niepusty", bool(titles[code].strip()))

check("tytuly unikalne miedzy jezykami", len(set(titles.values())) == len(titles))

# Punkt 7g regulaminu GGG zakazuje znacznikow meta zawierajacych ich nazwe
# i znaki towarowe. Znacznik keywords i tak nie ma zadnej wartosci dla
# wyszukiwarek od kilkunastu lat, wiec nie ma czego bronic.
check("brak znacznika keywords ze znakiem towarowym",
      not any('name="keywords"' in read(f"{code}/index.html") for code in LANGS))

print("\n=== bezpieczenstwo ===")
# Interesuja nas tylko zasoby LADOWANE przez przegladarke. Adresy kanoniczne
# i hreflang tez sa bezwzgledne, ale to metadane - nic z nich nie leci po sieci.
LOADED_RE = re.compile(r'<(?:script|img|iframe)[^>]+src="(https?://[^"]+)"'
                       r'|<link[^>]+rel="(?:stylesheet|preload|preconnect)"[^>]+'
                       r'href="(https?://[^"]+)"')
external = set()
for path in DIST.rglob("*.html"):
    page = path.read_text(encoding="utf-8")
    for groups in LOADED_RE.findall(page):
        url = next((g for g in groups if g), "")
        if url:
            external.add(url)
check("zero zewnetrznych zasobow (CDN, fonty)", not external, str(external))

# Linki wychodzace musza miec noopener - inaczej otwarta strona dostaje
# uchwyt do naszego okna przez window.opener.
risky = []
for path in DIST.rglob("*.html"):
    page = path.read_text(encoding="utf-8")
    for tag in re.findall(r'<a\b[^>]*href="https?://[^"]+"[^>]*>', page):
        if "noopener" not in tag:
            risky.append(tag[:60])
check("linki zewnetrzne maja rel=noopener", not risky, str(risky[:3]))

headers = read("_headers")
for directive in ["Content-Security-Policy", "X-Content-Type-Options: nosniff",
                  "Referrer-Policy", "Strict-Transport-Security",
                  "Permissions-Policy"]:
    check(f"naglowek {directive.split(':')[0]}", directive in headers)
check("CSP domyslnie blokuje wszystko", "default-src 'none'" in headers)
check("panel admina ma wlasna regule", "/admin/*" in headers)

# Cloudflare stosuje WSZYSTKIE pasujace reguly, a sciezki dopasowuje prefiksem
# (samo "/" obejmuje cala witryne). Przy dwoch politykach CSP przegladarka
# wymusza ich czesc wspolna, wiec druga polityka potrafi po cichu zablokowac
# panelowi wlasne API - dokladnie tak juz raz bylo.
check("dokladnie jedna polityka CSP na cala witryne",
      headers.count("Content-Security-Policy") == 1,
      f"znaleziono {headers.count('Content-Security-Policy')}")
check("CSP pozwala panelowi wolac wlasne API", "connect-src 'self'" in headers)
check("CSP pozwala wyslac formularz logowania", "form-action 'self'" in headers)

# Bez znacznika tresci w adresie przegladarka po zmianie wygladu przez kilka
# godzin serwuje stary arkusz - zakladki potrafily przez to wygladac na zupelnie
# niezestylowane.
print("\n=== pamiec podreczna zasobow ===")
for name in ["style.css", "admin.js", "hit.js"]:
    used_in = read("admin/index.html") + read(f"{DEFAULT}/index.html")
    check(f"{name} ma znacznik tresci w adresie", f"/assets/{name}?v=" in used_in)
check("zasoby cachowane bezterminowo",
      "/assets/*" in headers and "immutable" in headers)
check("panel admina wylaczony z indeksu",
      'name="robots" content="noindex' in read("admin/index.html"))
check("robots.txt blokuje /admin/", "Disallow: /admin/" in read("robots.txt"))

print("\n=== panel administracyjny ===")
admin = read("admin/index.html")
login = read("admin/login/index.html")
admin_js = read("assets/admin.js")

# Regula /admin/* jest w osobnej sekcji pliku _headers.
admin_rule = headers.split("/admin/*", 1)[1] if "/admin/*" in headers else ""
check("panel wylaczony z indeksu w naglowkach",
      "X-Robots-Tag: noindex" in admin_rule)
check("odpowiedzi API bez zapisu w posrednikach",
      "/api/*" in headers and "Cache-Control: no-store" in headers)

# CSP na /admin/* nie dopuszcza stylow ani skryptow w tresci strony - gdyby
# ktos je dopisal, panel przestalby dzialac dopiero po wdrozeniu, bo lokalny
# serwer naglowkow nie wysyla.
for name, page in [("panel", admin), ("logowanie", login)]:
    check(f"{name} bez stylow w atrybutach", 'style="' not in page)
    check(f"{name} bez skryptow w tresci",
          not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", page))
    check(f"{name} wylaczone z indeksu", 'content="noindex' in page)

# Panel nie ma prawa trzymac zadnego sekretu - od tego jest sesja w ciasteczku
# HttpOnly. Samo slowo "password" wystepuje tu legalnie (formularz zmiany
# hasla), wiec sprawdzamy nie tresc, tylko co trafia do pamieci przegladarki:
# jedyny dozwolony zapis to wybrany zakres dni.
stored = re.findall(r"(?:local|session)Storage\.setItem\(\s*([\w.'\"]+)", admin_js)
check("panel zapisuje wylacznie ustawienia widoku",
      set(stored) <= {"PREFS"}, str(stored))
check("panel nie odwoluje sie do obcych hostow",
      "script.google.com" not in admin_js and "localhost" not in admin_js)

print("\n=== backend ===")
FUNCTIONS = HERE = pathlib.Path(__file__).parent
for name in ["functions/api/collect.js", "functions/api/login.js",
             "functions/api/logout.js", "functions/api/stats.js",
             "functions/api/setup.js", "functions/api/password.js",
             "functions/api/hit.js", "functions/api/traffic.js",
             "functions/admin/_middleware.js", "lib/auth.js",
             "schema.sql", "wrangler.toml"]:
    check(f"istnieje {name}", (HERE / name).exists())

print("\n=== licznik odwiedzin ===")
check("strony jezykowe wolaja licznik",
      all('src="/assets/hit.js?v=' in read(f"{code}/index.html") for code in LANGS))
check("panel NIE liczy sam siebie", "/assets/hit.js" not in admin)

hit_js = read("assets/hit.js")
check("licznik szanuje Do Not Track", "doNotTrack" in hit_js)
check("licznik nie uzywa ciasteczek", "cookie" not in hit_js.lower())

hit_fn = (HERE / "functions" / "api" / "hit.js").read_text(encoding="utf-8")
check("adres IP tylko do skrotu, nie do zapisu",
      "CF-Connecting-IP" in hit_fn and "INSERT INTO visits" in hit_fn
      and "ip," not in hit_fn)
check("skrot odwiedzajacego solony", "ANALYTICS_SALT" in hit_fn)
check("skrot zmienia sie co dobe", "toISOString().slice(0, 10)" in hit_fn)
check("panel admina wylaczony z liczenia", "startsWith('/admin')" in hit_fn)

check("tabela odwiedzin w schemacie",
      "CREATE TABLE IF NOT EXISTS visits" in (HERE / "schema.sql").read_text(encoding="utf-8"))
check("panel ma dwie zakladki",
      'data-tab="app"' in admin and 'data-tab="web"' in admin)

auth = (HERE / "lib" / "auth.js").read_text(encoding="utf-8")
check("hasla przez PBKDF2", "PBKDF2" in auth)
check("ciasteczko sesji jest HttpOnly", "HttpOnly" in auth and "Secure" in auth)
check("w bazie skrot tokenu, nie token", "tokenDigest" in auth)

login_fn = (HERE / "functions" / "api" / "login.js").read_text(encoding="utf-8")
check("logowanie ma limit prob", "login_attempts" in login_fn)

middleware = (HERE / "functions" / "admin" / "_middleware.js").read_text(encoding="utf-8")
check("panel chroniony po stronie serwera", "currentSession" in middleware)
check("logowanie dostepne bez sesji", "/admin/login" in middleware)

print("\n=== sitemap ===")
sitemap = read("sitemap.xml")
for code in LANGS:
    check(f"sitemap zawiera /{code}/", f"/{code}/</loc>" in sitemap)
check("sitemap NIE zawiera panelu admina", "/admin/" not in sitemap)
check("sitemap ma alternatywy jezykowe", 'xhtml:link rel="alternate"' in sitemap)
# HTML i sitemapa musza deklarowac ten sam zestaw wersji jezykowych - inaczej
# same sobie przecza. x-default wypadl stad przy pierwszej wersji.
check("sitemap ma x-default tak jak strony", 'hreflang="x-default"' in sitemap)

print("\n=== strona wejsciowa ===")
root = read("index.html")
check("linki do wszystkich jezykow bez skryptu",
      all(f'href="/{code}/"' in root for code in LANGS))
check("canonical wskazuje na jezyk domyslny", f'/{DEFAULT}/"' in root)

print(f"\n{sum(ok)}/{len(ok)} OK")
sys.exit(0 if all(ok) else 1)
