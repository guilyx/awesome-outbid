# Best practices

Everything here is written for one specific thing: a public leaderboard where
position is bought, settled by a card payment, under traffic you did not plan
for.

Read them in order the first time. They build on each other — the auction rule
you pick in 01 determines the schema in 03, and the schema is what makes the
webhook in 02 safe.

| # | File | What it covers |
| --- | --- | --- |
| 1 | [Auction mechanics](01-auction-mechanics.md) | Cumulative vs highest-bid, why you must never promise a rank at checkout, total sort orders, variants |
| 2 | [Payments and webhooks](02-payments.md) | Signature verification, double idempotency, status codes, chargebacks, payout holds, refund policy |
| 3 | [Data model and concurrency](03-data-model.md) | Ledger-first schema, atomic increments, keyset pagination, click buffering, reconciliation |
| 4 | [Surviving the spike](04-scale-and-realtime.md) | Caching the one query, keeping payments alive under load, realtime without regret, analytics that hold |
| 5 | [Abuse and moderation](05-abuse-and-moderation.md) | Post-payment bait-and-switch, SSRF, XSS, takedown policy, impersonation, card testing |
| 6 | [Legal and trust](06-legal-and-trust.md) | Paid-placement disclosure, when a variant becomes gambling, EU/UK withdrawal rights, the four pages to publish |
| 7 | [Launch and distribution](07-launch-and-distribution.md) | Seeding, per-listing OG images, building in public, why cloning the domain fails |
| 8 | [After the spike](08-after-the-spike.md) | Decay, telling bidders the truth, three honest endgames, obligations that outlive the hype |

## The short version

If you read nothing else:

1. **The webhook is the only thing that grants rank.** `success_url` is a
   redirect, not a payment.
2. **Never promise a position at checkout.** Sell a contribution; let the sort
   place it once the money is real.
3. **Idempotency at two levels** — event id and PaymentIntent id — enforced by
   unique constraints, not by a `SELECT` first.
4. **Money is integer cents in an append-only ledger.** Totals are derived and
   reconcilable.
5. **One atomic `UPDATE ... SET total = total + n`.** Never read-modify-write.
6. **Total, stable sort order.** `total_cents DESC, first_paid_at ASC, id ASC`,
   paginated by keyset *with* a seek predicate.
7. **Lock the URL after payment.** Otherwise you sell the top of a viral page
   to a phishing kit.
8. **Cache the board hard, and keep the payment path off the read path's
   resources.**
9. **Publish rules, refunds, takedowns and who you are** before taking a
   dollar.
10. **Traffic is the product.** Cloning the code copies the cheap half.

## Reference implementation

The patterns above, as code you can read in ten minutes:

- [`reference/schema.sql`](../reference/schema.sql) — the three tables,
  `credit_bid()`, click buffering, and the board queries.
- [`reference/create-checkout.ts`](../reference/create-checkout.ts) — amount
  validation, URL normalisation, and the rank promise deliberately not made.
- [`reference/stripe-webhook.ts`](../reference/stripe-webhook.ts) — signature
  verification, event routing, status codes.
- [`reference/pre-launch-checklist.md`](../reference/pre-launch-checklist.md) —
  the list to run through the night before.

They are illustrative, not a framework. Copy the ideas, not the imports.

## Anti-patterns

Every one of these has shipped, in public, on a board taking real money.

| Anti-pattern | What happens | Fix |
| --- | --- | --- |
| Granting rank on `success_url` | Free ranks for anyone who reads a URL | [02](02-payments.md#only-the-webhook-grants-rank) |
| Parsing the body before signature verification | Every webhook fails in prod, all of them pass locally | [02](02-payments.md#verify-the-signature-against-the-raw-bytes) |
| `SELECT` then `UPDATE` on the total | Silently lost payments under exactly the load you wanted | [03](03-data-model.md#one-atomic-increment-no-read-modify-write) |
| Enforcing "must beat #1" at checkout | Refund-or-lie, during your best hour | [01](01-auction-mechanics.md#never-promise-a-rank-at-checkout) |
| `ORDER BY total DESC` with no tiebreak | Board reshuffles on refresh; pagination duplicates and skips | [01](01-auction-mechanics.md#make-the-sort-total-and-stable) |
| `LIMIT/OFFSET` pagination | Listings appear twice or vanish while the board moves | [03](03-data-model.md#keyset-pagination-never-offset) |
| Keyset pagination with no seek predicate | Correct rows, but deep pages scan the whole index — 769 buffers vs 7, measured | [03](03-data-model.md#the-redundant-line-is-the-whole-optimisation) |
| Editable URL after payment | You sold the top of a viral page to a phishing kit | [05](05-abuse-and-moderation.md#the-bait-and-switch-is-the-attack-you-will-actually-see) |
| Re-payment resets `status` to active | Money buys its way past your own moderation | [03](03-data-model.md#statuses-and-the-one-rule-that-must-not-be-buyable) |
| `click_count = click_count + 1` per redirect | The hottest row becomes a global lock | [03](03-data-model.md#do-not-increment-a-counter-per-click) |
| Server-side favicon fetch with no IP validation | An HTTP client inside your VPC, for $5 | [05](05-abuse-and-moderation.md#ssrf-if-you-fetch-the-url-you-are-a-proxy) |
| Floats for money | `10.10 * 100 === 1009.9999999999999` | [01](01-auction-mechanics.md#integer-cents-one-currency) |
| Unrecognisable statement descriptor | The most common — and most preventable — dispute reason | [02](02-payments.md#chargebacks-are-the-real-risk-not-fraud) |
| No refund policy until the first refund | You improvise it under pressure, in public | [02](02-payments.md#refunds-pick-a-policy-and-publish-it-before-you-need-one) |
| Revenue sharing promised in launch week | Your funds are under review and you cannot pay | [02](02-payments.md#expect-a-hold-and-do-not-promise-money-you-cannot-move) |
| Fabricated seed bids or inflated click counts | Fraud, trivially caught by comparing board to ledger | [07](07-launch-and-distribution.md#an-empty-board-converts-at-zero) |
| Taking the board down after the hype | A wave of chargebacks and no credibility for the next launch | [08](08-after-the-spike.md#three-honest-endgames) |
| Shipping the same board on a new domain | Clone #40's traffic curve is flat | [07](07-launch-and-distribution.md#if-you-are-cloning-change-the-audience--not-the-domain) |

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
[2. Payments](02-payments.md) — most of these ship the happy
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
