"""Tlumaczenia interfejsu.

Jeden slownik na jezyk. Dodanie kolejnego to skopiowanie bloku i przetlumaczenie
wartosci - klucze musza zostac te same. Brakujacy klucz spada na angielski,
wiec niepelne tlumaczenie nie psuje aplikacji.

Tlumaczenia poza angielskim i polskim warto dac do przejrzenia komus, kto uzywa
danego jezyka na co dzien - sa poprawne, ale moga brzmiec sztywno.
"""

import ctypes

DEFAULT = "en"

LANGUAGES = {
    "en": "English",
    "pl": "Polski",
    "de": "Deutsch",
    "es": "Español",
    "pt": "Português (BR)",
    "ru": "Русский",
}

# Kod jezyka Windows (pierwsze 2 znaki) -> nasz kod.
_WINDOWS_HINTS = {"pl": "pl", "de": "de", "es": "es", "pt": "pt", "ru": "ru",
                  "uk": "ru", "be": "ru"}

STRINGS: dict[str, dict[str, str]] = {}

STRINGS["en"] = {
    # okno glowne
    "app.running": "Running",
    "app.league_bridge": "league {league}  ·  bridge ready",
    "app.checks": "checks this session",
    "app.price_check": "price check an item",
    "app.other_hotkeys": "OTHER SHORTCUTS",
    "app.hk_clipboard": "price check clipboard",
    "app.hk_close": "close result window",
    "app.hk_quit": "quit the program",
    "app.minimise": "You can minimise this -\nshortcuts keep working.",
    "app.quit": "Quit",

    # kreator
    "setup.title": "PoE Price Check - setup",
    "setup.language": "Language",
    "setup.step_of": "Step {n} of 2",
    "setup.next": "Next",
    "setup.back": "Back",
    "setup.finish": "Save and start",
    "setup.p1_title": "The bridge document",
    "setup.p1_intro": "The game runs in the cloud and Boosteroid's clipboard only "
                      "travels one way. To get an item's text out of it you need a "
                      "middleman: an ordinary Google Doc.",
    "setup.p1_s1": "Create an empty Google Doc",
    "setup.p1_s1_note": "In the document click Share → General access → "
                        "“Anyone with the link”, and set the role to EDITOR.",
    "setup.p1_s1_why": "Without edit rights the cloud session cannot write the item "
                       "into it.",
    "setup.p1_s1_btn": "Open docs.new",
    "setup.p1_s2": "Paste the document link here",
    "setup.verify": "Check",
    "setup.st_bad_link": "That does not look like a Google Docs link.",
    "setup.st_checking": "Checking…",
    "setup.st_failed": "Could not connect: {error}",
    "setup.st_ok": "The document is reachable. You can continue.",
    "setup.st_need_link": "Paste the document link first.",
    "setup.p2_title": "Steam overlay in Boosteroid",
    "setup.p2_intro": "The program sends a key sequence into the session that pastes "
                      "the item into your document. Steam needs two settings for it "
                      "to work.",
    "setup.p2_s1": "Change the overlay shortcut to F7",
    "setup.p2_s1_note": "Steam → Settings → In Game → “Steam Overlay shortcut keys” "
                        "→ set F7.",
    "setup.p2_s1_why": "Shift+Tab sent programmatically does not get through "
                       "Boosteroid. F7 does - that is the only reason for this change.",
    "setup.p2_s2": "Set the document as the browser home page",
    "setup.p2_s2_note": "Steam → Settings → In Game → “Web browser home page” → "
                        "paste the address below.",
    "setup.p2_copy": "Copy",
    "setup.p2_copied": "Copied to clipboard.",
    "setup.p2_s3": "In game: open the overlay and click the document",
    "setup.p2_s3_note": "Enter the game, press F7 - the document should open. Click "
                        "once inside its text so the caret sits there.",
    "setup.p2_s3_why": "The sequence pastes wherever the caret is. Without that click "
                       "the first price check goes nowhere.",

    # okno wyniku
    "res.value": "ESTIMATED VALUE",
    "res.no_offers": "no offers",
    "res.loosen": "try loosening the filters",
    "res.mods": "Mods",
    "res.props": "Properties",
    "res.show_hidden": "show {n} hidden mods",
    "res.collapse": "collapse again",
    "res.still_filtering": "{n} still filtering",
    "res.not_tradeable": "not in trade",
    "res.search_again": "Search again",
    "res.wider": "Wider -10%",
    "res.all": "All",
    "res.none": "None",
    "res.error": "Something went wrong",
    "res.stale": "This is the previous item - the bridge document did not change. "
                 "The key sequence never reached the cloud.",
    "res.no_match": "Nobody has listed an item with this set of mods. Untick the mods "
                    "that do not matter and search again.",
    "res.open_trade": "Open on pathofexile.com/trade  →",
    "res.exchange": "bulk exchange",
    "res.offers": "{n} offers",
    "res.rate_wait": "Path of Exile limits how often you may search - {n} s left",

    # kolumny
    "col.price": "Price",
    "col.div": "≈div",
    "col.ilvl": "iLvl",
    "col.quality": "Q%",
    "col.account": "Account",
    "col.age": "Listed",

    # suwaki wlasciwosci
    "prop.ilvl": "Item level",
    "prop.links": "Links",

    # afiksy
    "craft.can_modify": "Can be modified",
    "craft.full": "All affixes used",
    "craft.corrupted": "Corrupted - cannot be modified",
    "craft.mirrored": "Mirrored - cannot be modified",
    "craft.free": "free",
    "craft.prefixes": "prefixes",
    "craft.suffixes": "suffixes",
    "craft.prefix": "prefix",
    "craft.suffix": "suffix",

    # wycena
    "sum.no_data": "not enough data to estimate",
    "sum.range": "range",
    "sum.converted": "converted {done}/{total}",
    "sum.in_currency": "from {done}/{total} offers in this currency",

    # bledy
    "err.bridge_empty": "The bridge document is empty. Check that it is open in the "
                        "Steam overlay browser in your Boosteroid session and that "
                        "the caret is inside the text.",
    "err.clipboard_empty": "The local clipboard is empty.",
    "err.item_unknown": "Cannot recognise this item: {error}",
}

