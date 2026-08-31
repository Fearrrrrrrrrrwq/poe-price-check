# poe-price-check (Boosteroid)

Sprawdzanie cen przedmiotów z Path of Exile 1 przy grze przez **Boosteroid**.

## Dlaczego to jest w ogóle potrzebne

Awakened PoE Trade i podobne narzędzia działają tak: `Ctrl+C` nad przedmiotem →
tool czyta **schowek** → pyta API trade'a. Przy Boosteroidzie gra chodzi na
maszynie w chmurze, więc `Ctrl+C` wypełnia schowek *tam*, a nie u ciebie.
Boosteroid synchronizuje schowek [tylko w kierunku lokalnie → chmura](https://help.boosteroid.com/en/content/how-to-paste-from-clipboard),
więc powrotu nie ma i standardowe narzędzia są bezużyteczne.

Obejście: w sesji chmurowej trzymamy otwarty publiczny dokument Google w
przeglądarce Steam Overlay. Skrypt wysyła do Boosteroida sekwencję klawiszy,
która kopiuje przedmiot i wkleja go do dokumentu, a lokalnie czytamy ten sam
dokument przez HTTP i odpytujemy oficjalne API trade'a.

```
gra (chmura) --Ctrl+C--> schowek chmury --Ctrl+V--> Google Doc
                                                        |
                                              HTTP export?format=txt
                                                        v
                                        lokalny skrypt -> API trade'a -> overlay
```

## Wymagania

- Windows lub macOS (patrz [macOS](#macos-eksperymentalne) niżej — wsparcie jest nowe i niepełne)
- Gra uruchamiana w Boosteroidzie **przez Steama** (potrzebny Steam Overlay)
- Konto Google

### Wariant A: gotowy .exe (bez Pythona)

Pobierz archiwum ze strony **[poepricecheck.eu](https://poepricecheck.eu)**,
rozpakuj i uruchom `poe-price-check.exe` — nic nie trzeba instalować. Przy
pierwszym uruchomieniu otworzy się **kreator konfiguracji**, który przeprowadzi
przez utworzenie dokumentu-mostu; wystarczy wkleić link, resztę wyciągnie sam.

Program działa jako zwykła aplikacja okienkowa — bez okna konsoli. Diagnostyka
trafia do pliku `poe-price-check.log` obok exe. Słownik statystyk (~2 MB) leży
w podkatalogu `.cache`.

Tryby diagnostyczne uruchamiane z argumentami same podpinają konsolę, więc
`poe-price-check.exe --test-sequence` w terminalu nadal wypisuje wszystko na
bieżąco.

> **Dwie rzeczy, które zrobi Windows.** Exe nie jest podpisany cyfrowo, więc
> SmartScreen pokaże „System Windows ochronił Twój komputer" → *Więcej informacji*
> → *Uruchom mimo to*. Dodatkowo program zakłada globalny hook klawiatury (inaczej
> nie da się złapać skrótu w trakcie gry), co część antywirusów heurystycznie
> zgłasza jako keylogger. Jeśli Defender go skasuje, dodaj wyjątek — albo zbuduj
> sam z tych źródeł przez `build.bat` i miej pewność, co uruchamiasz.

### Wariant B: ze źródeł

Python 3.11+, potem:

```bash
pip install -r requirements.txt
```

Przebudowa exe (wymaga dodatkowo `pip install pyinstaller`):

```bash
build.bat
```

### macOS (eksperymentalne)

Gotowy `.exe` jest tylko dla Windows — na macOS uruchamiasz **ze źródeł**
(nie ma jeszcze paczki `.app`, patrz zastrzeżenie niżej):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Program prosi macOS o uprawnienie **Dostępność** (Accessibility) dla
Terminala/Pythona — bez niego globalny skrót klawiszowy i przełączanie się
między oknem gry a programem nie zadziała. System sam o to zapyta przy
pierwszym użyciu; jeśli nie zapyta, dodaj ręcznie: *Ustawienia systemowe →
Prywatność i ochrona → Dostępność*.

> **To wsparcie jest świeże i nieprzetestowane na prawdziwym Macu** — kod
> platformowy (`winutil_macos.py`) został napisany na podstawie dokumentacji
> AppleScript/System Events, nie sprawdzony ręcznie krok po kroku na macOS.
> Jeśli używasz Maca i coś nie działa — zgłoś na GitHubie albo Discordzie
> (linki niżej), to pomoże doszlifować tę ścieżkę. Budowanie gotowej paczki
> `.app` (jak `build.bat` robi `.exe`) nie jest jeszcze zrobione.

## 1. Dokument-most

1. Utwórz nowy dokument na [docs.new](https://docs.new).
2. **Udostępnij** → Dostęp ogólny → *Każdy użytkownik, który ma link* → rola
   **Edytujący**. Bez prawa edycji sesja w chmurze nie wklei do niego treści.
3. W dokumencie: *Narzędzia → Preferencje* → odznacz **Automatyczne zastępowanie**.
   Inaczej autokorekta potrafi przerobić `--------` na pauzę i zepsuć parsowanie.
   (Parser radzi sobie z oboma wariantami, ale po co ryzykować.)
4. Z adresu `docs.google.com/document/d/**TO_JEST_ID**/edit` wyciągnij ID i wklej
   do `config.json` jako `gdoc_id`.

> Dokument z takim udostępnieniem może edytować każdy, kto zgadnie link. Leci
> przez niego wyłącznie tekst przedmiotów z gry, więc to nic wrażliwego — ale
> nie trzymaj tam niczego innego.

## 2. Strona chmurowa (raz na sesję)

1. Steam → *Ustawienia → W grze* → ustaw **stronę startową przeglądarki overlaya**
   na URL dokumentu.
2. W Steamie zmień **skrót nakładki na F7** (*Ustawienia → W grze → Skrót
   klawiszowy nakładki*). `Shift+Tab` wysłany programowo nie przechodzi przez
   Boosteroida — to jest ta jedna rzecz, bez której nic nie zadziała.
3. Wejdź do gry, wciśnij `F7`, otwórz przeglądarkę — dokument powinien się załadować.
4. **Kliknij raz w treść dokumentu**, żeby kursor stał w tekście. Sekwencja
   klawiszy zakłada, że fokus jest w dokumencie.
5. Zamknij overlay i graj.

Jeśli edytor Dokumentów nie chce działać w przeglądarce overlaya (potrafi być za
ciężki), użyj lżejszego zamiennika: `bridge_appsscript.gs` + `page.html`.
Instrukcja wdrożenia jest w nagłówku pliku `.gs`; potem ustaw w configu
`"transport": "appsscript"` i `appsscript_url`.

## 3. Konfiguracja

Wersja .exe tworzy `config.json` sama przy pierwszym uruchomieniu. Ze źródeł:

```bash
copy config.example.json config.json
```

Uzupełnij `gdoc_id`. Reszta ma sensowne domyślne wartości. `"league": "auto"`
samo wykrywa aktualną ligę czasową.

## 4. Uruchomienie

```bash
poe-price-check.exe
```

Ze źródeł to samo robi `python main.py` — w dalszych przykładach zamiennie.

| Skrót | Działanie |
|---|---|
| `Ctrl+D` | wyceń przedmiot pod kursorem (pełna sekwencja przez Boosteroida) |
| `Ctrl+Alt+D` | wyceń to, co masz w **lokalnym** schowku |
| `Ctrl+Alt+Q` | wyjście |

Wynik pojawia się w bezramkowym okienku przy kursorze. Okienko nie przejmuje
fokusu, więc klawisze dalej idą do gry. Kliknięcie w link na dole otwiera
wyszukiwanie na `pathofexile.com/trade` z gotowymi filtrami.

## 5. Strojenie opóźnień

To jest najbardziej kruchy element całości — sekwencja leci „w ciemno", bez
żadnej informacji zwrotnej z maszyny w chmurze. Przy wolniejszym łączu trzeba
podnieść wartości w sekcji `timing` w `config.json`, przede wszystkim
`overlay_open_ms` (czas na otwarcie overlaya) i `after_paste_ms` (czas na
autozapis Google).

Do strojenia służy:

```bash
poe-price-check.exe --test-sequence
```

Masz 5 sekund na przełączenie się do Boosteroida, potem program wykonuje pełną
sekwencję i wypisuje, co faktycznie dotarło do dokumentu. **Od tego zacznij.**

Sprawdzenie samego odczytu dokumentu, bez wysyłania klawiszy:

```bash
poe-price-check.exe --test-read
```

Wycena z lokalnego schowka — pozwala sprawdzić parser i API bez całej maszynerii
z overlayem:

```bash
poe-price-check.exe --paste
```

Test całego rdzenia na wbudowanych przykładach (tylko ze źródeł):

```bash
python smoke_test.py
```

## Ograniczenia

- **Rzadkie przedmioty.** Skrypt najpierw szuka z wszystkimi modami. Realny rzadki
  item prawie zawsze da 0 trafień, więc automatycznie powtarza zapytanie
  z modami wyłączonymi i **wyraźnie to oznacza** — pokazana cena jest wtedy ceną
  za samą bazę, nie za twój przedmiot. Prawdziwa wycena to kliknięcie w link
  i zaznaczenie na stronie tych modów, które mają znaczenie. Automatyczny wybór
  „które mody są cenne" to naturalny następny krok, ale wymaga danych o wagach
  modów (np. z poe.ninja).
- Nie obsługuje wymiany walut (endpoint `/exchange`) — waluty wyceniają się przez
  zwykłe wyszukiwanie.
- Klaster jewels, memories i inne przedmioty z opcjami wyboru w filtrach mogą się
  nie dopasować w pełni.
- Skrypt musi mieć prawo wysyłania klawiszy do okna Boosteroida. Jeśli Boosteroid
  chodzi jako administrator, uruchom też skrypt jako administrator.

## Limity API i regulamin

Narzędzie odpytuje te same endpointy, z których korzysta strona
pathofexile.com/trade w przeglądarce. **Nie są one częścią udokumentowanego API
GGG**, a dokumentacja deweloperska GGG stwierdza wprost, że korzystanie z
endpointów spoza niej jest niezgodne z punktem 7i regulaminu. Nabór wniosków o
dostęp do udokumentowanego API jest zamknięty. Cała rodzina społecznościowych
narzędzi do wyceny działa tak od lat, ale warto o tym wiedzieć.

API ma za to ostre limity. Klient sam się przyhamowuje na podstawie nagłówków
`X-Rate-Limit-*` i respektuje `Retry-After`, ale **nie spamuj skrótem** — GGG
potrafi zablokować IP na endpoincie. W `user_agent` domyślnie jest adres strony projektu.

Jeśli dostaniesz `403`, wklej `POESESSID` (ciasteczko z zalogowanej sesji na
pathofexile.com) do `config.json`.
