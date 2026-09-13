"""Dane dla PoE1 Map Regex (poepricecheck.eu/tools/poe-map-regex/).

Uruchomienie:  python web/tools/map_regex_data.py
Wynik:         web/assets/map-regex-data.json  (commitowany - build strony go kopiuje)

Skad teksty:
  - Pula modow: RePoE (repoe-fork.github.io, mods.json) - mody z domeny "area",
    prefix/suffix, id "Map...", z waga dla tagow map (default, *_tier_map,
    maven/primordial, T17: uber_tier_map / has_uber_map_*). Mody Expedition
    (logbooki) i bocznych obszarow Vaal odpadaja.
  - Tekst: tlumaczenia statystyk RePoE (ten sam tlumacz co kalkulator Instill).
  - Widocznosc linii: czesc statystyk moda gra ukrywa ("# patches with Ground
    Effect per # tiles"). Linia zostaje, jesli jej szablon istnieje na liscie
    statystyk trade PoE1 - fragment z ukrytej linii nigdy by niczego nie trafil.

Pula jest weryfikowana na prawdziwych mapach z trade (patrz komentarz w
main - skrypt weryfikacyjny zyje obok danych testowych, nie w repo).
"""

import json
import pathlib
import re
import sys
from datetime import date

import requests

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
from tools.instill_data import build_translator  # noqa: E402
from tools.regex_data import shortest_fragment  # noqa: E402

OUT = ROOT / "web" / "assets" / "map-regex-data.json"
UA = "poe-price-check/1.0 (+https://poepricecheck.eu)"
REPOE = "https://repoe-fork.github.io"

MAP_TAGS = {"default", "low_tier_map", "mid_tier_map", "top_tier_map", "uber_tier_map",
            "has_uber_map_prefix", "has_uber_map_prefix ", "has_uber_map_suffix",
            "maven_map", "primordial_map"}
T17_TAGS = {"uber_tier_map", "has_uber_map_prefix", "has_uber_map_prefix ", "has_uber_map_suffix"}

# Linie obecne na KAZDEJ mapie - fragment nie moze w nie trafic.
NOISE = [
    "item class: maps", "rarity: rare", "rarity: magic", "rarity: normal", "map (tier #)",
    "item quantity: +#%", "item rarity: +#%", "monster pack size: +#%", "quality: +#%",
    "item level: #", "monster level: #", "corrupted", "unidentified", "unmodifiable", "(augmented)",
    "chance for dropped maps to convert to:", "conqueror map: #%", "unique map: #%", "scarab: #%",
    "map area:", "reward:", "delirium reward type:", "more maps: +#%", "more currency: +#%",
    "more scarabs: +#%", "shaper map: #%", "elder map: #%", "foil (celestial",
    "modifiable only with chaos orbs, vaal orbs, delirium orbs and chisels",
    "travel to a map of this tier or lower by using this in a personal map device. "
    "maps can only be used once.",
    "travel to this map by using it in a personal map device. maps can only be used once.",
]

# Progi wlasciwosci - etykiety sprawdzone na zywym tekscie mapy z trade.
PROPS = [
    {"id": "tier", "label": "Map Tier", "re": "tier {n}\\)", "def": 16},
    {"id": "iiq", "label": "Item Quantity", "re": "quantity: \\+{n}%", "def": 80},
    {"id": "iir", "label": "Item Rarity", "re": "rarity: \\+{n}%", "def": 50},
    {"id": "pack", "label": "Monster Pack Size", "re": "size: \\+{n}%", "def": 25},
    {"id": "maps", "label": "More Maps", "re": "maps: \\+{n}%", "def": 20},
    {"id": "currency", "label": "More Currency", "re": "currency: \\+{n}%", "def": 20},
    {"id": "scarabs", "label": "More Scarabs", "re": "scarabs: \\+{n}%", "def": 20},
    {"id": "scarab", "label": "Converts to Scarab", "re": "scarab: {n}%", "def": 40},
    {"id": "umap", "label": "Converts to Unique Map", "re": "unique map: {n}%", "def": 5},
    {"id": "conq", "label": "Converts to Conqueror Map", "re": "conqueror map: {n}%", "def": 5},
    {"id": "shaper", "label": "Converts to Shaper Map", "re": "shaper map: {n}%", "def": 5},
    {"id": "elder", "label": "Converts to Elder Map", "re": "elder map: {n}%", "def": 5},
]


