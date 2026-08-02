"""Reguly wyliczania pseudo-modow, czyli sum typu "65% total Elemental Resistance".

Trade pozwala szukac po sumach zamiast po pojedynczych modach. Dla rzadkiego
przedmiotu to zwykle duzo sensowniejsze: kupujacego interesuje laczna odpornosc,
a nie to, czy siedzi w jednym modzie czy w trzech.

Klucze to skanonizowane wzorce modow (male litery, liczby zamienione na '#'),
takie same jak w indeksie statystyk. ID pochodza z /api/trade/data/stats.
"""

FIRE = "pseudo.pseudo_total_fire_resistance"
COLD = "pseudo.pseudo_total_cold_resistance"
LIGHTNING = "pseudo.pseudo_total_lightning_resistance"
CHAOS = "pseudo.pseudo_total_chaos_resistance"
ELEMENTAL = "pseudo.pseudo_total_elemental_resistance"
ANY_RES = "pseudo.pseudo_total_resistance"

STRENGTH = "pseudo.pseudo_total_strength"
DEXTERITY = "pseudo.pseudo_total_dexterity"
INTELLIGENCE = "pseudo.pseudo_total_intelligence"
ALL_ATTRIBUTES = "pseudo.pseudo_total_all_attributes"

LIFE = "pseudo.pseudo_total_life"
MANA = "pseudo.pseudo_total_mana"
ENERGY_SHIELD = "pseudo.pseudo_total_energy_shield"

# wzorzec moda -> ile wnosi do ktorej sumy
# Mod dwuzywiolowy ("Fire and Cold") daje pelna wartosc kazdemu z zywiolow
# osobno, wiec do sumy zywiolowej wchodzi podwojnie.
RULES: dict[str, tuple[tuple[str, float], ...]] = {
    "#% to fire resistance": ((FIRE, 1), (ELEMENTAL, 1), (ANY_RES, 1)),
    "#% to cold resistance": ((COLD, 1), (ELEMENTAL, 1), (ANY_RES, 1)),
    "#% to lightning resistance": ((LIGHTNING, 1), (ELEMENTAL, 1), (ANY_RES, 1)),
    "#% to chaos resistance": ((CHAOS, 1), (ANY_RES, 1)),

    "#% to fire and cold resistances": ((FIRE, 1), (COLD, 1), (ELEMENTAL, 2), (ANY_RES, 2)),
    "#% to fire and lightning resistances": ((FIRE, 1), (LIGHTNING, 1), (ELEMENTAL, 2), (ANY_RES, 2)),
    "#% to cold and lightning resistances": ((COLD, 1), (LIGHTNING, 1), (ELEMENTAL, 2), (ANY_RES, 2)),
    "#% to fire and chaos resistances": ((FIRE, 1), (CHAOS, 1), (ELEMENTAL, 1), (ANY_RES, 2)),
    "#% to cold and chaos resistances": ((COLD, 1), (CHAOS, 1), (ELEMENTAL, 1), (ANY_RES, 2)),
    "#% to lightning and chaos resistances": ((LIGHTNING, 1), (CHAOS, 1), (ELEMENTAL, 1), (ANY_RES, 2)),

    "#% to all elemental resistances": (
        (FIRE, 1), (COLD, 1), (LIGHTNING, 1), (ELEMENTAL, 3), (ANY_RES, 3),
    ),

    "# to strength": ((STRENGTH, 1),),
    "# to dexterity": ((DEXTERITY, 1),),
    "# to intelligence": ((INTELLIGENCE, 1),),
    "# to strength and dexterity": ((STRENGTH, 1), (DEXTERITY, 1)),
    "# to strength and intelligence": ((STRENGTH, 1), (INTELLIGENCE, 1)),
    "# to dexterity and intelligence": ((DEXTERITY, 1), (INTELLIGENCE, 1)),
    "# to all attributes": (
        (STRENGTH, 1), (DEXTERITY, 1), (INTELLIGENCE, 1), (ALL_ATTRIBUTES, 1),
    ),

    "# to maximum life": ((LIFE, 1),),
    "# to maximum mana": ((MANA, 1),),
    "# to maximum energy shield": ((ENERGY_SHIELD, 1),),
}

# Sumy skladajace sie z jednego skladnika nie wnosza nic ponad sam mod - nie ma
# sensu zasmiecac nimi listy. Pokazujemy je dopiero, gdy zrodel jest wiecej.
ONLY_IF_COMBINED = frozenset({
    FIRE, COLD, LIGHTNING, CHAOS, STRENGTH, DEXTERITY, INTELLIGENCE,
    LIFE, MANA, ENERGY_SHIELD, ALL_ATTRIBUTES,
})
