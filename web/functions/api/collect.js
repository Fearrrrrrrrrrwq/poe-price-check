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

export async function onRequestPost({ request, env }) {
  const data = await readJson(request);

  const install = text(data.id, 32);
  // Bez identyfikatora sygnal jest bezuzyteczny - nie da sie go przypisac
  // do instalacji, a zasmiecilby wszystkie liczniki unikalnych uzytkownikow.
  if (!install) return json({ ok: true });

  await env.DB.prepare(
    `INSERT INTO pings
       (at, install, version, os, language, league, transport,
        checks, failures, uptime_min)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    Date.now(),
    install,
    text(data.version),
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
