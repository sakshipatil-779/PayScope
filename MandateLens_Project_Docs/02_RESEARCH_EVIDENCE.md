# 02 — Research Evidence and Assumption Register

## 1. Purpose

This document distinguishes information supplied in the problem brief and desk-research notes from inferences, hypotheses, and assumptions. Do not convert an unverified assumption into a product fact.

## 2. Evidence classification

Use these labels in research notes and, where useful, in product explanations:

- **Evidence:** directly present in a supplied source, synthetic record, or observed user test.
- **Inference:** a reasoned interpretation of evidence; explain the reasoning.
- **Hypothesis:** a proposition that can be tested with users or data.
- **Assumption:** an unverified belief used temporarily to make progress.

## 3. Evidence from the supplied problem brief

| ID | Evidence / source statement | Product implication | Limitation |
|---|---|---|---|
| E-01 | The brief says recurring subscriptions, premiums, and app charges can accumulate quietly over time. | Show a unified commitment list and annual total. | Prevalence and average amount are not quantified. |
| E-02 | The brief says bank interfaces may show mandates separately and not explain the merchant. | Connect mandate, transaction, and canonical merchant. | Interfaces vary by institution and must not be generalised without research. |
| E-03 | The brief says statement descriptors are compressed strings designed for systems rather than people. | Preserve raw descriptor and provide a canonical merchant mapping. | Descriptor patterns vary by processor and region. |
| E-04 | The brief says cancellation paths differ by mechanism. | Make playbooks mechanism-aware. | Exact current instructions must be verified before merchant-specific display. |
| E-05 | The brief says price increases inside existing mandates can be difficult to notice. | Compare historical charge groups and show change evidence. | A higher amount may also result from variable usage, tax, or plan changes. |
| E-06 | The brief explicitly requires synthetic statements and notifications. | Generate and use synthetic data only. | No production financial-data integration is permitted in this prototype. |

## 4. Evidence from the supplied desk-research notes

The attached research notes describe the following solution categories and gaps. Treat these as **secondary desk-research leads**, not fresh independent verification:

| Category / example in supplied notes | Described capability | Gap to investigate |
|---|---|---|
| Rocket Money / Truebill | Linked-account recurring charge discovery, renewal/price alerts, cancellation assistance, and bill negotiation are described. | Dependence on linked-account access, market/region coverage, cancellation transparency, and feature availability need current verification. |
| Bobby | Manual subscription tracking and privacy-oriented setup are described. | Manual entry can miss forgotten commitments; discovery and cancellation support may be limited. |
| Plaid recurring transactions / enrichment | Developer infrastructure for transaction streams and merchant enrichment is described. | It is infrastructure, not a complete consumer discovery-to-cancellation experience; regional availability must be checked. |
| UPI AutoPay manager apps and bank/UPI mandate screens | Mandate viewing and management are described. | Merchant interpretation, variable/irregular patterns, historical price changes, usage signals, and annual impact may remain fragmented. |

The research note references these sources for further checking:

- Rocket Money learning resources: https://www.rocketmoney.com/learn/personal-finance/best-apps-to-manage-recurring-payments
- Rocket Money subscription-management resources: https://www.rocketmoney.com/learn/personal-finance/best-subscription-management-apps
- Plaid financial insights documentation: https://plaid.com/docs/financial-insights/
- NPCI UPI consolidated circular referenced in the notes: https://www.npci.org.in/uploads/UPI_Consolidated_Circular_f9c023a0ef.pdf
- A UPI AutoPay manager example referenced in the notes: https://play.google.com/store/apps/details?id=com.wealthmize.autopaycancel.autopaymanager&hl=en_IN
- Other secondary commentary links are present in the supplied research text. Verify authority, publication date, jurisdiction, and current status before relying on them.

**Important:** This document does not assert that the linked product features, legal obligations, or regulatory processes remain current. For a hackathon prototype, avoid hardcoding legal claims. If current merchant-specific or regulatory instructions are later included, verify them against official sources and store provenance and verification date.

## 5. Inferences

| ID | Inference | Evidence basis | Confidence / caveat |
|---|---|---|---|
| I-01 | A consolidated commitment view may reduce the work of switching among statement, mandate, and merchant screens. | E-02, E-03, E-04 | Plausible; needs usability testing. |
| I-02 | Merchant alias resolution is a key technical capability because the same merchant may use several descriptors. | E-03 and synthetic examples in supplied research | Strong design rationale; alias quality must be tested. |
| I-03 | Annualised cost can make cumulative commitments easier to understand than monthly totals alone. | E-01 and E-06 | Needs user testing; do not assume it changes behaviour. |
| I-04 | A cancellation guide must distinguish merchant subscription state from payment mandate state. | E-04 and mechanism examples in supplied research | Product logic should preserve distinction; exact local instructions require verification. |

## 6. Hypotheses to test

| ID | Hypothesis | Falsifiable test |
|---|---|---|
| H-01 | Users can identify more commitments from an evidence-backed statement-first list than from a blank manual tracker. | Give participants the same synthetic records and compare correct identification and time. |
| H-02 | Showing raw descriptor beside canonical merchant improves trust. | Compare comprehension and correction rates with/without raw descriptor. |
| H-03 | Confidence plus linked transactions makes inferred commitments understandable. | Ask participants to explain why a commitment was detected. |
| H-04 | Annualised totals help users prioritise which commitment to review. | Ask participants to select a review priority before and after seeing annual totals. |
| H-05 | Mechanism-specific guidance is more actionable than generic “cancel in app” wording. | Give participants different mechanism scenarios and assess correct next step. |
| H-06 | Manual review for unknown descriptors is preferable to confident incorrect merchant mapping. | Seed ambiguous descriptors and measure correction and trust. |

## 7. Assumptions and risks

- A-01: The target user has access to downloadable or copyable statement-like records.
- A-02: A small, curated descriptor reference set can cover the hackathon's representative scenarios.
- A-03: Synthetic usage events can demonstrate the distinction between “no evidence of use” and “not used”.
- A-04: Users will understand annualisation estimates when the formula is visible.
- A-05: A simulated cancellation workflow is sufficient to demonstrate the intended product value at hackathon stage.
- A-06: The project can support INR examples while storing currency explicitly and avoiding assumptions that every record is INR.

## 8. Research gaps

Before making stronger product claims, collect:

1. Five reachable target-user examples and their current workaround.
2. Real examples of anonymised descriptor *formats* only if consent and research rules permit; do not import real statements into this synthetic prototype.
3. Which commitment types users most often fail to recognise.
4. Which cancellation mechanism causes the greatest confusion.
5. What proof users want to retain after attempting cancellation.
6. How people interpret “potentially unused” when usage coverage is incomplete.
7. Whether annual cost or next renewal date is more useful for prioritisation.

## 9. Research interview prompts

1. Tell me about the last time you noticed a recurring payment you did not expect.
2. How did you identify what the descriptor referred to?
3. What did you do next, and which apps or screens did you use?
4. How did you know whether cancelling a service also stopped its payment authorisation?
5. Have you noticed a price change in an existing recurring service? How?
6. What evidence or confirmation would make you confident that a cancellation request was recorded?
7. What would make an automated recurring-payment finding feel untrustworthy?
8. What would you currently use instead of this product?

Do not lead participants toward the product's proposed solution. Record quotes only with permission and label sample size.

## 10. Evidence policy for the UI

Every finding must expose:
- What was observed.
- What the system inferred.
- Which records support it.
- Confidence or review status.
- What is not known.
- Whether a user confirmed the interpretation.

Never display synthetic examples as actual customer findings or market statistics.
