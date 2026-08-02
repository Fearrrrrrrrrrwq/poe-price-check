/**
 * Logowanie do panelu.  POST /api/login  {login, password}
 *
 * Odpowiedz nigdy nie mowi, ktore pole bylo zle - inaczej endpoint sluzylby
 * do sprawdzania, jakie loginy istnieja.
 */

import {
  clientIp, createSession, json, readJson, sessionCookie, SESSION_DAYS,
  verifyPassword,
} from '../../lib/auth.js';

const WINDOW_MS = 15 * 60 * 1000;
const MAX_ATTEMPTS = 10;

// Zapis o ksztalcie prawdziwego hasla, ktorego nikt nie zna - sluzy tylko do
// tego, zeby proba z nieistniejacym loginem trwala tyle samo co z istniejacym.
const DUMMY_HASH = 'pbkdf2x$sha256$100000$6$'
  + 'AAAAAAAAAAAAAAAAAAAAAA==$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=';

export async function onRequestPost({ request, env }) {
  const ip = clientIp(request);
  const since = Date.now() - WINDOW_MS;

  // Bez tego haslo mozna zgadywac w petli - PBKDF2 spowalnia pojedyncza probe,
  // ale nie milion prob.
  const recent = await env.DB.prepare(
    'SELECT COUNT(*) AS failed FROM login_attempts WHERE ip = ? AND at > ?'
  ).bind(ip, since).first();

  if (recent && recent.failed >= MAX_ATTEMPTS) {
    return json({ error: 'too_many' }, 429);
  }

  const data = await readJson(request);
  const login = String(data.login || '').trim().slice(0, 64);
  const password = String(data.password || '');

  const admin = login
    ? await env.DB.prepare('SELECT id, login, hash FROM admins WHERE login = ?')
        .bind(login).first()
    : null;

  // Liczymy hash takze wtedy, gdy login nie istnieje. Inaczej brak konta
  // odpowiadalby natychmiast, a istniejace - po chwili, i czas odpowiedzi
  // zdradzalby, ktore loginy sa prawdziwe.
  //
  // Atrapa musi miec te same parametry co prawdziwe zapisy: przy innych
  // policzylaby sie w innym czasie, a przy zawyzonych iteracjach wywrocilaby
  // sie wyjatkiem na limicie Workers.
  const stored = admin ? admin.hash : DUMMY_HASH;
  const ok = await verifyPassword(password, stored);

  if (!admin || !ok) {
    await env.DB.prepare('INSERT INTO login_attempts (ip, at) VALUES (?, ?)')
      .bind(ip, Date.now()).run();
    await env.DB.prepare('DELETE FROM login_attempts WHERE at < ?')
      .bind(since).run();
    return json({ error: 'bad_credentials' }, 401);
  }

  const { token } = await createSession(env, admin.id);

  return json({ ok: true, login: admin.login }, 200, {
    'Set-Cookie': sessionCookie(token, SESSION_DAYS * 86400),
  });
}
