/**
 * Zmiana hasla.  POST /api/password  {current, next}
 *
 * Wymaga zalogowania i podania obecnego hasla - samo ciasteczko nie wystarczy,
 * bo ktos, kto dopadl niezablokowanej przegladarki, nie moze przy okazji
 * przejac konta na stale.
 */

import {
  currentSession, hashPassword, json, readJson, verifyPassword,
} from '../../lib/auth.js';

const MIN_PASSWORD = 12;

export async function onRequestPost({ request, env }) {
  const session = await currentSession(request, env);
  if (!session) return json({ error: 'unauthorised' }, 401);

  const data = await readJson(request);
  const current = String(data.current || '');
  const next = String(data.next || '');

  if (next.length < MIN_PASSWORD) {
    return json({ error: 'weak_password', min: MIN_PASSWORD }, 400);
  }

  const admin = await env.DB.prepare('SELECT id, hash FROM admins WHERE id = ?')
    .bind(session.admin).first();

  if (!admin || !(await verifyPassword(current, admin.hash))) {
    return json({ error: 'bad_credentials' }, 401);
  }

  await env.DB.prepare('UPDATE admins SET hash = ? WHERE id = ?')
    .bind(await hashPassword(next), admin.id).run();

  // Zmiana hasla ma wyrzucic wszystkie inne sesje - to caly sens zmiany,
  // gdy podejrzewasz, ze ktos je poznal.
  await env.DB.prepare('DELETE FROM sessions WHERE admin = ?').bind(admin.id).run();

  return json({ ok: true, relogin: true });
}
