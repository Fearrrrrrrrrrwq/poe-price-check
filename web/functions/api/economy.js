/**
 * Ceny rynkowe dla strony /economy/.
 *
 *   GET /api/economy?game=poe2&league=Forbidden%20Rites&type=Currency
 *   GET /api/economy?game=poe2&leagues=1            -> lista lig
 *
 * Zrodlo cen: poe.ninja (strona pokazuje atrybucje). poe.ninja sam trzyma
 * odpowiedzi 30 minut, wiec my trzymamy je tyle samo w pamieci podrecznej
 * Cloudflare - kazda liga/kategoria idzie do poe.ninja najwyzej raz na pol
 * godziny, niezaleznie od ruchu na stronie.
 *
 * Zmiany 24h i 7d liczymy z "sparkline" poe.ninja (7 dziennych punktow, %
 * zmiany wzgledem wartosci sprzed tygodnia). 30 dni poe.ninja nie podaje, wiec
 * raz dziennie odkladamy migawke cen do D1 i zmiana 30d zapelnia sie sama
 * w ciagu miesiaca. Brak tabeli albo bazy nie psuje odpowiedzi - wtedy po
 * prostu nie ma kolumny 30d.
 */

const NINJA = 'https://poe.ninja';
const UA = 'poe-price-check/1.0 (+https://poepricecheck.eu)';
const CACHE_SECONDS = 1800;
const LEAGUE_CACHE_SECONDS = 6 * 3600;

// Kategorie sprawdzone na zywym API poe.ninja (niepuste odpowiedzi).
export const TYPES = {
  poe2: ['Currency', 'Fragments', 'Runes', 'Essences', 'SoulCores', 'Idols',
    'UncutGems', 'LineageSupportGems', 'Expedition', 'Delirium', 'Breach',
    'Ritual', 'Abyss'],
  poe1: ['Currency', 'Fragment', 'Scarab', 'Essence', 'Fossil', 'Resonator',
    'Oil', 'DeliriumOrb', 'Omen', 'Tattoo', 'Artifact', 'DivinationCard',
    'Runegraft', 'AllflameEmber'],
};

function json(body, status = 200, maxAge = 300) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': status === 200 ? `public, max-age=${maxAge}` : 'no-store',
      'X-Robots-Tag': 'noindex',
    },
  });
}

async function cachedFetchJson(url, ttl, ctx) {
  const cache = caches.default;
  const key = new Request(url);
  const hit = await cache.match(key);
  if (hit) return hit.json();
  const response = await fetch(url, { headers: { 'User-Agent': UA, Accept: 'application/json' } });
  if (!response.ok) throw new Error(`upstream ${response.status}`);
  const data = await response.json();
  const stored = new Response(JSON.stringify(data), {
    headers: { 'Content-Type': 'application/json', 'Cache-Control': `public, max-age=${ttl}` },
  });
  ctx.waitUntil(cache.put(key, stored));
  return data;
}

async function leagues(game, ctx) {
  const api = game === 'poe2' ? 'trade2' : 'trade';
  const data = await cachedFetchJson(
    `https://www.pathofexile.com/api/${api}/data/leagues`, LEAGUE_CACHE_SECONDS, ctx);
  const seen = new Set();
  const names = [];
  for (const entry of data.result || []) {
    const id = entry.id || entry.text;
    // SSF nie ma handlu - poe.ninja i tak ich nie sledzi.
    if (!id || seen.has(id) || /ssf|solo self-found/i.test(id)) continue;
    seen.add(id);
    names.push(id);
  }
  return names;
}

function round(value, digits = 4) {
  const f = 10 ** digits;
  return Math.round(value * f) / f;
}

function change24h(data) {
  // data[i] = % zmiany wzgledem poczatku tygodnia. Zmiana dzienna to stosunek
  // dwoch ostatnich punktow, nie ich roznica.
  if (!Array.isArray(data) || data.length < 2) return null;
  const a = data[data.length - 2];
  const b = data[data.length - 1];
  if (a == null || b == null || a <= -100) return null;
  return round(((100 + b) / (100 + a) - 1) * 100, 2);
}

