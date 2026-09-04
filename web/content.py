"""Tresc strony we wszystkich jezykach.

Klucze musza byc identyczne w kazdym jezyku - build.py to sprawdza i przerywa,
gdy czegos brakuje. Lepiej nie zbudowac strony niz wypuscic ja z dziura.
"""

LANGS = {
    "en": "English",
    "pl": "Polski",
    "de": "Deutsch",
    "es": "Español",
    "pt": "Português",
    "ru": "Русский",
}

# Kod jezyka -> pelny kod dla hreflang i og:locale.
LOCALES = {"en": "en_US", "pl": "pl_PL", "de": "de_DE",
           "es": "es_ES", "pt": "pt_BR", "ru": "ru_RU"}

DEFAULT = "en"

C: dict[str, dict] = {}

C["en"] = {
    "dir": "ltr",
    "shot_result_alt": "The result panel showing an item's estimated value, matched mods and current trade listings",
    "shot_status_alt": "The main window with the app running and its keyboard shortcuts",
    "eyebrow_problem": "The problem",
    "eyebrow_how": "Setup",
    "eyebrow_features": "Capabilities",
    "eyebrow_faq": "FAQ",
    "title": "PoE Price Check for Boosteroid and cloud gaming",
    "description": "Free price checking for Path of Exile when you play through "
                   "Boosteroid or any cloud gaming service. One hotkey, live trade "
                   "prices, no clipboard needed.",
    "keywords": "path of exile price check, boosteroid, cloud gaming, poe trade, "
                "poe overlay, price checker",
    "skip": "Skip to content",
    "nav_how": "How it works",
    "nav_features": "Features",
    "nav_faq": "FAQ",
    "nav_download": "Download",
    "hero_badge": "Free · Open source · No account",
    "hero_title": "Price check in Path of Exile,\neven when the game runs in the cloud",
    "hero_lead": "Cloud gaming breaks every price checking tool, because the "
                 "clipboard only travels one way. This one works anyway.",
    "hero_cta": "Download for Windows",
    "hero_note": "Windows 10/11 · 16 MB · no installer",
    "problem_title": "Why the usual tools fail",
    "problem_body": "Awakened PoE Trade and the rest read your clipboard. When the "
                    "game runs on a machine in Warsaw and you sit in front of a "
                    "browser, that clipboard is not yours. Boosteroid only syncs it "
                    "one way, so nothing ever comes back.",
    "problem_solution": "This tool routes the item text out of the session through a "
                        "document you own, then asks the official trade API. You "
                        "press one key and see the price.",
    "how_title": "Three steps, once",
    "how_cloud_note": "Steps 1 and 2 are only for cloud gaming (Boosteroid, "
                      "GeForce NOW). On a normal PC, skip straight to step 3 - "
                      "the setup wizard asks first and skips the bridge "
                      "entirely if you're not in the cloud.",
    "how_1_t": "Create a bridge document",
    "how_1_b": "An ordinary Google Doc. The setup wizard walks you through sharing "
               "it and checks it works.",
    "how_2_t": "Point Steam at it",
    "how_2_b": "Set the overlay shortcut to F7 and the browser home page to your "
               "document. The wizard gives you the exact address to copy.",
    "how_3_t": "Press Ctrl+D in game",
    "how_3_b": "Hover an item, press the hotkey, read the price. Mods, tiers and "
               "filters are all there.",
    "features_title": "What you get",
    "f1_t": "Real mod matching",
    "f1_b": "Every mod mapped to the official trade stat, with tiers, ranges and "
            "local variants handled properly. 99.7% of the stat dictionary "
            "round-trips correctly.",
    "f2_t": "Pseudo totals",
    "f2_b": "Total elemental resistance, total life, attributes - computed and "
            "searchable, the way experienced traders actually price items.",
    "f3_t": "Divine conversion",
    "f3_b": "Prices converted using live exchange rates taken from the official "
            "bulk exchange, with outliers filtered out.",
    "f4_t": "Everything, not just rares",
    "f4_b": "Uniques, rares, magic items, gems, flasks, jewels, maps - plus "
            "currency, cards and fragments through the bulk exchange.",
    "f5_t": "Windows and macOS",
    "f5_b": "The same hotkey and matching engine run natively on both - macOS "
            "support is new and experimental, Apple Silicon included.",
    "f6_t": "One shortcut, either way",
    "f6_b": "A toggle switches the main hotkey between the Boosteroid bridge and "
            "your local clipboard - no need to remember two shortcuts.",
    "privacy_title": "About your data",
    "privacy_body": "The program sends an anonymous counter: version, language, "
                    "league, number of checks. Never items, prices, account names "
                    "or your document. You can switch it off in one line of the "
                    "config file.",
    "faq_title": "Questions",
    "faq_1_q": "Is this allowed?",
    "faq_1_a": "It reads your own screen and clipboard and queries the public trade "
               "site, the same category as every other price checking tool. There "
               "is no gameplay automation of any kind.",
    "faq_2_q": "Does it work outside Boosteroid?",
    "faq_2_a": "Yes. On a normal PC it reads the clipboard directly, so you skip the "
               "bridge document entirely and just press the hotkey.",
    "faq_3_q": "Why does Windows warn me?",
    "faq_3_a": "The file is not code-signed, and the program installs a keyboard hook "
               "to catch the hotkey during a game - antivirus heuristics dislike "
               "both. The source is public if you would rather build it yourself.",
    "faq_4_q": "Which PoE version?",
    "faq_4_a": "Path of Exile 1. PoE 2 uses a different trade API and is not "
               "supported yet.",
    "faq_5_q": "Can I just use Awakened PoE Trade instead?",
    "faq_5_a": "Not on Boosteroid or any other cloud gaming service - Awakened PoE "
               "Trade reads your local clipboard, and cloud gaming only syncs the "
               "clipboard one way (local to cloud, never back). That's the whole "
               "reason this tool exists: same trade data, same official API, but "
               "it pulls the item text out of the cloud session instead of "
               "assuming your clipboard has it.",
    "faq_6_q": "Does this work on GeForce NOW too?",
    "faq_6_a": "You probably don't need it there - GeForce NOW syncs the "
               "clipboard in both directions, so Awakened PoE Trade already "
               "works directly on GFN. This tool's bridge step is built for "
               "services where the clipboard only goes one way (local to "
               "cloud), like Boosteroid. On a different cloud service and not "
               "sure which kind it is? Copy something locally, then try "
               "pasting it inside the cloud session - if it shows up, you "
               "don't need this.",
    "download_title": "Get it",
    "download_body": "One file. Run it, the wizard does the rest.",
    "download_cta": "Download for Windows",
    "download_mac_cta": "Download for macOS",
    "download_mac_note": "Experimental and unsigned - macOS will warn about an "
                         "unidentified developer. Right-click the app -> Open -> "
                         "Open (once) to run it. See the README for details and "
                         "current limitations.",
    "download_alt": "Source code",
    "discord_cta": "Join the Discord",
    "discord_body": "Questions, bug reports and news about new versions - the Discord is the fastest way to reach me.",
    "footer_disclaimer": "This product isn't affiliated with or endorsed by Grinding "
                         "Gear Games in any way.",
    "footer_lang": "Language",
}

