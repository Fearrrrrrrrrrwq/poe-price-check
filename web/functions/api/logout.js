/** Wylogowanie.  POST /api/logout */

import { COOKIE, destroySession, json } from '../../lib/auth.js';

export async function onRequestPost({ request, env }) {
  await destroySession(request, env);

  // Sesja znika z bazy, ale ciasteczko trzeba jeszcze uniewaznic
  // w przegladarce - inaczej zostaje martwy token do konca terminu.
  return json({ ok: true }, 200, {
    'Set-Cookie': `${COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`,
  });
}
