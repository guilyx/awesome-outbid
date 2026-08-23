# 8. After the spike

Launch week is the easy part and it is over in about 72 hours. This file is
about the other 51 weeks, which almost nobody in the August 2026 wave planned
for.

## The decay is the default, not a failure

Revenue on a pay-to-rank board is a direct function of attention, and attention
from a viral moment decays fast. The board does not slowly plateau; it drops.

Concretely, expect:

- Bid volume to fall by an order of magnitude within two weeks.
- Click counts per listing to fall further and faster than visitor counts,
  because the remaining traffic is less curious.
- The top few bidders to keep paying for a while and then stop, because they
  can see their own click counter.

None of this means you did something wrong. It means you have to decide what
the board is once the spectacle ends.

## Tell bidders the truth about the traffic

Someone paying $500 today is pricing against numbers they saw on your homepage.
If those numbers are three weeks stale, you are selling something you no longer
have.

- Publish a rolling traffic figure — last 7 days, not since-launch. A
  since-launch counter is honest on day two and misleading on day sixty.
- Keep per-listing click counts public and current. They are the bidder's own
  measurement of what your board is worth, which is exactly why they should
  stay visible when the answer gets less flattering.
- Consider showing a traffic trend on the submission page. Bidders who go in
  informed do not file disputes.

This costs you some bids. It is still the right call: the alternative is
selling placement on a dead page, which is the accusation the whole genre is
most vulnerable to.

## Three honest endgames

**1. Sunset it.** Say so in advance, stop taking new bids, and leave the board
up read-only and permanently. People paid for a public placement; deleting it
is both a wave of chargebacks and the end of your credibility for whatever you
launch next. Keep the domain, keep redirects working, keep the billing address
monitored for a few months.

**2. Sell it.** Offers arrive fast for boards that work. Know what is actually
being sold — a decaying attention asset with an open payments-risk position,
not recurring revenue. Make sure the buyer takes on the takedown obligations
and the outstanding disputes, and tell existing bidders who now runs the board.

**3. Convert it into something durable.** The hardest and the only one with a
future. The board gave you an audience and a category; the question is whether
there is a reason to come back. Directories that survive give people something
to *find*, not something to *watch*. If you go this way, do it while you still
have traffic to convert, not after.

Picking none of these is itself a choice: a board nobody maintains, still
taking payments, with an unmonitored abuse inbox. That is how a fun project
turns into a liability.

## The obligations do not decay with the revenue

For as long as the board is up and has ever taken money:

- **The abuse inbox stays monitored.** A top listing can be compromised months
  later, and yours is the page sending traffic to it.
- **Disputes arrive late.** Cardholders generally have 120 days, sometimes
  more. Keep receipts, ledger, and evidence for at least a year, and keep
  enough in the account to cover them.
- **Refund exceptions still apply.** Duplicate charges and legally required
  refunds do not expire because the hype did.
- **Someone must be able to take a listing down.** If that is a SQL client on
  a laptop you no longer own, fix it now.

## Reconcile before you stop paying attention

Run the ledger-vs-total check from
[3. Data model](03-data-model.md#ledger-first-totals-derived) one more time,
sweep abandoned `pending` listings, confirm every settled PaymentIntent in
Stripe has a matching `payments` row, and confirm the reverse. Do it while you
still remember how the code works.

The failure you are looking for is money that arrived and never got placed —
someone paid and is quietly wondering why they are not on the board.

## What to write down before you move on

A short post-mortem is worth more than the board:

- The traffic curve, with dates.
- Revenue by day, and the decay rate.
- Dispute rate and what caused each one.
- What broke under load, and what you would build differently.

The genre produced hundreds of boards and very few honest write-ups of what
happened after week one. That gap is worth more to the next builder than
another clone.