C["pl"] = {
    "dir": "ltr",
    "shot_result_alt": "Panel wyniku z szacowaną wartością przedmiotu, dopasowanymi modami i aktualnymi ofertami z rynku",
    "shot_status_alt": "Okno główne z działającą aplikacją i listą skrótów klawiszowych",
    "eyebrow_problem": "Problem",
    "eyebrow_how": "Konfiguracja",
    "eyebrow_features": "Możliwości",
    "eyebrow_faq": "Pytania",
    "title": "PoE Price Check dla Boosteroida i gry w chmurze",
    "description": "Darmowa wycena przedmiotów w Path of Exile przy grze przez "
                   "Boosteroid i inne usługi chmurowe. Jeden skrót, aktualne ceny "
                   "z rynku, bez schowka.",
    "keywords": "path of exile wycena, poe price check, boosteroid, granie w chmurze, "
                "poe trade, poe overlay",
    "skip": "Przejdź do treści",
    "nav_how": "Jak to działa",
    "nav_features": "Możliwości",
    "nav_faq": "Pytania",
    "nav_download": "Pobierz",
    "hero_badge": "Za darmo · Otwarty kod · Bez konta",
    "hero_title": "Wyceniaj przedmioty w Path of Exile,\nnawet gdy gra działa w chmurze",
    "hero_lead": "Granie w chmurze psuje każde narzędzie do wyceny, bo schowek "
                 "przesyła dane tylko w jedną stronę. To działa mimo wszystko.",
    "hero_cta": "Pobierz na Windows",
    "hero_note": "Windows 10/11 · 16 MB · bez instalatora",
    "problem_title": "Dlaczego zwykłe narzędzia zawodzą",
    "problem_body": "Awakened PoE Trade i reszta czytają twój schowek. Gdy gra "
                    "chodzi na maszynie w Warszawie, a ty siedzisz przed "
                    "przeglądarką, ten schowek nie jest twój. Boosteroid "
                    "synchronizuje go tylko w jedną stronę, więc nic nie wraca.",
    "problem_solution": "Ten program wyprowadza opis przedmiotu z sesji przez "
                        "dokument, który należy do ciebie, a potem pyta oficjalne "
                        "API rynku. Wciskasz jeden klawisz i widzisz cenę.",
    "how_title": "Trzy kroki, raz",
    "how_cloud_note": "Kroki 1 i 2 dotyczą tylko grania w chmurze (Boosteroid, "
                      "GeForce NOW). Na zwykłym PC możesz przejść od razu do "
                      "kroku 3 - kreator konfiguracji pyta o to na starcie i "
                      "całkowicie pomija most, jeśli nie grasz w chmurze.",
    "how_1_t": "Utwórz dokument-most",
    "how_1_b": "Zwykły dokument Google. Kreator przeprowadzi cię przez "
               "udostępnienie i sprawdzi, czy działa.",
    "how_2_t": "Wskaż go Steamowi",
    "how_2_b": "Ustaw skrót nakładki na F7, a dokument jako stronę startową "
               "przeglądarki. Kreator poda gotowy adres do skopiowania.",
    "how_3_t": "Wciśnij Ctrl+D w grze",
    "how_3_b": "Najedź na przedmiot, wciśnij skrót, przeczytaj cenę. Mody, tiery "
               "i filtry są na miejscu.",
    "features_title": "Co dostajesz",
    "f1_t": "Prawdziwe dopasowanie modów",
    "f1_b": "Każdy mod mapowany na oficjalną statystykę rynku, z tierami, zakresami "
            "i obsługą wariantów lokalnych. 99,7% słownika statystyk wraca "
            "poprawnie w teście.",
    "f2_t": "Sumy pseudo",
    "f2_b": "Łączna odporność żywiołowa, łączne życie, atrybuty - wyliczane i "
            "wyszukiwalne, tak jak wyceniają doświadczeni handlarze.",
    "f3_t": "Przeliczanie na diviny",
    "f3_b": "Ceny przeliczane po aktualnym kursie z oficjalnej giełdy wymiany, "
            "z odsianiem skrajnych ofert.",
    "f4_t": "Wszystko, nie tylko rzadkie",
    "f4_b": "Unikaty, rzadkie, magiczne, kamienie, flaszki, klejnoty, mapy - a "
            "waluta, karty i fragmenty przez giełdę wymiany.",
    "f5_t": "Windows i macOS",
    "f5_b": "Ten sam skrót i silnik dopasowania działają natywnie na obu - "
            "wsparcie macOS jest nowe i eksperymentalne, także na Apple Silicon.",
    "f6_t": "Jeden skrót, dwa tryby",
    "f6_b": "Przełącznik zmienia zachowanie głównego skrótu między mostem "
            "Boosteroid a lokalnym schowkiem - nie trzeba pamiętać dwóch "
            "różnych skrótów.",
    "privacy_title": "O twoich danych",
    "privacy_body": "Program wysyła anonimowy licznik: wersja, język, liga, liczba "
                    "wycen. Nigdy przedmiotów, cen, nazw kont ani twojego "
                    "dokumentu. Wyłączysz to jedną linijką w pliku konfiguracji.",
    "faq_title": "Pytania",
    "faq_1_q": "Czy to jest dozwolone?",
    "faq_1_a": "Czyta twój własny ekran i schowek oraz odpytuje publiczny serwis "
               "rynku - ta sama kategoria co każde inne narzędzie do wyceny. "
               "Nie ma tu żadnej automatyzacji rozgrywki.",
    "faq_2_q": "Czy działa poza Boosteroidem?",
    "faq_2_a": "Tak. Na zwykłym komputerze czyta schowek wprost, więc dokument-most "
               "w ogóle nie jest potrzebny - wciskasz sam skrót.",
    "faq_3_q": "Dlaczego Windows ostrzega?",
    "faq_3_a": "Plik nie jest podpisany cyfrowo, a program zakłada hook klawiatury, "
               "żeby złapać skrót w trakcie gry - heurystyki antywirusów nie lubią "
               "obu tych rzeczy. Kod źródłowy jest jawny, jeśli wolisz zbudować "
               "go samodzielnie.",
    "faq_4_q": "Która wersja PoE?",
    "faq_4_a": "Path of Exile 1. PoE 2 ma inne API rynku i nie jest jeszcze "
               "obsługiwane.",
    "faq_5_q": "Czy nie prościej użyć Awakened PoE Trade?",
    "faq_5_a": "Nie na Boosteroidzie ani żadnej innej chmurze - Awakened PoE Trade "
               "czyta lokalny schowek, a przy graniu w chmurze schowek "
               "synchronizuje się tylko w jedną stronę (lokalnie → chmura, "
               "nigdy z powrotem). To cały powód, dla którego to narzędzie "
               "istnieje: te same dane rynkowe, to samo oficjalne API, tylko "
               "tekst przedmiotu wyciągnięty z sesji chmurowej zamiast "
               "zakładania, że jest w schowku.",
    "faq_6_q": "Czy to działa też na GeForce NOW?",
    "faq_6_a": "Prawdopodobnie tam tego nie potrzebujesz - GeForce NOW "
               "synchronizuje schowek w obie strony, więc Awakened PoE Trade "
               "działa tam wprost. Most w tym narzędziu jest zrobiony pod "
               "usługi, gdzie schowek leci tylko w jedną stronę (lokalnie → "
               "chmura), jak Boosteroid. Grasz w innej usłudze chmurowej i "
               "nie wiesz, która to wersja? Skopiuj coś lokalnie i spróbuj "
               "wkleić w sesji chmurowej - jeśli się pojawi, tego narzędzia "
               "nie potrzebujesz.",
    "download_title": "Pobierz",
    "download_body": "Jeden plik. Uruchom, resztą zajmie się kreator.",
    "download_cta": "Pobierz na Windows",
    "download_mac_cta": "Pobierz na macOS",
    "download_mac_note": "Eksperymentalne i niepodpisane - macOS ostrzeże o "
                         "nieznanym deweloperze. Kliknij prawym na aplikację -> "
                         "Otwórz -> Otwórz (raz), żeby uruchomić. Szczegóły i "
                         "obecne ograniczenia są w README.",
    "download_alt": "Kod źródłowy",
    "discord_cta": "Wbij na Discorda",
    "discord_body": "Pytania, zgłoszenia błędów i informacje o nowych wersjach - na Discordzie złapiesz mnie najszybciej.",
    "footer_disclaimer": "This product isn't affiliated with or endorsed by Grinding "
                         "Gear Games in any way.",
    "footer_lang": "Język",
}

