/**
 * Zapasowy most dla poe-price-check.
 *
 * Uzyj tego zamiast dokumentu Google, jesli przegladarka Steam Overlay nie
 * udzwignie pelnego edytora Dokumentow (Docs to ciezki JS - potrafi sie nie
 * zaladowac albo dzialac tak wolno, ze wklejanie nie zdazy przed zamknieciem
 * overlaya).
 *
 * Wdrozenie:
 *   1. script.google.com -> Nowy projekt -> wklej ten plik.
 *   2. Wdroz -> Nowe wdrozenie -> typ "Aplikacja internetowa".
 *   3. "Wykonaj jako": Ja.  "Kto ma dostep": Wszyscy.
 *   4. Skopiuj URL konczacy sie na /exec do config.json jako "appsscript_url"
 *      i ustaw "transport": "appsscript".
 *
 * W sesji Boosteroida otworz ten sam URL w przegladarce Steam Overlay.
 * Lokalny skrypt czyta tresc przez <URL>?r=1.
 */

var STORE_KEY = 'poe_item_text';

function doGet(e) {
  if (e && e.parameter && e.parameter.r) {
    var text = PropertiesService.getScriptProperties().getProperty(STORE_KEY) || '';
    return ContentService.createTextOutput(text)
      .setMimeType(ContentService.MimeType.TEXT);
  }
  return HtmlService.createHtmlOutputFromFile('page')
    .setTitle('PoE bridge')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/** Wywolywane z przegladarki przez google.script.run. */
function save(text) {
  PropertiesService.getScriptProperties().setProperty(STORE_KEY, text || '');
  return 'ok';
}
