"""Klient oficjalnego API trade'a Path of Exile 1 (pathofexile.com/trade).

Obsluguje: pobieranie i cache slownika statystyk, dopasowanie modow z tekstu
przedmiotu do ID statystyk, budowanie zapytania, wyszukiwanie i pobieranie ofert.

Uwaga na limity zapytan - GGG zwraca naglowki X-Rate-Limit-* i potrafi zbanowac
IP na endpoincie. Klient sam sie przyhamowuje na podstawie tych naglowkow.
"""

# Adnotacje jako tekst, nie wyliczane od razu. Bez tego odwolanie w przod
# (np. list[Listing] przed definicja klasy) wywala import na Pythonie
# starszym niz 3.14 - dokladnie tak padl build z CI, ktory uzywa 3.12.
from __future__ import annotations

import json
import re
import statistics
import time
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

import pseudo_stats
from currency import CurrencyRates
from i18n import t
from item_parser import QUALIFIER_RE, Mod, ParsedItem, normalize
from paths import APP_DIR

BASE = "https://www.pathofexile.com"
CACHE_DIR = APP_DIR / ".cache"
CACHE_TTL_SECONDS = 7 * 24 * 3600
MAX_FETCH_IDS = 10  # twardy limit endpointu /api/trade/fetch/

# "+#% to Fire Resistance" i "#% to Fire Resistance" to ten sam wzorzec.
SIGNED_HASH_RE = re.compile(r"[+-]?#")
LOCAL_SUFFIX_RE = re.compile(r"\s*\(local\)\s*$", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+")

# Mody "reduced"/"less" trade trzyma jako "increased"/"more" z ujemna wartoscia.
NEGATED_WORDS = {"reduced": "increased", "less": "more"}

# Liczba w tekscie statystyki - do zbudowania luznego indeksu.
NUM_IN_TEXT_RE = re.compile(r"[+-]?\d+(?:\.\d+)?")

# Rodzaje statystyk w kolejnosci, w jakiej warto ich probowac przy dopasowaniu.
# Kolejnosc ma znaczenie tylko dla szybkosci - trafienie w "explicit" jest
# najczestsze. Lista musi obejmowac WSZYSTKIE grupy, ktore zwraca
# /api/trade/data/stats; brakujaca grupa oznacza mody, ktorych nigdy nie
# dopasujemy. Sprawdza to test w check_stat_kinds.py.
ALL_STAT_KINDS = (
    "explicit", "implicit", "fractured", "crafted", "enchant",
    "veiled", "scourge", "crucible", "pseudo",
    # Dopisane po tym, jak okazalo sie, ze GGG ma ich wiecej niz znalismy.
    "imbued", "mercenary", "delve", "ultimatum", "sanctum",
)

# Klasy przedmiotow, na ktorych statystyka moze byc "lokalna", czyli dotyczyc
# samego przedmiotu, a nie postaci. Pancerz zwieksza wlasne ES, pierscien - cale.
LOCAL_DEFENCE_CLASSES = {"Body Armours", "Helmets", "Gloves", "Boots", "Shields"}
WEAPON_CLASS_HINTS = ("Sword", "Axe", "Mace", "Bow", "Wand", "Dagger", "Claw",
                      "Sceptre", "Stave", "Staff", "Fishing Rod")
DEFENCE_WORDS = ("armour", "evasion", "energy shield", "ward", "block")
WEAPON_WORDS = ("attack speed", "critical strike chance", "accuracy", "weapon range",
                "physical damage", "elemental damage", "chaos damage",
                "fire damage", "cold damage", "lightning damage",
                # Te tez maja warianty lokalne wylacznie na broni.
                "leeched", "poison on hit", "chance to bleed", "maim on hit",
                "hits can't be evaded")


def _prefers_local(item: ParsedItem, pattern: str) -> bool:
    """Czy dla tego przedmiotu i tego moda wlasciwy jest wariant '(Local)'."""
    item_class = item.item_class or ""
    text = pattern.lower()
    if item_class in LOCAL_DEFENCE_CLASSES:
        return any(word in text for word in DEFENCE_WORDS)
    if any(hint in item_class for hint in WEAPON_CLASS_HINTS):
        return any(word in text for word in WEAPON_WORDS)
    return False


class TradeError(RuntimeError):
    """Blad po stronie API handlu.

    Atrybut kind niesie krotka, stabilna etykiete rodzaju bledu. Sam komunikat
    jest tlumaczony i przeredagowywany miedzy wersjami, wiec do zliczania w
    statystykach nadaje sie wylacznie taka etykieta.
    """

    def __init__(self, message: str, kind: str = "trade") -> None:
        super().__init__(message)
        self.kind = kind


def _fmt_number(value: float) -> str:
    return str(int(value)) if value == int(value) else f"{value:.1f}"


def _fmt_price(value: float) -> str:
    if value >= 10:
        return str(round(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _quality_from_properties(properties: list | None) -> int | None:
    """Wyciaga jakosc z listy wlasciwosci przedmiotu w odpowiedzi trade'a."""
    for prop in properties or []:
        if (prop or {}).get("name") != "Quality":
            continue
        values = prop.get("values") or []
        if values and values[0]:
            match = re.search(r"\d+", str(values[0][0]))
            if match:
                return int(match.group(0))
    return None


def _flask_variants(pattern: str):
    """Warianty tekstu moda flaszki tak, jak zapisuje go trade.

    Na samej flaszce mod jest lokalny ("13% increased Movement Speed"), a GGG
    indeksuje go z dopisanym kontekstem ("... during Effect") albo ze slowem
    "Flask" wsrodku ("#% reduced Flask Charges used").
    """
    yield f"{pattern} during Effect"
    with_flask = re.sub(
        r"\b(increased|reduced|more|less)\s+", r"\1 Flask ", pattern, count=1,
        flags=re.IGNORECASE,
    )
    if with_flask != pattern:
        yield with_flask


def _drop_outliers(listings: list[Listing]) -> list[Listing]:
    """Odsiewa skrajne oferty gieldy wzgledem mediany.

    Gielda sortuje po najtanszej ofercie, a na samej gorze siedza "1 chaos za
    divine" - naciagactwo albo pomylki. Bez odsiania trzy pierwsze oferty daja
    wycene divine'a na 2 chaosy zamiast 180.
    """
    priced = [entry for entry in listings if entry.chaos_value]
    if len(priced) < 4:
        return listings
    middle = statistics.median(entry.chaos_value for entry in priced)
    return [
        entry for entry in priced
        if middle * 0.4 <= entry.chaos_value <= middle * 2.5
    ] or listings


def _value_filter(
    values: list[float], ranges: list[tuple[float, float]]
) -> dict | None:
    """Buduje warunek na wartosc statystyki - zawsze tylko dolna granica.

    Gdy PoE poda zakres tieru (wymaga wlaczonych rozszerzonych opisow modow),
    bierzemy jego dol. Dzieki temu w wynikach lada tez przedmioty z tym samym
    modem w wyzszym tierze - bez gornej granicy nic ich nie odcina. Bez zakresu
    zostaje sama rolka.
    """
    if ranges:
        return {"min": ranges[0][0]}
    if values:
        return {"min": min(values)}
    return None


def canon(text: str) -> str:
    """Sprowadza tekst moda do postaci porownywalnej po obu stronach."""
    text = text.lower().strip()
    text = LOCAL_SUFFIX_RE.sub("", text)
    text = SIGNED_HASH_RE.sub("#", text)
    return WHITESPACE_RE.sub(" ", text)


@dataclass
class Listing:
    price_amount: float | None
    price_currency: str
    account: str
    character: str
    item_name: str
    note: str
    item_level: int | None = None
    quality: int | None = None
    indexed: str = ""  # znacznik czasu wystawienia, ISO 8601
    chaos_value: float | None = None  # rownowartosc w chaosach
    divine_value: float | None = None  # rownowartosc w divinach

    def divine_text(self) -> str:
        if self.divine_value is None:
            return ""
        return f"{self.divine_value:.2f}"

    def price_text(self) -> str:
        if self.price_amount is None:
            return "brak ceny"
        amount = (int(self.price_amount) if self.price_amount == int(self.price_amount)
                  else round(self.price_amount, 2))
        return f"{amount} {self.price_currency}"

    def age_text(self) -> str:
        """Ile czasu minelo od wystawienia: '3h', '2d', '<1h'."""
        if not self.indexed:
            return ""
        try:
            listed = datetime.fromisoformat(self.indexed.replace("Z", "+00:00"))
        except ValueError:
            return ""
        delta = datetime.now(timezone.utc) - listed
        if delta.days >= 1:
            return f"{delta.days}d"
        hours = delta.seconds // 3600
        return f"{hours}h" if hours else "<1h"


@dataclass
class PropertyOption:
    """Wlasciwosc przedmiotu sterowana suwakiem (poziom przedmiotu, linki).

    Tak jak przy modach trzymamy sie samej dolnej granicy - gorna odcinalaby
    lepsze przedmioty, a to wlasnie one wyznaczaja gorna polke ceny.
    """

    key: str  # ilvl | links | pdps | edps | dps
    label: str
    value: int
    minimum: int
    maximum: int
    enabled: bool = False


@dataclass
class ModOption:
    """Jeden mod przedmiotu wraz z filtrem, ktory z niego wynika.

    To jest model dla interfejsu: uzytkownik moze go wlaczyc, wylaczyc albo
    zmienic dolna granice, a my przebudowujemy z tego zapytanie.
    """

    mod: Mod
    stat_id: str
    min_value: float | None
    enabled: bool = True
    hidden: bool = False  # zwiniete, bo juz wchodzi w pokazana sume
    searchable: bool = True  # False dla modow bez odpowiednika w trade
    sources: tuple = ()  # dla sum: mody, z ktorych powstala

    def label(self) -> str:
        return self.mod.text

    def badge(self) -> str:
        """Dla sumy - afiksy skladowe, np. 'P2+S5'. Dla moda - jego wlasny tier."""
        if self.sources:
            parts = [s.badge() for s in self.sources if s.badge()]
            if parts:
                return "+".join(dict.fromkeys(parts))
        return self.mod.badge()


@dataclass
class SearchResult:
    search_id: str
    total: int
    listings: list[Listing]
    league: str
    mods_used: int = 0  # ile modow poszlo do zapytania
    mods_unmatched: int = 0  # ilu modow nie udalo sie zmapowac na ID statystyki
    is_exchange: bool = False  # wynik z gieldy wymiany, nie z wyszukiwarki

    def browser_url(self) -> str:
        section = "exchange" if self.is_exchange else "search"
        return f"{BASE}/trade/{section}/{self.league}/{self.search_id}"

    def summary(self) -> str:
        """Szacowana wartosc liczona z pobranych ofert.

        Gdy udalo sie pobrac kursy, liczymy po rownowartosci w chaosach - dzieki
        temu oferty w roznych walutach sa porownywalne. Bez kursow spadamy do
        waluty wystepujacej najczesciej i mowimy to wprost.
        """
        priced = [l for l in self.listings if l.price_amount is not None]
        if not priced:
            return t("sum.no_data")

        converted = [l for l in priced if l.chaos_value is not None]
        if len(converted) >= 2:
            values = sorted(l.chaos_value for l in converted)
            median = statistics.median(values)
            # ile divinow przypada na jednego chaosa
            divine_per_chaos = next(
                (l.divine_value / l.chaos_value for l in converted if l.divine_value), None
            )
            in_divine = median * divine_per_chaos if divine_per_chaos else None

            # Prowadzimy ta jednostka, w ktorej liczba jest czytelna: przy drogim
            # przedmiocie "94 div" mowi wiecej niz "16920 chaos", przy tanim odwrotnie.
            if in_divine is not None and in_divine >= 1:
                text = f"~{in_divine:.1f} div   ({_fmt_price(median)} chaos)"
                lo = values[0] * divine_per_chaos
                hi = values[-1] * divine_per_chaos
                text += f"   {t('sum.range')} {lo:.1f}-{hi:.1f} div"
            else:
                text = f"~{_fmt_price(median)} chaos"
                if in_divine is not None:
                    text += f"   ({in_divine:.2f} div)"
                text += f"   {t('sum.range')} {_fmt_price(values[0])}-{_fmt_price(values[-1])} chaos"

            if len(converted) < len(priced):
                text += f"   [{t('sum.converted', done=len(converted), total=len(priced))}]"
            return text

        dominant, count = Counter(l.price_currency for l in priced).most_common(1)[0]
        amounts = sorted(l.price_amount for l in priced if l.price_currency == dominant)
        median = statistics.median(amounts)
        text = (f"~{_fmt_price(median)} {dominant}   "
                f"({t('sum.range')} {_fmt_price(amounts[0])}-{_fmt_price(amounts[-1])})")
        if count < len(priced):
            text += f"   [{t('sum.in_currency', done=count, total=len(priced))}]"
        return text


def _policy_of(url: str) -> str:
    """Nazwa polityki limitow dla adresu: 'search', 'fetch', 'exchange', 'data'."""
    tail = url.split("/api/trade/", 1)[-1]
    return tail.split("/", 1)[0] or "other"


class RateLimiter:
    """Limiter na oknach przesuwnych, liczony OSOBNO dla kazdego endpointu.

    Poprzednia wersja trzymala jeden wspolny licznik i zwalniala dopiero przy
    80% wykorzystania okna, dokladajac srednie odstepy. Nie dzialalo z dwoch
    powodow:

    * GGG stosuje inne limity dla /search, /fetch i /exchange, a naglowki
      opisuja tylko ten endpoint, ktory wlasnie odpowiedzial - wspolny licznik
      mieszal je ze soba,
    * reakcja przy 80% jest spozniona. Zanim odpowiedz z takim naglowkiem
      wrocila, kolejne zapytania juz poszly i okno bylo przepelnione.

    W praktyce konczylo sie to bledem 429 i szescdziesieciosekundowa blokada
    juz po trzech wycenach.

    Teraz prowadzimy wlasny dziennik wyslanych zapytan i przed kazdym kolejnym
    sprawdzamy, czy zmiesci sie w KAZDEJ regule. Jesli nie - czekamy dokladnie
    tyle, ile trzeba, zeby najstarsze zapytanie wypadlo z okna.
    """

    # Zostawiamy jedno zapytanie zapasu w kazdym oknie: nasz zegar i zegar GGG
    # nie sa zsynchronizowane, a blokada kosztuje minute.
    SAFETY = 1

    # Zanim poznamy prawdziwe reguly (pierwsza odpowiedz), zakladamy ostroznie.
    DEFAULT_RULES = ((6, 10),)

    def __init__(self, on_wait=None) -> None:
        self._rules: dict[str, tuple[tuple[int, int], ...]] = {}
        self._sent: dict[str, deque[float]] = {}
        self._blocked_until: dict[str, float] = {}
        # Wywolanie zwrotne do interfejsu. Bez niego dluzsze czekanie wyglada
        # jak zawieszony program - a to najczestsza skarga, jaka dostajemy.
        self._on_wait = on_wait

    def wait(self, policy: str) -> None:
        now = time.monotonic()
        rules = self._rules.get(policy, self.DEFAULT_RULES)
        sent = self._sent.setdefault(policy, deque())

        # Wpisy starsze niz najdluzsze okno nie maja juz znaczenia.
        horizon = max(period for _, period in rules)
        while sent and now - sent[0] > horizon:
            sent.popleft()

        until = self._blocked_until.get(policy, 0.0)
        for limit, period in rules:
            budget = max(1, limit - self.SAFETY)
            window = [stamp for stamp in sent if now - stamp < period]
            if len(window) >= budget:
                # Wolne miejsce zrobi sie, gdy najstarsze zapytanie z okna
                # przestanie sie liczyc.
                until = max(until, window[-budget] + period)

        delay = until - time.monotonic()
        if delay > 0:
            # Spimy sekundowymi kawalkami i po kazdym odswiezamy odliczanie.
            # Jedno dlugie sleep() daloby ten sam efekt co teraz: martwe okno.
            deadline = time.monotonic() + delay
            while True:
                left = deadline - time.monotonic()
                if left <= 0:
                    break
                if self._on_wait and delay >= 1:
                    self._on_wait(int(left) + 1)
                time.sleep(min(1.0, left))
        sent.append(time.monotonic())

    def update(self, policy: str, response: requests.Response) -> None:
        if response.status_code == 429:
            retry_after = float(response.headers.get("Retry-After", "60"))
            self._blocked_until[policy] = time.monotonic() + retry_after
            return

        # Naglowki maja postac "hits:period:ban,hits:period:ban". Bierzemy
        # sumę wszystkich zakresow - i tak sprawdzamy kazda regule osobno,
        # wiec najostrzejsza zadziala sama z siebie.
        found: list[tuple[int, int]] = []
        for scope in ("Ip", "Account", "Client"):
            spec = response.headers.get(f"X-Rate-Limit-{scope}")
            if not spec:
                continue
            for rule in spec.split(","):
                try:
                    limit, period, _ = (int(part) for part in rule.split(":"))
                except ValueError:
                    continue
                if limit > 0 and period > 0:
                    found.append((limit, period))
        if found:
            self._rules[policy] = tuple(found)


class TradeClient:
    def __init__(
        self,
        league: str,
        user_agent: str,
        poesessid: str = "",
        status: str = "securable",
        on_wait=None,
    ) -> None:
        self.league = league
        # Odpowiednik listy "status" na stronie trade'a. Identyfikatory nie sa
        # oczywiste - pochodza z /api/trade/data/filters:
        #   available     - Instant Buyout and In Person
        #   securable     - Instant Buyout
        #   onlineleague  - In Person (Online in League)
        #   online        - In Person (Online)
        #   any           - Any (tez oferty offline)
        self.status = status or "securable"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        if poesessid:
            self.session.cookies.set("POESESSID", poesessid, domain=".pathofexile.com")
        self.limiter = RateLimiter(on_wait=on_wait)
        self.rates = CurrencyRates(self, league, CACHE_DIR)
        self._stat_index: dict[str, str] | None = None
        self._stat_local: dict[str, str] | None = None
        self._stat_loose: dict[str, list[str]] | None = None
        self._stat_text: dict[str, str] | None = None
        self._base_types: set[str] | None = None
        self._static_index: dict[str, str] | None = None

    # ---------------------------------------------------------------- requests

    def _request(self, method: str, url: str, **kwargs) -> dict:
        # Kazdy endpoint ma wlasny limit, wiec i wlasny licznik.
        policy = _policy_of(url)
        self.limiter.wait(policy)
        try:
            response = self.session.request(method, url, timeout=20, **kwargs)
        except requests.RequestException as exc:
            # Zerwana siec to normalna sytuacja, a nie awaria programu. Bez tego
            # opakowania leci goly wyjatek requests i tryby konsolowe koncza sie
            # tracebackiem zamiast komunikatem.
            raise TradeError(
                f"Brak polaczenia z pathofexile.com ({type(exc).__name__}). "
                "Sprawdz siec i sprobuj ponownie.",
                kind="trade_siec",
            ) from exc
        self.limiter.update(policy, response)

        if response.status_code == 429:
            raise TradeError(
                "Limit zapytan do trade'a przekroczony. Odczekaj chwile "
                f"({response.headers.get('Retry-After', '?')} s).",
                kind="trade_limit",
            )
        if response.status_code == 403:
            raise TradeError(
                "403 od pathofexile.com - najczesciej Cloudflare. Wpisz POESESSID "
                "w config.json (ciasteczko z zalogowanej sesji na pathofexile.com).",
                kind="trade_403",
            )
        if not response.ok:
            # Sam kod HTTP w etykiecie: 400 od /search to prawie zawsze filtr,
            # ktorego GGG nie zna - dokladnie tak objawil sie bug z Foulborn.
            raise TradeError(f"HTTP {response.status_code} z {url}: {response.text[:200]}",
                             kind=f"trade_{response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            raise TradeError(f"Odpowiedz z {url} nie jest JSON-em.",
                             kind="trade_json") from exc

    def _cached(self, name: str, url: str) -> dict:
        CACHE_DIR.mkdir(exist_ok=True)
        path = CACHE_DIR / f"{name}.json"
        if path.exists() and (time.time() - path.stat().st_mtime) < CACHE_TTL_SECONDS:
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                # Uciety albo uszkodzony plik (np. program zabity w trakcie
                # zapisu) nie moze na stale blokowac startu - pobieramy na nowo.
                print(f"[uwaga] cache {path.name} jest uszkodzony - pobieram ponownie.")

        data = self._request("GET", url)
        try:
            path.write_text(json.dumps(data), encoding="utf-8")
        except OSError:
            pass  # brak zapisu cache tylko spowalnia kolejny start
        return data

    # ------------------------------------------------------------------- dane

    @staticmethod
    def fetch_leagues(user_agent: str) -> list[str]:
        """Nazwy lig. GGG zwraca je raz na realm (PC/Xbox/PS), wiec deduplikujemy."""
        # To leci przy starcie, zanim cokolwiek zdazy zlapac wyjatek - a brak
        # sieci przy uruchomieniu jest calkiem prawdopodobny.
        try:
            response = requests.get(
                f"{BASE}/api/trade/data/leagues",
                headers={"User-Agent": user_agent, "Accept": "application/json"},
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise TradeError(
                f"Nie moge pobrac listy lig ({type(exc).__name__}). Sprawdz siec, "
                "albo wpisz nazwe ligi na sztywno w config.json.",
                kind="trade_siec",
            ) from exc
        seen: dict[str, None] = {}
        for entry in response.json().get("result", []):
            if entry.get("id"):
                seen.setdefault(entry["id"], None)
        return list(seen)

    def stat_index(self) -> dict[str, str]:
        """Mapuje skanonizowany wzorzec moda ('kind|tekst') na ID statystyki."""
        if self._stat_index is not None:
            return self._stat_index

        data = self._cached("stats", f"{BASE}/api/trade/data/stats")
        index: dict[str, str] = {}
        local: dict[str, str] = {}
        loose: dict[str, list[str]] = {}
        texts: dict[str, str] = {}
        for group in data.get("result", []):
            for entry in group.get("entries", []):
                stat_id = entry.get("id", "")
                kind = stat_id.split(".", 1)[0] if "." in stat_id else "explicit"
                text = entry.get("text", "")
                if not stat_id or not text:
                    continue
                # Wielolinijkowe statystyki laczymy spacja - tak samo skladamy
                # kolejne linie moda przy dopasowaniu.
                flat = text.replace(chr(10), " ")
                # "(Local)" to OSOBNA statystyka o innym ID: pancerz z wlasnym
                # ES ma stat_4052037485, a pierscien z globalnym stat_3489782002.
                # canon() ten dopisek scina, wiec oba warianty daja ten sam klucz
                # i musza trafic do dwoch osobnych indeksow.
                target = local if LOCAL_SUFFIX_RE.search(flat) else index
                target.setdefault(f"{kind}|{canon(flat)}", stat_id)
                # Drugi indeks, w ktorym LITERALNE liczby tez ida na '#'.
                # GGG zostawia je w co czwartym wpisie ("#% increased Damage per
                # 100 Intelligence"), a tekst przedmiotu normalizujemy w calosci,
                # wiec bez tego takie mody nigdy by sie nie dopasowaly.
                # Tu trzymamy WSZYSTKICH kandydatow: warianty "per 15" i "per 100"
                # daja ten sam klucz, a rozstrzyga dopiero szablon.
                loose.setdefault(
                    f"{kind}|{canon(NUM_IN_TEXT_RE.sub('#', flat))}", []
                ).append(stat_id)
                texts.setdefault(stat_id, flat)
        # Przy kilku kandydatach w luznym indeksie pierwszy powinien byc ten
        # NAJBARDZIEJ konkretny - z najwieksza liczba cyfr wpisanych na sztywno.
        # Inaczej "for # seconds" wygrywaloby z "for 4 seconds", choc przedmiot
        # mowi wprost o czterech sekundach.
        for candidates in loose.values():
            candidates.sort(
                key=lambda sid: sum(ch.isdigit() for ch in texts.get(sid, "")),
                reverse=True,
            )

        self._stat_index = index
        self._stat_local = local
        self._stat_loose = loose
        self._stat_text = texts
        return index

    def _find_stat(
        self,
        kinds: list[str],
        pattern: str,
        prefer_local: bool = False,
        verify_text: str = "",
    ) -> str | None:
        """Szuka ID statystyki: najpierw doslownie, potem z liczbami na '#'.

        W kazdym przebiegu najpierw probujemy rodzaju, ktory przypisal parser,
        a potem WSZYSTKICH pozostalych - inaczej mod istniejacy w slowniku tylko
        jako implicit (np. "Gain # Rage on Attack Hit") nigdy by sie nie trafil,
        gdy tekst przedmiotu nie mial adnotacji.
        """
        self.stat_index()
        key = canon(pattern)
        plain, local = self._stat_index or {}, self._stat_local or {}
        # Kolejnosc zalezy od przedmiotu: pancerz z wlasnym ES chce wariantu
        # lokalnego, pierscien z ES globalnego.
        ordered = [local, plain] if prefer_local else [plain, local]

        for source in ordered:
            for kind in [*kinds, *ALL_STAT_KINDS]:
                stat_id = source.get(f"{kind}|{key}")
                if stat_id:
                    return stat_id

        # Luzny indeks na koncu. Kandydatow moze byc kilku ("per 15" i "per 100"
        # Intelligence), wiec bierzemy tego, ktorego szablon faktycznie pasuje
        # do tekstu moda - inaczej wybor bylby przypadkowy.
        loose = self._stat_loose or {}
        fallback = None
        for kind in [*kinds, *ALL_STAT_KINDS]:
            for stat_id in loose.get(f"{kind}|{key}", ()):
                if not verify_text:
                    return stat_id
                if self._template_values(stat_id, verify_text) is not None:
                    return stat_id
                fallback = fallback or stat_id
        return fallback

    def _template_values(self, stat_id: str, text: str) -> list[float] | None:
        """Wyciaga z tekstu moda te liczby, ktore w szablonie GGG stoja pod '#'.

        Bez tego "3% increased Damage per 100 Intelligence" oddaje [3, 100],
        a jako prog trafialaby dowolna z nich. Szablon mowi wprost, ktora liczba
        jest zmienna, a ktora czescia opisu.
        """
        template = (self._stat_text or {}).get(stat_id)
        if not template or "#" not in template:
            return None
        regex = "".join(
            r"([+-]?\d+(?:\.\d+)?)" if part == "#" else re.escape(part)
            for part in re.split(r"(#)", template)
        )
        match = re.fullmatch(regex, text.strip(), re.IGNORECASE)
        if not match:
            return None
        try:
            return [float(g) for g in match.groups()]
        except ValueError:
            return None

    def stat_label(self, stat_id: str, value: float) -> str:
        """Opis statystyki z podstawiona wartoscia, np. '+65% total Elemental Resistance'."""
        if self._stat_text is None:
            self.stat_index()
        template = (self._stat_text or {}).get(stat_id, stat_id)
        return template.replace("#", _fmt_number(value), 1)

    def pseudo_options(self, item: ParsedItem) -> list[ModOption]:
        """Sumy w stylu '65% total Elemental Resistance' wyliczone z modow przedmiotu.

        Domyslnie wylaczone - wlaczone naraz z pojedynczymi modami, z ktorych
        powstaly, zawezalyby wyszukiwanie podwojnie.
        """
        self.stat_index()  # upewnia sie, ze mamy opisy statystyk

        totals: dict[str, float] = {}
        sources: dict[str, list[Mod]] = {}
        for mod in item.mods:
            if mod.kind in ("scourge", "enchant") or not mod.values:
                continue
            rules = pseudo_stats.RULES.get(canon(mod.pattern))
            if not rules:
                continue
            for stat_id, weight in rules:
                totals[stat_id] = totals.get(stat_id, 0.0) + mod.values[0] * weight
                sources.setdefault(stat_id, []).append(mod)

        options: list[ModOption] = []
        for stat_id, total in totals.items():
            contributors = sources[stat_id]
            # Suma z jednego moda nie wnosi nic ponad ten mod.
            if len(contributors) < 2 and stat_id in pseudo_stats.ONLY_IF_COMBINED:
                continue
            options.append(ModOption(
                mod=Mod(
                    text=self.stat_label(stat_id, total),
                    kind="pseudo",
                    pattern="",
                    values=[total],
                    affix="PS",
                ),
                stat_id=stat_id,
                min_value=total,
                enabled=False,
                sources=tuple(contributors),
            ))
        options.sort(key=lambda option: option.mod.text)
        return options

    def static_index(self) -> dict[str, str]:
        """Nazwa -> identyfikator gieldy, dla wszystkiego co idzie hurtem.

        Waluta, fragmenty, skarabeusze, esencje, fosylia, oleje, karty - tych
        przedmiotow nie ma w wyszukiwarce przedmiotow, handluje sie nimi na
        gieldzie wymiany. Wyszukiwanie po 'type' zwracalo dla nich zawsze zero.
        """
        if self._static_index is not None:
            return self._static_index
        data = self._cached("static", f"{BASE}/api/trade/data/static")
        names: dict[str, str] = {}
        for group in data.get("result", []):
            for entry in group.get("entries", []) or []:
                text, entry_id = entry.get("text"), entry.get("id")
                if text and entry_id:
                    names.setdefault(text, entry_id)
        self._static_index = names
        return names

    def exchange_id(self, item: ParsedItem) -> str | None:
        """Identyfikator gieldy dla przedmiotu, albo None gdy to zwykly ekwipunek."""
        if item.is_unique or item.is_rare:
            return None
        try:
            index = self.static_index()
        except TradeError:
            return None
        return index.get(item.base_type) or index.get(item.name)

    def exchange_check(self, item: ParsedItem, max_listings: int = 10) -> SearchResult:
        """Wycena przez gielde wymiany: ile chaosow za jedna sztuke."""
        want = self.exchange_id(item)
        # Pytamy o oplate i w chaosach, i w divinach - drogie rzeczy (karty,
        # fragmenty) sprzedaje sie za diviny i zapytanie o same chaosy
        # zwracaloby dla nich prawie nic.
        # Waluta placaca nie moze byc ta sama, o ktora pytamy - "mam chaosy, chce
        # chaosy" to bezsens, ktory zwracal Chaos Orb wyceniony na 4 chaosy.
        have = [c for c in ("chaos", "divine") if c != want] or ["chaos"]
        payload = {
            "query": {"status": {"option": "online"}, "have": have, "want": [want]},
            "sort": {"have": "asc"},
        }
        data = self._request(
            "POST",
            f"{BASE}/api/trade/exchange/{requests.utils.quote(self.league)}",
            data=json.dumps(payload),
        )

        divine_rate = self.rates.chaos_per("divine") or 0
        listings: list[Listing] = []
        for entry in (data.get("result") or {}).values():
            listing = (entry or {}).get("listing", {}) or {}
            account = listing.get("account", {}) or {}
            for offer in listing.get("offers", []) or []:
                exchange = offer.get("exchange") or {}
                paid, currency = exchange.get("amount"), exchange.get("currency", "chaos")
                got = (offer.get("item") or {}).get("amount")
                if not paid or not got:
                    continue
                rate = self.rates.chaos_per(currency)
                if rate is None:
                    continue
                in_chaos = paid * rate / got
                listings.append(Listing(
                    price_amount=paid / got,
                    price_currency=currency,
                    account=account.get("name", "?"),
                    character=account.get("lastCharacterName", "?"),
                    item_name=item.display_name(),
                    note="",
                    quality=(offer.get("item") or {}).get("stock"),
                    indexed=listing.get("indexed", ""),
                    chaos_value=in_chaos,
                    divine_value=(in_chaos / divine_rate) if divine_rate else None,
                ))

        listings.sort(key=lambda entry: entry.chaos_value or 0)
        listings = _drop_outliers(listings)

        return SearchResult(
            search_id=data.get("id", ""),
            total=int(data.get("total", len(listings))),
            listings=listings[:max_listings],
            league=self.league,
            is_exchange=True,
        )

    def base_types(self) -> set[str]:
        if self._base_types is not None:
            return self._base_types
        data = self._cached("items", f"{BASE}/api/trade/data/items")
        names: set[str] = set()
        for group in data.get("result", []):
            for entry in group.get("entries", []):
                if entry.get("type"):
                    names.add(entry["type"])
        self._base_types = names
        return names

    # -------------------------------------------------------- dopasowanie mod

    def analyze_mods(self, item: ParsedItem) -> tuple[list[ModOption], list[Mod]]:
        """Rozklada przedmiot na liste sterowalnych opcji + mody nierozpoznane.

        Kazdy mod zostaje osobnym wierszem, nawet jesli dwa prowadza do tej samej
        statystyki - scalanie nastepuje dopiero przy budowaniu zapytania, zeby
        w interfejsie dalo sie odznaczyc pojedynczy mod.
        """
        index = self.stat_index()
        options: list[ModOption] = []
        unmatched: list[Mod] = []

        mods = [m for m in item.mods if m.kind != "scourge"]
        i = 0
        while i < len(mods):
            mod = mods[i]
            stat_id, values, ranges, consumed = self._match_one(index, mods, i, item)
            if stat_id is None:
                unmatched.append(mod)
                i += 1
                continue
            value = _value_filter(values, ranges)
            options.append(ModOption(
                mod=mod,
                stat_id=stat_id,
                min_value=value.get("min") if value else None,
            ))
            i += consumed

        pseudo = self.pseudo_options(item)

        # Mod, ktory juz wchodzi w pokazana sume, zwijamy - to dokladnie te
        # "ukryte mody" z PoE Overlay. Zwijanie jest wylacznie wizualne: mod
        # zostaje wlaczony i nadal filtruje, zeby wynik sie nie zmienil bez
        # wiedzy uzytkownika.
        covered = {id(mod) for option in pseudo for mod in option.sources}
        for option in options:
            if id(option.mod) in covered:
                option.hidden = True

        # Mody bez odpowiednika w trade tez ida do zwinietych - lepiej pokazac
        # WLASNIE KTORE nie zadzialaly niz sama liczbe w ostrzezeniu.
        untradeable = [
            ModOption(mod=mod, stat_id="", min_value=None,
                      enabled=False, hidden=True, searchable=False)
            for mod in unmatched
        ]

        # Sumy ida na gore listy - to one najczesciej decyduja o wycenie.
        return pseudo + options + untradeable, unmatched

    @staticmethod
    def filters_from_options(options: list[ModOption]) -> list[dict]:
        """Sklada zapytanie z zaznaczonych opcji, scalajac powtorzone statystyki."""
        merged: dict[str, dict] = {}
        for option in options:
            if not option.enabled or not option.searchable or not option.stat_id:
                continue
            entry = merged.get(option.stat_id)
            if entry is None:
                entry = {"id": option.stat_id, "disabled": False}
                if option.min_value is not None:
                    entry["value"] = {"min": option.min_value}
                merged[option.stat_id] = entry
            elif option.min_value is not None:
                # Ten sam mod dwa razy (np. dwa razy max Life) - sumujemy granice.
                current = entry.setdefault("value", {})
                current["min"] = current.get("min", 0) + option.min_value
        return list(merged.values())

    def match_mods(self, item: ParsedItem) -> tuple[list[dict], list[Mod]]:
        """Skrot: od razu gotowe filtry, bez przechodzenia przez interfejs."""
        options, unmatched = self.analyze_mods(item)
        return self.filters_from_options(options), unmatched

    def _match_one(
        self, index: dict[str, str], mods: list[Mod], i: int, item: ParsedItem
    ) -> tuple[str | None, list[float], list[tuple[float, float]], int]:
        """Dopasowuje mod nr i. Zwraca (id, wartosci, zakresy tieru, ile linii zuzyto)."""
        mod = mods[i]
        # Mody "(Hidden)" sa wylacznie opisowe - trade ich nie indeksuje. Nie
        # probujemy ich dopasowac, bo luzny indeks potrafi znalezc cos podobnego
        # i taki filtr wycina wszystkie oferty.
        if mod.kind == "hidden":
            return None, [], [], 1

        # Przy wlaczonych rozszerzonych opisach KAZDY prawdziwy mod ma adnotacje
        # w klamrach. Linia bez niej to wrodzona wlasciwosc bazy - np. "40%
        # increased Movement Speed" Quicksilver Flask. Trade tego nie indeksuje
        # jako moda, a doliczanie tego do sufiksu dawalo filtr na 53% i zero ofert.
        if item.affix_info and not mod.annotated:
            return None, [], [], 1

        # Mody z sufiksem (fractured)/(crafted) i tak leza w puli explicit.
        kinds = ["explicit"] if mod.kind in ("crafted", "fractured", "veiled") else [mod.kind]
        if mod.kind == "explicit":
            kinds = ["explicit", "pseudo"]

        local = _prefers_local(item, mod.pattern)

        # 0) Flaszki NAJPIERW - ich mody sa zawsze kontekstowe. "13% increased
        # Movement Speed" na flaszce to "#% increased Movement Speed during
        # Effect", a nie globalna predkosc ruchu, ktora dopasowalaby sie pierwsza.
        if "Flask" in (item.item_class or ""):
            for variant in _flask_variants(mod.pattern):
                stat_id = self._find_stat(kinds, variant, local)
                if stat_id:
                    return stat_id, mod.values, mod.ranges, 1

        # 1) proba na pojedynczej linii
        stat_id = self._find_stat(kinds, mod.pattern, local, mod.text)
        if stat_id:
            values = self._template_values(stat_id, mod.text) or mod.values
            return stat_id, values, mod.ranges, 1

        # 2) bez znacznika wariantu doklejanego przez gre, np.
        #    "...Summon Carrion Golem(Fireball-Mana-Infused Staff) Gems".
        #    Dopiero teraz, bo GGG ma wlasne nawiasy - "(Shields)", "(Local)".
        stripped = QUALIFIER_RE.sub("", mod.pattern).strip()
        if stripped != mod.pattern:
            clean_text = QUALIFIER_RE.sub("", mod.text).strip()
            stat_id = self._find_stat(kinds, stripped, local, clean_text)
            if stat_id:
                values = self._template_values(stat_id, clean_text) or mod.values
                return stat_id, values, mod.ranges, 1

        # 3) "10% reduced X" -> stat "#% increased X" z wartoscia ujemna.
        #    Zakres tez sie odwraca: (10-20) reduced to od -20 do -10 increased.
        for word, replacement in NEGATED_WORDS.items():
            if word in mod.pattern:
                stat_id = self._find_stat(
                    kinds, mod.pattern.replace(word, replacement), local
                )
                if stat_id:
                    negated = [(-high, -low) for low, high in mod.ranges]
                    return stat_id, [-v for v in mod.values], negated, 1

        # 4) statystyka rozbita na dwie linie w tekscie przedmiotu
        if i + 1 < len(mods):
            following = mods[i + 1]
            joined_text = f"{mod.text} {following.text}"
            joined_pattern, joined_values = normalize(joined_text)
            stat_id = self._find_stat(kinds, joined_pattern, local, joined_text)
            if stat_id:
                values = self._template_values(stat_id, joined_text) or joined_values
                return stat_id, values, mod.ranges + following.ranges, 2

        return None, [], [], 1

    # ------------------------------------------------------------- zapytanie

    def property_options(self, item: ParsedItem) -> list[PropertyOption]:
        """Suwaki wlasciwosci z sensownymi wartosciami startowymi.

        Poziom przedmiotu domyslnie wylaczony - dla wiekszosci rzeczy nie ma
        wplywu na cene, a wlaczony niepotrzebnie odcinalby oferty. Linki
        odwrotnie: przy 5L i 6L to one decyduja o wartosci, wiec ida wlaczone.
        """
        options: list[PropertyOption] = []
        if item.item_level is not None:
            options.append(PropertyOption(
                key="ilvl", label=t("prop.ilvl"),
                value=item.item_level, minimum=1, maximum=100, enabled=False,
            ))
        if item.sockets:
            links = item.link_count
            options.append(PropertyOption(
                key="links", label=t("prop.links"),
                value=links, minimum=0, maximum=6, enabled=links >= 5,
            ))
        # DPS decyduje o cenie broni bardziej niz prawie kazdy pojedynczy mod,
        # wiec calkowity DPS idzie wlaczony domyslnie - pDPS/eDPS zostaja do
        # doprecyzowania, gdyby ktos chcial zawezic po samej fizyce/zywiolach.
        if item.total_dps is not None:
            value = round(item.total_dps)
            options.append(PropertyOption(
                key="dps", label=t("prop.dps"),
                value=value, minimum=0, maximum=max(value * 2, 10), enabled=True,
            ))
        if item.physical_dps is not None:
            value = round(item.physical_dps)
            options.append(PropertyOption(
                key="pdps", label=t("prop.pdps"),
                value=value, minimum=0, maximum=max(value * 2, 10), enabled=False,
            ))
        if item.elemental_dps is not None:
            value = round(item.elemental_dps)
            options.append(PropertyOption(
                key="edps", label=t("prop.edps"),
                value=value, minimum=0, maximum=max(value * 2, 10), enabled=False,
            ))
        return options

    def resolve_base_type(self, item: ParsedItem) -> str:
        """Wyluskuje baze z nazwy przedmiotu magicznego.

        PoE oddaje magiczny przedmiot jedna linia, z afiksami wtopionymi w nazwe:
        "Shimmering Iron Ring of the Walrus". Trade oczekuje samej bazy, wiec
        szukamy najdluzszego ciagu slow, ktory wystepuje na oficjalnej liscie baz.
        Najdluzszego, bo inaczej "Two-Stone Ring" przegralby z samym "Ring".
        """
        if item.rarity != "Magic" or not item.base_type:
            return item.base_type

        try:
            bases = self.base_types()
        except TradeError:
            return item.base_type  # bez listy baz zostajemy przy tym, co mamy

        words = item.base_type.split()
        best = ""
        for start in range(len(words)):
            for end in range(start + 1, len(words) + 1):
                candidate = " ".join(words[start:end])
                if len(candidate) > len(best) and candidate in bases:
                    best = candidate
        return best or item.base_type

    def build_query(
        self,
        item: ParsedItem,
        stat_filters: list[dict],
        properties: list[PropertyOption] | None = None,
        sort_desc: bool = False,
    ) -> dict:
        filters: dict[str, dict] = {}
        misc: dict[str, dict] = {}

        # Identyfikatory z /api/trade/data/filters. Wczesniej Normal i Magic szly
        # razem jako "nonunique", co dorzucalo do wynikow takze rzadkie.
        rarity = {
            "Unique": "unique",
            "Rare": "rare",
            "Magic": "magic",
            "Normal": "normal",
        }.get(item.rarity, "")

        type_filters: dict[str, dict] = {}
        if rarity:
            type_filters["rarity"] = {"option": rarity}
        if type_filters:
            filters["type_filters"] = {"filters": type_filters}

        if item.corrupted:
            misc["corrupted"] = {"option": "true"}
        # Bez tego filtru bonus z fracturu ginie w wynikach: oferty z i bez
        # przefracturowanego moda mieszaja sie w jedna srednia, a fracture
        # zwykle podbija cene (utrwala konkretny mod na sztywno). To ten sam
        # rodzaj bledu co z Foulbornem nizej, tylko dla fracture.
        if "fractured_item" in item.flags:
            misc["fractured_item"] = {"option": "true"}
        # Bez tego filtru wersja Foulborn miesza sie ze zwykla: dla jednego
        # unikatu bylo 618 ofert lacznie, a tylko 57 to faktycznie Foulborny.
        # Wycena bez filtru zanizalaby ceny kilkukrotnie.
        if item.is_foulborn:
            misc["mutated"] = {"option": "true"}
        # Ponizsze flagi parser rozpoznawal juz od dawna (item.flags), ale
        # nigdy nie trafialy do zapytania - dokladnie ten sam rodzaj bledu co
        # fractured_item wyzej. Kazda z nich realnie zmienia cene: lustrzana
        # kopia i split to zupelnie inna liga cenowa niz zwykly przedmiot,
        # nieziden. rzadki/unikat wyceni sie zupelnie inaczej niz zidenty-
        # fikowany o tych samych widocznych modach (bo kupujacy nie widzi
        # reszty), synteza i implanty eldrycze tak samo licza sie w wartosc
        # jak fracture.
        if "mirrored" in item.flags:
            misc["mirrored"] = {"option": "true"}
        if "split" in item.flags:
            misc["split"] = {"option": "true"}
        if "synthesised" in item.flags:
            misc["synthesised_item"] = {"option": "true"}
        if "veiled" in item.flags:
            misc["veiled"] = {"option": "true"}
        if "searing_item" in item.flags:
            misc["searing_item"] = {"option": "true"}
        if "tangled_item" in item.flags:
            misc["tangled_item"] = {"option": "true"}
        if "unidentified" in item.flags:
            misc["identified"] = {"option": "false"}
        if item.gem_level is not None:
            misc["gem_level"] = {"min": item.gem_level}
        # Jakosc filtrujemy tylko dla kamieni. Dla broni/pancerzy wymuszanie
        # konkretnej jakosci niepotrzebnie odcina wiekszosc ofert.
        if item.quality and item.is_gem:
            misc["quality"] = {"min": item.quality}
        if item.map_tier is not None:
            misc["map_tier"] = {"min": item.map_tier, "max": item.map_tier}
        for influence in item.influences:
            misc[f"{influence}_item"] = {"option": "true"}
        sockets: dict[str, dict] = {}
        weapon: dict[str, dict] = {}
        if properties is None:
            properties = self.property_options(item)
        for prop in properties:
            if not prop.enabled:
                continue
            if prop.key == "ilvl":
                misc["ilvl"] = {"min": prop.value}
            elif prop.key == "links":
                sockets["links"] = {"min": prop.value}
            elif prop.key in ("pdps", "edps", "dps"):
                weapon[prop.key] = {"min": prop.value}

        if misc:
            filters["misc_filters"] = {"filters": misc}
        if sockets:
            filters["socket_filters"] = {"filters": sockets}
        if weapon:
            filters["weapon_filters"] = {"filters": weapon}

        query: dict = {"status": {"option": self.status}}
        if item.is_unique and item.name:
            query["name"] = item.name
            query["type"] = item.base_type
        else:
            query["type"] = self.resolve_base_type(item) or item.name

        if filters:
            query["filters"] = filters
        if stat_filters:
            query["stats"] = [{"type": "and", "filters": stat_filters}]

        return {"query": query, "sort": {"price": "desc" if sort_desc else "asc"}}

    # ------------------------------------------------------- wyszukiwanie

    def price_check(
        self,
        item: ParsedItem,
        max_listings: int = 10,
        options: list[ModOption] | None = None,
        unmatched_count: int = 0,
        properties: list[PropertyOption] | None = None,
    ) -> SearchResult:
        """Szuka przedmiotu. Bez podanych opcji bierze wszystkie mody przedmiotu.

        Rolki ida jako dolna granica tieru. Zadnego automatycznego rozluzniania -
        od tego jest interfejs, w ktorym mozna odznaczyc mody i zmienic progi.
        """
        # Waluta, karty, fragmenty - wszystko, co ma swoj identyfikator gieldy -
        # nie istnieje w wyszukiwarce przedmiotow i musi isc przez wymiane.
        if self.exchange_id(item):
            return self.exchange_check(item, max_listings)

        if options is None:
            options, unmatched = self.analyze_mods(item)
            unmatched_count = len(unmatched)

        stat_filters = self.filters_from_options(options)
        payload = self.build_query(item, stat_filters, properties)
        search_id, total, hashes = self._search(payload)

        listings = self._fetch(hashes[:max_listings], search_id) if hashes else []
        if listings:
            self.rates.annotate(listings)
        return SearchResult(
            search_id=search_id,
            total=total,
            listings=listings,
            league=self.league,
            mods_used=len(stat_filters),
            mods_unmatched=unmatched_count,
        )

    def craft_ceiling_url(self, item: ParsedItem) -> str:
        """Adres wyszukiwania tej samej bazy/rzadkosci BEZ wymagania
        konkretnych modow, posortowany od najdrozszych - orientacyjny
        "sufit" tego, ile moze byc wart w pelni obrobiony przedmiot tej
        bazy. Misc-filtry (fractured/mirrored/wplywy itd.) zostaja, zeby
        porownanie bylo w miare rowne - tylko wymog na KONKRETNE mody
        znika.

        Celowo nie liczymy tu zadnej "oczekiwanej wartosci craftu" -
        prawdziwa cena zalezy od tego, jaki dokladnie mod wypadnie, a to
        jest wrozenie z fusow, ktore latwo wprowadzic w blad. Zamiast
        zgadywac, dajemy punkt odniesienia i zostawiamy ocene czlowiekowi.

        Sam POST po search_id, bez pobierania ofert - to tylko link do
        otwarcia w przegladarce, nie pelna wycena.
        """
        payload = self.build_query(item, [], sort_desc=True)
        search_id, _, _ = self._search(payload)
        return SearchResult(
            search_id=search_id, total=0, listings=[], league=self.league,
        ).browser_url()

    def _search(self, payload: dict) -> tuple[str, int, list[str]]:
        data = self._request(
            "POST",
            f"{BASE}/api/trade/search/{requests.utils.quote(self.league)}",
            data=json.dumps(payload),
        )
        return data.get("id", ""), int(data.get("total", 0)), data.get("result") or []

    def _fetch(self, hashes: list[str], search_id: str) -> list[Listing]:
        # Endpoint /fetch/ przyjmuje najwyzej 10 identyfikatorow naraz - wiecej
        # to blad HTTP, a max_listings pochodzi z configu i moze byc dowolne.
        hashes = hashes[:MAX_FETCH_IDS]
        if not hashes:
            return []
        data = self._request(
            "GET",
            f"{BASE}/api/trade/fetch/{','.join(hashes)}",
            params={"query": search_id},
        )
        listings: list[Listing] = []
        for entry in data.get("result", []) or []:
            if not entry:
                continue
            listing = entry.get("listing", {}) or {}
            price = listing.get("price") or {}
            account = listing.get("account", {}) or {}
            item = entry.get("item", {}) or {}
            listings.append(Listing(
                price_amount=price.get("amount"),
                price_currency=price.get("currency", ""),
                account=account.get("name", "?"),
                character=(account.get("lastCharacterName") or account.get("name") or "?"),
                item_name=(item.get("name") or item.get("typeLine") or "?").strip(),
                note=listing.get("whisper", ""),
                item_level=item.get("ilvl"),
                quality=_quality_from_properties(item.get("properties")),
                indexed=listing.get("indexed", ""),
            ))
        return listings
