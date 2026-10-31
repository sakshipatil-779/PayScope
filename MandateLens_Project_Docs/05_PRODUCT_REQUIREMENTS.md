# 05 — Product Requirements

## 1. Requirement conventions

- **P0:** required for MVP acceptance.
- **P1:** important after the core vertical slice works.
- **P2:** optional enhancement.
- **Observed:** directly present in imported synthetic records.
- **Inferred:** algorithmic conclusion from observed records.
- **User-confirmed:** explicit user action stored separately.

## 2. Functional requirements

### A. Demo and data ingestion

| ID | Priority | Requirement | Acceptance condition |
|---|---|---|---|
| FR-001 | P0 | Load a reproducible synthetic demo dataset. | Fixed seed produces documented scenarios and stable expected outcomes. |
| FR-002 | P0 | Import synthetic CSV, XLSX, and JSON files. | Valid records persist; unsupported/invalid input returns readable errors. |
| FR-003 | P0 | Preview and map input columns. | User can inspect rows and map required fields before import. |
| FR-004 | P0 | Prevent duplicate transaction ingestion. | Re-importing same stable synthetic transaction IDs does not create duplicate transactions. |
| FR-005 | P0 | Preserve import provenance and raw descriptor. | Each transaction links to its import/source row; raw descriptor is unchanged. |
| FR-006 | P1 | Process longer imports asynchronously. | Celery job status is visible and errors are recorded. |
| FR-007 | P2 | Extract text/tables from synthetic PDFs. | Optional PDF path is isolated and disabled unless specifically built. |

### B. Merchant intelligence

| ID | Priority | Requirement | Acceptance condition |
|---|---|---|---|
| FR-010 | P0 | Maintain canonical merchant reference records. | Merchant has canonical name, category, aliases/patterns, and provenance metadata. |
| FR-011 | P0 | Normalise descriptors without overwriting raw values. | Both raw and normalised text are stored. |
| FR-012 | P0 | Apply deterministic matching order. | Exact → alias/pattern → regex/prefix → fuzzy → corroboration → review. |
| FR-013 | P0 | Expose match reason and confidence. | Detail shows matching method, score/band, and source alias. |
| FR-014 | P0 | Route uncertain matches to manual review. | Low-confidence or conflicting match remains unresolved pending review. |
| FR-015 | P1 | Allow a user to add/correct a merchant alias. | Decision is audited and influences later synthetic matching. |

### C. Recurring commitment discovery

| ID | Priority | Requirement | Acceptance condition |
|---|---|---|---|
| FR-020 | P0 | Discover likely recurring debits. | Seeded fixed and variable recurring cases are detected with documented reasons. |
| FR-021 | P0 | Support irregular amounts and intervals. | Detection does not require exact amount or exact calendar-day gaps. |
| FR-022 | P0 | Classify cadence. | Weekly, fortnightly, monthly, quarterly, annual, variable, irregular, or needs-review. |
| FR-023 | P0 | Distinguish commitment types. | Subscription, membership, utility, insurance, loan/EMI, other recurring, needs-review. |
| FR-024 | P0 | Assign confidence and evidence. | Every inferred commitment has confidence and linked transactions/notifications. |
| FR-025 | P0 | Support user correction/confirmation. | User-confirmed state does not overwrite original algorithmic finding. |
| FR-026 | P1 | Detect duplicate/category overlaps. | Shows possible overlap as a review suggestion, not an automatic waste claim. |

### D. Insight detection

| ID | Priority | Requirement | Acceptance condition |
|---|---|---|---|
| FR-030 | P0 | Detect sustained price/amount changes. | Prior/current values, dates, percentage, evidence, and caveat are shown. |
| FR-031 | P0 | Avoid false subscription price alerts for variable bills. | Variable-bill rules classify ordinary variation separately from price events. |
| FR-032 | P0 | Detect trial-to-paid conversion from explicit events and later debit. | Timeline shows trial evidence and paid transaction; uncertain match is labelled possible. |
| FR-033 | P0 | Detect potential unused service only with usage coverage. | No-coverage case displays unavailable, not unused. |
| FR-034 | P0 | Detect later charge after user-confirmed cancellation. | Cancellation event and later successful debit are both visible. |
| FR-035 | P1 | Detect billing frequency changes or mandate amount outliers. | Alert includes historical pattern and evidence. |

