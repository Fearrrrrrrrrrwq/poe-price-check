"""Dane dla PoE1 Regex (poepricecheck.eu/tools/poe-map-regex/): mapy, vendor,
kontrakty/blueprinty Heist i Expedition Logbooki.

Uruchomienie:
  python web/tools/map_regex_data.py --sample maps.json --sample-extra heist_logbook.json
Wynik: web/assets/map-regex-data.json (commitowany - build strony go czyta)

Skad teksty:
  - Pule modow: RePoE (repoe-fork.github.io, mods.json).
      mapy:     domena "area", prefix/suffix, id "Map...", tagi map (default,
                *_tier_map, maven/primordial, T17: uber_tier_map / has_uber_map_*)
      heist:    domena "heist_area", prefix/suffix z waga "default"
      logbooki: domena "area" z tagiem "expedition_logbook" (mody) oraz
                generation_type "expedition_logbook" (bonusy obszarow)
  - Tekst: tlumaczenia statystyk RePoE (ten sam tlumacz co kalkulator Instill).
  - Widocznosc linii: czesc statystyk moda gra ukrywa ("# patches with Ground
    Effect per # tiles"). Linia zostaje, jesli jej szablon istnieje na liscie
    statystyk trade PoE1 - fragment z ukrytej linii nigdy by niczego nie trafil.
  - Probki (--sample: lista tekstow map, --sample-extra: {"contract": [...],
    "blueprint": [...], "logbook": [...]}) z trade: dopisuja linie spoza RePoE
    (enchanty Delirium, Originator) i wszystkie NIE-modowe linie przedmiotow
    jako szum - fragment nie moze trafic w nazwe klienta, obszaru czy opis.

Pule sa weryfikowane na tych samych probkach (skrypt weryfikacyjny zyje obok
danych testowych, nie w repo).
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

# Progi wlasciwosci - etykiety sprawdzone na zywym tekscie przedmiotow z trade.
# "re" bez {n} = sama obecnosc (bez pola liczby).
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

HEIST_JOBS = ("Lockpicking", "Brute Force", "Perception", "Demolition", "Counter-Thaumaturgy",
              "Trap Disarmament", "Agility", "Deception", "Engineering")
HEIST_PROPS = [
    {"id": "alvl", "label": "Area Level", "re": "area level: {n}", "def": 81},
    {"id": "iiq", "label": "Item Quantity", "re": "quantity: \\+{n}%", "def": 50},
    {"id": "iir", "label": "Item Rarity", "re": "rarity: \\+{n}%", "def": 30},
    {"id": "alert", "label": "Alert Level Reduction", "re": "reduction: \\+{n}%", "def": 20},
    {"id": "lockdown", "label": "Time Before Lockdown", "re": "lockdown: \\+{n}%", "def": 20},
    {"id": "precious", "label": "Target: Precious or Priceless", "re": "(precious|priceless)\\)", "def": None},
    {"id": "priceless", "label": "Target: Priceless", "re": "priceless\\)", "def": None},
] + [{"id": "job-" + job.lower().replace(" ", "-"), "label": f"{job} level", "group": "job",
      "re": job.lower() + " \\(level {n}\\)", "def": 1} for job in HEIST_JOBS]

LOGBOOK_PROPS = [
    {"id": "alvl", "label": "Area Level", "re": "area level: {n}", "def": 81},
    {"id": "iiq", "label": "Item Quantity", "re": "quantity: \\+{n}%", "def": 50},
    {"id": "iir", "label": "Item Rarity", "re": "rarity: \\+{n}%", "def": 30},
    {"id": "pack", "label": "Monster Pack Size", "re": "size: \\+{n}%", "def": 20},
]
LOGBOOK_FACTIONS = ("Black Scythe Mercenaries", "Druids of the Broken Circle",
                    "Knights of the Sun", "Order of the Chalice")

# Vendor przy levelowaniu. Hybrydowe odpornosci ("+#% to Fire and Cold
# Resistances") licza sie do obu zywiolow.
VENDOR_PROPS = [
    {"id": "ms", "label": "Movement Speed", "re": "{n}% increased movement speed", "def": 10},
    {"id": "life", "label": "Maximum Life", "re": "\\+{n} to maximum life", "def": 30},
    {"id": "mana", "label": "Maximum Mana", "re": "\\+{n} to maximum mana", "def": 30},
    {"id": "es", "label": "Maximum Energy Shield", "re": "\\+{n} to maximum energy", "def": 20},
    {"id": "fire", "label": "Fire Resistance", "re": "\\+{n}% to fire", "def": 15},
    {"id": "cold", "label": "Cold Resistance", "re": "\\+{n}% to (cold|fire and cold)", "def": 15},
    {"id": "light", "label": "Lightning Resistance", "re": "\\+{n}% to (lightning|\\w+ and lightning)", "def": 15},
    {"id": "allres", "label": "All Elemental Resistances", "re": "\\+{n}% to all ele", "def": 8},
    {"id": "chaos", "label": "Chaos Resistance", "re": "\\+{n}% to chaos res", "def": 10},
    {"id": "str", "label": "Strength", "re": "\\+{n} to strength", "def": 15},
    {"id": "dex", "label": "Dexterity", "re": "\\+{n} to dexterity", "def": 15},
    {"id": "int", "label": "Intelligence", "re": "\\+{n} to intelligence", "def": 15},
    {"id": "phys", "label": "Increased Physical Damage", "re": "{n}% increased physical damage", "def": 40},
    {"id": "aspd", "label": "Attack Speed", "re": "{n}% increased attack speed", "def": 8},
    {"id": "spell", "label": "Spell Damage", "re": "{n}% increased spell damage", "def": 20},
    {"id": "cspd", "label": "Cast Speed", "re": "{n}% increased cast speed", "def": 8},
    {"id": "gems", "label": "+ Level of Socketed Gems", "re": "\\+{n} to level of socketed gems", "def": 1},
    {"id": "spellgems", "label": "+ Level of Spell Skill Gems", "re": "\\+{n} to level of all.*spell", "def": 1},
    {"id": "minion", "label": "+ Level of Minion Gems", "re": "\\+{n} to level of all minion", "def": 1},
    {"id": "addphys", "label": "Adds Physical Damage", "re": "adds \\d+ to \\d+ physical", "def": None},
    {"id": "addfire", "label": "Adds Fire Damage", "re": "adds \\d+ to \\d+ fire", "def": None},
    {"id": "addcold", "label": "Adds Cold Damage", "re": "adds \\d+ to \\d+ cold", "def": None},
    {"id": "addlight", "label": "Adds Lightning Damage", "re": "adds \\d+ to \\d+ lightning", "def": None},
]

MARKUP = re.compile(r"\[(?:[^\]|]*\|)?([^\]]+)\]")
FLAGS = {"corrupted", "unidentified", "unmodifiable", "mirrored", "split"}
SAMPLE_ARG = "--sample"
EXTRA_ARG = "--sample-extra"
NUM = re.compile(r"[+-]?\d+(?:\.\d+)?")


def _sections(text: str) -> list[list[str]]:
    text = text.replace("\r\n", "\n")
    return [sec.strip().split("\n") for sec in re.split(r"\n-{8}\n", text)]


def map_mod_lines(text: str) -> list[str]:
    """Linie modow z tekstu mapy: sekcje miedzy "Monster Level:" a opisem "Travel to"."""
    out, after = [], False
    for sec in _sections(text):
        if any(ln.startswith("Monster Level:") for ln in sec):
            after = True
            continue
        if after:
            if any(ln.startswith("Travel to") for ln in sec):
                break
            out.extend(ln.strip() for ln in sec if ln.strip())
    return out


def heist_mod_lines(text: str) -> list[str]:
    """Kontrakt/blueprint: jedna sekcja zaraz po "Item Level:" (dalej opis i instrukcja)."""
    secs = _sections(text)
    for i, sec in enumerate(secs):
        if any(ln.startswith("Item Level:") for ln in sec) and i + 1 < len(secs):
            nxt = secs[i + 1]
            if nxt and not nxt[0].startswith(('"', "Give this", "Use Intelligence")):
                return [ln.strip() for ln in nxt if ln.strip()]
    return []


def logbook_lines(text: str) -> tuple[list[str], list[str]]:
    """Logbook: (frakcje + bonusy obszarow, mody). Pierwsza linia sekcji obszaru to jego nazwa."""
    implicit, explicit, after = [], [], False
    for sec in _sections(text):
        if any(ln.startswith("Item Level:") for ln in sec):
            after = True
            continue
        if not after:
            continue
        if any(ln.startswith("Take this item") for ln in sec):
            break
        if any("(implicit)" in ln for ln in sec):
            implicit.extend(ln.strip() for ln in sec[1:] if ln.strip())
        else:
            explicit.extend(ln.strip() for ln in sec if ln.strip())
    return implicit, explicit


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
    return NUM.sub("#", text.lower())


def clean_line(line: str) -> str:
    line = MARKUP.sub(r"\1", line)
    for suffix in (" (enchant)", " (implicit)", " (augmented)"):
        line = line.replace(suffix, "")
    return NUM.sub("#", line.strip())


def fetch_json(url: str):
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=180)
    resp.raise_for_status()
    return resp.json()


def tpl(text: str) -> str:
    return NUM.sub("#", text.lower()).replace("+#", "#").strip()


class Pool:
    """Pula linii jednego rodzaju przedmiotu (per linia, nie per mod: wyszukiwarka
    dopasowuje pojedyncze linie - mod T17 z trzema klatwami to trzy linie)."""

    def __init__(self) -> None:
        self.lines: dict[str, dict] = {}
        self.noise: list[str] = []

    def add(self, line: str, source: str, t17: bool = False, group: str = "") -> None:
        text = clean_line(line)
        # "DNT ..." (do not translate) to niewydane mody z plikow gry.
        if not text or text.lower() in FLAGS or text.startswith("DNT"):
            return
        entry = self.lines.get(text)
        if entry is None:
            self.lines[text] = {"t17": t17, "source": source, "group": group}
        elif source == "repoe" and not t17:
            entry["t17"] = False

    def add_noise_from(self, item_text: str) -> None:
        """Wszystkie linie przedmiotu, ktore nie sa w puli, sa szumem."""
        for sec in _sections(item_text):
            for ln in sec:
                if ln.strip() and clean_line(ln) not in self.lines:
                    self.noise.append(_norm(clean_line(ln)))

    def build(self, extra_noise: list[str]) -> list[dict]:
        noise = extra_noise + self.noise
        texts = sorted(self.lines, key=str.lower)
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
                frag = shortest_fragment(text, [o for o in others if o not in supers], noise,
                                         allowed=ALLOWED_MAP)
                also = len(supers)
            if not frag:
                print(f"  [pomijam - brak unikalnego fragmentu] {text}")
                continue
            item = {"text": text, "frag": frag}
            if also:
                item["also"] = also
            info = self.lines[text]
            if info["t17"]:
                item["t17"] = True
            if info["group"]:
                item["group"] = info["group"]
            out.append(item)
        return out


def main() -> int:
    mods = fetch_json(f"{REPOE}/mods.min.json")
    translate = build_translator(fetch_json(f"{REPOE}/stat_translations.min.json"))
    stats_cache = ROOT / ".cache" / "stats.json"
    try:
        trade_stats = fetch_json("https://www.pathofexile.com/api/trade/data/stats")
    except requests.RequestException:
        trade_stats = json.loads(stats_cache.read_text(encoding="utf-8"))
    visible = {tpl(e["text"]) for g in trade_stats.get("result", []) for e in g.get("entries", [])}

    maps, heist, logbook = Pool(), Pool(), Pool()

    def mod_lines(mod: dict) -> list[str]:
        stats = {s["id"]: s.get("max", s.get("min", 0)) for s in mod.get("stats", [])}
        lines, _ = translate(stats)
        return [ln for ln in lines if tpl(ln) in visible] or lines[:1]

    for mod_id, mod in mods.items():
        tags = {w["tag"] for w in mod.get("spawn_weights", []) if w.get("weight", 0) > 0}
        domain, gen = mod.get("domain"), mod.get("generation_type")
        if domain == "area" and gen in ("prefix", "suffix") and mod_id.startswith("Map"):
            if "expedition_logbook" in tags:
                for ln in mod_lines(mod):
                    logbook.add(ln, "repoe", group="mod")
            if tags & MAP_TAGS and "Expedition" not in mod_id:
                for ln in mod_lines(mod):
                    maps.add(ln, "repoe", t17=not (tags - T17_TAGS))
        elif domain == "area" and gen == "expedition_logbook":
            for ln in mod_lines(mod):
                logbook.add(ln, "repoe", group="bonus")
        elif domain == "heist_area" and gen in ("prefix", "suffix") and "default" in tags:
            for ln in mod_lines(mod):
                heist.add(ln, "repoe")
    for faction in LOGBOOK_FACTIONS:
        logbook.add(faction, "fixed", group="faction")

    # Probki z trade: linie spoza RePoE (enchanty Delirium, Originator) + szum.
    sample, extra = [], {}
    if SAMPLE_ARG in sys.argv:
        sample = json.loads(pathlib.Path(sys.argv[sys.argv.index(SAMPLE_ARG) + 1]).read_text(encoding="utf-8"))
        for item_text in sample:
            for ln in map_mod_lines(item_text):
                maps.add(ln, "sample")
    if EXTRA_ARG in sys.argv:
        extra = json.loads(pathlib.Path(sys.argv[sys.argv.index(EXTRA_ARG) + 1]).read_text(encoding="utf-8"))
        for item_text in extra.get("contract", []) + extra.get("blueprint", []):
            for ln in heist_mod_lines(item_text):
                heist.add(ln, "sample")
        for item_text in extra.get("logbook", []):
            implicit, explicit = logbook_lines(item_text)
            for ln in implicit:
                if ln not in LOGBOOK_FACTIONS:
                    logbook.add(ln, "sample", group="bonus")
            for ln in explicit:
                logbook.add(ln, "sample", group="mod")
    # Szum dopiero po zebraniu calej puli - inaczej linia z pozniejszej probki
    # wpadlaby do szumu wczesniejszej.
    for item_text in sample:
        head = item_text.replace("\r", "").split("\n")[2:4]  # nazwa rzadkiej mapy + baza
        maps.noise.extend(h.lower() for h in head if not h.startswith("--"))
    for item_text in extra.get("contract", []) + extra.get("blueprint", []):
        heist.add_noise_from(item_text)
    for item_text in extra.get("logbook", []):
        logbook.add_noise_from(item_text)

    # Nazwy baz i unikatowych map tez sa przeszukiwane - "guard" trafialby
    # w kazda "Shaper Guardian Map".
    map_names = []
    try:
        items = fetch_json("https://www.pathofexile.com/api/trade/data/items")
        for group in items.get("result", []):
            for e in group.get("entries", []):
                if (e.get("type") or "").endswith(" Map"):
                    map_names.extend(x.lower() for x in (e.get("type"), e.get("name")) if x)
    except requests.RequestException:
        print("  [uwaga] brak listy map z trade - fragmenty nie sprawdzone wzgledem nazw map")

    order = {"faction": 0, "bonus": 1, "mod": 2}
    logbook_out = sorted(logbook.build([]), key=lambda m: order.get(m.get("group", "mod"), 2))
    data = {
        "generated": date.today().isoformat(),
        "maps": {"mods": maps.build(NOISE + map_names), "props": PROPS},
        "vendor": {"props": VENDOR_PROPS},
        "heist": {"mods": heist.build([]), "props": HEIST_PROPS},
        "logbook": {"mods": logbook_out, "props": LOGBOOK_PROPS},
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"zapisano {OUT} ({OUT.stat().st_size} B): mapy {len(data['maps']['mods'])} "
          f"(T17: {sum(1 for m in data['maps']['mods'] if m.get('t17'))}), "
          f"heist {len(data['heist']['mods'])}, logbooki {len(logbook_out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
