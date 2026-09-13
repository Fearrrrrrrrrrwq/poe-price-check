"""Dane dla kalkulatora Instill PoE2 (poepricecheck.eu/tools/poe2-instill/).

Uruchomienie:  python web/tools/instill_data.py
Wynik:         web/assets/instill-data.json  (commitowany - build strony go kopiuje)

Skad dane:
  - Przepisy: data/stats_poe2.ndjson (Exiled Exchange 2, MIT) - statystyka
    "Allocates #" ma przy kazdej nazwie notable pole "oils" = trzy indeksy
    Distilled Emotions w kolejnosci slotow, a "value" = hash pasywki.
  - Opisy notable: drzewo pasywne PoE2 z RePoE (repoe-fork.github.io/poe2,
    passive_skill_trees/Default.json) - po hashu.
  - Tekst statystyk: tlumaczenia RePoE (passive_skill_stat_descriptions i
    stat_descriptions) - te same szablony, z ktorych gra sklada opis pasywki.

Kolejnosc emocji MA znaczenie: ten sam zestaw w innej kolejnosci daje inny
notable (9,0,5 = Void, 0,5,9 = Revenge) - sprawdzone na danych.
"""

import json
import pathlib
import re
import sys
from datetime import date

import requests

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "web" / "assets" / "instill-data.json"
UA = "poe-price-check/1.0 (+https://poepricecheck.eu)"
REPOE = "https://repoe-fork.github.io/poe2"

# Kolejnosc indeksow z danych - ta sama tabela co w Exiled Exchange 2
# (renderer/src/web/price-check/filters/pseudo/anointments.ts).
EMOTIONS = [
    "Diluted Liquid Ire", "Diluted Liquid Guilt", "Diluted Liquid Greed",
    "Liquid Paranoia", "Liquid Envy", "Liquid Disgust", "Liquid Despair",
    "Concentrated Liquid Fear", "Concentrated Liquid Suffering", "Concentrated Liquid Isolation",
    "Potent Liquid Melancholy", "Potent Liquid Ferocity", "Potent Liquid Contempt",
]

MARKUP = re.compile(r"\[(?:[^\]|]*\|)?([^\]]+)\]")

# index_handlers z RePoE: przeliczenie wartosci przed wstawieniem do tekstu.
HANDLERS = {
    "negate": lambda v: -v,
    "negate_and_double": lambda v: -2 * v,
    "double": lambda v: 2 * v,
    "divide_by_two_0dp": lambda v: v / 2,
    "divide_by_three": lambda v: v / 3,
    "divide_by_four": lambda v: v / 4,
    "divide_by_five": lambda v: v / 5,
    "divide_by_six": lambda v: v / 6,
    "divide_by_ten_0dp": lambda v: v / 10,
    "divide_by_ten_1dp": lambda v: v / 10,
    "divide_by_ten_1dp_if_required": lambda v: v / 10,
    "divide_by_twelve": lambda v: v / 12,
    "divide_by_fifteen_0dp": lambda v: v / 15,
    "divide_by_twenty": lambda v: v / 20,
    "divide_by_twenty_then_double_0dp": lambda v: v / 10,
    "divide_by_fifty": lambda v: v / 50,
    "divide_by_one_hundred": lambda v: v / 100,
    "divide_by_one_hundred_0dp": lambda v: v / 100,
    "divide_by_one_hundred_1dp": lambda v: v / 100,
    "divide_by_one_hundred_2dp": lambda v: v / 100,
    "divide_by_one_hundred_2dp_if_required": lambda v: v / 100,
    "divide_by_one_hundred_and_negate": lambda v: -v / 100,
    "divide_by_one_thousand": lambda v: v / 1000,
    "per_minute_to_per_second": lambda v: v / 60,
    "per_minute_to_per_second_0dp": lambda v: v / 60,
    "per_minute_to_per_second_1dp": lambda v: v / 60,
    "per_minute_to_per_second_2dp": lambda v: v / 60,
    "per_minute_to_per_second_2dp_if_required": lambda v: v / 60,
    "milliseconds_to_seconds": lambda v: v / 1000,
    "milliseconds_to_seconds_0dp": lambda v: v / 1000,
    "milliseconds_to_seconds_1dp": lambda v: v / 1000,
    "milliseconds_to_seconds_2dp": lambda v: v / 1000,
    "milliseconds_to_seconds_2dp_if_required": lambda v: v / 1000,
    "deciseconds_to_seconds": lambda v: v / 10,
    "locations_to_metres": lambda v: v / 10,
    "multiply_by_four": lambda v: v * 4,
    "times_one_point_five": lambda v: v * 1.5,
    "times_twenty": lambda v: v * 20,
    "30%_of_value": lambda v: v * 0.3,
    "60%_of_value": lambda v: v * 0.6,
    "multiplicative_damage_modifier": lambda v: v + 100,
    "multiplicative_permyriad_damage_modifier": lambda v: v / 100 + 100,
    "old_leech_percent": lambda v: v / 5,
    "old_leech_permyriad": lambda v: v / 50,
    "permyriad_to_percent": lambda v: v / 100,
}


