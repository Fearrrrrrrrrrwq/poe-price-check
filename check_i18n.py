"""Kontrola tlumaczen interfejsu.

Napis wpisany na sztywno niczego nie wywala - program dziala, tylko jedna
linijka zostaje w cudzym jezyku. Tak wlasnie "Poziom przedmiotu" przetrwalo
w angielskim oknie wyniku. Szukanie po polskich znakach tez nie wystarczy,
bo akurat ten napis nie ma ani jednego ogonka.

Dlatego idziemy po drzewie skladni i sprawdzamy argumenty, ktore trafiaja
na ekran: label, text, title.

Uruchomienie:  python check_i18n.py
"""

import ast
import pathlib
import re
import sys

import i18n

HERE = pathlib.Path(__file__).parent

# Moduly, ktore cokolwiek pokazuja uzytkownikowi.
UI_FILES = ["main.py", "overlay.py", "status_window.py", "setup_window.py",
            "trade_api.py", "item_parser.py", "currency.py", "bridge.py"]

LABEL_ARGS = {"label", "text", "title", "message"}

# Napisy, ktore zostaja po angielsku swiadomie: nazwa programu i zargon z gry,
# ktorego gracze i tak uzywaja w oryginale.
ALLOWED = {"PoE Price Check"}

# Tekst dla czlowieka zaczyna sie wielka litera i ma co najmniej trzy znaki.
# Znaczniki, symbole i puste napisy odpadaja same.
HUMAN_RE = re.compile(r"^[A-ZĄĆĘŁŃÓŚŹŻ][^\n]{2,}$")

problems: list[str] = []


def literal_keys(tree: ast.Module) -> set[int]:
    """Literaly bedace argumentem t() - to klucze, nie tekst."""
    keys = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "t" and node.args
                and isinstance(node.args[0], ast.Constant)):
            keys.add(id(node.args[0]))
    return keys


print("=== napisy interfejsu wpisane na sztywno ===")
for name in UI_FILES:
    tree = ast.parse((HERE / name).read_text(encoding="utf-8"), filename=name)
    keys = literal_keys(tree)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg not in LABEL_ARGS or not isinstance(kw.value, ast.Constant):
                continue
            value = kw.value.value
            if (not isinstance(value, str) or id(kw.value) in keys
                    or value in ALLOWED or not HUMAN_RE.match(value)):
                continue
            problems.append(f"{name}:{kw.value.lineno}  {kw.arg}={value!r}")

print(f"  znaleziono: {len(problems)}")
for line in problems:
    print(f"  [ZLE] {line}")

print("\n=== komplet kluczy w kazdym jezyku ===")
base = set(i18n.STRINGS[i18n.DEFAULT])
for code in i18n.LANGUAGES:
    keys = set(i18n.STRINGS[code])
    lack, extra = sorted(base - keys), sorted(keys - base)
    if lack or extra:
        problems.append(f"{code}: brakuje={lack} nadmiar={extra}")
        print(f"  [ZLE] {code}: brakuje={lack} nadmiar={extra}")
    else:
        print(f"  [OK ] {code}: {len(keys)} kluczy")

print("\n=== klucze uzywane w kodzie ===")
used = set()
for name in UI_FILES:
    src = (HERE / name).read_text(encoding="utf-8")
    used |= set(re.findall(r"""\bt\(\s*["']([\w.]+)["']""", src))
unknown = sorted(used - base)
if unknown:
    problems.append(f"klucze bez tlumaczenia: {unknown}")
    print(f"  [ZLE] uzywane w kodzie, brak w {i18n.DEFAULT}: {unknown}")
else:
    print(f"  [OK ] wszystkie {len(used)} uzywanych kluczy ma tlumaczenie")

# Placeholdery musza sie zgadzac - t('res.offers', n=...) wywali sie w locie,
# jesli ktores tlumaczenie zgubi {n}.
print("\n=== pola {…} zgodne miedzy jezykami ===")
fields = re.compile(r"\{(\w+)\}")
for key, text in i18n.STRINGS[i18n.DEFAULT].items():
    want = set(fields.findall(text))
    for code in i18n.LANGUAGES:
        got = set(fields.findall(i18n.STRINGS[code].get(key, "")))
        if got != want:
            problems.append(f"{code}/{key}: pola {sorted(got)} zamiast {sorted(want)}")
            print(f"  [ZLE] {code} {key}: {sorted(got)} zamiast {sorted(want)}")
if not any("pola" in p for p in problems):
    print("  [OK ] wszystkie zgodne")

print(f"\n{'OK - brak zastrzezen' if not problems else f'ZLE - {len(problems)} problemow'}")
sys.exit(0 if not problems else 1)
