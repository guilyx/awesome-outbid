#!/usr/bin/env python3
"""Build the GitHub Pages site, and keep the README's board list in sync.

data/boards.yml is the single source of truth. This script renders it into
both the README (between generated markers) and the static site, so the two
can never drift.

    python3 scripts/build.py               # write README section + build _site/
    python3 scripts/build.py --check       # exit 1 if the README is out of date
    python3 scripts/build.py --site-only   # build _site/ only
    python3 scripts/build.py --readme-only # rewrite the README section only

In CI the README is regenerated automatically on main by
.github/workflows/regenerate.yml, so contributors only ever edit
data/boards.yml.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

try:
    import markdown
except ImportError:  # pragma: no cover
    markdown = None

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
DATA = ROOT / "data" / "boards.yml"
GUIDES = ROOT / "best-practices"
REPO = "https://github.com/guilyx/awesome-outbid"
BLOB = f"{REPO}/blob/main"

BEGIN = "<!-- BEGIN GENERATED BOARDS -->"
END = "<!-- END GENERATED BOARDS -->"

# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------


def slugify(heading: str) -> str:
    """GitHub's heading-to-anchor transformation, so in-repo anchors survive."""
    text = heading.strip().lower()
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*{1,2}([^*]*)\*{1,2}", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s", "-", text)


def load() -> dict:
    data = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    # YAML parses bare ISO dates into date objects; the renderers want strings.
    data["meta"]["snapshot"] = str(data["meta"]["snapshot"])
    for board in data["boards"]:
        if board.get("launched"):
            board["launched"] = str(board["launched"])

    known = {g["id"] for g in data["groups"]}
    for board in data["boards"]:
        if board["group"] not in known:
            raise SystemExit(f"boards.yml: unknown group {board['group']!r} on {board['name']}")
        if not board.get("sourced"):
            raise SystemExit(
                f"boards.yml: {board['name']} is in `boards` but not sourced. "
                "Undescribed domains belong in `named_only`."
            )
        if "nsfw" in board and not isinstance(board["nsfw"], bool):
            raise SystemExit(
                f"boards.yml: {board['name']} has a non-boolean `nsfw`. "
                "Use `nsfw: true`, or leave the field out."
            )
    return data


def tidy(text: str) -> str:
    return " ".join((text or "").split())


# ---------------------------------------------------------------------------
# README section
# ---------------------------------------------------------------------------


def render_readme_section(data: dict) -> str:
    lines = [
        BEGIN,
        "",
        "<!-- Generated from data/boards.yml by scripts/build.py. Do not edit by hand. -->",
        "",
        f"Snapshot: **{data['meta']['snapshot']}** · "
        f"**{len(data['boards'])}** boards described · "
        f"**{len(data['named_only'])}** named only.",
        "",
        tidy(data["meta"]["note"]),
        "",
    ]

    for group in data["groups"]:
        members = [b for b in data["boards"] if b["group"] == group["id"]]
        if not members:
            continue
        lines += [f"### {group['title']}", "", tidy(group["blurb"]), ""]
        lines += ["| Board | Ranks | What it does |", "| --- | --- | --- |"]
        for b in members:
            extra = ""
            if b.get("by"):
                extra += f" *by {b['by']}*"
            if b.get("launched"):
                extra += f" *({b['launched']})*"
            # The marker goes before the link, so it is visible in the cell
            # before anyone clicks -- that is the entire point of it.
            badge = "**NSFW** " if b.get("nsfw") else ""
            lines.append(
                f"| {badge}[{b['name']}]({b['url']}) | {b['ranks']} | {tidy(b['what'])}{extra} |"
            )
        lines.append("")

    lines += [
        "### Named only",
        "",
        "Domains named in launch-week roundups with no description we could",
        "source. Listed so the record is complete; we do not invent mechanics to",
        "fill the gap. Know one? A sourced description promotes it into the",
        "tables above — see [CONTRIBUTING.md](CONTRIBUTING.md).",
        "",
        ", ".join(f"`{n}`" for n in data["named_only"]),
        "",
        "> **On these links.** This is a snapshot of a genre that moved in days;",
        "> entries are community-submitted and unverified. Domains in this space go",
        "> dark quickly, and every one of them takes non-refundable money from",
        "> strangers. Listing a board here is not an endorsement, a safety check, or",
        "> advice to bid on it.",
        "",
        END,
    ]
    return "\n".join(lines)


