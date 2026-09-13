"""Teksty stron narzedzi we wszystkich jezykach strony.

Co tlumaczymy, a czego nie:
  - tlumaczymy interfejs, opisy, instrukcje i FAQ;
  - NIE tlumaczymy nazw modow, wlasciwosci, kategorii ani przedmiotow. Regex
    dopasowuje doslowny tekst angielskiego klienta gry, a ceny z poe.ninja maja
    angielskie nazwy - przetlumaczona etykieta nie zgadzalaby sie z tym, co
    gracz widzi w grze i w wyszukiwarce.

Klucze z koncowka _html sa wstawiane bez escapowania (zawieraja <b>, <code>).
Placeholdery {n}, {date} itp. musza byc identyczne w kazdym jezyku - check()
to sprawdza przy budowaniu.
"""

import re
import string

T: dict[str, dict[str, str]] = {}

T["en"] = {
    # --- wspolne ---
    "nav_home": "Price Checker",
    "nav_poe1": "PoE1 Regex",
    "nav_poe2": "PoE2 Regex",
    "nav_instill": "PoE2 Instill",
    "nav_economy": "Economy",
    "nav_aria": "Tools",
    "lang_aria": "Language",
    "skip": "Skip to content",
    "footer_cta": "price check items in Path of Exile 1 & 2, also on cloud gaming (Boosteroid).",
    "disclaimer": "Not affiliated with or endorsed by Grinding Gear Games.",
    "free_tool": "free tool",
    "faq": "FAQ",
    # --- regex: wspolne ---
    "your_regex": "Your regex",
    "copy": "Copy",
    "copied": "Copied",
    "copy_link": "Copy link",
    "link_in_bar": "Link is in the address bar",
    "clear": "Clear",
    "generated_aria": "Generated regex",
    "item_type_aria": "Item type",
    "mode_legend": "Wanted modifiers must match",
    "mode_legend_poe1": "Wanted modifiers (Vendor: stats) must match",
    "mode_any": "any of them",
    "mode_all": "all of them",
    "filter": "Filter modifiers…",
    "want": "Want",
    "avoid": "Avoid",
    "picked": "{want} wanted · {avoid} avoided",
    "also_title": "Also matches {n} longer modifier(s) containing this text",
    "min_values": "Minimum values",
    "modifiers": "Modifiers",
    "minimum_aria": "{label} minimum",
    "english_only": "Only works with the English game client.",
    "data_generated": "Modifier data generated {date}.",
    "how1_html": "<b>Quoted text is a pattern.</b> {code} highlights every item whose text contains it.",
    "how2_html": "<b>{bar} means “or”.</b> {code} matches either one.",
    "how3_html": "<b>A leading {bang} negates.</b> {code} hides items with any of them.",
    "how4_html": "<b>Space-separated patterns must all match.</b> {code} — {example}",
    # --- PoE2 regex ---
    "r2_title": "PoE2 Regex Builder — Waystones, Tablets & Vendor Search",
    "r2_desc": "Free Path of Exile 2 regex builder: generate stash and vendor search strings for "
               "Waystones, Precursor Tablets and vendor items within the 250 character limit.",
    "r2_h1": "PoE2 Regex Builder",
    "r2_lead": "Build stash and vendor search strings for Waystones, Precursor Tablets and vendor "
               "items. Pick what you want and what to avoid, copy, paste into the in-game search.",
    "tab_waystones": "Waystones",
    "tab_tablets": "Tablets",
    "tab_vendor": "Vendor",
    "r2_waystone_note_html": "{n} Waystone modifiers. <b>{want}</b> highlights maps that have them, "
                             "<b>{avoid}</b> hides maps with them.",
    "r2_tablet_note": "{n} Precursor Tablet modifiers.",
    "r2_vendor_note": "Tick the stats you are shopping for and set a minimum. Useful for levelling: "
                      "movement speed boots, +skill level weapons, resistances.",
    "r2_placeholder": "Pick modifiers to build a search string",
    "r2_paste": "Paste into the stash, vendor or map device search box.",
    "r2_how_title": "How PoE2 search regex works",
    "r2_how_example": "tier 15+ without the mod.",
    "r2_q1": "How do I use regex in Path of Exile 2?",
    "r2_a1": "Open your stash, a vendor window or the map device, click the search box, paste the "
             "generated text and matching items get highlighted. Everything in quotes is a regular "
             "expression; a leading ! means \"does not match\".",
    "r2_q2": "Why is there a 250 character limit?",
    "r2_a2": "The in-game search box accepts at most 250 characters. The builder uses the shortest "
             "fragment of each modifier that no other modifier contains, so you can fit many more "
             "mods into the limit than with full modifier texts.",
    "r2_q3": "Does it work with the game in another language?",
    "r2_a3": "No. Search matches the item text the client displays, and the modifier texts here are "
             "English. Switch the client to English or adapt the fragments.",
    "r2_q4": "Are the modifier lists up to date?",
    "r2_a4": "Waystone modifiers come from the game's own stat data and tablet modifiers from the "
             "official trade site's stat list, regenerated with each site update.",
    # --- PoE1 regex ---
    "r1_title": "PoE Regex Builder — Maps, Vendor, Heist Contracts & Logbooks",
    "r1_desc": "Free Path of Exile regex builder: rare map quantity and bad mods (T17 included), "
               "levelling vendor items with links and colours, Heist Contracts and Expedition "
               "Logbooks — with shareable links, within the 250 character limit.",
    "r1_h1": "PoE Regex Builder",
    "r1_lead": "Stash and vendor search strings for rare maps, levelling gear, Heist Contracts and "
               "Expedition Logbooks. Pick what you want and what your build cannot run, then copy "
               "the text or share the link.",
    "tab_maps": "Maps",
    "tab_heist": "Heist",
    "tab_logbooks": "Logbooks",
    "r1_maps_note_html": "{n} map modifier lines. <b>{want}</b> highlights maps that have them, "
                         "<b>{avoid}</b> hides maps with any of them.",
    "quick_avoid": "Quick avoid:",
    "quick_avoid_aria": "Quick avoid presets",
    "preset_count": "{n} modifier(s)",
    "preset_regen": "No regen",
    "preset_leech": "No leech",
    "preset_curses": "Curses",
    "preset_maxres": "Max res",
    "preset_thorns": "Thorns",
    "preset_block": "Block",
    "preset_flasks": "Flasks",
    "hide_t17": "Hide T17-only ({n})",
    "t17_title": "Only rolls on Tier 17 maps",
    "r1_vendor_note": "Levelling shopping list for vendors: tick the stats you want and set a minimum. "
                      "With “any of them” an item needs one ticked stat, with “all of them” every one.",
    "sockets": "Sockets",
    "linked_group": "Linked group",
    "linked_aria": "Linked sockets",
    "link_any": "Any",
    "link_n": "{n}-link",
    "red": "Red",
    "green": "Green",
    "blue": "Blue",
    "colour_aria": "{colour} sockets",
    "sockets_note": "Colours count inside one linked group, e.g. 3-link with 1 red, 1 green, 1 blue "
                    "finds any R-G-B order. Sockets always apply on top of the stats.",
    "stats": "Stats",
    "r1_heist_note": "Heist Contracts and Blueprints. Minimum values, rogue job levels and modifiers "
                     "all apply together.",
    "job_title": "Required job level",
    "job_note": "Highlights contracts that need the job at this level or higher — higher levels mean "
                "better rewards. Blueprints list several jobs; every ticked job must be on it.",
    "job_label": "{job} level",
    "r1_logbook_note": "Expedition Logbooks: pick the faction and area bonuses you want, avoid the "
                       "modifiers your build cannot run.",
    "factions": "Factions",
    "bonuses": "Area bonuses & bosses",
    "r1_placeholder": "Pick values or modifiers to build a search string",
    "r1_apply_note": "Minimum values and avoided modifiers always apply together. The link opens this "
                     "tab with the same picks.",
    "r1_how_title": "How the search works",
    "r1_how_example": "90%+ quantity without no regen.",
    "r1_q1": "How do I use a map regex in Path of Exile?",
    "r1_a1": "Open your stash or the map device, click the search box and paste the generated text. "
             "Maps that match are highlighted. Avoided modifiers use a leading ! so maps carrying any "
             "of them stay dark.",
    "r1_q2": "Which modifiers should I avoid?",
    "r1_a2": "It depends on the build. Common picks are \"Players cannot Regenerate\", the leech mods "
             "for leech-reliant builds, \"Players are Cursed with ...\", reduced maximum resistances "
             "and the Physical/Elemental Thorns mods for melee. The quick presets above the list tick "
             "those in one click.",
    "r1_q3": "Why do some fragments look strange, like \"ve .*% increased ar\"?",
    "r1_a3": "Each modifier gets the shortest piece of text that no other map modifier, map name or "
             "map property contains. When both halves around a number also appear in other modifiers, "
             "the fragment spans the number with .* — the in-game search supports it.",
    "r1_q4": "Does it cover Tier 17 maps?",
    "r1_a4": "Yes. Modifiers that only roll on Tier 17 maps are marked T17 and can be hidden from the "
             "list. Thresholds also cover the More Maps / More Scarabs / More Currency lines and the "
             "map conversion chances.",
    "r1_q5": "Is the list checked against real maps?",
    "r1_a5": "Every fragment was tested on rare Tier 14–17 maps listed on the official trade site: each "
             "modifier line matched its own fragment and no fragment matched another line. Heist "
             "Contracts, Blueprints and Expedition Logbooks were checked the same way.",
    "r1_q6": "How do I share my regex?",
    "r1_a6": "Click Copy link. The link opens the same tab with the same thresholds and modifiers "
             "picked, so a guild mate can paste it straight into their stash search.",
    "r1_q7": "How does the vendor socket search work?",
    "r1_a7": "Pick a linked group size and the colours you need. The builder writes every colour order "
             "for one linked group (R-G-B, G-R-B, ...), so a 3-link with red, green and blue is found "
             "however the sockets are ordered.",
    "r1_q8": "Which Expedition Logbook bonuses can I search for?",
    "r1_a8": "The four factions, the area bonuses such as artifact quantity, explosive radius, remnants "
             "and chest markers, and the logbook bosses. Modifiers work like map modifiers.",
    # --- Instill ---
    "in_title": "PoE2 Instilling Calculator — Distilled Emotions Anoint List",
    "in_desc": "All {n} Path of Exile 2 instill recipes: which Distilled Emotions in which order "
               "allocate each notable on your amulet, searchable by name and effect.",
    "in_h1": "PoE2 Instilling Calculator",
    "in_lead": "Which three Distilled Emotions allocate which notable on your amulet — and which notable "
               "your emotions make. Order matters: the same emotions in a different order give a "
               "different notable.",
    "in_make": "What do my emotions make?",
    "in_slot": "Slot {n}",
    "in_slot_aria": "Emotion in slot {n}",
    "in_pick": "Pick an emotion for each slot.",
    "in_none": "No notable uses these three emotions in this order. Try another order — each order is "
               "a different recipe.",
    "in_find": "Find a notable",
    "in_search": "Search by name or effect — e.g. chaos, charm, freeze",
    "in_search_aria": "Search notables",
    "in_owned": "Only recipes I can make with",
    "in_owned_aria": "Emotions you have",
    "in_tiers": "Emotion tiers:",
    "in_count": "{n} notables",
    "in_count_of": "{shown} of {n} notables",
    "in_recipe_aria": "Recipe: {list}",
    "in_data": "Data generated {date}.",
    "in_q1": "How does instilling an amulet work in Path of Exile 2?",
    "in_a1": "Three Distilled Emotions are placed on an amulet and it gains an enchantment that "
             "allocates one notable passive skill, even if it is not connected on your tree. This "
             "calculator lists every notable with the emotions it needs.",
    "in_q2": "Does the order of the emotions matter?",
    "in_a2": "Yes. The same three emotions in a different order give a different notable — for example "
             "Isolation, Ire, Disgust allocates Void, while Ire, Disgust, Isolation allocates Revenge. "
             "Recipes here are shown in slot order.",
    "in_q3": "Where does this data come from?",
    "in_a3": "Recipes come from the game's own data (via Exiled Exchange 2) and notable descriptions "
             "from the game's passive tree and stat descriptions (via RePoE), regenerated with each "
             "site update.",
    # --- Economy ---
    "ec_poe2_title": "PoE2 Economy — Currency, Runes & Essence Prices",
    "ec_poe2_desc": "Live Path of Exile 2 prices: Divine and Exalted Orb rates, runes, essences, soul "
                    "cores, uncut gems — with 24h, 7 day and 30 day change.",
    "ec_poe1_title": "PoE Economy — Currency, Unique & Scarab Prices",
    "ec_poe1_desc": "Live Path of Exile prices: Divine Orb rate, unique items, scarabs, essences, "
                    "divination cards — with 24h, 7 day and 30 day change and league price history.",
    "ec_live": "live prices",
    "ec_h1": "{game} Economy",
    "ec_lead_poe1": "Currency, unique item prices for the current league, with price changes over the "
                    "last day, week and month — click a row for its price history.",
    "ec_lead_poe2": "Currency and consumable prices for the current league, with price changes over "
                    "the last day, week and month — click a row for its price history.",
    "ec_game_aria": "Game",
    "ec_league": "League",
    "ec_loading_leagues": "Loading…",
    "ec_search": "Search all items by name…",
    "ec_hide_low": "Hide low confidence",
    "ec_category_aria": "Category",
    "ec_col_item": "Item",
    "ec_col_value": "Value",
    "ec_col_volume": "Volume",
    "ec_col_listed": "Listed",
    "ec_col_vol_listed": "Volume / Listed",
    "ec_col_spark": "Last 7 days",
    "ec_loading": "Loading prices…",
    "ec_source_html": "Prices from {link}, refreshed every 30 minutes.",
    "ec_history_loading": "Loading price history…",
    "ec_history_short": "Not enough price history for this item yet.",
    "ec_history_error": "Price history is unavailable right now.",
    "ec_now": "Now",
    "ec_low": "League low",
    "ec_high": "League high",
    "ec_since": "Since {date}",
    "ec_show_table": "Show data table",
    "ec_day": "Day",
    "ec_price_unit": "Price ({unit})",
    "ec_chart_aria": "Price history, {n} days, from {from} to {to} {unit}",
    "ec_low_tag": "low confidence",
    "ec_results": "{n} results",
    "ec_no_results": "No results",
    "ec_for_query": "for “{q}” across all categories",
    "ec_top": "(showing top {n})",
    "ec_searching": "searching {loaded}/{total} categories…",
    "ec_click_row": "click a row for price history",
    "ec_items": "{n} items",
    "ec_updated": "updated {time}",
    "ec_prices_error": "Prices are unavailable right now. Try again in a few minutes.",
    "ec_leagues_error": "League list is unavailable right now. Try again in a few minutes.",
    "ec_q1": "Where do these prices come from?",
    "ec_a1": "From poe.ninja, which aggregates the currency exchange and public stash tabs. Prices "
             "refresh every 30 minutes.",
    "ec_q2": "What do the 24h, 7d and 30d columns mean?",
    "ec_a2": "The price change over the last day, week and month. 24h and 7d come from poe.ninja's "
             "price history; 30d comes from daily snapshots this site keeps, so it fills in during the "
             "first month of a league.",
    "ec_q3": "Do I need to know which category an item is in?",
    "ec_a3": "No. Type at least two letters of any item name in the search box and the results come "
             "from every category at once, each marked with its category.",
    "ec_q4": "Can I see how a price changed over the league?",
    "ec_a4": "Yes — click any row to open its price history for the whole league, with the league low, "
             "high and the change since the league started.",
    "ec_q5": "What does \"low confidence\" mean for unique items?",
    "ec_a5": "The price is based on fewer than 10 listings, so it can be far off. Those items are hidden "
             "by default; untick \"Hide low confidence\" to see them. Unique prices are only available "
             "for Path of Exile 1 — Path of Exile 2 has no public stash data.",
    "ec_q6": "How do I price a rare item?",
    "ec_a6": "Currency-style items are here. For rares and uniques use the free PoE Price Check app — it "
             "reads the item under your cursor and searches the official trade site.",
}

