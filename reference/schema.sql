-- Reference Postgres schema for a pay-to-rank board.
--
-- Design rules this schema encodes:
--   1. Money is integer cents. Never floats, never client-supplied.
--   2. Rank is derived from an append-only ledger, never from a mutable
--      "current bid" column that racing writers read-modify-write.
--   3. Every write path is idempotent, because Stripe delivers webhooks
--      at least once and will retry for up to three days.
--   4. The board sort is total, deterministic and stable, so pagination
--      does not duplicate or skip rows while the board is moving.
--
-- Tested against Postgres 14+.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- listings
-- ---------------------------------------------------------------------------

create table listings (
  id             uuid primary key default gen_random_uuid(),
  slug           text        not null unique,
  name           text        not null check (length(name) between 1 and 60),
  target_url     text        not null,
  kind           text        not null default 'product'
                             check (kind in ('product', 'profile')),

  -- pending : created for checkout, no confirmed money yet. Not on the board.
  -- active  : has confirmed money. On the board.
  -- hidden  : temporarily off the board (under review).
  -- removed : permanently off the board (takedown). Keeps its ledger.
  status         text        not null default 'pending'
                             check (status in ('pending', 'active', 'hidden', 'removed')),

  -- Denormalised sum of payments.amount_cents. Maintained only by
  -- credit_bid() below, always as a single atomic increment.
  total_cents    bigint      not null default 0 check (total_cents >= 0),

  -- Flushed in batches from click_buffer. Never incremented per request.
  click_count    bigint      not null default 0 check (click_count >= 0),

  first_paid_at  timestamptz,
  created_at     timestamptz not null default now(),

  -- Set on first confirmed payment. After this, target_url changes go back
  -- through review: paying for a clean URL and then swapping it for a
  -- phishing page is the single most common attack on these boards.
  url_locked_at  timestamptz,

  -- A listing can only be on the board if it has a paid-at timestamp, which
  -- is what the sort tiebreak depends on.
  constraint active_listings_are_paid
    check (status <> 'active' or first_paid_at is not null)
);

-- The board sort, as an index. total_cents desc, then oldest-first, then id
-- as a final total tiebreak so the order is fully deterministic.
create index listings_board_order_idx
  on listings (total_cents desc, first_paid_at asc, id asc)
  where status = 'active';

-- ---------------------------------------------------------------------------
-- payments  (append-only ledger)
-- ---------------------------------------------------------------------------

create table payments (
  id                       uuid        primary key default gen_random_uuid(),
  listing_id               uuid        not null references listings(id),

  -- The idempotency anchor. One PaymentIntent credits a listing exactly once,
  -- no matter how many webhook events describe it.
  stripe_payment_intent_id text        not null unique,
  stripe_session_id        text        unique,

  amount_cents             bigint      not null check (amount_cents > 0),
  currency                 text        not null default 'usd',
  created_at               timestamptz not null default now()
);

create index payments_listing_idx on payments (listing_id, created_at desc);

-- ---------------------------------------------------------------------------
-- webhook_events  (event-level replay guard)
-- ---------------------------------------------------------------------------

