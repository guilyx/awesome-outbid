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

**📖 Read it as a site: <https://guilyx.github.io/awesome-outbid/>**
— the same content with a searchable, filterable board directory.

## Contents

- [Start here](#start-here)
- [Reference implementation](#reference-implementation)
- [The ten rules](#the-ten-rules)
- [The original](#the-original)
- [The boards](#the-boards)
- [Boilerplates and tooling](#boilerplates-and-tooling)
- [Writeups and analysis](#writeups-and-analysis)
- [Anti-patterns](#anti-patterns)
- [Contributing](#contributing)
- [The site](#the-site)
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

## The boards

Grouped by what each one actually changed — the mechanic, the audience, or the
unit ranked. A different domain is not a variant, which is why clone forty's
traffic curve is flat.

Source of truth is [`data/boards.yml`](data/boards.yml); the tables below and the
[site's board directory](https://guilyx.github.io/awesome-outbid/boards/) are both
generated from it by `scripts/build.py`, and CI fails if they drift. Browse it
with search and filters [on the site](https://guilyx.github.io/awesome-outbid/boards/).

<!-- BEGIN GENERATED BOARDS -->

<!-- Generated from data/boards.yml by scripts/build.py. Do not edit by hand. -->

Snapshot: **2026-08-23** · **29** boards described · **25** named only.

Compiled from press coverage, the clone directories, and search results indexing X posts from the launch week. x.com itself could not be read directly, so quoted numbers are those the sources report, not figures we measured.

### The original

The board that started it, and its own rulebook.

| Board | Ranks | What it does |
| --- | --- | --- |
| [outbid.lol](https://outbid.lol) | products, apps and X profiles | Rank equals total dollars paid, cumulatively. Whole dollars, $5 minimum, $1 increments, $999,999 cap. Nothing expires, nothing is refunded, and taking #1 costs at least $5 more than the current top bid. No accounts, no ads, no revenue share. *by Jonathan Wilke* *(2026-08-19)* |

### Pure cumulative bidding

The original mechanic, re-domained. Rank is total dollars paid, nothing expires. Also the group with the flattest traffic curves — see guide 07.

| Board | Ranks | What it does |
| --- | --- | --- |
| [uprank.lol](https://www.uprank.lol) | websites | Your rank is your lifetime total and anyone can pay a dollar more to take it. The first spot cost $1; each new #1 costs $1 more than the last. |
| [overbid.lol](https://www.overbid.lol) | products | Overbid everyone and take #1. No ads, no API keys, no revenue share -- the original's positioning, near-verbatim. |
| [whynotalso.bid](https://whynotalso.bid) | anything | A live leaderboard where you bid real dollars to climb the rankings. |
| [bidwall.lol](https://bidwall.lol) | companies | Framed as a digital billboard rather than a leaderboard: position is bought, not given. Pay what you like and hold the rank until someone pays more. |
| [puremoney.lol](https://puremoney.lol) | listings | A permanent pay-to-rank leaderboard — placements do not expire. |
| [outrank.lol](https://www.outrank.lol) | listings | Pay to be #1. The mechanic with the marketing stripped out. |
| [outbid-lol.com](https://outbid-lol.com) | listings | Bid your way to the top. Notable mainly as the near-miss domain play on the original. |

### Decay and time pressure

A bid is a balance that drains, so #1 comes back into reach. Converts one-time payments into recurring ones and manufactures the urgency a static board only has while trending.

| Board | Ranks | What it does |
| --- | --- | --- |
| [lastspot.lol](https://lastspot.lol) | products | A 100-slot board where payments set a live value, repeat payments top it up, and every value drops 5% a day. Also maintains an "Outbid & friends" list. |
| [rankwars.lol](https://rankwars.lol) | sites and X handles | Highest bid wins #1, from $5. The first 24 hours are shielded, then your value decays until someone outbids you — so the war never stops. Outbid or top up to climb. |
| [topple.lol](https://topple.lol) | products | A bid is a balance that drains with time *and* with every click it earns, so the top spot comes back into reach instead of climbing out of it. Also publishes a live tracker of what #1 on outbid.lol currently costs. |

### Inverted auctions

Lowest unique bid, or undercutting. Removes the richest-founder-wins feel — and can edge into gambling law. See guide 06.

| Board | Ranks | What it does |
| --- | --- | --- |
| [lowbid.lol](https://lowbid.lol) | products | Lowest unique bid takes the top, Dutch-style undercutting below it. Turns the board into a puzzle and removes the richest-founder-wins feel. Also the variant most likely to be a game of chance in your jurisdiction. |

### Maps and territory

Position becomes a place instead of a row number. Scarcity is built into the geography rather than the price.

| Board | Ranks | What it does |
| --- | --- | --- |
| [warmap.lol](https://warmap.lol) | companies, by country | Your company colour appears on the world map until someone pays 1.5x to take it from you. No refunds. The multiplier is the whole design. |
| [mapbid.lol](https://mapbid.lol) | countries | Outbid the competition to claim the #1 sovereign spot in any country on an interactive world map. 190-odd #1 spots instead of one. |

### Different unit ranked

Same mechanic, different audience. The most durable direction, because a niche brings its own buyers.

| Board | Ranks | What it does |
| --- | --- | --- |
| [xbid.lol](https://xbid.lol) | X accounts | A public leaderboard of X accounts ranked by one thing — how much you have paid to be on it. |
| [topnewsletters.lol](https://www.topnewsletters.lol) | newsletters | Bid for the inbox. Your amount decides the rank, and paying under the #1 price still places you wherever that bid can reach. |
| [topseos.lol](https://topseos.lol) | SEO experts, agencies and apps | A pay-to-rank leaderboard for the SEO industry, aimed at its own buyers. |
| [vibewar.lol](https://vibewar.lol) | vibecoded apps and SaaS | A battlefield for vibecoded apps and SaaS. Founders pay to rank; you outbid them to take their spot. |
| [pujalo.lol](https://pujalo.lol) | products, LATAM | The LATAM edition — Spanish, and pesos. The clearest example of the one clone direction that reliably works: same mechanic, an audience the original was never going to reach. |

### Other currencies and stunts

Boards where the thing you spend is not a bid, or the thing you win is not a row.

| Board | Ranks | What it does |
| --- | --- | --- |
| [payluck.lol](https://payluck.lol) | listings | Randomised coupon codes against locked prices on a limited board. Cost is capped and known upfront and your position cannot be outbid — which also means the only variable left is whether the site itself gets any attention. |
| [outlike.lol](https://www.outlike.lol) | sites | Likes are the only currency — the most-liked announcement tweet holds #1, and listing is free. The one board in the wave that takes no money at all. |
| [lamborghini.lol](https://lamborghini.lol) | panels on a physical car | SaaS companies buy panel space on a real Lamborghini Urus. Bid $50k, wear a quarter of the car. The mechanic applied to an object rather than a row. |

### Meta — boards and directories of boards

The layer that appeared within days. Absurd, and it worked, because the audience was already assembled.

| Board | Ranks | What it does |
| --- | --- | --- |
| [outbidstory.lol](https://outbidstory.lol) | the wave itself | A hand-updated live directory of the bid-site wave, which is itself bidding out its own spots. Free to read and independent. |
| [outbidception.lol](https://www.outbidception.lol) | pay-to-rank leaderboards | A leaderboard of pay-to-rank leaderboards, ranked by how much they pay. |
| [biddirectory.lol](https://biddirectory.lol) | bid sites | A directory of bidding sites, ranked by bid. *by Damon Chen* |
| [outbid.fyi](https://outbid.fyi) | clones, by quality | Lists the copycats, cheap clones, ghost towns and weird map ones. Three seats at the top are for sale, on the one rule the genre runs on. |
| [leadingboards.lol](https://www.leadingboards.lol) | bid-based leaderboards | A directory of bid-based leaderboard sites. Free to list, pay to be featured — the freemium version of the mechanic. |
| [outoutbid.lol](https://outoutbid.lol) | every outbid.lol clone | Groups the clones by what they rank rather than by bid. |
| [biddingarena.com](https://biddingarena.com/boards) | boards, live and dead | The largest tracker of the wave, and the only one that says which boards are still up. |

### Named only

Domains named in launch-week roundups with no description we could
source. Listed so the record is complete; we do not invent mechanics to
fill the gap. Know one? A sourced description promotes it into the
tables above — see [CONTRIBUTING.md](CONTRIBUTING.md).

`topx.lol`, `tweetbid.lol`, `xme.lol`, `dontbid.lol`, `undercut.lol`, `upbid.lol`, `outbids.lol`, `rankbid.lol`, `bidanything.lol`, `whosetheboss.lol`, `claimrank.lol`, `watchbid.lol`, `takeone.lol`, `spots.lol`, `landgrab.lol`, `bidfast.lol`, `aistartups.lol`, `bidking.lol`, `bidding.lol`, `tinybid.lol`, `iamtherichest.lol`, `indiehackers.lol`, `outflex.lol`, `ranky.lol`, `topspot.so`

> **On these links.** This is a snapshot of a genre that moved in days;
> entries are community-submitted and unverified. Domains in this space go
> dark quickly, and every one of them takes non-refundable money from
> strangers. Listing a board here is not an endorsement, a safety check, or
> advice to bid on it.

<!-- END GENERATED BOARDS -->

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

## The site

<https://guilyx.github.io/awesome-outbid/> is built from this repo — no CMS, no
framework, one stylesheet, no runtime dependencies.

```sh
pip install pyyaml markdown
python3 scripts/build.py        # regenerate the README section + build _site/
python3 scripts/check_site.py   # every internal link and anchor resolves
python3 -m http.server -d _site 8000
```

`scripts/build.py --check` is what CI runs: it fails if `data/boards.yml` and the
README's board tables have drifted, so neither can be edited without the other.

## Disclaimer

Nothing here is legal, financial, or tax advice. Pay-to-rank boards take
non-refundable payments from consumers, publish user-submitted links, and sit
in a payments-risk category that gets accounts terminated. If yours is making
real money, talk to a lawyer and to your payment processor.

## License

[CC0 1.0](LICENSE) — public domain. Take it, ship it, no attribution needed.
