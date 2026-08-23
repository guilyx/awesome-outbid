# 7. Launch and distribution

The code is a weekend. outbid.lol was three hours on top of an existing
boilerplate. What made it $139k was not the code, and cloning the code
reproduces the cheap half.

## What bidders are actually buying

Not a row on a leaderboard. Attention — the specific, measurable attention
that board sends to their link this week.

Which means your board's value to a bidder is a direct function of your
traffic, and a board with no traffic is a page with a payment button on it.
This is why clone #40 with a fresh domain earns nothing: the mechanic
transfers, the audience does not.

Everything below follows from that.

## An empty board converts at zero

Nobody wants to be the first name on a list of one. Before you tell anyone:

- Seed 15–30 real listings. Your own projects, friends' projects, things you
  genuinely like — with permission, and with the seeding disclosed if the
  amounts are not real money.
- Make sure the top few rows look like a real contest, not a placeholder.
- Never fake bid amounts. It is the one lie that destroys the whole premise,
  it is trivially caught by anyone comparing the board to the ledger, and it
  is fraud.

## Make every bidder a distributor

The highest-leverage feature on a board of this kind is a per-listing share
asset. Someone who just paid to be #1 *wants* to tell people. Give them
something worth posting:

- A dynamically generated OG image per listing: name, rank, amount, board
  branding. Rendered server-side, cached, regenerated on rank change.
- A permalink at `/l/{slug}` that renders that image and links back.
- A "share" button on the success page, pre-filled, shown at the exact moment
  of maximum enthusiasm.

Every bid then produces a post, that post produces visitors, visitors make the
board worth bidding on, and that loop is the entire business. Boards without it
have to buy attention. Boards with it are given it.

## Build in public with real numbers

The genre's growth engine is the revenue screenshot. It is not vanity — a
public, verifiable number is the proof a stranger needs before sending you
money, and it is the thing that gets reposted.

- Post the counter, the milestones, the traffic graph, the mistakes.
- Publish live stats on the board itself: visitors, listings, total bid,
  people online. outbid.lol showing "1,080 online, 1,170,900 visitors" is not
  decoration; it is the pitch.
- Reply to everyone during the window. The window is roughly 72 hours.

Then keep publishing when the numbers fall. Bidders who were told the truth
about a slowdown come back; ones who found out by watching their click counter
do not.

## Ship the launch-day essentials, skip the rest

Have on day one:

- OG images (board and per-listing) — you are about to be linked everywhere.
- A working mobile layout. Most of the traffic is people tapping a link in a
  social app.
- Live-updating counters. The spectacle is watching numbers move.
- Public click counts per listing. This is what makes the spend feel legible.
- A billing contact address, visible.
- The rules page.

Do not have on day one: accounts, dashboards, subscriptions, an API, referral
programmes, revenue sharing (see the payout-hold warning in
[2. Payments](02-payments.md#expect-a-hold-and-do-not-promise-money-you-cannot-move)),
or an admin panel more elaborate than a hide button.

## If you are cloning, change the audience — not the domain

A pure clone competes with the original on the original's strongest asset:
everyone is already looking there. The variants that survived the August 2026
wave earned their own reason to gather.

Directions that worked:

- **A niche with its own buyers.** A board for one industry, one region, one
  professional community. Smaller traffic, but traffic that converts for the
  bidder — and bidders can tell the difference within a week.
- **A different mechanic.** Lowest unique bid, decaying slots, undercutting.
  See [1. Auction mechanics](01-auction-mechanics.md#variants-that-actually-changed-something)
  — and check [6. Legal and trust](06-legal-and-trust.md#keep-it-deterministic-or-you-may-be-running-a-lottery)
  before you build a chance-based one.
- **A different unit.** Rank people, songs, cities, open-source projects,
  job listings. The mechanic is generic; the object changes who shows up.
- **The meta-layer.** Directories of boards, and boards that rank boards, both
  worked — because the audience was already assembled.

The honest test: if your board vanished tomorrow, would anyone be annoyed? If
the answer is no, you are selling launch-week curiosity, and that is a
three-day business.

## Have the acquisition conversation ready

A board that works gets an offer fast — outbid.lol had a six-figure one inside
24 hours. Know in advance what you would say, and know that the thing being
valued is a decaying attention asset with a payments-risk profile attached, not
an ARR multiple. That is not a reason to say no. It is a reason not to
improvise the number.