def sync_readme(data: dict, check: bool) -> bool:
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit("README.md is missing the generated-boards markers")

    head, _, rest = text.partition(BEGIN)
    _, _, tail = rest.partition(END)
    updated = head + render_readme_section(data) + tail

    if updated == text:
        print("README board section is up to date")
        return True
    if check:
        print(
            "::error file=README.md::board section is stale. Run: "
            "pip install pyyaml markdown && python3 scripts/build.py",
            file=sys.stderr,
        )
        return False
    readme.write_text(updated, encoding="utf-8")
    print("README board section rewritten")
    return True


# ---------------------------------------------------------------------------
# site
# ---------------------------------------------------------------------------

GUIDE_TITLES = {
    "01-auction-mechanics": "Auction mechanics",
    "02-payments": "Payments and webhooks",
    "03-data-model": "Data model and concurrency",
    "04-scale-and-realtime": "Surviving the spike",
    "05-abuse-and-moderation": "Abuse and moderation",
    "06-legal-and-trust": "Legal and trust",
    "07-launch-and-distribution": "Launch and distribution",
    "08-after-the-spike": "After the spike",
}


def guide_order() -> list[str]:
    return sorted(GUIDE_TITLES)


def rewrite_links(body: str, base: str, src_dir: Path) -> str:
    """Point in-repo markdown links at the built site, everything else at GitHub.

    `src_dir` is the source file's directory, relative to the repo root, so that
    `../reference/schema.sql` resolves to the right blob URL.
    """

    def repl(match: re.Match) -> str:
        target = match.group(1)
        if target.startswith(("http://", "https://", "#", "mailto:")):
            return match.group(0)

        path, _, fragment = target.partition("#")
        anchor = f"#{fragment}" if fragment else ""
        if not path:
            return match.group(0)

        # Resolve relative to the source file, then express from the repo root.
        try:
            rel = (src_dir / path).resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return match.group(0)

        stem = Path(rel).stem
        if rel.startswith("best-practices/") and stem in GUIDE_TITLES:
            return f"]({base}/guides/{stem}/{anchor})"
        if rel == "best-practices/README.md":
            return f"]({base}/guides/{anchor})"
        if rel == "README.md":
            return f"]({base}/{anchor})"
        return f"]({BLOB}/{rel}{anchor})"

    return re.sub(r"\]\(([^)\s]+)\)", repl, body)


def md_to_html(text: str) -> str:
    if markdown is None:
        raise SystemExit("pip install markdown")
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "attr_list", "toc"],
        extension_configs={"toc": {"slugify": lambda value, sep: slugify(value)}},
    )
    return md.convert(text)


CONTRIBUTORS = ROOT / "data" / "contributors.yml"


def page(
    base: str,
    title: str,
    desc: str,
    body: str,
    *,
    scripts: str = "",
    active: str = "",
) -> str:
    """The shared chrome. `body` is everything between masthead and footer."""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="website">
<link rel="stylesheet" href="{base}/assets/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#128176;</text></svg>">
<script>
  // Applied before first paint so a chosen theme never flashes the other one.
  try {{
    var t = localStorage.getItem('theme');
    if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t;
  }} catch (e) {{}}
</script>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{body}
<footer class="footer">
  <div class="shell">
    <p>Built from <a href="{BLOB}/data/boards.yml">data/boards.yml</a> — add a board by
    editing one file. Nothing here is vetted, endorsed, or legal advice; every board
    listed takes non-refundable money from strangers.</p>
    <p><a href="{REPO}">Source</a> · <a href="{BLOB}/CONTRIBUTING.md">Contribute</a> ·
    <a href="{base}/guides/">Guides</a> · <a href="{base}/reference/">Reference</a> · CC0 1.0</p>
  </div>
