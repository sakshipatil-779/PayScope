# 12 — Phased Build Plan and Handoff Protocol

## 1. How to use this plan

Build MandateLens through small, reviewable phases. The user will run one phase in Antigravity, receive a summary, send that summary to ChatGPT, and then receive the next phase prompt. Antigravity must not continue automatically.

**Rule: one prompt = one phase = one handoff summary.**

The phase list below is the complete roadmap. Only the phase explicitly authorised in the current Antigravity prompt may be implemented.

## 2. Phase sequence

### Phase 0 — Workspace audit and implementation alignment

**Goal:** Understand the existing workspace before changing it.

Deliverables:
- Read all project documents.
- Inspect existing files, package managers, runtime versions, and available services.
- Report whether the repository is empty or contains existing work.
- Propose a concrete folder structure matching the PDF stack.
- Identify conflicts, missing prerequisites, risks, and the smallest safe first implementation slice.
- Do not overwrite files; do not implement application features.

Exit criteria:
- Workspace state is accurately described.
- Proposed structure and commands are documented.
- No unrelated files changed.

### Phase 1 — Repository foundation and runnable skeleton

**Goal:** Establish the minimum monorepo structure and prove the web/API shells can run.

Deliverables:
- Create/adapt `apps/web` for Next.js + TypeScript.
- Create/adapt `apps/api` for FastAPI.
- Add root development documentation and `.env.example`.
- Add minimal web landing/health status and FastAPI health endpoint.
- Add formatting/lint/test configuration appropriate to the actual package managers.
- Add Docker Compose for PostgreSQL only if required by the approved local run path; do not add Neo4j, Celery, Gemini, OCR, or cloud resources yet.
- Add `.gitignore` and safe defaults.

Exit criteria:
- Web shell starts.
- API health endpoint responds.
- No secret is committed.
- Commands and resolved package versions are recorded.

### Phase 2 — PostgreSQL, SQLAlchemy, Alembic, and demo workspace

**Goal:** Establish authoritative persistence.

Deliverables:
- PostgreSQL local service and connection settings.
- SQLAlchemy 2.0 setup.
- Alembic initial migration.
- Initial core tables for demo user/workspace, accounts, imports, transactions, merchants, aliases, and audit events as justified by the first data slice.
- Health/readiness check for database connectivity.
- Basic repository/service patterns.

Exit criteria:
- Migration upgrades a clean database.
- Database connection works.
- A small synthetic workspace fixture persists and can be read back.
- Rollback/reset instructions are documented.

### Phase 3 — Synthetic data generator and ingestion pipeline

**Goal:** Load deterministic synthetic statement and notification records.

Deliverables:
- Faker + custom fixed-seed generator.
- CSV/XLSX/JSON sample files.
- Backend parsers and validation.
- Import provenance and row-level results.
- Duplicate prevention/idempotency.
- Upload API and first working upload UI.

Exit criteria:
- Sample files import successfully.
- Invalid rows are reported.
- Reimport creates no duplicate transactions.
- All data is clearly synthetic.

### Phase 4 — Merchant reference database and resolution

**Goal:** Convert confusing descriptors into traceable merchant candidates.

Deliverables:
- Curated fictional/demo merchant records and descriptor aliases.
- Normalisation function preserving raw strings.
- Exact, alias, regex/prefix, and RapidFuzz matching.
- Confidence bands, match reason, and manual-review flow.
- Unit tests for positives, near misses, and ambiguous aliases.

Exit criteria:
- Seed descriptor scenarios map as expected.
- Low-confidence/ambiguous cases are not automatically confirmed.
- User correction/alias action is audited.

### Phase 5 — Recurring commitment discovery

**Goal:** Detect fixed, variable, annual, and irregular recurring obligations.

Deliverables:
- Cadence interval calculations and tolerance configuration.
- Amount consistency/variation analysis.
- Commitment type classification.
- Evidence links, confidence, and detector version.
- Commitment list/detail API and initial UI.

Exit criteria:
- Seed scenarios detect expected patterns.
- Utility and insurance cases are not misclassified as ordinary subscriptions.
- Insufficient evidence produces review/unknown states.

### Phase 6 — Insight engine and annual impact calculations

**Goal:** Detect changes and quantify recurring commitments transparently.

Deliverables:
- Price increase and cadence-change detection.
- Trial-to-paid detection.
- Usage coverage and potentially-unused logic.
- User-confirmed cancellation and later successful debit detection.
- Annualisation and potential-vs-realised savings calculations.
- Insight and annual impact UI/API.

Exit criteria:
- All seeded insight scenarios pass tests.
- Variable bill does not create false subscription price alert.
- Missing usage coverage never becomes “unused”.
- All totals are reproducible and currency-aware.

