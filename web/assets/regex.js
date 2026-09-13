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
  var shareBtn = document.getElementById('regex-share');
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
      if (on.checked) terms.push(n ? row.dataset.re.replace('{n}', atLeast(n.value)) : row.dataset.re);
    });
    return terms;
  }

  // Gniazda w tekscie przedmiotu: "Sockets: R-G-B B". Polaczenie n gniazd to
  // n liter polaczonych myslnikami; kolory = wszystkie kolejnosci liter w jednej
  // grupie (pozostale miejsca: dowolne gniazdo).
  function permutations(letters) {
    if (letters.length <= 1) return [letters.slice()];
    var seen = {}, outList = [];
    letters.forEach(function (l, i) {
      if (seen[l]) return;
      seen[l] = true;
      var rest = letters.slice(0, i).concat(letters.slice(i + 1));
      permutations(rest).forEach(function (perm) { outList.push([l].concat(perm)); });
    });
    return outList;
  }
  function socketsTerm(kind) {
    var box = panel(kind).querySelector('.sockets');
    if (!box) return '';
    var links = Number(box.querySelector('[data-role="links"]').value) || 0;
    var letters = [];
    ['r', 'g', 'b'].forEach(function (c) {
      var k = Math.max(0, Math.min(6, Number(box.querySelector('[data-role="' + c + '"]').value) || 0));
      for (var i = 0; i < k; i++) letters.push(c);
    });
    var size = Math.max(links, letters.length);
    box.classList.toggle('on', size > 1 || letters.length > 0);
    if (size < 2 && !letters.length) return '';
    if (size < 2) return 'sockets:.*' + letters[0];
    // "." jako dowolne gniazdo tylko przy 3+ polaczeniach: ".-." trafialby
    // w zwykle slowa z myslnikiem ("Two-Handed").
    while (letters.length < size) letters.push(size === 2 ? '[rgbwa]' : '.');
    var perms = permutations(letters).map(function (perm) { return perm.join('-'); });
    return perms.join('|');
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
      var sock = socketsTerm(active);
      if (sock) parts.push(quote(sock));
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
    if (shareBtn) shareBtn.disabled = !text;
    save();
    syncHash();
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
        var n = row.querySelector('[data-role="n"]');
        state.thr[key] = [row.querySelector('[data-role="on"]').checked, n ? n.value : ''];
      });
      state.sockets = {};
      Array.prototype.forEach.call(document.querySelectorAll('.sockets'), function (box) {
        state.sockets[box.closest('.tool-panel').id] = socketValues(box);
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
        var n = row.querySelector('[data-role="n"]');
        if (n && v[1] !== '') n.value = v[1];
      }
    });
    Array.prototype.forEach.call(document.querySelectorAll('.sockets'), function (box) {
      var v = (state.sockets || {})[box.closest('.tool-panel').id];
      if (v) setSocketValues(box, v);
    });
    var m = document.querySelector('input[name="mode"][value="' + state.mode + '"]');
    if (m) m.checked = true;
    var t17 = document.getElementById('hide-t17');
    if (t17 && state.hideT17) { t17.checked = true; filterList(t17.closest('.tool-panel')); }
    if (state.active && panel(state.active)) select(state.active);
  }

  function socketValues(box) {
    return ['links', 'r', 'g', 'b'].map(function (role) {
      return box.querySelector('[data-role="' + role + '"]').value || '0';
    }).join('.');
  }
  function setSocketValues(box, text) {
    String(text).split('.').forEach(function (v, i) {
      var el = box.querySelector('[data-role="' + ['links', 'r', 'g', 'b'][i] + '"]');
      if (el) el.value = v;
    });
  }

  // Link opisuje tylko aktywny panel - to, co widac i co trafia do regexu.
  // Fragmenty modow zamiast indeksow: nie przesuwaja sie po dodaniu nowego moda.
  var SEP = '~';
  function shareParams() {
    var p = panel(active), params = new URLSearchParams();
    if (tabs.length) params.set('tab', active);
    var thr = [];
    Array.prototype.forEach.call(p.querySelectorAll('.thr[data-id]'), function (row) {
      if (!row.querySelector('[data-role="on"]').checked) return;
      var n = row.querySelector('[data-role="n"]');
      thr.push(row.dataset.id + (n ? '.' + n.value : ''));
    });
    if (thr.length) params.set('t', thr.join(SEP));
    var s = p.querySelector('.mods') ? modStates(active) : { want: [], avoid: [] };
    if (s.want.length) params.set('w', s.want.join(SEP));
    if (s.avoid.length) params.set('a', s.avoid.join(SEP));
    var box = p.querySelector('.sockets');
    if (box && socketValues(box) !== '0.0.0.0') params.set('s', socketValues(box));
    if (mode() === 'all') params.set('m', 'all');
    return params;
  }
  function shareUrl() {
    var params = shareParams();
    // "~" bez kodowania - link czytelniejszy na Discordzie.
    var q = params.toString().replace(/%7E/gi, '~');
    return location.origin + location.pathname + (q ? '#' + q : '');
  }
  function syncHash() {
    try { history.replaceState(null, '', shareUrl()); } catch (e) { /* file:// itp. */ }
  }
  function loadHash() {
    if (location.hash.length < 2) return false;
    var params = new URLSearchParams(location.hash.slice(1));
    if (!['tab', 't', 'w', 'a', 's'].some(function (k) { return params.has(k); })) return false;
    if (params.get('tab') && panel(params.get('tab'))) select(params.get('tab'));
    var p = panel(active);
    // Link zastepuje zapamietany stan tego panelu, nie dokleja sie do niego.
    Array.prototype.forEach.call(p.querySelectorAll('.mods li[data-state]'), function (li) { setState(li, null); });
    Array.prototype.forEach.call(p.querySelectorAll('.thr [data-role="on"]'), function (c) { c.checked = false; });
    (params.get('t') || '').split(SEP).forEach(function (item) {
      if (!item) return;
      var dot = item.indexOf('.');
      var id = dot === -1 ? item : item.slice(0, dot);
      var row = p.querySelector('.thr[data-id="' + CSS.escape(id) + '"]');
      if (!row) return;
      row.querySelector('[data-role="on"]').checked = true;
      var n = row.querySelector('[data-role="n"]');
      if (n && dot !== -1) n.value = item.slice(dot + 1);
    });
    [['w', 'want'], ['a', 'avoid']].forEach(function (pair) {
      (params.get(pair[0]) || '').split(SEP).forEach(function (frag) {
        if (!frag) return;
        var li = p.querySelector('.mods li[data-frag="' + CSS.escape(frag) + '"]');
        if (li) setState(li, pair[1]);
      });
    });
    var box = p.querySelector('.sockets');
    if (box) setSocketValues(box, params.get('s') || '0.0.0.0');
    var m = document.querySelector('input[name="mode"][value="' + (params.get('m') === 'all' ? 'all' : 'any') + '"]');
    if (m) m.checked = true;
    return true;
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
    if (e.target.closest('.sockets')) { build(); return; }
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
    if (e.target.closest('.thr') || e.target.closest('.sockets') || e.target.name === 'mode') build();
  });

  function copyText(btn, text, label, fallback) {
    var done = function () {
      btn.textContent = 'Copied';
      setTimeout(function () { btn.textContent = label; }, 1500);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else {
      fallback();
    }
  }
  copyBtn.addEventListener('click', function () {
    copyText(copyBtn, out.value, 'Copy', function () {
      out.select();
      try { document.execCommand('copy'); } catch (err) { /* uzytkownik skopiuje sam */ }
    });
  });
  if (shareBtn) {
    shareBtn.addEventListener('click', function () {
      // Bez schowka adres i tak jest juz w pasku przegladarki (syncHash).
      copyText(shareBtn, shareUrl(), 'Copy link', function () { shareBtn.textContent = 'Link is in the address bar'; });
    });
  }

  clearBtn.addEventListener('click', function () {
    var p = panel(active);
    Array.prototype.forEach.call(p.querySelectorAll('.mods li[data-state]'), function (li) { setState(li, null); });
    Array.prototype.forEach.call(p.querySelectorAll('.thr [data-role="on"]'), function (c) { c.checked = false; });
    var box = p.querySelector('.sockets');
    if (box) setSocketValues(box, '0.0.0.0');
    build();
  });

  load();
  loadHash();
  build();

  // Dla testow w konsoli / przyszlych stron.
  window.poeRegexAtLeast = atLeast;
})();
