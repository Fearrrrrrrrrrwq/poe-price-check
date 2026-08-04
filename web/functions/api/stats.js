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
// Drugi prog, na LICZBE INSTALACJI. Sam prog na liczbe prob nie wystarcza:
// jedna osoba z gorszym kwadransem potrafila wygenerowac 39 prob i zapalic
// czerwony baner "wysoki odsetek bledow" na cala strone. Awaria warta alarmu
// dotyka wiecej niz jednej instalacji.
const MIN_INSTALLS = 3;

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

  const [totals, session_, daily, firstSeen, returning, windows,
         activeInstalls, errorKinds, ...splits] =
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

      // Ile ROZNYCH instalacji zlozylo sie na probki z okna alarmowego.
      // Odsetek liczony z jednej instalacji nie mowi nic o stanie aplikacji.
      env.DB.prepare(
        `SELECT COUNT(DISTINCT install) AS installs FROM pings
          WHERE at >= ?1 AND (checks > 0 OR failures > 0)`
      ).bind(weekAgo),

      // Rodzaje bledow z tego samego okna co odsetek - inaczej alert i lista
      // przyczyn opisywalyby dwa rozne okresy.
      env.DB.prepare(
        `SELECT kind AS name,
                SUM(count) AS count,
                COUNT(DISTINCT install) AS installs
           FROM errors WHERE at >= ?1
          GROUP BY kind ORDER BY count DESC LIMIT 12`
      ).bind(weekAgo),

      // Kazda instalacja liczy sie RAZ, wedlug ostatnio zgloszonej wartosci.
      //
      // Wczesniej bylo COUNT(DISTINCT install) GROUP BY kolumna, wiec kto
      // zaktualizowal program, siedzial jednocześnie w kilku wersjach naraz -
      // udzialy sumowaly sie do wiecej niz 100% wszystkich instalacji, a
      // "1.0.7 - 30.8%" nie znaczylo "30.8% uzytkownikow ma 1.0.7".
      //
      // Dotyczy tak samo jezyka, ligi i systemu: kazde z nich potrafi sie
      // miedzy sygnalami zmienic.
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
  // null, a NIE zero, gdy poprzedni tydzien jest pusty. Zero znaczy "bylo
  // bezbledne", a brak danych znaczy "nie ma z czym porownac" - podstawienie
  // zera pokazywalo skok "+17.9 pkt" wzgledem okresu, ktory nie istnial.
  const ratePrev = samplePrev ? (win.f_prev * 100) / samplePrev : null;

  const installsNow = activeInstalls.results[0].installs;
  const solid = sampleNow >= MIN_SAMPLE && installsNow >= MIN_INSTALLS;

  let level = 'ok';
  if (solid && rate >= FAILURE_ALERT) level = 'alert';
  else if (solid && rate >= FAILURE_ALERT / 2) level = 'warn';

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
      rate_previous: ratePrev === null ? null : round(ratePrev),
      sample: sampleNow,
      installs: installsNow,
      // Najczestszy rodzaj bledu wprost z danych. Panel wypisywal tu wczesniej
      // zdanie zaszyte na sztywno ("zmiana w API handlu"), ktorego nie mial
      // z czego wyprowadzic - baza trzymala sam licznik, bez rodzaju.
      top: errorKinds.results[0]
        ? { name: errorKinds.results[0].name, count: errorKinds.results[0].count }
        : null,
    },

    errors: share(errorKinds.results).map((row, index) => ({
      ...row,
      installs: errorKinds.results[index].installs,
    })),

    daily: series,
  };

  BREAKDOWNS.forEach(([name], index) => {
    payload[name] = share(splits[index].results);
  });

  return json(payload);
}
