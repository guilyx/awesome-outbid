# Contributing

Two kinds of contribution, with different bars.

## Best practices and reference code

The bar is **"this bit someone, in production, on a board taking real money."**

Pull requests that add a guide, a section, or a fix should:

- Describe a concrete failure, not a preference. "Use X, it's cleaner" is not
  a best practice; "reading the total before updating it loses payments under
  concurrent load, here is why" is.
- Say what the failure costs — lost money, a free rank, an outage, a dispute, a
  takedown you could not perform.
- Keep code runnable and framework-light. The reference files are meant to be
  read in ten minutes, not imported.
- Prefer Postgres and Stripe for examples, since that is what the genre runs
  on, but note where the idea generalises.

Post-mortems are the most valuable thing you can add — especially unflattering
ones. Hundreds of boards launched in August 2026 and almost nobody wrote up
what happened in week four. If you ran one, we want the traffic curve, the
decay rate, the dispute rate, and what broke.

## Adding a board to the list

The list is a snapshot of a genre that moves in days, so entries earn their
place by being *interesting*, not by existing.

To be listed, a board should:

- Be live and reachable at the time of the PR.
- Change something about the mechanic, the audience, or the unit being ranked.
  A cumulative-bid board on a new domain is not a variant and will be closed.
- State its rules and its refund policy somewhere public.
- Have a contact address.

To be listed, a board must **not**:

- Fabricate bid amounts, click counts, or traffic figures.
- Rank people who did not consent and cannot remove themselves.
- Be a wrapper whose only purpose is to sell a course, a boilerplate, or a
  waitlist.

Add an entry to [`data/boards.yml`](data/boards.yml) — never to the README
directly. The README tables and the site's board directory are both generated
from that file, and CI fails if they drift.

```yaml
  - name: example.lol
    url: https://example.lol
    group: decay          # see the `groups:` block at the top of the file
    ranks: side projects  # what it ranks, a few words
    what: >-
      One or two sentences on the mechanic, in your own words. What did this
      board change? Why would someone bid here instead of on the original?
    launched: 2026-08-21  # optional, only if a source states it
    by: Someone           # optional, only if a source names them
    sourced: true
```

That is the whole change. **You do not need to touch the README** — CI
regenerates its board tables from this file after your pull request merges, and
your PR's job summary shows you the exact rows it will add, so a reviewer can
check the wording without either of you running anything.

If you would rather see it locally first:

```sh
pip install pyyaml markdown
python3 scripts/build.py     # rewrites the README section, builds _site/
```

Committing that regenerated README is fine but not required — CI arrives at the
same result either way.

File it under the group whose *mechanic* it matches, not alphabetically. If it
matches none of them, that is a good sign — propose a new group in the same PR
and say what it is.

### `sourced: true` means you have a source

The `sourced` flag is not decoration. It asserts that the description came from
somewhere — the board's own rules page, a write-up, a post from its creator —
rather than from guessing at the mechanic from the domain name.

If you know a board exists but cannot describe what it does, add it to
`named_only` instead. That list exists precisely so the record can be complete
without anyone inventing mechanics. `scripts/build.py` refuses to build if a
board sits in `boards:` without `sourced: true`.

### What listing does not mean

Nothing here is vetted, endorsed, or checked for safety, and every board in the
list takes non-refundable money from strangers. Contributors are not
recommending that anyone bid. Do not open PRs asking us to describe a board as
trustworthy, safe, or a good investment; those will be closed.

### Removing a dead board

Very welcome. Domains in this space go dark fast, and a directory full of parked
pages is worse than a short one. Drop the entry from `data/boards.yml`, rebuild,
and open the PR — no justification is needed beyond "it does not resolve."

The weekly [link check](.github/workflows/link-check.yml) opens an issue listing
dead links rather than failing pull requests, so nobody is ever blocked by
someone else's expired board.

## Self-promotion

Allowed and expected — most people who build one of these will want it listed.
Say in the PR that it is yours. The bar is the same either way.

## Style

- One sentence per idea; short lines. The files are read on phones.
- Sentence case for headings.
- Relative links between files in this repo, so they work on forks.

Adding a board needs none of this — edit `data/boards.yml` and open the PR.
For everything else, CI runs:

```sh
npx markdownlint-cli2 "**/*.md"                    # style
python3 .github/scripts/check_relative_links.py    # in-repo links and anchors
python3 scripts/build.py --site-only               # build, and validate boards.yml
python3 scripts/check_site.py                      # site links and anchors
```

Run them locally if you want a faster loop (`pip install pyyaml markdown` for
the last two).

## Code of conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
