/* Publiczna strona statystyk spolecznosci - /{lang}/community/.
 *
 * Zero logowania, zero danych wrazliwych: pobiera /api/public-stats (te same
 * agregaty co panel admina w assets/admin.js, ale bez bledow/odsetka awarii/
 * pojedynczych instalacji) i rysuje je tymi samymi klasami CSS co panel
 * (.bar-row/.bar-track/.bar-fill), zeby wygladaly spojnie z reszta strony.
 *
 * CSP nie pozwala na atrybut style ani zewnetrzne biblioteki - szerokosc
 * paskow idzie przez CSSOM (element.style.width), ktorego CSP nie obejmuje.
 */
(function () {
  'use strict';

  var nf = new Intl.NumberFormat(document.documentElement.lang || 'en');

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function setTile(id, value) {
    var node = document.getElementById(id);
    if (node) node.textContent = nf.format(value);
  }

  function renderBars(host, items) {
    if (!host) return;
    clear(host);
    if (!items || !items.length) {
      host.appendChild(el('p', 'note', '—'));
      return;
    }
    var top = items[0].count || 1;
    items.forEach(function (item) {
      var row = el('div', 'bar-row');
      row.appendChild(el('span', 'bar-name', item.name));

      var track = el('span', 'bar-track');
      var fill = el('span', 'bar-fill');
      fill.style.width = Math.round((item.count / top) * 100) + '%';
      track.appendChild(fill);
      row.appendChild(track);

      row.appendChild(el('span', 'bar-count',
        nf.format(item.count) + '  ·  ' + item.share + '%'));
      host.appendChild(row);
    });
  }

  fetch('/api/public-stats')
    .then(function (res) { return res.ok ? res.json() : Promise.reject(res.status); })
    .then(function (data) {
      setTile('cs-installs', data.installs_total);
      setTile('cs-installs-week', data.installs_week);
      setTile('cs-checks-week', data.checks_week);
      setTile('cs-session', data.avg_session_min);

      renderBars(document.querySelector('[data-bars="systems"]'), data.systems);
      renderBars(document.querySelector('[data-bars="leagues"]'), data.leagues);
      renderBars(document.querySelector('[data-bars="versions"]'), data.versions);
      renderBars(document.querySelector('[data-bars="languages"]'), data.languages);
      renderBars(document.querySelector('[data-bars="transports"]'), data.transports);

      var updated = document.getElementById('cs-updated');
      if (updated && data.updated) {
        updated.textContent = new Date(data.updated).toLocaleString(
          document.documentElement.lang || 'en');
      }
    })
    .catch(function () {
      var board = document.getElementById('cs-board');
      if (board) board.textContent = '—';
    });
})();