C["de"] = {
    "dir": "ltr",
    "shot_result_alt": "Das Ergebnisfenster mit dem geschätzten Wert, den zugeordneten Mods und aktuellen Angeboten",
    "shot_status_alt": "Das Hauptfenster mit laufendem Programm und den Tastenkürzeln",
    "eyebrow_problem": "Das Problem",
    "eyebrow_how": "Einrichtung",
    "eyebrow_features": "Funktionen",
    "eyebrow_faq": "Fragen",
    "title": "PoE Price Check für Boosteroid - Preisabfrage in der Cloud",
    "description": "Kostenlose Preisabfrage für Path of Exile beim Spielen über Boosteroid und andere Cloud-Dienste. Ein Tastenkürzel, aktuelle Marktpreise.",
    "keywords": "path of exile preisabfrage, poe price check, boosteroid, cloud "
                "gaming, poe trade, poe overlay",
    "skip": "Zum Inhalt springen",
    "nav_how": "So funktioniert es",
    "nav_features": "Funktionen",
    "nav_faq": "Fragen",
    "nav_download": "Herunterladen",
    "hero_badge": "Kostenlos · Quelloffen · Ohne Konto",
    "hero_title": "Preise prüfen in Path of Exile,\nauch wenn das Spiel in der Cloud läuft",
    "hero_lead": "Cloud-Gaming macht jedes Preis-Tool unbrauchbar, weil die "
                 "Zwischenablage nur in eine Richtung geht. Dieses funktioniert trotzdem.",
    "hero_cta": "Für Windows herunterladen",
    "hero_note": "Windows 10/11 · 16 MB · ohne Installer",
    "problem_title": "Warum die üblichen Tools scheitern",
    "problem_body": "Awakened PoE Trade und der Rest lesen deine Zwischenablage. Wenn "
                    "das Spiel auf einem Rechner in Warschau läuft und du vor einem "
                    "Browser sitzt, gehört diese Zwischenablage nicht dir. Boosteroid "
                    "überträgt sie nur in eine Richtung, es kommt nichts zurück.",
    "problem_solution": "Dieses Programm leitet den Gegenstandstext über ein Dokument "
                        "aus der Sitzung, das dir gehört, und fragt dann die "
                        "offizielle Handels-API. Eine Taste, ein Preis.",
    "how_title": "Drei Schritte, einmalig",
    "how_cloud_note": "Schritt 1 und 2 gelten nur für Cloud-Gaming "
                      "(Boosteroid, GeForce NOW). Auf einem normalen PC "
                      "kannst du direkt zu Schritt 3 springen - der "
                      "Einrichtungsassistent fragt das zu Beginn ab und "
                      "überspringt die Brücke komplett, wenn du nicht in der "
                      "Cloud spielst.",
    "how_1_t": "Brücken-Dokument anlegen",
    "how_1_b": "Ein gewöhnliches Google-Dokument. Der Assistent führt dich durch die "
               "Freigabe und prüft, ob es funktioniert.",
    "how_2_t": "Steam darauf zeigen lassen",
    "how_2_b": "Overlay-Kürzel auf F7, Dokument als Browser-Startseite. Der Assistent "
               "liefert die fertige Adresse zum Kopieren.",
    "how_3_t": "Im Spiel Strg+D drücken",
    "how_3_b": "Über den Gegenstand fahren, Taste drücken, Preis lesen. Mods, Tiers "
               "und Filter sind alle da.",
    "features_title": "Was du bekommst",
    "f1_t": "Echte Mod-Zuordnung",
    "f1_b": "Jeder Mod auf die offizielle Handelsstatistik abgebildet, mit Tiers, "
            "Spannen und korrekt behandelten lokalen Varianten. 99,7% des "
            "Statistik-Wörterbuchs laufen im Test sauber durch.",
    "f2_t": "Pseudo-Summen",
    "f2_b": "Gesamte Elementarresistenz, gesamtes Leben, Attribute - berechnet und "
            "durchsuchbar, so wie erfahrene Händler tatsächlich bepreisen.",
    "f3_t": "Umrechnung in Divine",
    "f3_b": "Preise umgerechnet zum aktuellen Kurs aus dem offiziellen Massenhandel, "
            "Ausreißer werden herausgefiltert.",
    "f4_t": "Alles, nicht nur Raritäten",
    "f4_b": "Uniques, Raritäten, magische Gegenstände, Gems, Fläschchen, Juwelen, "
            "Karten - Währung, Divinationskarten und Fragmente über den Massenhandel.",
    "f5_t": "Windows und macOS",
    "f5_b": "Derselbe Shortcut und dieselbe Abgleich-Engine laufen nativ auf "
            "beiden - die macOS-Unterstützung ist neu und experimentell, auch "
            "auf Apple Silicon.",
    "f6_t": "Ein Shortcut, zwei Modi",
    "f6_b": "Ein Schalter wechselt den Haupt-Shortcut zwischen der "
            "Boosteroid-Brücke und der lokalen Zwischenablage - kein Merken von "
            "zwei verschiedenen Tastenkürzeln nötig.",
    "privacy_title": "Zu deinen Daten",
    "privacy_body": "Das Programm sendet einen anonymen Zähler: Version, Sprache, "
                    "Liga, Anzahl der Abfragen. Niemals Gegenstände, Preise, "
                    "Kontonamen oder dein Dokument. Abschaltbar mit einer Zeile in "
                    "der Konfigurationsdatei.",
    "faq_title": "Fragen",
    "faq_1_q": "Ist das erlaubt?",
    "faq_1_a": "Es liest deinen eigenen Bildschirm und deine Zwischenablage und fragt "
               "die öffentliche Handelsseite ab - dieselbe Kategorie wie jedes andere "
               "Preis-Tool. Es gibt keinerlei Spielautomatisierung.",
    "faq_2_q": "Funktioniert es außerhalb von Boosteroid?",
    "faq_2_a": "Ja. Auf einem normalen PC wird die Zwischenablage direkt gelesen, das "
               "Brücken-Dokument entfällt komplett.",
    "faq_3_q": "Warum warnt mich Windows?",
    "faq_3_a": "Die Datei ist nicht signiert, und das Programm setzt einen "
               "Tastatur-Hook, um das Kürzel im Spiel abzufangen - beides mögen "
               "Virenscanner-Heuristiken nicht. Der Quellcode ist offen, falls du "
               "lieber selbst baust.",
    "faq_4_q": "Welche PoE-Version?",
    "faq_4_a": "Path of Exile 1. PoE 2 nutzt eine andere Handels-API und wird noch "
               "nicht unterstützt.",
    "faq_5_q": "Kann ich nicht einfach Awakened PoE Trade nutzen?",
    "faq_5_a": "Nicht bei Boosteroid oder einem anderen Cloud-Gaming-Dienst - "
               "Awakened PoE Trade liest die lokale Zwischenablage, und beim "
               "Cloud-Gaming wird die Zwischenablage nur in eine Richtung "
               "synchronisiert (lokal → Cloud, nie zurück). Genau deshalb gibt es "
               "dieses Tool: gleiche Handelsdaten, gleiche offizielle API, nur "
               "wird der Item-Text aus der Cloud-Sitzung geholt statt "
               "anzunehmen, dass er in der Zwischenablage steht.",
    "faq_6_q": "Funktioniert das auch mit GeForce NOW?",
    "faq_6_a": "Dort brauchst du es wahrscheinlich nicht - GeForce NOW "
               "synchronisiert die Zwischenablage in beide Richtungen, "
               "Awakened PoE Trade funktioniert dort also direkt. Der "
               "Brücken-Schritt dieses Tools ist für Dienste gedacht, bei "
               "denen die Zwischenablage nur in eine Richtung geht (lokal → "
               "Cloud), wie bei Boosteroid. Bist du auf einem anderen "
               "Cloud-Dienst und weißt nicht, welche Art das ist: kopiere "
               "lokal etwas und versuche es in der Cloud-Sitzung einzufügen "
               "- erscheint es dort, brauchst du dieses Tool nicht.",
    "download_title": "Holen",
    "download_body": "Eine Datei. Starten, den Rest macht der Assistent.",
    "download_cta": "Für Windows herunterladen",
    "download_mac_cta": "Für macOS herunterladen",
    "download_mac_note": "Experimentell und unsigniert - macOS warnt vor einem "
                         "nicht verifizierten Entwickler. Rechtsklick auf die App "
                         "-> Öffnen -> Öffnen (einmalig), um sie zu starten. "
                         "Details und aktuelle Einschränkungen stehen im README.",
    "download_alt": "Quellcode",
    "discord_cta": "Discord beitreten",
    "discord_body": "Fragen, Fehlermeldungen und Neuigkeiten zu neuen Versionen - über Discord erreichst du mich am schnellsten.",
    "footer_disclaimer": "This product isn't affiliated with or endorsed by Grinding "
                         "Gear Games in any way.",
    "footer_lang": "Sprache",
}

