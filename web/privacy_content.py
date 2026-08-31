# Tresc strony /{lang}/privacy/. Osobny slownik, bo to prawny tekst, a nie
# marketing - trzymanie go z dala od C[lang] ulatwia pilnowanie, ktory jest
# ktory. Klucze musza byc identyczne w kazdym jezyku, jak w C.
PRIVACY: dict[str, dict] = {}

PRIVACY["en"] = {
    "title": "Privacy Policy",
    "description": "How poepricecheck.eu collects, uses and protects data, "
                   "including Google AdSense advertising and cookies.",
    "updated": "Last updated: 2026-08-30",
    "sections": [
        ("Who this applies to", [
            "This policy covers the website you are on now (poepricecheck.eu). "
            "The desktop application has its own, much stricter data practices, "
            "described in the app itself — it never sends anything from your "
            "machine except queries to the official Path of Exile trade API.",
            "This is an independent hobby project, not a company. For any question "
            "about this policy, reach out on Discord or open an issue on GitHub — "
            "see the links in the footer.",
        ]),
        ("Anonymous visit counter", [
            "To see roughly how many people visit, the site hashes your IP address "
            "together with a secret salt that changes every 24 hours, and stores "
            "only that hash — never the IP itself. This makes it impossible to "
            "link visits across days or identify you personally.",
            "No cookies are used for this counter, and it is skipped entirely if "
            "your browser sends a Do Not Track signal.",
        ]),
        ("Advertising (Google AdSense)", [
            "This site shows ads served by Google AdSense to help cover hosting "
            "costs. Google and its advertising partners may use cookies, device "
            "identifiers, or similar technologies to show ads based on your visits "
            "to this and other sites.",
            "If you are in the European Economic Area, the United Kingdom, or "
            "Switzerland, a consent banner (Google's Funding Choices) appears "
            "before any personalized ad is shown, letting you agree, refuse, or "
            "manage your choices per purpose and partner.",
            "You can review or change your ad personalization settings at Google's "
            "Ads Settings (adssettings.google.com), and learn more about how Google "
            "uses data at policies.google.com/technologies/partner-sites.",
        ]),
        ("Admin panel", [
            "A password-protected panel exists for the site operator to view the "
            "visit counter. It uses a session cookie (HttpOnly, not readable by "
            "scripts) that is set only after a successful login and never applies "
            "to regular visitors.",
        ]),
        ("Hosting", [
            "The site is hosted on Cloudflare Pages, with the visit counter and "
            "admin login stored in a Cloudflare D1 database. No data is sold or "
            "shared with anyone beyond what's described above.",
        ]),
        ("Your rights", [
            "Because visit data is anonymized (hashed, rotated daily, no "
            "identifiers), there is normally nothing tied to you to access or "
            "delete. For anything related to ad personalization, use Google's Ads "
            "Settings linked above. For any other question, contact us via the "
            "links in the footer.",
        ]),
        ("Children", [
            "This site is not directed at children under 13 (or the equivalent "
            "minimum age in your country) and does not knowingly collect data "
            "from them.",
        ]),
        ("Changes", [
            "This policy may be updated as the site changes. The date above "
            "reflects the latest revision.",
        ]),
    ],
    "back": "Back to homepage",
}