async function snapshot30d(env, game, league, type, items) {
  if (!env.DB) return {};
  const day = new Date().toISOString().slice(0, 10);
  const monthAgo = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);
  try {
    const exists = await env.DB.prepare(
      'SELECT 1 FROM economy_prices WHERE game = ?1 AND league = ?2 AND type = ?3 AND day = ?4 LIMIT 1',
    ).bind(game, league, type, day).first();
    if (!exists) {
      const stmt = env.DB.prepare(
        'INSERT OR IGNORE INTO economy_prices (game, league, type, day, item, value) VALUES (?1, ?2, ?3, ?4, ?5, ?6)',
      );
      const rows = items.filter((it) => it.value > 0)
        .map((it) => stmt.bind(game, league, type, day, it.id, it.value));
      for (let i = 0; i < rows.length; i += 100) {
        await env.DB.batch(rows.slice(i, i + 100));
      }
      // Sprzatanie przy pierwszej migawce dnia: dluzej niz ~40 dni nic nie
      // jest potrzebne (kolumna 30d), a tabela rosnie o kilka tysiecy wierszy dziennie.
      const cutoff = new Date(Date.now() - 40 * 86400000).toISOString().slice(0, 10);
      await env.DB.prepare('DELETE FROM economy_prices WHERE day < ?1').bind(cutoff).run();
    }
    const old = await env.DB.prepare(
      `SELECT item, value FROM economy_prices
        WHERE game = ?1 AND league = ?2 AND type = ?3
          AND day = (SELECT MIN(day) FROM economy_prices
                      WHERE game = ?1 AND league = ?2 AND type = ?3 AND day >= ?4)`,
    ).bind(game, league, type, monthAgo).all();
    const out = {};
    for (const row of old.results || []) out[row.item] = row.value;
    return out;
  } catch (err) {
    return {}; // brak tabeli / chwilowy blad bazy - bez kolumny 30d
  }
}

export async function onRequestGet({ request, env, waitUntil }) {
  const ctx = { waitUntil };
  const url = new URL(request.url);
  const game = url.searchParams.get('game') === 'poe1' ? 'poe1' : 'poe2';

  if (url.searchParams.get('leagues')) {
    try {
      return json({ game, leagues: await leagues(game, ctx), types: TYPES[game] }, 200, 3600);
    } catch (err) {
      return json({ error: 'leagues_unavailable' }, 502);
    }
  }

  const type = url.searchParams.get('type') || 'Currency';
  const league = (url.searchParams.get('league') || '').slice(0, 80);
  if (!TYPES[game].includes(type) || !league) {
    return json({ error: 'bad_request' }, 400);
  }

  let data;
  try {
    data = await cachedFetchJson(
      `${NINJA}/${game}/api/economy/exchange/current/overview?league=${encodeURIComponent(league)}&type=${type}`,
      CACHE_SECONDS, ctx);
  } catch (err) {
    return json({ error: 'upstream_unavailable' }, 502);
  }

  const core = data.core || {};
  const meta = new Map((data.items || []).map((it) => [it.id, it]));
  // Kurs waluty bazowej: PoE2 liczy w Divine, PoE1 w Chaos. rates mowi, ile
  // danej waluty daje 1 jednostka bazowej.
  const primary = core.primary || (game === 'poe2' ? 'divine' : 'chaos');
  const rates = core.rates || {};

  const items = (data.lines || []).map((line) => {
    const m = meta.get(line.id) || {};
    return {
      id: line.id,
      name: m.name || line.id,
      icon: m.image ? `https://web.poecdn.com${m.image}` : '',
      category: m.category || type,
      value: line.primaryValue ?? 0,
      volume: line.volumePrimaryValue ?? 0,
      change7d: line.sparkline ? round(line.sparkline.totalChange ?? 0, 2) : null,
      change24h: line.sparkline ? change24h(line.sparkline.data) : null,
      spark: line.sparkline && Array.isArray(line.sparkline.data) ? line.sparkline.data : [],
    };
  }).filter((it) => it.value > 0);

  const old = await snapshot30d(env, game, league, type, items);
  for (const it of items) {
    const prev = old[it.id];
    it.change30d = prev > 0 ? round((it.value / prev - 1) * 100, 2) : null;
  }

  return json({
    game, league, type, primary, rates,
    source: 'poe.ninja',
    fetchedAt: new Date().toISOString(),
    items,
  }, 200, 600);
}