MARKUP = re.compile(r"\[(?:[^\]|]*\|)?([^\]]+)\]")
FLAGS = {"corrupted", "unidentified", "unmodifiable", "mirrored", "split"}
SAMPLE_ARG = "--sample"


def map_mod_lines(text: str) -> list[str]:
    """Linie modow z tekstu mapy: sekcje miedzy "Monster Level:" a opisem "Travel to"."""
    text = text.replace("\r\n", "\n")
    sections = [sec.strip().split("\n") for sec in re.split(r"\n-{8}\n", text)]
    out, after = [], False
    for sec in sections:
        if any(ln.startswith("Monster Level:") for ln in sec):
            after = True
            continue
        if after:
            if any(ln.startswith("Travel to") for ln in sec):
                break
            out.extend(ln.strip() for ln in sec if ln.strip())
    return out


# Dwukropek dozwolony: "type: currency" jest jedynym unikalnym kawalkiem linii
# enchantu Delirium ("currency" i "armour" wystepuja w innych modach).
ALLOWED_MAP = re.compile(r"^[a-z][a-z ',:-]*[a-z]$")
SPAN_SIDE = re.compile(r"^[a-z ',:%-]*$")


def span_fragment(text: str, others: list[str], noise: list[str], max_side: int = 24) -> str:
    """Fragment "lewo.*prawo" przez liczbe, gdy zadna ciagla czesc nie jest unikalna.

    "Monsters have #% increased Area of Effect" vs "Unique Boss has #% increased
    Area of Effect": obie strony liczby wystepuja osobno w innych liniach, ale
    "ve .*% increased ar" juz nie. Wyszukiwarka PoE1 obsluguje ".*" (uzywa tego tez poe.re).
    """
    t = _norm(text)
    corpus = [_norm(o) for o in others] + noise
    best = ""
    for i, ch in enumerate(t):
        if ch != "#":
            continue
        for a in range(1, min(max_side, i) + 1):
            left = t[i - a:i]
            if not SPAN_SIDE.match(left) or not left[0].isalpha():
                continue
            for b in range(1, min(max_side, len(t) - i - 1) + 1):
                right = t[i + 1:i + 1 + b]
                if not SPAN_SIDE.match(right) or not right[-1].isalpha():
                    continue
                frag = left + ".*" + right
                if best and len(frag) >= len(best):
                    break
                pattern = re.compile(re.escape(left) + ".*" + re.escape(right))
                if not any(pattern.search(o) for o in corpus):
                    best = frag
                    break
    return best


def _norm(text: str) -> str:
    return re.sub(r"[+-]?\d+(?:\.\d+)?", "#", text.lower())


def fetch_json(url: str):
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=180)
    resp.raise_for_status()
    return resp.json()


def tpl(text: str) -> str:
    return re.sub(r"[+-]?\d+(?:\.\d+)?", "#", text.lower()).replace("+#", "#").strip()