def fetch_json(url: str):
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=120)
    resp.raise_for_status()
    return resp.json()


def number(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.2f}".rstrip("0").rstrip(".")


def cond_ok(cond: dict, v: float) -> bool:
    ok = True
    if "min" in cond and cond["min"] is not None and v < cond["min"]:
        ok = False
    if "max" in cond and cond["max"] is not None and v > cond["max"]:
        ok = False
    return (not ok) if cond.get("negated") else ok


def build_translator(entries: list[dict]):
    index: dict[str, dict] = {}
    for entry in entries:
        for sid in entry.get("ids", []):
            index.setdefault(sid, entry)

    def translate(stats: dict) -> tuple[list[str], list[str]]:
        lines, missing, used = [], [], set()
        for sid in stats:
            if sid in used:
                continue
            entry = index.get(sid)
            if entry is None:
                missing.append(sid)
                continue
            ids = entry["ids"]
            used.update(ids)
            values = [stats.get(i, 0) for i in ids]
            for variant in entry.get("English", []):
                conds = variant.get("condition") or [{}] * len(ids)
                if not all(cond_ok(c or {}, v) for c, v in zip(conds, values)):
                    continue
                text = variant["string"]
                for i, v in enumerate(values):
                    handlers = (variant.get("index_handlers") or [[]] * len(ids))[i] or []
                    for h in handlers:
                        v = HANDLERS.get(h, lambda x: x)(v)
                    fmt = (variant.get("format") or ["#"] * len(ids))[i]
                    if fmt == "ignore":
                        rep = ""
                    elif fmt == "+#":
                        rep = ("+" if v > 0 else "") + number(v)
                    else:
                        rep = number(v)
                    text = text.replace("{" + str(i) + "}", rep)
                    text = re.sub(r"\{" + str(i) + r":[+]?d\}", ("+" if v > 0 else "") + number(v), text)
                text = MARKUP.sub(r"\1", text)
                lines.extend(part.strip() for part in text.split("\n") if part.strip())
                break
        return lines, missing

    return translate


def main() -> int:
    recipes = []
    for line in (ROOT / "data" / "stats_poe2.ndjson").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        for m in rec.get("matchers", []):
            if m.get("oils") and m.get("string", "").startswith("Allocates "):
                recipes.append((m["string"][len("Allocates "):], int(m["value"]),
                                [int(x) for x in str(m["oils"]).split(",")]))
    print(f"przepisow: {len(recipes)}")

    tree = fetch_json(f"{REPOE}/passive_skill_trees/Default.min.json")
    by_hash = {int(v["hash"]): v for v in tree["passives"].values() if "hash" in v}
    translations = (fetch_json(f"{REPOE}/stat_translations/passive_skill_stat_descriptions.min.json")
                    + fetch_json(f"{REPOE}/stat_translations/stat_descriptions.min.json"))
    translate = build_translator(translations)

    notables, missing_nodes, missing_stats = [], 0, set()
    for name, passive_hash, oils in recipes:
        if any(i >= len(EMOTIONS) for i in oils):
            print(f"  [pomijam - nieznana emocja] {name} {oils}")
            continue
        node = by_hash.get(passive_hash)
        stats: list[str] = []
        if node is None:
            missing_nodes += 1
        else:
            stats, missing = translate(node.get("stats") or {})
            missing_stats.update(missing)
        notables.append({"name": name, "recipe": oils, "stats": stats})
    notables.sort(key=lambda n: n["name"].lower())

    OUT.write_text(json.dumps({
        "generated": date.today().isoformat(),
        "emotions": EMOTIONS,
        "notables": notables,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"zapisano {OUT} ({OUT.stat().st_size} B): {len(notables)} notable, "
          f"bez wezla w drzewie: {missing_nodes}, statystyki bez tlumaczenia: {sorted(missing_stats)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
