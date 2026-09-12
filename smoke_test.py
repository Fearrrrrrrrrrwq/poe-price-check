"""Test dymny: sprawdza czy API trade'a odpowiada i czy parser + matcher dzialaja.

Uruchom:  python smoke_test.py
"""

import sys

from item_parser import parse_item
from trade_api import ALL_STAT_KINDS, ALL_STAT_KINDS_POE2, BASE, TradeClient, TradeError

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

WEAPON_SAMPLE = """Item Class: One Hand Swords
Rarity: Rare
Reaper's Bite
Elegant Foil
--------
Physical Damage: 15-45 (augmented)
Elemental Damage: 20-35 (augmented) (fire), 1-50 (augmented) (cold)
Critical Strike Chance: 6.50%
Attacks per Second: 1.55 (augmented)
Weapon Range: 11
--------
Requirements:
Level: 68
--------
Item Level: 80
--------
{ Prefix Modifier "Tyrannical" (Tier: 1) }
Adds 20 to 35 Fire Damage
{ Suffix Modifier "of the Order" (Tier: 2) }
+104 to Accuracy Rating
"""

ARMOUR_SAMPLE = """Item Class: Body Armours
Rarity: Rare
Iron Heart
Glorious Plate
--------
Armour: 850 (augmented)
--------
Requirements:
Level: 68
--------
Item Level: 82
--------
{ Prefix Modifier "Tyrannical" (Tier: 1) }
+120 to maximum Life
"""


PLAIN_IMPLICIT_SAMPLE = """Item Class: Rings
Rarity: Rare
Doom Whorl
Amethyst Ring
--------
Requirements:
Level: 49
--------
Item Level: 84
--------
+23% to Chaos Resistance
--------
+42 to maximum Life
+35% to Cold Resistance
"""


def check_plain_implicit() -> bool:
    """Bez rozszerzonych opisow blok implicitow ma trafic pod grupe 'implicit',
    nie 'explicit' - inaczej trade filtruje po zlym ID i wycina wszystkie oferty.
    """
    item = parse_item(PLAIN_IMPLICIT_SAMPLE)
    kinds = {m.text: m.kind for m in item.mods}
    ok = (kinds.get("+23% to Chaos Resistance") == "implicit"
          and kinds.get("+42 to maximum Life") == "explicit")
    print("== implicit bez adnotacji ==")
    print(f"  chaos res -> {kinds.get('+23% to Chaos Resistance')!r}, "
          f"life -> {kinds.get('+42 to maximum Life')!r}  [{'OK' if ok else 'BLAD'}]\n")
    return ok


def _first_stat(client: TradeClient, raw: str, text: str) -> str:
    options, _ = client.analyze_mods(parse_item(raw))
    return next((o.stat_id for o in options if o.mod.text == text and not o.sources), "")


def check_game_engine(client: TradeClient) -> bool:
    """Silnik na danych z gry: dane sie laduja, lokalne vs globalne ES
    rozstrzygniete, opis efektu flaszki nie jest brany za mody."""
    ok = client.game_stats() is not None
    armour = ("Item Class: Body Armours\nRarity: Rare\nX\nVaal Regalia\n--------\n"
              "Item Level: 84\n--------\n+80 to maximum Energy Shield\n")
    ring = ("Item Class: Rings\nRarity: Rare\nX\nMoonstone Ring\n--------\n"
            "Item Level: 84\n--------\n+30 to maximum Energy Shield\n")
    flask = ("Item Class: Utility Flasks\nRarity: Unique\nLion's Roar\nGranite Flask\n"
             "--------\nLasts 6 Seconds\n+1500 to Armour\n--------\nItem Level: 84\n"
             "--------\n9% more Melee Physical Damage during effect\n")
    local = _first_stat(client, armour, "+80 to maximum Energy Shield")
    glob = _first_stat(client, ring, "+30 to maximum Energy Shield")
    flask_mods = [m.text for m in parse_item(flask).mods]
    ok = ok and local == "explicit.stat_4052037485" and glob == "explicit.stat_3489782002"
    ok = ok and "+1500 to Armour" not in flask_mods
    print("== silnik na danych z gry ==")
    print(f"  ES pancerz -> {local}, ES pierscien -> {glob}, flaszka: {flask_mods}"
          f"  [{'OK' if ok else 'BLAD'}]\n")
    return ok


GEM_SAMPLE = """Item Class: Skill Gems
Rarity: Gem
Flameblast
--------
Spell, AoE, Fire, Channelling, Nova, Staged
Level: 23
19 Levels from Gem
+4 Levels from Global Modifiers (augmented)
Quality: +6% (augmented)
+6% Quality from Global Modifiers (augmented)
Cost: 76.9 Mana per second
--------
Requirements:
Level: 70
--------
Deals 370 to 556 Fire Damage
10 maximum Stages
"""


def check_gem() -> bool:
    """Gem PoE2: handluje sie SAMYM gemem, wiec poziom i jakosc licza sie
    tylko te "from Gem" - poziom z modyfikatorow przedmiotu dawal filtr na
    poziom, ktorego w handlu nie ma (zero ofert). Opis umiejetnosci to nie mody.
    """
    item = parse_item(GEM_SAMPLE)
    ok = item.gem_level == 19 and item.quality == 0 and not item.mods
    print("== gem PoE2 ==")
    print(f"  poziom {item.gem_level} (w grze 23), jakosc {item.quality} (w grze 6), modow {len(item.mods)}  [{'OK' if ok else 'BLAD'}]\n")
    return ok


