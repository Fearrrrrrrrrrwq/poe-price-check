# PoE Price Check

Price checking for **Path of Exile** when you play through a cloud gaming
service such as Boosteroid — where every other price-check tool stops working.

**[poepricecheck.eu](https://poepricecheck.eu)** · Windows · free · 6 languages

*(Polski: [README.pl.md](README.pl.md) — a much more detailed guide.)*

---

## Why this exists

Awakened PoE Trade and everything like it reads your clipboard. When the game
runs in a data centre and you sit in front of a browser, that clipboard is not
yours: `Ctrl+C` fills the clipboard *there*. Boosteroid synchronises the
clipboard one way only — local to cloud — so nothing comes back.

## How it gets around that

The item text is pushed out of the cloud session through a Google Doc that acts
as a bridge:

```
game (cloud)  --Ctrl+C-->        cloud clipboard
              --F7-->            Steam overlay browser, bridge doc open
              --Ctrl+A, Ctrl+V-->  Google Doc
your PC       --HTTP GET-->      doc text -> parse -> pathofexile.com/trade
```

One keypress in game, a result window on your machine a moment later.

## Features

- Mod matching on the game's own stat data (every text variant the game can
  print, mapped to trade stat IDs per mod type, local vs global) rather than
  guessing from the trade site's stat list — measured against ~600 real
  listings: 99.9% of stats matched in PoE1, 100% in PoE2
- Copies items in the advanced format (Ctrl+C in PoE1 since 3.29, Ctrl+Alt+C
  in PoE2), so implicit / crafted / fractured mods and tiers are known exactly
- Interactive mod panel — untick what does not matter, search again in place
- Tier ranges read from the item, minimum only, so better rolls still show up
- Pseudo totals: total elemental resistance, total life, attributes
- Divine/chaos conversion from live rates, median based, outliers dropped
- Item level and link sliders, hidden mods, craftable-affix detection
- Trade status set to instant buyout
- Interface in English, Polish, German, Spanish, Portuguese and Russian,
  picked automatically from the Windows locale

### Path of Exile 2 (experimental)

The setup wizard lets you pick PoE1 or PoE2 up front (also editable later in
`config.json` as `game_version`). Mod matching, pseudo totals (resistances,
life, attributes) and pricing work against the real `/api/trade2/` endpoint.
Weapon/armour filters (DPS, Armour/Evasion/Energy Shield, quality) go to
PoE2's merged `equipment_filters` group instead of PoE1's split
`weapon_filters`/`armour_filters`. Socket links are skipped — PoE2 has no
linked-socket mechanic (gems slot into skill slots, not gear), so there's no
equivalent filter to send.

Waystones (PoE2 maps) *are* supported, verified against real listings:
Item Rarity, Pack Size, Monster Rarity, Monster Effectiveness, Revives
Available and Waystone Drop Chance all price-check correctly — there's no
Item Quantity filter in PoE2 at all, so that one's simply absent rather than
mapped to something wrong.

## Install