C["es"] = {
    "dir": "ltr",
    "shot_result_alt": "El panel de resultados con el valor estimado, los mods reconocidos y las ofertas actuales del mercado",
    "shot_status_alt": "La ventana principal con la aplicación en marcha y sus atajos de teclado",
    "eyebrow_problem": "El problema",
    "eyebrow_how": "Configuración",
    "eyebrow_features": "Funciones",
    "eyebrow_faq": "Preguntas",
    "title": "PoE Price Check para Boosteroid y juego en la nube",
    "description": "Consulta de precios gratuita para Path of Exile jugando por Boosteroid u otros servicios en la nube. Un atajo y precios reales del mercado.",
    "keywords": "path of exile precios, poe price check, boosteroid, juego en la nube, "
                "poe trade, poe overlay",
    "skip": "Saltar al contenido",
    "nav_how": "Cómo funciona",
    "nav_features": "Funciones",
    "nav_faq": "Preguntas",
    "nav_download": "Descargar",
    "hero_badge": "Gratis · Código abierto · Sin cuenta",
    "hero_title": "Consulta precios en Path of Exile,\naunque el juego corra en la nube",
    "hero_lead": "El juego en la nube rompe cualquier herramienta de precios, porque "
                 "el portapapeles solo viaja en un sentido. Esta funciona igual.",
    "hero_cta": "Descargar para Windows",
    "hero_note": "Windows 10/11 · 16 MB · sin instalador",
    "problem_title": "Por qué fallan las herramientas habituales",
    "problem_body": "Awakened PoE Trade y las demás leen tu portapapeles. Cuando el "
                    "juego corre en una máquina en Varsovia y tú estás frente a un "
                    "navegador, ese portapapeles no es tuyo. Boosteroid solo lo "
                    "sincroniza en un sentido, así que nunca vuelve nada.",
    "problem_solution": "Este programa saca el texto del objeto de la sesión a través "
                        "de un documento que es tuyo y luego consulta la API oficial "
                        "del mercado. Pulsas una tecla y ves el precio.",
    "how_title": "Tres pasos, una vez",
    "how_cloud_note": "Los pasos 1 y 2 son solo para juego en la nube "
                      "(Boosteroid, GeForce NOW). En un PC normal puedes ir "
                      "directo al paso 3 - el asistente de configuración lo "
                      "pregunta al principio y omite el puente por completo "
                      "si no juegas en la nube.",
    "how_1_t": "Crea un documento puente",
    "how_1_b": "Un documento de Google corriente. El asistente te guía para "
               "compartirlo y comprueba que funciona.",
    "how_2_t": "Apunta Steam hacia él",
    "how_2_b": "Pon el atajo de la superposición en F7 y el documento como página de "
               "inicio del navegador. El asistente te da la dirección lista.",
    "how_3_t": "Pulsa Ctrl+D en el juego",
    "how_3_b": "Pasa el ratón por el objeto, pulsa el atajo, lee el precio. Mods, "
               "tiers y filtros están todos ahí.",
    "features_title": "Qué obtienes",
    "f1_t": "Coincidencia real de mods",
    "f1_b": "Cada mod mapeado a la estadística oficial del mercado, con tiers, rangos "
            "y variantes locales bien tratadas. El 99,7% del diccionario de "
            "estadísticas vuelve correctamente en la prueba.",
    "f2_t": "Totales pseudo",
    "f2_b": "Resistencia elemental total, vida total, atributos - calculados y "
            "buscables, como realmente valoran los comerciantes con experiencia.",
    "f3_t": "Conversión a divine",
    "f3_b": "Precios convertidos con el cambio actual del intercambio masivo oficial, "
            "descartando ofertas atípicas.",
    "f4_t": "Todo, no solo raros",
    "f4_b": "Únicos, raros, mágicos, gemas, frascos, joyas, mapas - y moneda, cartas "
            "y fragmentos por el intercambio masivo.",
    "f5_t": "Windows y macOS",
    "f5_b": "El mismo atajo y el mismo motor de coincidencia funcionan de forma "
            "nativa en ambos - el soporte de macOS es nuevo y experimental, "
            "también en Apple Silicon.",
    "f6_t": "Un atajo, dos modos",
    "f6_b": "Un interruptor cambia el atajo principal entre el puente de "
            "Boosteroid y el portapapeles local - sin tener que recordar dos "
            "atajos distintos.",
    "privacy_title": "Sobre tus datos",
    "privacy_body": "El programa envía un contador anónimo: versión, idioma, liga y "
                    "número de consultas. Nunca objetos, precios, nombres de cuenta "
                    "ni tu documento. Se apaga con una línea del archivo de "
                    "configuración.",
    "faq_title": "Preguntas",
    "faq_1_q": "¿Está permitido?",
    "faq_1_a": "Lee tu propia pantalla y portapapeles y consulta el sitio público de "
               "comercio - la misma categoría que cualquier otra herramienta de "
               "precios. No hay ninguna automatización del juego.",
    "faq_2_q": "¿Funciona fuera de Boosteroid?",
    "faq_2_a": "Sí. En un PC normal lee el portapapeles directamente, así que el "
               "documento puente no hace falta en absoluto.",
    "faq_3_q": "¿Por qué me avisa Windows?",
    "faq_3_a": "El archivo no está firmado y el programa instala un hook de teclado "
               "para capturar el atajo durante el juego - a las heurísticas de "
               "antivirus no les gusta ninguna de las dos cosas. El código es "
               "público si prefieres compilarlo tú.",
    "faq_4_q": "¿Qué versión de PoE?",
    "faq_4_a": "Path of Exile 1. PoE 2 usa otra API de mercado y todavía no está "
               "soportado.",
    "faq_5_q": "¿No puedo simplemente usar Awakened PoE Trade?",
    "faq_5_a": "No en Boosteroid ni en ningún otro servicio de juego en la nube - "
               "Awakened PoE Trade lee el portapapeles local, y al jugar en la "
               "nube el portapapeles solo se sincroniza en un sentido (local → "
               "nube, nunca al revés). Por eso existe esta herramienta: los "
               "mismos datos de mercado, la misma API oficial, pero el texto del "
               "objeto se saca de la sesión en la nube en vez de asumir que está "
               "en el portapapeles.",
    "faq_6_q": "¿Esto funciona también en GeForce NOW?",
    "faq_6_a": "Ahí probablemente no lo necesites - GeForce NOW sincroniza el "
               "portapapeles en ambas direcciones, así que Awakened PoE Trade "
               "ya funciona directamente. El paso del puente de esta "
               "herramienta está pensado para servicios donde el "
               "portapapeles solo va en un sentido (local → nube), como "
               "Boosteroid. ¿Usas otro servicio en la nube y no sabes de qué "
               "tipo es? Copia algo localmente e intenta pegarlo dentro de "
               "la sesión en la nube - si aparece, no necesitas esta "
               "herramienta.",
    "download_title": "Descárgalo",
    "download_body": "Un archivo. Ejecútalo y el asistente hace el resto.",
    "download_cta": "Descargar para Windows",
    "download_mac_cta": "Descargar para macOS",
    "download_mac_note": "Experimental y sin firmar - macOS avisará sobre un "
                         "desarrollador no identificado. Clic derecho en la "
                         "app -> Abrir -> Abrir (una vez) para ejecutarla. Más "
                         "detalles y limitaciones actuales en el README.",
    "download_alt": "Código fuente",
    "discord_cta": "Únete al Discord",
    "discord_body": "Preguntas, informes de errores y novedades sobre nuevas versiones: en Discord me localizas más rápido.",
    "footer_disclaimer": "This product isn't affiliated with or endorsed by Grinding "
                         "Gear Games in any way.",
    "footer_lang": "Idioma",
}

