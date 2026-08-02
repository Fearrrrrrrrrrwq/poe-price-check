/**
 * Zbieracz telemetrii i zrodlo danych panelu dla poe-price-check.
 *
 * Sygnaly trafiaja do arkusza Google, a pod adresem /exec stoi endpoint JSON -
 * bez serwera, bez bazy, bez kosztow.
 *
 * Wdrozenie:
 *   1. Utworz nowy arkusz Google.
 *   2. Rozszerzenia -> Apps Script.
 *   3. Wklej ten plik jako Kod.gs, a dashboard.html jako plik HTML o nazwie
 *      "dashboard" (Plik -> Nowy -> Plik HTML).
 *   4. Wdroz -> Nowe wdrozenie -> "Aplikacja internetowa".
 *      "Wykonaj jako": Ja.  "Kto ma dostep": Wszyscy.
 *   5. Ustaw ADMIN_USER i ADMIN_PASS ponizej.
 *   6. URL konczacy sie na /exec wklej do config.json jako "telemetry_url"
 *      oraz do TELEMETRY_URL w web/build.py, zeby panel znal go od reki.
 *
 * WAZNE: po kazdej zmianie kodu trzeba zrobic Wdroz -> Zarzadzaj wdrozeniami
 * -> Edytuj -> Wersja: Nowa. Bez tego pod /exec dziala nadal stara wersja.
 *
 * Panel na stronie pyta POST-em, z loginem i haslem w tresci zapytania.
 * Ten sam adres otwarty w przegladarce pokazuje zapasowy panel HTML -
 * wtedy dane trzeba podac w adresie: /exec?user=...&pass=...
 *
 * UWAGA: nie zapisujemy adresow IP. Apps Script ich nie udostepnia i tak ma
 * zostac - losowy identyfikator instalacji wystarczy do liczenia uzytkownikow.
 */

/**
 * LOGIN I HASLO do statystyk. Zmien oba na wlasne.
 *
 * Sprawdzanie odbywa sie TUTAJ, po stronie serwera - i to jest jedyne miejsce,
 * gdzie ma ono sens. Strona z panelem jest statyczna, wiec cokolwiek
 * sprawdzalaby sama w przegladarce, kazdy odczytalby z zrodla.
 *
 * Puste haslo = panel otwarty dla kazdego, kto zna adres.
 */
var ADMIN_USER = 'admin';
var ADMIN_PASS = 'ZMIEN-MNIE-na-dlugie-losowe-haslo';

var SHEET_NAME = 'telemetria';
var HEADERS = ['czas', 'id', 'wersja', 'system', 'jezyk', 'liga', 'transport',
               'wycen', 'bledow', 'minut'];

var COL = {czas: 0, id: 1, wersja: 2, system: 3, jezyk: 4, liga: 5,
           transport: 6, wycen: 7, bledow: 8, minut: 9};

var DAY_MS = 24 * 60 * 60 * 1000;

/**
 * Ile ostatnich wierszy czytamy. Kazdy uzytkownik dosyla sygnal co 6 godzin,
 * wiec przy 100 osobach to ~400 wierszy dziennie. Bez limitu odczyt calego
 * arkusza po roku trwalby kilkanascie sekund i lapal limit czasu Apps Script.
 */
var MAX_ROWS = 50000;

/** Odswiezanie panelu nie ma sensu czesciej niz raz na minute. */
var CACHE_SECONDS = 60;

/** Po tylu dniach wiersze idzie skasowac - patrz trimOldRows_(). */
var KEEP_DAYS = 180;

/** Powyzej tego odsetka nieudanych wycen zapala sie ostrzezenie. */
var FAILURE_ALERT = 0.15;


function sheet_() {
  var book = SpreadsheetApp.getActiveSpreadsheet();
  var tab = book.getSheetByName(SHEET_NAME);
  if (!tab) {
    tab = book.insertSheet(SHEET_NAME);
    tab.appendRow(HEADERS);
    tab.setFrozenRows(1);
  }
  return tab;
}