PRIVACY["pl"] = {
    "title": "Polityka prywatności",
    "description": "Jak poepricecheck.eu zbiera, wykorzystuje i chroni dane, w tym "
                   "reklamy Google AdSense i pliki cookie.",
    "updated": "Ostatnia aktualizacja: 2026-08-30",
    "sections": [
        ("Kogo to dotyczy", [
            "Ta polityka dotyczy strony, na której właśnie jesteś "
            "(poepricecheck.eu). Aplikacja desktopowa ma własne, dużo "
            "bardziej restrykcyjne zasady dotyczące danych, opisane w samej "
            "aplikacji — nigdy nie wysyła niczego poza Twój komputer, "
            "poza zapytaniami do oficjalnego API handlu Path of Exile.",
            "To niezależny projekt hobbystyczny, nie firma. W razie pytań "
            "o tę politykę napisz na Discordzie albo załóż "
            "zgłoszenie na GitHubie — linki w stopce.",
        ]),
        ("Anonimowy licznik odwiedzin", [
            "Żeby orientacyjnie wiedzieć, ile osób odwiedza stronę, "
            "licznik haszuje Twój adres IP razem z tajną solą, która "
            "zmienia się co 24 godziny, i zapisuje tylko ten hasz — nigdy "
            "sam adres IP. Dzięki temu nie da się połączyć "
            "wizyt z różnych dni ani Cię zidentyfikować.",
            "Licznik nie używa plików cookie i jest całkowicie "
            "pomijany, jeśli Twoja przeglądarka wysyła sygnał "
            "Do Not Track.",
        ]),
        ("Reklamy (Google AdSense)", [
            "Strona wyświetla reklamy Google AdSense, żeby pokryć "
            "koszty utrzymania. Google i jego partnerzy reklamowi mogą "
            "używać plików cookie, identyfikatorów urządzenia "
            "lub podobnych technologii, żeby wyświetlać reklamy "
            "dopasowane na podstawie Twoich wizyt na tej i innych stronach.",
            "Jeśli jesteś w Europejskim Obszarze Gospodarczym, Wielkiej "
            "Brytanii lub Szwajcarii, przed wyświetleniem spersonalizowanej "
            "reklamy pojawia się baner zgody (Google Funding Choices), w "
            "którym możesz się zgodzić, odmówić albo "
            "zarządzać wyborami dla poszczególnych celów i "
            "partnerów.",
            "Ustawienia personalizacji reklam możesz sprawdzić i zmienić "
            "w Ustawieniach reklam Google (adssettings.google.com), a więcej o "
            "wykorzystaniu danych przez Google przeczytasz na "
            "policies.google.com/technologies/partner-sites.",
        ]),
        ("Panel administracyjny", [
            "Istnieje chroniony hasłem panel dla operatora strony, żeby "
            "móc podejrzeć licznik odwiedzin. Używa ciasteczka sesji "
            "(HttpOnly, nieczytelnego dla skryptów), które jest ustawiane "
            "wyłącznie po udanym logowaniu i nigdy nie dotyczy zwykłych "
            "odwiedzających.",
        ]),
        ("Hosting", [
            "Strona jest hostowana na Cloudflare Pages, a licznik odwiedzin i "
            "logowanie do panelu przechowywane są w bazie Cloudflare D1. "
            "Żadne dane nie są sprzedawane ani udostępniane komukolwiek "
            "poza tym, co opisano powyżej.",
        ]),
        ("Twoje prawa", [
            "Ponieważ dane o odwiedzinach są zanonimizowane (zahaszowane, "
            "rotowane codziennie, bez identyfikatorów), zwykle nie ma nic "
            "przypisanego do Ciebie, do czego mógłbyś uzyskać "
            "dostęp albo co mógłbyś usunąć. W sprawach "
            "personalizacji reklam skorzystaj z Ustawień reklam Google powyżej. "
            "W innych sprawach napisz do nas przez linki w stopce.",
        ]),
        ("Dzieci", [
            "Strona nie jest kierowana do dzieci poniżej 13 roku życia (lub "
            "odpowiedniego minimalnego wieku w Twoim kraju) i świadomie nie "
            "zbiera od nich danych.",
        ]),
        ("Zmiany", [
            "Ta polityka może być aktualizowana wraz ze zmianami na "
            "stronie. Data powyżej odzwierciedla ostatnią rewizję.",
        ]),
    ],
    "back": "Wróć na stronę główną",
}

