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

Open a PR with:

```text
- `example.lol` — one line on what it changed. [live | dead]
```

Put it under the group whose *mechanic* it matches, not alphabetically. If it
does not match any group, that is a good sign — propose a new group and say
what it is.

### What listing does not mean

Nothing here is vetted, endorsed, or checked for safety, and every board in the
list takes non-refundable money from strangers. Contributors are not
recommending that anyone bid. Do not open PRs asking us to describe a board as
trustworthy, safe, or a good investment; those will be closed.

### Removing a dead board

Very welcome. Domains in this space go dark fast, and a directory full of
parked pages is worse than a short one. Mark it dead or drop the entry — either
is fine, and no justification is needed beyond "it does not resolve."

## Self-promotion

Allowed and expected — most people who build one of these will want it listed.
Say in the PR that it is yours. The bar is the same either way.

## Style

- One sentence per idea; short lines. The files are read on phones.
- Sentence case for headings.
- `markdownlint` runs in CI. Run it locally with
  `npx markdownlint-cli2 "**/*.md"`.
- Relative links between files in this repo, so they work on forks.

## Code of conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