</footer>
<script>
(function () {{
  var btn = document.getElementById('theme-toggle');
  if (!btn) return;
  var root = document.documentElement;
  function label() {{
    var t = root.dataset.theme;
    btn.textContent = t === 'dark' ? '\u2600' : t === 'light' ? '\u263e' : '\u25d1';
    btn.title = 'Theme: ' + (t || 'system');
  }}
  btn.addEventListener('click', function () {{
    // system -> dark -> light -> system
    var next = !root.dataset.theme ? 'dark' : root.dataset.theme === 'dark' ? 'light' : '';
    if (next) {{ root.dataset.theme = next; }} else {{ delete root.dataset.theme; }}
    try {{ next ? localStorage.setItem('theme', next) : localStorage.removeItem('theme'); }} catch (e) {{}}
    label();
  }});
  label();
}})();
</script>
{scripts}
</body>
</html>
"""


def masthead(base: str, *, title: str, tagline: str, stats: str = "", controls: str = "") -> str:
    """Wordmark, theme toggle, headline, and the guides strip.

    The guides sit *above* the list but read as a secondary strip: the list is
    what people come for, the guides are what they read once they are building.
    """
    links = "".join(
        f'<a href="{base}/guides/{s}/">{s[:2]} {html.escape(GUIDE_TITLES[s])}</a>'
        for s in guide_order()
    )
    return f"""<header class="masthead">
  <div class="shell">
    <div class="masthead__top">
      <a class="wordmark" href="{base}/">
        <span class="tile tile--gold">#1</span>
        <span class="tile tile--green">$</span>
        <span class="wordmark__text">awesome-outbid</span>
      </a>
      <div class="masthead__actions">
        <button id="theme-toggle" class="icon-button" type="button" aria-label="Toggle theme">&#9681;</button>
        <a class="button" href="{REPO}">GitHub</a>
      </div>
    </div>
    <h1>{title}</h1>
    <p class="tagline">{tagline}</p>
    {stats}
    <div class="guidebar">
      <span class="guidebar__label">Building one?</span>
      <div class="guidebar__links">
        <a class="all" href="{base}/guides/">All 8 guides &rarr;</a>
        {links}
      </div>
    </div>
    {controls}
  </div>
</header>"""


def board_card(b: dict) -> str:
    nsfw = bool(b.get("nsfw"))
    first = b["group"] == "original"

    badges = ""
    if nsfw:
        badges += '<span class="badge badge--nsfw">nsfw</span>'
    if first:
        badges += '<span class="badge badge--first">the original</span>'

    meta = []
    if b.get("launched"):
        meta.append(html.escape(str(b["launched"])))
    if b.get("by"):
        meta.append("by " + html.escape(b["by"]))
    meta_html = f'<p class="card__meta">{" · ".join(meta)}</p>' if meta else ""

    haystack = " ".join(
        [b["name"], b["ranks"], tidy(b["what"]), "nsfw adult" if nsfw else ""]
    ).lower()

    classes = "card"
    if first:
        classes += " card--original"
    elif nsfw:
        classes += " card--nsfw"

    return f"""<article class="{classes}" data-group="{b['group']}" data-text="{html.escape(haystack)}">
  <p class="card__title">{badges}<a href="{html.escape(b['url'])}" rel="nofollow ugc noopener" target="_blank">{html.escape(b['name'])}</a></p>
  <p class="card__ranks">ranks {html.escape(b['ranks'])}</p>
  <p class="card__what">{html.escape(tidy(b['what']))}</p>
  {meta_html}
</article>"""


# ---------------------------------------------------------------------------
# contributors
# ---------------------------------------------------------------------------


def contributors() -> list[dict]:
    """Derived from git log, so there is nothing to keep in sync by hand.

    No API call and no token: it reads the history that is already checked out.
    That does mean CI needs `fetch-depth: 0` -- a shallow clone only knows about
    its single commit, and would report one contributor forever.
    """
    cfg = yaml.safe_load(CONTRIBUTORS.read_text(encoding="utf-8")) if CONTRIBUTORS.exists() else {}
    logins = {k.lower(): v for k, v in (cfg.get("logins") or {}).items()}
    excluded = {e.lower() for e in (cfg.get("exclude") or [])}

    try:
        out = subprocess.run(
            ["git", "log", "--no-merges", "--format=%an%x00%ae"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    people: dict[str, dict] = {}
    for line in out.splitlines():
        name, sep, email = line.partition("\x00")
        if not sep:
            continue
        email = email.strip().lower()
        if not email or email in excluded:
            continue
        # Key on email so one person with two spellings of their name is one row.
        entry = people.setdefault(email, {"name": name.strip(), "email": email, "commits": 0})
        entry["commits"] += 1
        if len(name.strip()) > len(entry["name"]):
            entry["name"] = name.strip()

    for email, entry in people.items():
        entry["login"] = logins.get(email)

    return sorted(people.values(), key=lambda p: (-p["commits"], p["name"].lower()))


def contributors_section(people: list[dict]) -> str:
    if not people:
        return ""

    rows = []
    for p in people:
        login = p.get("login")
        initials = "".join(w[0] for w in p["name"].split()[:2]).upper() or "?"
        if login:
            # If the avatar 404s or github.com is unreachable, fall back to
            # initials rather than rendering a broken-image icon.
            avatar = (
                f'<img src="https://github.com/{html.escape(login)}.png?size=60" '
                f'alt="" width="30" height="30" loading="lazy" '
                f'onerror="this.style.display=\'none\';'
                f'this.nextElementSibling.style.display=\'grid\'">'
                f'<span class="who__fallback" style="display:none">{html.escape(initials)}</span>'
            )
            href = f'https://github.com/{html.escape(login)}'
            label = "@" + html.escape(login)
        else:
            avatar = f'<span class="who__fallback">{html.escape(initials)}</span>'
            href = REPO + "/graphs/contributors"
            label = html.escape(p["name"])
        n = p["commits"]
        rows.append(
            f'<a class="who" href="{href}" rel="noopener" target="_blank">{avatar}'
            f'<span><span class="who__name">{label}</span> '
            f'<span class="who__n">{n} commit{"s" if n != 1 else ""}</span></span></a>'
        )

    return f"""<section class="contributors">
  <h2>Who built this</h2>
  <p>Everyone who has landed a commit — the list is read straight from the git
  history at build time, so anyone who contributes shows up here automatically on
  the next deploy. Add a board and you are on it.</p>
  <div class="wall">{''.join(rows)}</div>
