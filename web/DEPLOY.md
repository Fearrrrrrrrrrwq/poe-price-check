# Wdrożenie na Cloudflare Pages

Strona, backend i baza stoją na jednym koncie Cloudflare, w jednej domenie.
Nie ma tu serwera do utrzymywania ani nic, co trzeba aktualizować.

Wszystkie polecenia uruchamiasz **z katalogu `web/`**. To ważne: `wrangler`
wysyła zawartość `dist/` jako pliki statyczne, a `functions/` i `lib/` bierze
z katalogu, w którym stoisz.

---

## Najkrótsza droga

Dwa polecenia. Pierwsze otwiera przeglądarkę i prosi o zgodę na dostęp do
Twojego konta — tego nie da się zrobić za Ciebie:

```
npx wrangler login
```

```
python deploy.py --domain poe.twojadomena.pl
```

`deploy.py` robi resztę: zakłada bazę, wpisuje jej identyfikator do
`wrangler.toml` (w oba miejsca), zakłada tabele, tworzy projekt Pages, ustawia
token startowy, buduje stronę z właściwym adresem, sprawdza ją i wysyła.
Jest idempotentny — można go uruchamiać wielokrotnie, istniejących zasobów
nie zakłada drugi raz.

Na koniec wypisze polecenie do założenia konta administratora. **Hasło
podstawiasz własne** — skrypt go nie generuje i nie zna.

Bez `--domain` wdroży na `poe-price-check.pages.dev`, co jest dobrym sposobem
na sprawdzenie wszystkiego przed podpięciem domeny.

Reszta tego dokumentu opisuje te same kroki ręcznie — przydatne, gdy coś
pójdzie nie tak albo gdy chcesz wiedzieć, co dokładnie się dzieje.

---

## Co będzie potrzebne

- konto Cloudflare (darmowe wystarczy — D1 i Pages mieszczą się w limitach),
- domena **wpięta w Cloudflare**, czyli taka, której serwery nazw wskazują
  na Cloudflare. Jeśli domena jest u innego operatora, patrz „Domena poza
  Cloudflare" na końcu,
- Node.js (jest) i `wrangler` (zainstalowany lokalnie w `web/`).

---

## 1. Zaloguj wranglera

```
npx wrangler login
```

Otworzy przeglądarkę i poprosi o zgodę. Robisz to raz.

## 2. Załóż bazę

```
npx wrangler d1 create poe-price-check
```

Polecenie wypisze `database_id`. **Wklej go w `wrangler.toml` w dwa miejsca** —
do sekcji produkcyjnej i do `[env.preview]`. Bez tego drugiego wdrożenia
z gałęzi bocznych ruszą bez bazy.

Załóż tabele:

```
npx wrangler d1 execute poe-price-check --remote --file=schema.sql
```

`--remote` jest tu kluczowe. Bez tej flagi wrangler zakłada tabele w bazie
lokalnej na Twoim dysku, a zdalna zostaje pusta.

## 3. Utwórz projekt Pages

```
npx wrangler pages project create poe-price-check --production-branch=main
```

## 4. Ustaw sekrety projektu

```
npx wrangler pages secret put SETUP_TOKEN
```

Wklej długi losowy ciąg. Posłuży jeden raz — do założenia konta w kroku 6 —
i potem przestaje mieć znaczenie.

```
npx wrangler pages secret put ANALYTICS_SALT
```

Też długi losowy ciąg. Solą jest hashowany odwiedzający w liczniku wejść.
Bez niej dałoby się odtworzyć adres IP zgadywaniem — przestrzeń adresów IPv4
jest na to za mała. Raz ustawionej nie zmieniaj bez potrzeby: zmiana rozspójni
liczbę unikalnych wejść na styku dnia.

`deploy.py` ustawia oba sekrety sam, więc ten krok dotyczy tylko instalacji
ręcznej.

## 5. Zbuduj i wyślij

W PowerShellu:

```
$env:SITE_URL="https://poe.twojadomena.pl"; python build.py
```

W bashu:

```
SITE_URL=https://poe.twojadomena.pl python build.py
```

Adres musi być ten docelowy — wchodzi w `canonical`, `hreflang`, `sitemap.xml`
i `og:image`. Zła wartość niczego nie wywali, tylko wyszukiwarki zaindeksują
nieistniejące adresy. `build.py` ostrzeże, jeśli zostawisz adres testowy.

```
npx wrangler pages deploy
```

Dostaniesz adres `https://poe-price-check.pages.dev`. Na nim wszystko już
działa — domena to ostatni krok.

## 6. Załóż konto administratora

Jednorazowo, z tokenem z kroku 4:

```
curl -X POST https://poe-price-check.pages.dev/api/setup -H "Content-Type: application/json" -d "{\"token\":\"TWOJ-SETUP-TOKEN\",\"login\":\"kacper\",\"password\":\"dlugie-haslo\"}"
```

Odpowiedź `{"ok":true,...}` oznacza sukces. Od tej chwili `/api/setup` zwraca
`already_done` i nie da się nim niczego nadpisać.

Wejdź na `/admin/` i zaloguj się. Hasło zmienisz później w samym panelu.

## 7. Podepnij domenę

W panelu Cloudflare: **Workers & Pages → poe-price-check → Custom domains →
Set up a domain**. Wpisz `poe.twojadomena.pl`.