STRINGS["pl"] = {
    "app.running": "Działa",
    "app.league_bridge": "liga {league}  ·  most gotowy",
    "app.checks": "wycen w tej sesji",
    "app.price_check": "wyceń przedmiot",
    "app.other_hotkeys": "POZOSTAŁE SKRÓTY",
    "app.hk_clipboard": "wyceń zawartość schowka",
    "app.hk_close": "zamknij okno wyniku",
    "app.hk_quit": "zakończ program",
    "app.minimise": "Możesz zminimalizować -\nskróty działają w tle.",
    "app.quit": "Zakończ",

    "setup.title": "PoE Price Check - konfiguracja",
    "setup.language": "Język",
    "setup.step_of": "Krok {n} z 2",
    "setup.next": "Dalej",
    "setup.back": "Wstecz",
    "setup.finish": "Zapisz i uruchom",
    "setup.p1_title": "Dokument-most",
    "setup.p1_intro": "Gra działa w chmurze, a schowek Boosteroida przesyła dane "
                      "tylko w jedną stronę. Żeby wydostać z niej opis przedmiotu, "
                      "potrzebny jest pośrednik: zwykły dokument Google.",
    "setup.p1_s1": "Utwórz pusty dokument Google",
    "setup.p1_s1_note": "W dokumencie kliknij Udostępnij → Dostęp ogólny → "
                        "„Każdy użytkownik, który ma link”, a rolę ustaw na EDYTUJĄCY.",
    "setup.p1_s1_why": "Bez prawa edycji sesja w chmurze nie zapisze do niego "
                       "przedmiotu.",
    "setup.p1_s1_btn": "Otwórz docs.new",
    "setup.p1_s2": "Wklej tutaj link do dokumentu",
    "setup.verify": "Sprawdź",
    "setup.st_bad_link": "To nie wygląda na link do dokumentu Google.",
    "setup.st_checking": "Sprawdzam…",
    "setup.st_failed": "Nie udało się połączyć: {error}",
    "setup.st_ok": "Dokument jest dostępny. Możesz przejść dalej.",
    "setup.st_need_link": "Najpierw wklej link do dokumentu.",
    "setup.p2_title": "Nakładka Steam w Boosteroidzie",
    "setup.p2_intro": "Program wysyła do sesji sekwencję klawiszy, która wkleja "
                      "przedmiot do dokumentu. Żeby zadziałała, Steam musi być "
                      "ustawiony w dwóch miejscach.",
    "setup.p2_s1": "Zmień skrót nakładki na F7",
    "setup.p2_s1_note": "Steam → Ustawienia → W grze → „Skrót klawiszowy nakładki "
                        "Steam” → ustaw F7.",
    "setup.p2_s1_why": "Shift+Tab wysłany programowo nie przechodzi przez "
                       "Boosteroida. F7 przechodzi - to jedyny powód tej zmiany.",
    "setup.p2_s2": "Ustaw dokument jako stronę startową przeglądarki",
    "setup.p2_s2_note": "Steam → Ustawienia → W grze → „Strona startowa przeglądarki "
                        "internetowej” → wklej poniższy adres.",
    "setup.p2_copy": "Kopiuj",
    "setup.p2_copied": "Skopiowano do schowka.",
    "setup.p2_s3": "W grze: otwórz nakładkę i kliknij w dokument",
    "setup.p2_s3_note": "Wejdź do gry, wciśnij F7 - powinien otworzyć się dokument. "
                        "Kliknij raz w jego treść, żeby kursor stał w tekście.",
    "setup.p2_s3_why": "Sekwencja wkleja tam, gdzie stoi kursor. Bez tego kliknięcia "
                       "pierwsza wycena trafi w próżnię.",

    "res.value": "SZACOWANA WARTOŚĆ",
    "res.no_offers": "brak ofert",
    "res.loosen": "spróbuj poluzować filtry",
    "res.mods": "Mody",
    "res.props": "Właściwości",
    "res.show_hidden": "pokaż {n} ukrytych modów",
    "res.collapse": "zwiń z powrotem",
    "res.still_filtering": "{n} nadal filtruje",
    "res.not_tradeable": "brak w trade",
    "res.search_again": "Szukaj ponownie",
    "res.wider": "Szeroki -10%",
    "res.all": "Wszystkie",
    "res.none": "Żadne",
    "res.error": "Coś poszło nie tak",
    "res.stale": "To poprzedni przedmiot - dokument-most się nie zmienił. "
                 "Sekwencja klawiszy nie doszła do chmury.",
    "res.no_match": "Nikt nie wystawił przedmiotu z takim zestawem. Odznacz mody, "
                    "które nie mają znaczenia, i szukaj ponownie.",
    "res.open_trade": "Otwórz na pathofexile.com/trade  →",
    "res.exchange": "giełda wymiany",
    "res.offers": "{n} ofert",
    "res.rate_wait": "Path of Exile ogranicza częstotliwość wyszukiwań - jeszcze {n} s",

    "col.price": "Cena",
    "col.div": "≈div",
    "col.ilvl": "iLvl",
    "col.quality": "Q%",
    "col.account": "Konto",
    "col.age": "Wyst.",

    "prop.ilvl": "Poziom przedmiotu",
    "prop.links": "Linki",

    "craft.can_modify": "Można modyfikować",
    "craft.full": "Pełne afiksy",
    "craft.corrupted": "Skorumpowany - nie do modyfikacji",
    "craft.mirrored": "Skopiowany - nie do modyfikacji",
    "craft.free": "wolne",
    "craft.prefixes": "prefiksów",
    "craft.suffixes": "sufiksów",
    "craft.prefix": "prefiks",
    "craft.suffix": "sufiks",

    "sum.no_data": "brak danych do oszacowania",
    "sum.range": "zakres",
    "sum.converted": "przeliczono {done}/{total}",
    "sum.in_currency": "z {done}/{total} ofert w tej walucie",

    "err.bridge_empty": "Dokument-most jest pusty. Sprawdź, czy w sesji Boosteroida "
                        "masz go otwartego w przeglądarce Steam Overlay i czy kursor "
                        "stoi w treści dokumentu.",
    "err.clipboard_empty": "Lokalny schowek jest pusty.",
    "err.item_unknown": "Nie rozpoznaję przedmiotu: {error}",
}

