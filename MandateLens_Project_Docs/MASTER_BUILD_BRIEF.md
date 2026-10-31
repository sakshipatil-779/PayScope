# MASTER_BUILD_BRIEF — MandateLens

**Product:** MandateLens  
**Tagline:** Find the money leaving quietly.  
**Category:** FinTech / recurring-payment intelligence  
**Prototype data policy:** Synthetic data only  
**Primary outcome:** Turn confusing payment records into understandable, evidence-backed recurring commitments and mechanism-specific guidance.

## 1. Executive summary

MandateLens is a statement-first recurring-payment intelligence tool. It analyses synthetic transaction statements, payment notifications, mandate records, and synthetic usage signals to reconstruct the recurring commitments a person may have.

It goes beyond a flat subscription list. It explains the merchant behind a raw descriptor, identifies the recurring pattern, surfaces price changes and trial conversions, flags possible unused or post-cancellation charges when evidence exists, calculates an annual view, and guides the user through the correct cancellation route for the payment mechanism.

The prototype must demonstrate the entire chain:

**Raw statement descriptor → merchant resolution → recurring commitment → evidence-backed insight → annual impact → cancellation playbook → recorded user checklist/evidence.**

## 2. The user problem

Recurring payments accumulate quietly: subscriptions, premiums, memberships, app plans, recurring bills, and other obligations. People may forget they agreed to them, fail to recognise compressed statement descriptors, miss price changes inside an existing mandate, or not know whether a service cancellation also stops the payment mechanism.

The product brief identifies four important failure areas in current experiences:

1. Bank interfaces may show mandates separately and may not explain the underlying merchant/service.
2. Statement descriptors are often shortened or processor-formatted and are difficult for a person to recognise.
3. Cancellation routes differ by mechanism and are not always explained in one place.
4. A price increase under an existing mandate can be easy to overlook.

The challenge also explicitly expects synthetic statements and notifications, including irregular recurrence; merchant interpretation; price increase, trial-conversion and stopped-use detection; correct mechanism-specific cancellation guidance; escalation when the merchant does not respond; and an annual cost view.

## 3. Product principles

1. **Statement-first:** import synthetic files rather than requiring account linking.
2. **Evidence before conclusion:** every inference should expose the transactions or notifications that support it.
3. **Deterministic core:** merchant mapping, recurrence, anomaly detection, and money calculations use explainable rules.
4. **Human-readable:** translate technical descriptors into a likely merchant and plain-language explanation.
5. **Mechanism-aware:** cancellation guidance depends on the recorded payment mechanism.
6. **Truthful uncertainty:** show confidence, review queues, and unavailable evidence; do not overstate.
7. **Annual perspective:** make cumulative cost visible without misrepresenting estimates as realised savings.
8. **Synthetic-only safety:** no real financial-data connection or actual cancellation action.

## 4. Primary prototype user

A digitally active person who has several recurring commitments across subscriptions, memberships, apps, utilities, or premiums; receives statement-like transaction records; and needs to understand what is being charged, how much it costs annually, and what steps are appropriate to stop a selected commitment.

Personas in `03_USER_PERSONAS.md` are design hypotheses, not claims from completed interviews.

## 5. Core user journey

1. Open the demo workspace and load reproducible synthetic data or upload a synthetic CSV/XLSX/JSON file.
2. Review the import preview and validation report.
3. Run merchant descriptor normalisation and alias matching.
4. Review proposed recurring commitments with cadence, amount pattern, confidence, and supporting transactions.
5. Open an insight: silent price increase, trial-to-paid conversion, potential unused commitment, unexpected cadence/amount, or post-cancellation debit.
6. Understand the annualised cost and the assumptions behind it.
7. Open the mechanism-specific cancellation playbook.
8. Complete a simulated checklist, record a simulated contact/response, and attach synthetic evidence.
9. Return to the dashboard and see status/impact update without claiming an external cancellation occurred.

## 6. Required technology stack

Use the hybrid stack defined in the supplied **Recommended Hybrid Technology Stack** PDF.

| Area | Chosen technology | Status |
|---|---|---|
| Frontend | Next.js + TypeScript | Core |
| Styling/components | Tailwind CSS + shadcn/ui | Core |
| Motion | Framer Motion | Optional enhancement |
| Charts | Apache ECharts | Core for analytics screens |
| Graph view | Cytoscape.js | Later optional capability |
| Primary API | Python + FastAPI | Core |
| Relational database | PostgreSQL | Core / source of truth |
| ORM | SQLAlchemy 2.0 | Core |
| Migrations | Alembic | Core |
| Graph database | Neo4j | Optional, non-blocking projection |
| Async jobs | Celery | Add for long-running imports/analytics |
| Broker/cache | Redis | Paired with Celery |
| Data processing | Pandas; Polars when useful | Core analytics may start with Pandas |
| Merchant matching | RapidFuzz + regex + curated reference set | Core |
| Statistics | NumPy + SciPy + Statsmodels | Use where justified and testable |
| ML | Scikit-learn | Optional supporting signals only |
| LLM | Google Gemini API | Optional explanations of verified results only |
| Synthetic data | Faker + custom deterministic generators | Core |
| Authentication | One integrated session approach; default FastAPI-managed session for demo | Core only as required |
| Structured files | CSV / XLSX / JSON | Core |
| PDF extraction | PyMuPDF / pdfplumber | Optional later |
| OCR | PaddleOCR | Optional later; not MVP |
| Storage | Local development storage; S3-compatible when deployed | Core local / future cloud |
| Tests | Pytest + Playwright | Core |
| Runtime | Docker + Docker Compose | Core local reproducibility |
| Monitoring | Sentry + OpenTelemetry | Later / optional |