T["pl"] = {
    "nav_home": "Price Checker",
    "nav_poe1": "PoE1 Regex",
    "nav_poe2": "PoE2 Regex",
    "nav_instill": "PoE2 Instill",
    "nav_economy": "Ekonomia",
    "nav_aria": "Narzędzia",
    "lang_aria": "Język",
    "skip": "Przejdź do treści",
    "footer_cta": "wycena przedmiotów w Path of Exile 1 i 2, także w chmurze (Boosteroid).",
    "disclaimer": "Projekt niezwiązany z Grinding Gear Games i przez nich niepopierany.",
    "free_tool": "darmowe narzędzie",
    "faq": "Najczęstsze pytania",
    "your_regex": "Twój regex",
    "copy": "Kopiuj",
    "copied": "Skopiowano",
    "copy_link": "Kopiuj link",
    "link_in_bar": "Link jest w pasku adresu",
    "clear": "Wyczyść",
    "generated_aria": "Wygenerowany regex",
    "item_type_aria": "Rodzaj przedmiotu",
    "mode_legend": "Pożądane mody muszą pasować",
    "mode_legend_poe1": "Pożądane mody (Vendor: statystyki) muszą pasować",
    "mode_any": "dowolny z nich",
    "mode_all": "wszystkie",
    "filter": "Filtruj mody…",
    "want": "Chcę",
    "avoid": "Omijaj",
    "picked": "chcę: {want} · omijam: {avoid}",
    "also_title": "Trafia też {n} dłuższych modów zawierających ten tekst",
    "min_values": "Wartości minimalne",
    "modifiers": "Mody",
    "minimum_aria": "{label} – minimum",
    "english_only": "Działa tylko z angielskim klientem gry.",
    "data_generated": "Dane modów wygenerowane {date}.",
    "how1_html": "<b>Tekst w cudzysłowie to wzorzec.</b> {code} podświetla każdy przedmiot, którego tekst go zawiera.",
    "how2_html": "<b>{bar} oznacza „lub”.</b> {code} pasuje do jednego albo drugiego.",
    "how3_html": "<b>{bang} na początku to zaprzeczenie.</b> {code} ukrywa przedmioty z którymkolwiek z nich.",
    "how4_html": "<b>Wzorce oddzielone spacją muszą pasować wszystkie.</b> {code} — {example}",
    "r2_title": "Regex PoE2 — kreator wyszukiwania Waystone, Tablet i vendora",
    "r2_desc": "Darmowy kreator regexów do Path of Exile 2: teksty wyszukiwania w skrytce i u vendora "
               "dla Waystone, Precursor Tablet i przedmiotów u sprzedawcy, w limicie 250 znaków.",
    "r2_h1": "Kreator regexów PoE2",
    "r2_lead": "Składaj teksty wyszukiwania do skrytki i vendora dla Waystone, Precursor Tablet i "
               "przedmiotów u sprzedawcy. Wybierz, czego chcesz i czego unikasz, skopiuj i wklej w grze.",
    "tab_waystones": "Waystones",
    "tab_tablets": "Tablets",
    "tab_vendor": "Vendor",
    "r2_waystone_note_html": "{n} modów Waystone. <b>{want}</b> podświetla mapy, które je mają, "
                             "<b>{avoid}</b> ukrywa mapy z nimi.",
    "r2_tablet_note": "{n} modów Precursor Tablet.",
    "r2_vendor_note": "Zaznacz statystyki, których szukasz, i ustaw minimum. Przydatne przy levelowaniu: "
                      "buty z szybkością ruchu, bronie z +poziomem umiejętności, odporności.",
    "r2_placeholder": "Wybierz mody, aby złożyć tekst wyszukiwania",
    "r2_paste": "Wklej w pole wyszukiwania skrytki, vendora albo urządzenia map.",
    "r2_how_title": "Jak działa regex w wyszukiwarce PoE2",
    "r2_how_example": "tier 15+ bez tego moda.",
    "r2_q1": "Jak używać regexu w Path of Exile 2?",
    "r2_a1": "Otwórz skrytkę, okno vendora albo urządzenie map, kliknij pole wyszukiwania i wklej "
             "wygenerowany tekst — pasujące przedmioty zostaną podświetlone. Wszystko w cudzysłowie to "
             "wyrażenie regularne; ! na początku oznacza „nie pasuje”.",
    "r2_q2": "Skąd limit 250 znaków?",
    "r2_a2": "Pole wyszukiwania w grze przyjmuje najwyżej 250 znaków. Kreator używa najkrótszego "
             "fragmentu każdego moda, którego nie zawiera żaden inny mod, więc zmieścisz dużo więcej "
             "modów niż z pełnymi tekstami.",
    "r2_q3": "Czy działa z grą w innym języku?",
    "r2_a3": "Nie. Wyszukiwarka dopasowuje tekst wyświetlany przez klienta, a teksty modów są tu po "
             "angielsku. Przełącz klienta na angielski albo dostosuj fragmenty.",
    "r2_q4": "Czy listy modów są aktualne?",
    "r2_a4": "Mody Waystone pochodzą z danych statystyk samej gry, a mody Tablet z listy statystyk "
             "oficjalnej strony trade — generujemy je od nowa przy każdej aktualizacji strony.",
    "r1_title": "Regex PoE — mapy, vendor, kontrakty Heist i Logbooki",
    "r1_desc": "Darmowy kreator regexów do Path of Exile: quantity i złe mody na rzadkich mapach "
               "(z T17), przedmioty u vendora przy levelowaniu z linkami i kolorami, kontrakty Heist i "
               "Expedition Logbooki — z linkiem do udostępnienia, w limicie 250 znaków.",
    "r1_h1": "Kreator regexów PoE",
    "r1_lead": "Teksty wyszukiwania do skrytki i vendora dla rzadkich map, sprzętu przy levelowaniu, "
               "kontraktów Heist i Expedition Logbooków. Wybierz, czego chcesz i czego Twój build nie "
               "udźwignie, a potem skopiuj tekst albo udostępnij link.",
    "tab_maps": "Mapy",
    "tab_heist": "Heist",
    "tab_logbooks": "Logbooki",
    "r1_maps_note_html": "{n} linii modów map. <b>{want}</b> podświetla mapy, które je mają, "
                         "<b>{avoid}</b> ukrywa mapy z którymkolwiek z nich.",
    "quick_avoid": "Szybko omijaj:",
    "quick_avoid_aria": "Gotowe zestawy do omijania",
    "preset_count": "modów: {n}",
    "preset_regen": "Brak regeneracji",
    "preset_leech": "Brak leecha",
    "preset_curses": "Klątwy",
    "preset_maxres": "Max odporności",
    "preset_thorns": "Ciernie",
    "preset_block": "Blok",
    "preset_flasks": "Flaszki",
    "hide_t17": "Ukryj tylko-T17 ({n})",
    "t17_title": "Wypada tylko na mapach Tier 17",
    "r1_vendor_note": "Lista zakupów u vendora przy levelowaniu: zaznacz statystyki i ustaw minimum. "
                      "Przy „dowolny z nich” przedmiot potrzebuje jednej zaznaczonej, przy „wszystkie” — każdej.",
    "sockets": "Gniazda",
    "linked_group": "Połączona grupa",
    "linked_aria": "Połączone gniazda",
    "link_any": "Dowolna",
    "link_n": "{n}-link",
    "red": "Czerwone",
    "green": "Zielone",
    "blue": "Niebieskie",
    "colour_aria": "{colour} gniazda",
    "sockets_note": "Kolory liczą się w jednej połączonej grupie, np. 3-link z 1 czerwonym, 1 zielonym i "
                    "1 niebieskim znajdzie każdą kolejność R-G-B. Gniazda zawsze obowiązują oprócz statystyk.",
    "stats": "Statystyki",
    "r1_heist_note": "Kontrakty i Blueprinty Heist. Wartości minimalne, poziomy profesji i mody "
                     "obowiązują jednocześnie.",
    "job_title": "Wymagany poziom profesji",
    "job_note": "Podświetla kontrakty wymagające profesji na tym poziomie lub wyższym — wyższy poziom "
                "to lepsze nagrody. Blueprinty wymieniają kilka profesji; każda zaznaczona musi się na nim znaleźć.",
    "job_label": "{job} – poziom",
    "r1_logbook_note": "Expedition Logbooki: wybierz frakcję i bonusy obszarów, których chcesz, omijaj "
                       "mody, których Twój build nie udźwignie.",
    "factions": "Frakcje",
    "bonuses": "Bonusy obszarów i bossowie",
    "r1_placeholder": "Wybierz wartości lub mody, aby złożyć tekst wyszukiwania",
    "r1_apply_note": "Wartości minimalne i omijane mody zawsze obowiązują razem. Link otwiera tę "
                     "zakładkę z tymi samymi wyborami.",
    "r1_how_title": "Jak działa wyszukiwarka",
    "r1_how_example": "quantity 90%+ bez braku regeneracji.",
    "r1_q1": "Jak używać regexu do map w Path of Exile?",
    "r1_a1": "Otwórz skrytkę albo urządzenie map, kliknij pole wyszukiwania i wklej wygenerowany tekst. "
             "Pasujące mapy zostaną podświetlone. Omijane mody mają ! na początku, więc mapy z "
             "którymkolwiek z nich pozostają ciemne.",
    "r1_q2": "Których modów unikać?",
    "r1_a2": "Zależy od buildu. Najczęściej omijane to „Players cannot Regenerate”, mody na leech dla "
             "buildów opartych na leechu, „Players are Cursed with ...”, obniżone maksymalne odporności "
             "i mody Physical/Elemental Thorns dla postaci walczących wręcz. Gotowe zestawy nad listą "
             "zaznaczają je jednym kliknięciem.",
    "r1_q3": "Czemu niektóre fragmenty wyglądają dziwnie, np. „ve .*% increased ar”?",
    "r1_a3": "Każdy mod dostaje najkrótszy kawałek tekstu, którego nie zawiera żaden inny mod map, nazwa "
             "mapy ani jej właściwość. Gdy obie części wokół liczby występują też w innych modach, "
             "fragment przechodzi przez liczbę za pomocą .* — wyszukiwarka w grze to obsługuje.",
    "r1_q4": "Czy obejmuje mapy Tier 17?",
    "r1_a4": "Tak. Mody wypadające tylko na mapach Tier 17 mają oznaczenie T17 i można je ukryć. Progi "
             "obejmują też linie More Maps / More Scarabs / More Currency i szanse zamiany map.",
    "r1_q5": "Czy lista jest sprawdzona na prawdziwych mapach?",
    "r1_a5": "Każdy fragment przetestowaliśmy na rzadkich mapach Tier 14–17 z oficjalnej strony trade: "
             "każda linia moda trafiała swój fragment i żaden fragment nie trafiał innej linii. Kontrakty "
             "i Blueprinty Heist oraz Expedition Logbooki sprawdziliśmy tak samo.",
    "r1_q6": "Jak udostępnić swój regex?",
    "r1_a6": "Kliknij „Kopiuj link”. Link otwiera tę samą zakładkę z tymi samymi progami i modami, więc "
             "znajomy z gildii wklei go od razu do swojej skrytki.",
    "r1_q7": "Jak działa wyszukiwanie gniazd u vendora?",
    "r1_a7": "Wybierz wielkość połączonej grupy i potrzebne kolory. Kreator wypisuje każdą kolejność "
             "kolorów w jednej grupie (R-G-B, G-R-B, ...), więc 3-link z czerwonym, zielonym i niebieskim "
             "znajdzie się niezależnie od ułożenia gniazd.",
    "r1_q8": "Jakich bonusów Expedition Logbooka mogę szukać?",
    "r1_a8": "Czterech frakcji, bonusów obszarów, takich jak ilość artefaktów, zasięg eksplozji, remnanty "
             "i znaczniki skrzyń, oraz bossów logbooka. Mody działają jak mody map.",
    "in_title": "Kalkulator Instill PoE2 — lista Distilled Emotions do amuletu",
    "in_desc": "Wszystkie {n} przepisy instill w Path of Exile 2: które Distilled Emotions i w jakiej "
               "kolejności dają dany notable na amulecie, z wyszukiwaniem po nazwie i efekcie.",
    "in_h1": "Kalkulator Instill PoE2",
    "in_lead": "Które trzy Distilled Emotions dają który notable na amulecie — i jaki notable zrobisz ze "
               "swoich emocji. Kolejność ma znaczenie: te same emocje w innej kolejności dają inny notable.",
    "in_make": "Co zrobię ze swoich emocji?",
    "in_slot": "Slot {n}",
    "in_slot_aria": "Emocja w slocie {n}",
    "in_pick": "Wybierz emocję dla każdego slotu.",
    "in_none": "Żaden notable nie używa tych trzech emocji w tej kolejności. Spróbuj innej kolejności — "
               "każda to inny przepis.",
    "in_find": "Znajdź notable",
    "in_search": "Szukaj po nazwie lub efekcie — np. chaos, charm, freeze",
    "in_search_aria": "Szukaj notable",
    "in_owned": "Tylko przepisy, które zrobię z",
    "in_owned_aria": "Posiadane emocje",
    "in_tiers": "Poziomy emocji:",
    "in_count": "notable: {n}",
    "in_count_of": "{shown} z {n} notable",
    "in_recipe_aria": "Przepis: {list}",
    "in_data": "Dane wygenerowane {date}.",
    "in_q1": "Jak działa instill amuletu w Path of Exile 2?",
    "in_a1": "Na amulecie umieszczasz trzy Distilled Emotions, a on dostaje enchant, który przydziela "
             "jeden notable z drzewka pasywnego, nawet jeśli nie jest połączony z Twoim drzewkiem. "
             "Kalkulator pokazuje każdy notable z potrzebnymi emocjami.",
    "in_q2": "Czy kolejność emocji ma znaczenie?",
    "in_a2": "Tak. Te same trzy emocje w innej kolejności dają inny notable — np. Isolation, Ire, "
             "Disgust daje Void, a Ire, Disgust, Isolation daje Revenge. Przepisy są pokazane w kolejności slotów.",
    "in_q3": "Skąd pochodzą dane?",
    "in_a3": "Przepisy pochodzą z danych gry (przez Exiled Exchange 2), a opisy notable z drzewka "
             "pasywnego i opisów statystyk gry (przez RePoE) — generujemy je od nowa przy każdej "
             "aktualizacji strony.",
    "ec_poe2_title": "Ekonomia PoE2 — ceny walut, run i esencji",
    "ec_poe2_desc": "Aktualne ceny w Path of Exile 2: kurs Divine i Exalted Orb, runy, esencje, soul "
                    "cores, uncut gems — ze zmianą z 24 godzin, 7 i 30 dni.",
    "ec_poe1_title": "Ekonomia PoE — ceny walut, unikatów i skarabeuszy",
    "ec_poe1_desc": "Aktualne ceny w Path of Exile: kurs Divine Orb, unikaty, skarabeusze, esencje, karty "
                    "dywinacyjne — ze zmianą z 24 godzin, 7 i 30 dni oraz historią ceny z ligi.",
    "ec_live": "aktualne ceny",
    "ec_h1": "Ekonomia {game}",
    "ec_lead_poe1": "Ceny walut i unikatów w bieżącej lidze ze zmianą z ostatniego dnia, tygodnia i "
                    "miesiąca — kliknij wiersz, aby zobaczyć historię ceny.",
    "ec_lead_poe2": "Ceny walut i materiałów w bieżącej lidze ze zmianą z ostatniego dnia, tygodnia i "
                    "miesiąca — kliknij wiersz, aby zobaczyć historię ceny.",
    "ec_game_aria": "Gra",
    "ec_league": "Liga",
    "ec_loading_leagues": "Wczytywanie…",
    "ec_search": "Szukaj przedmiotów po nazwie…",
    "ec_hide_low": "Ukryj niepewne ceny",
    "ec_category_aria": "Kategoria",
    "ec_col_item": "Przedmiot",
    "ec_col_value": "Wartość",
    "ec_col_volume": "Obrót",
    "ec_col_listed": "Ofert",
    "ec_col_vol_listed": "Obrót / ofert",
    "ec_col_spark": "Ostatnie 7 dni",
    "ec_loading": "Wczytywanie cen…",
    "ec_source_html": "Ceny z {link}, odświeżane co 30 minut.",
    "ec_history_loading": "Wczytywanie historii ceny…",
    "ec_history_short": "Za mało historii ceny dla tego przedmiotu.",
    "ec_history_error": "Historia ceny jest teraz niedostępna.",
    "ec_now": "Teraz",
    "ec_low": "Minimum ligi",
    "ec_high": "Maksimum ligi",
    "ec_since": "Od {date}",
    "ec_show_table": "Pokaż tabelę danych",
    "ec_day": "Dzień",
    "ec_price_unit": "Cena ({unit})",
    "ec_chart_aria": "Historia ceny, dni: {n}, od {from} do {to} {unit}",
    "ec_low_tag": "niepewna cena",
    "ec_results": "wyników: {n}",
    "ec_no_results": "Brak wyników",
    "ec_for_query": "dla „{q}” we wszystkich kategoriach",
    "ec_top": "(pokazuję pierwsze {n})",
    "ec_searching": "przeszukuję kategorie {loaded}/{total}…",
    "ec_click_row": "kliknij wiersz, aby zobaczyć historię ceny",
    "ec_items": "przedmiotów: {n}",
    "ec_updated": "aktualizacja {time}",
    "ec_prices_error": "Ceny są teraz niedostępne. Spróbuj za kilka minut.",
    "ec_leagues_error": "Lista lig jest teraz niedostępna. Spróbuj za kilka minut.",
    "ec_q1": "Skąd pochodzą te ceny?",
    "ec_a1": "Z poe.ninja, które zbiera dane z giełdy walut i publicznych zakładek skrytek. Ceny "
             "odświeżają się co 30 minut.",
    "ec_q2": "Co oznaczają kolumny 24h, 7d i 30d?",
    "ec_a2": "Zmianę ceny z ostatniego dnia, tygodnia i miesiąca. 24h i 7d pochodzą z historii cen "
             "poe.ninja; 30d z codziennych zapisów tej strony, więc uzupełnia się w pierwszym miesiącu ligi.",
    "ec_q3": "Czy muszę wiedzieć, w jakiej kategorii jest przedmiot?",
    "ec_a3": "Nie. Wpisz co najmniej dwie litery nazwy przedmiotu, a wyniki przyjdą ze wszystkich "
             "kategorii naraz, każdy z oznaczeniem kategorii.",
    "ec_q4": "Czy zobaczę, jak zmieniała się cena w lidze?",
    "ec_a4": "Tak — kliknij dowolny wiersz, aby otworzyć historię ceny z całej ligi z minimum, maksimum i "
             "zmianą od startu ligi.",
    "ec_q5": "Co oznacza „niepewna cena” przy unikatach?",
    "ec_a5": "Cena opiera się na mniej niż 10 ofertach, więc może być daleka od prawdy. Takie przedmioty są "
             "domyślnie ukryte; odznacz „Ukryj niepewne ceny”, aby je zobaczyć. Ceny unikatów są dostępne "
             "tylko dla Path of Exile 1 — Path of Exile 2 nie ma publicznych danych skrytek.",
    "ec_q6": "Jak wycenić rzadki przedmiot?",
    "ec_a6": "Tutaj są przedmioty walutowe. Rzadkie i unikatowe przedmioty wyceń darmową aplikacją PoE "
             "Price Check — czyta przedmiot pod kursorem i szuka na oficjalnej stronie trade.",
}