STRINGS["de"] = {
    "app.running": "Läuft",
    "app.league_bridge": "Liga {league}  ·  Brücke bereit",
    "app.checks": "Prüfungen in dieser Sitzung",
    "app.price_check": "Gegenstand prüfen",
    "app.other_hotkeys": "WEITERE TASTENKÜRZEL",
    "app.hk_clipboard": "Zwischenablage prüfen",
    "app.hk_close": "Ergebnisfenster schließen",
    "app.hk_quit": "Programm beenden",
    "app.minimise": "Du kannst minimieren -\ndie Tastenkürzel laufen weiter.",
    "app.quit": "Beenden",

    "setup.title": "PoE Price Check - Einrichtung",
    "setup.language": "Sprache",
    "setup.step_of": "Schritt {n} von 2",
    "setup.next": "Weiter",
    "setup.back": "Zurück",
    "setup.finish": "Speichern und starten",
    "setup.p1_title": "Das Brücken-Dokument",
    "setup.p1_intro": "Das Spiel läuft in der Cloud und die Zwischenablage von "
                      "Boosteroid überträgt nur in eine Richtung. Um den Text eines "
                      "Gegenstands herauszubekommen, braucht es einen Vermittler: "
                      "ein gewöhnliches Google-Dokument.",
    "setup.p1_s1": "Erstelle ein leeres Google-Dokument",
    "setup.p1_s1_note": "Klicke im Dokument auf Freigeben → Allgemeiner Zugriff → "
                        "„Jeder mit dem Link“ und setze die Rolle auf BEARBEITER.",
    "setup.p1_s1_why": "Ohne Bearbeitungsrecht kann die Cloud-Sitzung den Gegenstand "
                       "nicht hineinschreiben.",
    "setup.p1_s1_btn": "docs.new öffnen",
    "setup.p1_s2": "Füge hier den Link zum Dokument ein",
    "setup.verify": "Prüfen",
    "setup.st_bad_link": "Das sieht nicht nach einem Google-Docs-Link aus.",
    "setup.st_checking": "Prüfe…",
    "setup.st_failed": "Verbindung fehlgeschlagen: {error}",
    "setup.st_ok": "Das Dokument ist erreichbar. Du kannst fortfahren.",
    "setup.st_need_link": "Füge zuerst den Link zum Dokument ein.",
    "setup.p2_title": "Steam-Overlay in Boosteroid",
    "setup.p2_intro": "Das Programm sendet eine Tastenfolge in die Sitzung, die den "
                      "Gegenstand in dein Dokument einfügt. Damit das klappt, muss "
                      "Steam an zwei Stellen eingestellt werden.",
    "setup.p2_s1": "Ändere das Overlay-Kürzel auf F7",
    "setup.p2_s1_note": "Steam → Einstellungen → Im Spiel → „Tastenkürzel für das "
                        "Steam-Overlay“ → auf F7 setzen.",
    "setup.p2_s1_why": "Programmatisch gesendetes Shift+Tab kommt durch Boosteroid "
                       "nicht durch. F7 schon - das ist der einzige Grund.",
    "setup.p2_s2": "Setze das Dokument als Startseite des Browsers",
    "setup.p2_s2_note": "Steam → Einstellungen → Im Spiel → „Startseite des "
                        "Webbrowsers“ → die Adresse unten einfügen.",
    "setup.p2_copy": "Kopieren",
    "setup.p2_copied": "In die Zwischenablage kopiert.",
    "setup.p2_s3": "Im Spiel: Overlay öffnen und ins Dokument klicken",
    "setup.p2_s3_note": "Starte das Spiel, drücke F7 - das Dokument sollte sich "
                        "öffnen. Klicke einmal in den Text, damit der Cursor dort steht.",
    "setup.p2_s3_why": "Die Tastenfolge fügt dort ein, wo der Cursor steht. Ohne "
                       "diesen Klick geht die erste Prüfung ins Leere.",

    "res.value": "GESCHÄTZTER WERT",
    "res.no_offers": "keine Angebote",
    "res.loosen": "versuche die Filter zu lockern",
    "res.mods": "Mods",
    "res.props": "Eigenschaften",
    "res.show_hidden": "{n} versteckte Mods anzeigen",
    "res.collapse": "wieder einklappen",
    "res.still_filtering": "{n} filtern weiterhin",
    "res.not_tradeable": "nicht im Handel",
    "res.search_again": "Erneut suchen",
    "res.wider": "Weiter -10%",
    "res.all": "Alle",
    "res.none": "Keine",
    "res.error": "Etwas ist schiefgelaufen",
    "res.stale": "Das ist der vorherige Gegenstand - das Brücken-Dokument hat sich "
                 "nicht geändert. Die Tastenfolge kam nicht in der Cloud an.",
    "res.no_match": "Niemand bietet einen Gegenstand mit diesen Mods an. Hake die "
                    "unwichtigen Mods ab und suche erneut.",
    "res.open_trade": "Auf pathofexile.com/trade öffnen  →",
    "res.exchange": "Massenhandel",
    "res.offers": "{n} Angebote",
    "res.rate_wait": "Path of Exile begrenzt die Suchhäufigkeit - noch {n} s",

    "col.price": "Preis",
    "col.div": "≈div",
    "col.ilvl": "iLvl",
    "col.quality": "Q%",
    "col.account": "Konto",
    "col.age": "Seit",

    "prop.ilvl": "Gegenstandsstufe",
    "prop.links": "Verbindungen",

    "craft.can_modify": "Kann verändert werden",
    "craft.full": "Alle Affixe belegt",
    "craft.corrupted": "Verderbt - nicht veränderbar",
    "craft.mirrored": "Gespiegelt - nicht veränderbar",
    "craft.free": "frei",
    "craft.prefixes": "Präfixe",
    "craft.suffixes": "Suffixe",
    "craft.prefix": "Präfix",
    "craft.suffix": "Suffix",

    "sum.no_data": "zu wenig Daten für eine Schätzung",
    "sum.range": "Spanne",
    "sum.converted": "{done}/{total} umgerechnet",
    "sum.in_currency": "aus {done}/{total} Angeboten in dieser Währung",

    "err.bridge_empty": "Das Brücken-Dokument ist leer. Prüfe, ob es im "
                        "Steam-Overlay-Browser deiner Boosteroid-Sitzung geöffnet ist "
                        "und der Cursor im Text steht.",
    "err.clipboard_empty": "Die lokale Zwischenablage ist leer.",
    "err.item_unknown": "Gegenstand nicht erkannt: {error}",
}

