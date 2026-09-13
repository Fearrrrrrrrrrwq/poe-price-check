/* Strona /economy/ - tabela cen z /api/economy (zrodlo: poe.ninja).
 *
 * Stan (liga, kategoria) trzymamy w adresie (?league=&type=), zeby link do
 * konkretnej tabeli dalo sie wkleic na Discorda. Klikniecie wiersza otwiera
 * pod nim wykres ceny z calej ligi.
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
  var lowToggle = document.getElementById('econ-lowconf');
  var lowWrap = document.getElementById('econ-lowconf-wrap');
  var volHead = document.querySelector('.econ-table th[data-sort="volume"]');

  var LABELS = {
    SoulCores: 'Soul Cores', UncutGems: 'Uncut Gems', LineageSupportGems: 'Lineage Supports',
    DeliriumOrb: 'Delirium Orbs', DivinationCard: 'Divination Cards', AllflameEmber: 'Allflame Embers',
    Fragment: 'Fragments', Scarab: 'Scarabs', Essence: 'Essences', Fossil: 'Fossils',
    Resonator: 'Resonators', Oil: 'Oils', Omen: 'Omens', Tattoo: 'Tattoos', Artifact: 'Artifacts',
    Runegraft: 'Runegrafts', UniqueWeapon: 'Unique Weapons', UniqueArmour: 'Unique Armours',
    UniqueAccessory: 'Unique Accessories', UniqueJewel: 'Unique Jewels', UniqueFlask: 'Unique Flasks',
    UniqueMap: 'Unique Maps', UniqueRelic: 'Unique Relics', UniqueTincture: 'Unique Tinctures',
    ClusterJewel: 'Cluster Jewels', Beast: 'Beasts', Map: 'Maps', BlightedMap: 'Blighted Maps',
    Invitation: 'Invitations',
  };
  var UNIT = { divine: 'div', exalted: 'ex', chaos: 'c' };

  var params = new URLSearchParams(location.search);
  var state = { league: params.get('league') || '', type: params.get('type') || 'Currency',
    sort: 'value', dir: -1, data: null, open: null, types: [], stashTypes: [], all: {}, loadingAll: false };
  // Wyszukiwanie od tylu znakow przeszukuje WSZYSTKIE kategorie - nie kazdy
  // wie, czy "Mageblood" to akcesorium, a "Fracturing Orb" waluta.
  var GLOBAL_MIN = 2;

  function fmt(n) {
    if (n == null || isNaN(n)) return '–';
    var abs = Math.abs(n);
    var digits = abs >= 100 ? 0 : abs >= 10 ? 1 : abs >= 1 ? 2 : abs >= 0.1 ? 3 : 4;
    return n.toLocaleString('en-US', { maximumFractionDigits: digits });
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
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

  // --- wykres historii ceny (jedna seria: wartosc przedmiotu w czasie) -----
  function niceTicks(min, max, count) {
    if (min === max) { min = min * 0.9; max = max * 1.1 || 1; }
    var span = max - min, step = Math.pow(10, Math.floor(Math.log10(span / count)));
    var err = span / count / step;
    step *= err >= 7.5 ? 10 : err >= 3.5 ? 5 : err >= 1.5 ? 2 : 1;
    var lo = Math.floor(min / step) * step, hi = Math.ceil(max / step) * step, ticks = [];
    for (var v = lo; v <= hi + step / 2; v += step) ticks.push(Math.round(v / step) * step);
    return ticks;
  }

  function dayLabel(iso) {
    var d = new Date(iso + 'T00:00:00Z');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
  }

  function drawChart(box, points, unit) {
    // Rysujemy w rzeczywistej szerokosci kontenera - skalowany viewBox
    // powiekszal tez tekst osi razem z wykresem.
    var W = Math.max(320, Math.round(box.clientWidth || 720)), H = 240, L = 58, R = 18, T = 16, B = 28;
    var vals = points.map(function (p) { return p.v; });
    var ticks = niceTicks(Math.min.apply(null, vals), Math.max.apply(null, vals), 4);
    var y0 = ticks[0], y1 = ticks[ticks.length - 1];
    var n = points.length;
    var x = function (i) { return L + (n === 1 ? (W - L - R) / 2 : i * (W - L - R) / (n - 1)); };
    var y = function (v) { return T + (1 - (v - y0) / (y1 - y0 || 1)) * (H - T - B); };
    var line = points.map(function (p, i) { return (i ? 'L' : 'M') + x(i).toFixed(1) + ' ' + y(p.v).toFixed(1); }).join(' ');
    var area = line + ' L' + x(n - 1).toFixed(1) + ' ' + (H - B) + ' L' + x(0).toFixed(1) + ' ' + (H - B) + ' Z';
    var grid = ticks.map(function (t) {
      return '<line class="gl" x1="' + L + '" x2="' + (W - R) + '" y1="' + y(t).toFixed(1) + '" y2="' + y(t).toFixed(1) + '"/>' +
        '<text class="axis" x="' + (L - 8) + '" y="' + (y(t) + 4).toFixed(1) + '" text-anchor="end">' + fmt(t) + '</text>';
    }).join('');
    var xIdx = n > 2 ? [0, Math.floor((n - 1) / 2), n - 1] : n === 2 ? [0, 1] : [0];
    var xl = xIdx.map(function (i, k) {
      var anchor = k === 0 ? 'start' : k === xIdx.length - 1 ? 'end' : 'middle';
      return '<text class="axis" x="' + x(i).toFixed(1) + '" y="' + (H - 8) + '" text-anchor="' + anchor + '">' + dayLabel(points[i].t) + '</text>';
    }).join('');
    var last = points[n - 1];
    box.innerHTML =
      '<div class="chart-wrap"><svg class="hist" viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" role="img" aria-label="Price history, ' +
      n + ' days, from ' + fmt(points[0].v) + ' to ' + fmt(last.v) + ' ' + UNIT[unit] + '">' + grid + xl +
      '<path class="area" d="' + area + '"/><path class="line" d="' + line + '"/>' +
      '<line class="cross" x1="0" x2="0" y1="' + T + '" y2="' + (H - B) + '" visibility="hidden"/>' +
      '<circle class="dot-end" cx="' + x(n - 1).toFixed(1) + '" cy="' + y(last.v).toFixed(1) + '" r="4"/>' +
      '<circle class="dot-hover" r="4" visibility="hidden"/>' +
      '<rect class="hit" x="' + L + '" y="' + T + '" width="' + (W - L - R) + '" height="' + (H - T - B) + '"/></svg>' +
      '<div class="tip" hidden></div></div>';
    var svg = box.querySelector('svg'), tip = box.querySelector('.tip');
    var cross = svg.querySelector('.cross'), dot = svg.querySelector('.dot-hover');
    function show(i) {
      var p = points[i], px = x(i), py = y(p.v);
      cross.setAttribute('x1', px); cross.setAttribute('x2', px); cross.setAttribute('visibility', 'visible');
      dot.setAttribute('cx', px); dot.setAttribute('cy', py); dot.setAttribute('visibility', 'visible');
      tip.hidden = false;
      tip.innerHTML = '<b>' + fmt(p.v) + ' ' + UNIT[unit] + '</b><span>' + dayLabel(p.t) + '</span>';
      var rect = svg.getBoundingClientRect(), scale = rect.width / W;
      tip.style.left = Math.min(Math.max(px * scale, 60), rect.width - 60) + 'px';
      tip.style.top = (py * scale - 10) + 'px';
    }
    function hide() { cross.setAttribute('visibility', 'hidden'); dot.setAttribute('visibility', 'hidden'); tip.hidden = true; }
    var hit = svg.querySelector('.hit');
    hit.addEventListener('mousemove', function (e) {
      var rect = svg.getBoundingClientRect();
      var sx = (e.clientX - rect.left) * W / rect.width;
      var i = Math.round((sx - L) / ((W - L - R) / Math.max(n - 1, 1)));
      show(Math.max(0, Math.min(n - 1, i)));
    });
    hit.addEventListener('mouseleave', hide);
    if (!box._resize) {
      var pending;
      box._resize = function () {
        clearTimeout(pending);
        pending = setTimeout(function () { if (box.isConnected) drawChart(box, points, unit); }, 150);
      };
      window.addEventListener('resize', box._resize);
    }
  }

  function pickUnit(series, item, data) {
    var keys = Object.keys(series).filter(function (k) { return series[k].length; });
    if (!keys.length) return null;
    if (data.kind === 'stash') return 'chaos';
    if (game === 'poe2') {
      if (item.value < 1 && series.exalted) return 'exalted';
      return series.divine ? 'divine' : keys[0];
    }
    var perDiv = data.rates && data.rates.divine ? 1 / data.rates.divine : Infinity;
    if (item.value >= perDiv && series.divine) return 'divine';
    return series.chaos ? 'chaos' : keys[0];
  }

  function openDetail(tr, item) {
    var existing = rowsBox.querySelector('tr.detail');
    if (existing) {
      var wasFor = existing.dataset.for;
      existing.remove();
      rowsBox.querySelectorAll('tr[aria-expanded="true"]').forEach(function (r) { r.setAttribute('aria-expanded', 'false'); });
      if (wasFor === item._key) { state.open = null; setHash(null); return; }
    }
    state.open = item._key;
    setHash(item._key.indexOf('|') === -1 ? item._key : null);
    tr.setAttribute('aria-expanded', 'true');
    var detail = document.createElement('tr');
    detail.className = 'detail';
    detail.dataset.for = item._key;
    detail.innerHTML = '<td colspan="7"><div class="detail-box"><p class="note">Loading price history…</p></div></td>';
    tr.after(detail);
    var box = detail.querySelector('.detail-box');
    var data = item._data || state.data;
    var url = '/api/economy?game=' + game + '&league=' + encodeURIComponent(data.league) +
      '&type=' + encodeURIComponent(data.type) + '&history=' + encodeURIComponent(item.detailsId);
    fetch(url).then(function (r) { return r.json(); }).then(function (h) {
      var unit = h.series ? pickUnit(h.series, item, data) : null;
      var points = unit ? h.series[unit] : [];
      if (!points || points.length < 2) {
        box.innerHTML = '<p class="note">Not enough price history for this item yet.</p>';
        return;
      }
      var vals = points.map(function (p) { return p.v; });
      var first = points[0].v, last = points[points.length - 1].v;
      var sinceStart = first > 0 ? (last / first - 1) * 100 : null;
      box.innerHTML = '<div class="detail-head"><h3>' + esc(item.name) + '</h3>' +
        '<dl class="detail-stats">' +
        '<div><dt>Now</dt><dd>' + fmt(last) + ' ' + UNIT[unit] + '</dd></div>' +
        '<div><dt>League low</dt><dd>' + fmt(Math.min.apply(null, vals)) + ' ' + UNIT[unit] + '</dd></div>' +
        '<div><dt>League high</dt><dd>' + fmt(Math.max.apply(null, vals)) + ' ' + UNIT[unit] + '</dd></div>' +
        '<div><dt>Since ' + dayLabel(points[0].t) + '</dt><dd>' + change(sinceStart) + '</dd></div>' +
        '</dl></div><div class="chart-slot"></div>' +
        '<details class="data-table"><summary>Show data table</summary><table><thead><tr><th scope="col">Day</th><th scope="col" class="col-n">Price (' + UNIT[unit] + ')</th></tr></thead><tbody>' +
        points.slice().reverse().map(function (p) { return '<tr><td>' + dayLabel(p.t) + '</td><td class="col-n">' + fmt(p.v) + '</td></tr>'; }).join('') +
        '</tbody></table></details>';
      drawChart(box.querySelector('.chart-slot'), points, unit);
    }).catch(function () {
      box.innerHTML = '<p class="note">Price history is unavailable right now.</p>';
    });
  }

  function globalQuery() {
    var q = search.value.trim().toLowerCase();
    return q.length >= GLOBAL_MIN ? q : '';
  }

  // Wszystkie kategorie aktualnej ligi - pobierane raz, przy pierwszym wyszukiwaniu.
  function loadAll() {
    var league = state.league;
    var bucket = state.all[league] || (state.all[league] = {});
    var missing = state.types.filter(function (t) { return !bucket[t]; });
    if (!missing.length || state.loadingAll) return;
    state.loadingAll = true;
    var left = missing.length;
    missing.forEach(function (t) {
      var cached = state.data && state.data.type === t && state.data.league === league ? state.data : null;
      var done = function () {
        left -= 1;
        if (!left) state.loadingAll = false;
        if (globalQuery() && state.league === league) render();
      };
      if (cached) { bucket[t] = cached; done(); return; }
      fetch('/api/economy?game=' + game + '&league=' + encodeURIComponent(league) + '&type=' + encodeURIComponent(t))
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (j) { bucket[t] = j || { type: t, items: [], failed: true }; })
        .catch(function () { bucket[t] = { type: t, items: [], failed: true }; })
        .then(done);
    });
  }

  function render() {
    var q = globalQuery();
    var global = !!q;
    var data = state.data;
    if (!global && !data) return;
    var hideLow = lowToggle && lowToggle.checked;
    var pool = [];
    if (global) {
      loadAll();
      var bucket = state.all[state.league] || {};
      state.types.forEach(function (t) {
        var d = bucket[t];
        if (!d || !d.items) return;
        d.items.forEach(function (it) {
          it._data = d;
          it._key = t + '|' + it.id;
          pool.push(it);
        });
      });
    } else {
      data.items.forEach(function (it) { it._data = data; it._key = it.id; pool.push(it); });
    }
    var items = pool.filter(function (it) {
      if (it._key === state.open) return true;
      if (hideLow && it.lowConfidence) return false;
      return !q || it.name.toLowerCase().indexOf(q) !== -1 || (it.sub || '').toLowerCase().indexOf(q) !== -1;
    });
    var key = state.sort, dir = state.dir;
    items.sort(function (a, b) {
      if (key === 'name') return a.name.localeCompare(b.name) * dir;
      var av = a[key], bv = b[key];
      if (av == null) return 1;
      if (bv == null) return -1;
      return (av - bv) * dir;
    });
    // W wyszukiwaniu pokazujemy najwyzej 200 wynikow - krotkie zapytanie ("or")
    // pasuje do setek przedmiotow, a tabela na tysiac wierszy tylko by zamulila.
    var total = items.length;
    if (global && items.length > 200) items = items.slice(0, 200);
    var byId = {};
    rowsBox.innerHTML = items.map(function (it) {
      byId[it._key] = it;
      var p = price(it.value, it._data);
      var cat = global ? '<button type="button" class="cat" data-type="' + esc(it._data.type) + '">' +
        esc(LABELS[it._data.type] || it._data.type) + '</button>' : '';
      return '<tr class="row' + (it.lowConfidence ? ' low' : '') + '" data-id="' + esc(it._key) +
        '" tabindex="0" aria-expanded="false">' +
        '<th scope="row"><span class="item">' +
          (it.icon ? '<img src="' + esc(it.icon) + '" alt="" width="28" height="28" loading="lazy">' : '') +
          '<span>' + esc(it.name) + cat + (it.sub ? '<small>' + esc(it.sub) + '</small>' : '') +
          (it.lowConfidence ? '<small class="lowtag">low confidence</small>' : '') + '</span></span></th>' +
        '<td class="col-n"><b>' + p.main + '</b>' + (p.sub ? '<small>' + p.sub + '</small>' : '') + '</td>' +
        '<td class="col-n">' + change(it.change24h) + '</td>' +
        '<td class="col-n">' + change(it.change7d) + '</td>' +
        '<td class="col-n">' + change(it.change30d) + '</td>' +
        '<td class="col-n muted">' + fmt(it.volume) + '</td>' +
        '<td class="spark-col">' + spark(it.spark) + '</td></tr>';
    }).join('');
    state.byId = byId;
    document.querySelectorAll('.econ-table th[data-sort]').forEach(function (th) {
      th.setAttribute('aria-sort', th.dataset.sort === key ? (dir > 0 ? 'ascending' : 'descending') : 'none');
    });
    typesBox.classList.toggle('dimmed', global);
    var anyStash = global ? state.stashTypes.length > 0 : data.kind === 'stash';
    if (volHead) volHead.textContent = global ? 'Volume / Listed' : (data.kind === 'stash' ? 'Listed' : 'Volume');
    if (lowWrap) lowWrap.hidden = !anyStash;
    if (global) {
      var bucketNow = state.all[state.league] || {};
      var loaded = state.types.filter(function (t) { return bucketNow[t]; }).length;
      statusEl.textContent = (total ? total + ' results' : 'No results') + ' for “' + search.value.trim() +
        '” across all categories' + (total > items.length ? ' (showing top ' + items.length + ')' : '') +
        (loaded < state.types.length ? ' · searching ' + loaded + '/' + state.types.length + ' categories…' : '') +
        ' · click a row for price history';
    } else {
      var when = new Date(data.fetchedAt);
      statusEl.textContent = items.length + ' items · ' + data.league + ' · updated ' +
        when.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' · click a row for price history';
    }
    var rateData = data || (items[0] && items[0]._data) || {};
    var r = rateData.rates || {};
    ratesEl.textContent = rateData.primary === 'divine'
      ? (r.exalted ? '1 Divine = ' + fmt(r.exalted) + ' Exalted' + (r.chaos ? ' = ' + fmt(r.chaos) + ' Chaos' : '') : '')
      : (r.divine ? '1 Divine = ' + fmt(1 / r.divine) + ' Chaos' : '');
    if (state.open && byId[state.open]) {
      var tr = rowsBox.querySelector('tr.row[data-id="' + CSS.escape(state.open) + '"]');
      state.open = null;
      if (tr) openDetail(tr, byId[tr.dataset.id]);
    }
  }

  // #item=<id> w adresie: link prosto do historii ceny konkretnego przedmiotu.
  function setHash(id) {
    var base = location.pathname + location.search;
    history.replaceState(null, '', id ? base + '#item=' + encodeURIComponent(id) : base);
  }
  var hashItem = (location.hash.match(/^#item=(.+)$/) || [])[1];
  if (params.get('q')) search.value = params.get('q');
  if (hashItem) state.open = decodeURIComponent(hashItem);

  function syncUrl() {
    var p = new URLSearchParams();
    if (state.league) p.set('league', state.league);
    if (state.type !== 'Currency') p.set('type', state.type);
    if (search.value.trim()) p.set('q', search.value.trim());
    var qs = p.toString();
    history.replaceState(null, '', location.pathname + (qs ? '?' + qs : '') +
      (state.open ? '#item=' + encodeURIComponent(state.open) : ''));
  }

  function load() {
    statusEl.textContent = 'Loading prices…';
    rowsBox.innerHTML = '';
    if (!hashItem) state.open = null;
    hashItem = null;
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

  rowsBox.addEventListener('click', function (e) {
    var catBtn = e.target.closest('button.cat');
    if (catBtn) {
      // Etykieta kategorii w wynikach: przejdz do tej kategorii.
      e.stopPropagation();
      search.value = '';
      selectType(catBtn.dataset.type);
      return;
    }
    var tr = e.target.closest('tr.row');
    if (tr && state.byId && state.byId[tr.dataset.id]) openDetail(tr, state.byId[tr.dataset.id]);
  });
  rowsBox.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    var tr = e.target.closest('tr.row');
    if (!tr) return;
    e.preventDefault();
    openDetail(tr, state.byId[tr.dataset.id]);
  });
  function selectType(type) {
    state.type = type;
    Array.prototype.forEach.call(typesBox.children, function (c) {
      c.setAttribute('aria-selected', c.dataset.type === state.type ? 'true' : 'false');
    });
    load();
  }
  typesBox.addEventListener('click', function (e) {
    var b = e.target.closest('button[data-type]');
    if (!b) return;
    if (b.dataset.type === state.type && !globalQuery()) return;
    search.value = '';
    selectType(b.dataset.type);
  });
  leagueSel.addEventListener('change', function () { state.league = leagueSel.value; load(); });
  search.placeholder = 'Search all items by name…';
  var searchTimer;
  search.addEventListener('input', function () {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(function () { state.open = null; syncUrl(); render(); }, 200);
  });
  if (lowToggle) lowToggle.addEventListener('change', render);
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
      state.types = j.types || ['Currency'];
      state.stashTypes = j.stashTypes || [];
      renderTypes(state.types);
      load();
    })
    .catch(function () {
      statusEl.textContent = 'League list is unavailable right now. Try again in a few minutes.';
    });
})();
