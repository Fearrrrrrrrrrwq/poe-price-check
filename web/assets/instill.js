/* Kalkulator Instill PoE2 - /tools/poe2-instill/.
 *
 * Lista notable jest w HTML (data-recipe="i,j,k" = indeksy emocji w kolejnosci
 * slotow). Skrypt: wynik dla trzech wybranych emocji, wyszukiwanie po nazwie
 * i efekcie, filtr "tylko to, co moge zrobic z posiadanych emocji".
 */
(function () {
  'use strict';

  // Teksty w jezyku strony (<script type="application/json" id="i18n">),
  // angielski jako zapas - skrypt dziala tez na stronie bez tlumaczen.
  var I18N = (function () {
    try { return JSON.parse(document.getElementById('i18n').textContent); } catch (e) { return {}; }
  })();
  function txt(key, fallback, vars) {
    return String(I18N[key] || fallback).replace(/\{(\w+)\}/g, function (m, k) {
      return vars && Object.prototype.hasOwnProperty.call(vars, k) ? vars[k] : m;
    });
  }

  var root = document.querySelector('.instill');
  if (!root) return;
  var names = JSON.parse(root.dataset.emotions || '[]');
  var rows = Array.prototype.slice.call(document.querySelectorAll('.notables .notable'));
  var selects = Array.prototype.slice.call(document.querySelectorAll('.slots select'));
  var result = document.querySelector('.combo-result');
  var search = document.getElementById('nt-search');
  var count = document.querySelector('.nt-count');
  var owned = new Set();

  var byRecipe = {};
  rows.forEach(function (li) { byRecipe[li.dataset.recipe] = li; });

  function combo() {
    var picked = selects.map(function (s) { return s.value; });
    if (picked.some(function (v) { return v === ''; })) {
      result.innerHTML = '<p class="note">' + txt('in_pick', 'Pick an emotion for each slot.') + '</p>';
      return;
    }
    var li = byRecipe[picked.join(',')];
    if (!li) {
      result.innerHTML = '<p class="note">' + txt('in_none', 'No notable uses these three emotions in this order. ' +
        'Try another order — each order is a different recipe.') + '</p>';
      return;
    }
    var clone = li.cloneNode(true);
    clone.classList.add('picked');
    result.innerHTML = '';
    result.appendChild(clone);
  }

  function filter() {
    var q = search.value.trim().toLowerCase();
    var shown = 0;
    rows.forEach(function (li) {
      var ok = !q || li.textContent.toLowerCase().indexOf(q) !== -1;
      if (ok && owned.size) {
        ok = li.dataset.recipe.split(',').every(function (i) { return owned.has(i); });
      }
      li.hidden = !ok;
      if (ok) shown++;
    });
    count.textContent = shown === rows.length ? txt('in_count', '{n} notables', { n: rows.length })
      : txt('in_count_of', '{shown} of {n} notables', { shown: shown, n: rows.length });
  }

  selects.forEach(function (s) { s.addEventListener('change', combo); });
  search.addEventListener('input', filter);
  document.querySelector('.owned').addEventListener('click', function (e) {
    var b = e.target.closest('button[data-emo]');
    if (!b) return;
    var on = b.getAttribute('aria-pressed') !== 'true';
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
    if (on) owned.add(b.dataset.emo); else owned.delete(b.dataset.emo);
    filter();
  });

  // Klikniecie przepisu na liscie wpisuje go w sloty - latwo sprawdzic sasiednie
  // kolejnosci tych samych emocji.
  document.querySelector('.notables').addEventListener('click', function (e) {
    var li = e.target.closest('.notable');
    if (!li) return;
    li.dataset.recipe.split(',').forEach(function (v, i) { selects[i].value = v; });
    combo();
    result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });

  window.poeInstillNames = names;
})();
