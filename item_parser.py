"""Parser tekstu przedmiotu skopiowanego z Path of Exile 1 (Ctrl+C nad itemem).

Format schowka PoE1 to sekcje rozdzielone linia '--------'. Pierwsza sekcja to
naglowek (klasa, rzadkosc, nazwa, baza), kolejne to wlasciwosci, wymagania,
implicity, explicity i flagi.
"""

import re
from dataclasses import dataclass, field

from i18n import t

# Sekcje rozdziela linia "--------". Dopuszczamy warianty, bo autokorekta
# Google Docs potrafi zamienic ciag myslnikow na pauze.
SEP_RE = re.compile(r"^[ \t]*(?:-{3,}|—+|–+)[ \t]*$", re.MULTILINE)

# Liczba w tekscie moda: +12, -3, 25, 1.20
NUM_RE = re.compile(r"[+-]?\d+(?:\.\d+)?")

# Linia typu "Quality: +20% (augmented)" - wlasciwosc, nie mod.
# Nawiasy w nazwie sa konieczne dla "Quality (Attack Modifiers): 20%" na bizuterii -
# bez nich taka linia lecial do modow i byla tam kaleczona.
PROPERTY_RE = re.compile(r"^([A-Za-z][A-Za-z '/()]*):\s*(.*)$")

# Przy wlaczonych rozszerzonych opisach modyfikatorow PoE poprzedza kazdy mod
# linia w klamrach, np.  { Prefix Modifier "Gentian" (Tier: 6) - Mana }
MOD_ANNOTATION_RE = re.compile(r"^\{.*\}$")

# ...i dopisuje do wartosci zakres tieru:  +50(50-54) to maximum Mana
ROLL_RANGE_RE = re.compile(
    r"\(\s*([+-]?\d+(?:\.\d+)?)\s*(?:-\s*([+-]?\d+(?:\.\d+)?)\s*)?\)"
)

# Znacznik wariantu doklejany przez gre do tekstu moda, np.
#   "+3 to Level of all Summon Carrion Golem(Fireball-Mana-Infused Staff) Gems"
# UWAGA: nie usuwamy tego przy parsowaniu. GGG ma 104 wpisy z takim nawiasem
# ("(Local)", "(Shields)"), wiec ciecie w ciemno psuloby ich dopasowanie.
# Matcher probuje najpierw tekstu z nawiasem, a dopiero potem bez.
QUALIFIER_RE = re.compile(r"\s*\((?=[^)]*[A-Za-z])(?![^)]*\d)[^)]*\)")

# Slowo w adnotacji -> rodzaj moda. Kolejnosc ma znaczenie: "Crafted Prefix
# Modifier" musi trafic na 'crafted', zanim zlapie go domyslny explicit.
ANNOTATION_KINDS = (
    ("implicit", "implicit"),
    ("enchant", "enchant"),
    ("crafted", "crafted"),
    ("fractured", "fractured"),
    ("scourge", "scourge"),
    ("veiled", "veiled"),
    ("crucible", "crucible"),
)

RARITIES = {
    "Normal", "Magic", "Rare", "Unique", "Gem", "Currency",
    "Divination Card", "Quest Item",
}

# Sufiksy okreslajace typ moda. Kolejnosc ma znaczenie tylko dla czytelnosci.
MOD_SUFFIXES = {
    # "(Hidden)" oznacza mod pokazywany tylko w opisie - trade go nie indeksuje,
    # wiec nie wolno go uzywac jako filtru. Bez tego unikat z takim modem
    # zwracal zero ofert.
    "(Hidden)": "hidden",
    "(enchant)": "enchant",
    "(implicit)": "implicit",
    "(crafted)": "crafted",
    "(fractured)": "fractured",
    "(scourge)": "scourge",
    "(crucible)": "crucible",
    "(veiled)": "veiled",
}

INFLUENCES = {
    "Shaper Item": "shaper",
    "Elder Item": "elder",
    "Crusader Item": "crusader",
    "Redeemer Item": "redeemer",
    "Hunter Item": "hunter",
    "Warlord Item": "warlord",
}

