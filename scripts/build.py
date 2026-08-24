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


def page(base: str, title: str, desc: str, body: str, *, active: str = "", wide: bool = False) -> str:
    def nav(href: str, label: str, key: str) -> str:
        cls = ' class="on"' if key == active else ""
        return f'<a href="{href}"{cls}>{label}</a>'

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
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#127942;</text></svg>">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <a class="brand" href="{base}/"><span class="mark">$</span> awesome-outbid</a>
  <nav>
    {nav(f"{base}/guides/", "Guides", "guides")}
    {nav(f"{base}/boards/", "Boards", "boards")}
    {nav(f"{base}/reference/", "Reference", "reference")}
    <a href="{REPO}">GitHub</a>
  </nav>
</header>
<main id="main"{' class="wide"' if wide else ''}>
{body}
</main>
<footer>
  <p>Built from <a href="{BLOB}/data/boards.yml">data/boards.yml</a>. Nothing here is
  vetted, endorsed, or legal advice — every board listed takes non-refundable money
  from strangers.</p>
  <p><a href="{REPO}">Source</a> · <a href="{BLOB}/CONTRIBUTING.md">Contribute</a> ·
  CC0 1.0</p>
</footer>
</body>
</html>
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def board_card(b: dict) -> str:
    meta = []
    if b.get("launched"):
        meta.append(html.escape(b["launched"]))
    if b.get("by"):
        meta.append("by " + html.escape(b["by"]))
    meta_html = f'<p class="meta">{" · ".join(meta)}</p>' if meta else ""
    nsfw = bool(b.get("nsfw"))
    badge = '<span class="nsfw" title="Adult content">NSFW</span> ' if nsfw else ""
    # "nsfw" joins the haystack so the filter box can find (or exclude) them.
    haystack = (b["name"] + " " + b["ranks"] + " " + tidy(b["what"]) + (" nsfw adult" if nsfw else "")).lower()
    return f"""<article class="board{' is-nsfw' if nsfw else ''}" data-group="{b['group']}" data-name="{html.escape(b['name'])}" data-text="{html.escape(haystack)}">
  <h3>{badge}<a href="{html.escape(b['url'])}" rel="nofollow ugc noopener" target="_blank">{html.escape(b['name'])}</a></h3>
  <p class="ranks">ranks {html.escape(b['ranks'])}</p>
  <p class="what">{html.escape(tidy(b['what']))}</p>
  {meta_html}
</article>"""