/**
 * Odbior sygnalu z aplikacji, a takze zapytania panelu o statystyki.
 *
 * Panel pyta POST-em, a nie GET-em, zeby login i haslo szly w tresci zapytania
 * zamiast w adresie - adresy laduja w historii przegladarki i w logach
 * wykonania Apps Script.
 *
 * Naglowek text/plain jest tu celowy: przy application/json przegladarka
 * wysyla najpierw zapytanie OPTIONS, a Apps Script na nie nie odpowiada.
 */
function doPost(e) {
  var data = {};
  try {
    data = JSON.parse(e.postData.contents) || {};
  } catch (err) {
    data = {};
  }

  if (data.action === 'stats') {
    if (!authorised_(data.user, data.pass)) {
      return jsonOut_(JSON.stringify({error: 'unauthorised'}));
    }
    return jsonOut_(cachedStats_(data.days));
  }

  try {
    sheet_().appendRow([
      new Date(),
      String(data.id || '').slice(0, 32),
      String(data.version || ''),
      String(data.os || ''),
      String(data.language || ''),
      String(data.league || ''),
      String(data.transport || ''),
      Number(data.checks || 0),
      Number(data.failures || 0),
      Number(data.uptime_min || 0)
    ]);
  } catch (err) {
    // Zly sygnal nie moze wywrocic zbieracza - po prostu go pomijamy.
  }
  return ContentService.createTextOutput('ok');
}


/** Czyta ostatnie MAX_ROWS wierszy. Sygnaly dopisujemy, wiec nowe sa na dole. */
function readRows_() {
  var tab = sheet_();
  var last = tab.getLastRow();
  if (last < 2) return [];
  var first = Math.max(2, last - MAX_ROWS + 1);
  return tab.getRange(first, 1, last - first + 1, HEADERS.length).getValues();
}


/**
 * Rozklad wartosci w kolumnie - liczony po unikalnych instalacjach, nie po
 * wierszach. Inaczej ktos, kto trzyma program wlaczony calymi dniami, przebilby
 * dziesieciu zwyklych uzytkownikow.
 */
function breakdown_(rows, column, limit) {
  var seen = {};
  rows.forEach(function (row) {
    var key = String(row[column] || '').trim() || '(brak)';
    if (!seen[key]) seen[key] = {};
    seen[key][row[COL.id]] = true;
  });

  var out = Object.keys(seen).map(function (key) {
    return {name: key, count: Object.keys(seen[key]).length};
  });
  out.sort(function (a, b) { return b.count - a.count; });

  var total = 0;
  out.forEach(function (item) { total += item.count; });
  out.forEach(function (item) {
    item.share = total ? Math.round(item.count * 1000 / total) / 10 : 0;
  });

  return out.slice(0, limit || 8);
}


/** Odsetek nieudanych wycen w zadanym przedziale czasu. */
function failureRate_(rows, fromMs, toMs) {
  var checks = 0, failures = 0;
  rows.forEach(function (row) {
    var stamp = new Date(row[COL.czas]).getTime();
    if (stamp < fromMs || stamp >= toMs) return;
    checks += Number(row[COL.wycen] || 0);
    failures += Number(row[COL.bledow] || 0);
  });
  var total = checks + failures;
  return {checks: checks, failures: failures,
          rate: total ? failures / total : 0, total: total};
}