# Linie-flagi stojace samodzielnie w sekcji. Nazwy po prawej to identyfikatory
# z /api/trade/data/filters (grupa misc_filters) - musza byc DOKLADNIE takie,
# inaczej filtr milczaco nic nie robi (API nie zglasza bledu na nieznany klucz,
# po prostu go ignoruje). "veiled_item" ponizej bylo taka pomylka - prawdziwy
# identyfikator to "veiled", sprawdzone bezposrednio w API.
STANDALONE_FLAGS = {
    "Corrupted": "corrupted",
    "Mirrored": "mirrored",
    "Unidentified": "unidentified",
    "Split": "split",
    "Synthesised Item": "synthesised",
    "Fractured Item": "fractured_item",
    "Veiled Item": "veiled",
    # Implanty eldrycze (Wykuwacz/Wchłaniacz) - tekst linii niepotwierdzony
    # na zywym przedmiocie (nie mamy jak przetestowac), ale identyfikatory
    # API (searing_item/tangled_item) sa pewne, a bledny tekst po lewej
    # po prostu nigdy sie nie dopasuje - bezpieczny blad, nie fal.
    "Searing Exarch Item": "searing_item",
    "Eater of Worlds Item": "tangled_item",
}


@dataclass
class Mod:
    """Pojedynczy modyfikator przedmiotu."""

    text: str  # oryginalna linia, np. "+45% to Fire Resistance"
    kind: str  # explicit / implicit / enchant / crafted / fractured / ...
    pattern: str  # tekst z liczbami zamienionymi na '#'
    values: list[float] = field(default_factory=list)  # faktyczne rolki
    ranges: list[tuple[float, float]] = field(default_factory=list)  # zakresy tieru
    affix: str = ""  # P / S / I  (prefix, sufiks, implicit)
    tier: int | None = None  # numer tieru z adnotacji
    group: str = ""  # nazwa afiksu, np. "Gentian"
    annotated: bool = False  # czy poprzedzala go adnotacja w klamrach

    def badge(self) -> str:
        """Krotka etykieta do wyswietlenia, np. 'P6', 'S4', 'I'."""
        if not self.affix:
            return ""
        return f"{self.affix}{self.tier}" if self.tier is not None else self.affix


