# Awesome Outbid [![Awesome](https://awesome.re/badge-flat2.svg)](https://awesome.re)

> Best practices, reference code, and a field guide for building pay-to-rank
> leaderboards — the [outbid.lol](https://outbid.lol) genre.

On 19 August 2026, Jonathan Wilke shipped a leaderboard in a three-hour coding
sprint. One rule: pay money, rank higher. Within 65 hours it had taken
**$139,041** across ~900 listings from **1.1M+ visitors**, broken its analytics
provider, attracted a six-figure acquisition offer, and spawned a few hundred
clones.

The mechanic is four lines of SQL. Everything that makes one of these boards
survive contact with real money — idempotent payments, a sort that does not
shuffle, a URL that cannot be swapped for a phishing page after it reaches #1,
a refund policy written before the first dispute — is not.

This repo is that missing half.

## Contents

- [Start here](#start-here)
- [Reference implementation](#reference-implementation)
- [The ten rules](#the-ten-rules)
- [The original](#the-original)
- [Directories and trackers](#directories-and-trackers)
- [Notable boards and variants](#notable-boards-and-variants)
- [Boilerplates and tooling](#boilerplates-and-tooling)
- [Writeups and analysis](#writeups-and-analysis)
- [Anti-patterns](#anti-patterns)
- [Contributing](#contributing)
- [License](#license)

## Start here

Eight guides, in the order they build on each other.

| # | Guide | What it covers |
| --- | --- | --- |
| 1 | [Auction mechanics](best-practices/01-auction-mechanics.md) | Cumulative vs highest-bid, why you must never promise a rank at checkout, total sort orders, variants |
| 2 | [Payments and webhooks](best-practices/02-payments.md) | Signature verification, double idempotency, status codes, chargebacks, payout holds |
| 3 | [Data model and concurrency](best-practices/03-data-model.md) | Ledger-first schema, atomic increments, keyset pagination, click buffering |
| 4 | [Surviving the spike](best-practices/04-scale-and-realtime.md) | Caching the one query, keeping payments alive under load, realtime without regret |
| 5 | [Abuse and moderation](best-practices/05-abuse-and-moderation.md) | Post-payment bait-and-switch, SSRF, XSS, takedowns, impersonation, card testing |
| 6 | [Legal and trust](best-practices/06-legal-and-trust.md) | Paid-placement disclosure, when a variant becomes gambling, EU/UK withdrawal rights |
| 7 | [Launch and distribution](best-practices/07-launch-and-distribution.md) | Seeding, per-listing OG images, building in public, why cloning the domain fails |
| 8 | [After the spike](best-practices/08-after-the-spike.md) | Decay, telling bidders the truth, three honest endgames, obligations that outlive the hype |

## Reference implementation

Annotated, framework-light, readable in ten minutes. Copy the ideas, not the
imports.

- **[`reference/schema.sql`](reference/schema.sql)** — three tables, an
  idempotent `credit_bid()` function, write-absorbing click counters, and the
  board queries including keyset pagination and rank lookup.
- **[`reference/create-checkout.ts`](reference/create-checkout.ts)** — amount
  validation, SSRF-aware URL normalisation, and the rank promise deliberately
  *not* made.
- **[`reference/stripe-webhook.ts`](reference/stripe-webhook.ts)** — raw-body
  signature verification, event routing, and which HTTP status code to return
  when.
- **[`reference/pre-launch-checklist.md`](reference/pre-launch-checklist.md)** —
  the list to run the night before.

## The ten rules

1. **The webhook is the only thing that grants rank.** `success_url` is a
   redirect, not a payment. Boards that grant on redirect can be ranked for
   free.
2. **Never promise a position at checkout.** The top can move between your
   quote and the webhook. Sell a contribution; let the sort place it.
3. **Idempotency at two levels** — event id *and* PaymentIntent id — enforced
   by unique constraints, not by a `SELECT` first.
4. **Money is integer cents in an append-only ledger.** Totals are derived,
   and therefore reconcilable.
5. **One atomic `UPDATE ... SET total = total + n`.** Read-modify-write loses
   payments in exactly the traffic that pays your bills.
6. **Make the sort total.** `total_cents DESC, first_paid_at ASC, id ASC`, or
   the board reshuffles on refresh and pagination eats rows.
7. **Lock the URL after first payment.** Otherwise you are selling the top of a
   1M-visitor page to whoever swaps in a phishing kit.
8. **Cache the board hard; keep the payment path off the read path's
   resources.** Being down during the window is the one unrecoverable failure.
9. **Publish rules, refunds, takedowns and who you are** before taking a
   dollar. All four get asked in week one.
10. **Traffic is the product.** The code is a weekend; cloning it copies the
    cheap half.

## The original

- [outbid.lol](https://outbid.lol) — the board. Rank equals total dollars paid.
  Whole dollars, $5 minimum, $1 increments, $999,999 cap, nothing expires,
  nothing is refunded.
- [outbid.lol/rules](https://outbid.lol/rules) — the entire rulebook, and a
  good model for how short one should be.
- [outbid.lol/about](https://outbid.lol/about) — no ads, no API keys, no
  revenue sharing, no accounts.
- [@jonathan_wilke](https://x.com/jonathan_wilke) — built it on his
  [supastarter](https://supastarter.dev) boilerplate (Next.js + Postgres) in
  three hours; posted the numbers as they happened.

## Directories and trackers

Meta-layers that emerged within days, and the fastest way to see the current
state of the genre.

- [outoutbid.lol](https://outoutbid.lol) — every outbid.lol clone, grouped by
  what it ranks.
- [Bidding Arena](https://biddingarena.com/boards) — the largest tracker;
  hundreds of boards, with which are still live.
- [outbid.fyi](https://outbid.fyi) — pay-to-rank board index.
- [outbid-directory.lol](https://outbid-directory.lol) — clone directory,
  plus a boilerplate.
- [topple.lol](https://topple.lol) — tracks the live price of the #1 spot on
  outbid.lol and explains the mechanics.

## Notable boards and variants

The wave stopped being clones fast. These are grouped by *what they changed*,
because that is the only useful axis — a different domain is not a variant.

**Pure cumulative bidding** (the original mechanic)

- [overbid.lol](https://www.overbid.lol), rankbid.lol, upbid.lol, outbids.lol

**Inverted auctions** — removes the "richest founder wins" feel

- `lowbid.lol` — lowest *unique* bid takes the top. Note the gambling-law
  caveat in [6. Legal and trust](best-practices/06-legal-and-trust.md#keep-it-deterministic-or-you-may-be-running-a-lottery).
- `undercut.lol`, `dontbid.lol` — Dutch-style undercutting.

**Time pressure** — manufactures urgency a static board only has while trending

- `lastspot.lol` — fixed slot count with daily decay.

**Different unit ranked** — same mechanic, different audience

- `tweetbid.lol`, `xbid.lol` — X posts and handles.
- `indiehackers.lol`, `outflex.lol` — people and profiles.
- `landgrab.lol`, `warmap.lol`, `spots.lol` — territory and map metaphors.
- `topspot.so` — the non-`.lol` sibling.

**Meta** — boards that rank boards

- `biddirectory.lol`, and the trackers above.

> **On these links.** This is a snapshot of a genre that moved in days; entries
> are community-submitted and unverified. Domains in this space go dark
> quickly, and every one of them takes non-refundable money from strangers.
> Listing a board here is not an endorsement, a safety check, or advice to
> bid on it. See [CONTRIBUTING.md](CONTRIBUTING.md) for what gets listed.

## Boilerplates and tooling

- [Outbid boilerplate](https://outbid-directory.lol/outbid-boilerplate) —
  extracted from a production board and trimmed to a starting point.
- [Bidkit](https://www.superfa.st/outbid-lol) — hosted "launch a bidding
  platform" tooling.
- [supastarter](https://supastarter.dev) — the Next.js + Postgres boilerplate
  outbid.lol itself was built on.
- [Stripe Checkout](https://stripe.com/docs/payments/checkout) +
  [webhook docs](https://stripe.com/docs/webhooks) — read the idempotency and
  signature-verification sections specifically.
- [Stripe Tax](https://stripe.com/tax) — destination-based VAT on digital
  services is not a thing you want to hand-roll.

Before reaching for a boilerplate, read
[2. Payments](best-practices/02-payments.md) — most of these ship the happy
path and leave idempotency, dispute evidence and URL locking to you.

## Writeups and analysis

- [Inside outbid.lol: the pay-to-rank board taking over tech](https://automatio.ai/articles/dev-tools/inside-outbid-lol-the-pay-to-rank-board-taking-over-tech)
  — the most technical account: concurrency handling, webhook flow, the
  three-hour build.
- [Why the pay-to-rank board went viral](https://www.explainx.ai/blog/outbid-lol-pay-to-rank-leaderboard-viral-august-2026)
  — why clones with no audience earn nothing.
- [The .lol bidding directory frenzy of August 2026](https://saascity.io/blog/lol-bidding-directory-frenzy-outbid-payluck-2026)
  — taxonomy of the variants.
- [A dead-simple website that made $100K in under 48 hours](https://generativeai.pub/outbid-lol-is-blowing-up-right-now-a-dead-simple-website-and-made-100k-in-less-than-48-hours-ee471942bebf)
  — the timeline as it happened.
- [$139,041 in 65 hours](https://www.allblogthings.com/2026/08/outbidlol-simple-pay-to-rank-website-generates-139041-in-56-hours.html)
  — the numbers.
- [Hacker News discussion](https://news.ycombinator.com/item?id=49385854)
- [How outbid.lol works, and why the price only goes up](https://topple.lol/how-outbid-lol-works)
- [Is it legit, and is a spot worth paying for?](https://topple.lol/outbid-lol-review)
  — the bidder's side, which is worth reading if you are selling to them.

## Anti-patterns

Every one of these has shipped, in public, on a board taking real money.

| Anti-pattern | What happens | Fix |
| --- | --- | --- |
| Granting rank on `success_url` | Free ranks for anyone who reads a URL | [02](best-practices/02-payments.md#only-the-webhook-grants-rank) |
| Parsing the body before signature verification | Every webhook fails in prod, all of them pass locally | [02](best-practices/02-payments.md#verify-the-signature-against-the-raw-bytes) |
| `SELECT` then `UPDATE` on the total | Silently lost payments under exactly the load you wanted | [03](best-practices/03-data-model.md#one-atomic-increment-no-read-modify-write) |
| Enforcing "must beat #1" at checkout | Refund-or-lie, during your best hour | [01](best-practices/01-auction-mechanics.md#never-promise-a-rank-at-checkout) |
| `ORDER BY total DESC` with no tiebreak | Board reshuffles on refresh; pagination duplicates and skips | [01](best-practices/01-auction-mechanics.md#make-the-sort-total-and-stable) |
| `LIMIT/OFFSET` pagination | Listings appear twice or vanish while the board moves | [03](best-practices/03-data-model.md#keyset-pagination-never-offset) |
| Keyset pagination with no seek predicate | Correct rows, but deep pages scan the whole index — 769 buffers vs 7, measured | [03](best-practices/03-data-model.md#the-redundant-line-is-the-whole-optimisation) |
| Editable URL after payment | You sold the top of a viral page to a phishing kit | [05](best-practices/05-abuse-and-moderation.md#the-bait-and-switch-is-the-attack-you-will-actually-see) |
| Re-payment resets `status` to active | Money buys its way past your own moderation | [03](best-practices/03-data-model.md#statuses-and-the-one-rule-that-must-not-be-buyable) |
| `click_count = click_count + 1` per redirect | The hottest row becomes a global lock | [03](best-practices/03-data-model.md#do-not-increment-a-counter-per-click) |
| Server-side favicon fetch with no IP validation | An HTTP client inside your VPC, for $5 | [05](best-practices/05-abuse-and-moderation.md#ssrf-if-you-fetch-the-url-you-are-a-proxy) |
| Floats for money | `10.10 * 100 === 1009.9999999999999` | [01](best-practices/01-auction-mechanics.md#integer-cents-one-currency) |
| Unrecognisable statement descriptor | The most common — and most preventable — dispute reason | [02](best-practices/02-payments.md#chargebacks-are-the-real-risk-not-fraud) |
| No refund policy until the first refund | You improvise it under pressure, in public | [02](best-practices/02-payments.md#refunds-pick-a-policy-and-publish-it-before-you-need-one) |
| Revenue sharing promised in launch week | Your funds are under review and you cannot pay | [02](best-practices/02-payments.md#expect-a-hold-and-do-not-promise-money-you-cannot-move) |
| Fabricated seed bids or inflated click counts | Fraud, trivially caught by comparing board to ledger | [07](best-practices/07-launch-and-distribution.md#an-empty-board-converts-at-zero) |
| Taking the board down after the hype | A wave of chargebacks and no credibility for the next launch | [08](best-practices/08-after-the-spike.md#three-honest-endgames) |
| Shipping the same board on a new domain | Clone #40's traffic curve is flat | [07](best-practices/07-launch-and-distribution.md#if-you-are-cloning-change-the-audience--not-the-domain) |

## Contributing

Additions welcome — especially post-mortems, and especially unflattering ones.
The genre produced hundreds of boards and almost no honest accounts of what
happened after week one.

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Disclaimer

Nothing here is legal, financial, or tax advice. Pay-to-rank boards take
non-refundable payments from consumers, publish user-submitted links, and sit
in a payments-risk category that gets accounts terminated. If yours is making
real money, talk to a lawyer and to your payment processor.

## License

[CC0 1.0](LICENSE) — public domain. Take it, ship it, no attribution needed.