Select mutually compatible, supported dependency versions at implementation time and record exact versions in lockfiles. Do not add all optional services in the first phase.

## 7. Architecture summary

- Next.js renders the user experience and calls the FastAPI backend.
- FastAPI validates requests, orchestrates ingestion and analytics, and exposes versioned APIs.
- PostgreSQL is the authoritative source for imports, transactions, merchants, commitments, mandates, insights, playbooks, and evidence.
- SQLAlchemy 2.0 maps relational entities; Alembic manages schema migrations.
- Python analytics modules use Pandas/Polars, RapidFuzz, regex, and appropriate statistical libraries.
- Celery + Redis handle longer-running statement processing once needed.
- Neo4j receives a derived relationship projection for graph exploration; it must not be required for the core app.
- Gemini may turn already-calculated, structured findings into plain-language explanations, but it is not a source of financial facts.

See `08_TECHNICAL_ARCHITECTURE.md` for the detailed flow.

## 8. Core capabilities

### 8.1 Synthetic ingestion

Accept CSV, XLSX, and JSON. Show column mapping, preview, validation, duplicate handling, import progress, and row-level errors. All sample files and records must carry a synthetic label.

### 8.2 Merchant intelligence

Maintain a curated reference set with canonical merchant names, categories, descriptor aliases/patterns, supported mechanisms, cancellation-playbook references, source/verification metadata, and confidence rules. Matching order: exact normalised match → alias/pattern → regex/prefix → fuzzy token similarity → corroborating cadence/amount evidence → manual review.

### 8.3 Recurrence discovery

Group debit records by merchant candidate, currency, and context. Evaluate cadence and amount stability without demanding identical amounts or exact intervals. Recognise weekly, fortnightly, monthly, quarterly, annual, variable monthly, and irregular recurring patterns. Distinguish subscriptions from utilities, premiums, EMIs, and other recurring obligations.

### 8.4 Insights

Detect sustained amount changes within a stable commitment, trial start followed by paid charge, promotional conversion where evidence exists, payment frequency changes, potential unused services with usage-data coverage, and successful debit after user-confirmed cancellation.

### 8.5 Annual impact

Show current estimated annual committed spend, category totals, annualised price-increase impact, potentially unused spend, potential savings opportunities, and separately recorded realised savings. State formulas and assumptions.

### 8.6 Cancellation guidance

Provide mechanism-specific steps for UPI AutoPay, card recurring mandate, app-store subscription, direct debit/bank instruction, and insurance/loan obligations. Keep merchant-service cancellation distinct from mandate pause/revocation. Include a simulated checklist and evidence log. No external action is executed.

## 9. Data and trust boundaries

- All transaction, notification, mandate, trial, usage, and cancellation events in the prototype are synthetic.
- Do not request, accept, store, or transmit real account credentials or real financial statements.
- The product must identify what is observed versus inferred versus user-confirmed.
- “Potentially unused” requires explicit synthetic usage coverage or user confirmation.
- “Charge after cancellation” requires a recorded cancellation event/date and a later successful linked debit.
- “Price increase” must not be confused with ordinary variable consumption billing.
- If merchant or cancellation details are not verified, present generic guidance and say so.

## 10. MVP success criteria

A judge or tester can use the local demo to:

- Load synthetic data and see import results.
- Resolve several raw descriptors to the correct canonical merchants.
- Inspect at least 12 synthetic commitment scenarios across multiple mechanisms.
- See recurring detection explanations and confidence.
- Identify a price increase, trial-to-paid conversion, potential unused service with coverage, and a post-cancellation debit.
- See annual cost and potential savings with transparent calculations.
- Open the appropriate cancellation guide and complete a simulated checklist.
- Inspect an evidence timeline.
- Use the core app while Neo4j, Gemini, OCR, or cloud storage are disabled.

Detailed acceptance criteria are in `05_PRODUCT_REQUIREMENTS.md` and `11_VALIDATION_AND_TEST_PLAN.md`.

## 11. Delivery method

Work strictly in phases as listed in `12_BUILD_PLAN.md`. Antigravity must complete only the phase named by the current prompt and then return a Phase Handoff Summary. The user will share that summary with ChatGPT before requesting the next phase prompt. Do not continue automatically.