@dataclass
class ParsedItem:
    rarity: str = ""
    item_class: str = ""
    name: str = ""  # nazwa unikatu / rzadkiego, pusta dla zwyklych
    base_type: str = ""  # baza, np. "Simple Robe"
    mods: list[Mod] = field(default_factory=list)
    item_level: int | None = None
    quality: int | None = None
    gem_level: int | None = None
    map_tier: int | None = None
    sockets: str = ""
    influences: list[str] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)
    seller_note: str = ""
    raw: str = ""
    # Wlasciwosci broni - do wyliczenia DPS. Puste dla wszystkiego innego.
    physical_damage: tuple[float, float] | None = None
    elemental_damage: list[tuple[str, float, float]] = field(default_factory=list)
    attacks_per_second: float | None = None
    critical_chance: float | None = None
    # Obrona pancerza/tarczy - jak DPS, glowny czynnik ceny dla tej kategorii.
    armour: int | None = None
    evasion: int | None = None
    energy_shield: int | None = None
    ward: int | None = None
    block_chance: int | None = None
    # Wlasciwosci mapy - obok Map Tier decyduja o cenie.
    item_quantity: int | None = None
    item_rarity: int | None = None
    monster_pack_size: int | None = None
    area_level: int | None = None
    # Zajete gniazda afiksow. Liczymy adnotacje w klamrach, nie linie tekstu -
    # mod hybrydowy zajmuje jedno gniazdo, a zajmuje dwie linie.
    prefix_count: int = 0
    suffix_count: int = 0
    affix_info: bool = False  # czy w ogole mamy rozszerzone opisy modow

    @property
    def is_unique(self) -> bool:
        return self.rarity == "Unique"

    @property
    def is_rare(self) -> bool:
        return self.rarity == "Rare"

    @property
    def is_gem(self) -> bool:
        return self.rarity == "Gem"

    @property
    def corrupted(self) -> bool:
        return "corrupted" in self.flags

    @property
    def is_foulborn(self) -> bool:
        """Odmiana Foulborn - gielda ma na nia osobny filtr 'mutated'."""
        return "foulborn" in self.flags

    @property
    def link_count(self) -> int:
        """Najdluzszy link w socketach, np. 'W-W-W-W-W-W' -> 6."""
        if not self.sockets:
            return 0
        return max(len(group.split("-")) for group in self.sockets.split(" "))

    @property
    def max_prefixes(self) -> int:
        if self.rarity == "Magic":
            return 1
        if self.rarity != "Rare":
            return 0
        # Klejnoty maja ciasniejsze limity niz reszta ekwipunku.
        return 2 if "Jewel" in self.item_class else 3

    @property
    def max_suffixes(self) -> int:
        return self.max_prefixes

    @property
    def open_prefixes(self) -> int:
        return max(0, self.max_prefixes - self.prefix_count)

    @property
    def open_suffixes(self) -> int:
        return max(0, self.max_suffixes - self.suffix_count)

    @property
    def can_be_modified(self) -> bool:
        """Czy zostalo wolne gniazdo i czy przedmiot w ogole da sie jeszcze ruszyc."""
        if self.corrupted or "mirrored" in self.flags:
            return False
        return bool(self.open_prefixes or self.open_suffixes)

    @property
    def physical_dps(self) -> float | None:
        """Sredni obrazenia fizyczne * ataki/s. None, gdy brak ktoregos skladnika."""
        if self.physical_damage is None or not self.attacks_per_second:
            return None
        low, high = self.physical_damage
        return (low + high) / 2 * self.attacks_per_second

    @property
    def elemental_dps(self) -> float | None:
        """Suma srednich wszystkich zywiolow * ataki/s (tak jak liczy to trade)."""
        if not self.elemental_damage or not self.attacks_per_second:
            return None
        total_avg = sum((low + high) / 2 for _, low, high in self.elemental_damage)
        return total_avg * self.attacks_per_second

    @property
    def total_dps(self) -> float | None:
        """pDPS + eDPS. None, gdy bron nie ma zadnego zrodla obrazen (np. tylko chaos)."""
        parts = [v for v in (self.physical_dps, self.elemental_dps) if v is not None]
        return sum(parts) if parts else None

    def craft_summary(self) -> str:
        """Jednolinijkowy opis stanu afiksow. Pusty, gdy nie ma na czym oprzec."""
        if not self.affix_info or self.max_prefixes == 0:
            return ""
        if self.corrupted:
            return t("craft.corrupted")
        if "mirrored" in self.flags:
            return t("craft.mirrored")

        slots = (f"{self.prefix_count}/{self.max_prefixes} {t('craft.prefixes')}, "
                 f"{self.suffix_count}/{self.max_suffixes} {t('craft.suffixes')}")
        if not self.can_be_modified:
            return f"{t('craft.full')}  ·  {slots}"

        # Zapis "2x prefiks" zamiast odmiany - liczba mnoga rzadzi sie w kazdym
        # jezyku inaczej, a mnoznik jest zrozumialy wszedzie.
        free = []
        if self.open_prefixes:
            free.append(f"{self.open_prefixes}× {t('craft.prefix')}")
        if self.open_suffixes:
            free.append(f"{self.open_suffixes}× {t('craft.suffix')}")
        return f"{t('craft.can_modify')} - {t('craft.free')}: {', '.join(free)}  ·  {slots}"

    def display_name(self) -> str:
        if self.name and self.base_type:
            return f"{self.name} ({self.base_type})"
        return self.name or self.base_type or "?"


def normalize(text: str) -> tuple[str, list[float]]:
    """Zamienia liczby na '#' i zwraca (wzorzec, lista liczb).

    "+45% to Fire Resistance" -> ("+#% to Fire Resistance", [45.0])
    """
    values: list[float] = []

    def _sub(match: re.Match[str]) -> str:
        values.append(float(match.group(0)))
        return "#"

    return NUM_RE.sub(_sub, text), values


def _strip_augmented(value: str) -> str:
    """Usuwa znaczniki '(augmented)' / '(unmet)' z wartosci wlasciwosci."""
    return re.sub(r"\s*\((?:augmented|unmet)\)\s*$", "", value).strip()


