"""Strona kalkulatora Instill PoE2 (/tools/poe2-instill/).

Cala lista notable jest renderowana w HTML: wyszukiwarka widzi kazda nazwe,
przepis i opis ("poe2 instill <nazwa>"), a skrypt tylko filtruje i obsluguje
wybor trzech emocji.
"""

import json
import pathlib

from tools.pages import _faq_ld, _shell

DATA = pathlib.Path(__file__).resolve().parent.parent / "assets" / "instill-data.json"

PREFIXES = ("Diluted Liquid ", "Concentrated Liquid ", "Potent Liquid ", "Liquid ")
TIERS = ("Diluted", "Liquid", "Concentrated", "Potent")

FAQ = (
    ("How does instilling an amulet work in Path of Exile 2?",
     "Three Distilled Emotions are placed on an amulet and it gains an enchantment "
     "that allocates one notable passive skill, even if it is not connected on your tree. "
     "This calculator lists every notable with the emotions it needs."),
    ("Does the order of the emotions matter?",
     "Yes. The same three emotions in a different order give a different notable — "
     "for example Isolation, Ire, Disgust allocates Void, while Ire, Disgust, Isolation "
     "allocates Revenge. Recipes here are shown in slot order."),
    ("Where does this data come from?",
     "Recipes come from the game's own data (via Exiled Exchange 2) and notable "
     "descriptions from the game's passive tree and stat descriptions (via RePoE), "
     "regenerated with each site update."),
)


def _short(name: str) -> str:
    for prefix in PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def _tier(index: int) -> int:
    return 0 if index <= 2 else 1 if index <= 6 else 2 if index <= 9 else 3


def instill_page(*, esc, asset, site_url) -> str:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    emotions = data["emotions"]

    def chip(i: int, slot: int | None = None) -> str:
        label = esc(_short(emotions[i]))
        num = f'<i aria-hidden="true">{slot}</i>' if slot else ""
        return (f'<span class="emo t{_tier(i)}" title="{esc(emotions[i])}">{num}{label}</span>')

    options = "".join(f'<option value="{i}">{esc(e)}</option>' for i, e in enumerate(emotions))
    slots = "".join(
        f'<label class="slot">Slot {n}<select data-slot="{n - 1}" aria-label="Emotion in slot {n}">'
        f'<option value="">—</option>{options}</select></label>' for n in (1, 2, 3))
    owned = "".join(
        f'<button type="button" class="emo t{_tier(i)}" data-emo="{i}" aria-pressed="false" '
        f'title="{esc(e)}">{esc(_short(e))}</button>' for i, e in enumerate(emotions))

    rows = []
    for n in data["notables"]:
        recipe = "".join(chip(i, s + 1) for s, i in enumerate(n["recipe"]))
        stats = "".join(f"<li>{esc(line)}</li>" for line in n["stats"])
        rows.append(
            f'<li class="notable" data-recipe="{",".join(map(str, n["recipe"]))}">'
            f'<div class="nt-head"><h3>{esc(n["name"])}</h3>'
            f'<span class="recipe" aria-label="Recipe: '
            f'{esc(", ".join(emotions[i] for i in n["recipe"]))}">{recipe}</span></div>'
            f'<ul class="nt-stats">{stats}</ul></li>')

    faq = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in FAQ)
    legend = "".join(f'<span class="emo t{t}">{name}</span>' for t, name in enumerate(TIERS))

    body = f"""
<section class="tool-hero">
  <div class="wrap wide">
    <p class="eyebrow">Path of Exile 2 · free tool</p>
    <h1>PoE2 Instilling Calculator</h1>
    <p class="lead">Which three Distilled Emotions allocate which notable on your amulet —
    and which notable your emotions make. Order matters: the same emotions in a different
    order give a different notable.</p>
  </div>
</section>

<section class="tool instill" data-emotions='{esc(json.dumps([_short(e) for e in emotions]))}'>
  <div class="wrap wide">
    <div class="instill-grid">
      <div class="out-card">
        <h2>What do my emotions make?</h2>
        <div class="slots">{slots}</div>
        <div class="combo-result" aria-live="polite">
          <p class="note">Pick an emotion for each slot.</p>
        </div>
      </div>
      <div class="out-card">
        <h2>Find a notable</h2>
        <input type="search" id="nt-search" class="filter wide" placeholder="Search by name or effect — e.g. chaos, charm, freeze" aria-label="Search notables">
        <p class="sub">Only recipes I can make with</p>
        <div class="owned" role="group" aria-label="Emotions you have">{owned}</div>
        <p class="note small">Emotion tiers: {legend}</p>
      </div>
    </div>

    <p class="nt-count note" aria-live="polite">{len(data["notables"])} notables</p>
    <ul class="notables">{"".join(rows)}</ul>
  </div>
</section>

<section class="band">
  <div class="wrap narrow">
    <h2 id="faq">FAQ</h2>
    <div class="faq">{faq}</div>
    <p class="note">Data generated {esc(data["generated"])}.</p>
  </div>
</section>
"""
    return _shell(esc=esc, asset=asset, site_url=site_url, path="/tools/poe2-instill/",
                  title="PoE2 Instilling Calculator — Distilled Emotions Anoint List",
                  description=(f"All {len(data['notables'])} Path of Exile 2 instill recipes: which "
                               "Distilled Emotions in which order allocate each notable on your "
                               "amulet, searchable by name and effect."),
                  body=body, script="instill.js", json_ld=_faq_ld(FAQ))