function stats_(days) {
  days = Math.min(Math.max(Number(days) || 14, 1), 90);

  var rows = readRows_();
  var now = new Date().getTime();
  var zone = Session.getScriptTimeZone();

  var today = {}, week = {}, month = {}, all = {};
  var firstSeen = {};      // instalacja -> najwczesniejszy sygnal
  var daysSeen = {};       // instalacja -> zbior dni, w ktorych byla widoczna
  var checks = 0, failures = 0, minutes = 0, sessions = 0;
  var perDay = {};

  rows.forEach(function (row) {
    var stamp = new Date(row[COL.czas]).getTime();
    if (!stamp) return;
    var age = now - stamp;
    var id = row[COL.id];
    if (!id) return;

    all[id] = true;
    if (age < DAY_MS) today[id] = true;
    if (age < 7 * DAY_MS) week[id] = true;
    if (age < 30 * DAY_MS) month[id] = true;

    if (!firstSeen[id] || stamp < firstSeen[id]) firstSeen[id] = stamp;

    var key = Utilities.formatDate(new Date(stamp), zone, 'yyyy-MM-dd');
    if (!daysSeen[id]) daysSeen[id] = {};
    daysSeen[id][key] = true;

    var rowChecks = Number(row[COL.wycen] || 0);
    var rowFails = Number(row[COL.bledow] || 0);
    checks += rowChecks;
    failures += rowFails;

    var length = Number(row[COL.minut] || 0);
    if (length > 0) { minutes += length; sessions += 1; }

    if (age < days * DAY_MS) {
      if (!perDay[key]) perDay[key] = {users: {}, checks: 0, failures: 0, fresh: {}};
      perDay[key].users[id] = true;
      perDay[key].checks += rowChecks;
      perDay[key].failures += rowFails;
    }
  });

  // Nowi tego dnia - instalacja, ktorej pierwszy sygnal wypadl wlasnie wtedy.
  Object.keys(firstSeen).forEach(function (id) {
    var key = Utilities.formatDate(new Date(firstSeen[id]), zone, 'yyyy-MM-dd');
    if (perDay[key]) perDay[key].fresh[id] = true;
  });

  // Pelny szereg dni, takze pustych - inaczej wykres klamie o ciaglosci.
  var daily = [];
  for (var offset = days - 1; offset >= 0; offset--) {
    var day = Utilities.formatDate(new Date(now - offset * DAY_MS), zone, 'yyyy-MM-dd');
    var bucket = perDay[day];
    daily.push({
      date: day,
      users: bucket ? Object.keys(bucket.users).length : 0,
      fresh: bucket ? Object.keys(bucket.fresh).length : 0,
      checks: bucket ? bucket.checks : 0,
      failures: bucket ? bucket.failures : 0
    });
  }

  // Wracajacy: instalacja widziana w co najmniej dwoch roznych dniach. To
  // najuczciwsza miara przy sygnale co 6 godzin - jedno posiedzenie nie liczy
  // sie dwa razy.
  var installs = Object.keys(daysSeen);
  var returning = 0;
  installs.forEach(function (id) {
    if (Object.keys(daysSeen[id]).length >= 2) returning += 1;
  });

  var recent = failureRate_(rows, now - 7 * DAY_MS, now);
  var previous = failureRate_(rows, now - 14 * DAY_MS, now - 7 * DAY_MS);

  var level = 'ok';
  if (recent.total >= 20 && recent.rate >= FAILURE_ALERT) level = 'alert';
  else if (recent.total >= 20 && recent.rate >= FAILURE_ALERT / 2) level = 'warn';

  var newToday = 0;
  Object.keys(firstSeen).forEach(function (id) {
    if (now - firstSeen[id] < DAY_MS) newToday += 1;
  });

  return {
    updated: Utilities.formatDate(new Date(), zone, 'yyyy-MM-dd HH:mm'),
    timezone: zone,
    range_days: days,
    truncated: rows.length >= MAX_ROWS,
    rows_read: rows.length,

    users_today: Object.keys(today).length,
    users_week: Object.keys(week).length,
    users_month: Object.keys(month).length,
    users_total: installs.length,
    users_new_today: newToday,
    users_returning: returning,
    retention: installs.length
      ? Math.round(returning * 1000 / installs.length) / 10 : 0,

    checks: checks,
    failures: failures,
    checks_per_user: installs.length
      ? Math.round(checks * 10 / installs.length) / 10 : 0,
    pings: rows.length,
    avg_session: sessions ? Math.round(minutes / sessions) : 0,

    health: {
      level: level,
      rate: Math.round(recent.rate * 1000) / 10,
      rate_previous: Math.round(previous.rate * 1000) / 10,
      sample: recent.total
    },

    daily: daily,
    versions: breakdown_(rows, COL.wersja),
    languages: breakdown_(rows, COL.jezyk),
    leagues: breakdown_(rows, COL.liga),
    systems: breakdown_(rows, COL.system),
    transports: breakdown_(rows, COL.transport, 4)
  };
}