T["de"] = {
    "nav_home": "Price Checker",
    "nav_poe1": "PoE1 Regex",
    "nav_poe2": "PoE2 Regex",
    "nav_instill": "PoE2 Instill",
    "nav_economy": "Wirtschaft",
    "nav_aria": "Werkzeuge",
    "lang_aria": "Sprache",
    "skip": "Zum Inhalt springen",
    "footer_cta": "Preise für Items in Path of Exile 1 & 2 prüfen, auch beim Cloud-Gaming (Boosteroid).",
    "disclaimer": "Nicht mit Grinding Gear Games verbunden oder von ihnen unterstützt.",
    "free_tool": "kostenloses Tool",
    "faq": "Häufige Fragen",
    "your_regex": "Dein Regex",
    "copy": "Kopieren",
    "copied": "Kopiert",
    "copy_link": "Link kopieren",
    "link_in_bar": "Link steht in der Adresszeile",
    "clear": "Leeren",
    "generated_aria": "Erzeugter Regex",
    "item_type_aria": "Item-Art",
    "mode_legend": "Gewünschte Mods müssen passen",
    "mode_legend_poe1": "Gewünschte Mods (Vendor: Werte) müssen passen",
    "mode_any": "einer davon",
    "mode_all": "alle",
    "filter": "Mods filtern…",
    "want": "Will",
    "avoid": "Meiden",
    "picked": "{want} gewünscht · {avoid} gemieden",
    "also_title": "Trifft auch {n} längere Mod(s), die diesen Text enthalten",
    "min_values": "Mindestwerte",
    "modifiers": "Mods",
    "minimum_aria": "{label} Minimum",
    "english_only": "Funktioniert nur mit dem englischen Spielclient.",
    "data_generated": "Mod-Daten erzeugt am {date}.",
    "how1_html": "<b>Text in Anführungszeichen ist ein Muster.</b> {code} hebt jedes Item hervor, dessen Text es enthält.",
    "how2_html": "<b>{bar} bedeutet „oder“.</b> {code} passt auf das eine oder andere.",
    "how3_html": "<b>Ein vorangestelltes {bang} verneint.</b> {code} blendet Items mit einem davon aus.",
    "how4_html": "<b>Durch Leerzeichen getrennte Muster müssen alle passen.</b> {code} — {example}",
    "r2_title": "PoE2 Regex Builder — Suche für Waystones, Tablets & Händler",
    "r2_desc": "Kostenloser Regex Builder für Path of Exile 2: Suchtexte für Truhe und Händler für "
               "Waystones, Precursor Tablets und Händler-Items innerhalb des 250-Zeichen-Limits.",
    "r2_h1": "PoE2 Regex Builder",
    "r2_lead": "Erstelle Suchtexte für Truhe und Händler für Waystones, Precursor Tablets und Händler-Items. "
               "Wähle, was du willst und was du meidest, kopiere es und füge es im Spiel ein.",
    "tab_waystones": "Waystones",
    "tab_tablets": "Tablets",
    "tab_vendor": "Händler",
    "r2_waystone_note_html": "{n} Waystone-Mods. <b>{want}</b> hebt Maps mit ihnen hervor, "
                             "<b>{avoid}</b> blendet Maps mit ihnen aus.",
    "r2_tablet_note": "{n} Precursor-Tablet-Mods.",
    "r2_vendor_note": "Hake die gesuchten Werte an und setze ein Minimum. Praktisch beim Leveln: Stiefel "
                      "mit Bewegungsgeschwindigkeit, Waffen mit +Skill-Level, Widerstände.",
    "r2_placeholder": "Wähle Mods, um einen Suchtext zu erstellen",
    "r2_paste": "In das Suchfeld von Truhe, Händler oder Map-Gerät einfügen.",
    "r2_how_title": "So funktioniert Regex in der PoE2-Suche",
    "r2_how_example": "Tier 15+ ohne diesen Mod.",
    "r2_q1": "Wie benutze ich Regex in Path of Exile 2?",
    "r2_a1": "Öffne deine Truhe, ein Händlerfenster oder das Map-Gerät, klicke ins Suchfeld und füge den "
             "erzeugten Text ein — passende Items werden hervorgehoben. Alles in Anführungszeichen ist "
             "ein regulärer Ausdruck; ein vorangestelltes ! bedeutet „passt nicht“.",
    "r2_q2": "Warum gibt es ein Limit von 250 Zeichen?",
    "r2_a2": "Das Suchfeld im Spiel nimmt höchstens 250 Zeichen an. Der Builder nutzt das kürzeste Stück "
             "jedes Mods, das kein anderer Mod enthält — so passen viel mehr Mods hinein als mit den "
             "vollen Texten.",
    "r2_q3": "Funktioniert es mit dem Spiel in einer anderen Sprache?",
    "r2_a3": "Nein. Die Suche vergleicht den Text, den der Client anzeigt, und die Mod-Texte hier sind "
             "englisch. Stelle den Client auf Englisch um oder passe die Fragmente an.",
    "r2_q4": "Sind die Mod-Listen aktuell?",
    "r2_a4": "Waystone-Mods stammen aus den Wertedaten des Spiels, Tablet-Mods aus der Werteliste der "
             "offiziellen Trade-Seite — sie werden bei jedem Update der Seite neu erzeugt.",
    "r1_title": "PoE Regex Builder — Maps, Händler, Heist-Kontrakte & Logbücher",
    "r1_desc": "Kostenloser Regex Builder für Path of Exile: Quantity und schlechte Mods auf seltenen Maps "
               "(inkl. T17), Händler-Items beim Leveln mit Links und Farben, Heist-Kontrakte und "
               "Expedition-Logbücher — mit teilbarem Link, innerhalb von 250 Zeichen.",
    "r1_h1": "PoE Regex Builder",
    "r1_lead": "Suchtexte für Truhe und Händler für seltene Maps, Leveling-Ausrüstung, Heist-Kontrakte und "
               "Expedition-Logbücher. Wähle, was du willst und was dein Build nicht schafft, dann kopiere "
               "den Text oder teile den Link.",
    "tab_maps": "Maps",
    "tab_heist": "Heist",
    "tab_logbooks": "Logbücher",
    "r1_maps_note_html": "{n} Map-Mod-Zeilen. <b>{want}</b> hebt Maps mit ihnen hervor, "
                         "<b>{avoid}</b> blendet Maps mit einem davon aus.",
    "quick_avoid": "Schnell meiden:",
    "quick_avoid_aria": "Vorlagen zum Meiden",
    "preset_count": "{n} Mod(s)",
    "preset_regen": "Keine Regeneration",
    "preset_leech": "Kein Leech",
    "preset_curses": "Flüche",
    "preset_maxres": "Max. Widerstände",
    "preset_thorns": "Dornen",
    "preset_block": "Block",
    "preset_flasks": "Fläschchen",
    "hide_t17": "Nur-T17 ausblenden ({n})",
    "t17_title": "Kommt nur auf Tier-17-Maps vor",
    "r1_vendor_note": "Einkaufsliste für Händler beim Leveln: hake Werte an und setze ein Minimum. Bei "
                      "„einer davon“ braucht ein Item einen angehakten Wert, bei „alle“ jeden.",
    "sockets": "Sockel",
    "linked_group": "Verbundene Gruppe",
    "linked_aria": "Verbundene Sockel",
    "link_any": "Beliebig",
    "link_n": "{n}-Link",
    "red": "Rot",
    "green": "Grün",
    "blue": "Blau",
    "colour_aria": "{colour}e Sockel",
    "sockets_note": "Farben zählen innerhalb einer verbundenen Gruppe, z. B. findet ein 3-Link mit 1 Rot, "
                    "1 Grün und 1 Blau jede R-G-B-Reihenfolge. Sockel gelten immer zusätzlich zu den Werten.",
    "stats": "Werte",
    "r1_heist_note": "Heist-Kontrakte und Blueprints. Mindestwerte, Job-Level der Schurken und Mods gelten "
                     "gemeinsam.",
    "job_title": "Benötigtes Job-Level",
    "job_note": "Hebt Kontrakte hervor, die den Job auf diesem Level oder höher brauchen — höhere Level "
                "bedeuten bessere Belohnungen. Blueprints nennen mehrere Jobs; jeder angehakte muss dabei sein.",
    "job_label": "{job} Level",
    "r1_logbook_note": "Expedition-Logbücher: wähle Fraktion und Gebietsboni, meide Mods, die dein Build "
                       "nicht schafft.",
    "factions": "Fraktionen",
    "bonuses": "Gebietsboni & Bosse",
    "r1_placeholder": "Wähle Werte oder Mods, um einen Suchtext zu erstellen",
    "r1_apply_note": "Mindestwerte und gemiedene Mods gelten immer zusammen. Der Link öffnet diesen Tab mit "
                     "derselben Auswahl.",
    "r1_how_title": "So funktioniert die Suche",
    "r1_how_example": "90%+ Quantity ohne „keine Regeneration“.",
    "r1_q1": "Wie benutze ich einen Map-Regex in Path of Exile?",
    "r1_a1": "Öffne deine Truhe oder das Map-Gerät, klicke ins Suchfeld und füge den erzeugten Text ein. "
             "Passende Maps werden hervorgehoben. Gemiedene Mods beginnen mit !, daher bleiben Maps mit "
             "einem davon dunkel.",
    "r1_q2": "Welche Mods sollte ich meiden?",
    "r1_a2": "Das hängt vom Build ab. Häufig gemieden werden „Players cannot Regenerate“, die Leech-Mods "
             "für Leech-Builds, „Players are Cursed with ...“, reduzierte maximale Widerstände und die "
             "Physical/Elemental-Thorns-Mods für Nahkämpfer. Die Vorlagen über der Liste haken sie mit "
             "einem Klick an.",
    "r1_q3": "Warum sehen manche Fragmente seltsam aus, z. B. „ve .*% increased ar“?",
    "r1_a3": "Jeder Mod bekommt das kürzeste Textstück, das kein anderer Map-Mod, Map-Name und keine "
             "Map-Eigenschaft enthält. Kommen beide Hälften um eine Zahl auch in anderen Mods vor, "
             "überspannt das Fragment die Zahl mit .* — die Suche im Spiel unterstützt das.",
    "r1_q4": "Werden Tier-17-Maps abgedeckt?",
    "r1_a4": "Ja. Mods, die nur auf Tier-17-Maps vorkommen, sind mit T17 markiert und lassen sich "
             "ausblenden. Die Schwellen decken auch More Maps / More Scarabs / More Currency und die "
             "Map-Umwandlungschancen ab.",
    "r1_q5": "Ist die Liste an echten Maps geprüft?",
    "r1_a5": "Jedes Fragment wurde an seltenen Tier-14–17-Maps von der offiziellen Trade-Seite getestet: "
             "jede Mod-Zeile traf ihr eigenes Fragment und kein Fragment traf eine andere Zeile. "
             "Heist-Kontrakte, Blueprints und Expedition-Logbücher wurden genauso geprüft.",
    "r1_q6": "Wie teile ich meinen Regex?",
    "r1_a6": "Klicke auf „Link kopieren“. Der Link öffnet denselben Tab mit denselben Schwellen und Mods, "
             "so kann ihn ein Gildenkollege direkt in seine Truhensuche einfügen.",
    "r1_q7": "Wie funktioniert die Sockelsuche beim Händler?",
    "r1_a7": "Wähle die Größe der verbundenen Gruppe und die nötigen Farben. Der Builder schreibt jede "
             "Farbreihenfolge für eine Gruppe (R-G-B, G-R-B, ...), sodass ein 3-Link mit Rot, Grün und "
             "Blau unabhängig von der Anordnung gefunden wird.",
    "r1_q8": "Nach welchen Boni von Expedition-Logbüchern kann ich suchen?",
    "r1_a8": "Nach den vier Fraktionen, Gebietsboni wie Artefaktmenge, Explosionsradius, Remnants und "
             "Truhenmarkierungen sowie den Logbuch-Bossen. Mods funktionieren wie Map-Mods.",
    "in_title": "PoE2 Instill-Rechner — Liste der Distilled Emotions für Amulette",
    "in_desc": "Alle {n} Instill-Rezepte in Path of Exile 2: welche Distilled Emotions in welcher "
               "Reihenfolge welches Notable auf dem Amulett geben, durchsuchbar nach Name und Effekt.",
    "in_h1": "PoE2 Instill-Rechner",
    "in_lead": "Welche drei Distilled Emotions welches Notable auf deinem Amulett geben — und welches "
               "Notable deine Emotionen ergeben. Die Reihenfolge zählt: dieselben Emotionen in anderer "
               "Reihenfolge ergeben ein anderes Notable.",
    "in_make": "Was ergeben meine Emotionen?",
    "in_slot": "Slot {n}",
    "in_slot_aria": "Emotion in Slot {n}",
    "in_pick": "Wähle für jeden Slot eine Emotion.",
    "in_none": "Kein Notable nutzt diese drei Emotionen in dieser Reihenfolge. Probiere eine andere "
               "Reihenfolge — jede ist ein eigenes Rezept.",
    "in_find": "Notable finden",
    "in_search": "Nach Name oder Effekt suchen — z. B. chaos, charm, freeze",
    "in_search_aria": "Notables durchsuchen",
    "in_owned": "Nur Rezepte, die ich machen kann mit",
    "in_owned_aria": "Emotionen, die du hast",
    "in_tiers": "Emotion-Stufen:",
    "in_count": "{n} Notables",
    "in_count_of": "{shown} von {n} Notables",
    "in_recipe_aria": "Rezept: {list}",
    "in_data": "Daten erzeugt am {date}.",
    "in_q1": "Wie funktioniert Instill auf Amuletten in Path of Exile 2?",
    "in_a1": "Drei Distilled Emotions kommen auf ein Amulett, und es erhält eine Verzauberung, die ein "
             "Notable des Passivbaums zuweist, auch wenn es nicht mit deinem Baum verbunden ist. Dieser "
             "Rechner listet jedes Notable mit den nötigen Emotionen.",
    "in_q2": "Spielt die Reihenfolge der Emotionen eine Rolle?",
    "in_a2": "Ja. Dieselben drei Emotionen in anderer Reihenfolge ergeben ein anderes Notable — z. B. "
             "Isolation, Ire, Disgust ergibt Void, Ire, Disgust, Isolation dagegen Revenge. Die Rezepte "
             "werden in Slot-Reihenfolge gezeigt.",
    "in_q3": "Woher stammen die Daten?",
    "in_a3": "Rezepte stammen aus den Spieldaten (über Exiled Exchange 2), Notable-Beschreibungen aus "
             "dem Passivbaum und den Wertebeschreibungen des Spiels (über RePoE) — neu erzeugt bei jedem "
             "Update der Seite.",
    "ec_poe2_title": "PoE2 Wirtschaft — Preise für Währung, Runen & Essenzen",
    "ec_poe2_desc": "Aktuelle Preise in Path of Exile 2: Kurs von Divine und Exalted Orb, Runen, Essenzen, "
                    "Soul Cores, Uncut Gems — mit Änderung über 24 Stunden, 7 und 30 Tage.",
    "ec_poe1_title": "PoE Wirtschaft — Preise für Währung, Uniques & Skarabäen",
    "ec_poe1_desc": "Aktuelle Preise in Path of Exile: Divine-Orb-Kurs, Unique-Items, Skarabäen, Essenzen, "
                    "Weissagungskarten — mit Änderung über 24 Stunden, 7 und 30 Tage und Preisverlauf der Liga.",
    "ec_live": "aktuelle Preise",
    "ec_h1": "{game} Wirtschaft",
    "ec_lead_poe1": "Preise für Währung und Unique-Items in der aktuellen Liga mit Änderung über den letzten "
                    "Tag, die Woche und den Monat — klicke auf eine Zeile für den Preisverlauf.",
    "ec_lead_poe2": "Preise für Währung und Verbrauchsgüter in der aktuellen Liga mit Änderung über den "
                    "letzten Tag, die Woche und den Monat — klicke auf eine Zeile für den Preisverlauf.",
    "ec_game_aria": "Spiel",
    "ec_league": "Liga",
    "ec_loading_leagues": "Lädt…",
    "ec_search": "Alle Items nach Namen suchen…",
    "ec_hide_low": "Unsichere Preise ausblenden",
    "ec_category_aria": "Kategorie",
    "ec_col_item": "Item",
    "ec_col_value": "Wert",
    "ec_col_volume": "Volumen",
    "ec_col_listed": "Angebote",
    "ec_col_vol_listed": "Volumen / Angebote",
    "ec_col_spark": "Letzte 7 Tage",
    "ec_loading": "Preise werden geladen…",
    "ec_source_html": "Preise von {link}, alle 30 Minuten aktualisiert.",
    "ec_history_loading": "Preisverlauf wird geladen…",
    "ec_history_short": "Für dieses Item gibt es noch nicht genug Preisverlauf.",
    "ec_history_error": "Der Preisverlauf ist gerade nicht verfügbar.",
    "ec_now": "Jetzt",
    "ec_low": "Liga-Tief",
    "ec_high": "Liga-Hoch",
    "ec_since": "Seit {date}",
    "ec_show_table": "Datentabelle anzeigen",
    "ec_day": "Tag",
    "ec_price_unit": "Preis ({unit})",
    "ec_chart_aria": "Preisverlauf, {n} Tage, von {from} bis {to} {unit}",
    "ec_low_tag": "unsicherer Preis",
    "ec_results": "{n} Ergebnisse",
    "ec_no_results": "Keine Ergebnisse",
    "ec_for_query": "für „{q}“ in allen Kategorien",
    "ec_top": "(zeige die ersten {n})",
    "ec_searching": "durchsuche {loaded}/{total} Kategorien…",
    "ec_click_row": "Zeile anklicken für den Preisverlauf",
    "ec_items": "{n} Items",
    "ec_updated": "aktualisiert {time}",
    "ec_prices_error": "Preise sind gerade nicht verfügbar. Versuche es in ein paar Minuten erneut.",
    "ec_leagues_error": "Die Ligaliste ist gerade nicht verfügbar. Versuche es in ein paar Minuten erneut.",
    "ec_q1": "Woher kommen diese Preise?",
    "ec_a1": "Von poe.ninja, das die Währungsbörse und öffentliche Truhen-Tabs auswertet. Preise werden "
             "alle 30 Minuten aktualisiert.",
    "ec_q2": "Was bedeuten die Spalten 24h, 7d und 30d?",
    "ec_a2": "Die Preisänderung über den letzten Tag, die Woche und den Monat. 24h und 7d stammen aus dem "
             "Preisverlauf von poe.ninja; 30d aus täglichen Aufzeichnungen dieser Seite, daher füllt es sich "
             "im ersten Monat einer Liga.",
    "ec_q3": "Muss ich wissen, in welcher Kategorie ein Item ist?",
    "ec_a3": "Nein. Tippe mindestens zwei Buchstaben eines Item-Namens ins Suchfeld, und die Ergebnisse "
             "kommen aus allen Kategorien gleichzeitig, jeweils mit ihrer Kategorie markiert.",
    "ec_q4": "Kann ich sehen, wie sich ein Preis in der Liga verändert hat?",
    "ec_a4": "Ja — klicke auf eine Zeile, um den Preisverlauf der ganzen Liga mit Tief, Hoch und Änderung "
             "seit Ligastart zu öffnen.",
    "ec_q5": "Was bedeutet „unsicherer Preis“ bei Unique-Items?",
    "ec_a5": "Der Preis beruht auf weniger als 10 Angeboten und kann daher stark abweichen. Solche Items "
             "sind standardmäßig ausgeblendet; entferne den Haken bei „Unsichere Preise ausblenden“, um sie "
             "zu sehen. Unique-Preise gibt es nur für Path of Exile 1 — Path of Exile 2 hat keine "
             "öffentlichen Truhen-Daten.",
    "ec_q6": "Wie bewerte ich ein seltenes Item?",
    "ec_a6": "Hier stehen währungsartige Items. Für seltene und einzigartige Items nutze die kostenlose App "
             "PoE Price Check — sie liest das Item unter dem Cursor und sucht auf der offiziellen Trade-Seite.",
}

