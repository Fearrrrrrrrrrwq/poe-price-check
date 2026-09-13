"""Dane dla Regex Buildera PoE2 (poepricecheck.eu/tools/poe2-regex/).

Uruchomienie:  python web/tools/regex_data.py
Wynik:         web/assets/regex-data.json  (commitowany - build strony go kopiuje)

Skad teksty:
  - Waystone: statystyki "fromAreaMods" z danych gry (data/stats_poe2.ndjson,
    Exiled Exchange 2, MIT) - dokladnie te mody, ktore moga wypasc na Waystonie.
  - Tablety: mody z "Map" w tekscie z aktualnej listy statystyk trade2
    (/api/trade2/data/stats) - to afiksy Precursor Tabletow ("Breaches in Map
    ...", "...Rarity of Items found in Map").

Dla kazdego moda liczymy NAJKROTSZY fragment tekstu, ktory nie wystepuje
w zadnym innym modzie z tej samej puli ani w stalych liniach przedmiotu
(wlasciwosci, nazwa bazy). Wyszukiwarka PoE ma limit 250 znakow - pelne
teksty modow zajmowalyby go po 2-3 modach, a zbyt krotkie fragmenty lapalyby
cudze mody.
"""

import json
import pathlib
import re
import sys
from datetime import date

import requests

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "web" / "assets" / "regex-data.json"
UA = "poe-price-check/1.0 (+https://poepricecheck.eu)"

# Linie, ktore stoja na KAZDYM Waystonie/Tablecie - fragment nie moze w nie
# trafic, bo pasowalby do wszystkiego.
NOISE_WAYSTONE = [
    "item class: waystones", "waystone (tier #)", "rarity: rare", "rarity: magic",
    "rarity: normal", "revives available: #", "item rarity: +#%", "pack size: +#%",
    "monster rarity: +#%", "monster effectiveness: +#%", "waystone drop chance: +#%",
    "item level: #", "area level: #", "corrupted", "unidentified", "(augmented)",
    "can be used in a map device, allowing you to enter a map. "
    "waystones can only be used once.",
]
NOISE_TABLET = [
    "item class: tablet", "precursor tablet", "breach precursor tablet",
    "delirium precursor tablet", "ritual precursor tablet", "expedition precursor tablet",
    "rarity: rare", "rarity: magic", "rarity: normal", "# uses remaining", "item level: #",
    "corrupted", "unidentified",
    "can be used in a completed tower on your atlas to influence surrounding maps. "
    "tablets are consumed once placed into a tower.",
]
ALLOWED = re.compile(r"^[a-z][a-z ',-]*[a-z]$")


def _norm(text: str) -> str:
    return re.sub(r"[+-]?\d+(?:\.\d+)?", "#", text.lower().replace("\n", " "))


def shortest_fragment(text: str, others: list[str], noise: list[str],
                      min_len: int = 5) -> str:
    """Najkrotszy fragment `text` bez cyfr/'#'/'%', ktorego nie ma w innych.

    Minimum 5 znakow i przy rownej dlugosci pierwszenstwo dla fragmentu
    zaczynajacego sie od poczatku slowa - 4-znakowe zlepki przez granice slow
    ("f mag") byly unikalne w puli modow, ale latwo trafialy w losowa nazwe
    rzadkiego przedmiotu, ktora wyszukiwarka tez przeszukuje.
    """
    t = _norm(text)
    corpus = [_norm(o) for o in others] + noise
    for length in range(min_len, len(t) + 1):
        best = None
        for start in range(0, len(t) - length + 1):
            frag = t[start:start + length]
            if not ALLOWED.match(frag):
                continue
            if any(frag in other for other in corpus):
                continue
            at_word = start == 0 or not t[start - 1].isalpha()
            if at_word:
                return frag
            best = best or frag
        if best:
            return best
    return ""  # tekst zawiera sie w innym - fragment niemozliwy


def build_pool(texts: list[str], noise: list[str]) -> list[dict]:
    texts = sorted(set(texts), key=str.lower)
    pool = []
    for text in texts:
        others = [o for o in texts if o != text]
        frag = shortest_fragment(text, others, noise)
        also = 0
        if not frag:
            # Mod zawarty w dluzszym ("Breaches in Map spawn an additional Rare
            # Monster" w "Unstable Breaches in Map spawn ..."). Fragment moze
            # wtedy pasowac takze do tych dluzszych - lepsze niz brak moda.
            norm = _norm(text)
            supers = [o for o in others if norm in _norm(o)]
            frag = shortest_fragment(text, [o for o in others if o not in supers], noise)
            also = len(supers)
        if frag:
            entry = {"text": text.replace("\n", " "), "frag": frag}
            if also:
                entry["also"] = also
            pool.append(entry)
        else:
            print(f"  [pomijam - brak unikalnego fragmentu] {text}")
    return pool


def waystone_texts() -> list[str]:
    out = []
    source = ROOT / "data" / "stats_poe2.ndjson"
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("fromAreaMods") and rec.get("matchers"):
            out.append(rec["matchers"][0]["string"])
    return out


