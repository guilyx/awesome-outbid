## What is this?

<!-- One of: a board for the list, a best practice, a post-mortem, a fix. -->

- [ ] Board addition
- [ ] Best practice / guide change
- [ ] Post-mortem
- [ ] Fix or correction

## Summary

<!-- What changed and why. For a best practice, lead with the concrete failure
     it prevents, not the preference it expresses. -->

## For board additions

- [ ] The board is live and reachable right now
- [ ] It changed the mechanic, the audience, or the unit ranked — not just the domain
- [ ] Its rules and refund policy are published publicly
- [ ] It has a contact address
- [ ] Amounts and click counts shown on it are real
- [ ] It does not rank people who cannot remove themselves
- [ ] Filed in `data/boards.yml` (not the README directly), under the group matching its mechanic
- [ ] `sourced: true` only where a real source describes the mechanic; otherwise `named_only`
- [ ] Ran `python3 scripts/build.py` and committed the regenerated README
- [ ] Disclosed above if the board is mine

## For guide or reference changes

- [ ] Describes a concrete failure and what it costs
- [ ] Code samples are runnable and framework-light
- [ ] Cross-links to the relevant guide or reference file

## Checks

- [ ] `npx markdownlint-cli2 "**/*.md"` passes
- [ ] `python3 .github/scripts/check_relative_links.py` passes
- [ ] `python3 scripts/build.py --check` passes (README in sync with `data/boards.yml`)
- [ ] `python3 scripts/build.py && python3 scripts/check_site.py` passes