T["es"] = {
    "nav_home": "Price Checker",
    "nav_poe1": "PoE1 Regex",
    "nav_poe2": "PoE2 Regex",
    "nav_instill": "PoE2 Instill",
    "nav_economy": "Economía",
    "nav_aria": "Herramientas",
    "lang_aria": "Idioma",
    "skip": "Saltar al contenido",
    "footer_cta": "consulta precios de objetos en Path of Exile 1 y 2, también en la nube (Boosteroid).",
    "disclaimer": "Sin relación ni respaldo de Grinding Gear Games.",
    "free_tool": "herramienta gratuita",
    "faq": "Preguntas frecuentes",
    "your_regex": "Tu regex",
    "copy": "Copiar",
    "copied": "Copiado",
    "copy_link": "Copiar enlace",
    "link_in_bar": "El enlace está en la barra de direcciones",
    "clear": "Limpiar",
    "generated_aria": "Regex generado",
    "item_type_aria": "Tipo de objeto",
    "mode_legend": "Los mods deseados deben coincidir con",
    "mode_legend_poe1": "Los mods deseados (Vendedor: estadísticas) deben coincidir con",
    "mode_any": "cualquiera de ellos",
    "mode_all": "todos",
    "filter": "Filtrar mods…",
    "want": "Quiero",
    "avoid": "Evitar",
    "picked": "{want} deseados · {avoid} evitados",
    "also_title": "También coincide con {n} mod(s) más largo(s) que contienen este texto",
    "min_values": "Valores mínimos",
    "modifiers": "Mods",
    "minimum_aria": "{label} mínimo",
    "english_only": "Solo funciona con el cliente del juego en inglés.",
    "data_generated": "Datos de mods generados el {date}.",
    "how1_html": "<b>El texto entre comillas es un patrón.</b> {code} resalta cada objeto cuyo texto lo contiene.",
    "how2_html": "<b>{bar} significa «o».</b> {code} coincide con uno u otro.",
    "how3_html": "<b>Un {bang} al principio niega.</b> {code} oculta los objetos con cualquiera de ellos.",
    "how4_html": "<b>Los patrones separados por espacios deben coincidir todos.</b> {code} — {example}",
    "r2_title": "Regex PoE2 — búsqueda de Waystones, Tablets y vendedor",
    "r2_desc": "Generador de regex gratuito para Path of Exile 2: textos de búsqueda para el alijo y el "
               "vendedor de Waystones, Precursor Tablets y objetos de vendedor dentro del límite de 250 caracteres.",
    "r2_h1": "Generador de regex PoE2",
    "r2_lead": "Crea textos de búsqueda para el alijo y el vendedor de Waystones, Precursor Tablets y "
               "objetos de vendedor. Elige lo que quieres y lo que evitas, copia y pega en el juego.",
    "tab_waystones": "Waystones",
    "tab_tablets": "Tablets",
    "tab_vendor": "Vendedor",
    "r2_waystone_note_html": "{n} mods de Waystone. <b>{want}</b> resalta los mapas que los tienen, "
                             "<b>{avoid}</b> oculta los mapas con ellos.",
    "r2_tablet_note": "{n} mods de Precursor Tablet.",
    "r2_vendor_note": "Marca las estadísticas que buscas y fija un mínimo. Útil al subir de nivel: botas con "
                      "velocidad de movimiento, armas con +nivel de habilidad, resistencias.",
    "r2_placeholder": "Elige mods para crear un texto de búsqueda",
    "r2_paste": "Pega en la búsqueda del alijo, del vendedor o del dispositivo de mapas.",
    "r2_how_title": "Cómo funciona el regex en la búsqueda de PoE2",
    "r2_how_example": "tier 15+ sin ese mod.",
    "r2_q1": "¿Cómo uso regex en Path of Exile 2?",
    "r2_a1": "Abre tu alijo, la ventana de un vendedor o el dispositivo de mapas, haz clic en la búsqueda y "
             "pega el texto generado: los objetos que coinciden se resaltan. Todo lo que va entre comillas "
             "es una expresión regular; un ! al principio significa «no coincide».",
    "r2_q2": "¿Por qué hay un límite de 250 caracteres?",
    "r2_a2": "La búsqueda del juego acepta como máximo 250 caracteres. El generador usa el fragmento más "
             "corto de cada mod que no contiene ningún otro mod, así caben muchos más mods que con los "
             "textos completos.",
    "r2_q3": "¿Funciona con el juego en otro idioma?",
    "r2_a3": "No. La búsqueda compara el texto que muestra el cliente y aquí los textos de mods están en "
             "inglés. Cambia el cliente a inglés o adapta los fragmentos.",
    "r2_q4": "¿Están actualizadas las listas de mods?",
    "r2_a4": "Los mods de Waystone salen de los datos de estadísticas del propio juego y los de Tablet de "
             "la lista de estadísticas del sitio oficial de trade; se regeneran en cada actualización del sitio.",
    "r1_title": "Regex PoE — mapas, vendedor, contratos de Heist y Logbooks",
    "r1_desc": "Generador de regex gratuito para Path of Exile: cantidad y mods malos en mapas raros "
               "(incluido T17), objetos de vendedor al subir de nivel con enlaces y colores, contratos de "
               "Heist y Expedition Logbooks, con enlace para compartir y en el límite de 250 caracteres.",
    "r1_h1": "Generador de regex PoE",
    "r1_lead": "Textos de búsqueda para el alijo y el vendedor de mapas raros, equipo para subir de nivel, "
               "contratos de Heist y Expedition Logbooks. Elige lo que quieres y lo que tu build no aguanta, "
               "luego copia el texto o comparte el enlace.",
    "tab_maps": "Mapas",
    "tab_heist": "Heist",
    "tab_logbooks": "Logbooks",
    "r1_maps_note_html": "{n} líneas de mods de mapas. <b>{want}</b> resalta los mapas que las tienen, "
                         "<b>{avoid}</b> oculta los mapas con cualquiera de ellas.",
    "quick_avoid": "Evitar rápido:",
    "quick_avoid_aria": "Conjuntos rápidos para evitar",
    "preset_count": "{n} mod(s)",
    "preset_regen": "Sin regeneración",
    "preset_leech": "Sin leech",
    "preset_curses": "Maldiciones",
    "preset_maxres": "Res. máx.",
    "preset_thorns": "Espinas",
    "preset_block": "Bloqueo",
    "preset_flasks": "Frascos",
    "hide_t17": "Ocultar solo-T17 ({n})",
    "t17_title": "Solo aparece en mapas Tier 17",
    "r1_vendor_note": "Lista de compras en vendedores al subir de nivel: marca las estadísticas y fija un "
                      "mínimo. Con «cualquiera de ellos» un objeto necesita una marcada; con «todos», cada una.",
    "sockets": "Engarces",
    "linked_group": "Grupo enlazado",
    "linked_aria": "Engarces enlazados",
    "link_any": "Cualquiera",
    "link_n": "{n}-link",
    "red": "Rojo",
    "green": "Verde",
    "blue": "Azul",
    "colour_aria": "Engarces {colour}",
    "sockets_note": "Los colores cuentan dentro de un grupo enlazado; p. ej., un 3-link con 1 rojo, 1 verde y "
                    "1 azul encuentra cualquier orden R-G-B. Los engarces se aplican siempre además de las estadísticas.",
    "stats": "Estadísticas",
    "r1_heist_note": "Contratos y Blueprints de Heist. Valores mínimos, niveles de oficio y mods se aplican "
                     "a la vez.",
    "job_title": "Nivel de oficio requerido",
    "job_note": "Resalta los contratos que piden el oficio en este nivel o superior; más nivel significa "
                "mejores recompensas. Los Blueprints piden varios oficios; cada oficio marcado debe estar.",
    "job_label": "Nivel de {job}",
    "r1_logbook_note": "Expedition Logbooks: elige la facción y los bonos de zona que quieres y evita los "
                       "mods que tu build no aguanta.",
    "factions": "Facciones",
    "bonuses": "Bonos de zona y jefes",
    "r1_placeholder": "Elige valores o mods para crear un texto de búsqueda",
    "r1_apply_note": "Los valores mínimos y los mods evitados se aplican siempre juntos. El enlace abre esta "
                     "pestaña con la misma selección.",
    "r1_how_title": "Cómo funciona la búsqueda",
    "r1_how_example": "cantidad 90%+ sin «sin regeneración».",
    "r1_q1": "¿Cómo uso un regex de mapas en Path of Exile?",
    "r1_a1": "Abre tu alijo o el dispositivo de mapas, haz clic en la búsqueda y pega el texto generado. "
             "Los mapas que coinciden se resaltan. Los mods evitados empiezan con !, así que los mapas con "
             "cualquiera de ellos quedan oscuros.",
    "r1_q2": "¿Qué mods debería evitar?",
    "r1_a2": "Depende del build. Los más evitados son «Players cannot Regenerate», los mods de leech para "
             "builds que dependen de él, «Players are Cursed with ...», las resistencias máximas reducidas y "
             "los mods Physical/Elemental Thorns para cuerpo a cuerpo. Los conjuntos rápidos sobre la lista "
             "los marcan con un clic.",
    "r1_q3": "¿Por qué algunos fragmentos se ven raros, como «ve .*% increased ar»?",
    "r1_a3": "Cada mod recibe el trozo de texto más corto que no contiene ningún otro mod de mapa, nombre "
             "de mapa ni propiedad. Cuando las dos mitades alrededor de un número aparecen también en otros "
             "mods, el fragmento cruza el número con .*, y la búsqueda del juego lo admite.",
    "r1_q4": "¿Incluye mapas Tier 17?",
    "r1_a4": "Sí. Los mods que solo salen en mapas Tier 17 llevan la marca T17 y se pueden ocultar. Los "
             "umbrales cubren también More Maps / More Scarabs / More Currency y las probabilidades de "
             "conversión de mapas.",
    "r1_q5": "¿La lista está comprobada con mapas reales?",
    "r1_a5": "Cada fragmento se probó con mapas raros Tier 14–17 del sitio oficial de trade: cada línea de "
             "mod coincidió con su propio fragmento y ningún fragmento coincidió con otra línea. Los contratos "
             "y Blueprints de Heist y los Expedition Logbooks se comprobaron igual.",
    "r1_q6": "¿Cómo comparto mi regex?",
    "r1_a6": "Haz clic en «Copiar enlace». El enlace abre la misma pestaña con los mismos umbrales y mods, "
             "así un compañero de gremio puede pegarlo directamente en su alijo.",
    "r1_q7": "¿Cómo funciona la búsqueda de engarces en el vendedor?",
    "r1_a7": "Elige el tamaño del grupo enlazado y los colores que necesitas. El generador escribe cada orden "
             "de colores para un grupo (R-G-B, G-R-B, ...), así un 3-link con rojo, verde y azul aparece sea "
             "cual sea el orden de los engarces.",
    "r1_q8": "¿Qué bonos de Expedition Logbook puedo buscar?",
    "r1_a8": "Las cuatro facciones, los bonos de zona como cantidad de artefactos, radio de explosión, "
             "remanentes y marcadores de cofres, y los jefes del logbook. Los mods funcionan como los de mapas.",
    "in_title": "Calculadora Instill PoE2 — lista de Distilled Emotions para amuletos",
    "in_desc": "Las {n} recetas de instill de Path of Exile 2: qué Distilled Emotions y en qué orden asignan "
               "cada notable en tu amuleto, con búsqueda por nombre y efecto.",
    "in_h1": "Calculadora Instill PoE2",
    "in_lead": "Qué tres Distilled Emotions asignan cada notable en tu amuleto y qué notable crean tus "
               "emociones. El orden importa: las mismas emociones en otro orden dan otro notable.",
    "in_make": "¿Qué crean mis emociones?",
    "in_slot": "Ranura {n}",
    "in_slot_aria": "Emoción en la ranura {n}",
    "in_pick": "Elige una emoción para cada ranura.",
    "in_none": "Ningún notable usa estas tres emociones en este orden. Prueba otro orden: cada orden es una "
               "receta distinta.",
    "in_find": "Buscar un notable",
    "in_search": "Busca por nombre o efecto, p. ej. chaos, charm, freeze",
    "in_search_aria": "Buscar notables",
    "in_owned": "Solo recetas que puedo hacer con",
    "in_owned_aria": "Emociones que tienes",
    "in_tiers": "Niveles de emoción:",
    "in_count": "{n} notables",
    "in_count_of": "{shown} de {n} notables",
    "in_recipe_aria": "Receta: {list}",
    "in_data": "Datos generados el {date}.",
    "in_q1": "¿Cómo funciona el instill de amuletos en Path of Exile 2?",
    "in_a1": "Se colocan tres Distilled Emotions en un amuleto y este obtiene un encantamiento que asigna un "
             "notable pasivo, aunque no esté conectado a tu árbol. Esta calculadora muestra cada notable con "
             "las emociones que necesita.",
    "in_q2": "¿Importa el orden de las emociones?",
    "in_a2": "Sí. Las mismas tres emociones en otro orden dan otro notable: por ejemplo, Isolation, Ire, "
             "Disgust asigna Void, mientras que Ire, Disgust, Isolation asigna Revenge. Las recetas se "
             "muestran en orden de ranura.",
    "in_q3": "¿De dónde salen los datos?",
    "in_a3": "Las recetas salen de los datos del juego (vía Exiled Exchange 2) y las descripciones de "
             "notables del árbol pasivo y las descripciones de estadísticas del juego (vía RePoE); se "
             "regeneran en cada actualización del sitio.",
    "ec_poe2_title": "Economía PoE2 — precios de monedas, runas y esencias",
    "ec_poe2_desc": "Precios actuales de Path of Exile 2: cambio de Divine y Exalted Orb, runas, esencias, "
                    "soul cores, uncut gems, con variación en 24 horas, 7 y 30 días.",
    "ec_poe1_title": "Economía PoE — precios de monedas, únicos y escarabajos",
    "ec_poe1_desc": "Precios actuales de Path of Exile: cambio de Divine Orb, objetos únicos, escarabajos, "
                    "esencias, cartas de adivinación, con variación en 24 horas, 7 y 30 días e historial de la liga.",
    "ec_live": "precios en vivo",
    "ec_h1": "Economía {game}",
    "ec_lead_poe1": "Precios de monedas y objetos únicos en la liga actual con la variación del último día, "
                    "semana y mes; haz clic en una fila para ver su historial.",
    "ec_lead_poe2": "Precios de monedas y consumibles en la liga actual con la variación del último día, "
                    "semana y mes; haz clic en una fila para ver su historial.",
    "ec_game_aria": "Juego",
    "ec_league": "Liga",
    "ec_loading_leagues": "Cargando…",
    "ec_search": "Busca objetos por nombre…",
    "ec_hide_low": "Ocultar precios poco fiables",
    "ec_category_aria": "Categoría",
    "ec_col_item": "Objeto",
    "ec_col_value": "Valor",
    "ec_col_volume": "Volumen",
    "ec_col_listed": "Ofertas",
    "ec_col_vol_listed": "Volumen / ofertas",
    "ec_col_spark": "Últimos 7 días",
    "ec_loading": "Cargando precios…",
    "ec_source_html": "Precios de {link}, actualizados cada 30 minutos.",
    "ec_history_loading": "Cargando historial de precios…",
    "ec_history_short": "Todavía no hay suficiente historial de precios para este objeto.",
    "ec_history_error": "El historial de precios no está disponible ahora.",
    "ec_now": "Ahora",
    "ec_low": "Mínimo de la liga",
    "ec_high": "Máximo de la liga",
    "ec_since": "Desde {date}",
    "ec_show_table": "Mostrar tabla de datos",
    "ec_day": "Día",
    "ec_price_unit": "Precio ({unit})",
    "ec_chart_aria": "Historial de precios, {n} días, de {from} a {to} {unit}",
    "ec_low_tag": "precio poco fiable",
    "ec_results": "{n} resultados",
    "ec_no_results": "Sin resultados",
    "ec_for_query": "para «{q}» en todas las categorías",
    "ec_top": "(mostrando los primeros {n})",
    "ec_searching": "buscando en {loaded}/{total} categorías…",
    "ec_click_row": "haz clic en una fila para ver el historial",
    "ec_items": "{n} objetos",
    "ec_updated": "actualizado {time}",
    "ec_prices_error": "Los precios no están disponibles ahora. Inténtalo en unos minutos.",
    "ec_leagues_error": "La lista de ligas no está disponible ahora. Inténtalo en unos minutos.",
    "ec_q1": "¿De dónde salen estos precios?",
    "ec_a1": "De poe.ninja, que recopila el intercambio de monedas y las pestañas públicas de alijo. Los "
             "precios se actualizan cada 30 minutos.",
    "ec_q2": "¿Qué significan las columnas 24h, 7d y 30d?",
    "ec_a2": "La variación de precio del último día, semana y mes. 24h y 7d salen del historial de poe.ninja; "
             "30d de registros diarios que guarda este sitio, por lo que se completa durante el primer mes de liga.",
    "ec_q3": "¿Necesito saber en qué categoría está un objeto?",
    "ec_a3": "No. Escribe al menos dos letras del nombre y los resultados llegan de todas las categorías a la "
             "vez, cada uno marcado con su categoría.",
    "ec_q4": "¿Puedo ver cómo cambió un precio durante la liga?",
    "ec_a4": "Sí: haz clic en cualquier fila para abrir su historial de toda la liga, con el mínimo, el "
             "máximo y el cambio desde el inicio de la liga.",
    "ec_q5": "¿Qué significa «precio poco fiable» en los objetos únicos?",
    "ec_a5": "El precio se basa en menos de 10 ofertas, así que puede estar lejos de la realidad. Esos "
             "objetos se ocultan por defecto; desmarca «Ocultar precios poco fiables» para verlos. Los precios "
             "de únicos solo existen para Path of Exile 1: Path of Exile 2 no tiene datos públicos de alijos.",
    "ec_q6": "¿Cómo tasar un objeto raro?",
    "ec_a6": "Aquí están los objetos tipo moneda. Para raros y únicos usa la app gratuita PoE Price Check: lee "
             "el objeto bajo el cursor y busca en el sitio oficial de trade.",
}