### E. Annual impact

| ID | Priority | Requirement | Acceptance condition |
|---|---|---|---|
| FR-040 | P0 | Calculate annual committed spend. | Cadence formulas are tested and displayed. |
| FR-041 | P0 | Separate recurring spend by category and type. | Dashboard and annual page use persisted commitments. |
| FR-042 | P0 | Separate potential savings from realised savings. | Simulated selection does not count as realised savings. |
| FR-043 | P0 | Show estimation assumptions. | Cadence, representative amount, period, currency, and limitations are accessible. |
| FR-044 | P1 | Model hypothetical cancellation combinations. | Selected commitments update a clearly labelled scenario estimate. |

### F. Cancellation and evidence

| ID | Priority | Requirement | Acceptance condition |
|---|---|---|---|
| FR-050 | P0 | Provide mechanism-specific playbooks. | UPI AutoPay, card, app-store, direct debit, insurance/loan scenarios have distinct content. |
| FR-051 | P0 | Distinguish merchant cancellation from mandate action. | UI explains the distinction wherever relevant. |
| FR-052 | P0 | Explain pause vs revoke for UPI AutoPay. | Generic explanation is shown; no actual mandate action is offered. |
| FR-053 | P0 | Provide checklist and simulated status tracking. | User can record steps and status without external action. |
| FR-054 | P0 | Provide escalation/evidence checklist. | Template and evidence timeline are available; no invented support contact. |
| FR-055 | P0 | Preserve audit/evidence history. | User actions and source evidence have timestamps and references. |
| FR-056 | P0 | Warn on insurance/loan consequences. | User is advised to review agreement and contact provider before stopping payment. |

### G. User interface and graph

| ID | Priority | Requirement | Acceptance condition |
|---|---|---|---|
| FR-060 | P0 | Provide Dashboard, Commitments, Transactions, Insights, Annual Impact, Cancellation, Upload, and Settings/Demo Data pages. | Navigation and primary journeys work. |
| FR-061 | P0 | Provide search, filters, sorting, and detail views. | Results are driven by API data. |
| FR-062 | P1 | Render a relationship graph with Cytoscape.js. | Graph uses real PostgreSQL-derived relationships; app still works if graph service is off. |
| FR-063 | P1 | Integrate Neo4j as optional projection. | Projection can be rebuilt from PostgreSQL and is non-authoritative. |
| FR-064 | P2 | Add Gemini plain-language explanations. | LLM receives structured verified fields and cannot calculate or invent facts. |

## 3. Non-functional requirements

- **NFR-01 Reliability:** core features function with PostgreSQL and FastAPI; optional services fail gracefully.
- **NFR-02 Explainability:** each inferred commitment/insight exposes evidence and reason.
- **NFR-03 Data integrity:** relational constraints, migrations, idempotent imports, and currency-aware amounts.
- **NFR-04 Security:** synthetic-only policy, input validation, safe file storage, secrets via environment, session protections.
- **NFR-05 Performance:** paginate transaction lists; process large imports asynchronously when implemented.
- **NFR-06 Accessibility:** keyboard navigation, semantic labels, accessible contrast, and no colour-only status cues.
- **NFR-07 Maintainability:** separate frontend, API, analytics, persistence, and optional adapters.
- **NFR-08 Reproducibility:** fixed-seed synthetic generator and deterministic calculation tests.
- **NFR-09 Observability:** actionable logs and job errors without sensitive payload logging.
- **NFR-10 Transparency:** estimates, confidence, and simulation status are clearly labelled.

## 4. API contract expectations

All endpoints are versioned under `/api/v1`. Use validated request/response schemas, consistent error payloads, pagination for collections, and explicit status values. Do not expose ORM objects directly. API endpoint inventory is maintained in `08_TECHNICAL_ARCHITECTURE.md` and may be refined during implementation without changing product requirements.

## 5. Acceptance rule

A feature is not complete because a screen exists. It is complete when its underlying data, API behaviour, business logic, user action, and relevant test are connected end to end.