def _first_int(value: str) -> int | None:
    match = NUM_RE.search(value)
    return int(float(match.group(0))) if match else None


def _first_float(value: str) -> float | None:
    match = NUM_RE.search(value)
    return float(match.group(0)) if match else None


DAMAGE_RANGE_RE = re.compile(r"(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)")
ELEMENTAL_PART_RE = re.compile(
    r"(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\s*\((fire|cold|lightning)\)", re.IGNORECASE
)


def _parse_damage_range(value: str) -> tuple[float, float] | None:
    """'10-20 (augmented)' -> (10.0, 20.0). '(augmented)' moze siedziec przed
    zakresem tak samo jak po nim, wiec usuwamy go zamiast liczyc na koniec linii."""
    value = re.sub(r"\(augmented\)", "", value, flags=re.IGNORECASE)
    match = DAMAGE_RANGE_RE.search(value)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def _parse_elemental_damage(value: str) -> list[tuple[str, float, float]]:
    """'10-20 (augmented) (fire), 1-40 (cold)' -> [("fire", 10, 20), ("cold", 1, 40)].

    Kazdy zywiol to osobny skladnik pola po przecinku - w odroznieniu od
    Physical Damage nie da sie tu wziac po prostu pierwszego zakresu w linii.
    """
    parts: list[tuple[str, float, float]] = []
    for chunk in value.split(","):
        chunk = re.sub(r"\(augmented\)", "", chunk, flags=re.IGNORECASE)
        match = ELEMENTAL_PART_RE.search(chunk)
        if match:
            parts.append((match.group(3).lower(), float(match.group(1)), float(match.group(2))))
    return parts


class ItemParseError(ValueError):
    """Tekstu nie da sie zrozumiec jako przedmiotu z PoE.

    Atrybut kind rozroznia sytuacje, ktore wygladaja tak samo w oknie, a
    znacza cos zupelnie innego dla nas: "ktos wcisnal skrot nie nad
    przedmiotem" to zachowanie uzytkownika, a "tekst wyglada na przedmiot,
    ale nie ma rzadkosci" to juz nasza luka w parserze. Bez tego podzialu
    93% wszystkich bledow siedzialo w jednym worku, z ktorego nic nie
    wynikalo.
    """

    def __init__(self, message: str, kind: str = "tekst_przedmiotu") -> None:
        super().__init__(message)
        self.kind = kind


def parse_item(raw: str) -> ParsedItem:
    """Parsuje surowy tekst ze schowka na ParsedItem."""
    raw = raw.replace("\r\n", "\n").strip()
    if not raw:
        raise ItemParseError("Pusty tekst przedmiotu.", kind="tekst_pusty")

    sections = [
        [line.strip() for line in block.split("\n") if line.strip()]
        for block in SEP_RE.split(raw)
    ]
    sections = [s for s in sections if s]
    if not sections:
        raise ItemParseError("Brak sekcji w tekscie przedmiotu.",
                             kind="tekst_bez_sekcji")

    item = ParsedItem(raw=raw)
    _parse_header(sections[0], item)
    for section in sections[1:]:
        _parse_section(section, item)
    return item