STRINGS["es"] = {
    "app.running": "Funcionando",
    "app.league_bridge": "liga {league}  ·  puente listo",
    "app.checks": "consultas en esta sesión",
    "app.price_check": "consultar objeto",
    "app.other_hotkeys": "OTROS ATAJOS",
    "app.hk_clipboard": "consultar portapapeles",
    "app.hk_close": "cerrar ventana de resultado",
    "app.hk_quit": "salir del programa",
    "app.minimise": "Puedes minimizar -\nlos atajos siguen activos.",
    "app.quit": "Salir",

    "setup.title": "PoE Price Check - configuración",
    "setup.language": "Idioma",
    "setup.step_of": "Paso {n} de 2",
    "setup.next": "Siguiente",
    "setup.back": "Atrás",
    "setup.finish": "Guardar e iniciar",
    "setup.p1_title": "El documento puente",
    "setup.p1_intro": "El juego corre en la nube y el portapapeles de Boosteroid solo "
                      "viaja en un sentido. Para sacar el texto de un objeto hace "
                      "falta un intermediario: un documento de Google corriente.",
    "setup.p1_s1": "Crea un documento de Google vacío",
    "setup.p1_s1_note": "En el documento pulsa Compartir → Acceso general → "
                        "«Cualquier persona con el enlace» y pon el rol en EDITOR.",
    "setup.p1_s1_why": "Sin permiso de edición la sesión en la nube no puede escribir "
                       "el objeto dentro.",
    "setup.p1_s1_btn": "Abrir docs.new",
    "setup.p1_s2": "Pega aquí el enlace del documento",
    "setup.verify": "Comprobar",
    "setup.st_bad_link": "Esto no parece un enlace de Google Docs.",
    "setup.st_checking": "Comprobando…",
    "setup.st_failed": "No se pudo conectar: {error}",
    "setup.st_ok": "El documento es accesible. Puedes continuar.",
    "setup.st_need_link": "Pega primero el enlace del documento.",
    "setup.p2_title": "Superposición de Steam en Boosteroid",
    "setup.p2_intro": "El programa envía a la sesión una secuencia de teclas que pega "
                      "el objeto en tu documento. Para que funcione, Steam necesita "
                      "dos ajustes.",
    "setup.p2_s1": "Cambia el atajo de la superposición a F7",
    "setup.p2_s1_note": "Steam → Configuración → En el juego → «Atajo de teclado de "
                        "la superposición» → pon F7.",
    "setup.p2_s1_why": "Shift+Tab enviado por software no atraviesa Boosteroid. F7 sí "
                       "- esa es la única razón de este cambio.",
    "setup.p2_s2": "Pon el documento como página de inicio del navegador",
    "setup.p2_s2_note": "Steam → Configuración → En el juego → «Página de inicio del "
                        "navegador web» → pega la dirección de abajo.",
    "setup.p2_copy": "Copiar",
    "setup.p2_copied": "Copiado al portapapeles.",
    "setup.p2_s3": "En el juego: abre la superposición y haz clic en el documento",
    "setup.p2_s3_note": "Entra al juego, pulsa F7 - debería abrirse el documento. Haz "
                        "clic una vez en su texto para que el cursor quede ahí.",
    "setup.p2_s3_why": "La secuencia pega donde esté el cursor. Sin ese clic la "
                       "primera consulta se pierde.",

    "res.value": "VALOR ESTIMADO",
    "res.no_offers": "sin ofertas",
    "res.loosen": "prueba a relajar los filtros",
    "res.mods": "Mods",
    "res.props": "Propiedades",
    "res.show_hidden": "mostrar {n} mods ocultos",
    "res.collapse": "volver a plegar",
    "res.still_filtering": "{n} siguen filtrando",
    "res.not_tradeable": "no está en trade",
    "res.search_again": "Buscar de nuevo",
    "res.wider": "Amplio -10%",
    "res.all": "Todos",
    "res.none": "Ninguno",
    "res.error": "Algo salió mal",
    "res.stale": "Este es el objeto anterior - el documento puente no cambió. La "
                 "secuencia de teclas no llegó a la nube.",
    "res.no_match": "Nadie ha publicado un objeto con este conjunto de mods. Desmarca "
                    "los que no importan y busca de nuevo.",
    "res.open_trade": "Abrir en pathofexile.com/trade  →",
    "res.exchange": "intercambio masivo",
    "res.offers": "{n} ofertas",
    "res.rate_wait": "Path of Exile limita la frecuencia de búsqueda - quedan {n} s",

    "col.price": "Precio",
    "col.div": "≈div",
    "col.ilvl": "iLvl",
    "col.quality": "Q%",
    "col.account": "Cuenta",
    "col.age": "Desde",

    "prop.ilvl": "Nivel del objeto",
    "prop.links": "Enlaces",

    "craft.can_modify": "Se puede modificar",
    "craft.full": "Todos los afijos ocupados",
    "craft.corrupted": "Corrupto - no se puede modificar",
    "craft.mirrored": "Reflejado - no se puede modificar",
    "craft.free": "libres",
    "craft.prefixes": "prefijos",
    "craft.suffixes": "sufijos",
    "craft.prefix": "prefijo",
    "craft.suffix": "sufijo",

    "sum.no_data": "faltan datos para estimar",
    "sum.range": "rango",
    "sum.converted": "convertidas {done}/{total}",
    "sum.in_currency": "de {done}/{total} ofertas en esta moneda",

    "err.bridge_empty": "El documento puente está vacío. Comprueba que esté abierto "
                        "en el navegador de la superposición de Steam en tu sesión de "
                        "Boosteroid y que el cursor esté dentro del texto.",
    "err.clipboard_empty": "El portapapeles local está vacío.",
    "err.item_unknown": "No reconozco este objeto: {error}",
}