T["pt"] = {
    "nav_home": "Price Checker",
    "nav_poe1": "PoE1 Regex",
    "nav_poe2": "PoE2 Regex",
    "nav_instill": "PoE2 Instill",
    "nav_economy": "Economia",
    "nav_aria": "Ferramentas",
    "lang_aria": "Idioma",
    "skip": "Pular para o conteúdo",
    "footer_cta": "consulte preços de itens em Path of Exile 1 e 2, também em jogos na nuvem (Boosteroid).",
    "disclaimer": "Sem vínculo ou endosso da Grinding Gear Games.",
    "free_tool": "ferramenta grátis",
    "faq": "Perguntas frequentes",
    "your_regex": "Seu regex",
    "copy": "Copiar",
    "copied": "Copiado",
    "copy_link": "Copiar link",
    "link_in_bar": "O link está na barra de endereço",
    "clear": "Limpar",
    "generated_aria": "Regex gerado",
    "item_type_aria": "Tipo de item",
    "mode_legend": "Mods desejados devem corresponder a",
    "mode_legend_poe1": "Mods desejados (Vendedor: atributos) devem corresponder a",
    "mode_any": "qualquer um",
    "mode_all": "todos",
    "filter": "Filtrar mods…",
    "want": "Quero",
    "avoid": "Evitar",
    "picked": "{want} desejados · {avoid} evitados",
    "also_title": "Também corresponde a {n} mod(s) mais longo(s) que contêm este texto",
    "min_values": "Valores mínimos",
    "modifiers": "Mods",
    "minimum_aria": "{label} mínimo",
    "english_only": "Funciona apenas com o cliente do jogo em inglês.",
    "data_generated": "Dados de mods gerados em {date}.",
    "how1_html": "<b>Texto entre aspas é um padrão.</b> {code} destaca todo item cujo texto o contém.",
    "how2_html": "<b>{bar} significa “ou”.</b> {code} corresponde a um ou outro.",
    "how3_html": "<b>Um {bang} no início nega.</b> {code} esconde itens com qualquer um deles.",
    "how4_html": "<b>Padrões separados por espaço precisam corresponder todos.</b> {code} — {example}",
    "r2_title": "Regex PoE2 — busca de Waystones, Tablets e vendedor",
    "r2_desc": "Gerador de regex grátis para Path of Exile 2: textos de busca no baú e no vendedor para "
               "Waystones, Precursor Tablets e itens de vendedor dentro do limite de 250 caracteres.",
    "r2_h1": "Gerador de regex PoE2",
    "r2_lead": "Monte textos de busca no baú e no vendedor para Waystones, Precursor Tablets e itens de "
               "vendedor. Escolha o que quer e o que evitar, copie e cole no jogo.",
    "tab_waystones": "Waystones",
    "tab_tablets": "Tablets",
    "tab_vendor": "Vendedor",
    "r2_waystone_note_html": "{n} mods de Waystone. <b>{want}</b> destaca mapas que os têm, "
                             "<b>{avoid}</b> esconde mapas com eles.",
    "r2_tablet_note": "{n} mods de Precursor Tablet.",
    "r2_vendor_note": "Marque os atributos que procura e defina um mínimo. Útil para upar: botas com "
                      "velocidade de movimento, armas com +nível de habilidade, resistências.",
    "r2_placeholder": "Escolha mods para montar um texto de busca",
    "r2_paste": "Cole na busca do baú, do vendedor ou do dispositivo de mapas.",
    "r2_how_title": "Como funciona o regex na busca do PoE2",
    "r2_how_example": "tier 15+ sem esse mod.",
    "r2_q1": "Como uso regex no Path of Exile 2?",
    "r2_a1": "Abra o baú, a janela de um vendedor ou o dispositivo de mapas, clique na busca e cole o texto "
             "gerado: os itens correspondentes ficam destacados. Tudo entre aspas é uma expressão regular; "
             "um ! no início significa “não corresponde”.",
    "r2_q2": "Por que existe um limite de 250 caracteres?",
    "r2_a2": "A busca do jogo aceita no máximo 250 caracteres. O gerador usa o menor trecho de cada mod que "
             "nenhum outro mod contém, então cabem muito mais mods do que com os textos completos.",
    "r2_q3": "Funciona com o jogo em outro idioma?",
    "r2_a3": "Não. A busca compara o texto exibido pelo cliente, e os textos dos mods aqui estão em inglês. "
             "Mude o cliente para inglês ou adapte os trechos.",
    "r2_q4": "As listas de mods estão atualizadas?",
    "r2_a4": "Os mods de Waystone vêm dos dados de atributos do próprio jogo e os de Tablet da lista de "
             "atributos do site oficial de trade, gerados de novo a cada atualização do site.",
    "r1_title": "Regex PoE — mapas, vendedor, contratos de Heist e Logbooks",
    "r1_desc": "Gerador de regex grátis para Path of Exile: quantidade e mods ruins em mapas raros (com T17), "
               "itens de vendedor para upar com links e cores, contratos de Heist e Expedition Logbooks, com "
               "link para compartilhar, dentro de 250 caracteres.",
    "r1_h1": "Gerador de regex PoE",
    "r1_lead": "Textos de busca no baú e no vendedor para mapas raros, equipamento para upar, contratos de "
               "Heist e Expedition Logbooks. Escolha o que quer e o que sua build não aguenta, depois copie o "
               "texto ou compartilhe o link.",
    "tab_maps": "Mapas",
    "tab_heist": "Heist",
    "tab_logbooks": "Logbooks",
    "r1_maps_note_html": "{n} linhas de mods de mapas. <b>{want}</b> destaca mapas que as têm, "
                         "<b>{avoid}</b> esconde mapas com qualquer uma delas.",
    "quick_avoid": "Evitar rápido:",
    "quick_avoid_aria": "Conjuntos rápidos para evitar",
    "preset_count": "{n} mod(s)",
    "preset_regen": "Sem regeneração",
    "preset_leech": "Sem leech",
    "preset_curses": "Maldições",
    "preset_maxres": "Res. máx.",
    "preset_thorns": "Espinhos",
    "preset_block": "Bloqueio",
    "preset_flasks": "Frascos",
    "hide_t17": "Ocultar só-T17 ({n})",
    "t17_title": "Só aparece em mapas Tier 17",
    "r1_vendor_note": "Lista de compras no vendedor para upar: marque os atributos e defina um mínimo. Com "
                      "“qualquer um” o item precisa de um marcado; com “todos”, de cada um.",
    "sockets": "Encaixes",
    "linked_group": "Grupo ligado",
    "linked_aria": "Encaixes ligados",
    "link_any": "Qualquer",
    "link_n": "{n}-link",
    "red": "Vermelho",
    "green": "Verde",
    "blue": "Azul",
    "colour_aria": "Encaixes {colour}",
    "sockets_note": "As cores contam dentro de um grupo ligado; por exemplo, um 3-link com 1 vermelho, 1 verde "
                    "e 1 azul encontra qualquer ordem R-G-B. Os encaixes sempre valem além dos atributos.",
    "stats": "Atributos",
    "r1_heist_note": "Contratos e Blueprints de Heist. Valores mínimos, níveis de função e mods valem juntos.",
    "job_title": "Nível de função exigido",
    "job_note": "Destaca contratos que exigem a função neste nível ou acima; nível maior significa recompensas "
                "melhores. Blueprints listam várias funções; toda função marcada precisa estar nele.",
    "job_label": "Nível de {job}",
    "r1_logbook_note": "Expedition Logbooks: escolha a facção e os bônus de área que quer e evite os mods que "
                       "sua build não aguenta.",
    "factions": "Facções",
    "bonuses": "Bônus de área e chefes",
    "r1_placeholder": "Escolha valores ou mods para montar um texto de busca",
    "r1_apply_note": "Valores mínimos e mods evitados sempre valem juntos. O link abre esta aba com as mesmas "
                     "escolhas.",
    "r1_how_title": "Como funciona a busca",
    "r1_how_example": "quantidade 90%+ sem “sem regeneração”.",
    "r1_q1": "Como uso um regex de mapas no Path of Exile?",
    "r1_a1": "Abra o baú ou o dispositivo de mapas, clique na busca e cole o texto gerado. Os mapas "
             "correspondentes ficam destacados. Mods evitados começam com !, então mapas com qualquer um "
             "deles ficam escuros.",
    "r1_q2": "Quais mods devo evitar?",
    "r1_a2": "Depende da build. Os mais evitados são “Players cannot Regenerate”, os mods de leech para builds "
             "que dependem dele, “Players are Cursed with ...”, resistências máximas reduzidas e os mods "
             "Physical/Elemental Thorns para corpo a corpo. Os conjuntos rápidos acima da lista marcam tudo "
             "com um clique.",
    "r1_q3": "Por que alguns trechos parecem estranhos, como “ve .*% increased ar”?",
    "r1_a3": "Cada mod recebe o menor trecho de texto que nenhum outro mod de mapa, nome de mapa ou "
             "propriedade contém. Quando as duas metades em volta de um número aparecem também em outros mods, "
             "o trecho atravessa o número com .*, e a busca do jogo aceita isso.",
    "r1_q4": "Cobre mapas Tier 17?",
    "r1_a4": "Sim. Mods que só aparecem em mapas Tier 17 têm a marca T17 e podem ser ocultados. Os limites "
             "também cobrem More Maps / More Scarabs / More Currency e as chances de conversão de mapas.",
    "r1_q5": "A lista foi conferida com mapas reais?",
    "r1_a5": "Cada trecho foi testado em mapas raros Tier 14–17 do site oficial de trade: cada linha de mod "
             "correspondeu ao próprio trecho e nenhum trecho correspondeu a outra linha. Contratos e Blueprints "
             "de Heist e Expedition Logbooks foram conferidos do mesmo jeito.",
    "r1_q6": "Como compartilho meu regex?",
    "r1_a6": "Clique em “Copiar link”. O link abre a mesma aba com os mesmos limites e mods, então um colega "
             "de guilda cola direto na busca do baú.",
    "r1_q7": "Como funciona a busca de encaixes no vendedor?",
    "r1_a7": "Escolha o tamanho do grupo ligado e as cores de que precisa. O gerador escreve toda ordem de "
             "cores para um grupo (R-G-B, G-R-B, ...), então um 3-link com vermelho, verde e azul é encontrado "
             "em qualquer ordem.",
    "r1_q8": "Quais bônus de Expedition Logbook posso buscar?",
    "r1_a8": "As quatro facções, bônus de área como quantidade de artefatos, raio de explosão, remanescentes e "
             "marcadores de baús, e os chefes do logbook. Os mods funcionam como os de mapas.",
    "in_title": "Calculadora de Instill PoE2 — lista de Distilled Emotions para amuletos",
    "in_desc": "Todas as {n} receitas de instill do Path of Exile 2: quais Distilled Emotions, e em que ordem, "
               "alocam cada notable no seu amuleto, com busca por nome e efeito.",
    "in_h1": "Calculadora de Instill PoE2",
    "in_lead": "Quais três Distilled Emotions alocam cada notable no seu amuleto e qual notable suas emoções "
               "criam. A ordem importa: as mesmas emoções em outra ordem dão outro notable.",
    "in_make": "O que minhas emoções criam?",
    "in_slot": "Espaço {n}",
    "in_slot_aria": "Emoção no espaço {n}",
    "in_pick": "Escolha uma emoção para cada espaço.",
    "in_none": "Nenhum notable usa essas três emoções nessa ordem. Tente outra ordem: cada ordem é uma receita "
               "diferente.",
    "in_find": "Encontrar um notable",
    "in_search": "Busque por nome ou efeito, ex.: chaos, charm, freeze",
    "in_search_aria": "Buscar notables",
    "in_owned": "Só receitas que consigo fazer com",
    "in_owned_aria": "Emoções que você tem",
    "in_tiers": "Níveis de emoção:",
    "in_count": "{n} notables",
    "in_count_of": "{shown} de {n} notables",
    "in_recipe_aria": "Receita: {list}",
    "in_data": "Dados gerados em {date}.",
    "in_q1": "Como funciona o instill de amuletos no Path of Exile 2?",
    "in_a1": "Três Distilled Emotions são colocadas em um amuleto, que ganha um encantamento que aloca um "
             "notable passivo, mesmo sem ligação com a sua árvore. Esta calculadora lista cada notable com as "
             "emoções necessárias.",
    "in_q2": "A ordem das emoções importa?",
    "in_a2": "Sim. As mesmas três emoções em outra ordem dão outro notable: por exemplo, Isolation, Ire, "
             "Disgust aloca Void, enquanto Ire, Disgust, Isolation aloca Revenge. As receitas aparecem na ordem "
             "dos espaços.",
    "in_q3": "De onde vêm os dados?",
    "in_a3": "As receitas vêm dos dados do jogo (via Exiled Exchange 2) e as descrições dos notables da árvore "
             "passiva e das descrições de atributos do jogo (via RePoE), geradas de novo a cada atualização do site.",
    "ec_poe2_title": "Economia PoE2 — preços de moedas, runas e essências",
    "ec_poe2_desc": "Preços atuais do Path of Exile 2: cotação de Divine e Exalted Orb, runas, essências, soul "
                    "cores, uncut gems, com variação em 24 horas, 7 e 30 dias.",
    "ec_poe1_title": "Economia PoE — preços de moedas, únicos e escaravelhos",
    "ec_poe1_desc": "Preços atuais do Path of Exile: cotação do Divine Orb, itens únicos, escaravelhos, "
                    "essências, cartas de adivinhação, com variação em 24 horas, 7 e 30 dias e histórico da liga.",
    "ec_live": "preços ao vivo",
    "ec_h1": "Economia {game}",
    "ec_lead_poe1": "Preços de moedas e itens únicos na liga atual com a variação do último dia, semana e mês; "
                    "clique em uma linha para ver o histórico.",
    "ec_lead_poe2": "Preços de moedas e consumíveis na liga atual com a variação do último dia, semana e mês; "
                    "clique em uma linha para ver o histórico.",
    "ec_game_aria": "Jogo",
    "ec_league": "Liga",
    "ec_loading_leagues": "Carregando…",
    "ec_search": "Busque itens pelo nome…",
    "ec_hide_low": "Ocultar preços pouco confiáveis",
    "ec_category_aria": "Categoria",
    "ec_col_item": "Item",
    "ec_col_value": "Valor",
    "ec_col_volume": "Volume",
    "ec_col_listed": "Ofertas",
    "ec_col_vol_listed": "Volume / ofertas",
    "ec_col_spark": "Últimos 7 dias",
    "ec_loading": "Carregando preços…",
    "ec_source_html": "Preços do {link}, atualizados a cada 30 minutos.",
    "ec_history_loading": "Carregando histórico de preços…",
    "ec_history_short": "Ainda não há histórico de preços suficiente para este item.",
    "ec_history_error": "O histórico de preços está indisponível agora.",
    "ec_now": "Agora",
    "ec_low": "Mínimo da liga",
    "ec_high": "Máximo da liga",
    "ec_since": "Desde {date}",
    "ec_show_table": "Mostrar tabela de dados",
    "ec_day": "Dia",
    "ec_price_unit": "Preço ({unit})",
    "ec_chart_aria": "Histórico de preços, {n} dias, de {from} a {to} {unit}",
    "ec_low_tag": "preço pouco confiável",
    "ec_results": "{n} resultados",
    "ec_no_results": "Nenhum resultado",
    "ec_for_query": "para “{q}” em todas as categorias",
    "ec_top": "(mostrando os primeiros {n})",
    "ec_searching": "buscando em {loaded}/{total} categorias…",
    "ec_click_row": "clique em uma linha para ver o histórico",
    "ec_items": "{n} itens",
    "ec_updated": "atualizado {time}",
    "ec_prices_error": "Os preços estão indisponíveis agora. Tente de novo em alguns minutos.",
    "ec_leagues_error": "A lista de ligas está indisponível agora. Tente de novo em alguns minutos.",
    "ec_q1": "De onde vêm esses preços?",
    "ec_a1": "Do poe.ninja, que reúne a troca de moedas e as abas públicas de baú. Os preços são atualizados "
             "a cada 30 minutos.",
    "ec_q2": "O que significam as colunas 24h, 7d e 30d?",
    "ec_a2": "A variação de preço no último dia, semana e mês. 24h e 7d vêm do histórico do poe.ninja; 30d vem "
             "de registros diários deste site, por isso se completa durante o primeiro mês da liga.",
    "ec_q3": "Preciso saber em que categoria o item está?",
    "ec_a3": "Não. Digite pelo menos duas letras do nome e os resultados vêm de todas as categorias ao mesmo "
             "tempo, cada um marcado com sua categoria.",
    "ec_q4": "Posso ver como um preço mudou durante a liga?",
    "ec_a4": "Sim: clique em qualquer linha para abrir o histórico da liga inteira, com mínimo, máximo e a "
             "variação desde o início da liga.",
    "ec_q5": "O que significa “preço pouco confiável” em itens únicos?",
    "ec_a5": "O preço se baseia em menos de 10 ofertas, então pode estar longe do real. Esses itens ficam "
             "ocultos por padrão; desmarque “Ocultar preços pouco confiáveis” para vê-los. Preços de únicos só "
             "existem para Path of Exile 1: Path of Exile 2 não tem dados públicos de baús.",
    "ec_q6": "Como avaliar um item raro?",
    "ec_a6": "Aqui ficam os itens do tipo moeda. Para raros e únicos use o app grátis PoE Price Check: ele lê o "
             "item sob o cursor e busca no site oficial de trade.",
}