C["pt"] = {
    "dir": "ltr",
    "shot_result_alt": "O painel de resultado com o valor estimado, os mods reconhecidos e as ofertas atuais do mercado",
    "shot_status_alt": "A janela principal com o programa rodando e seus atalhos de teclado",
    "eyebrow_problem": "O problema",
    "eyebrow_how": "Configuração",
    "eyebrow_features": "Recursos",
    "eyebrow_faq": "Perguntas",
    "title": "PoE Price Check para Boosteroid - preços de itens na nuvem",
    "description": "Consulta de preços gratuita para Path of Exile jogando pelo Boosteroid ou outros serviços em nuvem. Um atalho e preços reais do mercado.",
    "keywords": "path of exile preços, poe price check, boosteroid, jogo em nuvem, "
                "poe trade, poe overlay",
    "skip": "Ir para o conteúdo",
    "nav_how": "Como funciona",
    "nav_features": "Recursos",
    "nav_faq": "Perguntas",
    "nav_download": "Baixar",
    "hero_badge": "Grátis · Código aberto · Sem conta",
    "hero_title": "Consulte preços no Path of Exile,\nmesmo com o jogo rodando na nuvem",
    "hero_lead": "Jogar na nuvem quebra qualquer ferramenta de preços, porque a área "
                 "de transferência só vai numa direção. Esta funciona mesmo assim.",
    "hero_cta": "Baixar para Windows",
    "hero_note": "Windows 10/11 · 16 MB · sem instalador",
    "problem_title": "Por que as ferramentas comuns falham",
    "problem_body": "Awakened PoE Trade e as demais leem sua área de transferência. "
                    "Quando o jogo roda numa máquina em Varsóvia e você está diante "
                    "de um navegador, essa área não é sua. O Boosteroid só sincroniza "
                    "numa direção, então nada volta.",
    "problem_solution": "Este programa tira o texto do item da sessão por um documento "
                        "que é seu e depois consulta a API oficial do mercado. Você "
                        "aperta uma tecla e vê o preço.",
    "how_title": "Três passos, uma vez",
    "how_cloud_note": "Os passos 1 e 2 são apenas para jogo em nuvem "
                      "(Boosteroid, GeForce NOW). Em um PC normal, você pode "
                      "ir direto para o passo 3 - o assistente de "
                      "configuração pergunta isso logo no início e pula a "
                      "ponte por completo se você não jogar na nuvem.",
    "how_1_t": "Crie um documento ponte",
    "how_1_b": "Um documento comum do Google. O assistente orienta o "
               "compartilhamento e verifica se funciona.",
    "how_2_t": "Aponte a Steam para ele",
    "how_2_b": "Defina o atalho do overlay como F7 e o documento como página inicial "
               "do navegador. O assistente entrega o endereço pronto.",
    "how_3_t": "Aperte Ctrl+D no jogo",
    "how_3_b": "Passe o mouse no item, aperte o atalho, leia o preço. Mods, tiers e "
               "filtros estão todos lá.",
    "features_title": "O que você ganha",
    "f1_t": "Correspondência real de mods",
    "f1_b": "Cada mod mapeado para a estatística oficial do mercado, com tiers, "
            "faixas e variantes locais tratadas corretamente. 99,7% do dicionário "
            "de estatísticas volta certo no teste.",
    "f2_t": "Totais pseudo",
    "f2_b": "Resistência elemental total, vida total, atributos - calculados e "
            "pesquisáveis, do jeito que os traders experientes realmente precificam.",
    "f3_t": "Conversão para divine",
    "f3_b": "Preços convertidos pela cotação atual da troca em massa oficial, com "
            "ofertas fora da curva descartadas.",
    "f4_t": "Tudo, não só raros",
    "f4_b": "Únicos, raros, mágicos, gemas, frascos, joias, mapas - e moeda, cartas "
            "e fragmentos pela troca em massa.",
    "f5_t": "Windows e macOS",
    "f5_b": "O mesmo atalho e o mesmo mecanismo de correspondência rodam "
            "nativamente em ambos - o suporte a macOS é novo e experimental, "
            "incluindo Apple Silicon.",
    "f6_t": "Um atalho, dois modos",
    "f6_b": "Um alternador muda o atalho principal entre a ponte do Boosteroid "
            "e a área de transferência local - sem precisar lembrar dois "
            "atalhos diferentes.",
    "privacy_title": "Sobre seus dados",
    "privacy_body": "O programa envia um contador anônimo: versão, idioma, liga e "
                    "número de consultas. Nunca itens, preços, nomes de conta ou seu "
                    "documento. Dá para desligar com uma linha no arquivo de "
                    "configuração.",
    "faq_title": "Perguntas",
    "faq_1_q": "Isso é permitido?",
    "faq_1_a": "Ele lê a sua própria tela e área de transferência e consulta o site "
               "público de trade - a mesma categoria de qualquer outra ferramenta de "
               "preços. Não há nenhuma automação de jogabilidade.",
    "faq_2_q": "Funciona fora do Boosteroid?",
    "faq_2_a": "Sim. Num PC comum ele lê a área de transferência direto, então o "
               "documento ponte nem é necessário.",
    "faq_3_q": "Por que o Windows me avisa?",
    "faq_3_a": "O arquivo não é assinado e o programa instala um hook de teclado para "
               "capturar o atalho durante o jogo - as heurísticas de antivírus não "
               "gostam de nenhum dos dois. O código é aberto, se preferir compilar.",
    "faq_4_q": "Qual versão do PoE?",
    "faq_4_a": "Path of Exile 1. O PoE 2 usa outra API de mercado e ainda não é "
               "suportado.",
    "faq_5_q": "Não dá pra simplesmente usar o Awakened PoE Trade?",
    "faq_5_a": "Não no Boosteroid nem em outro serviço de jogo em nuvem - o "
               "Awakened PoE Trade lê a área de transferência local, e ao jogar "
               "na nuvem a área de transferência só sincroniza em um sentido "
               "(local → nuvem, nunca de volta). É exatamente por isso que essa "
               "ferramenta existe: os mesmos dados de mercado, a mesma API "
               "oficial, só que o texto do item é retirado da sessão na nuvem "
               "em vez de presumir que está na área de transferência.",
    "faq_6_q": "Isso funciona também no GeForce NOW?",
    "faq_6_a": "Ali você provavelmente não precisa dele - o GeForce NOW "
               "sincroniza a área de transferência nos dois sentidos, então "
               "o Awakened PoE Trade já funciona diretamente lá. A etapa de "
               "ponte desta ferramenta foi feita para serviços em que a "
               "área de transferência só vai em um sentido (local → nuvem), "
               "como o Boosteroid. Usa outro serviço em nuvem e não sabe "
               "qual é o tipo? Copie algo localmente e tente colar dentro "
               "da sessão na nuvem - se aparecer, você não precisa desta "
               "ferramenta.",
    "download_title": "Baixe",
    "download_body": "Um arquivo. Execute e o assistente faz o resto.",
    "download_cta": "Baixar para Windows",
    "download_mac_cta": "Baixar para macOS",
    "download_mac_note": "Experimental e sem assinatura - o macOS vai avisar "
                         "sobre um desenvolvedor não identificado. Clique com o "
                         "botão direito no app -> Abrir -> Abrir (uma vez) para "
                         "executar. Detalhes e limitações atuais no README.",
    "download_alt": "Código-fonte",
    "discord_cta": "Entre no Discord",
    "discord_body": "Dúvidas, relatos de erros e novidades sobre novas versões - no Discord você me encontra mais rápido.",
    "footer_disclaimer": "This product isn't affiliated with or endorsed by Grinding "
                         "Gear Games in any way.",
    "footer_lang": "Idioma",
}