Cloudflare sam doda rekord DNS i wystawi certyfikat. Trwa to od minuty do
kilkunastu. Działa też domena główna (`twojadomena.pl`) — Cloudflare radzi
sobie z tym mimo ograniczeń CNAME.

Po podpięciu **zbuduj i wyślij ponownie** z właściwym adresem, jeśli w kroku 5
użyłeś innego:

```
$env:SITE_URL="https://poe.twojadomena.pl"; python build.py; npx wrangler pages deploy
```

## 8. Przełącz aplikację na nowy adres

W `config.json` aplikacji:

```json
"telemetry_url": "https://poe.twojadomena.pl/api/collect"
```

Stary adres Apps Script przestaje być potrzebny.

---

## Późniejsze aktualizacje

```
$env:SITE_URL="https://poe.twojadomena.pl"; python build.py; npx wrangler pages deploy
```

Zmiany w `functions/` i `lib/` idą tym samym poleceniem. Zmiana schematu bazy
wymaga osobno `wrangler d1 execute ... --remote`.

Podgląd na żywo przed wysłaniem:

```
npx wrangler pages dev --persist-to=.wrangler/state
```

---

## Pułapki, na które już wpadliśmy

**Nagłówki w `_headers` nakładają się.** Cloudflare stosuje **wszystkie**
pasujące reguły, nie tylko najbardziej szczegółową, a ścieżki dopasowuje
prefiksem — samo `/` obejmuje całą witrynę. Gdy strona dostanie dwie polityki
CSP, przeglądarka wymusza ich część wspólną, więc reguła ogólna potrafi po cichu
zablokować panelowi własne API. Dlatego CSP jest **dokładnie jedna** i `check.py`
tego pilnuje. Nie dodawaj drugiej.

**HSTS preload jest prawie nieodwracalny.** Domyślnie go nie wysyłamy.
Wykreślenie z listy trwa miesiącami, a do tego czasu przeglądarki odmawiają
połączenia po http z całą domeną. Włączaj dopiero, gdy strona jest stabilna
i na pewno zostaje pod tym adresem:

```
$env:HSTS_PRELOAD="1"; python build.py
```

Zwróć uwagę, że `includeSubDomains` obejmuje wszystkie poddomeny hosta, który
wysłał nagłówek. Na `poe.twojadomena.pl` to bezpieczne. Na domenie głównej
dotknie **każdej** poddomeny firmy — wtedy przemyśl to dwa razy.

**`--remote` przy poleceniach do bazy.** Bez tej flagi pracujesz na kopii
lokalnej i będziesz się zastanawiał, czemu panel na produkcji jest pusty.

**Lokalny `workerd` nie egzekwuje wszystkich limitów produkcji.** Testy
w `wrangler pages dev` przechodziły z PBKDF2 o 150 000 iteracji, a produkcja
odrzuca wszystko powyżej 100 000 wyjątkiem i błędem 1101. Jeśli po wdrożeniu
dostajesz 1101 mimo działającego kodu lokalnie, sięgnij po prawdziwy powód
zamiast zgadywać:

```
npx wrangler pages deployment tail <ID-WDROZENIA> --project-name=poe-price-check
```

Identyfikator wdrożenia znajdziesz w panelu albo przez API. Log pokazuje
dokładną treść wyjątku — bez tego 1101 nic nie mówi.

**Sprawdzaj treść odpowiedzi, nie sam kod HTTP.** Zaparkowana domena też
zwraca 200. Kilka razy dało to złudzenie, że coś działa.

**Klienty pythonowe bywają odrzucane po sygnaturze.** `Python-urllib/3.x`
dostaje od Cloudflare `error code: 1010`, zanim zapytanie dojdzie do kodu.
Wystarczy ustawić własny nagłówek `User-Agent`. `requests` z domyślną
sygnaturą przechodzi, więc telemetria aplikacji działa bez zmian.

**Zatrzymywanie serwera deweloperskiego.** Ubicie procesu `node` zostawia przy
życiu `workerd`, który dalej trzyma port. Jeśli po restarcie widzisz stare
odpowiedzi, sprawdź, czy nie chodzą dwa naraz.

---

## Domena poza Cloudflare

Jeśli nie chcesz przenosić serwerów nazw, dodaj u swojego operatora rekord:

```
CNAME   poe   poe-price-check.pages.dev
```

Domenę i tak trzeba najpierw dodać w Custom domains, żeby Cloudflare wystawił
certyfikat. Domena główna tą drogą nie zadziała — CNAME na apeksie jest
niedozwolony, potrzebne są serwery nazw Cloudflare.

---

## Ile to kosztuje

Darmowy plan Cloudflare obejmuje nielimitowany transfer plików statycznych,
100 tys. wywołań funkcji dziennie oraz bazę D1: 5 GB miejsca, 5 mln odczytów
i **100 tys. zapisów** dziennie.

Wiążący jest ten ostatni limit, bo każdy sygnał z aplikacji to jeden zapis.
Przy sygnale co 6 godzin jedna instalacja daje 4 zapisy dziennie, czyli limit
wyczerpie dopiero jakieś 25 tys. czynnych użytkowników. Do tego czasu
nie zapłacisz nic.

Gdyby kiedyś przycisnęło, najtańszym ruchem jest zwiększenie odstępu między
sygnałami (`HEARTBEAT_SECONDS` w `telemetry.py`) — z 6 na 12 godzin podwaja
zapas bez utraty czegokolwiek istotnego.
