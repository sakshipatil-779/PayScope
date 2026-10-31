# 11 — Validation and Test Plan

## 1. Validation goals

1. Verify that synthetic source files are parsed correctly and reproducibly.
2. Verify merchant matching and ambiguity handling.
3. Verify recurring detection for fixed, variable, annual, and irregular patterns.
4. Verify insights are evidence-backed and do not overstate certainty.
5. Verify annualisation and money calculations.
6. Verify mechanism-specific cancellation content and simulated statuses.
7. Verify the entire user journey through the UI.
8. Ensure the core app works without optional services.

## 2. Test layers and tools

- **Unit / algorithm tests:** Pytest.
- **API tests:** FastAPI TestClient/httpx with isolated test database.
- **Database tests:** migrations, constraints, unique identifiers, rollback/transaction handling.
- **Frontend/e2e:** Playwright.
- **Optional graph tests:** projection idempotency/rebuild tests.
- **Optional task tests:** Celery task retry/idempotency tests.

## 3. Synthetic acceptance dataset

Minimum demo fixture:
- 12 distinct recurring commitment scenarios.
- 80+ synthetic transactions.
- 15+ synthetic notifications.
- Several payment mechanisms.
- At least six months of transaction history; longer history for annual patterns where needed.
- Synthetic mandates.
- Usage events plus explicit coverage periods.
- Fixed random seed.

Required scenarios:

| ID | Scenario | Expected result |
|---|---|---|
| S-01 | Two descriptors map to one fictional merchant. | Same canonical merchant with raw descriptors preserved. |
| S-02 | Monthly charge increases from ₹499 to ₹649. | Price-change insight with dates, change, linked records, and annual impact only if cadence is stable. |
| S-03 | Zero/low-value trial event followed by ₹999 paid transaction. | Trial-to-paid insight with both event references. |
| S-04 | Membership with no usage events during complete 90-day synthetic coverage. | Potentially unused; wording says no recorded use during covered period. |
| S-05 | Later successful charge after recorded cancellation. | Post-cancellation charge insight with cancellation and payment evidence. |
| S-06 | Annual insurance premium. | Annual commitment candidate; not misclassified as monthly. |
| S-07 | Monthly utility charge varies. | Variable recurring bill, not automatic subscription price hike. |
| S-08 | Two music commitments. | Both listed; possible category overlap, not automatic waste. |
| S-09 | UPI mandate max ₹1,000, typical payment ₹399. | Mandate maximum distinguished from actual debit. |
| S-10 | Irregular repeated payments. | Irregular/needs-review candidate with reason and confidence. |
| S-11 | Card recurring mandate. | Card mechanism-specific playbook selected. |
| S-12 | Ambiguous descriptor. | Manual review, no false confirmed merchant. |

## 4. Unit test checklist

### File ingestion
- Valid CSV.
- Valid XLSX.
- Valid JSON notifications.
- Missing required columns.
- Invalid amount/date/currency.
- Empty file.
- Duplicate external synthetic IDs.
- Reimport of same file.
- Unsupported extension/type.
- Oversized file and malformed workbook/JSON.
- Formula-like content safely escaped on export.

### Merchant matching
- Exact normalised match.
- Exact alias match.
- Prefix/regex match.
- Fuzzy match above threshold.
- Near-match false positive below threshold.
- Conflicting aliases.
- Unknown descriptor.
- Raw descriptor preserved after matching.
- Currency/cadence evidence does not independently assert merchant identity.

### Recurrence detection
- Weekly, fortnightly, monthly, quarterly, annual.
- Month-end date shifts (28/29/30/31 days).
- Small amount variation.
- Large variable utility variation.
- Missing payment period.
- Irregular intervals.
- Failed/reversed transactions excluded from successful debit evidence as appropriate.
- Credits excluded from debit recurrence.
- Mixed currencies not clustered.
- Insufficient history results in low confidence/review.

### Insight detection
- Stable price increase.
- Amount decrease.
- Variable bill does not create false price increase.
- Trial event followed by paid charge.
- Trial with no paid charge does not create conversion.
- Missing usage coverage returns unknown.
- Complete usage coverage with no event supports “no recorded usage”.
- Cancellation event without later debit does not create zombie charge.
- Later failed debit does not count as successful charge.
- Later successful debit with uncertain merchant match has lower confidence/review.

### Financial calculations
- Weekly × 52.
- Fortnightly × 26.
- Monthly × 12.
- Quarterly × 4.
- Annual amount unchanged.
- Variable monthly estimate uses documented representative statistic and minimum history.
- Irregular cadence not annualised as certain.
- Decimal rounding and currency grouping.
- Potential savings and realised savings remain separate.

### Cancellation
- Correct playbook selected by mechanism.
- UPI pause vs revoke explained.
- Service cancellation distinct from mandate state.
- Insurance/loan caution shown.
- Generic guidance labelled generic.
- No fake support URL or contact generated.
- Checklist status remains simulated.

## 5. API integration tests

Test status codes, validation messages, pagination, filters, object ownership/workspace scoping, import idempotency, state transitions, evidence links, and demo reset isolation. Test optional service outages and expected fallback behaviour.

## 6. End-to-end Playwright journeys

1. Open app and load demo data.
2. Verify dashboard values match API/fixture calculations.
3. Open Upload Centre and import a synthetic CSV.
4. Review import summary and row errors.
5. Resolve a low-confidence merchant manually.
6. Open a recurring commitment and inspect linked transaction evidence.
7. Review a price increase.
8. Review a trial conversion.
9. Verify unused insight wording when coverage is present and when coverage is absent.
10. Review a post-cancellation charge timeline.
11. Open UPI AutoPay and card cancellation playbooks.
12. Complete a simulated checklist and verify the status label.
13. Open Annual Impact and inspect calculation assumptions.
14. Reset demo data and verify only demo workspace data changes.

## 7. Quality metrics

These are internal test targets, not external claims:

- All seeded scenarios have deterministic expected outcomes.
- 100% of P0 algorithm branches have unit tests or documented manual validation.
- Zero false “unused” result when usage coverage is absent.
- Zero false “price increase” for the seeded variable utility fixture.
- Zero duplicate transaction rows after same-file reimport.
- Every high-priority insight links to evidence.
- Every ambiguous merchant is reviewable.
- Every annual estimate is reproducible from persisted input data.
- No real financial data path exists in the application.

## 8. Test environment

Use an isolated test database and synthetic fixtures. Do not point automated tests to a real user database or real financial service. Prefer deterministic clocks/time fixtures for time-window and cadence calculations.

## 9. Defect severity

- **Blocker:** data corruption, wrong financial calculation, real-data integration/action, security exposure, or app cannot start.
- **Critical:** false high-confidence commitment/price/unused/post-cancel conclusion or wrong cancellation mechanism.
- **Major:** key workflow unavailable, data provenance missing, incorrect annual view.
- **Minor:** cosmetic, copy, or low-impact responsive defect.

All blocker/critical defects must be resolved before final acceptance or explicitly documented as blocking the demo.
