/**
 * Blokada calego /admin/.
 *
 * To jest ta roznica wzgledem poprzedniej wersji: panel nie jest juz plikiem,
 * ktory kazdy pobiera i ktory sam decyduje, czy sie pokazac. Bez waznej sesji
 * Cloudflare w ogole go nie wyda.
 */

import { currentSession } from '../../lib/auth.js';

export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);

  // Strona logowania musi byc dostepna bez sesji - inaczej nie da sie zalogowac.
  if (url.pathname.startsWith('/admin/login')) return next();

  const session = await currentSession(request, env);
  if (session) return next();

  const target = new URL('/admin/login/', url.origin);
  return new Response(null, {
    status: 302,
    headers: { Location: target.toString(), 'Cache-Control': 'no-store' },
  });
}
