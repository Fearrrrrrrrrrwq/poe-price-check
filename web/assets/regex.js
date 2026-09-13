/* Regex Builder - logika stron /tools/poe2-regex/ i /tools/poe-map-regex/.
 *
 * Strona sama opisuje, co ma: panele z lista modow (.mods) i/lub progami
 * (.thr), opcjonalne zakladki; klucz localStorage w data-store pola wyniku.
 *
 * Lista modow i progi sa wyrenderowane w HTML (widoczne dla wyszukiwarek);
 * skrypt tylko trzyma stan zaznaczen i sklada z niego tekst wyszukiwania.
 *
 * Skladnia wyszukiwarki PoE2: tekst w cudzyslowie to regex (bez rozrozniania
 * wielkosci liter), "a|b" = a albo b, "!a|b" = ani a, ani b, kilka
 * cudzyslowow oddzielonych spacja = wszystkie naraz. Limit pola: 250 znakow.
 */
(function () {
  'use strict';

  var LIMIT = 250;
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.tool-tabs [role="tab"]'));
  var out = document.getElementById('regex-out');
  var counter = document.querySelector('.counter');
  var copyBtn = document.getElementById('regex-copy');
  var clearBtn = document.getElementById('regex-clear');
  if (!out) return;
  var STORE = out.dataset.store || 'poe2-regex-v1';

  var panels = Array.prototype.slice.call(document.querySelectorAll('.tool-panel'));
  var modKinds = panels.filter(function (el) { return el.querySelector('.mods'); })
    .map(function (el) { return el.id.slice(6); });
  var active = panels.length ? panels[0].id.slice(6) : '';

  // "co najmniej n" jako regex na liczbe calkowita (bez zer wiodacych).
  // 45 -> (4[5-9]|[5-9]\d|\d\d\d). Mniejsza liczba nigdy nie pasuje: ma mniej
  // cyfr, a wzorce sa dokladnie tej dlugosci co n albo dluzsze.
  function cls(a, b) { return a === b ? String(a) : '[' + a + '-' + b + ']'; }
  function atLeast(n) {
    n = Math.max(0, Math.floor(Number(n) || 0));
    if (n === 0) return '\\d';
    var s = String(n), d = s.length, alts = [];
    for (var i = 0; i < d; i++) {
      var prefix = s.slice(0, i), c = Number(s[i]), rest = d - i - 1;
      if (i === d - 1) alts.push(prefix + cls(c, 9));
      else if (c < 9) alts.push(prefix + cls(c + 1, 9) + new Array(rest + 1).join('\\d'));
    }
    for (var len = d + 1; len <= Math.max(3, d + 1); len++) {
      alts.push(new Array(len + 1).join('\\d'));
    }
    return alts.length === 1 ? alts[0] : '(' + alts.join('|') + ')';
  }

  function panel(kind) { return document.getElementById('panel-' + kind); }

  function modStates(kind) {
    var want = [], avoid = [];
    var rows = panel(kind).querySelectorAll('.mods li');
    Array.prototype.forEach.call(rows, function (li) {
      if (li.dataset.state === 'want') want.push(li.dataset.frag);
      else if (li.dataset.state === 'avoid') avoid.push(li.dataset.frag);
    });
    return { want: want, avoid: avoid };
  }

  function thresholds(kind) {
    var terms = [];
    var rows = panel(kind).querySelectorAll('.thr');
    Array.prototype.forEach.call(rows, function (row) {
      var on = row.querySelector('[data-role="on"]');
      var n = row.querySelector('[data-role="n"]');
      row.classList.toggle('on', on.checked);
      if (on.checked) terms.push(row.dataset.re.replace('{n}', atLeast(n.value)));
    });
    return terms;
  }

  function mode() {
    var picked = document.querySelector('input[name="mode"]:checked');
    return picked ? picked.value : 'any';
  }

  function quote(t) { return '"' + t + '"'; }

  function build() {
    var parts = [];
    if (modKinds.indexOf(active) === -1) {
      var v = thresholds(active);
      if (v.length) parts = mode() === 'all' ? v.map(quote) : [quote(v.join('|'))];
    } else {
      var s = modStates(active);
      parts = parts.concat(thresholds(active).map(quote));
      if (s.want.length) {
        parts = parts.concat(mode() === 'all' ? s.want.map(quote) : [quote(s.want.join('|'))]);
      }
      if (s.avoid.length) parts.push(quote('!' + s.avoid.join('|')));
      var picked = panel(active).querySelector('.picked');
      if (picked) {
        picked.textContent = (s.want.length || s.avoid.length)
          ? s.want.length + ' wanted · ' + s.avoid.length + ' avoided' : '';
      }
    }
    var text = parts.join(' ');
    out.value = text;
    counter.querySelector('b').textContent = text.length;
    counter.classList.toggle('over', text.length > LIMIT);
    copyBtn.disabled = !text;
    save();
  }

  // --- stan w localStorage (wygoda: po odswiezeniu zaznaczenia zostaja) ---
  function save() {
    try {
      var state = { active: active, mode: mode(), mods: {}, thr: {} };
      modKinds.forEach(function (k) {
        state.mods[k] = {};
        Array.prototype.forEach.call(panel(k).querySelectorAll('.mods li[data-state]'), function (li) {
          state.mods[k][li.dataset.frag] = li.dataset.state;
        });
      });
      Array.prototype.forEach.call(document.querySelectorAll('.thr'), function (row) {
        var key = row.closest('.thresholds').dataset.kind + ':' + row.dataset.re;
        state.thr[key] = [row.querySelector('[data-role="on"]').checked,
          row.querySelector('[data-role="n"]').value];
      });
      var t17 = document.getElementById('hide-t17');
      if (t17) state.hideT17 = t17.checked;
      localStorage.setItem(STORE, JSON.stringify(state));
    } catch (e) { /* prywatne okno / zablokowany storage - bez zapamietywania */ }
  }

  function load() {
    var state;
    try { state = JSON.parse(localStorage.getItem(STORE) || 'null'); } catch (e) { state = null; }
    if (!state) return;
    modKinds.forEach(function (k) {
      var saved = (state.mods || {})[k] || {};
      Array.prototype.forEach.call(panel(k).querySelectorAll('.mods li'), function (li) {
        if (saved[li.dataset.frag]) setState(li, saved[li.dataset.frag]);
      });
    });
    Array.prototype.forEach.call(document.querySelectorAll('.thr'), function (row) {
      var key = row.closest('.thresholds').dataset.kind + ':' + row.dataset.re;
      var v = (state.thr || {})[key];
      if (v) {
        row.querySelector('[data-role="on"]').checked = !!v[0];
        row.querySelector('[data-role="n"]').value = v[1];
      }
    });
    var m = document.querySelector('input[name="mode"][value="' + state.mode + '"]');
    if (m) m.checked = true;
    var t17 = document.getElementById('hide-t17');
    if (t17 && state.hideT17) { t17.checked = true; filterList(t17.closest('.tool-panel')); }
    if (state.active && panel(state.active)) select(state.active);
  }

  function filterList(p) {
    var input = p.querySelector('.filter');
    var q = input ? input.value.trim().toLowerCase() : '';
    var t17 = p.querySelector('#hide-t17');
    var hideT17 = t17 && t17.checked;
    Array.prototype.forEach.call(p.querySelectorAll('.mods li'), function (li) {
      // Zaznaczone mody zostaja widoczne - ukryty "Avoid" dalej jest w regexie.
      var off = (q && li.textContent.toLowerCase().indexOf(q) === -1) ||
        (hideT17 && li.hasAttribute('data-t17') && !li.dataset.state);
      li.hidden = !!off;
    });
  }

  function setState(li, state) {
    if (state) li.dataset.state = state; else delete li.dataset.state;
    Array.prototype.forEach.call(li.querySelectorAll('button'), function (b) {
      b.setAttribute('aria-pressed', b.dataset.set === state ? 'true' : 'false');
    });
  }

  function select(kind) {
    active = kind;
    tabs.forEach(function (t) {
      var on = t.id === 'tab-' + kind;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      t.tabIndex = on ? 0 : -1;
      panel(t.id.slice(4)).hidden = !on;
    });
  }

  // --- zdarzenia ---
  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { select(t.id.slice(4)); build(); });
    t.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      var next = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
      next.focus(); next.click();
    });
  });

  // Gotowe zestawy ("Avoid: curses") - dopisuja Avoid do modow z listy;
  // drugie klikniecie zdejmuje, jesli caly zestaw juz jest zaznaczony.
  document.addEventListener('click', function (e) {
    var preset = e.target.closest('.presets button[data-frags]');
    if (!preset) return;
    var frags = JSON.parse(preset.dataset.frags);
    var rows = Array.prototype.filter.call(panel(active).querySelectorAll('.mods li'), function (li) {
      return frags.indexOf(li.dataset.frag) !== -1;
    });
    var all = rows.every(function (li) { return li.dataset.state === preset.dataset.set; });
    rows.forEach(function (li) { setState(li, all ? null : preset.dataset.set); });
    build();
  });

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.mods .seg button');
    if (!btn) return;
    var li = btn.closest('li');
    setState(li, li.dataset.state === btn.dataset.set ? null : btn.dataset.set);
    build();
  });

  document.addEventListener('input', function (e) {
    if (e.target.classList.contains('filter') || e.target.id === 'hide-t17') {
      filterList(e.target.closest('.tool-panel'));
      save();
      return;
    }
    if (e.target.closest('.thr') || e.target.name === 'mode') {
      // Wpisanie liczby od razu wlacza prog - nikt nie wpisuje minimum po to,
      // zeby go nie uzyc.
      if (e.target.dataset.role === 'n') {
        e.target.closest('.thr').querySelector('[data-role="on"]').checked = true;
      }
      build();
    }
  });
  document.addEventListener('change', function (e) {
    if (e.target.closest('.thr') || e.target.name === 'mode') build();
  });

  copyBtn.addEventListener('click', function () {
    var done = function () {
      copyBtn.textContent = 'Copied';
      setTimeout(function () { copyBtn.textContent = 'Copy'; }, 1500);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(out.value).then(done, function () { out.select(); });
    } else {
      out.select();
      try { document.execCommand('copy'); done(); } catch (err) { /* uzytkownik skopiuje sam */ }
    }
  });

  clearBtn.addEventListener('click', function () {
    var p = panel(active);
    Array.prototype.forEach.call(p.querySelectorAll('.mods li[data-state]'), function (li) { setState(li, null); });
    Array.prototype.forEach.call(p.querySelectorAll('.thr [data-role="on"]'), function (c) { c.checked = false; });
    build();
  });

  load();
  build();

  // Dla testow w konsoli / przyszlych stron.
  window.poeRegexAtLeast = atLeast;
})();
