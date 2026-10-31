# 00 — Project Charter

## Project name

**MandateLens — Recurring Payment Intelligence Platform**

**Tagline:** Find the money leaving quietly.

## 1. Vision

Help people understand recurring financial commitments that are hidden in confusing transaction records, see how those commitments change over time, understand their annual cost, and follow a safe, mechanism-appropriate process for ending a commitment when they decide to do so.

## 2. Mission

Build a demonstrable, explainable FinTech prototype that reconstructs recurring commitments from synthetic statements and payment notifications, using a curated merchant reference set and deterministic detection logic.

## 3. Problem to solve

People may have forgotten subscriptions, memberships, premiums, recurring bills, and app plans. Raw descriptors can be unclear; recurring payments can vary in amount or interval; price increases and trial conversions may be overlooked; and cancellation can require different steps depending on how the payment is authorised.

## 4. Objectives

1. Discover fixed, variable, annual, and irregular recurring commitments from synthetic records.
2. Resolve abbreviated or inconsistent descriptors into recognisable merchant identities with traceable confidence.
3. Explain why transactions were grouped into a commitment.
4. Detect meaningful amount increases, trial conversions, and cadence changes.
5. Flag potentially unused services only when usage coverage exists.
6. Detect a later debit after a user-confirmed cancellation event.
7. Provide mechanism-specific cancellation guidance and an evidence checklist.
8. Make annual costs, potential leakage, and potential savings understandable.
9. Keep the prototype reproducible and safe through synthetic-only data.

## 5. Non-goals

- Real bank, card, UPI, open-banking, or payment-processor integration.
- Real payment blocking, mandate revocation, cancellation submission, refunds, or disputes.
- Investment, credit scoring, lending, insurance underwriting, or financial product recommendations.
- Determining legal rights or guaranteeing regulator/bank outcomes.
- Claiming a service is unused without valid usage evidence.
- Full production multi-tenant financial-data infrastructure.
- OCR/PDF ingestion, Gemini, machine learning, Neo4j, and cloud deployment as prerequisites for the MVP.

## 6. Primary users and stakeholders

- Primary: individuals trying to understand several recurring commitments.
- Secondary: household budget organisers and freelancers with recurring digital tools/services.
- Hackathon judges/testers: need to see a clear, working, evidence-backed end-to-end demonstration.
- Project team: needs a staged, reproducible build with observable acceptance criteria.

Personas are hypotheses for design and must not be represented as validated user research.

## 7. Product principles

- Evidence first; explain every inference.
- Preserve raw input and keep normalised values separately.
- Make uncertainty visible.
- Use deterministic and testable algorithms for financial calculations.
- Keep the cancellation process informational and simulated.
- Prefer a reliable vertical slice over broad unfinished scope.
- Make the annual view central to the product story.

## 8. Success measures for the prototype

These are prototype targets, not market claims:

- 100% of seeded demo scenarios have an expected outcome documented in tests.
- Every high-priority insight links to at least one supporting evidence item.
- Low-confidence merchant matches enter manual review rather than being silently confirmed.
- Re-importing the same synthetic file does not duplicate transactions.
- Annualisation outputs match hand-calculated fixtures within defined rounding rules.
- The core user journey works without Neo4j, Gemini, OCR, or cloud services.
- A tester can complete the demo workflow without developer intervention.

## 9. Constraints

- Synthetic financial data only.
- Use the stack in `08_TECHNICAL_ARCHITECTURE.md`, based on the supplied hybrid technology-stack PDF.
- Use PostgreSQL as source of truth.
- Optional services must be non-blocking.
- Build in gated phases; Antigravity stops after every phase and returns a handoff report.

## 10. Assumptions to validate

- Users understand the value of a consolidated commitment view.
- Statement-first discovery is useful even without direct bank integration.
- A hand-curated reference set can resolve the most important demo descriptors.
- Users trust an insight more when the evidence and confidence are visible.
- Annualised totals make recurring costs easier to interpret.

## 11. Approval and change control

Changes to synthetic-only scope, primary stack, source-of-truth database, cancellation boundaries, or phase order require explicit user approval. Minor implementation choices may be made by the agent if they preserve the stated architecture and are documented in the handoff summary.
