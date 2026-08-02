"""Test dymny: sprawdza czy API trade'a odpowiada i czy parser + matcher dzialaja.

Uruchom:  python smoke_test.py
"""

import sys

from item_parser import parse_item
from trade_api import ALL_STAT_KINDS, BASE, TradeClient, TradeError

UA = "poe-price-check/1.0 (+https://poepricecheck.eu)"

UNIQUE_SAMPLE = """Item Class: Body Armours
Rarity: Unique
Tabula Rasa
Simple Robe
--------
Sockets: W-W-W-W-W-W
--------
Item Level: 68
--------
Item has no level requirement and Energy Shield (Hidden)
Socketed Gems are Supported by Level 10 Item Rarity (Hidden)
"""

RARE_SAMPLE = """Item Class: Rings
Rarity: Rare
Doom Circle
Two-Stone Ring
--------
Requirements:
Level: 60
--------
Item Level: 84
--------
+16% to Fire and Lightning Resistances (implicit)
--------
+35 to maximum Life
+42% to Fire Resistance
+31% to Cold Resistance
15% increased Rarity of Items found
Adds 3 to 9 Physical Damage to Attacks
"""


def main() -> int:
    print("== ligi ==")
    try:
        leagues = TradeClient.fetch_leagues(UA)
    except Exception as exc:  # noqa: BLE001 - to jest test dymny
        print(f"BLAD pobierania lig: {exc}")
        return 1
    print(", ".join(leagues))

    league = next(
        (l for l in leagues if l not in ("Standard", "Hardcore", "Ruthless", "Hardcore Ruthless")
         and not l.startswith("SSF")),
        "Standard",
    )
    print(f"-> uzywam ligi: {league}\n")

    client = TradeClient(league=league, user_agent=UA)

    print("== slownik statystyk ==")
    index = client.stat_index()
    print(f"wpisow: {len(index)}")

    # GGG dokłada nowe grupy statystyk przy kolejnych ligach. Grupa, ktorej nie
    # ma w ALL_STAT_KINDS, jest dla nas niewidoczna - jej mody nigdy sie nie
    # dopasuja, a wyszukiwanie po cichu zwroci nie to, co trzeba. Tak wlasnie
    # przegapilismy piec grup naraz.

    data = client._cached("stats", f"{BASE}/api/trade/data/stats")
    theirs = {group.get("id") for group in data.get("result", []) if group.get("id")}
    missing = sorted(theirs - set(ALL_STAT_KINDS))
    if missing:
        print(f"UWAGA: GGG ma grupy, ktorych nie znamy: {missing}")
        print("       Dopisz je do ALL_STAT_KINDS w trade_api.py.")
    else:
        print(f"grupy statystyk: znamy wszystkie {len(theirs)}")
    print()

    for label, sample in (("UNIKAT", UNIQUE_SAMPLE), ("RZADKI", RARE_SAMPLE)):
        print(f"== {label} ==")
        item = parse_item(sample)
        print(f"nazwa      : {item.display_name()}")
        print(f"rzadkosc   : {item.rarity}  ilvl={item.item_level}  linki={item.link_count}")

        filters, unmatched = client.match_mods(item)
        print(f"dopasowane : {len(filters)} modow")
        for f in filters:
            print(f"    {f['id']}  min={f.get('value', {}).get('min')}")
        if unmatched:
            print(f"NIEdopasowane ({len(unmatched)}):")
            for mod in unmatched:
                print(f"    [{mod.kind}] {mod.text}")

        try:
            result = client.price_check(item, max_listings=5)
        except TradeError as exc:
            print(f"BLAD wyszukiwania: {exc}\n")
            continue

        print(f"ofert      : {result.total}   "
              f"(mody w filtrze: {result.mods_used}, nierozpoznane: {result.mods_unmatched})")
        for listing in result.listings:
            print(f"    {listing.price_text():>18}  {listing.item_name}  @{listing.account}")
        print(f"link       : {result.browser_url()}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
