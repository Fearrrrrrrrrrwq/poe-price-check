/* Logowanie do panelu.
 *
 * Nie ma tu zadnej logiki dostepu - formularz tylko oddaje dane do /api/login.
 * Sprawdza je serwer, a sesja wraca jako ciasteczko HttpOnly, ktorego ten
 * skrypt nawet nie widzi. To jest cala roznica wzgledem poprzedniej wersji,
 * gdzie haslo lezalo w localStorage.
 */
(function () {
  'use strict';

  var form = document.getElementById('login');
  var note = document.getElementById('login-note');
  var button = form.querySelector('button[type="submit"]');

  var MESSAGES = {
    bad_credentials: 'Nieprawidłowy login lub hasło.',
    too_many: 'Za dużo nieudanych prób. Spróbuj ponownie za kwadrans.',
  };

  function fail(text) {
    note.textContent = text;
    note.className = 'note error';
    button.disabled = false;
    button.textContent = 'Zaloguj';
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();

    button.disabled = true;
    button.textContent = 'Sprawdzam…';
    note.className = 'note';

    fetch('/api/login', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        login: document.getElementById('login-name').value.trim(),
        password: document.getElementById('login-pass').value
      })
    })
      .then(function (response) {
        return response.json().then(function (data) {
          return { ok: response.ok, data: data };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          fail(MESSAGES[result.data.error] || 'Nie udało się zalogować.');
          return;
        }
        // Ciasteczko jest juz ustawione - wystarczy wejsc na panel, reszte
        // zalatwi funkcja brzegowa.
        window.location.assign('/admin/');
      })
      .catch(function () {
        fail('Brak połączenia z serwerem.');
      });
  });
})();