create table webhook_events (
  stripe_event_id text        primary key,
  type            text        not null,
  received_at     timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- credit_bid()
-- ---------------------------------------------------------------------------
--
-- The only function allowed to move money onto the board. Returns true if it
-- credited, false if this payment was already credited.
--
-- Both gates matter and they are not redundant:
--   * webhook_events catches Stripe redelivering the *same* event.
--   * payments.stripe_payment_intent_id catches *different* events describing
--     the same money (checkout.session.completed and
--     payment_intent.succeeded both carry the same PaymentIntent).
--
-- Callers must run this in a single transaction. In autocommit clients a
-- plpgsql function body is already one transaction, which is the point:
-- either the guard row and the credit both land, or neither does.

create or replace function credit_bid(
  p_event_id          text,
  p_event_type        text,
  p_listing_id        uuid,
  p_payment_intent_id text,
  p_session_id        text,
  p_amount_cents      bigint,
  p_currency          text default 'usd'
) returns boolean
language plpgsql as $$
declare
  v_rows int;
begin
  if p_amount_cents is null or p_amount_cents <= 0 then
    raise exception 'credit_bid: non-positive amount %', p_amount_cents;
  end if;

  insert into webhook_events (stripe_event_id, type)
  values (p_event_id, p_event_type)
  on conflict (stripe_event_id) do nothing;

  get diagnostics v_rows = row_count;
  if v_rows = 0 then
    return false;  -- event already processed
  end if;

  insert into payments (
    listing_id, stripe_payment_intent_id, stripe_session_id,
    amount_cents, currency
  )
  values (
    p_listing_id, p_payment_intent_id, p_session_id,
    p_amount_cents, p_currency
  )
  on conflict (stripe_payment_intent_id) do nothing;

  get diagnostics v_rows = row_count;
  if v_rows = 0 then
    return false;  -- this money is already on the board
  end if;

  -- One atomic increment. No SELECT ... then UPDATE, so there is no lost
  -- update to lose and no lock ordering to get wrong. Two people paying in
  -- the same millisecond both land.
  --
  -- Note the status CASE: a listing taken down for abuse stays down even if
  -- more money arrives. Money does not buy its way back onto the board.
  update listings
     set total_cents   = total_cents + p_amount_cents,
         first_paid_at = coalesce(first_paid_at, now()),
         url_locked_at = coalesce(url_locked_at, now()),
         status        = case when status = 'pending' then 'active' else status end
   where id = p_listing_id;

  -- Backstop. In practice the foreign key on payments.listing_id rejects an
  -- unknown listing before this runs; keeping the check means a clearer error
  -- if that FK is ever dropped for a migration.
  get diagnostics v_rows = row_count;
  if v_rows = 0 then
    raise exception 'credit_bid: unknown listing %', p_listing_id;
  end if;

  return true;
end;
$$;

-- ---------------------------------------------------------------------------
-- click_buffer  (write-absorbing counter)
-- ---------------------------------------------------------------------------
--
-- A viral board takes far more outbound clicks than bids. Incrementing
-- listings.click_count per request serialises every reader behind one row
-- lock. Absorb into per-minute buckets, flush on a timer.

create table click_buffer (
  listing_id uuid        not null references listings(id),
  bucket     timestamptz not null,
  clicks     bigint      not null default 0,
  primary key (listing_id, bucket)
);

-- Per redirect (better still: buffer in Redis and write one row per flush):
--   insert into click_buffer (listing_id, bucket, clicks)
--   values ($1, date_trunc('minute', now()), 1)
--   on conflict (listing_id, bucket) do update
--     set clicks = click_buffer.clicks + 1;

create or replace function flush_clicks() returns void
language sql as $$
  with drained as (
    delete from click_buffer
     where bucket < date_trunc('minute', now())
    returning listing_id, clicks
  ), totals as (
    select listing_id, sum(clicks) as clicks
      from drained
     group by listing_id
  )
  update listings l
     set click_count = l.click_count + t.clicks
    from totals t
   where l.id = t.listing_id;
$$;

-- ---------------------------------------------------------------------------
-- Reading the board
-- ---------------------------------------------------------------------------
--
-- Page 1:
--
--   select id, slug, name, total_cents, click_count, first_paid_at,
--          rank() over (order by total_cents desc) as display_rank
--     from listings
--    where status = 'active'
--    order by total_cents desc, first_paid_at asc, id asc
--    limit 50;
--
-- Page N -- keyset, not OFFSET. OFFSET on a board that is being reordered
-- mid-scroll shows the same listing twice and silently drops others. Pass the
-- last row of the previous page as :c / :t / :i.
--
--   select id, slug, name, total_cents, click_count, first_paid_at
--     from listings
--    where status = 'active'
--      and total_cents <= :c                     -- SEEK PREDICATE, see below
--      and (
--        total_cents < :c
--        or (total_cents = :c and (first_paid_at, id) > (:t, :i))
--      )
--    order by total_cents desc, first_paid_at asc, id asc
--    limit 50;
--
-- That `total_cents <= :c` line is logically redundant -- it is implied by the
-- OR below it -- and it is the difference between a seek and a scan.
--
-- The planner cannot derive an index starting position from a bare OR, so
-- without it Postgres starts at the top of the index and filters its way down
-- to your cursor. Measured on 200k active listings, page ~2000:
--
--   without the seek predicate:  769 buffers, 100,001 rows removed by filter
--   with it:                       7 buffers,       1 row  removed by filter
--
-- Page 1 is fast either way, which is exactly why this survives review and
-- then degrades as the board grows.
--
-- The redundancy is only needed because the sort mixes DESC and ASC, which
-- rules out a single row comparison. If you would rather not carry it, add a
-- generated column and make every direction ascending:
--
--   alter table listings
--     add column sort_key bigint generated always as (-total_cents) stored;
--   create index on listings (sort_key, first_paid_at, id) where status = 'active';
--
-- then `(sort_key, first_paid_at, id) > (:k, :t, :i)` is one row comparison
-- and Postgres seeks on it directly.
--
-- One listing's rank, without pulling the board into the app. "Ahead of me"
-- means more money, or the same money and got there first -- note the
-- directions differ, so this cannot be written as a single row comparison.
--
--   with me as (
--     select total_cents, first_paid_at, id from listings where id = :id
--   )
--   select count(*) + 1 as rank
--     from listings l, me
--    where l.status = 'active'
--      and (
--        l.total_cents > me.total_cents
--        or (l.total_cents = me.total_cents
--            and (l.first_paid_at, l.id) < (me.first_paid_at, me.id))
--      );
--
-- Note that rank() ties on equal totals (two #3s, no #4), while the board
-- order breaks the tie by who paid first. Pick one and use it everywhere --
-- a receipt that says #3 next to a board that shows #4 reads as a bug and
-- turns into a chargeback.