def _parse_header(lines: list[str], item: ParsedItem) -> None:
    """Naglowek: Item Class, Rarity, potem nazwa i/lub baza."""
    remaining: list[str] = []
    for line in lines:
        match = PROPERTY_RE.match(line)
        if match and match.group(1) == "Item Class":
            item.item_class = match.group(2).strip()
        elif match and match.group(1) == "Rarity":
            item.rarity = match.group(2).strip()
        else:
            remaining.append(line)

    if not item.rarity:
        # Rozroznienie kosztuje jedna linijke, a oszczedza zgadywania:
        # tekst z naglowkiem "Item Class:" albo z separatorem sekcji NA PEWNO
        # wyszedl z PoE, wiec brak rzadkosci jest luka po naszej stronie.
        # Tekst bez zadnego z tych znakow to po prostu cos innego - stara
        # zawartosc dokumentu albo skrot wcisniety nie nad przedmiotem.
        z_poe = "Item Class:" in item.raw or SEP_RE.search(item.raw) is not None
        raise ItemParseError(
            "Brak linii 'Rarity:' - to chyba nie jest tekst przedmiotu z PoE.",
            kind="przedmiot_bez_rzadkosci" if z_poe else "nie_przedmiot",
        )
    if item.rarity not in RARITIES:
        # Nowe klasy przedmiotow trafiaja tu zanim dopiszemy je do RARITIES;
        # nie przerywamy, tylko idziemy dalej z tym co jest.
        pass

    if len(remaining) >= 2:
        # Unique / Rare: linia nazwy + linia bazy.
        item.name, item.base_type = remaining[0], remaining[1]
    elif remaining:
        # Normal / Magic / Currency / Gem / Divination Card: sama nazwa.
        item.base_type = remaining[0]

    # Magic ma prefixy i sufiksy wtopione w nazwe bazy; zdejmujemy "of ..."
    # i wiodacy przymiotnik dopiero w trade_api, bo tam mamy liste baz.
    for prefix in ("Superior ", "Synthesised ", "Fractured "):
        if item.base_type.startswith(prefix):
            item.base_type = item.base_type[len(prefix):]

    # "Foulborn" dokleja sie do NAZWY, nie do bazy: unikat "Shackles of the
    # Wretched" nazywa sie wtedy "Foulborn Shackles of the Wretched".
    # Trade nie zna takiej nazwy i odpowiada bledem 400 "Unknown item name",
    # wiec bez zdjecia prefiksu wyszukiwanie w ogole nie rusza. Sam fakt
    # zapamietujemy jako flage - jest na to osobny filtr gieldy.
    if item.name.startswith(FOULBORN_PREFIX):
        item.name = item.name[len(FOULBORN_PREFIX):]
        item.flags.add("foulborn")


FOULBORN_PREFIX = "Foulborn "

TIER_RE = re.compile(r"Tier:\s*(\d+)", re.IGNORECASE)
GROUP_RE = re.compile(r'"([^"]+)"')


def _kind_from_annotation(line: str) -> str:
    """Wyciaga rodzaj moda z linii typu '{ Prefix Modifier "Gentian" ... }'."""
    lowered = line.lower()
    for needle, kind in ANNOTATION_KINDS:
        if needle in lowered:
            return kind
    return "explicit"  # Prefix / Suffix / Unique Modifier


def _affix_from_annotation(line: str) -> tuple[str, int | None, str]:
    """Zwraca (litera afiksu, tier, nazwa grupy) z adnotacji w klamrach."""
    lowered = line.lower()
    if "prefix" in lowered:
        affix = "P"
    elif "suffix" in lowered:
        affix = "S"
    elif "implicit" in lowered:
        affix = "I"
    elif "enchant" in lowered:
        affix = "E"
    else:
        affix = ""

    tier_match = TIER_RE.search(line)
    group_match = GROUP_RE.search(line)
    return (
        affix,
        int(tier_match.group(1)) if tier_match else None,
        group_match.group(1) if group_match else "",
    )


