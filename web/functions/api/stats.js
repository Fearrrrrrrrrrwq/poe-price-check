/**
 * Statystyki dla panelu.  GET /api/stats?days=30
 *
 * Wymaga zalogowania. Liczenie idzie w calosci do SQL-a - w arkuszu trzeba
 * bylo sciagac wszystkie wiersze i sumowac je w petli, tutaj baza oddaje
 * gotowe liczby niezaleznie od tego, ile sygnalow sie uzbieralo.
 *
 * Dni tniemy wedlug UTC. Strefa uzytkownika przesuwalaby granice doby
 * i te same dane wygladalyby inaczej w zaleznosci od tego, kto patrzy.
 */

import { currentSession, json } from '../../lib/auth.js';

const DAY = 86400000;
const FAILURE_ALERT = 15;   // procent nieudanych wycen zapalajacy ostrzezenie
const MIN_SAMPLE = 20;      // ponizej tylu prob odsetek nic nie znaczy

const BREAKDOWNS = [
  ['versions', 'version'],
  ['languages', 'language'],
  ['leagues', 'league'],
  ['systems', 'os'],
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

function round(value, places = 1) {
  const factor = 10 ** places;
  return Math.round(value * factor) / factor;
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
  const dayAgo = now - DAY;
  const weekAgo = now - 7 * DAY;
  const monthAgo = now - 30 * DAY;
  const twoWeeksAgo = now - 14 * DAY;
  // Poczatek najstarszej doby w zakresie, a nie "teraz minus N dni" - inaczej
  // pierwszy slupek pokazywalby urwany kawalek dnia.
  const from = Date.parse(isoDay(now - (days - 1) * DAY) + 'T00:00:00Z');

  const [totals, session_, daily, firstSeen, returning, windows, ...splits] =
    await env.DB.batch([
      env.DB.prepare(
        `SELECT COUNT(DISTINCT install) AS total,
                COUNT(DISTINCT CASE WHEN at >= ?1 THEN install END) AS today,
                COUNT(DISTINCT CASE WHEN at >= ?2 THEN install END) AS week,
                COUNT(DISTINCT CASE WHEN at >= ?3 THEN install END) AS month,
                COALESCE(SUM(checks), 0)   AS checks,
                COALESCE(SUM(failures), 0) AS failures,
                COUNT(*) AS pings
           FROM pings`
      ).bind(dayAgo, weekAgo, monthAgo),

      env.DB.prepare(
        'SELECT COALESCE(AVG(uptime_min), 0) AS average FROM pings WHERE uptime_min > 0'
      ),

      env.DB.prepare(
        `SELECT date(at / 1000, 'unixepoch') AS date,
                COUNT(DISTINCT install)      AS users,
                COALESCE(SUM(checks), 0)     AS checks,
                COALESCE(SUM(failures), 0)   AS failures
           FROM pings WHERE at >= ?1 GROUP BY date`
      ).bind(from),

      env.DB.prepare(
        `SELECT date, COUNT(*) AS fresh FROM (
           SELECT install, date(MIN(at) / 1000, 'unixepoch') AS date
             FROM pings GROUP BY install
         ) GROUP BY date`
      ),

      env.DB.prepare(
        `SELECT COUNT(*) AS installs FROM (
           SELECT install FROM pings GROUP BY install
            HAVING COUNT(DISTINCT date(at / 1000, 'unixepoch')) >= 2
         )`
      ),

      env.DB.prepare(
        `SELECT
           COALESCE(SUM(CASE WHEN at >= ?1 THEN checks   END), 0) AS c_now,
           COALESCE(SUM(CASE WHEN at >= ?1 THEN failures END), 0) AS f_now,
           COALESCE(SUM(CASE WHEN at >= ?2 AND at < ?1 THEN checks   END), 0) AS c_prev,
           COALESCE(SUM(CASE WHEN at >= ?2 AND at < ?1 THEN failures END), 0) AS f_prev
         FROM pings`
      ).bind(weekAgo, twoWeeksAgo),

      ...BREAKDOWNS.map(([, column]) => env.DB.prepare(
        `SELECT ${column} AS name, COUNT(DISTINCT install) AS count
           FROM pings GROUP BY ${column} ORDER BY count DESC LIMIT 8`
      )),
    ]);

  const sums = totals.results[0];
  const win = windows.results[0];

  const byDay = new Map(daily.results.map((row) => [row.date, row]));
  const byFirst = new Map(firstSeen.results.map((row) => [row.date, row.fresh]));

  // Pelny szereg dni, takze pustych - inaczej wykres klamie o ciaglosci.
  const series = [];
  for (let offset = days - 1; offset >= 0; offset--) {
    const date = isoDay(now - offset * DAY);
    const row = byDay.get(date);
    series.push({
      date,
      users: row ? row.users : 0,
      fresh: byFirst.get(date) || 0,
      checks: row ? row.checks : 0,
      failures: row ? row.failures : 0,
    });
  }

  const sampleNow = win.c_now + win.f_now;
  const samplePrev = win.c_prev + win.f_prev;
  const rate = sampleNow ? (win.f_now * 100) / sampleNow : 0;
  const ratePrev = samplePrev ? (win.f_prev * 100) / samplePrev : 0;

  let level = 'ok';
  if (sampleNow >= MIN_SAMPLE && rate >= FAILURE_ALERT) level = 'alert';
  else if (sampleNow >= MIN_SAMPLE && rate >= FAILURE_ALERT / 2) level = 'warn';

  const installs = sums.total;
  const newToday = byFirst.get(isoDay(now)) || 0;

  const payload = {
    admin: session.login,
    updated: new Date(now).toISOString().slice(0, 16).replace('T', ' '),
    timezone: 'UTC',
    range_days: days,
    truncated: false,
    rows_read: sums.pings,

    users_today: sums.today,
    users_week: sums.week,
    users_month: sums.month,
    users_total: installs,
    users_new_today: newToday,
    users_returning: returning.results[0].installs,
    retention: installs
      ? round((returning.results[0].installs * 100) / installs) : 0,

    checks: sums.checks,
    failures: sums.failures,
    checks_per_user: installs ? round(sums.checks / installs) : 0,
    pings: sums.pings,
    avg_session: Math.round(session_.results[0].average),

    health: {
      level,
      rate: round(rate),
      rate_previous: round(ratePrev),
      sample: sampleNow,
    },

    daily: series,
  };

  BREAKDOWNS.forEach(([name], index) => {
    payload[name] = share(splits[index].results);
  });

  return json(payload);
}