def main() -> int:
    mods = fetch_json(f"{REPOE}/mods.min.json")
    translate = build_translator(fetch_json(f"{REPOE}/stat_translations.min.json"))
    stats_cache = ROOT / ".cache" / "stats.json"
    try:
        trade_stats = fetch_json("https://www.pathofexile.com/api/trade/data/stats")
    except requests.RequestException:
        trade_stats = json.loads(stats_cache.read_text(encoding="utf-8"))
    visible = {tpl(e["text"]) for g in trade_stats.get("result", []) for e in g.get("entries", [])}

    # Pula PER LINIA, nie per mod: wyszukiwarka dopasowuje pojedyncze linie
    # tekstu. Mod T17 laczacy trzy klatwy to trzy zwykle linie "Players are
    # Cursed with ..." - liczone jako jeden tekst wypadal jako "nieunikalny".
    lines_pool: dict[str, dict] = {}

    def add_line(line: str, t17: bool, source: str) -> None:
        line = MARKUP.sub(r"\1", line).replace(" (enchant)", "").strip()
        text = re.sub(r"[+-]?\d+(?:\.\d+)?", "#", line)
        if not text or text.lower() in FLAGS:
            return
        entry = lines_pool.get(text)
        if entry is None:
            lines_pool[text] = {"t17": t17, "source": source}
        elif source == "repoe" and not t17:
            entry["t17"] = False

    for mod_id, mod in mods.items():
        if (mod.get("domain") != "area" or mod.get("generation_type") not in ("prefix", "suffix")
                or not mod_id.startswith("Map")):
            continue
        tags = {w["tag"] for w in mod.get("spawn_weights", []) if w.get("weight", 0) > 0}
        if not tags & MAP_TAGS or "Expedition" in mod_id:
            continue
        stats = {s["id"]: s.get("max", s.get("min", 0)) for s in mod.get("stats", [])}
        lines, _ = translate(stats)
        shown = [ln for ln in lines if tpl(ln) in visible] or lines[:1]
        for ln in shown:
            add_line(ln, not (tags - T17_TAGS), "repoe")

    # Linie widziane na prawdziwych mapach z trade (Valdo, Originator, enchanty
    # Delirium) - tych nie ma w zwyklej puli modow.
    if SAMPLE_ARG in sys.argv:
        sample = json.loads(pathlib.Path(sys.argv[sys.argv.index(SAMPLE_ARG) + 1]).read_text(encoding="utf-8"))
        for item_text in sample:
            t17 = False  # linie spoza RePoE (enchanty, Originator) - bez oznaczenia T17
            for ln in map_mod_lines(item_text):
                add_line(ln, t17, "sample")

    # Nazwy baz i unikatowych map tez sa przeszukiwane - "guard" trafialby
    # w kazda "Shaper Guardian Map".
    noise = list(NOISE)
    try:
        items = fetch_json("https://www.pathofexile.com/api/trade/data/items")
        for group in items.get("result", []):
            for e in group.get("entries", []):
                if (e.get("type") or "").endswith(" Map"):
                    noise.extend(x.lower() for x in (e.get("type"), e.get("name")) if x)
    except requests.RequestException:
        print("  [uwaga] brak listy map z trade - fragmenty nie sprawdzone wzgledem nazw map")
    if SAMPLE_ARG in sys.argv:
        for item_text in sample:
            head = item_text.replace("\r", "").split("\n")[2:4]  # nazwa rzadkiej mapy + baza
            noise.extend(h.lower() for h in head if not h.startswith("--"))

    texts = sorted(lines_pool, key=str.lower)
    out = []
    for text in texts:
        others = [o for o in texts if o != text]
        frag = (shortest_fragment(text, others, noise, allowed=ALLOWED_MAP)
                or span_fragment(text, others, noise))
        also = 0
        if not frag:
            # Linia zawarta w dluzszej ("... additional Modifier" w "... Modifiers") -
            # fragment trafi tez te dluzsze, lepsze niz brak linii.
            supers = [o for o in others if _norm(text) in _norm(o)]
            frag = shortest_fragment(text, [o for o in others if o not in supers], noise, allowed=ALLOWED_MAP)
            also = len(supers)
        if not frag:
            print(f"  [pomijam - brak unikalnego fragmentu] {text}")
            continue
        item = {"text": text, "frag": frag}
        if also:
            item["also"] = also
        if lines_pool[text]["t17"]:
            item["t17"] = True
        out.append(item)

    OUT.write_text(json.dumps({"generated": date.today().isoformat(), "maps": out, "props": PROPS},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"zapisano {OUT} ({OUT.stat().st_size} B): {len(out)} linii modow "
          f"(T17: {sum(1 for m in out if m.get('t17'))})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