T["ru"] = {
    "nav_home": "Price Checker",
    "nav_poe1": "PoE1 Regex",
    "nav_poe2": "PoE2 Regex",
    "nav_instill": "PoE2 Instill",
    "nav_economy": "Экономика",
    "nav_aria": "Инструменты",
    "lang_aria": "Язык",
    "skip": "Перейти к содержимому",
    "footer_cta": "оценка предметов в Path of Exile 1 и 2, в том числе в облачном гейминге (Boosteroid).",
    "disclaimer": "Проект не связан с Grinding Gear Games и не одобрен ими.",
    "free_tool": "бесплатный инструмент",
    "faq": "Частые вопросы",
    "your_regex": "Ваш regex",
    "copy": "Копировать",
    "copied": "Скопировано",
    "copy_link": "Копировать ссылку",
    "link_in_bar": "Ссылка в адресной строке",
    "clear": "Очистить",
    "generated_aria": "Созданный regex",
    "item_type_aria": "Тип предмета",
    "mode_legend": "Нужные моды должны совпадать",
    "mode_legend_poe1": "Нужные моды (Торговец: характеристики) должны совпадать",
    "mode_any": "любой из них",
    "mode_all": "все",
    "filter": "Фильтр модов…",
    "want": "Нужно",
    "avoid": "Избегать",
    "picked": "нужно: {want} · избегать: {avoid}",
    "also_title": "Также совпадает с более длинными модами, содержащими этот текст: {n}",
    "min_values": "Минимальные значения",
    "modifiers": "Моды",
    "minimum_aria": "{label}: минимум",
    "english_only": "Работает только с английским клиентом игры.",
    "data_generated": "Данные модов созданы {date}.",
    "how1_html": "<b>Текст в кавычках — шаблон.</b> {code} подсвечивает каждый предмет, в тексте которого он есть.",
    "how2_html": "<b>{bar} означает «или».</b> {code} совпадает с любым из вариантов.",
    "how3_html": "<b>{bang} в начале — отрицание.</b> {code} скрывает предметы с любым из них.",
    "how4_html": "<b>Шаблоны через пробел должны совпасть все.</b> {code} — {example}",
    "r2_title": "Regex PoE2 — поиск Waystone, Tablet и у торговца",
    "r2_desc": "Бесплатный конструктор regex для Path of Exile 2: строки поиска в тайнике и у торговца для "
               "Waystone, Precursor Tablet и товаров торговца в пределах 250 символов.",
    "r2_h1": "Конструктор regex PoE2",
    "r2_lead": "Собирайте строки поиска для тайника и торговца: Waystone, Precursor Tablet и товары "
               "торговца. Выберите, что нужно и чего избегать, скопируйте и вставьте в игре.",
    "tab_waystones": "Waystones",
    "tab_tablets": "Tablets",
    "tab_vendor": "Торговец",
    "r2_waystone_note_html": "Модов Waystone: {n}. <b>{want}</b> подсвечивает карты с ними, "
                             "<b>{avoid}</b> скрывает карты с ними.",
    "r2_tablet_note": "Модов Precursor Tablet: {n}.",
    "r2_vendor_note": "Отметьте нужные характеристики и задайте минимум. Полезно при прокачке: сапоги со "
                      "скоростью передвижения, оружие с +уровнем умений, сопротивления.",
    "r2_placeholder": "Выберите моды, чтобы собрать строку поиска",
    "r2_paste": "Вставьте в поиск тайника, торговца или устройства карт.",
    "r2_how_title": "Как работает regex в поиске PoE2",
    "r2_how_example": "тир 15+ без этого мода.",
    "r2_q1": "Как пользоваться regex в Path of Exile 2?",
    "r2_a1": "Откройте тайник, окно торговца или устройство карт, нажмите на поле поиска и вставьте "
             "созданный текст — подходящие предметы подсветятся. Всё в кавычках — регулярное выражение; "
             "! в начале означает «не совпадает».",
    "r2_q2": "Почему ограничение 250 символов?",
    "r2_a2": "Поле поиска в игре принимает не больше 250 символов. Конструктор берёт самый короткий фрагмент "
             "каждого мода, которого нет ни в одном другом моде, поэтому модов помещается гораздо больше, "
             "чем с полными текстами.",
    "r2_q3": "Работает ли с игрой на другом языке?",
    "r2_a3": "Нет. Поиск сравнивает текст, который показывает клиент, а тексты модов здесь на английском. "
             "Переключите клиент на английский или измените фрагменты.",
    "r2_q4": "Списки модов актуальны?",
    "r2_a4": "Моды Waystone берутся из данных характеристик самой игры, моды Tablet — из списка характеристик "
             "официального сайта trade; они создаются заново при каждом обновлении сайта.",
    "r1_title": "Regex PoE — карты, торговец, контракты Heist и Logbook",
    "r1_desc": "Бесплатный конструктор regex для Path of Exile: количество и плохие моды на редких картах "
               "(включая T17), товары торговца при прокачке со связками и цветами, контракты Heist и Expedition "
               "Logbook — со ссылкой для обмена, в пределах 250 символов.",
    "r1_h1": "Конструктор regex PoE",
    "r1_lead": "Строки поиска для тайника и торговца: редкие карты, снаряжение для прокачки, контракты Heist "
               "и Expedition Logbook. Выберите, что нужно и что ваш билд не вытянет, затем скопируйте текст "
               "или поделитесь ссылкой.",
    "tab_maps": "Карты",
    "tab_heist": "Heist",
    "tab_logbooks": "Logbooks",
    "r1_maps_note_html": "Строк модов карт: {n}. <b>{want}</b> подсвечивает карты с ними, "
                         "<b>{avoid}</b> скрывает карты с любым из них.",
    "quick_avoid": "Быстро избегать:",
    "quick_avoid_aria": "Готовые наборы для исключения",
    "preset_count": "модов: {n}",
    "preset_regen": "Без регена",
    "preset_leech": "Без лича",
    "preset_curses": "Проклятия",
    "preset_maxres": "Макс. сопр.",
    "preset_thorns": "Шипы",
    "preset_block": "Блок",
    "preset_flasks": "Флаконы",
    "hide_t17": "Скрыть только-T17 ({n})",
    "t17_title": "Встречается только на картах 17 тира",
    "r1_vendor_note": "Список покупок у торговца при прокачке: отметьте характеристики и задайте минимум. "
                      "При «любой из них» предмету нужна одна отмеченная, при «все» — каждая.",
    "sockets": "Гнёзда",
    "linked_group": "Связанная группа",
    "linked_aria": "Связанные гнёзда",
    "link_any": "Любая",
    "link_n": "{n}-линк",
    "red": "Красные",
    "green": "Зелёные",
    "blue": "Синие",
    "colour_aria": "{colour} гнёзда",
    "sockets_note": "Цвета считаются внутри одной связанной группы: например, 3-линк с 1 красным, 1 зелёным "
                    "и 1 синим найдёт любой порядок R-G-B. Гнёзда всегда действуют вместе с характеристиками.",
    "stats": "Характеристики",
    "r1_heist_note": "Контракты и Blueprint Heist. Минимальные значения, уровни профессий и моды действуют "
                     "одновременно.",
    "job_title": "Требуемый уровень профессии",
    "job_note": "Подсвечивает контракты, требующие профессию этого уровня или выше — чем выше уровень, тем "
                "лучше награды. В Blueprint несколько профессий; каждая отмеченная должна в нём быть.",
    "job_label": "{job}: уровень",
    "r1_logbook_note": "Expedition Logbook: выберите фракцию и бонусы областей, избегайте модов, которые ваш "
                       "билд не вытянет.",
    "factions": "Фракции",
    "bonuses": "Бонусы областей и боссы",
    "r1_placeholder": "Выберите значения или моды, чтобы собрать строку поиска",
    "r1_apply_note": "Минимальные значения и исключённые моды всегда действуют вместе. Ссылка открывает эту "
                     "вкладку с тем же выбором.",
    "r1_how_title": "Как работает поиск",
    "r1_how_example": "количество 90%+ без запрета регенерации.",
    "r1_q1": "Как пользоваться regex для карт в Path of Exile?",
    "r1_a1": "Откройте тайник или устройство карт, нажмите на поле поиска и вставьте созданный текст. "
             "Подходящие карты подсветятся. Исключённые моды начинаются с !, поэтому карты с любым из них "
             "останутся тёмными.",
    "r1_q2": "Каких модов избегать?",
    "r1_a2": "Зависит от билда. Чаще всего исключают «Players cannot Regenerate», моды на лич для билдов на "
             "личе, «Players are Cursed with ...», сниженные максимальные сопротивления и моды "
             "Physical/Elemental Thorns для ближнего боя. Готовые наборы над списком отмечают их одним кликом.",
    "r1_q3": "Почему некоторые фрагменты выглядят странно, например «ve .*% increased ar»?",
    "r1_a3": "Каждый мод получает самый короткий кусок текста, которого нет ни в другом моде карт, ни в "
             "названии карты, ни в её свойствах. Если обе половины вокруг числа встречаются в других модах, "
             "фрагмент перекрывает число через .* — поиск в игре это поддерживает.",
    "r1_q4": "Поддерживаются карты 17 тира?",
    "r1_a4": "Да. Моды, которые встречаются только на картах 17 тира, отмечены T17 и их можно скрыть. Пороги "
             "также охватывают строки More Maps / More Scarabs / More Currency и шансы превращения карт.",
    "r1_q5": "Список проверен на настоящих картах?",
    "r1_a5": "Каждый фрагмент проверен на редких картах 14–17 тира с официального сайта trade: каждая строка "
             "мода совпала со своим фрагментом, и ни один фрагмент не совпал с чужой строкой. Контракты и "
             "Blueprint Heist и Expedition Logbook проверены так же.",
    "r1_q6": "Как поделиться своим regex?",
    "r1_a6": "Нажмите «Копировать ссылку». Ссылка открывает ту же вкладку с теми же порогами и модами, так "
             "что соклановец сразу вставит её в поиск тайника.",
    "r1_q7": "Как работает поиск гнёзд у торговца?",
    "r1_a7": "Выберите размер связанной группы и нужные цвета. Конструктор выписывает каждый порядок цветов "
             "для одной группы (R-G-B, G-R-B, ...), поэтому 3-линк с красным, зелёным и синим найдётся при "
             "любом расположении гнёзд.",
    "r1_q8": "Какие бонусы Expedition Logbook можно искать?",
    "r1_a8": "Четыре фракции, бонусы областей — количество артефактов, радиус взрыва, остатки и метки "
             "сундуков — и боссов логбука. Моды работают как моды карт.",
    "in_title": "Калькулятор Instill PoE2 — список Distilled Emotions для амулета",
    "in_desc": "Все {n} рецептов instill в Path of Exile 2: какие Distilled Emotions и в каком порядке дают "
               "каждый notable на амулете, с поиском по названию и эффекту.",
    "in_h1": "Калькулятор Instill PoE2",
    "in_lead": "Какие три Distilled Emotions дают какой notable на амулете — и какой notable получится из "
               "ваших эмоций. Порядок важен: те же эмоции в другом порядке дают другой notable.",
    "in_make": "Что дадут мои эмоции?",
    "in_slot": "Слот {n}",
    "in_slot_aria": "Эмоция в слоте {n}",
    "in_pick": "Выберите эмоцию для каждого слота.",
    "in_none": "Ни один notable не использует эти три эмоции в таком порядке. Попробуйте другой порядок — "
               "каждый порядок это отдельный рецепт.",
    "in_find": "Найти notable",
    "in_search": "Поиск по названию или эффекту — например, chaos, charm, freeze",
    "in_search_aria": "Поиск notable",
    "in_owned": "Только рецепты, которые я могу сделать из",
    "in_owned_aria": "Ваши эмоции",
    "in_tiers": "Уровни эмоций:",
    "in_count": "notable: {n}",
    "in_count_of": "{shown} из {n} notable",
    "in_recipe_aria": "Рецепт: {list}",
    "in_data": "Данные созданы {date}.",
    "in_q1": "Как работает instill амулета в Path of Exile 2?",
    "in_a1": "На амулет помещают три Distilled Emotions, и он получает зачарование, которое даёт один "
             "notable пассивного дерева, даже если тот не связан с вашим деревом. Калькулятор показывает "
             "каждый notable с нужными эмоциями.",
    "in_q2": "Важен ли порядок эмоций?",
    "in_a2": "Да. Те же три эмоции в другом порядке дают другой notable — например, Isolation, Ire, Disgust "
             "даёт Void, а Ire, Disgust, Isolation — Revenge. Рецепты показаны в порядке слотов.",
    "in_q3": "Откуда эти данные?",
    "in_a3": "Рецепты взяты из данных игры (через Exiled Exchange 2), описания notable — из пассивного дерева "
             "и описаний характеристик игры (через RePoE); они создаются заново при каждом обновлении сайта.",
    "ec_poe2_title": "Экономика PoE2 — цены валюты, рун и эссенций",
    "ec_poe2_desc": "Актуальные цены Path of Exile 2: курс Divine и Exalted Orb, руны, эссенции, soul cores, "
                    "uncut gems — с изменением за 24 часа, 7 и 30 дней.",
    "ec_poe1_title": "Экономика PoE — цены валюты, уников и скарабеев",
    "ec_poe1_desc": "Актуальные цены Path of Exile: курс Divine Orb, уникальные предметы, скарабеи, эссенции, "
                    "гадальные карты — с изменением за 24 часа, 7 и 30 дней и историей цены за лигу.",
    "ec_live": "актуальные цены",
    "ec_h1": "Экономика {game}",
    "ec_lead_poe1": "Цены валюты и уникальных предметов в текущей лиге с изменением за день, неделю и месяц — "
                    "нажмите на строку, чтобы открыть историю цены.",
    "ec_lead_poe2": "Цены валюты и расходников в текущей лиге с изменением за день, неделю и месяц — нажмите "
                    "на строку, чтобы открыть историю цены.",
    "ec_game_aria": "Игра",
    "ec_league": "Лига",
    "ec_loading_leagues": "Загрузка…",
    "ec_search": "Поиск предметов по названию…",
    "ec_hide_low": "Скрыть ненадёжные цены",
    "ec_category_aria": "Категория",
    "ec_col_item": "Предмет",
    "ec_col_value": "Цена",
    "ec_col_volume": "Объём",
    "ec_col_listed": "Лотов",
    "ec_col_vol_listed": "Объём / лотов",
    "ec_col_spark": "Последние 7 дней",
    "ec_loading": "Загрузка цен…",
    "ec_source_html": "Цены с {link}, обновляются каждые 30 минут.",
    "ec_history_loading": "Загрузка истории цены…",
    "ec_history_short": "Для этого предмета пока мало истории цены.",
    "ec_history_error": "История цены сейчас недоступна.",
    "ec_now": "Сейчас",
    "ec_low": "Минимум лиги",
    "ec_high": "Максимум лиги",
    "ec_since": "С {date}",
    "ec_show_table": "Показать таблицу данных",
    "ec_day": "День",
    "ec_price_unit": "Цена ({unit})",
    "ec_chart_aria": "История цены, дней: {n}, от {from} до {to} {unit}",
    "ec_low_tag": "ненадёжная цена",
    "ec_results": "результатов: {n}",
    "ec_no_results": "Ничего не найдено",
    "ec_for_query": "по запросу «{q}» во всех категориях",
    "ec_top": "(показаны первые {n})",
    "ec_searching": "поиск в категориях {loaded}/{total}…",
    "ec_click_row": "нажмите на строку для истории цены",
    "ec_items": "предметов: {n}",
    "ec_updated": "обновлено {time}",
    "ec_prices_error": "Цены сейчас недоступны. Попробуйте через несколько минут.",
    "ec_leagues_error": "Список лиг сейчас недоступен. Попробуйте через несколько минут.",
    "ec_q1": "Откуда эти цены?",
    "ec_a1": "С poe.ninja, который собирает данные биржи валют и публичных вкладок тайника. Цены обновляются "
             "каждые 30 минут.",
    "ec_q2": "Что значат столбцы 24h, 7d и 30d?",
    "ec_a2": "Изменение цены за последний день, неделю и месяц. 24h и 7d берутся из истории цен poe.ninja; "
             "30d — из ежедневных записей этого сайта, поэтому заполняется в первый месяц лиги.",
    "ec_q3": "Нужно ли знать категорию предмета?",
    "ec_a3": "Нет. Введите хотя бы две буквы названия, и результаты придут сразу из всех категорий, каждый с "
             "пометкой категории.",
    "ec_q4": "Можно ли увидеть, как менялась цена за лигу?",
    "ec_a4": "Да — нажмите на любую строку, чтобы открыть историю цены за всю лигу с минимумом, максимумом и "
             "изменением с начала лиги.",
    "ec_q5": "Что значит «ненадёжная цена» у уникальных предметов?",
    "ec_a5": "Цена основана менее чем на 10 лотах, поэтому может сильно отличаться от реальной. Такие предметы "
             "по умолчанию скрыты; снимите отметку «Скрыть ненадёжные цены», чтобы их увидеть. Цены уников есть "
             "только для Path of Exile 1 — у Path of Exile 2 нет публичных данных тайников.",
    "ec_q6": "Как оценить редкий предмет?",
    "ec_a6": "Здесь предметы-валюта. Редкие и уникальные предметы оценивайте бесплатным приложением PoE Price "
             "Check — оно читает предмет под курсором и ищет на официальном сайте trade.",
}


def _fields(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def check() -> None:
    """Komplet kluczy i identyczne placeholdery w kazdym jezyku - inaczej build przerywa."""
    base = T["en"]
    problems = []
    for lang, table in T.items():
        missing = set(base) - set(table)
        extra = set(table) - set(base)
        if missing or extra:
            problems.append(f"{lang}: brakuje {sorted(missing)}, nadmiar {sorted(extra)}")
        for key in set(base) & set(table):
            if _fields(base[key]) != _fields(table[key]):
                problems.append(f"{lang}.{key}: placeholdery {sorted(_fields(table[key]))} "
                                f"zamiast {sorted(_fields(base[key]))}")
            if not key.endswith("_html") and re.search(r"<[a-z/]", table[key]):
                problems.append(f"{lang}.{key}: znacznik HTML w kluczu bez _html")
    if problems:
        raise SystemExit("Teksty narzedzi niezgodne:\n  " + "\n  ".join(problems))


def texts(lang: str) -> dict[str, str]:
    return T.get(lang, T["en"])
