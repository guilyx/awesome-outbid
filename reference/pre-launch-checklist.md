# Pre-launch checklist

Run this the night before. Anything unchecked is something you will be fixing
in public, during the only 72 hours that matter.

## Payments

- [ ] Webhook signature verified against the **raw request body**, with nothing
      parsing it upstream
- [ ] Verified with a real Stripe test webhook, not only `stripe listen`
- [ ] Bad signature returns **400**, transient DB failure returns **500**,
      everything else returns **200**
- [ ] Event-level idempotency: unique `stripe_event_id`
- [ ] Payment-level idempotency: unique `stripe_payment_intent_id`
- [ ] Replaying the same webhook twice credits once — actually tested
- [ ] `checkout.session.async_payment_succeeded` handled, not just `completed`
- [ ] `payment_status !== 'paid'` does not move a rank
- [ ] Amount read from `session.amount_total`, never from the client
- [ ] Currency checked before crediting
- [ ] `idempotencyKey` set on Checkout Session creation
- [ ] `statement_descriptor_suffix` set and recognisable
- [ ] Receipt email includes listing name, amount, timestamp, rank, permalink
- [ ] Terms consent collected at checkout
- [ ] Live keys in the environment; test keys are not
- [ ] Webhook endpoint registered against the **live** endpoint secret
- [ ] Alert on webhook 5xx rate

## Data

- [ ] Money is `bigint` cents everywhere — DB, API, and formatter input
- [ ] `UPDATE ... SET total_cents = total_cents + n`, no read-modify-write
      anywhere
- [ ] Sort order is total: `total_cents DESC, first_paid_at ASC, id ASC`
- [ ] Index covers that sort, partial on `status = 'active'`
- [ ] Pagination is keyset, not `OFFSET`
- [ ] Rank shown on the receipt matches rank shown on the board
- [ ] Clicks are buffered and flushed, not incremented per request
- [ ] Ledger-vs-total reconciliation query returns zero rows, and is scheduled
- [ ] Re-crediting a `removed` listing does not restore it

## Load

- [ ] Board endpoint is cached with a short TTL and
      `stale-while-revalidate`
- [ ] Cache is busted on webhook credit
- [ ] Homepage runs no per-visitor query
- [ ] Connection pooler in the connection string (not the direct endpoint)
- [ ] Load-tested at 10× your optimistic guess
- [ ] Webhook path verified to still work while the read path is saturated
- [ ] Static top-100 snapshot written periodically as an outage fallback
- [ ] Analytics degrades by sampling, not by erroring
- [ ] Own visitor/click counters in your own database

## Abuse

- [ ] URL validation rejects non-`http(s)`, credentials, localhost, raw IPs
- [ ] URL locked on first confirmed payment
- [ ] Edits after payment go through review, and are logged with the old value
- [ ] Reputation check (Safe Browsing / URLhaus) on submit and on edit
- [ ] Server-side fetches (favicon, OG) are SSRF-guarded: public-IP check,
      pinned address, redirect cap, size cap, timeout, metadata range blocked
- [ ] Outbound links are `rel="nofollow ugc noopener"`
- [ ] Listing names escaped everywhere, including OG images, receipt emails,
      and the admin view
- [ ] Content-Security-Policy set
- [ ] Rate limits on checkout creation, submissions, and click redirects
- [ ] Hide/remove a listing in one click, from a phone
- [ ] Audit log of every status change, edit, refund and removal

## Published pages

- [ ] Rules: mechanic, minimum, increments, what a bid buys, what it does not
- [ ] Explicit statement that a bid buys an amount, not a position
- [ ] Refund policy, including the exceptions you will honour
- [ ] Content policy and how to report a listing
- [ ] Legal entity name and a monitored contact address
- [ ] Privacy policy
- [ ] Paid placement is obvious on the board itself

## Launch

- [ ] 15–30 real seed listings, no fabricated amounts
- [ ] OG image for the board
- [ ] OG image per listing, showing rank and amount
- [ ] Share button on the success page, pre-filled
- [ ] Mobile layout works — most of your traffic is a tap from a social app
- [ ] Live counters on the board (visitors, listings, total bid)
- [ ] Billing contact visible at checkout
- [ ] You can answer: *if this board vanished tomorrow, who would be annoyed?*
