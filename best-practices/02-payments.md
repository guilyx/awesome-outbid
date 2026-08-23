# 2. Payments and webhooks

You are running a payments product with a leaderboard attached. This is the
file to read twice.

## Only the webhook grants rank

`success_url` is a redirect. A browser can reach it by typing it, a
prefetcher can hit it, a payment can fail asynchronously after it, and a card
can be declined at capture. If your board grants rank on redirect, it can be
ranked for free — and someone will find that out publicly on the day you go
viral.

Rank changes only when a **signature-verified webhook** confirms settled
money. If you want instant gratification on the success page, poll your own
API for the listing's state, or do a server-side
`checkout.sessions.retrieve()` and check `payment_status === 'paid'` — but
credit the ledger in one place, the webhook, so there is one code path to get
right.

## Verify the signature against the raw bytes

The single most common integration bug in this genre: some middleware parses
the request body before `constructEvent` sees it, so you verify a signature
against re-serialised JSON. It fails 100% in production and passes 100% with
`stripe listen`, because the CLI happens to send bytes you round-trip
cleanly.

- Next.js App Router: `await req.text()`, and nothing above it may consume the
  body.
- Express: `express.raw({ type: 'application/json' })` mounted **before** the
  global `express.json()`.
- Reject with **400** on a bad signature. Never 500 — a forged request should
  not enter Stripe's three-day retry queue.

## Assume every event arrives more than once

Stripe guarantees at-least-once delivery and retries with backoff for up to
three days. Your handler will be called twice with the same event, and it will
also be called with two *different* events describing the same money
(`checkout.session.completed` and `payment_intent.succeeded` carry the same
PaymentIntent).

So guard at both levels, in the database, in one transaction:

1. `INSERT` the `stripe_event_id` into a table with a primary key,
   `ON CONFLICT DO NOTHING`. Zero rows affected means you have seen this
   event.
2. `INSERT` the payment with a `UNIQUE` constraint on
   `stripe_payment_intent_id`. Zero rows affected means this money is already
   on the board.

An in-memory `Set` is not a guard. Neither is a `SELECT` before the `INSERT` —
that is a race with a friendlier shape. `credit_bid()` in
`reference/schema.sql` shows the whole thing in about thirty lines.

## Return the status code you mean

| Situation | Code | Why |
| --- | --- | --- |
| Credited successfully | 200 | Done |
| Already processed | 200 | Retrying will not help and it is not an error |
| Bad/absent signature | 400 | Never retry a forged request |
| Event type you ignore | 200 | Silence, not noise |
| Transient DB failure | 500 | You *want* the retry — your handler is idempotent |
| Missing `listing_id` on a paid session | 200 + alert | Money arrived that you cannot place. Retrying will not conjure the field; a human must reconcile it, and someone is waiting for a rank |

Do the side effects — receipt email, cache bust, OG image, realtime push —
*after* the credit and outside the response path. If a failing email turns
into a 500, Stripe redelivers an event whose money is already on the board,
the second pass correctly no-ops, and your alerting screams about a
non-problem while you are already busy.

## Take the amount from Stripe, never from the client

`session.amount_total` is integer minor units and is already net of coupons.
Build `price_data.unit_amount` server-side from a validated integer. Never
accept a client-supplied Price ID, and never trust an amount echoed back from
the browser.

Also validate the currency matches what your board sorts in, and alert rather
than crediting if it does not.

## Idempotency keys on the way out too

Pass `idempotencyKey` when creating the Checkout Session. A double-clicked
button or a retried fetch otherwise opens two sessions for one intent to pay,
and some people will pay both.

## Chargebacks are the real risk, not fraud

Digital goods, no shipping, no login, an unfamiliar name on the statement, and
often a founder expensing it — this is a high-dispute profile before anything
goes wrong. Card networks put merchants into monitoring programmes around
0.75–1% dispute rate, and processors terminate accounts that stay there. At
$139k in 65 hours you do not have the transaction history to absorb that.

Reduce disputes:

- **Statement descriptor.** Set `statement_descriptor_suffix` to something the
  cardholder will recognise as your board. "I don't recognise this charge" is
  the most common dispute reason and the easiest to prevent.
- **Receipt as evidence.** Email immediately: listing name, amount, timestamp,
  the rank it bought, and a permalink to the listing. That email is literally
  what you upload when you contest a dispute.
- **Consent at the moment of payment.** `consent_collection.terms_of_service:
  'required'` on the Checkout Session. A checkbox at checkout is worth far
  more in a dispute than a link in your footer.
- **A human before a dispute.** Put a billing email on the checkout page and
  the receipt, and answer it fast. Every refund you issue voluntarily is a
  dispute you did not get.
- **Radar on**, and rate-limit checkout creation per IP. Carding rings love an
  endpoint that takes an arbitrary amount with no account.

Win the ones you contest: a public, timestamped, immutable board is unusually
strong evidence that the service was delivered exactly as described.

## Expect a hold, and do not promise money you cannot move

A brand-new account taking six figures in two days looks exactly like fraud to
a risk model. Reviews and payout holds are normal, not a betrayal. Consequences
for how you design:

- Do not build revenue-sharing, referral payouts, or "we donate X%" into
  launch week. You may not be able to move the funds.
- Do not spend the float.
- Have a fallback processor configured, not just bookmarked, before you need
  it.

## Refunds: pick a policy and publish it before you need one

"Bids are permanent and non-refundable" is a legitimate policy and the one the
genre uses. It only holds up if it is stated plainly, agreed to at checkout,
and applied consistently. Carve out, in writing, the cases you *will* refund:

- Duplicate charges and technical failures.
- Refunds you are legally required to make.
- Listings you remove for abuse (decide in advance whether you refund those —
  and note that keeping the money is defensible if you said so up front, but
  refunding is a much better look).

Then honour it. A no-refund rule you quietly break for whoever complains
loudest is worse than no rule.
