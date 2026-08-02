/* Licznik odwiedzin.
 *
 * Zadnych ciasteczek, zadnego identyfikatora w przegladarce. Wysylamy tylko
 * sciezke, jezyk i host, z ktorego ktos przyszedl - reszte (kraj, rodzaj
 * urzadzenia) serwer odczytuje z samego zapytania i nie zapisuje adresu IP.
 *
 * sendBeacon zamiast fetch: przetrwa zamkniecie karty i nie opoznia strony.
 * Typ text/plain jest celowy - przy application/json przegladarka wyslalaby
 * najpierw zapytanie OPTIONS.
 */
(function () {
  'use strict';

  // Strona reklamuje sie prywatnoscia, wiec wypada uszanowac to ustawienie,
  // nawet jesli kosztuje troche danych.
  var dnt = navigator.doNotTrack || window.doNotTrack;
  if (dnt === '1' || dnt === 'yes') return;

  var body = JSON.stringify({
    path: location.pathname,
    lang: document.documentElement.lang || '',
    ref: document.referrer || ''
  });

  try {
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/hit', new Blob([body], { type: 'text/plain' }));
    } else {
      fetch('/api/hit', {
        method: 'POST',
        body: body,
        headers: { 'Content-Type': 'text/plain' },
        keepalive: true
      });
    }
  } catch (err) {
    /* licznik nie ma prawa niczego zepsuc */
  }
})();