C["ru"] = {
    "dir": "ltr",
    "shot_result_alt": "Окно результата с оценочной стоимостью, распознанными модами и актуальными предложениями рынка",
    "shot_status_alt": "Главное окно с работающей программой и списком сочетаний клавиш",
    "eyebrow_problem": "Проблема",
    "eyebrow_how": "Настройка",
    "eyebrow_features": "Возможности",
    "eyebrow_faq": "Вопросы",
    "title": "PoE Price Check для Boosteroid - оценка предметов в облаке",
    "description": "Бесплатная оценка предметов Path of Exile при игре через Boosteroid и другие облачные сервисы. Одно сочетание клавиш, актуальные цены рынка.",
    "keywords": "path of exile оценка, poe price check, boosteroid, облачный гейминг, "
                "poe trade, poe overlay",
    "skip": "Перейти к содержимому",
    "nav_how": "Как это работает",
    "nav_features": "Возможности",
    "nav_faq": "Вопросы",
    "nav_download": "Скачать",
    "hero_badge": "Бесплатно · Открытый код · Без аккаунта",
    "hero_title": "Оценивайте предметы в Path of Exile,\nдаже когда игра идёт в облаке",
    "hero_lead": "Облачный гейминг ломает любой инструмент оценки, потому что буфер "
                 "обмена передаёт данные только в одну сторону. Этот работает всё равно.",
    "hero_cta": "Скачать для Windows",
    "hero_note": "Windows 10/11 · 16 МБ · без установщика",
    "problem_title": "Почему обычные инструменты не работают",
    "problem_body": "Awakened PoE Trade и остальные читают ваш буфер обмена. Когда "
                    "игра идёт на машине в Варшаве, а вы сидите перед браузером, этот "
                    "буфер не ваш. Boosteroid синхронизирует его только в одну "
                    "сторону, поэтому ничего не возвращается.",
    "problem_solution": "Эта программа выводит описание предмета из сессии через "
                        "документ, который принадлежит вам, и затем обращается к "
                        "официальному API рынка. Нажимаете клавишу - видите цену.",
    "how_title": "Три шага, один раз",
    "how_cloud_note": "Шаги 1 и 2 нужны только для облачного гейминга "
                      "(Boosteroid, GeForce NOW). На обычном ПК можно сразу "
                      "переходить к шагу 3 - мастер настройки спрашивает об "
                      "этом в самом начале и полностью пропускает мост, если "
                      "вы не играете в облаке.",
    "how_1_t": "Создайте документ-мост",
    "how_1_b": "Обычный документ Google. Мастер настройки проведёт через открытие "
               "доступа и проверит, что всё работает.",
    "how_2_t": "Укажите его Steam",
    "how_2_b": "Поставьте сочетание оверлея на F7, а документ - домашней страницей "
               "браузера. Мастер даёт готовый адрес для копирования.",
    "how_3_t": "Нажмите Ctrl+D в игре",
    "how_3_b": "Наведите на предмет, нажмите сочетание, читайте цену. Моды, тиры и "
               "фильтры - всё на месте.",
    "features_title": "Что вы получаете",
    "f1_t": "Настоящее сопоставление модов",
    "f1_b": "Каждый мод сопоставлен с официальной статистикой рынка, с тирами, "
            "диапазонами и корректной обработкой локальных вариантов. 99,7% словаря "
            "статистик проходит проверку без ошибок.",
    "f2_t": "Псевдо-суммы",
    "f2_b": "Суммарное сопротивление стихиям, суммарное здоровье, атрибуты - "
            "вычисляются и ищутся так, как на самом деле оценивают опытные торговцы.",
    "f3_t": "Пересчёт в divine",
    "f3_b": "Цены пересчитываются по актуальному курсу с официальной биржи обмена, "
            "с отсевом выбросов.",
    "f4_t": "Всё, а не только редкие",
    "f4_b": "Уникальные, редкие, магические, камни, фляги, самоцветы, карты - а "
            "валюта, карты гадания и фрагменты через биржу обмена.",
    "f5_t": "Windows и macOS",
    "f5_b": "Тот же хоткей и тот же движок сопоставления работают нативно на "
            "обеих системах - поддержка macOS новая и экспериментальная, "
            "включая Apple Silicon.",
    "f6_t": "Один хоткей, два режима",
    "f6_b": "Переключатель меняет поведение основного хоткея между мостом "
            "Boosteroid и локальным буфером обмена - не нужно запоминать два "
            "разных хоткея.",
    "privacy_title": "О ваших данных",
    "privacy_body": "Программа отправляет анонимный счётчик: версия, язык, лига и "
                    "число оценок. Никогда - предметы, цены, имена аккаунтов или ваш "
                    "документ. Отключается одной строкой в файле настроек.",
    "faq_title": "Вопросы",
    "faq_1_q": "Это разрешено?",
    "faq_1_a": "Программа читает ваш собственный экран и буфер обмена и обращается к "
               "публичному сайту торговли - та же категория, что и любой другой "
               "инструмент оценки. Никакой автоматизации игрового процесса нет.",
    "faq_2_q": "Работает ли вне Boosteroid?",
    "faq_2_a": "Да. На обычном ПК буфер обмена читается напрямую, поэтому "
               "документ-мост вообще не нужен.",
    "faq_3_q": "Почему Windows предупреждает?",
    "faq_3_a": "Файл не подписан цифровой подписью, а программа ставит клавиатурный "
               "хук, чтобы поймать сочетание во время игры - эвристики антивирусов не "
               "любят ни то, ни другое. Исходный код открыт, если предпочитаете "
               "собрать сами.",
    "faq_4_q": "Какая версия PoE?",
    "faq_4_a": "Path of Exile 1. PoE 2 использует другое API рынка и пока не "
               "поддерживается.",
    "faq_5_q": "Разве нельзя просто использовать Awakened PoE Trade?",
    "faq_5_a": "Не на Boosteroid и не на других облачных сервисах - Awakened PoE "
               "Trade читает локальный буфер обмена, а при облачном гейминге "
               "буфер обмена синхронизируется только в одну сторону (локально → "
               "облако, никогда обратно). Именно поэтому существует этот "
               "инструмент: те же торговые данные, тот же официальный API, но "
               "текст предмета берётся из облачной сессии, а не из "
               "предположения, что он в буфере обмена.",
    "faq_6_q": "Работает ли это с GeForce NOW?",
    "faq_6_a": "Там это, скорее всего, не нужно - GeForce NOW синхронизирует "
               "буфер обмена в обе стороны, поэтому Awakened PoE Trade там "
               "уже работает напрямую. Мост в этом инструменте сделан для "
               "сервисов, где буфер обмена идёт только в одну сторону "
               "(локально → облако), как в Boosteroid. Играете в другом "
               "облачном сервисе и не знаете, какой у него тип? Скопируйте "
               "что-нибудь локально и попробуйте вставить внутри облачной "
               "сессии - если появилось, этот инструмент вам не нужен.",
    "download_title": "Скачать",
    "download_body": "Один файл. Запустите - остальное сделает мастер.",
    "download_cta": "Скачать для Windows",
    "download_mac_cta": "Скачать для macOS",
    "download_mac_note": "Экспериментально и без подписи - macOS предупредит о "
                         "неопознанном разработчике. Правый клик по приложению "
                         "-> Открыть -> Открыть (один раз), чтобы запустить. "
                         "Подробности и текущие ограничения - в README.",
    "download_alt": "Исходный код",
    "discord_cta": "Зайти в Discord",
    "discord_body": "Вопросы, сообщения об ошибках и новости о новых версиях - в Discord ответ придёт быстрее всего.",
    "footer_disclaimer": "This product isn't affiliated with or endorsed by Grinding "
                         "Gear Games in any way.",
    "footer_lang": "Язык",
}
