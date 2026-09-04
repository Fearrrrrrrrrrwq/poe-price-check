/**
 * Publiczne, zagregowane statystyki uzycia. GET /api/public-stats
 *
 * Bez logowania - w odroznieniu od /api/stats.js (panel admina) ten endpoint
 * NIE zwraca nic, czego nie byloby juz obiecane w polityce prywatnosci
 * (telemetry.py: "wersja, liga, liczba wycen"): zadnych rodzajow bledow,
 * zadnego odsetka awarii, zadnej pojedynczej instalacji. Same sumy i
 * rozklady (system, jezyk, liga, wersja, transport) z tabeli pings, tej
 * samej, ktora juz zasila panel.
 */

import { json } from '../../lib/auth.js';

const DAY = 86400000;

const BREAKDOWNS = [
  ['systems', 'os'],
  ['leagues', 'league'],
  ['versions', 'version'],
  ['languages', 'language'],
  ['transports', 'transport'],
];

function share(rows) {
  const total = rows.reduce((sum, row) => sum + row.count, 0);
  return rows.map((row) => ({
    name: row.name || '(brak)',
    count: row.count,
    share: total ? Math.round((row.count * 1000) / total) / 10 : 0,
  }));
}

export async function onRequestGet({ env }) {
  const now = Date.now();
  const weekAgo = now - 7 * DAY;
  const monthAgo = now - 30 * DAY;

  const [totals, ...splits] = await env.DB.batch([
    env.DB.prepare(
      `SELECT COUNT(DISTINCT install) AS total,
              COUNT(DISTINCT CASE WHEN at >= ?1 THEN install END) AS week,
              COUNT(DISTINCT CASE WHEN at >= ?2 THEN install END) AS month,
              COALESCE(SUM(checks), 0) AS checks,
              COALESCE(SUM(CASE WHEN at >= ?1 THEN checks END), 0) AS checks_week,
              COALESCE(AVG(CASE WHEN uptime_min > 0 THEN uptime_min END), 0) AS avg_session
         FROM pings`
    ).bind(weekAgo, monthAgo),

    // Kazda instalacja liczy sie RAZ, wedlug ostatnio zgloszonej wartosci -
    // patrz komentarz przy tym samym wzorcu w api/stats.js.
    ...BREAKDOWNS.map(([, column]) => env.DB.prepare(
      `SELECT name, COUNT(*) AS count FROM (
         SELECT ${column} AS name,
                ROW_NUMBER() OVER (
                  PARTITION BY install ORDER BY at DESC, id DESC) AS rn
           FROM pings
       ) WHERE rn = 1
       GROUP BY name ORDER BY count DESC LIMIT 8`
    )),
  ]);

  const sums = totals.results[0];
  const payload = {
    updated: new Date(now).toISOString(),
    installs_total: sums.total,
    installs_week: sums.week,
    installs_month: sums.month,
    checks_total: sums.checks,
    checks_week: sums.checks_week,
    avg_session_min: Math.round(sums.avg_session),
  };

  BREAKDOWNS.forEach(([name], index) => {
    payload[name] = share(splits[index].results);
  });

  // Bez wlasnego Cache-Control - globalna regula /api/* (_headers, patrz
  // web/build.py:headers()) i tak wymusza no-store na kazdym endpoincie API,
  // wiec drugi naglowek tutaj tylko myliby co do faktycznego zachowania.
  return json(payload);
}
