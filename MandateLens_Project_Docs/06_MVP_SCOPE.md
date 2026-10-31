# 06 — MVP Scope and Prioritisation

## 1. MVP objective

Prove one complete user journey using deterministic synthetic data:

**Import/load data → resolve merchant → discover recurring commitment → explain an insight → calculate annual impact → show correct simulated cancellation guidance → record evidence/status.**

## 2. Must have — MVP (P0)

### Data foundation
- Reproducible synthetic generator using Faker plus custom deterministic rules.
- CSV, XLSX, and JSON ingestion.
- Import preview, validation, row errors, and duplicate handling.
- PostgreSQL schema using SQLAlchemy 2.0 and Alembic.

### Intelligence
- Curated merchant reference set and descriptor aliases.
- Exact/alias/regex/fuzzy matching using RapidFuzz.
- Manual review for ambiguous descriptors.
- Fixed, variable, annual, and irregular recurrence detection.
- Confidence, reasoning, and evidence references.
- Price increase, trial conversion, potentially unused with usage coverage, and post-cancellation charge scenarios.
- Annualisation formulas and assumptions.

### User experience
- Dashboard with real metrics.
- Commitments list and detail.
- Transaction explorer.
- Insights page.
- Annual impact page.
- Cancellation playbooks and simulated checklist.
- Upload centre and synthetic demo reset.

### Trust
- Synthetic-only warning and labels.
- Raw descriptor preserved.
- Observed/inferred/user-confirmed distinctions.
- No real-world cancellation or payment action.

## 3. Should have — after core MVP is stable (P1)

- Celery + Redis background processing for long imports and analytics jobs.
- Neo4j graph projection and Cytoscape.js relationship explorer.
- More robust statistics using SciPy/Statsmodels where a clear rule benefits.
- Polars for larger synthetic datasets if measurement justifies it.
- Additional duplicate/category-overlap insights.
- Sentry and OpenTelemetry.

## 4. Could have — optional enhancements (P2)

- Gemini explanations of verified structured insights.
- PDF statement text/table extraction using PyMuPDF or pdfplumber.
- OCR using PaddleOCR for synthetic scanned images.
- S3-compatible object storage for hosted deployment.
- Scikit-learn anomaly signal as a secondary review signal.
- More advanced role/tenant support.

## 5. Won't have in this hackathon prototype

- Real banking or payment account connectivity.
- Real financial statements or real user financial data.
- Actual cancellation, mandate pause/revocation, payment blocking, dispute submission, refund, or merchant contact.
- Real card/UPI credentials or account linking.
- Legal advice or guaranteed regulatory escalation outcomes.
- Automatic inference that any commitment is wasteful.
- Automatic claim of service non-use without usage evidence.
- ML/LLM replacing deterministic calculations or curated merchant matching.
- OCR, PDF ingestion, or Neo4j blocking the first working vertical slice.

## 6. Suggested MVP demo dataset

Create at least 12 distinct recurring scenarios, 80+ synthetic transactions, 15+ synthetic notifications, synthetic mandates, and explicit usage-event coverage. Use additional historical periods for annual commitments where needed.

Required scenarios:

1. Same canonical merchant under two descriptors.
2. Monthly subscription with a silent price increase.
3. Free trial followed by paid conversion.
4. Membership with no recorded usage during covered period.
5. Successful charge after user-confirmed cancellation.
6. Annual insurance premium.
7. Variable monthly utility bill.
8. Two subscriptions in the same category.
9. UPI AutoPay with a maximum amount higher than usual debit.
10. Irregular recurring merchant payment.
11. Card recurring mandate.
12. Unknown/ambiguous merchant routed to manual review.

Use fictional merchant names in the demo where possible. If recognisable brands are used for demonstration, label records as synthetic examples and do not imply affiliation or verified policy details.

## 7. Scope gate

Do not start P1/P2 work until P0 requirements pass their tests and the complete core user journey is demonstrable. Optional technology in the stack is not permission to add complexity early.
