-- Baza panelu i telemetrii (Cloudflare D1 = SQLite).
--
-- Zakladanie:
--   wrangler d1 create poe-price-check
--   wrangler d1 execute poe-price-check --remote --file=schema.sql
--
-- Czas trzymamy jako liczbe milisekund (unix ms) w INTEGER. Teksty dat w SQLite
-- kusza czytelnoscia, ale porownania i indeksy na liczbach sa szybsze
-- i nie ma zabawy ze strefami.

CREATE TABLE IF NOT EXISTS pings (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  at         INTEGER NOT NULL,
  install    TEXT    NOT NULL,
  version    TEXT    NOT NULL DEFAULT '',
  os         TEXT    NOT NULL DEFAULT '',
  language   TEXT    NOT NULL DEFAULT '',
  league     TEXT    NOT NULL DEFAULT '',
  transport  TEXT    NOT NULL DEFAULT '',
  checks     INTEGER NOT NULL DEFAULT 0,
  failures   INTEGER NOT NULL DEFAULT 0,
  uptime_min INTEGER NOT NULL DEFAULT 0
);

-- Kazde pytanie panelu filtruje po czasie, a czesc grupuje po instalacji.
CREATE INDEX IF NOT EXISTS pings_at      ON pings (at);
CREATE INDEX IF NOT EXISTS pings_install ON pings (install, at);

-- Rodzaje bledow. Osobna tabela, a nie kolumny w pings: rodzajow przybywa
-- razem z kodem, a dokladanie kolumny przy kazdym nowym bylo by absurdem.
--
-- kind to zamknieta lista etykiet z kodu aplikacji ("trade_400", "most_dostep",
-- "tekst_przedmiotu"). Nie ma w niej nic o przedmiocie ani o uzytkowniku -
-- inaczej telemetria przestala by byc anonimowa.
CREATE TABLE IF NOT EXISTS errors (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  at      INTEGER NOT NULL,
  install TEXT    NOT NULL,
  version TEXT    NOT NULL DEFAULT '',
  kind    TEXT    NOT NULL,
  count   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS errors_at   ON errors (at);
CREATE INDEX IF NOT EXISTS errors_kind ON errors (kind, at);

CREATE TABLE IF NOT EXISTS admins (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  login   TEXT    NOT NULL UNIQUE,
  hash    TEXT    NOT NULL,
  created INTEGER NOT NULL
);

-- W kolumnie token siedzi SKROT tokenu, nie sam token. Kopia bazy nie daje
-- wiec nikomu gotowej sesji do przejecia.
CREATE TABLE IF NOT EXISTS sessions (
  token   TEXT    PRIMARY KEY,
  admin   INTEGER NOT NULL REFERENCES admins (id) ON DELETE CASCADE,
  created INTEGER NOT NULL,
  expires INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS sessions_expires ON sessions (expires);

-- Odwiedziny strony.
--
-- Bez ciasteczek i bez adresow IP. Kolumna visitor to skrot z adresu, przegladarki,
-- daty i tajnej soli - ten sam czlowiek nastepnego dnia dostaje inny skrot, wiec
-- nie da sie go sledzic w czasie. Wystarcza to do policzenia unikalnych wejsc
-- w obrebie doby i nic ponad to.
CREATE TABLE IF NOT EXISTS visits (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  at      INTEGER NOT NULL,
  path    TEXT    NOT NULL DEFAULT '',
  lang    TEXT    NOT NULL DEFAULT '',
  ref     TEXT    NOT NULL DEFAULT '',
  country TEXT    NOT NULL DEFAULT '',
  device  TEXT    NOT NULL DEFAULT '',
  visitor TEXT    NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS visits_at ON visits (at);

-- Nieudane logowania - bez tego haslo mozna po prostu zgadywac w petli.
CREATE TABLE IF NOT EXISTS login_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ip TEXT    NOT NULL,
  at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS login_attempts_ip ON login_attempts (ip, at);
