/**
 * Reference Stripe webhook handler for a pay-to-rank board.
 * Next.js App Router: app/api/stripe/webhook/route.ts
 *
 * This is the only code path in the system allowed to change a rank.
 * `success_url` is not proof of payment -- a browser can reach it without
 * paying, and delayed payment methods settle minutes later. If your board
 * grants rank on redirect, it can be ranked for free.
 *
 * Pairs with reference/schema.sql (credit_bid) and
 * reference/create-checkout.ts.
 */

import Stripe from 'stripe'
import { sql } from '@/lib/db' // any Postgres client; this example uses a tagged-template one

// The Stripe SDK needs Node crypto for signature verification, so this route
// cannot run on the Edge runtime.
export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)
const WEBHOOK_SECRET = process.env.STRIPE_WEBHOOK_SECRET!

// checkout.session.completed fires as soon as the session finishes, which for
// delayed-notification methods is before the money exists. The async_* event
// is the one that arrives when such a payment actually settles.
const CREDIT_EVENTS = new Set<Stripe.Event['type']>([
  'checkout.session.completed',
  'checkout.session.async_payment_succeeded',
])

export async function POST(req: Request) {
  const signature = req.headers.get('stripe-signature')
  if (!signature) {
    return new Response('missing stripe-signature', { status: 400 })
  }

  // The RAW body, byte for byte. Any middleware that parses the body before
  // this line (express.json(), a `await req.json()` above, a proxy that
  // re-serialises JSON) breaks every signature check in production while
  // still passing with `stripe listen`, because the CLI sends bytes you
  // happen to round-trip cleanly.
  const raw = await req.text()

  let event: Stripe.Event
  try {
    event = await stripe.webhooks.constructEventAsync(raw, signature, WEBHOOK_SECRET)
  } catch {
    // 400 tells Stripe not to retry. Correct: a bad signature never becomes
    // a good one, and retrying a forged request is pure load.
    return new Response('invalid signature', { status: 400 })
  }

  if (!CREDIT_EVENTS.has(event.type)) {
    return ok('ignored')
  }

  const session = event.data.object as Stripe.Checkout.Session

  if (session.payment_status !== 'paid') {
    // Not an error. The async_payment_succeeded event will arrive later, or
    // async_payment_failed will, and neither should move a rank now.
    return ok('not settled yet')
  }

  // Set both at checkout creation: metadata for humans reading the dashboard,
  // client_reference_id as the one Stripe surfaces in exports and reports.
  const listingId = session.metadata?.listing_id ?? session.client_reference_id
  const paymentIntentId =
    typeof session.payment_intent === 'string'
      ? session.payment_intent
      : session.payment_intent?.id

  // Trust Stripe's number, never the browser's. amount_total is integer
  // minor units, already net of any coupon.
  const amountCents = session.amount_total

  if (!listingId || !paymentIntentId || !amountCents || amountCents <= 0) {
    // Retrying will not conjure the missing field. Take the money off the
    // retry queue, alert, and reconcile by hand -- money arrived and someone
    // is expecting a rank for it.
    console.error('[stripe] unusable session', {
      event: event.id,
      session: session.id,
      listingId,
      paymentIntentId,
      amountCents,
    })
    return ok('unusable session, flagged for reconciliation')
  }

  if ((session.currency ?? 'usd') !== 'usd') {
    // A board that sorts by a number must sort one currency. Multi-currency
    // means either a fixed display currency plus conversion at capture, or a
    // separate board per currency -- not a mixed total_cents column.
    console.error('[stripe] unexpected currency', session.id, session.currency)
    return ok('unexpected currency, flagged for reconciliation')
  }

  try {
    // credit_bid() is idempotent at both the event and the PaymentIntent
    // level, so a retry of this exact request is free and safe.
    const [row] = await sql<{ credit_bid: boolean }[]>`
      select credit_bid(
        ${event.id},
        ${event.type},
        ${listingId}::uuid,
        ${paymentIntentId},
        ${session.id},
        ${amountCents}::bigint,
        'usd'
      )
    `

    if (!row.credit_bid) {
      return ok('already credited')
    }
  } catch (err) {
    // 500 makes Stripe retry with backoff for up to three days. That is
    // exactly what a transient database error deserves, and the idempotency
    // gates make the eventual retry harmless.
    console.error('[stripe] credit failed, will retry', event.id, err)
    return new Response('temporary failure', { status: 500 })
  }

  // Everything below is best-effort and must never turn a credited payment
  // into a 500 -- that would make Stripe redeliver an event whose money is
  // already on the board, and the second pass would silently no-op while your
  // alerting screams. Queue it; do not await it inline.
  void afterCredit({ listingId, amountCents, sessionId: session.id }).catch((err) =>
    console.error('[stripe] post-credit side effects failed', event.id, err),
  )

  return ok('credited')
}

function ok(reason: string) {
  // Stripe only reads the status code, but a body makes the dashboard's
  // delivery log readable at 3am during a spike.
  return new Response(reason, { status: 200 })
}

/**
 * Side effects that are allowed to fail: cache invalidation, the receipt
 * email, the freshly rendered OG image, the realtime nudge.
 *
 * The receipt is not decoration. It is the evidence you submit if the bid is
 * disputed: listing name, amount, timestamp, the rank it bought, and a
 * permalink. Boards that skip it lose disputes they should win.
 */
async function afterCredit(_input: {
  listingId: string
  amountCents: number
  sessionId: string
}) {
  // revalidateTag('board')
  // await redis.del('board:top')
  // await sendReceiptEmail(...)
  // await publishBoardUpdate(...)
}
