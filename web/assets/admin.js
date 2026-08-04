/* Panel statystyk.
 *
 * Strona jest wydawana tylko zalogowanym - pilnuje tego funkcja brzegowa
 * w functions/admin/_middleware.js. Tutaj nie ma juz zadnego hasla, zadnego
 * adresu endpointu ani niczego wrazliwego w pamieci przegladarki: sesja siedzi
 * w ciasteczku HttpOnly, ktorego ten skrypt nie widzi.
 *
 * CSP na /admin/* nie pozwala na zewnetrzne biblioteki ani na style
 * w atrybutach, wiec wykresy skladamy z elementow SVG, a szerokosci paskow
 * ustawiamy przez CSSOM (element.style.width), ktorego CSP nie obejmuje.
 */
(function () {
  'use strict';

  var PREFS = 'ppc-admin-prefs';   // tylko wybrany zakres dni, nic wiecej
  var REFRESH_MS = 5 * 60 * 1000;
  var SVG = 'http://www.w3.org/2000/svg';

  var board = document.getElementById('board');
  var updated = document.getElementById('updated');
  var who = document.getElementById('who');
  var refresh = document.getElementById('refresh');
  var alertBox = document.getElementById('alert');
  var meta = document.getElementById('meta');

  var nf = new Intl.NumberFormat('pl-PL');
  var state = { days: 14, tab: 'app', app: null, web: null };
  var timer = null;

  /** Kontener aktywnej zakladki. Oba widoki maja np. rozklad jezykow, wiec
   *  wszystkie wyszukiwania musza byc ograniczone do jednego z nich. */
  function panel(name) {
    return document.querySelector('[data-panel="' + name + '"]');
  }

  // ---------------------------------------------------------------- pomocne

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function svg(tag, attrs) {
    var node = document.createElementNS(SVG, tag);
    for (var name in attrs) {
      if (Object.prototype.hasOwnProperty.call(attrs, name)) {
        node.setAttribute(name, attrs[name]);
      }
    }
    return node;
  }

  function each(selector, fn) {
    Array.prototype.forEach.call(document.querySelectorAll(selector), fn);
  }

  /** "2026-08-01" -> "1.08" - na osi liczy sie czytelnosc, nie komplet. */
  function shortDate(iso) {
    var parts = String(iso).split('-');
    return parts.length === 3 ? Number(parts[2]) + '.' + parts[1] : iso;
  }

  function toLogin() {
    window.location.assign('/admin/login/');
  }

  // --------------------------------------------------------------- kafelki

  function setTile(root, key, value) {
    var node = root.querySelector('[data-tile="' + key + '"]');
    if (node) node.textContent = value;
  }

  function setNote(root, key, value) {
    var node = root.querySelector('[data-note="' + key + '"]');
    if (node) node.textContent = value;
  }

  function renderTiles(data) {
    var root = panel('app');
    setTile(root, 'users_today', nf.format(data.users_today));
    setTile(root, 'users_week', nf.format(data.users_week));
    setTile(root, 'users_month', nf.format(data.users_month));
    setTile(root, 'users_total', nf.format(data.users_total));
    setTile(root, 'checks', nf.format(data.checks));
    setTile(root, 'retention', data.retention + '%');
    setTile(root, 'avg_session', nf.format(data.avg_session));

    setNote(root, 'users_new_today', '+' + nf.format(data.users_new_today) + ' nowych');
    setNote(root, 'checks_per_user', data.checks_per_user + ' na instalację');
    setNote(root, 'users_returning', nf.format(data.users_returning) + ' instalacji');

    var health = data.health || {};
    setTile(root, 'failure_rate', (health.rate || 0) + '%');

    // Sama wartosc niewiele mowi - dopiero zmiana wzgledem poprzedniego
    // tygodnia pokazuje, czy cos wlasnie przestalo dzialac.
    //
    // Ale porownanie ma sens tylko wtedy, gdy poprzedni tydzien W OGOLE mial
    // dane. Przy pustym okresie odniesienia serwer oddaje null, a nie zero -
    // zero czytaloby sie jako "bylo bezbledne" i kazdy pierwszy tydzien
    // dzialania wygladalby na nagle pogorszenie.
    var note;
    if (!health.sample) {
      note = 'za mało danych';
    } else if (health.rate_previous === null || health.rate_previous === undefined) {
      note = 'brak poprzedniego tygodnia do porównania';
    } else {
      var delta = Math.round(((health.rate || 0) - health.rate_previous) * 10) / 10;
      note = (delta > 0 ? '+' : '') + delta + ' pkt wobec poprz. tygodnia';
    }
    setNote(root, 'failure_delta', note);

    var tile = root.querySelector('[data-tile="failure_rate"]');
    if (tile) {
      tile.className = health.level === 'alert' ? 'bad'
        : health.level === 'warn' ? 'warn' : '';
    }
  }

  function renderWebTiles(data) {
    var root = panel('web');
    setTile(root, 'views_today', nf.format(data.views_today));
    setTile(root, 'views_week', nf.format(data.views_week));
    setTile(root, 'views_month', nf.format(data.views_month));
    setTile(root, 'views_total', nf.format(data.views_total));

    setNote(root, 'visitors_today', nf.format(data.visitors_today) + ' unikalnych');
    setNote(root, 'visitors_week', nf.format(data.visitors_week) + ' unikalnych');
    setNote(root, 'visitors_month', nf.format(data.visitors_month) + ' unikalnych');
    // Bez rzeczownika po liczbie - inaczej trzeba by odmieniac "odslona"
    // przez przypadki zaleznie od wartosci.
    setNote(root, 'per_visitor', data.per_visitor + ' na odwiedzającego');
  }

  // Etykiety z aplikacji sa krotkie i techniczne ("trade_400"), zeby przezyc
  // zmiany tlumaczen. Ludzki opis jest wylacznie tutaj, po stronie panelu.
  var KINDS = {
    tekst_przedmiotu: 'nieczytelny tekst przedmiotu',
    nie_przedmiot: 'skopiowany tekst to nie przedmiot',
    przedmiot_bez_rzadkosci: 'przedmiot z PoE bez linii Rarity',
    tekst_pusty: 'pusty tekst z mostu',
    tekst_bez_sekcji: 'tekst bez sekcji',
    schowek_pusty: 'pusty schowek',
    most_pusty: 'most nie zwrócił tekstu',
    most_dostep: 'brak dostępu do dokumentu Google',
    most_siec: 'brak połączenia z Google Docs',
    most_konfig: 'błąd konfiguracji mostu',
    most: 'błąd mostu',
    trade_limit: 'limit zapytań do trade (429)',
    trade_403: 'blokada Cloudflare (403)',
    trade_siec: 'brak połączenia z pathofexile.com',
    trade_json: 'odpowiedź trade nie jest JSON-em',
    trade_400: 'trade odrzuca zapytanie (400)',
    trade_404: 'trade nie zna zasobu (404)',
    trade_500: 'awaria po stronie trade (500)',
    trade_503: 'trade niedostępny (503)',
    trade: 'błąd API handlu',
    inny: 'inny błąd',
  };

  function describeKind(name) {
    if (KINDS[name]) return KINDS[name];
    // Nieznany kod HTTP z trade'a - opisujemy go, zamiast pokazywac surowa
    // etykiete. Nowe kody pojawiaja sie bez zmian w panelu.
    var http = /^trade_(\d{3})$/.exec(name || '');
    if (http) return 'trade zwraca HTTP ' + http[1];
    return name || 'nieznany';
  }

  // Co z tym zrobic. Kazda rada wskazuje na inne miejsce, wiec zla diagnoza
  // kosztuje realnie czas - dlatego bierze sie z rodzaju bledu, a nie z domyslu.
  function adviceFor(name) {
    if (name === 'przedmiot_bez_rzadkosci') {
      return 'To NASZ błąd: tekst wyszedł z gry, ale parser go nie rozumie. ' +
        'Warto sprawdzić, jaka klasa przedmiotu to powoduje.';
    }
    if (name === 'nie_przedmiot' || name === 'tekst_pusty' ||
        name === 'tekst_bez_sekcji') {
      return 'Skopiowany tekst nie pochodzi z przedmiotu – skrót wciśnięty ' +
        'nie tam albo w dokumencie została stara treść.';
    }
    if (name === 'tekst_przedmiotu' || name === 'schowek_pusty') {
      return 'To najczęściej zwykłe użycie skrótu poza przedmiotem – ' +
        'niekoniecznie awaria aplikacji.';
    }
    if (name && name.indexOf('most') === 0) {
      return 'Problem jest po stronie mostu przez Dokumenty Google, ' +
        'a nie w API handlu.';
    }
    if (name === 'trade_limit') {
      return 'To limit zapytań GGG, nie awaria – aplikacja sama odczekuje.';
    }
    if (name === 'trade_403') {
      return 'Cloudflare blokuje zapytania: potrzebny POESESSID w config.json.';
    }
    if (/^trade_4\d\d$/.test(name || '')) {
      return 'Trade odrzuca samo zapytanie – to zwykle znak, że zmienił się ' +
        'format filtrów. Sprawdź, czy wyszukiwanie działa.';
    }
    if (/^trade_5\d\d$/.test(name || '')) {
      return 'Awaria jest po stronie GGG – zwykle mija sama.';
    }
    return 'Sprawdź, czy wyszukiwanie działa.';
  }

  function renderAlert(data) {
    var health = data.health || {};
    if (!health.sample || health.level === 'ok') {
      alertBox.hidden = true;
      return;
    }
    clear(alertBox);
    alertBox.hidden = false;
    // Nie uzywamy tu wprost health.level: poziom nazywa sie "alert" tak samo
    // jak klasa bazowa, wiec selektor .alert.alert lapalby rowniez ostrzezenia.
    alertBox.className = 'alert ' + (health.level === 'alert' ? 'danger' : 'warn');
    alertBox.appendChild(el('strong', null, health.level === 'alert'
      ? 'Wysoki odsetek błędów' : 'Podwyższony odsetek błędów'));

    var opis = ' – ' + health.rate + '% wycen kończy się niepowodzeniem (' +
      nf.format(health.sample) + ' prób, ' + nf.format(health.installs || 0) +
      ' instalacji, 7 dni). ';
    // Przyczyne bierzemy z danych. Wczesniej stalo tu zdanie zaszyte w kodzie
    // ("zmiana w API handlu"), ktore padalo przy KAZDYM alercie niezaleznie od
    // tego, co sie faktycznie dzialo - baza nie trzymala wtedy rodzaju bledu.
    if (health.top) {
      opis += 'Najczęstszy błąd: ' + describeKind(health.top.name) +
        ' (' + nf.format(health.top.count) + '×). ' + adviceFor(health.top.name);
    } else {
      opis += 'Brak danych o rodzajach błędów – zgłoszenia pochodzą z wersji ' +
        'starszej niż 1.0.7, która ich jeszcze nie wysyłała.';
    }
    alertBox.appendChild(el('span', null, opis));
  }

  // --------------------------------------------------------------- wykresy

  /**
   * Slupki z druga seria narysowana na pierwszej. Skala jest wspolna, wiec
   * "nieudane" widac jako czesc calosci, a nie jako osobny wykres.
   */
  function chart(host, rows, mainKey, subKey, mainClass, subClass) {
    clear(host);
    if (!rows || !rows.length) {
      host.appendChild(el('p', 'note', 'Brak danych w tym zakresie.'));
      return;
    }

    var W = 720, H = 200, FOOT = 26;
    var top = 0;
    rows.forEach(function (row) { top = Math.max(top, Number(row[mainKey]) || 0); });

    // Same zera to nie to samo co brak wierszy: bez tego rysowalibysmy pusta
    // siatke, ktora wyglada jak zepsuty wykres, a nie jak "jeszcze nic nie ma".
    if (top === 0) {
      host.appendChild(el('p', 'empty', 'Brak danych w tym zakresie.'));
      return;
    }

    // Bez preserveAspectRatio="none": przy nierownym skalowaniu osi napisy
    // na wykresie robily sie sciesnione.
    var frame = svg('svg', {
      viewBox: '0 0 ' + W + ' ' + (H + FOOT),
      role: 'img',
      'aria-label': 'Wykres dzienny, maksimum ' + top
    });

    [0.25, 0.5, 0.75, 1].forEach(function (part) {
      var y = H - H * part;
      frame.appendChild(svg('line', { x1: 0, y1: y, x2: W, y2: y, 'class': 'grid' }));
    });

    var slot = W / rows.length;
    var width = Math.max(2, slot * 0.62);
    var every = Math.ceil(rows.length / 12);

    rows.forEach(function (row, index) {
      var x = index * slot + (slot - width) / 2;

      var mainH = ((Number(row[mainKey]) || 0) / top) * H;
      frame.appendChild(svg('rect', {
        x: x, y: H - mainH, width: width, height: mainH, 'class': mainClass,
        rx: Math.min(3, width / 2)
      }));

      if (subKey) {
        var subH = ((Number(row[subKey]) || 0) / top) * H;
        if (subH > 0) {
          frame.appendChild(svg('rect', {
            x: x, y: H - subH, width: width, height: subH, 'class': subClass,
            rx: Math.min(3, width / 2)
          }));
        }
      }

      // Podpisy co kilka dni, zeby sie nie zlewaly przy zakresie 90 dni.
      if (index % every === 0 || index === rows.length - 1) {
        var label = svg('text', { x: x + width / 2, y: H + 18, 'class': 'axis' });
        label.textContent = shortDate(row.date);
        frame.appendChild(label);
      }
    });

    var peak = svg('text', { x: 4, y: 13, 'class': 'axis peak' });
    peak.textContent = 'max ' + nf.format(top);
    frame.appendChild(peak);

    host.appendChild(frame);
  }

  // -------------------------------------------------------------- rozklady

  function renderBars(host, items) {
    if (!host) return;
    clear(host);
    if (!items || !items.length) {
      host.appendChild(el('p', 'note', 'Brak danych.'));
      return;
    }
    var top = items[0].count || 1;

    items.forEach(function (item) {
      var row = el('div', 'bar-row');
      row.appendChild(el('span', 'bar-name', item.name));

      var track = el('span', 'bar-track');
      var fill = el('span', 'bar-fill');
      // CSSOM, nie atrybut style - CSP blokuje tylko ten drugi.
      fill.style.width = Math.round((item.count / top) * 100) + '%';
      track.appendChild(fill);
      row.appendChild(track);

      row.appendChild(el('span', 'bar-count',
        nf.format(item.count) + '  ·  ' + item.share + '%'));
      host.appendChild(row);
    });
  }

  function renderErrors(host, items) {
    if (!host) return;
    clear(host);
    if (!items || !items.length) {
      host.appendChild(el('p', 'note',
        'Brak błędów w tym okresie – albo zgłoszenia pochodzą z wersji ' +
        'starszej niż 1.0.7, która nie wysyłała ich rodzaju.'));
      return;
    }
    var top = items[0].count || 1;

    items.forEach(function (item) {
      var row = el('div', 'bar-row');
      var name = el('span', 'bar-name', describeKind(item.name));
      // Surowa etykieta zostaje pod kursorem - po niej szuka sie w kodzie.
      name.title = item.name;
      row.appendChild(name);

      var track = el('span', 'bar-track');
      var fill = el('span', 'bar-fill bar-bad');
      fill.style.width = Math.round((item.count / top) * 100) + '%';
      track.appendChild(fill);
      row.appendChild(track);

      row.appendChild(el('span', 'bar-count',
        nf.format(item.count) + '  ·  ' + item.share + '%  ·  ' +
        nf.format(item.installs) + (item.installs === 1 ? ' instalacja' : ' inst.')));
      host.appendChild(row);
    });
  }

  // -------------------------------------------------------------- pobranie

  function renderApp(data) {
    state.app = data;
    var root = panel('app');

    renderAlert(data);
    renderTiles(data);

    chart(root.querySelector('[data-chart="users"]'), data.daily,
          'users', 'fresh', 'bar-main', 'bar-accent');
    chart(root.querySelector('[data-chart="checks"]'), data.daily,
          'checks', 'failures', 'bar-main', 'bar-bad');

    ['versions', 'languages', 'leagues', 'systems', 'transports']
      .forEach(function (name) {
        renderBars(root.querySelector('[data-bars="' + name + '"]'), data[name]);
      });

    // Rodzaje bledow ida przez wlasny renderer: nazwa wymaga przetlumaczenia
    // na ludzki jezyk, a liczba instalacji odroznia awarie ogolna od jednej
    // osoby, ktora trafila na swoj wlasny problem.
    renderErrors(root.querySelector('[data-bars="errors"]'), data.errors);

    stamp(data);
    meta.textContent = nf.format(data.pings) + ' sygnałów w bazie';
  }

  function renderWeb(data) {
    state.web = data;
    var root = panel('web');

    renderWebTiles(data);

    chart(root.querySelector('[data-chart="traffic"]'), data.daily,
          'views', 'visitors', 'bar-main', 'bar-accent');

    ['pages', 'referrers', 'countries', 'languages', 'devices']
      .forEach(function (name) {
        renderBars(root.querySelector('[data-bars="' + name + '"]'), data[name]);
      });

    stamp(data);
    meta.textContent = nf.format(data.views_total) + ' odsłon w bazie';
  }

  function stamp(data) {
    updated.textContent = 'dane z ' + data.updated + ' ' + data.timezone;
    who.textContent = data.admin ? 'zalogowany: ' + data.admin : '';
  }

  function load() {
    var web = state.tab === 'web';
    var url = (web ? '/api/traffic?days=' : '/api/stats?days=') + state.days;
    updated.textContent = 'wczytuję…';

    fetch(url, { credentials: 'same-origin' })
      .then(function (response) {
        // Sesja mogla wygasnac miedzy odswiezeniami - wtedy po prostu
        // wracamy na logowanie zamiast pokazywac blad.
        if (response.status === 401) { toLogin(); return null; }
        if (!response.ok) throw new Error('HTTP ' + response.status);
        return response.json();
      })
      .then(function (data) {
        if (!data) return;
        if (web) renderWeb(data); else renderApp(data);
      })
      .catch(function (err) {
        updated.textContent = 'błąd: ' + ((err && err.message) || err);
      });
  }

  function schedule() {
    if (timer) clearInterval(timer);
    timer = setInterval(load, REFRESH_MS);
  }

  function selectTab(name) {
    state.tab = name;
    each('.tab', function (button) {
      button.setAttribute('aria-selected',
        button.getAttribute('data-tab') === name ? 'true' : 'false');
    });
    each('[data-panel]', function (node) {
      node.hidden = node.getAttribute('data-panel') !== name;
    });
    try {
      localStorage.setItem(PREFS, JSON.stringify({ days: state.days, tab: name }));
    } catch (err) { /* tryb prywatny - trudno */ }
    load();
  }

  // --------------------------------------------------------------- eksport

  function toCsv() {
    var web = state.tab === 'web';
    var data = web ? state.web : state.app;
    if (!data || !data.daily) return;

    var lines = [];
    if (web) {
      lines.push('data;odslony;unikalni');
      data.daily.forEach(function (row) {
        lines.push([row.date, row.views, row.visitors].join(';'));
      });
    } else {
      lines.push('data;uzytkownicy;nowi;wyceny;bledy');
      data.daily.forEach(function (row) {
        lines.push([row.date, row.users, row.fresh, row.checks, row.failures].join(';'));
      });
    }

    // Znacznik BOM, zeby Excel nie polamal polskich znakow w naglowku.
    var blob = new Blob(['﻿' + lines.join('\r\n')],
                        { type: 'text/csv;charset=utf-8' });
    var href = URL.createObjectURL(blob);
    var link = el('a');
    link.href = href;
    link.download = 'poe-price-check-' + (web ? 'strona' : 'aplikacja')
                  + '-' + data.range_days + 'd.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(href);
  }

  // ------------------------------------------------------------- zdarzenia

  refresh.addEventListener('click', load);
  document.getElementById('csv').addEventListener('click', toCsv);

  document.getElementById('logout').addEventListener('click', function () {
    fetch('/api/logout', { method: 'POST', credentials: 'same-origin' })
      .then(toLogin, toLogin);
  });

  var passwordForm = document.getElementById('password');
  var passwordNote = document.getElementById('password-note');

  passwordForm.addEventListener('submit', function (event) {
    event.preventDefault();
    passwordNote.className = 'note';
    passwordNote.textContent = 'Zmieniam…';

    fetch('/api/password', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        current: document.getElementById('current').value,
        next: document.getElementById('next').value
      })
    })
      .then(function (response) {
        return response.json().then(function (data) {
          return { ok: response.ok, data: data };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          passwordNote.className = 'note error';
          passwordNote.textContent = result.data.error === 'weak_password'
            ? 'Nowe hasło musi mieć co najmniej ' + result.data.min + ' znaków.'
            : 'Obecne hasło się nie zgadza.';
          return;
        }
        passwordNote.textContent = 'Hasło zmienione. Zaloguj się ponownie.';
        setTimeout(toLogin, 1500);
      })
      .catch(function () {
        passwordNote.className = 'note error';
        passwordNote.textContent = 'Brak połączenia z serwerem.';
      });
  });

  each('.range', function (button) {
    button.addEventListener('click', function () {
      state.days = Number(button.getAttribute('data-days'));
      each('.range', function (other) {
        other.setAttribute('aria-pressed', other === button ? 'true' : 'false');
      });
      try {
        localStorage.setItem(PREFS,
          JSON.stringify({ days: state.days, tab: state.tab }));
      } catch (err) { /* tryb prywatny - trudno, zakres wroci do domyslnego */ }
      load();
    });
  });

  // ----------------------------------------------------------------- start

  each('.tab', function (button) {
    button.addEventListener('click', function () {
      selectTab(button.getAttribute('data-tab'));
    });
  });

  try {
    var prefs = JSON.parse(localStorage.getItem(PREFS) || '{}');
    if (prefs.days) state.days = prefs.days;
    if (prefs.tab === 'web' || prefs.tab === 'app') state.tab = prefs.tab;
  } catch (err) { /* uszkodzony wpis traktujemy jak brak wpisu */ }

  each('.range', function (button) {
    button.setAttribute('aria-pressed',
      Number(button.getAttribute('data-days')) === state.days ? 'true' : 'false');
  });
  each('.tab', function (button) {
    button.setAttribute('aria-selected',
      button.getAttribute('data-tab') === state.tab ? 'true' : 'false');
  });
  each('[data-panel]', function (node) {
    node.hidden = node.getAttribute('data-panel') !== state.tab;
  });

  load();
  schedule();
})();
