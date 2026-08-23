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
