/**
 * Hasla, sesje i ciasteczka dla panelu.
 *
 * Lezy poza katalogiem functions/ celowo: wszystko, co tam wrzucimy, staje sie
 * osobnym adresem. To jest biblioteka, a nie endpoint.
 *
 * Zalozenia:
 *   - hasla trzymamy jako PBKDF2-SHA256, nigdy jawnie,
 *   - w bazie siedzi skrot tokenu sesji, nie sam token - wyciek bazy nie oddaje
 *     wiec gotowych sesji do przejecia,
 *   - porownania sekretow ida w stalym czasie.
 */

/*
 * Cloudflare Workers odmawia PBKDF2 powyzej 100 000 iteracji:
 *   "Pbkdf2 failed: iteration counts above 100000 are not supported".
 * Lokalny workerd tego limitu NIE egzekwuje, wiec wychodzi to dopiero
 * na produkcji, bledem 1101.
 *
 * 100 000 iteracji to dzis za malo, wiec skladamy kilka rund: wynik jednej
 * wchodzi jako material wejsciowy nastepnej. Sol i dlugosc klucza zostaja
 * te same, a koszt lamania rosnie liniowo z liczba rund.
 *
 * To NIE jest zwykle PBKDF2 o 600 000 iteracji - stad wlasny znacznik
 * "pbkdf2x" w zapisie, zeby nikt nie probowal zweryfikowac tego standardowa
 * biblioteka i nie zachodzil w glowe, czemu nie wychodzi.
 */
const ITERATIONS = 100000;
const ROUNDS = 6;
const KEY_BYTES = 32;
const SALT_BYTES = 16;

export const COOKIE = 'ppc_session';
export const SESSION_DAYS = 14;

const encoder = new TextEncoder();

// --------------------------------------------------------------- kodowanie

function toBase64(bytes) {
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

function fromBase64(text) {
  const binary = atob(text);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

function toBase64Url(bytes) {
  return toBase64(bytes).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/** Porownanie odporne na pomiar czasu - zawsze przechodzi przez cala dlugosc. */
function sameBytes(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

// ------------------------------------------------------------------ hasla

async function derive(material, salt, iterations, rounds) {
  let input = material;
  let bits;
  for (let round = 0; round < rounds; round++) {
    const key = await crypto.subtle.importKey(
      'raw', input, 'PBKDF2', false, ['deriveBits']);
    bits = await crypto.subtle.deriveBits(
      { name: 'PBKDF2', hash: 'SHA-256', salt, iterations }, key, KEY_BYTES * 8);
    input = new Uint8Array(bits);
  }
  return new Uint8Array(bits);
}

export async function hashPassword(password) {
  const salt = crypto.getRandomValues(new Uint8Array(SALT_BYTES));
  const derived = await derive(
    encoder.encode(password), salt, ITERATIONS, ROUNDS);
  // Parametry ida razem z hashem, zeby dalo sie je pozniej podniesc bez
  // uniewazniania hasel juz zapisanych.
  return `pbkdf2x$sha256$${ITERATIONS}$${ROUNDS}$`
       + `${toBase64(salt)}$${toBase64(derived)}`;
}

export async function verifyPassword(password, stored) {
  const parts = String(stored || '').split('$');
  if (parts.length !== 6 || parts[0] !== 'pbkdf2x') return false;

  const iterations = Number(parts[2]);
  const rounds = Number(parts[3]);
  if (!Number.isFinite(iterations) || iterations < 1000) return false;
  // Zapis z wieksza liczba iteracji niz platforma obsluguje wywrocilby
  // deriveBits wyjatkiem, a stad 500 zamiast czystego "zle haslo".
  if (iterations > ITERATIONS) return false;
  if (!Number.isFinite(rounds) || rounds < 1 || rounds > 20) return false;

  let salt;
  let expected;
  try {
    salt = fromBase64(parts[4]);
    expected = fromBase64(parts[5]);
  } catch {
    return false;
  }

  const derived = await derive(
    encoder.encode(password), salt, iterations, rounds);
  return sameBytes(derived, expected);
}

// ------------------------------------------------------------------ sesje

export function newToken() {
  return toBase64Url(crypto.getRandomValues(new Uint8Array(32)));
}

/** Skrot tokenu - to on trafia do bazy. */
export async function tokenDigest(token) {
  const bits = await crypto.subtle.digest('SHA-256', encoder.encode(token));
  return toBase64(new Uint8Array(bits));
}

export function readCookie(request, name) {
  const header = request.headers.get('Cookie') || '';
  for (const part of header.split(';')) {
    const [key, ...rest] = part.trim().split('=');
    if (key === name) return rest.join('=');
  }
  return '';
}

export function sessionCookie(token, maxAgeSeconds) {
  // SameSite=Lax, a nie Strict: przy Strict wejscie na panel z linku
  // w innej karcie wygladaloby jak wylogowanie.
  return [
    `${COOKIE}=${token}`,
    'Path=/',
    'HttpOnly',
    'Secure',
    'SameSite=Lax',
    `Max-Age=${maxAgeSeconds}`,
  ].join('; ');
}

export async function createSession(env, adminId) {
  const token = newToken();
  const digest = await tokenDigest(token);
  const now = Date.now();
  const expires = now + SESSION_DAYS * 86400000;

  await env.DB.prepare(
    'INSERT INTO sessions (token, admin, created, expires) VALUES (?, ?, ?, ?)'
  ).bind(digest, adminId, now, expires).run();

  // Sprzatanie przy okazji logowania - nie potrzeba osobnego wyzwalacza.
  await env.DB.prepare('DELETE FROM sessions WHERE expires < ?').bind(now).run();

  return { token, expires };
}

export async function currentSession(request, env) {
  const token = readCookie(request, COOKIE);
  if (!token) return null;

  const row = await env.DB.prepare(
    `SELECT s.admin AS admin, s.expires AS expires, a.login AS login
       FROM sessions s JOIN admins a ON a.id = s.admin
      WHERE s.token = ? AND s.expires > ?`
  ).bind(await tokenDigest(token), Date.now()).first();

  return row || null;
}

export async function destroySession(request, env) {
  const token = readCookie(request, COOKIE);
  if (!token) return;
  await env.DB.prepare('DELETE FROM sessions WHERE token = ?')
    .bind(await tokenDigest(token)).run();
}

// ---------------------------------------------------------------- pomocne

export function json(data, status = 200, headers = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      ...headers,
    },
  });
}

export async function readJson(request) {
  try {
    return (await request.json()) || {};
  } catch {
    return {};
  }
}

export function clientIp(request) {
  return request.headers.get('CF-Connecting-IP') || '0.0.0.0';
}
