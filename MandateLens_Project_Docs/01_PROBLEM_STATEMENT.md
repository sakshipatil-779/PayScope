# 01 — Problem Statement

## 1. Problem statement

People accumulate recurring financial commitments over time—subscriptions, app plans, memberships, premiums, and recurring bills—but often cannot easily identify every commitment, understand which service a confusing statement descriptor represents, notice changes to the amount or billing pattern, or determine the correct process for stopping future payments.

The information is fragmented across transaction statements, payment notifications, merchant accounts, mandate screens, and service-usage history. A mandate list may show authorisation details without explaining the real-world service; a transaction description may be shortened or processor-formatted; and cancellation steps vary by payment mechanism. A small monthly amount can also obscure the total annual commitment.

## 2. Who experiences the problem?

The initial target is a digitally active individual who has multiple recurring commitments across at least two or more categories or payment mechanisms and who can access statement-like records or payment notifications.

This definition is intentionally behavioural. It does not assume a particular age, income, bank, or subscription count until field research validates those attributes.

## 3. When does the problem occur?

- When reviewing a monthly or annual statement.
- When an unfamiliar descriptor appears.
- When a free trial ends and a paid amount is charged.
- When a familiar service changes its price.
- When a person realises they no longer use a service.
- When a person attempts to cancel but is unsure whether to cancel the merchant plan, pause a mandate, revoke a mandate, or contact the payment provider.
- When a debit appears after a cancellation was recorded.

## 4. User and financial cost

The immediate user costs are time spent identifying unfamiliar charges, uncertainty about future debits, missed opportunities to review unused commitments, and difficulty estimating total recurring expenditure. Possible monetary impact includes continued payments, price increases, trial conversion, or duplicate services. The prototype must calculate these only from synthetic evidence and must not claim that every detected recurring payment is unwanted.

## 5. Why this matters now

The supplied problem brief highlights the accumulation of digital subscriptions and payment mandates, inconsistent descriptors, different cancellation mechanisms, and the difficulty of noticing a price change when the payment authorisation remains active. The supplied research notes also identify existing product categories—subscription trackers, bank/UPI mandate screens, and recurring-transaction infrastructure—that address parts of the journey but may leave the interpretation-to-cancellation workflow fragmented.

These points are the rationale for the hackathon problem. Their prevalence, severity, and willingness-to-pay implications still require field validation; do not present them as quantified market findings.

## 6. Current workaround hypotheses

Users may currently:

- Search the descriptor online or in their email/messages.
- Open multiple bank or payment apps to inspect mandates.
- Search merchant apps or websites for billing settings.
- Maintain a manual list or calendar reminder.
- Ask the bank or merchant support team what a charge means.
- Ignore a charge because its source or cancellation path is unclear.

These are hypotheses to validate through interviews and observation, not established facts about all users.

## 7. Product opportunity

Build a statement-first intelligence layer that connects raw transactions, descriptor aliases, canonical merchants, recurring commitments, mandates, usage signals, price events, cancellation playbooks, and evidence into one understandable experience.

## 8. How might we statement

**How might we help a person reconstruct and understand their recurring financial commitments from messy statement and notification records, identify meaningful changes with evidence, see the annual cost, and follow the correct cancellation process for each payment mechanism—without connecting to real financial accounts or performing real cancellation actions?**

## 9. Falsifiable product hypothesis

For people who have multiple recurring commitments and can provide statement-like records, a statement-first tool that resolves descriptors, explains recurring patterns, surfaces evidence-backed changes, and provides mechanism-specific cancellation guidance will help them identify commitments and decide which ones to review more effectively than a manually maintained list alone.

This hypothesis is supported only if usability tests show that target users can correctly recognise commitments, understand evidence/confidence, and complete the simulated decision workflow. The test plan must record failures and counterexamples.

## 10. Scope boundary

The product identifies and explains. The user decides. The application does not execute payment or cancellation operations and does not make legal, banking, insurance, or lending determinations.
