# 3. Data model and concurrency

The whole schema is three tables. The care goes into which column is
authoritative and how it gets written.

Full annotated version: [`reference/schema.sql`](../reference/schema.sql).

## Ledger first, totals derived

```text
listings   -- one row per thing on the board, with a denormalised total
payments   -- append-only ledger, one row per settled PaymentIntent
webhook_events -- replay guard, one row per Stripe event id
```

`payments` is the truth. `listings.total_cents` is a cache of
`SUM(payments.amount_cents)` that exists so the board can be read with an
index scan instead of an aggregate over everything.

Because it is derived, you can always check it:

```sql
select l.id, l.total_cents, coalesce(sum(p.amount_cents), 0) as ledger
  from listings l
  left join payments p on p.listing_id = l.id
 group by l.id, l.total_cents
having l.total_cents <> coalesce(sum(p.amount_cents), 0);
```

Run that as a scheduled job. It should return zero rows forever. If it ever
does not, you have found a bug in a write path while it is still cheap to fix,
instead of finding it in a dispute.

## One atomic increment, no read-modify-write

The lost-update bug writes itself:

```sql
-- WRONG
select total_cents from listings where id = $1;   -- both read 500
update listings set total_cents = $2 where id = $1; -- both write 1000, $500 vanishes
```

Do not reach for `SELECT ... FOR UPDATE` to patch it. Just never read:

```sql
-- RIGHT
update listings set total_cents = total_cents + $2 where id = $1;
```

Postgres takes the row lock for the duration of the statement. Two payments in
the same millisecond both land, in some order, and the order does not matter
because addition is commutative. There is no lock ordering to reason about and
no deadlock to hit.

## Index the sort you actually run

```sql
create index listings_board_order_idx
  on listings (total_cents desc, first_paid_at asc, id asc)
  where status = 'active';
```

The partial `WHERE` keeps removed and pending rows out of the index entirely,
which matters more than it sounds — most of the board's traffic is one query,
and it should never touch a row it will not render.

## Keyset pagination, never OFFSET

`LIMIT 50 OFFSET 100` assumes the rows below you are holding still. On a live
board they are not: someone pays while a visitor scrolls, everything shifts,
and page 3 shows a listing that was on page 2 while another silently
disappears. Users read this as the board eating listings people paid for.

Page forward from the last row you rendered:

```sql
where status = 'active'
  and total_cents <= :c                    -- redundant, and load-bearing
  and ( total_cents < :c
        or (total_cents = :c and (first_paid_at, id) > (:t, :i)) )
order by total_cents desc, first_paid_at asc, id asc
limit 50
```

Note the directions differ between the two branches because the sort mixes
DESC and ASC — which is why this cannot be collapsed into a single row
comparison, and why the first line matters.

### The redundant line is the whole optimisation

`total_cents <= :c` is implied by the `OR` beneath it. Drop it and the query
returns identical rows. It is still the difference between a seek and a scan,
because the planner cannot derive an index starting position from a bare
`OR` — without it, Postgres starts at the top of the index and filters its way
down to your cursor.

Measured on 200k active listings, paging to roughly position 100,000:

| | Buffers | Rows removed by filter |
| --- | --- | --- |
| Without `total_cents <= :c` | 769 | 100,001 |
| With it | **7** | **1** |

Page 1 is fast either way. That is exactly why this passes review and then
degrades quietly as the board fills up — the query gets slower in proportion
to how deep people scroll, on the day lots of people are scrolling.

If you would rather not carry a redundant predicate, make every sort direction
ascending with a generated column, and a real row comparison seeks directly:

```sql
alter table listings
  add column sort_key bigint generated always as (-total_cents) stored;
create index on listings (sort_key, first_paid_at, id) where status = 'active';
-- ... where (sort_key, first_paid_at, id) > (:k, :t, :i)
```

The same DESC/ASC asymmetry shows up in the "what is my rank" count query;
both are written out in [`reference/schema.sql`](../reference/schema.sql).

## Statuses, and the one rule that must not be buyable

Four states are enough: `pending` (created for checkout, no money yet, not on
the board), `active`, `hidden` (under review), `removed` (taken down).

The important line is in `credit_bid()`:

```sql
status = case when status = 'pending' then 'active' else status end
```

A listing removed for abuse stays removed when more money arrives. If your
credit path unconditionally sets `status = 'active'`, then paying again
un-bans you, and you have built a machine that sells its way past its own
moderation. Someone will notice.

Keep the ledger for removed listings. You will need it to refund, to answer a
dispute, and to reconcile.

## Constrain what you can constrain

Cheap guarantees that cost one line each:

```sql
total_cents  bigint not null default 0 check (total_cents >= 0)
amount_cents bigint not null check (amount_cents > 0)
stripe_payment_intent_id text not null unique
check (status <> 'active' or first_paid_at is not null)
```

That last one means a row can never appear on the board without the timestamp
the sort tiebreak depends on. Constraints are the only part of your validation
that a hotfix at 2am cannot accidentally skip.

## Do not increment a counter per click

Public outbound click counts are a headline feature of the genre, and a viral
board takes orders of magnitude more clicks than bids. `UPDATE listings SET
click_count = click_count + 1` per redirect serialises every visitor behind
one row lock — and it is the *top* listing, the hottest row, that melts first.

Absorb writes into per-minute buckets (`click_buffer` in the reference schema)
or a Redis counter, and flush in batches on a timer. Dedupe by hashed IP +
listing + hour so one person hammering refresh does not inflate a number you
publish as evidence of value.

And publish that number honestly. Inflating click counts on a page where
people are deciding how much money to spend is fraud, not growth hacking.

## Cache the board, bust it on credit

The read:write ratio is roughly 1000:1 and every reader wants the same first
page. Cache the top N as rendered JSON with a short TTL (1–5s) and invalidate
on webhook credit. That one cache is the difference between a $20/month
database and an outage during the exact hour your board is on the front page.

Serve stale rather than erroring under load. A board that is four seconds
behind is fine. A board that 500s while people are trying to pay is not.
