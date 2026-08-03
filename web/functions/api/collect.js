/**
 * Odbior anonimowego sygnalu z aplikacji.  POST /api/collect
 *
 * Jedyny endpoint otwarty dla swiata. Nie wymaga logowania, wiec musi byc
 * odporny na smieci: kazde pole przycinamy i rzutujemy, a zle zapytanie
 * konczy sie zwyklym "ok" - aplikacja gracza nie ma z czym zrobic bledu,
 * a odpowiedz nie zdradza, co odrzucilismy.
 */

import { json, readJson } from '../../lib/auth.js';

const TEXT_LIMIT = 64;
const COUNT_LIMIT = 1000000;

function text(value, limit = TEXT_LIMIT) {
  return String(value == null ? '' : value).slice(0, limit);
}

function count(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < 0) return 0;
  return Math.min(Math.floor(number), COUNT_LIMIT);
}

const KIND_LIMIT = 24;
const MAX_KINDS = 20;
// Etykiety sa generowane przez kod aplikacji, ale endpoint jest otwarty dla
// swiata, wiec traktujemy je jak kazde inne dane z zewnatrz: tylko litery,
// cyfry i podkreslnik. Bez tego do panelu dalo by sie wstrzyknac dowolny tekst.
const KIND_RE = /^[a-z0-9_]+$/;

/** Zamienia {kind: liczba} na liste par, odsiewajac smieci. */
function errorPairs(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return [];
  const pairs = [];
  for (const [rawKind, rawCount] of Object.entries(value)) {
    const kind = String(rawKind).slice(0, KIND_LIMIT).toLowerCase();
    const times = count(rawCount);
    if (!times || !KIND_RE.test(kind)) continue;
    pairs.push([kind, times]);
    if (pairs.length >= MAX_KINDS) break;
  }
  return pairs;
}

export async function onRequestPost({ request, env }) {
  const data = await readJson(request);

  const install = text(data.id, 32);
  // Bez identyfikatora sygnal jest bezuzyteczny - nie da sie go przypisac
  // do instalacji, a zasmiecilby wszystkie liczniki unikalnych uzytkownikow.
  if (!install) return json({ ok: true });

  const now = Date.now();
  const version = text(data.version);
  const pairs = errorPairs(data.errors);
  if (pairs.length) {
    // Jednym batchem, a nie w petli z await: kazde osobne zapytanie to osobna
    // podroz do D1, a sygnal potrafi niesc kilkanascie rodzajow naraz.
    await env.DB.batch(pairs.map(([kind, times]) => env.DB.prepare(
      'INSERT INTO errors (at, install, version, kind, count) VALUES (?, ?, ?, ?, ?)'
    ).bind(now, install, version, kind, times)));
  }

  await env.DB.prepare(
    `INSERT INTO pings
       (at, install, version, os, language, league, transport,
        checks, failures, uptime_min)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    now,
    install,
    version,
    text(data.os),
    text(data.language, 8),
    text(data.league),
    text(data.transport, 16),
    count(data.checks),
    count(data.failures),
    count(data.uptime_min)
  ).run();

  return json({ ok: true });
}

/** GET tutaj to zwykle pomylka - odpowiadamy krotko zamiast 405 z Pages. */
export function onRequestGet() {
  return json({ ok: true, hint: 'ten adres przyjmuje POST' });
}
