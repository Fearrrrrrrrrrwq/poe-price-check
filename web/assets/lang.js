/* Strona wejsciowa: kieruje na wersje jezykowa przegladarki.
   Robot i tak dojdzie wszedzie przez hreflang i liste linkow, wiec brak
   skryptu niczego nie psuje - dlatego przekierowanie jest tu, a nie na serwerze. */
(function () {
  'use strict';
  var SUPPORTED = ['en', 'pl', 'de', 'es', 'pt', 'ru'];
  var FALLBACK = 'en';
  // Ukrainski i bialoruski kierujemy na rosyjski - lepszy niz angielski.
  var ALIAS = { uk: 'ru', be: 'ru' };

  function pick() {
    var wanted = navigator.languages || [navigator.language || FALLBACK];
    for (var i = 0; i < wanted.length; i++) {
      var code = String(wanted[i]).slice(0, 2).toLowerCase();
      code = ALIAS[code] || code;
      if (SUPPORTED.indexOf(code) !== -1) return code;
    }
    return FALLBACK;
  }

  try {
    // Wybor zapamietany przez uzytkownika ma pierwszenstwo nad przegladarka.
    var saved = localStorage.getItem('ppc-lang');
    var target = (saved && SUPPORTED.indexOf(saved) !== -1) ? saved : pick();
    location.replace('/' + target + '/');
  } catch (err) {
    location.replace('/' + FALLBACK + '/');
  }
})();