def main() -> int:
    if not check_plain_implicit() or not check_gem():
        return 1

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

    if not check_game_engine(client):
        return 1

    for label, sample in (
        ("UNIKAT", UNIQUE_SAMPLE), ("RZADKI", RARE_SAMPLE),
        ("BRON", WEAPON_SAMPLE), ("PANCERZ", ARMOUR_SAMPLE),
    ):
        print(f"== {label} ==")
        item = parse_item(sample)
        print(f"nazwa      : {item.display_name()}")
        print(f"rzadkosc   : {item.rarity}  ilvl={item.item_level}  linki={item.link_count}")
        if item.total_dps is not None:
            print(f"dps        : {item.total_dps:.1f}  "
                  f"(pdps={item.physical_dps or 0:.1f}, edps={item.elemental_dps or 0:.1f})")
        if item.armour is not None or item.evasion is not None or item.energy_shield is not None:
            print(f"obrona     : ar={item.armour} ev={item.evasion} es={item.energy_shield}")

        filters, unmatched = client.match_mods(item)
        print(f"dopasowane : {len(filters)} modow")
        for f in filters:
            print(f"    {f['id']}  min={f.get('value', {}).get('min')}")
        if unmatched:
            print(f"NIEdopasowane ({len(unmatched)}):")
            for mod in unmatched:
                print(f"    [{mod.kind}] {mod.text}")

        properties = client.property_options(item)
        for prop in properties:
            if prop.key in (
                "pdps", "edps", "dps", "ar", "ev", "es", "ward", "block",
                "map_iiq", "map_iir", "map_packsize", "area_level",
            ):
                print(f"    wlasciwosc {prop.key}={prop.value} wlaczona={prop.enabled}")

        try:
            result = client.price_check(item, max_listings=5, properties=properties)
        except TradeError as exc:
            print(f"BLAD wyszukiwania: {exc}\n")
            continue

        print(f"ofert      : {result.total}   "
              f"(mody w filtrze: {result.mods_used}, nierozpoznane: {result.mods_unmatched})")
        for listing in result.listings:
            print(f"    {listing.price_text():>18}  {listing.item_name}  @{listing.account}")
        print(f"link       : {result.browser_url()}\n")

    print("== PoE2 (MVP - tylko lacznosc i ksztalt zapytania) ==")
    try:
        leagues2 = TradeClient.fetch_leagues(UA, game="poe2")
    except Exception as exc:  # noqa: BLE001 - to jest test dymny
        print(f"BLAD pobierania lig PoE2: {exc}\n")
        return 1
    print(", ".join(leagues2))
    league2 = next((l for l in leagues2 if l not in ("Standard", "Hardcore")), "Standard")

    client2 = TradeClient(league=league2, user_agent=UA, game="poe2")

    # PoE2 dokleja do nazwy przymiotnik zalezny od jakosci ("Exceptional Apostle
    # Leggings") - trade go nie zna, resolve_base_type() musi go zdjac.
    quality_item = parse_item(
        "Item Class: Boots\nRarity: Normal\nExceptional Apostle Leggings\n"
        "--------\nQuality: +26%\nArmour: 169\n"
    )
    resolved = client2.resolve_base_type(quality_item)
    ok_quality = resolved == "Apostle Leggings"
    print("== przymiotnik jakosci PoE2 w nazwie bazy ==")
    print(f"  'Exceptional Apostle Leggings' -> {resolved!r}  "
          f"[{'OK' if ok_quality else 'BLAD'}]\n")
    if not ok_quality:
        return 1

    data2 = client2._cached("stats", f"{BASE}/api/trade2/data/stats")
    theirs2 = {group.get("id") for group in data2.get("result", []) if group.get("id")}
    missing2 = sorted(theirs2 - set(ALL_STAT_KINDS_POE2))
    if missing2:
        print(f"UWAGA: GGG ma grupy PoE2, ktorych nie znamy: {missing2}")
        print("       Dopisz je do ALL_STAT_KINDS_POE2 w trade_api.py.")
    else:
        print(f"grupy statystyk PoE2: znamy wszystkie {len(theirs2)}")

    # Zaden z naszych przykladow tekstu przedmiotu nie jest zweryfikowany na
    # prawdziwym PoE2 - zamiast zgadywac format, sprawdzamy tylko, ze
    # zapytanie bez modow (sama nazwa bazy) faktycznie dociera do trade2.
    try:
        result2 = client2.price_check(
            parse_item(
                "Item Class: Waystones\nRarity: Normal\nWaystone (Tier 1)\n"
                "--------\nItem Level: 1\n"
            ),
            max_listings=1,
        )
        print(f"ofert (Waystone T1, {league2}): {result2.total}")
        print(f"link: {result2.browser_url()}\n")
    except TradeError as exc:
        print(f"BLAD wyszukiwania PoE2: {exc}\n")
        return 1

    print("== WAYSTONE (PoE2 - realny format wlasciwosci, zweryfikowany na zywym API) ==")
    waystone_text = (
        "Item Class: Waystones\nRarity: Rare\nDark Carving\nWaystone (Tier 15)\n"
        "--------\nRevives Available: 2\nItem Rarity: +19% (augmented)\n"
        "Pack Size: +19% (augmented)\nMonster Rarity: +24% (augmented)\n"
        "Monster Effectiveness: +30% (augmented)\nWaystone Drop Chance: +60% "
        "(augmented)\n--------\nItem Level: 81\n"
    )
    waystone = parse_item(waystone_text)
    props3 = client2.property_options(waystone)
    for prop in props3:
        print(f"    wlasciwosc {prop.key}={prop.value} wlaczona={prop.enabled}")
    try:
        result3 = client2.price_check(waystone, max_listings=3, properties=props3)
        print(f"ofert (Waystone T15 z filtrami, {league2}): {result3.total}")
        print(f"link: {result3.browser_url()}\n")
    except TradeError as exc:
        print(f"BLAD wyszukiwania Waystone'a PoE2: {exc}\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
