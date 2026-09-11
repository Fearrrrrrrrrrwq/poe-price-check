"""Dopasowanie tekstu moda do ID statystyki trade na DANYCH Z GRY.

Stary silnik (trade_api._find_stat) porownuje tekst przedmiotu z opisami z
/api/trade/data/stats i zgaduje heurystykami: kanonizacja, "luzny indeks",
sklejanie linii, zamiana reduced->increased. Tu korzystamy z gotowej mapy
"kazdy wariant tekstu, jaki gra potrafi wypisac -> ID statystyki w trade, osobno
dla explicit/implicit/fractured/...", wyciagnietej z plikow gry.

Zrodlo danych (licencja MIT, patrz data/LICENSE-awakened-poe-trade.txt):
  PoE1: Awakened PoE Trade  - github.com/SnosMe/awakened-poe-trade
  PoE2: Exiled Exchange 2   - github.com/Kvan7/Exiled-Exchange-2
Plik stats.ndjson: jedna statystyka na linie, np.
  {"ref": "+#% to Chaos Resistance",
   "matchers": [{"string": "#% to Chaos Resistance"}],
   "trade": {"ids": {"explicit": ["explicit.stat_2923486259"],
                     "implicit": ["implicit.stat_2923486259"], ...}}}
oraz grupy {"resolve": {...}, "stats": [...]} dla tekstow, ktore znacza co
innego zaleznie od przedmiotu (lokalne ES na pancerzu vs globalne na pierscieniu).

Algorytm dopasowania odwzorowuje renderer/src/parser/stat-translations.ts z APT.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests

from paths import resource_path

DATA_URLS = {
    "poe1": "https://raw.githubusercontent.com/SnosMe/awakened-poe-trade/master/"
            "renderer/public/data/en/stats.ndjson",
    "poe2": "https://raw.githubusercontent.com/Kvan7/Exiled-Exchange-2/master/"
            "renderer/public/data/en/stats.ndjson",
}
# Dane zmieniaja sie z liga (nowe mody), ale nie z dnia na dzien.
DATA_TTL_SECONDS = 3 * 24 * 3600

# Liczba w tekscie moda. Nie lapiemy cyfr sklejonych z poprzedzajaca cyfra albo
# nawiasem - to czesc innej liczby / zakresu.
NUMBER_RE = re.compile(r"(?<![\d)])[+-]?\d+(?:\.\d+)?")

# Ktore liczby zostawic doslownie, a ktore zamienic na '#'. Najpierw probujemy
# najbardziej doslownych wariantow: "#% increased Damage per 100 Intelligence"
# ma w danych "100" wpisane na sztywno, wiec wariant z doslownym "100" trafia
# pierwszy. Kopia tabeli PLACEHOLDER_MAP z APT.
PLACEHOLDER_MAP = (
    ((),),
    ((0,), ()),
    ((0, 1), (0,), (1,), ()),
    ((0, 1, 2), (1, 2), (0, 2), (0, 1), (2,), (1,), (0,)),
    ((0, 1, 2, 3), (1, 2, 3), (0, 2, 3), (0, 1, 3), (0, 1, 2), (2, 3), (1, 3),
     (1, 2), (0, 3), (0, 2), (0, 1)),
)

# Linia moda moze zajac najwyzej tyle linii tekstu (w danych najdluzsze maja 3).
MAX_STAT_LINES = 4


@dataclass
class GameStatHit:
    """Wynik dopasowania: ID statystyki w trade + wartosci do filtra."""

    trade_ids: list[str]  # zwykle jedno; kilka, gdy tekst jest nierozroznialny
    values: list[float]
    consumed: int  # ile kolejnych linii modow zuzyto
    negated: bool = False
    ref: str = ""
    better: int = 1  # 1: wiecej = lepiej, -1: mniej = lepiej


@dataclass
class _Stat:
    ref: str
    better: int
    matchers: list[dict]
    ids: dict[str, list[str]]
    inverted: bool = False


@dataclass
class _Group:
    strat: str
    stats: list[_Stat]
    test: list = field(default_factory=list)
    kind: list = field(default_factory=list)


def _stat_from_json(data: dict) -> _Stat:
    trade = data.get("trade") or {}
    return _Stat(
        ref=data.get("ref", ""),
        better=int(data.get("better", 1) or 1),
        matchers=data.get("matchers") or [],
        ids={k: list(v) for k, v in (trade.get("ids") or {}).items()},
        inverted=bool(trade.get("inverted")),
    )


class GameStats:
    """Indeks "tekst moda (z '#' w miejscu liczb) -> statystyka albo grupa"."""

    def __init__(self, lines: list[str]) -> None:
        self._by_str: dict[str, _Stat | _Group] = {}
        for raw in lines:
            raw = raw.strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except ValueError:
                continue
            if "resolve" in data:
                resolve = data["resolve"] or {}
                entry: _Stat | _Group = _Group(
                    strat=resolve.get("strat", ""),
                    stats=[_stat_from_json(s) for s in data.get("stats") or []],
                    test=list(resolve.get("test") or []),
                    kind=list(resolve.get("kind") or []),
                )
                strings = {m.get(key) for s in entry.stats for m in s.matchers
                           for key in ("string", "advanced")}
            else:
                entry = _stat_from_json(data)
                strings = {m.get(key) for m in entry.matchers
                           for key in ("string", "advanced")}
            for text in strings:
                if text:
                    # Pierwszy wpis wygrywa - tak samo jak mapa w APT.
                    self._by_str.setdefault(text, entry)

    def __len__(self) -> int:
        return len(self._by_str)

    # ------------------------------------------------------------ dopasowanie

    def match(self, lines: list[str], kind: str, category: str | None) -> GameStatHit | None:
        """Probuje dopasowac poczatek listy linii (1..MAX_STAT_LINES linii).

        Jak w APT: najpierw pojedyncza linia, dopiero gdy ta nic nie da -
        coraz dluzsze sklejenia. Zwraca None, gdy nic nie pasuje dla tego
        rodzaju moda (np. tekst istnieje tylko jako enchant, a mod jest
        explicitem).
        """
        for end in range(1, min(MAX_STAT_LINES, len(lines)) + 1):
            text = "\n".join(lines[:end])
            hit = self._match_text(text, kind, category)
            if hit:
                hit.consumed = end
                return hit
        return None

    def _match_text(self, text: str, kind: str, category: str | None) -> GameStatHit | None:
        numbers = [(m.group(0), m.start(), m.end()) for m in NUMBER_RE.finditer(text)]
        combos = PLACEHOLDER_MAP[len(numbers)] if len(numbers) < len(PLACEHOLDER_MAP) else ()
        for literal in combos:
            parts, last, values = [], 0, []
            for idx, (num, start, end) in enumerate(numbers):
                parts.append(text[last:start])
                if idx in literal:
                    parts.append(num)
                else:
                    parts.append("#")
                    values.append(float(num))
                last = end
            parts.append(text[last:])
            hit = self._lookup("".join(parts), values, kind, category)
            if hit:
                return hit
        # Ostatnia deska: tekst doslownie, bez zadnych '#'.
        return self._lookup(text, [], kind, category)

    def _lookup(self, match_str: str, values: list[float], kind: str,
                category: str | None) -> GameStatHit | None:
        entry = self._by_str.get(match_str)
        if entry is None:
            return None
        stat, extra_ids = (entry, []) if isinstance(entry, _Stat) else \
            self._resolve(entry, match_str, kind, category, values)
        if stat is None:
            return None
        ids = list(stat.ids.get(kind) or [])
        # PoE2: kilka ID pod jednym tekstem ("# to Spirit" -> 3981240776 i
        # 2704225257). Najpierw to, ktore statystyka ma w najwiekszej liczbie
        # grup (implicit/crafted/enchant...) - to wariant ogolny; waski wariant
        # (np. tylko na berlach) zostaje alternatywa. Rozstrzygniecie lokalny/
        # globalny po "(Local)" robi dalej trade_api.
        if len(ids) > 1:
            suffix_count: dict[str, int] = {}
            for kind_ids in stat.ids.values():
                for sid in kind_ids:
                    num = sid.split(".", 1)[-1]
                    suffix_count[num] = suffix_count.get(num, 0) + 1
            ids.sort(key=lambda sid: -suffix_count.get(sid.split(".", 1)[-1], 0))
        for extra in extra_ids:
            if extra not in ids:
                ids.append(extra)
        if not ids:
            return None
        matcher = next((m for m in stat.matchers
                        if m.get("string") == match_str or m.get("advanced") == match_str), None)
        if matcher is None:
            return None
        negated = bool(matcher.get("negate"))
        vals = [-v for v in values] if negated else list(values)
        if not vals and matcher.get("value") is not None:
            vals = [float(matcher["value"])]
        if stat.inverted:
            vals = [-v for v in vals]
        return GameStatHit(trade_ids=ids, values=vals, consumed=1,
                           negated=negated, ref=stat.ref, better=stat.better)

    @staticmethod
    def _resolve(group: _Group, match_str: str, kind: str, category: str | None,
                 values: list[float]) -> tuple[_Stat | None, list[str]]:
        """Grupy tekstow o wielu znaczeniach - te same strategie co APT."""
        if group.strat == "select":
            # "select": wybor po kategorii przedmiotu, np. [None, "ARMOUR"] -
            # na pancerzu wariant lokalny, gdzie indziej domyslny (None).
            idx = next((i for i, expected in enumerate(group.test)
                        if expected is not None and category == expected), -1)
            if idx == -1:
                idx = group.test.index(None) if None in group.test else -1
            return (group.stats[idx] if 0 <= idx < len(group.stats) else None), []

        on_trade = [s for s in group.stats if kind in s.ids]
        if len(on_trade) == 1:
            return on_trade[0], []

        def has_str(s: _Stat) -> bool:
            return any(m.get("string") == match_str or m.get("advanced") == match_str
                       for m in s.matchers)

        if group.strat == "trivial-merge":
            # Ten sam tekst, kilka ID - z tekstu przedmiotu nie da sie ich
            # rozroznic. Zwracamy pierwszy + reszte jako alternatywy.
            candidates = [s for s in on_trade if has_str(s)]
            if not candidates:
                return None, []
            extra = [i for s in candidates[1:] for i in s.ids.get(kind, [])]
            return candidates[0], extra
        if group.strat == "percent-merge" and "percent" in group.kind and "value" in group.kind:
            # "Instant Recovery" = "100% of Recovery applied Instantly": gra
            # wypisuje ten sam efekt jako flage albo procent. Przy 100% trade
            # indeksuje przedmiot pod FLAGA - ta idzie pierwsza, procent jako
            # alternatywa.
            pct = group.stats[group.kind.index("percent")]
            other = group.stats[group.kind.index("value")]
            matcher = next((m for m in pct.matchers
                            if m.get("string") == match_str or m.get("advanced") == match_str), None)
            if matcher is not None and matcher.get("value") == 100 and kind in other.ids:
                return other, list(pct.ids.get(kind, []))
            return next((s for s in group.stats if has_str(s) and kind in s.ids), None), []
        if group.strat in ("percent-merge", "flag-merge"):
            return next((s for s in group.stats if has_str(s) and kind in s.ids), None), []
        return None, []


# ------------------------------------------------------------------ ladowanie

def _bundled_path(game: str) -> Path:
    return resource_path(f"data/stats_{game}.ndjson")


def load_game_stats(game: str, cache_dir: Path, user_agent: str,
                    allow_download: bool = True) -> GameStats | None:
    """Dane z cache (swieze) -> z sieci -> z kopii dolaczonej do programu.

    Zwraca None tylko, gdy nie ma ZADNEGO zrodla - wtedy trade_api zostaje
    przy starym silniku, zamiast wywalac wycene.
    """
    url = DATA_URLS.get(game)
    cache_path = cache_dir / f"game_stats_{game}.ndjson"
    text: str | None = None

    if cache_path.exists() and (time.time() - cache_path.stat().st_mtime) < DATA_TTL_SECONDS:
        text = _read(cache_path)
    if text is None and allow_download and url:
        try:
            response = requests.get(url, headers={"User-Agent": user_agent}, timeout=30)
            response.raise_for_status()
            text = response.text
            try:
                cache_dir.mkdir(exist_ok=True)
                cache_path.write_text(text, encoding="utf-8")
            except OSError:
                pass
        except requests.RequestException:
            text = None
    if text is None and cache_path.exists():
        text = _read(cache_path)  # przeterminowany cache lepszy niz nic
    if text is None:
        text = _read(_bundled_path(game))
    if not text:
        return None
    stats = GameStats(text.splitlines())
    return stats if len(stats) else None


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None
