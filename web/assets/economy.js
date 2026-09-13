/* Strona /economy/ - tabela cen z /api/economy (zrodlo: poe.ninja).
 *
 * Stan (liga, kategoria) trzymamy w adresie (?league=&type=), zeby link do
 * konkretnej tabeli dalo sie wkleic na Discorda.
 */
(function () {
  'use strict';

  var root = document.querySelector('.econ');
  if (!root) return;
  var game = root.dataset.game === 'poe1' ? 'poe1' : 'poe2';
  var leagueSel = document.getElementById('econ-league');
  var typesBox = document.getElementById('econ-types');
  var rowsBox = document.getElementById('econ-rows');
  var statusEl = document.getElementById('econ-status');
  var ratesEl = document.getElementById('econ-rates');
  var search = document.getElementById('econ-search');

  var LABELS = {
    SoulCores: 'Soul Cores', UncutGems: 'Uncut Gems', LineageSupportGems: 'Lineage Supports',
    DeliriumOrb: 'Delirium Orbs', DivinationCard: 'Divination Cards', AllflameEmber: 'Allflame Embers',
    Fragment: 'Fragments', Scarab: 'Scarabs', Essence: 'Essences', Fossil: 'Fossils',
    Resonator: 'Resonators', Oil: 'Oils', Omen: 'Omens', Tattoo: 'Tattoos', Artifact: 'Artifacts',
    Runegraft: 'Runegrafts',
  };

  var params = new URLSearchParams(location.search);
  var state = { league: params.get('league') || '', type: params.get('type') || 'Currency',
    sort: 'value', dir: -1, data: null };

  function fmt(n) {
    if (n == null || isNaN(n)) return '–';
    var abs = Math.abs(n);
    var digits = abs >= 100 ? 0 : abs >= 10 ? 1 : abs >= 1 ? 2 : abs >= 0.1 ? 3 : 4;
    return n.toLocaleString('en-US', { maximumFractionDigits: digits });
  }

  // Wartosc w najczytelniejszej walucie: PoE2 liczy w Divine, ale za 0,02 div
  // nikt nie mysli - wtedy pokazujemy Exalted. PoE1 liczy w Chaos, powyzej
  // kursu Divine przechodzimy na Divine.
  function price(value, data) {
    var r = data.rates || {};
    if (data.primary === 'divine') {
      if (value >= 1 || !r.exalted) return { main: fmt(value) + ' div', sub: r.chaos ? fmt(value * r.chaos) + ' c' : '' };
      return { main: fmt(value * r.exalted) + ' ex', sub: fmt(value) + ' div' };
    }
    var perDiv = r.divine ? 1 / r.divine : 0;
    if (perDiv && value >= perDiv) return { main: fmt(value * r.divine) + ' div', sub: fmt(value) + ' c' };
    return { main: fmt(value) + ' c', sub: '' };
  }

  function change(v) {
    if (v == null) return '<span class="chg none">–</span>';
    var cls = v > 0.05 ? 'up' : v < -0.05 ? 'down' : 'flat';
    return '<span class="chg ' + cls + '">' + (v > 0 ? '+' : '') + fmt(v) + '%</span>';
  }

  function spark(data) {
    if (!data || data.length < 2) return '';
    var w = 96, h = 26, min = Math.min.apply(null, data), max = Math.max.apply(null, data);
    var span = max - min || 1;
    var pts = data.map(function (v, i) {
      return (i * w / (data.length - 1)).toFixed(1) + ',' + (h - 2 - (v - min) / span * (h - 4)).toFixed(1);
    });
    var last = data[data.length - 1], first = data[0];
    var cls = last > first ? 'up' : last < first ? 'down' : 'flat';
    var end = pts[pts.length - 1].split(',');
    return '<svg class="spark ' + cls + '" viewBox="0 0 ' + w + ' ' + h + '" width="' + w + '" height="' + h +
      '" aria-hidden="true"><polyline fill="none" points="' + pts.join(' ') + '"/>' +
      '<circle cx="' + end[0] + '" cy="' + end[1] + '" r="2.2"/></svg>';
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function render() {
    var data = state.data;
    if (!data) return;
    var q = search.value.trim().toLowerCase();
    var items = data.items.filter(function (it) { return !q || it.name.toLowerCase().indexOf(q) !== -1; });
    var key = state.sort, dir = state.dir;
    items.sort(function (a, b) {
      if (key === 'name') return a.name.localeCompare(b.name) * dir;
      var av = a[key], bv = b[key];
      if (av == null) return 1;
      if (bv == null) return -1;
      return (av - bv) * dir;
    });
    rowsBox.innerHTML = items.map(function (it) {
      var p = price(it.value, data);
      return '<tr>' +
        '<th scope="row"><span class="item">' +
          (it.icon ? '<img src="' + esc(it.icon) + '" alt="" width="28" height="28" loading="lazy">' : '') +
          esc(it.name) + '</span></th>' +
        '<td class="col-n"><b>' + p.main + '</b>' + (p.sub ? '<small>' + p.sub + '</small>' : '') + '</td>' +
        '<td class="col-n">' + change(it.change24h) + '</td>' +
        '<td class="col-n">' + change(it.change7d) + '</td>' +
        '<td class="col-n">' + change(it.change30d) + '</td>' +
        '<td class="col-n muted">' + fmt(it.volume) + '</td>' +
        '<td class="spark-col">' + spark(it.spark) + '</td></tr>';
    }).join('');
    document.querySelectorAll('.econ-table th[data-sort]').forEach(function (th) {
      th.setAttribute('aria-sort', th.dataset.sort === key ? (dir > 0 ? 'ascending' : 'descending') : 'none');
    });
    var when = new Date(data.fetchedAt);
    statusEl.textContent = items.length + ' items · ' + data.league + ' · updated ' +
      when.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    var r = data.rates || {};
    ratesEl.textContent = data.primary === 'divine'
      ? (r.exalted ? '1 Divine = ' + fmt(r.exalted) + ' Exalted' + (r.chaos ? ' = ' + fmt(r.chaos) + ' Chaos' : '') : '')
      : (r.divine ? '1 Divine = ' + fmt(1 / r.divine) + ' Chaos' : '');
  }

  function syncUrl() {
    var p = new URLSearchParams();
    if (state.league) p.set('league', state.league);
    if (state.type !== 'Currency') p.set('type', state.type);
    var qs = p.toString();
    history.replaceState(null, '', location.pathname + (qs ? '?' + qs : ''));
  }

  function load() {
    statusEl.textContent = 'Loading prices…';
    rowsBox.innerHTML = '';
    syncUrl();
    var url = '/api/economy?game=' + game + '&league=' + encodeURIComponent(state.league) +
      '&type=' + encodeURIComponent(state.type);
    fetch(url).then(function (r) { return r.json().then(function (j) { return [r.ok, j]; }); })
      .then(function (res) {
        if (!res[0]) throw new Error(res[1].error || 'error');
        state.data = res[1];
        render();
      })
      .catch(function () {
        state.data = null;
        statusEl.textContent = 'Prices are unavailable right now. Try again in a few minutes.';
      });
  }

  function renderTypes(types) {
    typesBox.innerHTML = types.map(function (t) {
      return '<button type="button" role="tab" data-type="' + t + '" aria-selected="' +
        (t === state.type) + '">' + (LABELS[t] || t) + '</button>';
    }).join('');
  }

  typesBox.addEventListener('click', function (e) {
    var b = e.target.closest('button[data-type]');
    if (!b || b.dataset.type === state.type) return;
    state.type = b.dataset.type;
    Array.prototype.forEach.call(typesBox.children, function (c) {
      c.setAttribute('aria-selected', c.dataset.type === state.type ? 'true' : 'false');
    });
    load();
  });
  leagueSel.addEventListener('change', function () { state.league = leagueSel.value; load(); });
  search.addEventListener('input', render);
  document.querySelectorAll('.econ-table th[data-sort]').forEach(function (th) {
    th.tabIndex = 0;
    var go = function () {
      var key = th.dataset.sort;
      state.dir = state.sort === key ? -state.dir : (key === 'name' ? 1 : -1);
      state.sort = key;
      render();
    };
    th.addEventListener('click', go);
    th.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } });
  });

  fetch('/api/economy?game=' + game + '&leagues=1')
    .then(function (r) { return r.json(); })
    .then(function (j) {
      var leagues = j.leagues || [];
      // Domyslnie liga challenge: pierwsza, ktora nie jest Standard/Hardcore.
      var pick = leagues.filter(function (l) { return !/^(standard|hardcore)$/i.test(l) && !/^hc |hardcore|ruthless/i.test(l); })[0] || leagues[0];
      if (!state.league || leagues.indexOf(state.league) === -1) state.league = pick;
      leagueSel.innerHTML = leagues.map(function (l) {
        return '<option' + (l === state.league ? ' selected' : '') + '>' + esc(l) + '</option>';
      }).join('');
      if ((j.types || []).indexOf(state.type) === -1) state.type = 'Currency';
      renderTypes(j.types || ['Currency']);
      load();
    })
    .catch(function () {
      statusEl.textContent = 'League list is unavailable right now. Try again in a few minutes.';
    });
})();
