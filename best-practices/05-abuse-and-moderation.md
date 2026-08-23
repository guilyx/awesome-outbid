# 5. Abuse and moderation

You are running an open, unauthenticated, high-traffic page that publishes
arbitrary user-supplied links and sorts them by how much someone paid. That is
an attractive target, and "we take payment" filters almost nobody — a $5 floor
is not a trust signal, it is a rounding error to anyone doing this at scale.

## The bait-and-switch is the attack you will actually see

The pattern: submit a clean, plausible product URL. Pay. Reach the top of a
board with a million visitors. Then edit the URL to a phishing page, a malware
download, or an affiliate redirect.

This works against every board that lets a listing be edited freely after
payment, and it is worth thousands of dollars per hour to the attacker at the
top of a trending leaderboard.

Defences, in order of importance:

1. **Lock the URL on first confirmed payment** (`url_locked_at` in the
   reference schema).
2. Changes after that go through review, not straight to live.
3. Log every edit with a timestamp and the old value. When a listing gets
   reported, you need to know what it pointed at an hour ago.
4. Re-scan on edit — do not assume the first scan still applies.
5. Consider re-scanning the top listings periodically anyway. A URL that was
   clean on submission can be compromised later, and yours is the page sending
   the traffic.

## Validate the URL before you take money, not after

Rejecting a link post-payment is a refund and an argument. Rejecting it in the
form is a form error.

- `http:` / `https:` only. Reject `javascript:`, `data:`, `vbscript:`, and
  anything with embedded credentials.
- Reject `localhost`, `*.internal`, `*.local`, raw IPs, and bare IPv6.
- Cap length; strip fragments; normalise.
- Check against a reputation source (Google Safe Browsing, URLhaus,
  PhishTank) on submission and on edit.

`normaliseTargetUrl()` in
[`reference/create-checkout.ts`](../reference/create-checkout.ts) is a working
starting point.

## SSRF: if you fetch the URL, you are a proxy

The moment you fetch a favicon, a page title or an OG image server-side, you
have handed anyone with $5 an HTTP client inside your infrastructure —
pointed at your cloud metadata endpoint, your internal admin panel, your
database's private address.

Minimum controls:

- Resolve DNS yourself, check the resolved address is public, and **connect to
  the address you validated** — otherwise a hostname that resolves public on
  your check and private on the fetch (DNS rebinding) walks straight through.
- Block the link-local metadata range (`169.254.0.0/16`) explicitly, plus all
  private and loopback ranges, IPv4 and IPv6.
- Cap redirects, and re-validate the address at each hop.
- Hard timeout and response size cap.
- No cookies, no auth headers, no proxy credentials on that client.
- Ideally run the fetcher somewhere with no network access to anything of
  yours.

## XSS through the listing name

Listing names are attacker-controlled and rendered on the highest-traffic page
you will ever operate. Store raw, escape on output, and let your framework do
it — modern React/Svelte/Vue escape by default and the hole is always the one
place someone reached for `dangerouslySetInnerHTML` to render an emoji or a
bold tag.

Watch the places that are easy to forget:

- OG image generation and any SVG-to-PNG path.
- The receipt email (an HTML email template is a template like any other).
- Your own admin dashboard — reviewing reported listings is exactly when you
  render hostile input, and admin XSS is the expensive kind.
- JSON embedded in a `<script>` tag.

Set a Content-Security-Policy. Add `rel="nofollow ugc noopener"` and
`target="_blank"` on outbound links — `nofollow ugc` because you are selling
placement and should not be selling PageRank, `noopener` because
`window.opener` is a redirect vector.

## Publish a takedown policy, then honour it

Write it before you need it, because the first time you need it, you will need
it within the hour:

- What is not allowed. Keep it short and concrete: no malware, no phishing, no
  sexual content, no impersonation, no illegal goods. outbid.lol's version is
  three clauses long.
- How to report — a real, monitored address, on the page.
- What happens to the money when a listing is removed. **Decide this in
  advance.** Keeping it is defensible if you said so up front; refunding is a
  much better look and cheaper than the argument.
- Whether a removed listing's position is inherited by the listing below.

Then build the button. `status = 'hidden'` in one click, from a phone. During
a spike you will need to take something down while away from a laptop, and if
the only way to do it is a SQL client, you will not do it fast enough.

Make sure re-payment cannot undo a removal — see the `CASE` in `credit_bid()`
in [3. Data model](03-data-model.md#statuses-and-the-one-rule-that-must-not-be-buyable).

## Impersonation and the profile problem

Boards that rank X handles or personal profiles inherit a different problem:
someone pays $50 to put a rival, an ex, or a stranger on a public list. The
subject never consented and cannot remove themselves.

If you rank people:

- Require proof of control of the handle before the listing goes live, or
- Offer an unconditional, no-questions removal to the subject, and say so
  prominently.

"They paid, so it stays" is not a position that survives contact with a
harassment complaint, your processor's acceptable use policy, or a platform's
legal team.

## Card testing

An endpoint that accepts an arbitrary amount with no account is a carding
target. Rate-limit checkout creation per IP, keep Stripe Radar on, alert on a
spike in failed payment attempts, and watch for many small payments from
different cards in a short window. A wave of card testing hurts your
authorisation rate and your standing with your processor even when none of it
succeeds.

## Keep an audit trail

Every status change, URL edit, refund and removal, with actor and timestamp,
in a table you never delete from. It costs nothing now. It is the only thing
that answers "what did this listing point at when I clicked it" three weeks
later, when the question is coming from someone's lawyer.