</section>"""


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------


def build_index(data: dict, base: str) -> str:
    """The homepage IS the list."""
    groups = [g for g in data["groups"] if any(b["group"] == g["id"] for b in data["boards"])]
    counts = {g["id"]: sum(1 for b in data["boards"] if b["group"] == g["id"]) for g in groups}

    chips = [
        f'<button class="chip" data-filter="all" aria-pressed="true">All '
        f'<span class="chip__count">{len(data["boards"])}</span></button>'
    ]
    chips += [
        f'<button class="chip" data-filter="{g["id"]}" aria-pressed="false">'
        f'{html.escape(g["title"])} <span class="chip__count">{counts[g["id"]]}</span></button>'
        for g in groups
    ]

    sections = "".join(
        f"""<section class="group" data-group="{g['id']}">
  <div class="group__head">
    <h3><span class="group__n">{counts[g['id']]}</span> {html.escape(g['title'])}</h3>
    <p>{html.escape(tidy(g['blurb']))}</p>
  </div>
  <div class="results">{''.join(board_card(b) for b in data['boards'] if b['group'] == g['id'])}</div>
</section>"""
        for g in groups
    )

    named = "".join(f"<code>{html.escape(n)}</code>" for n in data["named_only"])

    stats = f"""<div class="statline">
      <span><b>{len(data['boards'])}</b> boards described</span>
      <span><b>{len(groups)}</b> distinct mechanics</span>
      <span><b>{len(data['named_only'])}</b> named only</span>
      <span>snapshot {html.escape(data['meta']['snapshot'])}</span>
    </div>"""

    controls = f"""<div class="controls">
      <div class="search">
        <input id="q" type="search" placeholder="Search boards, mechanics, what they rank…" aria-label="Search boards">
        <button id="random" class="button button--primary" type="button">Random</button>
      </div>
      <div class="chips" id="group-chips">{''.join(chips)}</div>
    </div>"""

    body = f"""{masthead(base,
        title="Every pay-to-rank board, and what each one changed",
        tagline="outbid.lol turned a three-hour build into <strong>$139,041 in 65 hours</strong> "
                "and a few hundred clones. This is the field guide to all of them — grouped by "
                "the mechanic they actually changed, not by who shouted loudest.",
        stats=stats, controls=controls)}

<main class="shell" id="main">
  <div class="results-bar">
    <h2>The list</h2>
    <span class="count" id="count"></span>
    <button id="reset" class="button button--ghost" type="button" hidden>Reset</button>
  </div>

  <p class="note">{html.escape(tidy(data['meta']['note']))}</p>

  <p id="empty" class="empty" hidden>Nothing matches that. <button class="button button--ghost" id="clear">Clear filters</button></p>

  <div class="groups">{sections}</div>

  <section class="named">
    <h3>Named only</h3>
    <p>Domains named in launch-week roundups with no description anyone could
    source. Listed so the record is complete — we do not invent mechanics to fill
    the gap. Know one? A sourced description promotes it into the groups above.</p>
    <div class="named__codes">{named}</div>
  </section>

  <p class="warn"><strong>On these links.</strong> A snapshot of a genre that moved in
  days; entries are community-submitted and unverified. Domains here go dark quickly,
  and every one of them takes non-refundable money from strangers. Listing a board is
  not an endorsement, a safety check, or advice to bid on it.</p>

  {contributors_section(contributors())}