PRIVACY["de"] = {
    "title": "Datenschutzerklärung",
    "description": "Wie poepricecheck.eu Daten erhebt, nutzt und schützt, "
                   "einschließlich Google AdSense-Werbung und Cookies.",
    "updated": "Letzte Aktualisierung: 2026-08-30",
    "sections": [
        ("Geltungsbereich", [
            "Diese Erklärung gilt für die Website, auf der Sie sich gerade "
            "befinden (poepricecheck.eu). Die Desktop-Anwendung hat eigene, deutlich "
            "strengere Datenpraktiken, die in der App selbst beschrieben sind — "
            "sie sendet nie etwas von Ihrem Rechner, außer Anfragen an die "
            "offizielle Path-of-Exile-Handels-API.",
            "Dies ist ein unabhängiges Hobbyprojekt, kein Unternehmen. Fragen "
            "zu dieser Erklärung gerne über Discord oder als Issue auf "
            "GitHub — Links in der Fußzeile.",
        ]),
        ("Anonymer Besucherzähler", [
            "Um ungefähr zu wissen, wie viele Personen die Seite besuchen, "
            "hasht der Zähler Ihre IP-Adresse zusammen mit einem geheimen Salt, "
            "das sich alle 24 Stunden ändert, und speichert nur diesen Hash "
            "— niemals die IP-Adresse selbst. Dadurch lassen sich Besuche "
            "über verschiedene Tage hinweg nicht verknüpfen und Sie nicht "
            "identifizieren.",
            "Für diesen Zähler werden keine Cookies verwendet, und er wird "
            "komplett übersprungen, wenn Ihr Browser ein Do-Not-Track-Signal "
            "sendet.",
        ]),
        ("Werbung (Google AdSense)", [
            "Diese Seite zeigt Werbung von Google AdSense, um die Hosting-Kosten "
            "zu decken. Google und seine Werbepartner können Cookies, "
            "Geräte-Kennungen oder ähnliche Technologien verwenden, um "
            "Anzeigen basierend auf Ihren Besuchen auf dieser und anderen Seiten zu "
            "zeigen.",
            "Wenn Sie sich im Europäischen Wirtschaftsraum, im Vereinigten "
            "Königreich oder in der Schweiz befinden, erscheint vor jeder "
            "personalisierten Anzeige ein Einwilligungsbanner (Google Funding "
            "Choices), in dem Sie zustimmen, ablehnen oder Ihre Auswahl je Zweck "
            "und Partner verwalten können.",
            "Sie können Ihre Anzeigenpersonalisierung in den "
            "Google-Anzeigeneinstellungen (adssettings.google.com) einsehen und "
            "ändern; mehr zur Datennutzung durch Google unter "
            "policies.google.com/technologies/partner-sites.",
        ]),
        ("Admin-Bereich", [
            "Es existiert ein passwortgeschützter Bereich für den "
            "Seitenbetreiber, um den Besucherzähler einzusehen. Er verwendet "
            "ein Session-Cookie (HttpOnly, nicht per Skript auslesbar), das nur "
            "nach erfolgreichem Login gesetzt wird und normale Besucher nie "
            "betrifft.",
        ]),
        ("Hosting", [
            "Die Seite wird auf Cloudflare Pages gehostet; Besucherzähler und "
            "Admin-Login werden in einer Cloudflare-D1-Datenbank gespeichert. Es "
            "werden keine Daten verkauft oder mit Dritten geteilt, außer wie "
            "oben beschrieben.",
        ]),
        ("Ihre Rechte", [
            "Da die Besuchsdaten anonymisiert sind (gehasht, täglich rotiert, "
            "ohne Kennungen), gibt es normalerweise nichts, das Ihnen zugeordnet "
            "werden könnte, um es einzusehen oder zu löschen. Für "
            "alles rund um Anzeigenpersonalisierung nutzen Sie die oben "
            "verlinkten Google-Anzeigeneinstellungen. Für andere Fragen "
            "kontaktieren Sie uns über die Links in der Fußzeile.",
        ]),
        ("Kinder", [
            "Diese Seite richtet sich nicht an Kinder unter 13 Jahren (oder dem "
            "entsprechenden Mindestalter in Ihrem Land) und erhebt wissentlich "
            "keine Daten von ihnen.",
        ]),
        ("Änderungen", [
            "Diese Erklärung kann bei Änderungen an der Seite "
            "aktualisiert werden. Das Datum oben zeigt die letzte Überarbeitung.",
        ]),
    ],
    "back": "Zurück zur Startseite",
}

