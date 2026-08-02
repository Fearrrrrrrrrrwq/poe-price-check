/**
 * Statystyki ruchu na stronie.  GET /api/traffic?days=30
 *
 * Wymaga zalogowania, tak samo jak /api/stats. Liczenie idzie w calosci
 * do SQL-a, dni tniemy wedlug UTC - tak samo jak tam, zeby oba zestawy
 * liczb dalo sie zestawiac bez przeliczania.
 */

import { currentSession, json } from '../../lib/auth.js';

const DAY = 86400000;

const BREAKDOWNS = [
  ['pages', 'path'],
  ['languages', 'lang'],
  ['referrers', 'ref'],
  ['countries', 'country'],
  ['devices', 'device'],
];

function share(rows, labelEmpty) {
  const total = rows.reduce((sum, row) => sum + row.count, 0);
  return rows.map((row) => ({
    name: row.name || labelEmpty,
    count: row.count,
    share: total ? Math.round((row.count * 1000) / total) / 10 : 0,
  }));
}

function isoDay(ms) {
  return new Date(ms).toISOString().slice(0, 10);
}

export async function onRequestGet({ request, env }) {
  const session = await currentSession(request, env);
  if (!session) return json({ error: 'unauthorised' }, 401);

  const url = new URL(request.url);
  const days = Math.min(Math.max(Number(url.searchParams.get('days')) || 14, 1), 90);

  const now = Date.now();
  const from = Date.parse(isoDay(now - (days - 1) * DAY) + 'T00:00:00Z');

  const [totals, daily, ...splits] = await env.DB.batch([
    env.DB.prepare(
      `SELECT COUNT(*) AS all_views,
              COUNT(DISTINCT visitor) AS all_visitors,
              COUNT(CASE WHEN at >= ?1 THEN 1 END) AS views_today,
              COUNT(DISTINCT CASE WHEN at >= ?1 THEN visitor END) AS visitors_today,
              COUNT(CASE WHEN at >= ?2 THEN 1 END) AS views_week,
              COUNT(DISTINCT CASE WHEN at >= ?2 THEN visitor END) AS visitors_week,
              COUNT(CASE WHEN at >= ?3 THEN 1 END) AS views_month,
              COUNT(DISTINCT CASE WHEN at >= ?3 THEN visitor END) AS visitors_month
         FROM visits`
    ).bind(now - DAY, now - 7 * DAY, now - 30 * DAY),

    env.DB.prepare(
      `SELECT date(at / 1000, 'unixepoch') AS date,
              COUNT(*)                     AS views,
              COUNT(DISTINCT visitor)      AS visitors
         FROM visits WHERE at >= ?1 GROUP BY date`
    ).bind(from),

    // Rozklady liczymy w wybranym zakresie, a nie od poczatku swiata - inaczej
    // stara popularna podstrona zaslanialaby to, co dzieje sie teraz.
    ...BREAKDOWNS.map(([, column]) => env.DB.prepare(
      `SELECT ${column} AS name, COUNT(*) AS count
         FROM visits WHERE at >= ?1 GROUP BY ${column}
        ORDER BY count DESC LIMIT 8`
    ).bind(from)),
  ]);

  const sums = totals.results[0];
  const byDay = new Map(daily.results.map((row) => [row.date, row]));

  const series = [];
  for (let offset = days - 1; offset >= 0; offset--) {
    const date = isoDay(now - offset * DAY);
    const row = byDay.get(date);
    series.push({
      date,
      views: row ? row.views : 0,
      visitors: row ? row.visitors : 0,
    });
  }

  const payload = {
    admin: session.login,
    updated: new Date(now).toISOString().slice(0, 16).replace('T', ' '),
    timezone: 'UTC',
    range_days: days,

    views_today: sums.views_today,
    visitors_today: sums.visitors_today,
    views_week: sums.views_week,
    visitors_week: sums.visitors_week,
    views_month: sums.views_month,
    visitors_month: sums.visitors_month,
    views_total: sums.all_views,

    // Ile stron oglada jedna osoba - ponizej 1.2 znaczy, ze wchodza i wychodza.
    per_visitor: sums.visitors_month
      ? Math.round((sums.views_month / sums.visitors_month) * 10) / 10 : 0,

    daily: series,
  };

  BREAKDOWNS.forEach(([name], index) => {
    payload[name] = share(
      splits[index].results,
      name === 'referrers' ? 'wejście bezpośrednie' : '(brak)');
  });

  return json(payload);
}
