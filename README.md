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

- Interactive mod panel — untick what does not matter, search again in place
- Tier ranges read from the item, minimum only, so better rolls still show up
- Pseudo totals: total elemental resistance, total life, attributes
- Divine/chaos conversion from live rates, median based, outliers dropped
- Item level and link sliders, hidden mods, craftable-affix detection
- Trade status set to instant buyout
- Interface in English, Polish, German, Spanish, Portuguese and Russian,
  picked automatically from the Windows locale

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

There is no `.app` build yet — run from source:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

macOS will prompt for **Accessibility** permission for Terminal/Python — the
global hotkey and window switching need it. If it doesn't prompt, add it
manually: *System Settings → Privacy & Security → Accessibility*.

> **This support is new and has not been tested on real macOS hardware** —
> the platform-specific code (`winutil_macos.py`) was written against the
> AppleScript/System Events documentation, not verified step by step on a
> Mac. If you're on macOS and something breaks, please open an issue or ping
> Discord — that's how this gets solid. A packaged `.app` (the macOS
> equivalent of `build.bat`'s `.exe`) doesn't exist yet.

## Build from source

Python 3.11+.

```
pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm poe-price-check.spec
```

The result is a single `dist/poe-price-check.exe` with no dependencies.

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

## Licence

MIT — see [LICENSE](LICENSE).

---

This product isn't affiliated with or endorsed by Grinding Gear Games in any way.