Download the archive from **[poepricecheck.eu](https://poepricecheck.eu)**,
unpack it, run `poe-price-check.exe`. A setup wizard walks you through the
bridge document and the Steam overlay settings.

Windows will say the publisher is unknown — the build is not code-signed,
because a certificate costs several hundred euros a year and this is free.
Choose **More info → Run anyway**. The program also installs a global keyboard
hook, which is the only way to catch a shortcut while the game has focus; some
antivirus software flags that heuristically. Build it yourself if you would
rather be sure what you are running.

### macOS (experimental)

Download `poe-price-check-<version>-macos.zip` from the
[latest release](../../releases/latest) — it contains a packaged
`PoE Price Check.app`, Apple Silicon included. Move it to Applications, then
right-click → Open → Open once (it's unsigned, so Gatekeeper needs that to
let it run the first time).

macOS will prompt for **Accessibility** permission — the global hotkey and
window switching need it. If it doesn't prompt, add it manually:
*System Settings → Privacy & Security → Accessibility*.

Running from source works too:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

> **This support is new** — CI builds and smoke-tests every release on a
> real macOS runner, but it hasn't seen the range of real-world setups
> Windows has. If something breaks, please open an issue or ping Discord —
> that's how this gets solid.

## Build from source

Python 3.11+.

```
pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm poe-price-check.spec
```

The result is a single `dist/poe-price-check.exe` with no dependencies.

On macOS, use `poe-price-check-mac.spec` instead — the result is
`dist/PoE Price Check.app`.

```
python check_i18n.py   # translation coverage, no hardcoded interface strings
python smoke_test.py   # live round trip against the trade API
```

## Layout

| Path | What it is |
| --- | --- |
| `main.py` | entry point, hotkeys, wiring |
| `item_parser.py` | parses the clipboard text the game produces |
| `trade_api.py` | maps mods to stat ids, builds and runs trade queries |
| `stat_data.py`, `data/` | mod matching on the game's stat data (see Licence) |
| `bridge.py` | the cloud-session clipboard bridge |
| `overlay.py`, `status_window.py`, `setup_window.py` | Tk interface |
| `i18n.py` | translations, six languages |
| `web/` | the website, its backend and the stats panel |

The website runs on Cloudflare Pages Functions with a D1 database — see
[`web/DEPLOY.md`](web/DEPLOY.md).

Code comments are in Polish; everything user-facing is translated.

## Privacy

The app sends an anonymous usage counter: version, operating system, language,
league, number of price checks. **Never** items, prices, account details or your
bridge document id. The install identifier is random and tied to nothing. Set
`"telemetry": false` in `config.json` to switch it off.

The website counts visits without cookies and without storing IP addresses.

## About the trade API

This tool calls the same website endpoints that pathofexile.com/trade uses in
your browser. Those are not part of GGG's documented developer API, and GGG's
developer documentation states that using endpoints outside that documentation
is against section 7i of their Terms of Use. Applications for documented API
access are closed at the time of writing. The whole family of community price
checkers works this way and has done for years, but go in knowing that.

The client throttles itself from the `X-Rate-Limit-*` headers and honours
`Retry-After`. Do not spam the hotkey.

## Releases

Every release is built by GitHub Actions from a tagged commit — see
[`.github/workflows/build.yml`](.github/workflows/build.yml). Nothing built on a
personal machine is published. Each release publishes the SHA-256 of the
executable so you can check what you downloaded.

How releases are approved and what would be signed:
[SIGNING-POLICY.md](SIGNING-POLICY.md).

### Updates

On Windows, the app checks for a newer version on every launch and updates
itself quietly in the background: it downloads the release archive, checks
the SHA-256 published inside that same archive against what it downloaded,
then swaps the executable and restarts once the old process has actually
exited (a `.exe` can't be overwritten while it's still running, so a small
helper script waits for that before moving anything). Any failure at any
step — no network, a bad download, a failed check — falls back silently to
just showing a banner with a link to the release page, same as before.
Turn it off with `"auto_update": false` in `config.json` (or
`"update_check": false` to disable checking entirely). macOS and dev runs
from source always fall back to the banner — the file layout there doesn't
support this kind of in-place swap the same way.

## Licence

MIT — see [LICENSE](LICENSE).

The stat data in `data/stats_poe1.ndjson` and `data/stats_poe2.ndjson` (also
refreshed at runtime from the same source) comes from
[Awakened PoE Trade](https://github.com/SnosMe/awakened-poe-trade) and
[Exiled Exchange 2](https://github.com/Kvan7/Exiled-Exchange-2), both MIT —
their licence texts ship alongside, in `data/`. The matching algorithm in
`stat_data.py` follows theirs. Thank you.

---

This product isn't affiliated with or endorsed by Grinding Gear Games in any way.