</main>"""

    script = """<script>
(function () {
  var q = document.getElementById('q');
  var chips = [].slice.call(document.querySelectorAll('#group-chips .chip'));
  var cards = [].slice.call(document.querySelectorAll('.card'));
  var groups = [].slice.call(document.querySelectorAll('.group'));
  var empty = document.getElementById('empty');
  var count = document.getElementById('count');
  var reset = document.getElementById('reset');
  var filter = 'all';

  function apply() {
    var term = q.value.trim().toLowerCase();
    var shown = 0;
    cards.forEach(function (card) {
      var ok = (filter === 'all' || card.dataset.group === filter) &&
               (!term || card.dataset.text.indexOf(term) !== -1);
      card.hidden = !ok;
      if (ok) shown++;
    });
    groups.forEach(function (g) { g.hidden = !g.querySelector('.card:not([hidden])'); });
    empty.hidden = shown !== 0;
    count.textContent = shown + (shown === 1 ? ' board' : ' boards');
    reset.hidden = filter === 'all' && !term;
  }

  function clear() {
    q.value = '';
    filter = 'all';
    chips.forEach(function (c) { c.setAttribute('aria-pressed', String(c.dataset.filter === 'all')); });
    apply();
  }

  q.addEventListener('input', apply);
  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      chips.forEach(function (c) { c.setAttribute('aria-pressed', 'false'); });
      chip.setAttribute('aria-pressed', 'true');
      filter = chip.dataset.filter;
      apply();
    });
  });
  reset.addEventListener('click', clear);
  document.getElementById('clear').addEventListener('click', clear);

  document.getElementById('random').addEventListener('click', function () {
    var visible = cards.filter(function (c) { return !c.hidden; });
    if (!visible.length) return;
    var pick = visible[Math.floor(Math.random() * visible.length)];
    pick.scrollIntoView({ behavior: 'smooth', block: 'center' });
    pick.style.transition = 'box-shadow .2s ease';
    pick.style.boxShadow = '0 0 0 3px var(--accent)';
    setTimeout(function () { pick.style.boxShadow = ''; }, 1200);
  });

  apply();
})();
</script>"""

    return page(
        base,
        "awesome-outbid — every pay-to-rank board, and what each changed",
        "The field guide to the outbid.lol wave: every pay-to-rank board with a sourced "
        "description, grouped by the mechanic it changed.",
        body,
        scripts=script,
        active="boards",
    )


def build_guide_pages(base: str) -> list[tuple[Path, str]]:
    order = guide_order()
    pages = []
    for i, stem in enumerate(order):
        raw = (GUIDES / f"{stem}.md").read_text(encoding="utf-8")
        body = md_to_html(rewrite_links(raw, base, GUIDES))

        prev_link = next_link = ""
        if i > 0:
            p = order[i - 1]
            prev_link = f'<a class="prev" href="{base}/guides/{p}/">&larr; {html.escape(GUIDE_TITLES[p])}</a>'
        if i < len(order) - 1:
            n = order[i + 1]
            next_link = f'<a class="next" href="{base}/guides/{n}/">{html.escape(GUIDE_TITLES[n])} &rarr;</a>'

        items = []
        for s in order:
            cls = ' class="on"' if s == stem else ""
            items.append(
                f'<li><a href="{base}/guides/{s}/"{cls}>'
                f'<span>{s[:2]}</span> {html.escape(GUIDE_TITLES[s])}</a></li>'
            )

        wrapped = f"""{masthead(base,
            title=GUIDE_TITLES[stem],
            tagline="One of eight guides on building a pay-to-rank board that survives real money.")}
<main class="shell" id="main">
  <div class="guide">
    <aside class="toc">
      <p class="toc__title">Guides</p>
      <ol>{''.join(items)}</ol>
    </aside>
    <article class="prose">
{body}
      <nav class="pager">{prev_link}{next_link}</nav>
    </article>
  </div>
