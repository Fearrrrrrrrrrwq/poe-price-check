"""Strona kalkulatora Instill PoE2 (/tools/poe2-instill/ i wersje jezykowe).

Cala lista notable jest renderowana w HTML: wyszukiwarka widzi kazda nazwe,
przepis i opis ("poe2 instill <nazwa>"), a skrypt tylko filtruje i obsluguje
wybor trzech emocji. Nazwy emocji, notable i ich opisy zostaja po angielsku
(dane gry) - tlumaczony jest interfejs i FAQ.
"""

import json
import pathlib

from tools.pages import INSTILL_JS_KEYS, _faq, _shell
from tools.tool_i18n import texts

DATA = pathlib.Path(__file__).resolve().parent.parent / "assets" / "instill-data.json"

PREFIXES = ("Diluted Liquid ", "Concentrated Liquid ", "Potent Liquid ", "Liquid ")
TIERS = ("Diluted", "Liquid", "Concentrated", "Potent")


def _short(name: str) -> str:
    for prefix in PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def _tier(index: int) -> int:
    return 0 if index <= 2 else 1 if index <= 6 else 2 if index <= 9 else 3


def instill_page(lang: str, *, esc, asset, site_url) -> str:
    t = texts(lang)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    emotions = data["emotions"]

    def chip(i: int, slot: int | None = None) -> str:
        label = esc(_short(emotions[i]))
        num = f'<i aria-hidden="true">{slot}</i>' if slot else ""
        return (f'<span class="emo t{_tier(i)}" title="{esc(emotions[i])}">{num}{label}</span>')

    options = "".join(f'<option value="{i}">{esc(e)}</option>' for i, e in enumerate(emotions))
    slots = "".join(
        f'<label class="slot">{esc(t["in_slot"].format(n=n))}<select data-slot="{n - 1}" '
        f'aria-label="{esc(t["in_slot_aria"].format(n=n))}">'
        f'<option value="">—</option>{options}</select></label>' for n in (1, 2, 3))
    owned = "".join(
        f'<button type="button" class="emo t{_tier(i)}" data-emo="{i}" aria-pressed="false" '
        f'title="{esc(e)}">{esc(_short(e))}</button>' for i, e in enumerate(emotions))

    rows = []
    for n in data["notables"]:
        recipe = "".join(chip(i, s + 1) for s, i in enumerate(n["recipe"]))
        stats = "".join(f"<li>{esc(line)}</li>" for line in n["stats"])
        recipe_aria = t["in_recipe_aria"].format(list=", ".join(emotions[i] for i in n["recipe"]))
        rows.append(
            f'<li class="notable" data-recipe="{",".join(map(str, n["recipe"]))}">'
            f'<div class="nt-head"><h3>{esc(n["name"])}</h3>'
            f'<span class="recipe" aria-label="{esc(recipe_aria)}">{recipe}</span></div>'
            f'<ul class="nt-stats">{stats}</ul></li>')

    faq, faq_ld = _faq(t, esc, "in", 3)
    legend = "".join(f'<span class="emo t{tier}">{name}</span>' for tier, name in enumerate(TIERS))
    total = len(data["notables"])

    body = f"""
<section class="tool-hero">
  <div class="wrap wide">
    <p class="eyebrow">Path of Exile 2 · {esc(t["free_tool"])}</p>
    <h1>{esc(t["in_h1"])}</h1>
    <p class="lead">{esc(t["in_lead"])}</p>
  </div>
</section>

<section class="tool instill" data-emotions='{esc(json.dumps([_short(e) for e in emotions]))}'>
  <div class="wrap wide">
    <div class="instill-grid">
      <div class="out-card">
        <h2>{esc(t["in_make"])}</h2>
        <div class="slots">{slots}</div>
        <div class="combo-result" aria-live="polite">
          <p class="note">{esc(t["in_pick"])}</p>
        </div>
      </div>
      <div class="out-card">
        <h2>{esc(t["in_find"])}</h2>
        <input type="search" id="nt-search" class="filter wide" placeholder="{esc(t["in_search"])}" aria-label="{esc(t["in_search_aria"])}">
        <p class="sub">{esc(t["in_owned"])}</p>
        <div class="owned" role="group" aria-label="{esc(t["in_owned_aria"])}">{owned}</div>
        <p class="note small">{esc(t["in_tiers"])} {legend}</p>
      </div>
    </div>

    <p class="nt-count note" aria-live="polite">{esc(t["in_count"].format(n=total))}</p>
    <ul class="notables">{"".join(rows)}</ul>
  </div>
</section>

<section class="band">
  <div class="wrap narrow">
    <h2 id="faq">{esc(t["faq"])}</h2>
    <div class="faq">{faq}</div>
    <p class="note">{esc(t["in_data"].format(date=data["generated"]))}</p>
  </div>
</section>
"""
    return _shell(lang=lang, esc=esc, asset=asset, site_url=site_url, path="/tools/poe2-instill/",
                  title=t["in_title"], description=t["in_desc"].format(n=total),
                  body=body, script="instill.js", json_ld=faq_ld, js_text=INSTILL_JS_KEYS)