def tablet_texts(exclude: set[str]) -> list[str]:
    try:
        resp = requests.get("https://www.pathofexile.com/api/trade2/data/stats",
                            headers={"User-Agent": UA}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        data = json.loads((ROOT / ".cache" / "stats_poe2.json").read_text(encoding="utf-8"))
    texts = {e["text"] for g in data.get("result", []) if g.get("id") == "explicit"
             for e in g.get("entries", [])}
    tablet_re = re.compile(r"\bin Map\b|Map Boss|your Maps|nearby Maps|Tower Maps|"
                           r"Map also counts|Map has|Map contains|Map is ")
    return [t for t in texts if tablet_re.search(t) and t not in exclude
            and "Passive" not in t and "Radius" not in t]


# Presety vendora: {n} to miejsce na prog liczbowy (regex "co najmniej N").
VENDOR = [
    {"id": "ms", "label": "Movement Speed", "re": "{n}% increased movement speed", "def": 25},
    {"id": "life", "label": "Maximum Life", "re": "\\+{n} to maximum life", "def": 80},
    {"id": "mana", "label": "Maximum Mana", "re": "\\+{n} to maximum mana", "def": 80},
    {"id": "spirit", "label": "Spirit", "re": "\\+{n} to spirit", "def": 30},
    {"id": "lvl", "label": "+ Level of all ... Skills (any)", "re": "\\+{n} to level of all", "def": 2},
    {"id": "lvlspell", "label": "+ Level of all Spell Skills", "re": "\\+{n} to level of all spell", "def": 2},
    {"id": "lvlminion", "label": "+ Level of all Minion Skills", "re": "\\+{n} to level of all minion", "def": 2},
    {"id": "lvlmelee", "label": "+ Level of all Melee Skills", "re": "\\+{n} to level of all melee", "def": 2},
    {"id": "lvlproj", "label": "+ Level of all Projectile Skills", "re": "\\+{n} to level of all projectile", "def": 2},
    {"id": "resfire", "label": "Fire Resistance", "re": "\\+{n}% to fire res", "def": 30},
    {"id": "rescold", "label": "Cold Resistance", "re": "\\+{n}% to cold res", "def": 30},
    {"id": "reslight", "label": "Lightning Resistance", "re": "\\+{n}% to lightning res", "def": 30},
    {"id": "reschaos", "label": "Chaos Resistance", "re": "\\+{n}% to chaos res", "def": 15},
    {"id": "resall", "label": "All Elemental Resistances", "re": "\\+{n}% to all elemental", "def": 10},
    {"id": "physinc", "label": "% increased Physical Damage", "re": "{n}% increased physical damage", "def": 100},
    {"id": "aspd", "label": "% increased Attack Speed", "re": "{n}% increased attack speed", "def": 15},
    {"id": "cspd", "label": "% increased Cast Speed", "re": "{n}% increased cast speed", "def": 15},
    {"id": "crit", "label": "% increased Critical Hit Chance", "re": "{n}% increased critical hit chance", "def": 25},
    {"id": "spelldmg", "label": "% increased Spell Damage", "re": "{n}% increased spell damage", "def": 50},
    {"id": "rarity", "label": "% increased Rarity of Items found", "re": "{n}% increased rarity of items", "def": 15},
    {"id": "attr", "label": "+ Strength / Dexterity / Intelligence",
     "re": "\\+{n} to (strength|dexterity|intelligence|all attributes)", "def": 20},
]

# Wlasciwosci Waystone'a z progiem. Etykiety sprawdzone na zywym tekscie
# przedmiotu ("Item Rarity: +19% (augmented)"). "em rarity" odroznia Item
# Rarity od Monster Rarity ("er rarity").
WAYSTONE_PROPS = [
    {"id": "tier", "label": "Waystone Tier", "re": "tier {n}\\)", "def": 15},
    {"id": "iir", "label": "Item Rarity", "re": "em rarity: \\+{n}%", "def": 30},
    {"id": "pack", "label": "Pack Size", "re": "ck size: \\+{n}%", "def": 20},
    {"id": "mrar", "label": "Monster Rarity", "re": "er rarity: \\+{n}%", "def": 30},
    {"id": "drop", "label": "Waystone Drop Chance", "re": "op chance: \\+{n}%", "def": 100},
]


def main() -> int:
    ways = waystone_texts()
    print(f"Waystone: {len(ways)} modow")
    waystone = build_pool(ways, NOISE_WAYSTONE)
    tabs = tablet_texts(set(ways))
    print(f"Tablety: {len(tabs)} modow")
    tablet = build_pool(tabs, NOISE_TABLET)
    OUT.write_text(json.dumps({
        "generated": date.today().isoformat(),
        "waystone": waystone, "waystoneProps": WAYSTONE_PROPS,
        "tablet": tablet, "vendor": VENDOR,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"zapisano {OUT} ({OUT.stat().st_size} B): "
          f"waystone {len(waystone)}, tablet {len(tablet)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