### Phase 7 — Mechanism-aware cancellation centre and evidence tracking

**Goal:** Explain the appropriate simulated route for each payment mechanism.

Deliverables:
- Playbooks for UPI AutoPay, card recurring, app-store subscription, direct debit/bank instruction, and insurance/loan obligations.
- Generic vs verified merchant-specific metadata.
- Pause vs revoke explanation.
- Service cancellation vs mandate action distinction.
- Checklist, simulated attempt statuses, evidence timeline, and escalation template.

Exit criteria:
- Each mechanism selects the correct guide.
- No real action or external contact is executed.
- Insurance/loan caution is visible.
- UI does not overstate a simulated status as an externally verified result.

### Phase 8 — Dashboard, transaction explorer, and UX integration

**Goal:** Connect all core workflows into a polished end-to-end application.

Deliverables:
- Overview dashboard with API-backed KPIs/charts.
- Transaction explorer with search/filter/pagination.
- Navigation and consistent component system.
- Loading, empty, error, and responsive states.
- ECharts visualisations driven by real API responses.

Exit criteria:
- Core user journey can be completed without developer tools.
- No fabricated dashboard values.
- Responsive/accessibility checks completed.

### Phase 9 — Celery + Redis background processing

**Goal:** Make long-running imports/analytics asynchronous where needed.

Deliverables:
- Redis service.
- Celery worker and task configuration.
- Import job state and polling/status API.
- Retry/idempotency strategy.
- Failure reporting and safe task payload design.

Exit criteria:
- Long-running task can be queued, processed, and inspected.
- Retries do not duplicate data.
- Core synchronous fallback or understandable failure state is defined.

### Phase 10 — Optional Neo4j relationship projection

**Goal:** Visualise real relationships between source records and commitments.

Deliverables:
- Neo4j service/configuration.
- Idempotent projection and rebuild process from PostgreSQL.
- Graph API.
- Cytoscape.js graph page and legend/detail panel.

Exit criteria:
- Projection matches PostgreSQL IDs/relationships.
- Graph can be rebuilt.
- Core application remains functional with Neo4j stopped.

### Phase 11 — Optional Gemini, statistics/ML refinement, and monitoring

**Goal:** Add only measured enhancements after deterministic functionality is correct.

Deliverables may include:
- Gemini explanations of verified structured insights with deterministic fallback.
- Statsmodels/SciPy refinement where tests demonstrate value.
- Scikit-learn anomaly signal as secondary review evidence.
- Sentry + OpenTelemetry.

Exit criteria:
- Core truth remains deterministic.
- No LLM/ML-only financial conclusion.
- Optional integrations fail gracefully and are disabled without credentials.

### Phase 12 — Hardening, full validation, and demo readiness

**Goal:** Validate the complete prototype.

Deliverables:
- Full Pytest suite.
- Playwright critical user journeys.
- Security/trust checklist.
- Clean Docker Compose startup instructions.
- Seed/reset/demo instructions.
- Known limitations and final build report.

Exit criteria:
- MVP acceptance criteria pass or blockers are clearly documented.
- All key demo scenarios are reproducible.
- No real financial integration/action exists.

## 3. Phase dependencies

- Phase 0 precedes all implementation.
- Phase 1 precedes all application services.
- Phase 2 precedes persistence-dependent ingestion.
- Phase 3 precedes merchant and recurrence analysis using imported files.
- Phase 4 precedes high-confidence merchant-based recurrence grouping.
- Phase 5 precedes price/cadence insight calculations.
- Phase 6 precedes annual impact acceptance.
- Phase 7 can proceed once commitments and mechanisms exist.
- Phase 8 integrates completed core APIs and workflows; visual components may be created earlier only when their API contract is already stable.
- Phase 9 is not a prerequisite for small demo imports.
- Phase 10 is optional and non-blocking.
- Phase 11 is optional and non-blocking.
- Phase 12 follows core phases and any optional components actually selected.

## 4. Mandatory handoff format

At the end of every phase, Antigravity must stop and produce:

1. **Phase completed**
2. **What changed**
3. **Implementation details**
4. **Commands executed**
5. **Tests and validation**
6. **Acceptance criteria status**
7. **Known issues and risks**
8. **Database or data changes**
9. **How to run or verify**
10. **Recommended next phase**
11. **Handoff notes for ChatGPT**

Include exact file paths and relevant command output. Do not hide warnings. Do not claim success for unrun tests.

## 5. Change-control rule

The user will send the phase summary to ChatGPT. ChatGPT will review the actual implementation status and produce the next phase-specific prompt. Antigravity must wait for that new prompt. Do not automatically start the next phase, create its implementation, or make unrelated “future-proofing” changes.
