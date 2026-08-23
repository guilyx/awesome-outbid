/**
 * Reference checkout creation for a pay-to-rank board.
 * Next.js App Router: app/api/checkout/route.ts
 *
 * The load-bearing idea here is what this endpoint does *not* do: it does not
 * promise a rank. It validates an amount, creates a listing in `pending`, and
 * hands off to Stripe. Rank is decided later, by the sort, over money that
 * actually arrived. See best-practices/01-auction-mechanics.md.
 */

import Stripe from 'stripe'
import { sql } from '@/lib/db'

export const runtime = 'nodejs'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

const MIN_CENTS = 5_00
const MAX_CENTS = 999_999_00

export async function POST(req: Request) {
  const body = await req.json()

  // Integer cents, parsed strictly. `parseInt('5.99')` is 5, `Number('5e3')`
  // is 5000, and `10.10 * 100` is 1009.9999999999999 -- so take cents from
  // the client as an integer or reject it.
  const amountCents = body.amount_cents
  if (!Number.isSafeInteger(amountCents) || amountCents < MIN_CENTS || amountCents > MAX_CENTS) {
    return json({ error: 'amount must be a whole number of cents in range' }, 400)
  }

  // Validate before you take money, not after. A rejected URL post-payment is
  // a refund; a rejected URL pre-payment is a form error.
  const url = normaliseTargetUrl(body.target_url)
  if (!url) {
    return json({ error: 'target_url must be a public http(s) URL' }, 400)
  }

  const name = String(body.name ?? '').trim()
  if (name.length < 1 || name.length > 60) {
    return json({ error: 'name must be 1-60 characters' }, 400)
  }

  // Deliberately NOT done here:
  //
  //   const top = await currentTopBid()
  //   if (amountCents <= top) return json({ error: 'someone outbid you' }, 409)
  //
  // Between this check and the webhook, the top can move -- and it moves most
  // during exactly the traffic that pays your bills. Enforcing it here means
  // either refusing money you already have (a refund, a fee, an annoyed
  // customer) or lying about the rank you sold. Quote the price to beat as a
  // live, explicitly non-binding number in the UI, take any amount above the
  // floor, and let the sort place it.

  const [listing] = await sql<{ id: string; slug: string }[]>`
    insert into listings (slug, name, target_url, kind, status)
    values (${slugify(name)}, ${name}, ${url.href}, ${body.kind === 'profile' ? 'profile' : 'product'}, 'pending')
    returning id, slug
  `

  const session = await stripe.checkout.sessions.create(
    {
      mode: 'payment',
      // Price is built server-side from the validated integer. Never accept a
      // client-supplied Price ID or a client-supplied unit_amount echo.
      line_items: [
        {
          quantity: 1,
          price_data: {
            currency: 'usd',
            unit_amount: amountCents,
            product_data: {
              name: `Bid on the board: ${name}`,
              description: 'One-time, non-refundable. Rank is set by total dollars paid.',
            },
          },
        },
      ],
      client_reference_id: listing.id,
      metadata: { listing_id: listing.id, listing_slug: listing.slug },

      // Shows up on the cardholder's statement. An unrecognisable descriptor
      // is a top cause of "I don't know what this charge is" disputes, which
      // you lose by default.
      payment_intent_data: { statement_descriptor_suffix: 'BOARD BID' },

      // You will need this to answer billing questions and to send a receipt
      // that doubles as dispute evidence.
      customer_creation: 'always',

      // Consent captured at the moment of payment is worth far more than a
      // link to a terms page. In the EU/UK this is also what waives the
      // 14-day withdrawal right for immediate digital performance.
      consent_collection: { terms_of_service: 'required' },

      success_url: `${process.env.PUBLIC_URL}/l/${listing.slug}?paid=1&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${process.env.PUBLIC_URL}/?cancelled=1`,

      // Abandoned sessions leave `pending` listings behind; sweep them.
      expires_at: Math.floor(Date.now() / 1000) + 30 * 60,
    },
    {
      // If the client retries this request, Stripe returns the same session
      // instead of opening a second one for the same intent to pay.
      idempotencyKey: `checkout:${listing.id}`,
    },
  )

  return json({ url: session.url }, 200)
}

/**
 * Reject anything that is not a public http(s) URL.
 *
 * This matters twice over. It stops `javascript:` and `data:` links reaching
 * an href, and -- if you ever fetch the URL server-side for a favicon, title
 * or OG image -- it is your first line against SSRF. If you do fetch, also:
 * resolve DNS yourself and check the resolved IP is public, cap redirects,
 * cap response size, and set a hard timeout. A hostname that resolves public
 * on your check and private on the fetch (DNS rebinding) is the reason to
 * pin the address you validated.
 */
function normaliseTargetUrl(input: unknown): URL | null {
  if (typeof input !== 'string' || input.length > 2048) return null

  let url: URL
  try {
    url = new URL(input.trim())
  } catch {
    return null
  }

  if (url.protocol !== 'http:' && url.protocol !== 'https:') return null
  if (url.username || url.password) return null

  const host = url.hostname.toLowerCase()
  if (
    host === 'localhost' ||
    host.endsWith('.localhost') ||
    host.endsWith('.internal') ||
    host.endsWith('.local') ||
    /^\d+\.\d+\.\d+\.\d+$/.test(host) || // resolve names yourself; refuse raw IPs
    host.includes(':') // bare IPv6
  ) {
    return null
  }

  url.hash = ''
  return url
}

function slugify(name: string) {
  const base = name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 40)
  // Slugs are public and permanent; collide-proof them rather than racing on
  // the unique index.
  return `${base || 'listing'}-${crypto.randomUUID().slice(0, 8)}`
}

function json(payload: unknown, status: number) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'content-type': 'application/json' },
  })
}
