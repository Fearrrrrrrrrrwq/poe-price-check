# Tresc strony /{lang}/community/ - publiczne, zagregowane statystyki uzycia.
# Same liczby ida z /api/public-stats (Cloudflare Function), tutaj tylko
# nazwy sekcji i opis. Klucze musza byc identyczne w kazdym jezyku, jak w C
# i PRIVACY.
COMMUNITY: dict[str, dict] = {}

COMMUNITY["en"] = {
    "title": "Community",
    "description": "Public, aggregated usage stats for PoE Price Check - how "
                   "many people use it, which systems, leagues and versions.",
    "heading": "Community stats",
    "intro": "The same anonymous counter described in the privacy policy, "
             "just made public instead of only visible to us. No individual "
             "installs, no error details - just totals and rounded shares.",
    "tile_installs": "Active installs",
    "tile_installs_week": "New this week",
    "tile_checks_week": "Checks this week",
    "tile_session": "Avg. session (min)",
    "section_systems": "Operating systems",
    "section_leagues": "Leagues",
    "section_versions": "Versions",
    "section_languages": "Languages",
    "section_transports": "Bridge transport",
    "updated_prefix": "Last updated:",
    "back": "Back to homepage",
}

COMMUNITY["pl"] = {
    "title": "Społeczność",
    "description": "Publiczne, zagregowane statystyki użycia PoE Price Check "
                   "- ile osób używa, jakie systemy, ligi i wersje.",
    "heading": "Statystyki społeczności",
    "intro": "Ten sam anonimowy licznik opisany w polityce prywatności, tylko "
             "jawny zamiast widoczny wyłącznie dla nas. Żadnych pojedynczych "
             "instalacji, żadnych szczegółów błędów - same sumy i zaokrąglone "
             "udziały.",
    "tile_installs": "Aktywne instalacje",
    "tile_installs_week": "Nowych w tym tygodniu",
    "tile_checks_week": "Wycen w tym tygodniu",
    "tile_session": "Śr. sesja (min)",
    "section_systems": "Systemy operacyjne",
    "section_leagues": "Ligi",
    "section_versions": "Wersje",
    "section_languages": "Języki",
    "section_transports": "Transport mostu",
    "updated_prefix": "Ostatnia aktualizacja:",
    "back": "Wróć na stronę główną",
}

COMMUNITY["de"] = {
    "title": "Community",
    "description": "Öffentliche, aggregierte Nutzungsstatistiken für PoE "
                   "Price Check - wie viele Nutzer, welche Systeme, Ligen "
                   "und Versionen.",
    "heading": "Community-Statistik",
    "intro": "Derselbe anonyme Zähler aus der Datenschutzerklärung, nur "
             "öffentlich statt nur für uns sichtbar. Keine einzelnen "
             "Installationen, keine Fehlerdetails - nur Summen und "
             "gerundete Anteile.",
    "tile_installs": "Aktive Installationen",
    "tile_installs_week": "Neu diese Woche",
    "tile_checks_week": "Prüfungen diese Woche",
    "tile_session": "Ø Sitzung (Min.)",
    "section_systems": "Betriebssysteme",
    "section_leagues": "Ligen",
    "section_versions": "Versionen",
    "section_languages": "Sprachen",
    "section_transports": "Brücken-Transport",
    "updated_prefix": "Zuletzt aktualisiert:",
    "back": "Zurück zur Startseite",
}

COMMUNITY["es"] = {
    "title": "Comunidad",
    "description": "Estadísticas de uso públicas y agregadas de PoE Price "
                   "Check - cuánta gente lo usa, qué sistemas, ligas y "
                   "versiones.",
    "heading": "Estadísticas de la comunidad",
    "intro": "El mismo contador anónimo descrito en la política de "
             "privacidad, solo que público en vez de visible únicamente "
             "para nosotros. Sin instalaciones individuales, sin detalles "
             "de errores - solo totales y porcentajes redondeados.",
    "tile_installs": "Instalaciones activas",
    "tile_installs_week": "Nuevas esta semana",
    "tile_checks_week": "Consultas esta semana",
    "tile_session": "Sesión media (min)",
    "section_systems": "Sistemas operativos",
    "section_leagues": "Ligas",
    "section_versions": "Versiones",
    "section_languages": "Idiomas",
    "section_transports": "Transporte del puente",
    "updated_prefix": "Última actualización:",
    "back": "Volver al inicio",
}

COMMUNITY["pt"] = {
    "title": "Comunidade",
    "description": "Estatísticas de uso públicas e agregadas do PoE Price "
                   "Check - quantas pessoas usam, quais sistemas, ligas e "
                   "versões.",
    "heading": "Estatísticas da comunidade",
    "intro": "O mesmo contador anônimo descrito na política de privacidade, "
             "só que público em vez de visível apenas para nós. Sem "
             "instalações individuais, sem detalhes de erros - só totais e "
             "porcentagens arredondadas.",
    "tile_installs": "Instalações ativas",
    "tile_installs_week": "Novas esta semana",
    "tile_checks_week": "Consultas esta semana",
    "tile_session": "Sessão média (min)",
    "section_systems": "Sistemas operacionais",
    "section_leagues": "Ligas",
    "section_versions": "Versões",
    "section_languages": "Idiomas",
    "section_transports": "Transporte da ponte",
    "updated_prefix": "Última atualização:",
    "back": "Voltar ao início",
}

COMMUNITY["ru"] = {
    "title": "Сообщество",
    "description": "Публичная, агрегированная статистика использования PoE "
                   "Price Check - сколько людей пользуется, какие системы, "
                   "лиги и версии.",
    "heading": "Статистика сообщества",
    "intro": "Тот же анонимный счётчик, описанный в политике "
             "конфиденциальности, только публичный, а не видимый только "
             "нам. Никаких отдельных установок, никаких деталей ошибок - "
             "только суммы и округлённые доли.",
    "tile_installs": "Активных установок",
    "tile_installs_week": "Новых за неделю",
    "tile_checks_week": "Проверок за неделю",
    "tile_session": "Средняя сессия (мин)",
    "section_systems": "Операционные системы",
    "section_leagues": "Лиги",
    "section_versions": "Версии",
    "section_languages": "Языки",
    "section_transports": "Транспорт моста",
    "updated_prefix": "Последнее обновление:",
    "back": "Вернуться на главную",
}
