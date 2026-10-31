# 03 — User Personas

> These are provisional design personas derived from the problem brief. They are not validated research findings or demographic claims. Validate them through interviews and usability tests.

## Persona 1 — The Subscription Juggler (primary)

**Context:** Uses several digital services, apps, memberships, or online tools. Has a mix of recurring charges and may not remember every plan or descriptor.

**Goal:** Understand what each recurring charge is, how much it costs annually, and which commitments deserve review.

**Pain points / needs:**
- Raw transaction description is hard to recognise.
- Same service may appear under multiple descriptors.
- Small monthly amounts are easy to overlook.
- Needs a clear explanation before deciding whether to cancel.

**Current workaround hypothesis:** Search a descriptor, review a payment app, check email/merchant account, or maintain a manual list.

**Product value:** Merchant resolution, evidence-backed recurring list, price-change insights, annual view, and an understandable cancellation checklist.

**Success signal:** Can correctly explain the merchant and recurring pattern for a selected commitment, identify whether a finding is certain or inferred, and locate the relevant next step.

## Persona 2 — The Household Payment Organiser (secondary)

**Context:** Keeps track of recurring household services and financial obligations such as utilities, memberships, and premiums.

**Goal:** See total recurring commitments and avoid treating variable household bills as subscriptions.

**Pain points / needs:**
- Different categories have different cadence and amount behaviour.
- Annual premiums can look like one-off payments.
- A changing utility bill should not be falsely labelled a price increase.
- Needs a clear annual estimate with uncertainty.

**Product value:** Commitment categories, variable recurring detection, annualisation with formulas, and clear separation between subscriptions and other obligations.

**Success signal:** Can distinguish a subscription from a recurring utility or premium and understand the assumptions behind the annual estimate.

## Persona 3 — The Independent Professional (secondary)

**Context:** Uses recurring software, cloud services, memberships, and business-related tools. May have several descriptors for the same provider or processor.

**Goal:** Identify duplicated or forgotten service commitments and understand ongoing cost.

**Pain points / needs:**
- Merchant descriptors do not always resemble the product name.
- Multiple tools can serve similar categories.
- A plan price may change without a change in the payment mandate.
- Needs a portable record of review/cancellation attempts.

**Product value:** Descriptor alias resolution, category-level duplicate visibility, change history, and evidence timeline.

**Success signal:** Can resolve an unknown-looking descriptor, inspect the linked history, and record a simulated cancellation/review outcome.

## Shared user needs

1. See all candidate commitments in one place.
2. Understand the merchant and category.
3. See how the system detected recurrence.
4. Understand confidence and evidence.
5. See historic amounts and estimated annual cost.
6. Know which payment mechanism applies.
7. Receive steps that do not overstate legal or merchant-specific certainty.
8. Correct the system when merchant matching is wrong.

## Persona anti-patterns to avoid

- Do not assume every user wants to cancel every recurring payment.
- Do not assume a high annual cost means a payment is wasteful.
- Do not infer a user's income, financial distress, or personal habits from synthetic transaction examples.
- Do not label people as careless or irresponsible.
- Do not use colour alone to indicate severity or status.
