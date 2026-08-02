/**
 * Licznik odwiedzin strony.  POST /api/hit
 *
 * Otwarty dla swiata, tak jak /api/collect - i tak samo nieufny wobec tego,
 * co dostaje.
 *
 * Zasady, ktore trzymamy tak samo jak w telemetrii aplikacji:
 *   - zadnych ciasteczek,
 *   - nie zapisujemy adresu IP ani pelnego opisu przegladarki,
 *   - tozsamosc odwiedzajacego to skrot, ktory zmienia sie kazdej doby,
 *     wiec nie da sie po nim sledzic nikogo miedzy dniami,
 *   - z adresu odsylajacego bierzemy sam host, bez sciezki i parametrow.
 */

import { json, readJson } from '../../lib/auth.js';

const encoder = new TextEncoder();

/** Skrot dobowy: ten sam czlowiek jutro wyglada jak ktos inny. */
async function visitorHash(request, env) {
  const parts = [
    request.headers.get('CF-Connecting-IP') || '',
    request.headers.get('User-Agent') || '',
    new Date().toISOString().slice(0, 10),
    // Bez tajnej soli dalo by sie odtworzyc adres IP zgadywaniem - przestrzen
    // adresow IPv4 jest na to za mala.
    env.ANALYTICS_SALT || '',
  ];
  const bits = await crypto.subtle.digest('SHA-256', encoder.encode(parts.join('|')));
  return [...new Uint8Array(bits).slice(0, 8)]
    .map((b) => b.toString(16).padStart(2, '0')).join('');
}

/** Bardzo zgrubny podzial - wystarczy, zeby wiedziec, czy warto dbac o telefony. */
function device(agent) {
  const text = String(agent || '').toLowerCase();
  if (/ipad|tablet/.test(text)) return 'tablet';
  if (/mobi|android|iphone/.test(text)) return 'mobile';
  return 'desktop';
}

/** Z adresu odsylajacego zostawiamy sam host. */
function referrerHost(value) {
  const text = String(value || '').trim();
  if (!text) return '';
  try {
    return new URL(text).hostname.replace(/^www\./, '').slice(0, 64);
  } catch {
    return '';
  }
}

/** Sciezki normalizujemy, zeby nie zrobil sie z tego smietnik. */
function cleanPath(value) {
  const text = String(value || '/').split('?')[0].split('#')[0];
  return ('/' + text.replace(/^\/+/, '')).slice(0, 128);
}

export async function onRequestPost({ request, env }) {
  const data = await readJson(request);

  // Panel administracyjny nie jest ruchem, ktory chcemy liczyc.
  const path = cleanPath(data.path);
  if (path.startsWith('/admin')) return json({ ok: true });

  await env.DB.prepare(
    `INSERT INTO visits (at, path, lang, ref, country, device, visitor)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    Date.now(),
    path,
    String(data.lang || '').slice(0, 8),
    referrerHost(data.ref),
    request.headers.get('CF-IPCountry') || '',
    device(request.headers.get('User-Agent')),
    await visitorHash(request, env)
  ).run();

  return json({ ok: true });
}
