# Awesome Outbid [![Awesome](https://awesome.re/badge-flat2.svg)](https://awesome.re)

> Every pay-to-rank board from the [outbid.lol](https://outbid.lol) wave, and what
> each one actually changed.

**➜ [Browse the list on the site](https://guilyx.github.io/awesome-outbid/)** —
searchable, filterable, grouped by mechanic.

outbid.lol turned a three-hour build into **$139,041 in 65 hours**, 1.1M visitors
and a few hundred clones. This is the field guide to all of them — plus eight
guides on building one that survives contact with real money.

**Adding a board is one file:** edit [`data/boards.yml`](data/boards.yml) and open a
PR. The tables below, the site, and the contributors wall all regenerate
themselves. See [CONTRIBUTING.md](CONTRIBUTING.md).

## The boards

Grouped by what each one changed — the mechanic, the audience, or the unit
ranked. A different domain is not a variant, which is why clone forty's traffic
curve is flat.

<!-- BEGIN GENERATED BOARDS -->

<!-- Generated from data/boards.yml by scripts/build.py. Do not edit by hand. -->

Snapshot: **2026-08-23** · **33** boards described · **25** named only.

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
| **NSFW** [topless.lol](https://topless.lol) | adult creator links | The adult-creator edition — OnlyFans, Fansly and fan-page links instead of startups. Two things differ from the original: every rank is a distinct dollar amount, so a bid that is already taken is refused rather than tie-broken by timestamp, and the board is quoted in USD while Brazilian buyers are charged in BRL at a fixed rate. *(2026-08-24)* |
| [pujalo.lol](https://pujalo.lol) | products, LATAM | The LATAM edition — Spanish, and pesos. The clearest example of the one clone direction that reliably works: same mechanic, an audience the original was never going to reach. |
| [bidboard.games](https://bidboard.games) | game sites, servers, wikis and tools | The games edition — playable games, servers, guide sites, wikis and game tools, in thirty categories. The listing total is capped at $500, so the top of the board cannot be bought outright; below that it is the original mechanic, payments accumulate and nothing expires, and anything listed in the last 24 hours holds a guaranteed row whatever it paid. |

### Other currencies and stunts

Boards where the thing you spend is not a bid, or the thing you win is not a row.

| Board | Ranks | What it does |
| --- | --- | --- |
| [payluck.lol](https://payluck.lol) | listings | Randomised coupon codes against locked prices on a limited board. Cost is capped and known upfront and your position cannot be outbid — which also means the only variable left is whether the site itself gets any attention. |
| [outlike.lol](https://www.outlike.lol) | sites | Likes are the only currency — the most-liked announcement tweet holds #1, and listing is free. The one board in the wave that takes no money at all. |
| [lamborghini.lol](https://lamborghini.lol) | panels on a physical car | SaaS companies buy panel space on a real Lamborghini Urus. Bid $50k, wear a quarter of the car. The mechanic applied to an object rather than a row. |
| [isopod.lol](https://isopod.lol) | advertising plates on a mascot | Eight fixed plates live on one isopod instead of a ranked list. Each plate can be stolen for its last paid price plus $10 during a 14-day season, then the final owners remain on the mascot for 90 days. *by @SX0OT* |

### Earned multipliers

Money sets the floor and referred visitors multiply it, so a small payment that brings an audience outranks a large one that brings none. The only direction where the listings themselves supply the board's traffic rather than the operator having to.

| Board | Ranks | What it does |
| --- | --- | --- |
| [outnumber.lol](https://outnumber.lol) | products, apps and X profiles | Rank is the amount paid multiplied by the unique visitors the listing itself referred, so $10 that brought 200 people outranks $25 that brought nobody. Every 100 referred visitors adds 1x, capped at 3x, and money alone cannot reach the top. A visitor counts once per listing forever, crawlers and link previews never count, and a listing can bank at most 250 a day. *(2026-08-24)* |

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

## Building one?

Eight guides, ordered so each builds on the last — the auction rule you pick in
01 decides the schema in 03, and the schema is what makes the webhook in 02 safe.

| # | Guide | # | Guide |
| --- | --- | --- | --- |
| 01 | [Auction mechanics](best-practices/01-auction-mechanics.md) | 05 | [Abuse and moderation](best-practices/05-abuse-and-moderation.md) |
| 02 | [Payments and webhooks](best-practices/02-payments.md) | 06 | [Legal and trust](best-practices/06-legal-and-trust.md) |
| 03 | [Data model and concurrency](best-practices/03-data-model.md) | 07 | [Launch and distribution](best-practices/07-launch-and-distribution.md) |
| 04 | [Surviving the spike](best-practices/04-scale-and-realtime.md) | 08 | [After the spike](best-practices/08-after-the-spike.md) |

The [index](best-practices/README.md) also carries the anti-pattern table, the
tooling list and the writeups.

**[`reference/`](reference/)** has the patterns as annotated code — an idempotent
Postgres schema verified against Postgres 16, a Stripe webhook handler and
checkout route that typecheck under `strict`, and a
[pre-launch checklist](reference/pre-launch-checklist.md).

## Disclaimer

Nothing here is legal, financial, or tax advice, and nothing in the list is
vetted or endorsed. Pay-to-rank boards take non-refundable payments from
consumers, publish user-submitted links, and sit in a payments-risk category that
gets accounts terminated. If yours is making real money, talk to a lawyer and to
your payment processor.

## License

[CC0 1.0](LICENSE) — public domain. Take it, ship it, no attribution needed.
