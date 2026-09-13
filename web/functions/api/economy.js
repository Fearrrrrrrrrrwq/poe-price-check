/**
 * Ceny rynkowe dla strony /economy/.
 *
 *   GET /api/economy?game=poe2&league=Forbidden%20Rites&type=Currency
 *   GET /api/economy?game=poe1&league=Allflame&type=UniqueArmour
 *   GET /api/economy?game=poe2&league=...&type=Currency&history=exalted-orb
 *   GET /api/economy?game=poe1&league=...&type=UniqueArmour&history=703
 *   GET /api/economy?game=poe2&leagues=1            -> lista lig + kategorie
 *
 * Zrodlo cen: poe.ninja (strona pokazuje atrybucje). poe.ninja sam trzyma
 * odpowiedzi 30 minut, wiec my trzymamy je tyle samo w pamieci podrecznej
 * Cloudflare - kazde zapytanie idzie do poe.ninja najwyzej raz na pol godziny,
 * niezaleznie od ruchu na stronie.
 *
 * Dwa rodzaje danych poe.ninja:
 *  - "exchange": waluty i przedmioty z gieldy (PoE1 i PoE2),
 *  - "stash": unikaty z publicznych stashy - TYLKO PoE1, bo GGG nie udostepnia
 *    publicznych stashy PoE2.
 *
 * Zmiany 24h i 7d liczymy z "sparkline" poe.ninja. 30 dni poe.ninja w przegladzie
 * nie podaje, wiec raz dziennie odkladamy migawke cen do D1. Historia calej ligi
 * dla pojedynczego przedmiotu przychodzi prosto z poe.ninja (?history=).
 */

const NINJA = 'https://poe.ninja';
const UA = 'poe-price-check/1.0 (+https://poepricecheck.eu)';
const CACHE_SECONDS = 1800;
const LEAGUE_CACHE_SECONDS = 6 * 3600;

