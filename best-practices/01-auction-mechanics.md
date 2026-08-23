# 1. Auction mechanics

The mechanic *is* the product. Everything else on a pay-to-rank board is
plumbing. Get this wrong and no amount of engineering saves it.

## Pick one rule and make it legible in a sentence

outbid.lol's whole rulebook fits on a business card: rank equals total dollars
paid, whole dollars, $5 minimum, nothing is refunded, nothing expires. A
visitor understands the game in about four seconds, which is why they shared
it.

If your rule needs a diagram, you have built a pricing page, not a spectacle.

## Cumulative totals, not "current highest bid"

Two models look similar and behave nothing alike:

| Model | What a bidder pays | What it feels like |
| --- | --- | --- |
| **Cumulative** (outbid.lol) | Every payment adds to your running total | You defend a position by topping up |
| **Highest single bid** | Only your largest payment counts | Your earlier payments evaporate |

Cumulative wins on every axis that matters. It creates repeat purchases from
the same person, it never makes someone feel their earlier money was burned,
and it makes the ledger and the rank the same object. Highest-single-bid
invites "you already have my $200, why do I have to pay $500 not $301" — a
support ticket you cannot win.

## Never promise a rank at checkout

This is the most common correctness bug in the genre, and it is not a race
condition you can lock your way out of.

The obvious flow is: read the current top bid, require the user to beat it,
take the money, put them at #1. But there is a gap of ten seconds to several
minutes between quoting that price and the webhook confirming the payment,
and during a viral spike that gap is precisely when other people are also
paying. When the money lands and the promise is no longer true, you have two
bad options — refund it (you eat the fee, they feel scammed) or keep it and
place them lower than you said (they dispute the charge).

The fix is to stop selling a rank and start selling a contribution:

- Enforce only a **floor** (`amount >= MIN`) at checkout. Nothing else.
- Show "beating #1 right now costs $X" as an explicitly **live, non-binding**
  number, timestamped, that updates while the form is open.
- Let the sort decide placement once the money is real.
- Say it in the rules: *"You are paying an amount, not a position. Your
  position is whatever your total buys when the payment settles."*

`reference/create-checkout.ts` implements exactly this, with the tempting
wrong version left in as a comment.

## Make the sort total and stable

`ORDER BY total_cents DESC` alone is not a sort — it is a partial order, and
Postgres is free to return tied rows in a different sequence on every query.
On a board where dozens of listings sit at exactly $5, that means the page
reshuffles on refresh and keyset pagination duplicates and skips rows.

Add tiebreakers until the order is total:

```sql
ORDER BY total_cents DESC, first_paid_at ASC, id ASC
```

Ties broken by *who got there first* also happens to be the fair answer, and
it is easy to explain.

Then pick one definition of the number you show and use it everywhere. SQL's
`RANK()` ties (two #3s, no #4); the board's row position does not. A receipt
that says #3 next to a board that shows #4 reads as a bug, and bugs about
money become chargebacks.

## Integer cents, one currency

Money is `bigint` cents. No floats anywhere — not in the DB, not in JS, not in
the display formatter's input. `10.10 * 100` is `1009.9999999999999`.

One currency per board. A column you sort by cannot hold mixed units, and
converting at display time means the order changes with the FX rate. If you
need multiple currencies, convert at capture into a single display currency
and store both, or run separate boards.

## Whole dollars are a feature

$5 minimum, $1 increments, no cents. It removes an entire class of input bugs,
it makes every number on the board scannable, and it makes the leaderboard
read like a scoreboard instead of an invoice.

## Variants that actually changed something

By clone #40 the genre had stopped being clones. The ones that got traction
changed the mechanic, not the domain:

- **Lowest unique bid** (`lowbid.lol`) — the winner is the smallest amount
  nobody else picked. Removes the "richest founder wins" feel that makes pure
  bidding read as rigged, and turns the board into a puzzle. Note this edges
  toward games of chance; see [6. Legal and trust](06-legal-and-trust.md).
- **Fixed slots with decay** (`lastspot.lol`) — a capped number of positions
  that expire. Manufactures the urgency a pure leaderboard only has while it
  is trending, and converts one-time payments into recurring ones.
- **Dutch / undercut** — the price to take #1 falls over time until someone
  takes it.
- **Meta-boards** — boards that rank boards. Absurd, and they worked, because
  the audience was already assembled.

Pick a change that alters *who wants to win and why*. A different colour
scheme is not a variant.

## Decide the endgame before you launch

Write down, in the rules, on day zero:

- Does a listing ever expire? (outbid.lol: no.)
- Can someone edit their URL after paying? (See
  [5. Abuse and moderation](05-abuse-and-moderation.md) — the answer should be
  "not without re-review.")
- What happens if you shut the board down?
- Is there a maximum bid? A cap avoids one whale making the board boring, and
  it caps your exposure on a single disputed charge.

These questions all get asked in week one. Answering them in public before
money is on the line costs nothing; answering them afterwards looks like you
are making the rules up to suit yourself.