STRINGS["pt"] = {
    "app.running": "Funcionando",
    "app.league_bridge": "liga {league}  ·  ponte pronta",
    "app.checks": "consultas nesta sessão",
    "app.price_check": "consultar item",
    "app.other_hotkeys": "OUTROS ATALHOS",
    "app.hk_clipboard": "consultar área de transferência",
    "app.hk_close": "fechar janela de resultado",
    "app.hk_quit": "encerrar o programa",
    "app.minimise": "Você pode minimizar -\nos atalhos continuam funcionando.",
    "app.quit": "Sair",

    "setup.title": "PoE Price Check - configuração",
    "setup.language": "Idioma",
    "setup.step_of": "Passo {n} de 2",
    "setup.next": "Avançar",
    "setup.back": "Voltar",
    "setup.finish": "Salvar e iniciar",
    "setup.p1_title": "O documento ponte",
    "setup.p1_intro": "O jogo roda na nuvem e a área de transferência do Boosteroid "
                      "só vai numa direção. Para tirar o texto de um item de lá é "
                      "preciso um intermediário: um documento comum do Google.",
    "setup.p1_s1": "Crie um documento do Google vazio",
    "setup.p1_s1_note": "No documento clique em Compartilhar → Acesso geral → "
                        "“Qualquer pessoa com o link” e defina o papel como EDITOR.",
    "setup.p1_s1_why": "Sem permissão de edição a sessão na nuvem não consegue "
                       "escrever o item nele.",
    "setup.p1_s1_btn": "Abrir docs.new",
    "setup.p1_s2": "Cole aqui o link do documento",
    "setup.verify": "Verificar",
    "setup.st_bad_link": "Isso não parece um link do Google Docs.",
    "setup.st_checking": "Verificando…",
    "setup.st_failed": "Não foi possível conectar: {error}",
    "setup.st_ok": "O documento está acessível. Você pode continuar.",
    "setup.st_need_link": "Cole primeiro o link do documento.",
    "setup.p2_title": "Overlay da Steam no Boosteroid",
    "setup.p2_intro": "O programa envia à sessão uma sequência de teclas que cola o "
                      "item no seu documento. Para funcionar, a Steam precisa de "
                      "dois ajustes.",
    "setup.p2_s1": "Mude o atalho do overlay para F7",
    "setup.p2_s1_note": "Steam → Configurações → No jogo → “Teclas de atalho do "
                        "overlay Steam” → defina F7.",
    "setup.p2_s1_why": "Shift+Tab enviado por software não passa pelo Boosteroid. F7 "
                       "passa - é o único motivo dessa mudança.",
    "setup.p2_s2": "Defina o documento como página inicial do navegador",
    "setup.p2_s2_note": "Steam → Configurações → No jogo → “Página inicial do "
                        "navegador” → cole o endereço abaixo.",
    "setup.p2_copy": "Copiar",
    "setup.p2_copied": "Copiado para a área de transferência.",
    "setup.p2_s3": "No jogo: abra o overlay e clique no documento",
    "setup.p2_s3_note": "Entre no jogo, pressione F7 - o documento deve abrir. Clique "
                        "uma vez no texto dele para o cursor ficar ali.",
    "setup.p2_s3_why": "A sequência cola onde o cursor estiver. Sem esse clique a "
                       "primeira consulta se perde.",

    "res.value": "VALOR ESTIMADO",
    "res.no_offers": "sem ofertas",
    "res.loosen": "tente afrouxar os filtros",
    "res.mods": "Mods",
    "res.props": "Propriedades",
    "res.show_hidden": "mostrar {n} mods ocultos",
    "res.collapse": "recolher de novo",
    "res.still_filtering": "{n} ainda filtrando",
    "res.not_tradeable": "não está no trade",
    "res.search_again": "Buscar de novo",
    "res.wider": "Amplo -10%",
    "res.all": "Todos",
    "res.none": "Nenhum",
    "res.error": "Algo deu errado",
    "res.stale": "Este é o item anterior - o documento ponte não mudou. A sequência "
                 "de teclas não chegou à nuvem.",
    "res.no_match": "Ninguém anunciou um item com esse conjunto de mods. Desmarque os "
                    "que não importam e busque de novo.",
    "res.open_trade": "Abrir em pathofexile.com/trade  →",
    "res.exchange": "troca em massa",
    "res.offers": "{n} ofertas",
    "res.rate_wait": "Path of Exile limita a frequência de busca - faltam {n} s",

    "col.price": "Preço",
    "col.div": "≈div",
    "col.ilvl": "iLvl",
    "col.quality": "Q%",
    "col.account": "Conta",
    "col.age": "Há",

    "prop.ilvl": "Nível do item",
    "prop.links": "Links",

    "craft.can_modify": "Pode ser modificado",
    "craft.full": "Todos os afixos ocupados",
    "craft.corrupted": "Corrompido - não pode ser modificado",
    "craft.mirrored": "Espelhado - não pode ser modificado",
    "craft.free": "livres",
    "craft.prefixes": "prefixos",
    "craft.suffixes": "sufixos",
    "craft.prefix": "prefixo",
    "craft.suffix": "sufixo",

    "sum.no_data": "dados insuficientes para estimar",
    "sum.range": "faixa",
    "sum.converted": "convertidas {done}/{total}",
    "sum.in_currency": "de {done}/{total} ofertas nesta moeda",

    "err.bridge_empty": "O documento ponte está vazio. Verifique se ele está aberto no "
                        "navegador do overlay da Steam na sua sessão do Boosteroid e "
                        "se o cursor está dentro do texto.",
    "err.clipboard_empty": "A área de transferência local está vazia.",
    "err.item_unknown": "Não reconheço este item: {error}",
}