// Kategorie sprawdzone na zywym API poe.ninja (niepuste odpowiedzi).
const EXCHANGE = {
  poe2: ['Currency', 'Fragments', 'Runes', 'Essences', 'SoulCores', 'Idols',
    'UncutGems', 'LineageSupportGems', 'Expedition', 'Delirium', 'Breach',
    'Ritual', 'Abyss'],
  poe1: ['Currency', 'Fragment', 'Scarab', 'Essence', 'Fossil', 'Resonator',
    'Oil', 'DeliriumOrb', 'Omen', 'Tattoo', 'Artifact', 'DivinationCard',
    'Runegraft', 'AllflameEmber'],
};
const STASH = {
  poe2: [],
  poe1: ['UniqueWeapon', 'UniqueArmour', 'UniqueAccessory', 'UniqueJewel',
    'UniqueFlask', 'UniqueMap', 'UniqueRelic', 'UniqueTincture',
    // Lzejsze kategorie stash - warto je miec dla wyszukiwania po nazwie.
    // SkillGem (3,7 MB) i BaseType (7,4 MB) celowo pominiete: za ciezkie.
    'ClusterJewel', 'Beast', 'Map', 'BlightedMap', 'Invitation'],
};
export const TYPES = {
  poe2: [...EXCHANGE.poe2, ...STASH.poe2],
  poe1: [...EXCHANGE.poe1, ...STASH.poe1],
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

async function exchangeOverview(game, league, type, ctx) {
  const data = await cachedFetchJson(
    `${NINJA}/${game}/api/economy/exchange/current/overview?league=${encodeURIComponent(league)}&type=${type}`,
    CACHE_SECONDS, ctx);
  const core = data.core || {};
  const meta = new Map((data.items || []).map((it) => [it.id, it]));
  // PoE2 liczy w Divine, PoE1 w Chaos. rates: ile danej waluty za 1 bazowa.
  const primary = core.primary || (game === 'poe2' ? 'divine' : 'chaos');
  const items = (data.lines || []).map((line) => {
    const m = meta.get(line.id) || {};
    return {
      id: line.id,
      detailsId: m.detailsId || line.id,
      name: m.name || line.id,
      icon: m.image ? `https://web.poecdn.com${m.image}` : '',
      value: line.primaryValue ?? 0,
      volume: line.volumePrimaryValue ?? 0,
      change7d: line.sparkline ? round(line.sparkline.totalChange ?? 0, 2) : null,
      change24h: line.sparkline ? change24h(line.sparkline.data) : null,
      spark: line.sparkline && Array.isArray(line.sparkline.data) ? line.sparkline.data : [],
    };
  });
  return { primary, rates: core.rates || {}, items };
}

async function stashOverview(game, league, type, ctx) {
  const data = await cachedFetchJson(
    `${NINJA}/${game}/api/economy/stash/current/item/overview?league=${encodeURIComponent(league)}&type=${type}`,
    CACHE_SECONDS, ctx);
  const lines = data.lines || [];
  // Kurs Divine wyliczony z samych linii: divineValue / chaosValue.
  const ref = lines.find((l) => l.chaosValue > 0 && l.divineValue > 0);
  const rates = ref ? { divine: ref.divineValue / ref.chaosValue } : {};
  const items = lines.map((line) => {
    // poe.ninja zapisuje czesc pol po swojemu: wariant mapy ", Gen-24",
    // rodziny bestii "Goliaths|Unnaturals". Sprzatamy do jednego formatu.
    const clean = (v) => String(v || '').replace(/^[,\s]+/, '').split('|').join(' · ').trim();
    const extra = [clean(line.baseType), clean(line.variant), line.links ? `${line.links}L` : '']
      .filter(Boolean).join(' · ');
    const spark = line.sparkLine || line.sparkline || {};
    return {
      id: String(line.id),
      detailsId: String(line.id),
      name: line.name,
      sub: extra,
      icon: line.icon || '',
      value: line.chaosValue ?? 0,
      volume: line.listingCount ?? line.count ?? 0,
      lowConfidence: (line.count ?? 0) < 10,
      change7d: Array.isArray(spark.data) && spark.data.length ? round(spark.totalChange ?? 0, 2) : null,
      change24h: change24h(spark.data),
      spark: Array.isArray(spark.data) ? spark.data : [],
    };
  });
  return { primary: 'chaos', rates, items };
}

async function history(game, league, type, id, ctx) {
  if (STASH[game].includes(type)) {
    if (!/^\d{1,9}$/.test(id)) throw new Error('bad id');
    const rows = await cachedFetchJson(
      `${NINJA}/${game}/api/economy/stash/current/item/history?league=${encodeURIComponent(league)}&type=${type}&id=${id}`,
      CACHE_SECONDS, ctx);
    const today = Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth(), new Date().getUTCDate());
    const points = (Array.isArray(rows) ? rows : [])
      .filter((r) => r.value > 0)
      .map((r) => ({ t: new Date(today - r.daysAgo * 86400000).toISOString().slice(0, 10), v: round(r.value, 4) }))
      .sort((a, b) => (a.t < b.t ? -1 : 1));
    return { series: { chaos: points } };
  }
  if (!/^[a-z0-9-]{1,80}$/.test(id)) throw new Error('bad id');
  const data = await cachedFetchJson(
    `${NINJA}/${game}/api/economy/exchange/current/details?league=${encodeURIComponent(league)}&type=${type}&id=${id}`,
    CACHE_SECONDS, ctx);
  const series = {};
  for (const pair of data.pairs || []) {
    series[pair.id] = (pair.history || [])
      .filter((h) => h.rate > 0)
      .map((h) => ({ t: String(h.timestamp).slice(0, 10), v: round(h.rate, 6) }))
      .sort((a, b) => (a.t < b.t ? -1 : 1));
  }
  return { series };
}

export async function onRequestGet({ request, env, waitUntil }) {
  const ctx = { waitUntil };
  const url = new URL(request.url);
  const game = url.searchParams.get('game') === 'poe1' ? 'poe1' : 'poe2';

  if (url.searchParams.get('leagues')) {
    try {
      return json({ game, leagues: await leagues(game, ctx), types: TYPES[game],
        stashTypes: STASH[game] }, 200, 3600);
    } catch (err) {
      return json({ error: 'leagues_unavailable' }, 502);
    }
  }

  const type = url.searchParams.get('type') || 'Currency';
  const league = (url.searchParams.get('league') || '').slice(0, 80);
  if (!TYPES[game].includes(type) || !league) {
    return json({ error: 'bad_request' }, 400);
  }

  const historyId = url.searchParams.get('history');
  if (historyId) {
    try {
      return json({ game, league, type, id: historyId, ...(await history(game, league, type, historyId, ctx)) },
        200, 900);
    } catch (err) {
      return json({ error: 'history_unavailable' }, 502);
    }
  }

  let overview;
  try {
    overview = STASH[game].includes(type)
      ? await stashOverview(game, league, type, ctx)
      : await exchangeOverview(game, league, type, ctx);
  } catch (err) {
    return json({ error: 'upstream_unavailable' }, 502);
  }

  const items = overview.items.filter((it) => it.value > 0);
  const old = await snapshot30d(env, game, league, type, items);
  for (const it of items) {
    const prev = old[it.id];
    it.change30d = prev > 0 ? round((it.value / prev - 1) * 100, 2) : null;
  }

  return json({
    game, league, type,
    kind: STASH[game].includes(type) ? 'stash' : 'exchange',
    primary: overview.primary,
    rates: overview.rates,
    source: 'poe.ninja',
    fetchedAt: new Date().toISOString(),
    items,
  }, 200, 600);
}