def build_boards_page(data: dict, base: str) -> str:
    groups = [g for g in data["groups"] if any(b["group"] == g["id"] for b in data["boards"])]

    chips = ['<button class="chip on" data-filter="all">All <span>%d</span></button>' % len(data["boards"])]
    for g in groups:
        n = sum(1 for b in data["boards"] if b["group"] == g["id"])
        chips.append(
            f'<button class="chip" data-filter="{g["id"]}">{html.escape(g["title"])} <span>{n}</span></button>'
        )

    sections = []
    for g in groups:
        members = [b for b in data["boards"] if b["group"] == g["id"]]
        cards = "\n".join(board_card(b) for b in members)
        sections.append(
            f"""<section class="group" data-group="{g['id']}">
  <h2 id="{g['id']}">{html.escape(g['title'])}</h2>
  <p class="blurb">{html.escape(tidy(g['blurb']))}</p>
  <div class="grid">
{cards}
  </div>
</section>"""
        )

    named = " ".join(f"<code>{html.escape(n)}</code>" for n in data["named_only"])

    body = f"""<div class="hero small">
  <h1>The board directory</h1>
  <p class="lede">Every pay-to-rank board we could find a sourced description for,
  grouped by what it actually changed — not alphabetically, and not by bid.</p>
  <p class="meta">Snapshot {html.escape(data['meta']['snapshot'])} ·
  {len(data['boards'])} described · {len(data['named_only'])} named only</p>
</div>

<p class="note">{html.escape(tidy(data['meta']['note']))}</p>

<div class="controls">
  <input id="q" type="search" placeholder="Search boards, mechanics, what they rank…" aria-label="Search boards">
  <div class="chips">{''.join(chips)}</div>
</div>

<p id="empty" class="empty" hidden>No board matches that.</p>

{''.join(sections)}

<section class="group named">
  <h2 id="named-only">Named only</h2>
  <p class="blurb">Domains named in launch-week roundups with no description we
  could source. Listed so the record is complete — we do not invent mechanics to
  fill the gap. Know one? A sourced description promotes it into the groups
  above.</p>
  <p class="codes">{named}</p>
</section>

<p class="warn"><strong>On these links.</strong> This is a snapshot of a genre that
moved in days; entries are community-submitted and unverified. Domains here go dark
quickly, and every one of them takes non-refundable money from strangers. Listing a
board is not an endorsement, a safety check, or advice to bid on it.</p>

<script>
(function () {{
  var q = document.getElementById('q');
  var chips = [].slice.call(document.querySelectorAll('.chip'));
  var cards = [].slice.call(document.querySelectorAll('.board'));
  var groups = [].slice.call(document.querySelectorAll('.group[data-group]'));
  var empty = document.getElementById('empty');
  var filter = 'all';

  function apply() {{
    var term = q.value.trim().toLowerCase();
    var shown = 0;
    cards.forEach(function (card) {{
      var ok = (filter === 'all' || card.dataset.group === filter) &&
               (!term || card.dataset.text.indexOf(term) !== -1);
      card.hidden = !ok;
      if (ok) shown++;
    }});
    groups.forEach(function (g) {{
      g.hidden = !g.querySelector('.board:not([hidden])');
    }});
    empty.hidden = shown !== 0;
  }}

  q.addEventListener('input', apply);
  chips.forEach(function (chip) {{
    chip.addEventListener('click', function () {{
      chips.forEach(function (c) {{ c.classList.remove('on'); }});
      chip.classList.add('on');
      filter = chip.dataset.filter;
      apply();
    }});
  }});
}})();
</script>"""
    return page(
        base,
        "Boards · awesome-outbid",
        "Every pay-to-rank board with a sourced description, grouped by what it changed.",
        body,
        active="boards",
        wide=True,
    )


def build_guide_pages(base: str) -> list[tuple[Path, str]]:
    order = guide_order()
    pages = []
    for i, stem in enumerate(order):
        src = GUIDES / f"{stem}.md"
        raw = src.read_text(encoding="utf-8")
        body = md_to_html(rewrite_links(raw, base, GUIDES))

        prev_link = next_link = ""
        if i > 0:
            p = order[i - 1]
            prev_link = f'<a class="prev" href="{base}/guides/{p}/">← {html.escape(GUIDE_TITLES[p])}</a>'
        if i < len(order) - 1:
            n = order[i + 1]
            next_link = f'<a class="next" href="{base}/guides/{n}/">{html.escape(GUIDE_TITLES[n])} →</a>'

        toc_items = []
        for s in order:
            cls = ' class="on"' if s == stem else ""
            toc_items.append(
                f'<li><a href="{base}/guides/{s}/"{cls}>'
                f'<span>{s[:2]}</span> {html.escape(GUIDE_TITLES[s])}</a></li>'
            )
        toc = "\n".join(toc_items)

        wrapped = f"""<div class="guide">
  <aside class="toc">
    <p class="toc-title">Guides</p>
    <ol>{toc}</ol>
  </aside>
  <article class="prose">
{body}
    <nav class="pager">{prev_link}{next_link}</nav>
  </article>
</div>"""
        pages.append(
            (
                OUT / "guides" / stem / "index.html",
                page(
                    base,
                    f"{GUIDE_TITLES[stem]} · awesome-outbid",
                    f"Pay-to-rank board best practices: {GUIDE_TITLES[stem].lower()}.",
                    wrapped,
                    active="guides",
                    wide=True,
                ),
            )
        )
    return pages


def build_guides_index(base: str) -> str:
    raw = (GUIDES / "README.md").read_text(encoding="utf-8")
    body = md_to_html(rewrite_links(raw, base, GUIDES))
    return page(
        base,
        "Guides · awesome-outbid",
        "Eight guides for building a pay-to-rank board that survives real money.",
        f'<article class="prose">{body}</article>',
        active="guides",
    )


