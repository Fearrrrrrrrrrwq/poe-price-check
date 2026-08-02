"""Kursy walut z oficjalnej gieldy wymiany GGG.

poe.ninja, z ktorego korzysta wiekszosc narzedzi, wylaczylo swoje API (404 na
wszystkich endpointach), wiec kursy bierzemy wprost z /api/trade/exchange.

Kurs liczymy jako MEDIANE ofert, nie najnizsza. Gielda sortuje po najtanszej,
a na gorze siedza oferty "1 chaos za 1 divine" - naciagactwo albo pomylki.
Przy prawdziwym kursie 180 wziecie minimum rozjechaloby wyceny stukrotnie.
"""

import json
import statistics
import time

EXCHANGE_URL = "https://www.pathofexile.com/api/trade/exchange/{league}"

CACHE_TTL_SECONDS = 3 * 3600  # kursy zmieniaja sie w ciagu dnia
MIN_SAMPLES = 5  # ponizej tego mediana jest zbyt przypadkowa
MAX_LOOKUPS_PER_CHECK = 3  # limit zapytan na jedna wycene, zeby nie oberwac 429


class CurrencyRates:
    """Przelicznik walut na chaosy i diviny. Dziala best-effort.

    Gdy kursu nie da sie pobrac, przeliczenie po prostu nie nastepuje - wycena
    nadal dziala, tylko bez kolumny z divinami. Kurs nigdy nie jest wazniejszy
    od samego wyniku.
    """

    def __init__(self, client, league: str, cache_dir) -> None:
        self.client = client  # obiekt z metodami _request i limiterem
        self.league = league
        self.cache_path = cache_dir / f"rates_{league.replace(' ', '_')}.json"
        self._rates: dict[str, float] = {"chaos": 1.0}
        self._failed: set[str] = set()
        self._load_cache()

    # ------------------------------------------------------------- cache

    def _load_cache(self) -> None:
        # Plik cache moze byc uszkodzony na wiecej sposobow niz "nie parsuje sie":
        # poprawny JSON o zlym ksztalcie (lista zamiast obiektu, tekst zamiast
        # liczby) tez nie moze wywrocic startu.
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            if time.time() - data.get("fetched_at", 0) > CACHE_TTL_SECONDS:
                return
            rates = data.get("rates")
            if isinstance(rates, dict):
                self._rates.update({
                    key: float(value) for key, value in rates.items()
                    if isinstance(value, (int, float))
                })
        except (OSError, ValueError, TypeError, AttributeError):
            return

    def _save_cache(self) -> None:
        try:
            self.cache_path.parent.mkdir(exist_ok=True)
            self.cache_path.write_text(
                json.dumps({"fetched_at": time.time(), "rates": self._rates}),
                encoding="utf-8",
            )
        except OSError:
            pass  # brak zapisu cache to nie powod, by cokolwiek przerywac

    # -------------------------------------------------------------- kursy

    def chaos_per(self, currency: str) -> float | None:
        """Ile chaosow kosztuje jedna sztuka podanej waluty."""
        if not currency:
            return None
        if currency in self._rates:
            return self._rates[currency]
        if currency in self._failed:
            return None

        rate = self._fetch_rate(currency)
        if rate is None:
            self._failed.add(currency)
            return None
        self._rates[currency] = rate
        self._save_cache()
        return rate

    def _fetch_rate(self, currency: str) -> float | None:
        payload = {
            "query": {
                "status": {"option": "online"},
                "have": ["chaos"],
                "want": [currency],
            },
            "sort": {"have": "asc"},
        }
        try:
            data = self.client._request(
                "POST",
                EXCHANGE_URL.format(league=self.league),
                data=json.dumps(payload),
            )
        except Exception:  # noqa: BLE001 - brak kursu nie moze przerwac wyceny
            return None

        ratios: list[float] = []
        for entry in (data.get("result") or {}).values():
            for offer in (entry.get("listing", {}) or {}).get("offers", []):
                have = (offer.get("exchange") or {}).get("amount")
                want = (offer.get("item") or {}).get("amount")
                if have and want:
                    ratios.append(have / want)

        if len(ratios) < MIN_SAMPLES:
            return None
        return statistics.median(ratios)

    def divine_rate(self) -> float | None:
        """Ile chaosow kosztuje divine."""
        return self.chaos_per("divine")

    # ---------------------------------------------------------- przeliczanie

    def annotate(self, listings: list) -> None:
        """Dopisuje ofertom rownowartosc w chaosach i divinach.

        Kursy pobieramy tylko dla walut faktycznie wystepujacych w wynikach i nie
        wiecej niz kilka na jedna wycene - kazdy brakujacy kurs to osobne
        zapytanie do gieldy, a te sa limitowane tak samo jak wyszukiwanie.
        """
        needed = {l.price_currency for l in listings if l.price_currency}
        known = set(self._rates) | self._failed
        missing = [c for c in needed if c not in known][:MAX_LOOKUPS_PER_CHECK]

        for currency in ["divine", *missing]:
            self.chaos_per(currency)

        divine = self._rates.get("divine")
        for listing in listings:
            if listing.price_amount is None:
                continue
            chaos = self.chaos_per(listing.price_currency)
            if chaos is None:
                continue
            listing.chaos_value = listing.price_amount * chaos
            if divine:
                listing.divine_value = listing.chaos_value / divine
