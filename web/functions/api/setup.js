/**
 * Zalozenie pierwszego konta.  POST /api/setup  {token, login, password}
 *
 * Dziala tylko wtedy, gdy kont jeszcze nie ma, i tylko z tokenem ustawionym
 * jako sekret projektu:
 *   wrangler pages secret put SETUP_TOKEN
 *
 * Sam warunek "brak kont" by nie wystarczyl - miedzy wdrozeniem a Twoim
 * pierwszym wejsciem kazdy moglby zajac panel. Po zalozeniu konta endpoint
 * przestaje cokolwiek robic.
 */

import { hashPassword, json, readJson } from '../../lib/auth.js';

const MIN_PASSWORD = 12;

export async function onRequestPost({ request, env }) {
  if (!env.SETUP_TOKEN) {
    return json({ error: 'setup_disabled' }, 403);
  }

  const existing = await env.DB.prepare('SELECT COUNT(*) AS count FROM admins').first();
  if (existing.count > 0) {
    return json({ error: 'already_done' }, 409);
  }

  const data = await readJson(request);

  if (String(data.token || '') !== env.SETUP_TOKEN) {
    return json({ error: 'bad_token' }, 403);
  }

  const login = String(data.login || '').trim().slice(0, 64);
  const password = String(data.password || '');

  if (!login) return json({ error: 'no_login' }, 400);
  if (password.length < MIN_PASSWORD) {
    return json({ error: 'weak_password', min: MIN_PASSWORD }, 400);
  }

  await env.DB.prepare(
    'INSERT INTO admins (login, hash, created) VALUES (?, ?, ?)'
  ).bind(login, await hashPassword(password), Date.now()).run();

  return json({ ok: true, login });
}