REFERENCE_FILES = [
    ("schema.sql", "Three tables, an idempotent <code>credit_bid()</code>, a write-absorbing click counter, and the board queries — including the keyset pagination seek predicate that is worth 769 buffers."),
    ("create-checkout.ts", "Amount validation, SSRF-aware URL normalisation, and the “must beat #1” check deliberately left out with the reasoning inline."),
    ("stripe-webhook.ts", "Raw-body signature verification, event routing, and which HTTP status code to return when."),
    ("pre-launch-checklist.md", "The list to run through the night before."),
]


def build_reference_page(base: str) -> str:
    items = "\n".join(
        f"""<article class="board">
  <h3><a href="{BLOB}/reference/{name}">{html.escape(name)}</a></h3>
  <p class="what">{desc}</p>
</article>"""
        for name, desc in REFERENCE_FILES
    )
    body = f"""<div class="hero small">
  <h1>Reference implementation</h1>
  <p class="lede">The patterns from the guides as code you can read in ten minutes.
  Framework-light on purpose — copy the ideas, not the imports.</p>
</div>

<p class="note">Verified rather than asserted: the schema was applied to Postgres 16
and its behaviour tested (replayed events credit once, two events describing the same
PaymentIntent credit once, money on a removed listing does not put it back on the
board, the rank query agrees with board position for every row). Both TypeScript
files typecheck under <code>strict</code> against the Stripe SDK.</p>

<div class="grid">{items}</div>"""
    return page(
        base,
        "Reference · awesome-outbid",
        "Annotated Postgres schema and Stripe integration for a pay-to-rank board.",
        body,
        active="reference",
    )


TEN_RULES = [
    ("The webhook is the only thing that grants rank.", "<code>success_url</code> is a redirect, not a payment. Boards that grant on redirect can be ranked for free.", "02-payments", "only-the-webhook-grants-rank"),
    ("Never promise a position at checkout.", "The top can move between your quote and the webhook. Sell a contribution; let the sort place it.", "01-auction-mechanics", "never-promise-a-rank-at-checkout"),
    ("Idempotency at two levels.", "Event id <em>and</em> PaymentIntent id, enforced by unique constraints — not by a <code>SELECT</code> first.", "02-payments", "assume-every-event-arrives-more-than-once"),
    ("Money is integer cents in an append-only ledger.", "Totals are derived, and therefore reconcilable.", "03-data-model", "ledger-first-totals-derived"),
    ("One atomic increment.", "<code>UPDATE … SET total = total + n</code>. Read-modify-write loses payments in exactly the traffic that pays your bills.", "03-data-model", "one-atomic-increment-no-read-modify-write"),
    ("Make the sort total.", "<code>total_cents DESC, first_paid_at ASC, id ASC</code>, paginated by keyset <em>with</em> a seek predicate.", "01-auction-mechanics", "make-the-sort-total-and-stable"),
    ("Lock the URL after first payment.", "Otherwise you are selling the top of a million-visitor page to whoever swaps in a phishing kit.", "05-abuse-and-moderation", "the-bait-and-switch-is-the-attack-you-will-actually-see"),
    ("Cache the board hard.", "And keep the payment path off the read path's resources. Being down during the window is the one unrecoverable failure.", "04-scale-and-realtime", "build-for-one-query"),
    ("Publish rules, refunds, takedowns and who you are.", "Before taking a dollar. All four get asked in week one.", "06-legal-and-trust", "publish-four-pages-before-you-take-a-dollar"),
    ("Traffic is the product.", "The code is a weekend; cloning it copies the cheap half.", "07-launch-and-distribution", "what-bidders-are-actually-buying"),
]