</main>"""

        pages.append((
            OUT / "guides" / stem / "index.html",
            page(
                base,
                f"{GUIDE_TITLES[stem]} · awesome-outbid",
                f"Pay-to-rank board best practices: {GUIDE_TITLES[stem].lower()}.",
                wrapped,
                active="guides",
            ),
        ))
    return pages


def build_guides_index(base: str) -> str:
    raw = (GUIDES / "README.md").read_text(encoding="utf-8")
    body = md_to_html(rewrite_links(raw, base, GUIDES))
    wrapped = f"""{masthead(base,
        title="The guides",
        tagline="Eight of them, ordered so each builds on the last. The list is the moat; "
                "these are what you read once you have decided to build one.")}
<main class="shell" id="main"><article class="prose">{body}</article></main>"""
    return page(
        base,
        "Guides · awesome-outbid",
        "Eight guides for building a pay-to-rank board that survives real money.",
        wrapped,
        active="guides",
    )


REFERENCE_FILES = [
    ("schema.sql", "Three tables, an idempotent <code>credit_bid()</code>, a write-absorbing click counter, and the board queries — including the keyset seek predicate worth 769 buffers."),
    ("create-checkout.ts", "Amount validation, SSRF-aware URL normalisation, and the &ldquo;must beat #1&rdquo; check deliberately left out with the reasoning inline."),
    ("stripe-webhook.ts", "Raw-body signature verification, event routing, and which HTTP status code to return when."),
    ("pre-launch-checklist.md", "The list to run through the night before."),
]


def build_reference_page(base: str) -> str:
    items = "".join(
        f"""<article class="card">
  <p class="card__title"><a href="{BLOB}/reference/{name}">{html.escape(name)}</a></p>
  <p class="card__what">{desc}</p>
</article>"""
        for name, desc in REFERENCE_FILES
    )
    wrapped = f"""{masthead(base,
        title="Reference implementation",
        tagline="The patterns from the guides as code you can read in ten minutes. "
                "Framework-light on purpose — copy the ideas, not the imports.")}
<main class="shell" id="main">
  <p class="note">Verified rather than asserted: the schema was applied to Postgres 16
  and its behaviour tested (replayed events credit once, two events describing the same
  PaymentIntent credit once, money on a removed listing does not put it back on the
  board, the rank query agrees with board position for every row). Both TypeScript files
  typecheck under <code>strict</code> against the Stripe SDK.</p>
  <div class="cards-plain">{items}</div>
</main>"""
    return page(
        base,
        "Reference · awesome-outbid",
        "Annotated Postgres schema and Stripe integration for a pay-to-rank board.",
        wrapped,
        active="reference",
    )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def redirect_page(base: str) -> str:
    """/boards/ -> / , for links made before the list moved to the homepage."""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>The list moved · awesome-outbid</title>
<link rel="canonical" href="{base}/">
<meta http-equiv="refresh" content="0; url={base}/">
</head>
<body>
<p>The board list is the homepage now. <a href="{base}/">Continue &rarr;</a></p>
</body>
</html>
"""


def build_site(data: dict, base: str) -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    write(OUT / "index.html", build_index(data, base))
    # The list used to live at /boards/. It is the homepage now, but the old URL
    # is in the README, in merged PR bodies, and possibly in someone's bookmarks.
    write(OUT / "boards" / "index.html", redirect_page(base))
    write(OUT / "guides" / "index.html", build_guides_index(base))
    write(OUT / "reference" / "index.html", build_reference_page(base))
    for path, content in build_guide_pages(base):
        write(path, content)
    write(OUT / "assets" / "style.css", (ROOT / "site" / "assets" / "style.css").read_text(encoding="utf-8"))
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    built = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob("*.html"))
    print(f"built {len(built)} pages into {OUT.relative_to(ROOT)}/")
    for p in built:
        print(f"  {p}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit 1 if the README board section is stale",
    )
    ap.add_argument("--site-only", action="store_true", help="build _site/, leave the README alone")
    ap.add_argument(
        "--readme-only",
        action="store_true",
        help="rewrite the README board section, skip the site build",
    )
    ap.add_argument("--base", default="/awesome-outbid", help="site base path")
    args = ap.parse_args()

    if args.site_only and args.readme_only:
        ap.error("--site-only and --readme-only are mutually exclusive")

    data = load()

    if not args.site_only:
        if not sync_readme(data, args.check):
            return 1
    if args.check or args.readme_only:
        return 0

    build_site(data, args.base.rstrip("/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