/** Wynik trzymamy chwile w pamieci - panel odswieza sie sam, arkusz nie musi. */
function cachedStats_(days) {
  var cache = CacheService.getScriptCache();
  var key = 'stats_' + days;
  var hit = cache.get(key);
  if (hit) return hit;

  var payload = JSON.stringify(stats_(days));
  try {
    cache.put(key, payload, CACHE_SECONDS);
  } catch (err) {
    // Powyzej 100 kB CacheService odmawia - trudno, policzymy jeszcze raz.
  }
  return payload;
}


/**
 * Porownanie o stalym czasie. Zwykle === konczy sie na pierwszej roznej
 * literze, wiec czas odpowiedzi zdradza, ile znakow hasla sie zgadza.
 */
function sameSecret_(given, expected) {
  given = String(given == null ? '' : given);
  expected = String(expected == null ? '' : expected);
  var diff = given.length ^ expected.length;
  for (var i = 0; i < given.length || i < expected.length; i++) {
    diff |= (given.charCodeAt(i) || 0) ^ (expected.charCodeAt(i) || 0);
  }
  return diff === 0;
}


function authorised_(user, pass) {
  if (!ADMIN_PASS) return true;  // brak hasla = panel jawny, swiadoma decyzja
  return sameSecret_(user, ADMIN_USER) && sameSecret_(pass, ADMIN_PASS);
}


function jsonOut_(text) {
  return ContentService.createTextOutput(text)
    .setMimeType(ContentService.MimeType.JSON);
}


/**
 * Kasuje wiersze starsze niz KEEP_DAYS.
 *
 * Podepnij pod wyzwalacz czasowy (Wyzwalacze -> Dodaj -> co tydzien). Bez tego
 * arkusz rosnie bez konca, a odczyt zaczyna lapac limit czasu.
 */
function trimOldRows_() {
  var tab = sheet_();
  var last = tab.getLastRow();
  if (last < 2) return;

  var stamps = tab.getRange(2, COL.czas + 1, last - 1, 1).getValues();
  var cutoff = new Date().getTime() - KEEP_DAYS * DAY_MS;

  // Wiersze sa dopisywane chronologicznie, wiec stare to zawsze poczatek.
  var stale = 0;
  while (stale < stamps.length
         && new Date(stamps[stale][0]).getTime() < cutoff) {
    stale += 1;
  }
  if (stale > 0) tab.deleteRows(2, stale);
}


/**
 * Zapasowy panel HTML pod tym samym adresem.
 *
 * Tutaj login i haslo ida w adresie, bo inaczej sie nie da - ramka ani pasek
 * adresu nie wysylaja POST-a. Dlatego to droga awaryjna: normalnie panel na
 * stronie pyta POST-em i haslo nie trafia do adresu.
 */
function doGet(e) {
  var params = (e && e.parameter) || {};

  if (!authorised_(params.user, params.pass)) {
    if (params.json) return jsonOut_(JSON.stringify({error: 'unauthorised'}));

    return HtmlService.createHtmlOutput(
      '<body style="background:#14110d;color:#92866e;font:15px system-ui;' +
      'padding:40px">Brak dostępu. Dopisz do adresu ' +
      '<code>?user=...&amp;pass=...</code>.</body>')
      .setTitle('Brak dostępu');
  }

  var days = params.days || 14;

  if (params.json) return jsonOut_(cachedStats_(days));

  var html = HtmlService.createHtmlOutputFromFile('dashboard').getContent();
  html = html.replace('__DATA__', cachedStats_(days));
  return HtmlService.createHtmlOutput(html)
    .setTitle('PoE Price Check - statystyki')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    // Panel na stronie osadza to w ramce, gdy pobranie JSON-a sie nie uda.
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