PRIVACY["es"] = {
    "title": "Política de privacidad",
    "description": "Cómo poepricecheck.eu recopila, usa y protege los datos, "
                   "incluida la publicidad de Google AdSense y las cookies.",
    "updated": "Última actualización: 2026-08-30",
    "sections": [
        ("A quién aplica", [
            "Esta política cubre el sitio web en el que te encuentras "
            "(poepricecheck.eu). La aplicación de escritorio tiene sus propias "
            "prácticas de datos, mucho más estrictas, descritas en la "
            "propia app — nunca envía nada desde tu equipo salvo consultas "
            "a la API oficial de comercio de Path of Exile.",
            "Este es un proyecto independiente y personal, no una empresa. Para "
            "cualquier duda sobre esta política, escribe en Discord o abre un "
            "issue en GitHub — enlaces en el pie de página.",
        ]),
        ("Contador anónimo de visitas", [
            "Para saber aproximadamente cuánta gente visita el sitio, el "
            "contador aplica un hash a tu dirección IP junto con una clave "
            "secreta que cambia cada 24 horas, y guarda solo ese hash — nunca "
            "la IP en sí. Esto hace imposible enlazar visitas entre días "
            "o identificarte.",
            "Este contador no usa cookies y se omite por completo si tu navegador "
            "envía una señal Do Not Track.",
        ]),
        ("Publicidad (Google AdSense)", [
            "Este sitio muestra anuncios de Google AdSense para ayudar a cubrir "
            "los costes de hosting. Google y sus socios publicitarios pueden usar "
            "cookies, identificadores de dispositivo o tecnologías similares "
            "para mostrar anuncios según tus visitas a este y otros sitios.",
            "Si estás en el Espacio Económico Europeo, el Reino Unido o "
            "Suiza, aparece un banner de consentimiento (Google Funding Choices) "
            "antes de mostrar cualquier anuncio personalizado, donde puedes "
            "aceptar, rechazar o gestionar tus opciones por finalidad y socio.",
            "Puedes revisar o cambiar tu personalización de anuncios en la "
            "Configuración de anuncios de Google (adssettings.google.com), y "
            "saber más sobre cómo usa Google los datos en "
            "policies.google.com/technologies/partner-sites.",
        ]),
        ("Panel de administración", [
            "Existe un panel protegido con contraseña para que el operador "
            "del sitio consulte el contador de visitas. Usa una cookie de sesión "
            "(HttpOnly, no accesible por scripts) que solo se establece tras un "
            "inicio de sesión correcto y nunca afecta a los visitantes "
            "normales.",
        ]),
        ("Alojamiento", [
            "El sitio está alojado en Cloudflare Pages, con el contador de "
            "visitas y el inicio de sesión del panel guardados en una base de "
            "datos Cloudflare D1. No se vende ni comparte ningún dato con "
            "nadie más allá de lo descrito arriba.",
        ]),
        ("Tus derechos", [
            "Como los datos de visitas están anonimizados (con hash, rotados "
            "a diario, sin identificadores), normalmente no hay nada vinculado a "
            "ti que puedas consultar o borrar. Para todo lo relacionado con la "
            "personalización de anuncios, usa la Configuración de anuncios "
            "de Google enlazada arriba. Para cualquier otra duda, contáctanos "
            "a través de los enlaces del pie de página.",
        ]),
        ("Menores", [
            "Este sitio no está dirigido a menores de 13 años (o la edad "
            "mínima equivalente en tu país) y no recopila datos suyos a "
            "sabiendas.",
        ]),
        ("Cambios", [
            "Esta política puede actualizarse a medida que cambie el sitio. "
            "La fecha de arriba refleja la última revisión.",
        ]),
    ],
    "back": "Volver al inicio",
}

PRIVACY["pt"] = {
    "title": "Política de Privacidade",
    "description": "Como o poepricecheck.eu coleta, usa e protege dados, incluindo "
                   "anúncios do Google AdSense e cookies.",
    "updated": "Última atualização: 2026-08-30",
    "sections": [
        ("A quem se aplica", [
            "Esta política cobre o site em que você está agora "
            "(poepricecheck.eu). O aplicativo de desktop tem suas próprias "
            "práticas de dados, bem mais rígidas, descritas no próprio "
            "app — ele nunca envia nada do seu computador além de "
            "consultas à API oficial de comércio do Path of Exile.",
            "Este é um projeto independente e pessoal, não uma empresa. "
            "Para qualquer dúvida sobre esta política, fale no Discord ou "
            "abra uma issue no GitHub — links no rodapé.",
        ]),
        ("Contador anônimo de visitas", [
            "Para saber aproximadamente quantas pessoas visitam o site, o contador "
            "aplica hash ao seu endereço IP junto com um salt secreto que muda "
            "a cada 24 horas, e guarda apenas esse hash — nunca o IP em si. "
            "Isso torna impossível ligar visitas entre dias diferentes ou "
            "identificar você.",
            "Esse contador não usa cookies e é totalmente ignorado se o "
            "seu navegador enviar um sinal Do Not Track.",
        ]),
        ("Publicidade (Google AdSense)", [
            "Este site exibe anúncios do Google AdSense para ajudar a cobrir "
            "os custos de hospedagem. O Google e seus parceiros de publicidade "
            "podem usar cookies, identificadores de dispositivo ou tecnologias "
            "semelhantes para exibir anúncios com base nas suas visitas a "
            "este e a outros sites.",
            "Se você estiver no Espaço Econômico Europeu, Reino "
            "Unido ou Suíça, um banner de consentimento (Google Funding "
            "Choices) aparece antes de qualquer anúncio personalizado, "
            "permitindo que você aceite, recuse ou gerencie suas escolhas por "
            "finalidade e parceiro.",
            "Você pode revisar ou alterar sua personalização de "
            "anúncios nas Configurações de anúncios do Google "
            "(adssettings.google.com), e saber mais sobre como o Google usa dados "
            "em policies.google.com/technologies/partner-sites.",
        ]),
        ("Painel administrativo", [
            "Existe um painel protegido por senha para o operador do site "
            "consultar o contador de visitas. Ele usa um cookie de sessão "
            "(HttpOnly, não acessível por scripts) que só é "
            "definido após um login bem-sucedido e nunca afeta visitantes "
            "comuns.",
        ]),
        ("Hospedagem", [
            "O site é hospedado no Cloudflare Pages, com o contador de "
            "visitas e o login do painel armazenados em um banco de dados "
            "Cloudflare D1. Nenhum dado é vendido ou compartilhado com "
            "ninguém além do descrito acima.",
        ]),
        ("Seus direitos", [
            "Como os dados de visita são anonimizados (com hash, rotacionados "
            "diariamente, sem identificadores), normalmente não há nada "
            "vinculado a você para acessar ou excluir. Para tudo relacionado "
            "à personalização de anúncios, use as "
            "Configurações de anúncios do Google linkadas acima. "
            "Para qualquer outra dúvida, entre em contato pelos links no "
            "rodapé.",
        ]),
        ("Crianças", [
            "Este site não é direcionado a crianças menores de 13 "
            "anos (ou a idade mínima equivalente no seu país) e não "
            "coleta dados delas intencionalmente.",
        ]),
        ("Alterações", [
            "Esta política pode ser atualizada conforme o site mudar. A data "
            "acima reflete a última revisão.",
        ]),
    ],
    "back": "Voltar ao início",
}

