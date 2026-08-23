# 6. Legal and trust

> **Not legal advice.** This is a checklist of the issues that come up, written
> by engineers. Rules vary enormously by country, and you are taking money from
> strangers in many of them. If your board is making real money, an hour with a
> lawyer is the cheapest thing you will buy.

## Say it is paid placement, in those words

You are selling ranking. That is advertising. The failure mode is not saying
so — a board that presents purchased position with the visual grammar of an
editorial "top products" list is making a claim about merit that it cannot
support.

Advertising regulators in most markets require paid placement to be
identifiable as paid. In the US the FTC's endorsement and native-advertising
guidance is the reference point; the UK, EU and Australia have close
equivalents.

In practice this is easy, and the genre already gets it right:

- The name of the game is in the name of the site.
- Bid amounts are shown on every row.
- The rules page says rank equals dollars in one sentence.

Keep it that way. Do not add "featured", "editor's pick", "verified" or a
star rating unless it means something independent of payment.

## Keep it deterministic, or you may be running a lottery

"Highest total payment ranks highest" has no element of chance. Everyone can
see the price to win and can choose to pay it. That is a sale, not a game of
chance.

Mechanics that introduce randomness or prizes can move you into gambling,
lottery or promotional-competition law — which is licensed, jurisdictional,
and not something you retrofit:

- Random winners, raffles, or "one bidder gets their money back."
- Prize pools funded by entry fees.
- **Lowest-unique-bid** formats. These are genuinely popular as an outbid
  variant, and they have been treated as gambling or as an illegal lottery in
  several jurisdictions, because you cannot know whether your bid is unique.
  If you build one, get advice first.
- Penny-auction mechanics, where each bid costs money and only one person gets
  the item. Multiple regulators have treated these as gambling.

The safe zone is: the buyer knows exactly what they get, before they pay, with
no chance element. Every step away from that is a legal question, not a
product decision.

## EU/UK withdrawal rights are a real thing with a simple fix

Consumers buying digital services at a distance in the EU/UK generally have a
14-day right to withdraw. It does not apply if the consumer expressly consents
to immediate performance **and** acknowledges losing the withdrawal right.

So collect that consent at checkout, not in a footer link. Stripe Checkout's
`consent_collection.terms_of_service: 'required'` plus a terms page that states
it plainly covers this cheaply, and it is the same checkbox that helps you win
disputes. Skipping it means a chunk of your bidders may have a statutory right
to a refund regardless of your "bids are permanent" rule.

Also relevant if you sell to consumers in the EU/UK: distance-selling rules
require identifying the trader (a real name and address, not just a domain),
and VAT/sales tax on digital services is destination-based. Stripe Tax exists
precisely because doing this by hand is miserable.

## Publish four pages before you take a dollar

1. **Rules** — the mechanic, the minimum, the increments, what a bid buys.
2. **Refund policy** — including the exceptions you *will* honour. See
   [2. Payments](02-payments.md#refunds-pick-a-policy-and-publish-it-before-you-need-one).
3. **Content policy and takedowns** — what is banned, how to report, what
   happens to the money. See
   [5. Abuse and moderation](05-abuse-and-moderation.md).
4. **Who you are** — the legal entity and a monitored contact address.

Anonymous boards taking five figures an hour attract exactly the scrutiny you
would expect. A name and a working email is most of what "legitimate" means to
a stranger deciding whether to send you $500.

## Privacy basics

You are collecting less than most sites, which is an advantage — keep it that
way.

- No accounts means no password breach. Do not add auth you do not need.
- Stripe holds the card data; you should never see a PAN. Do not log full
  webhook payloads into a third-party log service without checking what is in
  them.
- Hash IPs used for click deduplication and expire them quickly. Raw IPs are
  personal data under GDPR, and you only need them for rate limiting.
- If you publish a bidder's email or name anywhere, get consent first. Publish
  the listing, not the buyer.
- A one-page privacy policy naming what you collect, why, and for how long.

## Trust is a feature, and it is what compounds

Bidders are handing money to a domain they learned about an hour ago. Anything
that makes the transaction legible pays for itself:

- Public, permanent, timestamped bid history. Immutability *is* the trust
  model — anyone can audit the board against what they paid.
- Honest click counts, from a source you control. Inflating a number people
  are pricing against is fraud.
- Public traffic numbers. Bidders are buying attention; tell them how much
  there is, including when it is falling.
- Fast replies to billing mail. Every voluntary refund is a chargeback you
  avoided and a story you do not have to read about.
- Do not quietly change the rules after money is in. If you must change them,
  version the rules page, date it, and grandfather existing listings.

## Do not take the board down

If you wind it down, say so in advance and leave the board up read-only. People
paid for a public placement; deleting it is both the fastest route to a wave of
disputes and the end of your reputation for the next thing you launch.