def _parse_section(lines: list[str], item: ParsedItem) -> None:
    # Sekcja wymagan tez zawiera "Level:", ale to poziom postaci, nie kamienia.
    in_requirements = any(line.rstrip(":") == "Requirements" for line in lines)
    # Rodzaj narzucony przez ostatnia adnotacje w klamrach. Obowiazuje az do
    # nastepnej adnotacji, bo jeden mod potrafi zajac dwie linie.
    annotated_kind: str | None = None
    annotated_affix, annotated_tier, annotated_group = "", None, ""

    for line in lines:
        if MOD_ANNOTATION_RE.match(line):
            annotated_kind = _kind_from_annotation(line)
            annotated_affix, annotated_tier, annotated_group = _affix_from_annotation(line)
            # Jedna adnotacja = jedno gniazdo, nawet gdy mod zajmuje dwie linie.
            if annotated_affix == "P":
                item.prefix_count += 1
                item.affix_info = True
            elif annotated_affix == "S":
                item.suffix_count += 1
                item.affix_info = True
            elif annotated_affix:
                item.affix_info = True
            continue  # sama adnotacja nie jest modem
        if line in STANDALONE_FLAGS:
            item.flags.add(STANDALONE_FLAGS[line])
            continue
        if line in INFLUENCES:
            item.influences.append(INFLUENCES[line])
            continue

        kind: str | None = None
        text = line
        for suffix, mod_kind in MOD_SUFFIXES.items():
            if text.endswith(" " + suffix):
                kind = mod_kind
                text = text[: -len(suffix)].strip()
                break
        else:
            # Bez sufiksu moda - moze to byc wlasciwosc "Nazwa: wartosc".
            match = PROPERTY_RE.match(line)
            if match and _handle_property(
                match.group(1), match.group(2), item, in_requirements
            ):
                continue

        # Sufiks w rodzaju "(enchant)" jest rownie dobrym dowodem, ze to prawdziwy
        # mod, co adnotacja w klamrach - enchanty klejnotow klastrowych maja
        # wlasnie sufiks i bez tego wypadaly z wyszukiwania.
        from_suffix = kind is not None
        if kind is None:
            kind = annotated_kind or "explicit"

        # "+50(50-54) to maximum Mana" -> tekst "+50 to maximum Mana" + zakres (50, 54).
        # Zakres tieru jest cenniejszy od samej rolki: pozwala szukac przedmiotow
        # z tym samym modem na tym samym poziomie, a nie tylko lepiej dorzuconych.
        ranges = [
            (float(low), float(high) if high else float(low))
            for low, high in ROLL_RANGE_RE.findall(text)
        ]
        text = ROLL_RANGE_RE.sub("", text).strip()

        pattern, values = normalize(text)
        item.mods.append(Mod(
            text=text, kind=kind, pattern=pattern, values=values, ranges=ranges,
            affix=annotated_affix, tier=annotated_tier, group=annotated_group,
            annotated=from_suffix or annotated_kind is not None,
        ))


def _handle_property(
    key: str, value: str, item: ParsedItem, in_requirements: bool = False
) -> bool:
    """Zapisuje znana wlasciwosc. Zwraca True jesli linia zostala zuzyta."""
    value = _strip_augmented(value)
    if key == "Item Level":
        item.item_level = _first_int(value)
    elif key == "Quality":
        item.quality = _first_int(value)
    elif key == "Level":
        # Tylko kamienie maja poziom w sensie handlowym; w sekcji wymagan
        # "Level" to poziom postaci i musi zostac zignorowany.
        if not in_requirements and item.is_gem and item.gem_level is None:
            item.gem_level = _first_int(value)
    elif key == "Map Tier":
        item.map_tier = _first_int(value)
    elif key == "Sockets":
        item.sockets = value
    elif key == "Note":
        item.seller_note = value
    elif key == "Physical Damage":
        item.physical_damage = _parse_damage_range(value)
    elif key == "Elemental Damage":
        item.elemental_damage = _parse_elemental_damage(value)
    elif key == "Attacks per Second":
        item.attacks_per_second = _first_float(value)
    elif key == "Critical Strike Chance":
        item.critical_chance = _first_float(value)
    elif key == "Armour":
        item.armour = _first_int(value)
    elif key == "Evasion Rating":
        item.evasion = _first_int(value)
    elif key == "Energy Shield":
        item.energy_shield = _first_int(value)
    elif key == "Ward":
        item.ward = _first_int(value)
    elif key in ("Block chance", "Chance to Block"):
        item.block_chance = _first_int(value)
    elif key == "Item Quantity":
        item.item_quantity = _first_int(value)
    elif key == "Item Rarity":
        item.item_rarity = _first_int(value)
    elif key == "Monster Pack Size":
        item.monster_pack_size = _first_int(value)
    elif key == "Area Level":
        item.area_level = _first_int(value)
    elif key in (
        "Requirements", "Requires", "Str", "Dex", "Int",
        "Chaos Damage", "Weapon Range",
        "Stack Size",
        "Quality (Attack Modifiers)", "Quality (Defence Modifiers)",
        "Quality (Life and Mana Modifiers)", "Quality (Resistance Modifiers)",
        "Radius", "Limited to", "Talisman Tier", "Experience",
    ):
        pass  # znana wlasciwosc, ktorej nie uzywamy w zapytaniu
    else:
        return False  # nieznane - potraktuj jako mod
    return True