GUIDE_BLURBS = {
    "01-auction-mechanics": "Cumulative vs highest-bid, why you must never promise a rank at checkout, total sort orders, and which variants actually changed something.",
    "02-payments": "Signature verification, double idempotency, status codes, chargebacks, payout holds, and picking a refund policy before you need one.",
    "03-data-model": "Ledger-first schema, atomic increments, keyset pagination that seeks, click buffering, and a reconciliation query that should always return nothing.",
    "04-scale-and-realtime": "Caching the one query everyone runs, keeping payments alive when the read path saturates, and realtime you will not regret.",
    "05-abuse-and-moderation": "Post-payment bait-and-switch, SSRF, XSS, takedown policy, impersonation, and card testing.",
    "06-legal-and-trust": "Paid-placement disclosure, when a variant becomes gambling, EU/UK withdrawal rights, and the four pages to publish.",
    "07-launch-and-distribution": "Seeding, per-listing OG images, building in public, and why cloning the domain fails.",
    "08-after-the-spike": "Decay, telling bidders the truth about traffic, three honest endgames, and the obligations that outlive the hype.",
}


def build_index(data: dict, base: str) -> str:
    rules = "\n".join(
        f"""<li>
  <p class="rule"><a href="{base}/guides/{g}/#{a}">{t}</a></p>
  <p class="rule-why">{d}</p>
</li>"""
        for t, d, g, a in TEN_RULES
    )

    guides = "\n".join(
        f"""<a class="guide-card" href="{base}/guides/{s}/">
  <span class="num">{s[:2]}</span>
  <h3>{html.escape(GUIDE_TITLES[s])}</h3>
  <p>{GUIDE_BLURBS[s]}</p>
</a>"""
        for s in guide_order()
    )

    counts = {}
    for b in data["boards"]:
        counts[b["group"]] = counts.get(b["group"], 0) + 1
    group_rows = "\n".join(
        f"""<a class="group-row" href="{base}/boards/#{g['id']}">
  <span class="n">{counts[g['id']]}</span>
  <span class="t">{html.escape(g['title'])}</span>
  <span class="b">{html.escape(tidy(g['blurb']))}</span>
</a>"""
        for g in data["groups"]
        if counts.get(g["id"])
    )

    body = f"""<div class="hero">
  <p class="kicker">Best practices for the outbid.lol genre</p>
  <h1>Pay-to-rank boards, done properly</h1>
  <p class="lede">outbid.lol went from a three-hour build to <strong>$139,041 in 65
  hours</strong>, 1.1M visitors and a few hundred clones. The mechanic is four lines of
  SQL. Everything that makes one of these boards survive contact with real money is
  not — and that is what this is.</p>
  <p class="cta">
    <a class="btn" href="{base}/guides/01-auction-mechanics/">Start reading</a>
    <a class="btn ghost" href="{base}/boards/">{len(data['boards'])} boards, sorted by what they changed</a>
  </p>
</div>

<section>
  <h2>The ten rules</h2>
  <p class="section-lede">If you read nothing else. Each links to the guide that
  explains what it costs to get wrong.</p>
  <ol class="rules">{rules}</ol>
</section>

<section>
  <h2>The guides</h2>
  <p class="section-lede">Ordered so each builds on the last — the auction rule you
  pick in 01 determines the schema in 03, and the schema is what makes the webhook in
  02 safe.</p>
  <div class="guide-grid">{guides}</div>
</section>

<section>
  <h2>The wave</h2>
  <p class="section-lede">By clone forty the genre had stopped being clones. These are
  grouped by what they actually changed, because a different domain is not a variant.</p>
  <div class="groups">{group_rows}</div>
  <p class="more"><a href="{base}/boards/">Browse all {len(data['boards'])} boards →</a></p>
</section>

<section>
  <h2>Reference implementation</h2>
  <p class="section-lede">The patterns as annotated code. The schema was applied to
  Postgres 16 and its behaviour tested; both TypeScript files typecheck under
  <code>strict</code> against the Stripe SDK.</p>
  <p class="more"><a href="{base}/reference/">See the reference files →</a></p>
</section>"""
    return page(
        base,
        "awesome-outbid — pay-to-rank boards, done properly",
        "Best practices, reference code and a field guide for building pay-to-rank leaderboards — the outbid.lol genre.",
        body,
        active="",
    )


def build_site(data: dict, base: str) -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    write(OUT / "index.html", build_index(data, base))
    write(OUT / "boards" / "index.html", build_boards_page(data, base))
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
