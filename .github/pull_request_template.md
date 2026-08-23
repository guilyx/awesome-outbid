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
- [ ] It is filed under the group matching its mechanic
- [ ] Disclosed above if the board is mine

## For guide or reference changes

- [ ] Describes a concrete failure and what it costs
- [ ] Code samples are runnable and framework-light
- [ ] Cross-links to the relevant guide or reference file

## Checks

- [ ] `npx markdownlint-cli2 "**/*.md"` passes
- [ ] Relative links resolve (`python3 .github/scripts/check_relative_links.py`)
