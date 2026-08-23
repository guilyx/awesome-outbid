# 4. Surviving the spike

The traffic shape of a board that works is brutal and short: outbid.lol went
from launch to over a million visitors in about two days, and broke its
analytics provider on the way. You get one window. Being down during it is the
only unrecoverable failure mode in the genre, because attention does not come
back.

## Build for one query

Ninety-nine percent of your traffic is anonymous visitors loading the first
page of the board. Optimise that path and nothing else:

- Render the top N server-side into cached HTML or JSON.
- Cache at the edge with a short TTL (1–5 seconds) and a stale-while-revalidate
  window. Four seconds of staleness on a leaderboard is invisible; a 500 is
  not.
- Bust the cache on webhook credit so the payer sees their money land.
- Never issue a per-visitor personalised query on the homepage. No sessions, no
  auth, no "your listings" widget above the fold.

`Cache-Control: public, s-maxage=5, stale-while-revalidate=60` on the board
endpoint does more for survival than any amount of database tuning.

## Keep the paid path independent of the read path

Design so that a board under load can still take money. In practice:

- The checkout endpoint and the webhook endpoint must not depend on the same
  cache, connection pool ceiling, or rate limiter as the homepage.
- Reserve database connections for writes. On serverless, a viral homepage
  will exhaust your pool and your webhook handler will start returning 500s —
  which Stripe retries, which is survivable, but you will be reconciling by
  hand for a week.
- Use a pooler (PgBouncer, Supabase pooler, Neon's pooled endpoint). Serverless
  functions plus direct Postgres connections is the classic way to fall over
  at exactly the wrong moment.

If you must shed load, shed reads. Serving a cached board from five minutes
ago while payments keep clearing is a good day. The inverse is not.

## Realtime: pick the boring option

The genre's signature moment is watching your rank move. You do not need
WebSockets for that.

| Approach | Reality |
| --- | --- |
| Poll a cached endpoint every 3–5s | Works everywhere, survives serverless, costs nothing extra. Start here |
| Server-Sent Events | Good fit — the stream is one-directional. But long-lived connections and serverless platforms fight each other, and there are per-instance connection caps |
| WebSockets | Most operational surface, least payoff for a read-only firehose |
| Postgres `LISTEN`/`NOTIFY` fan-out | Elegant until every serverless instance holds a listener connection |

A 3-second poll against an edge-cached endpoint is indistinguishable from
realtime to a human watching a leaderboard, and it degrades into "slightly
stale" instead of "disconnected" under load.

If you do use SSE, cap concurrent connections, send heartbeats, and have the
client fall back to polling on failure rather than reconnect-storming you.

## Analytics that will not be the thing that breaks

Being the person whose analytics provider fell over is a fun tweet and a real
loss — you lose the traffic data from the only hours that mattered.

- Prefer a provider that ingests via a queue, or self-host something that
  degrades by dropping samples rather than by erroring.
- Sample aggressively above a threshold rather than dropping to zero.
- Keep your own minimal counters in the database (total visitors, clicks per
  listing) so you are never fully blind, and so the numbers you publish on the
  board come from a source you control.
- Never let an analytics script block render or a failing beacon break the
  page.

## Images are your bandwidth bill

Every listing has a favicon or OG image, and the board renders hundreds of
them at once.

- Fetch and re-host on submission; never hotlink someone's origin from a page
  taking a million views. You will take down their site and yours.
- Resize to display size, serve WebP/AVIF, set long cache headers.
- Fetch through a validated, timeout-capped, size-capped, redirect-capped
  client — see the SSRF notes in
  [5. Abuse and moderation](05-abuse-and-moderation.md).
- Have a placeholder for failures and cache the failure, so a dead favicon
  does not get retried on every render.

## Rate limits in the three places that matter

- **Checkout creation** — per IP. Prevents carding and stops a script from
  filling your database with `pending` listings.
- **Outbound click redirects** — per IP per listing. Protects the counter you
  publish as evidence of value.
- **Submission form** — per IP. Spam listings are cheap to post and expensive
  to moderate.

Do not rate-limit the webhook endpoint. That is Stripe, and throttling it just
moves your problems three days into the future.

## Have a static fallback

Write the top 100 to a flat JSON file or object storage every minute. If the
database is unreachable, serve that with a banner saying the board is showing
a cached snapshot. It takes an hour to build and it converts your worst
possible outage into a mild embarrassment.

## Before you launch

- Load-test the board endpoint at 10× your optimistic guess. It is one URL;
  there is no excuse for not knowing this number.
- Know your database's connection ceiling and your platform's concurrency
  limit, and confirm the pooler is actually in the connection string.
- Verify the webhook path works when the read path is saturated.
- Set an alert on webhook 5xx rate and on the ledger-vs-total reconciliation
  query from [3. Data model](03-data-model.md#ledger-first-totals-derived).