PRIVACY["ru"] = {
    "title": "Политика конфиденциальности",
    "description": "Как poepricecheck.eu собирает, использует и защищает данные, включая рекламу Google AdSense и файлы cookie.",
    "updated": "Последнее обновление: 2026-08-30",
    "sections": [
        ("К чему это относится", [
            "Эта политика касается сайта, на котором вы сейчас находитесь (poepricecheck.eu). У десктопного приложения свои, гораздо более строгие правила обработки данных, описанные в самом приложении — оно никогда не отправляет ничего с вашего компьютера, кроме запросов к официальному торговому API Path of Exile.",
            "Это независимый любительский проект, а не компания. По любым вопросам об этой политике пишите в Discord или создайте issue на GitHub — ссылки в подвале сайта.",
        ]),
        ("Анонимный счётчик посещений", [
            "Чтобы примерно понимать, сколько людей заходит на сайт, счётчик хеширует ваш IP-адрес вместе с секретной солью, которая меняется каждые 24 часа, и сохраняет только этот хеш — никогда сам IP. Это делает невозможным связать посещения за разные дни или идентифицировать вас.",
            "Этот счётчик не использует cookie и полностью пропускается, если ваш браузер отправляет сигнал Do Not Track.",
        ]),
        ("Реклама (Google AdSense)", [
            "На сайте показывается реклама Google AdSense, чтобы покрыть расходы на хостинг. Google и его рекламные партнёры могут использовать cookie, идентификаторы устройств или похожие технологии, чтобы показывать рекламу на основе ваших посещений этого и других сайтов.",
            "Если вы находитесь в Европейской экономической зоне, Великобритании или Швейцарии, перед показом персонализированной рекламы появляется баннер согласия (Google Funding Choices), где можно согласиться, отказаться или управлять выбором по каждой цели и партнёру.",
            "Вы можете просмотреть или изменить персонализацию рекламы в Настройках рекламы Google (adssettings.google.com), а подробнее о том, как Google использует данные — на policies.google.com/technologies/partner-sites.",
        ]),
        ("Панель администратора", [
            "Существует защищённая паролем панель для оператора сайта, чтобы видеть счётчик посещений. Она использует сессионную cookie (HttpOnly, недоступную для скриптов), которая устанавливается только после успешного входа и никогда не касается обычных посетителей.",
        ]),
        ("Хостинг", [
            "Сайт размещён на Cloudflare Pages, счётчик посещений и вход в панель хранятся в базе данных Cloudflare D1. Никакие данные не продаются и не передаются кому-либо, кроме описанного выше.",
        ]),
        ("Ваши права", [
            "Поскольку данные о посещениях анонимизированы (хешированы, обновляются ежедневно, без идентификаторов), обычно нет ничего привязанного к вам, что можно было бы запросить или удалить. По всем вопросам персонализации рекламы используйте Настройки рекламы Google по ссылке выше. По любым другим вопросам свяжитесь с нами по ссылкам в подвале сайта.",
        ]),
        ("Дети", [
            "Этот сайт не предназначен для детей младше 13 лет (или соответствующего минимального возраста в вашей стране) и сознательно не собирает их данные.",
        ]),
        ("Изменения", [
            "Эта политика может обновляться по мере изменений на сайте. Дата выше отражает последнюю редакцию.",
        ]),
    ],
    "back": "Вернуться на главную",
}
