# 04 — User Workflows

## Workflow 1 — Start a synthetic demo

**Goal:** Let a tester explore a populated example without uploading any personal records.

1. User opens the application.
2. User sees a clear “Synthetic demo data” label.
3. User selects “Load demo dataset”.
4. Backend creates or resets the demo workspace using a fixed seed.
5. UI reports the number of synthetic transactions, notifications, usage events, and mandates loaded.
6. Dashboard refreshes from API data.

**Expected result:** A reproducible demo workspace. Reset must not affect unrelated user data.

## Workflow 2 — Upload a synthetic statement or notification file

1. User opens Upload Centre.
2. The page states that only synthetic data is accepted for this prototype.
3. User selects CSV, XLSX, or JSON.
4. Client checks basic type/size; backend validates content, schema, and allowed fields.
5. UI shows an import preview and detected columns.
6. User maps required columns if the schema differs.
7. User confirms import.
8. Backend creates an import record and processes rows.
9. Duplicate rows are skipped or linked according to idempotency rules.
10. UI shows accepted, rejected, duplicate, and warning counts with row-level explanations.
11. User can open the import and inspect its source records.

**Failure paths:** Unsupported file; oversized file; invalid date/amount; missing required column; malformed row; duplicate import; empty file; partial import. Do not silently discard errors.

## Workflow 3 — Review merchant identity

1. System normalises descriptor into a separate field while preserving the raw string.
2. Exact alias/pattern and fuzzy matching are attempted in documented order.
3. UI displays raw descriptor, suggested merchant, match method, confidence, and explanation.
4. High-confidence known aliases can be proposed for acceptance according to configured threshold.
5. Low-confidence or conflicting matches enter manual review.
6. User accepts, selects a different known merchant, adds an alias, or leaves the descriptor unresolved.
7. The decision is recorded with timestamp and audit event.

**Expected result:** No silent confirmation of ambiguous merchant identities.

## Workflow 4 — Review recurring commitments

1. User opens My Commitments.
2. UI lists candidate commitments with merchant, category, inferred cadence, amount summary, annual estimate (when supportable), confidence, and status.
3. User filters by category, mechanism, cadence, confidence, or alert type.
4. User opens a commitment.
5. Detail page shows linked transactions, intervals, amount changes, mandate/notification evidence, detection reason, and limitations.
6. User can confirm, correct, or mark as not recurring.
7. The system records the user's decision separately from the algorithm's inference.

## Workflow 5 — Review a price increase

1. User opens an alert from Dashboard or Insights.
2. UI shows previous and current representative amounts, dates, percentage change, and supporting transactions.
3. UI states whether the pattern is a confirmed charge difference or an inferred price event.
4. Annual impact is calculated only if cadence and representative amounts support it.
5. User can mark “Reviewed”, “Expected change”, or “Needs investigation”.

**Expected result:** Variable usage bills are not automatically described as subscription price hikes.

## Workflow 6 — Review a free-trial conversion

1. System finds a synthetic trial-start notification or zero-value trial event.
2. A later successful paid transaction is matched to the same merchant/commitment context.
3. UI shows trial date, expected/observed conversion timing, paid date, amount, and evidence.
4. If matching is uncertain, the alert is labelled “Possible trial conversion — review”.

## Workflow 7 — Review potentially unused commitment

1. System checks explicit synthetic usage-event coverage for the relevant period.
2. If coverage exists and no usage event is found during the configured window, show “No recorded usage during covered period”.
3. If coverage is missing, show “Usage information unavailable”.
4. User can confirm the service is still useful, mark it as no longer used, or review the cancellation guide.

**Never infer non-use from bank debits alone.**

## Workflow 8 — Review charge after cancellation

1. User or synthetic notification records a cancellation-confirmed date.
2. Later successful debit is associated with the same merchant/commitment using documented matching rules.
3. UI displays cancellation evidence and later debit side by side.
4. Status is “Charge detected after recorded cancellation” and includes confidence.
5. User may record a simulated support request and attach synthetic evidence.

## Workflow 9 — Follow a cancellation playbook

1. User opens a commitment and selects “Review cancellation steps”.
2. UI identifies the recorded mechanism and any uncertainty.
3. Playbook explains whether the merchant service and payment mandate are separate actions.
4. Appropriate steps are shown for UPI AutoPay, card recurring mandate, app-store subscription, direct debit, or insurance/loan.
5. User checks steps as completed in the simulation.
6. User may record request submitted, response received, cancellation confirmed, mandate paused/revoked, or further debit detected.
7. UI makes clear that these are user-recorded demo states and no external action occurred.
8. Evidence timeline is updated.

## Workflow 10 — Understand annual impact

1. User opens Annual Impact.
2. UI shows annual committed spend grouped by commitment/category.
3. Every estimate includes cadence, representative amount, formula, data window, and limitations.
4. Potential unused spend, price-increase impact, and potential savings are shown separately.
5. A user can select commitments to model a hypothetical cancellation scenario.
6. Realised savings are recorded only when the user marks an outcome as confirmed; hypothetical savings never become realised automatically.

## Workflow 11 — Reset demo

1. User opens Settings / Demo Data.
2. UI explains which synthetic workspace records will be removed or re-created.
3. User confirms reset.
4. Backend resets only the demo workspace and regenerates reproducible synthetic records.
5. UI reports the result and refreshes all views.