STRINGS["ru"] = {
    "app.running": "Работает",
    "app.league_bridge": "лига {league}  ·  мост готов",
    "app.checks": "проверок за сессию",
    "app.price_check": "оценить предмет",
    "app.other_hotkeys": "ОСТАЛЬНЫЕ СОЧЕТАНИЯ",
    "app.hk_clipboard": "оценить из буфера обмена",
    "app.hk_close": "закрыть окно результата",
    "app.hk_quit": "выйти из программы",
    "app.minimise": "Можно свернуть -\nсочетания работают в фоне.",
    "app.quit": "Выход",

    "setup.title": "PoE Price Check - настройка",
    "setup.language": "Язык",
    "setup.step_of": "Шаг {n} из 2",
    "setup.next": "Далее",
    "setup.back": "Назад",
    "setup.finish": "Сохранить и запустить",
    "setup.p1_title": "Документ-мост",
    "setup.p1_intro": "Игра работает в облаке, а буфер обмена Boosteroid передаёт "
                      "данные только в одну сторону. Чтобы вытащить оттуда описание "
                      "предмета, нужен посредник: обычный документ Google.",
    "setup.p1_s1": "Создайте пустой документ Google",
    "setup.p1_s1_note": "В документе нажмите Настройки доступа → Общий доступ → "
                        "«Все, у кого есть ссылка», а роль поставьте РЕДАКТОР.",
    "setup.p1_s1_why": "Без права на редактирование облачная сессия не запишет туда "
                       "предмет.",
    "setup.p1_s1_btn": "Открыть docs.new",
    "setup.p1_s2": "Вставьте сюда ссылку на документ",
    "setup.verify": "Проверить",
    "setup.st_bad_link": "Это не похоже на ссылку Google Docs.",
    "setup.st_checking": "Проверяю…",
    "setup.st_failed": "Не удалось подключиться: {error}",
    "setup.st_ok": "Документ доступен. Можно продолжать.",
    "setup.st_need_link": "Сначала вставьте ссылку на документ.",
    "setup.p2_title": "Оверлей Steam в Boosteroid",
    "setup.p2_intro": "Программа отправляет в сессию последовательность клавиш, "
                      "которая вставляет предмет в документ. Чтобы это сработало, "
                      "Steam нужно настроить в двух местах.",
    "setup.p2_s1": "Смените сочетание оверлея на F7",
    "setup.p2_s1_note": "Steam → Настройки → В игре → «Сочетание клавиш оверлея "
                        "Steam» → установите F7.",
    "setup.p2_s1_why": "Shift+Tab, отправленный программно, не проходит через "
                       "Boosteroid. F7 проходит - это единственная причина замены.",
    "setup.p2_s2": "Сделайте документ домашней страницей браузера",
    "setup.p2_s2_note": "Steam → Настройки → В игре → «Домашняя страница браузера» → "
                        "вставьте адрес ниже.",
    "setup.p2_copy": "Копировать",
    "setup.p2_copied": "Скопировано в буфер обмена.",
    "setup.p2_s3": "В игре: откройте оверлей и щёлкните по документу",
    "setup.p2_s3_note": "Зайдите в игру, нажмите F7 - должен открыться документ. "
                        "Щёлкните один раз по тексту, чтобы курсор оказался там.",
    "setup.p2_s3_why": "Последовательность вставляет туда, где стоит курсор. Без "
                       "этого щелчка первая оценка уйдёт в пустоту.",

    "res.value": "ОЦЕНОЧНАЯ СТОИМОСТЬ",
    "res.no_offers": "нет предложений",
    "res.loosen": "попробуйте ослабить фильтры",
    "res.mods": "Моды",
    "res.props": "Свойства",
    "res.show_hidden": "показать {n} скрытых модов",
    "res.collapse": "свернуть обратно",
    "res.still_filtering": "{n} всё ещё фильтруют",
    "res.not_tradeable": "нет в trade",
    "res.search_again": "Искать снова",
    "res.wider": "Шире -10%",
    "res.all": "Все",
    "res.none": "Никакие",
    "res.error": "Что-то пошло не так",
    "res.stale": "Это предыдущий предмет - документ-мост не изменился. "
                 "Последовательность клавиш не дошла до облака.",
    "res.no_match": "Никто не выставил предмет с таким набором модов. Снимите "
                    "галочки с неважных и поищите снова.",
    "res.open_trade": "Открыть на pathofexile.com/trade  →",
    "res.exchange": "обмен валют",
    "res.offers": "{n} предложений",
    "res.rate_wait": "Path of Exile ограничивает частоту поиска - осталось {n} с",

    "col.price": "Цена",
    "col.div": "≈div",
    "col.ilvl": "iLvl",
    "col.quality": "Q%",
    "col.account": "Аккаунт",
    "col.age": "Выст.",

    "prop.ilvl": "Уровень предмета",
    "prop.links": "Связи",

    "craft.can_modify": "Можно модифицировать",
    "craft.full": "Все аффиксы заняты",
    "craft.corrupted": "Осквернён - модификация невозможна",
    "craft.mirrored": "Отражён - модификация невозможна",
    "craft.free": "свободно",
    "craft.prefixes": "префиксов",
    "craft.suffixes": "суффиксов",
    "craft.prefix": "префикс",
    "craft.suffix": "суффикс",

    "sum.no_data": "недостаточно данных для оценки",
    "sum.range": "диапазон",
    "sum.converted": "пересчитано {done}/{total}",
    "sum.in_currency": "из {done}/{total} предложений в этой валюте",

    "err.bridge_empty": "Документ-мост пуст. Проверьте, открыт ли он в браузере "
                        "оверлея Steam в вашей сессии Boosteroid и стоит ли курсор "
                        "внутри текста.",
    "err.clipboard_empty": "Локальный буфер обмена пуст.",
    "err.item_unknown": "Не распознаю предмет: {error}",
}

_current = DEFAULT


def detect_default() -> str:
    """Jezyk z ustawien Windows, z odwrotem na angielski."""
    try:
        code = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        buffer = ctypes.create_unicode_buffer(85)
        ctypes.windll.kernel32.LCIDToLocaleName(code, buffer, 85, 0)
        prefix = (buffer.value or "")[:2].lower()
        return _WINDOWS_HINTS.get(prefix, DEFAULT)
    except Exception:  # noqa: BLE001 - wykrycie jezyka nie moze psuc startu
        return DEFAULT


def set_language(code: str) -> None:
    global _current
    _current = code if code in STRINGS else DEFAULT


def current() -> str:
    return _current


def t(key: str, **kwargs) -> str:
    """Tlumaczenie klucza. Brak w danym jezyku spada na angielski, potem na klucz."""
    text = STRINGS.get(_current, {}).get(key) or STRINGS[DEFAULT].get(key) or key
    try:
        return text.format(**kwargs) if kwargs else text
    except (KeyError, IndexError):
        return text
