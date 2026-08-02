/**
 * Przekierowanie z www na domene glowna.
 *
 * Oba adresy sa podpiete do tego samego projektu, wiec bez tego ta sama tresc
 * siedzi pod dwoma adresami. Znaczniki canonical to porzadkuja, ale twarde
 * przekierowanie jest pewniejsze - odnosniki i ruch licza sie na jeden adres,
 * a nie rozchodza na dwa.
 *
 * Plik _redirects tego nie zalatwia: obsluguje sciezki w obrebie jednego
 * hosta, a nie przenosiny miedzy hostami.
 *
 * Middleware z korzenia functions/ dziala dla WSZYSTKICH adresow i uruchamia
 * sie przed tym z functions/admin/, wiec panel dalej jest chroniony.
 */

export async function onRequest({ request, next }) {
  const url = new URL(request.url);

  if (url.hostname.startsWith('www.')) {
    url.hostname = url.hostname.slice(4);
    // 301, bo to zmiana na stale - wyszukiwarki przepisza wtedy oceny
    // na adres docelowy.
    return Response.redirect(url.toString(), 301);
  }

  return next();
}
