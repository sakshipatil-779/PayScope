# AGENTS.md — MandateLens Agent Operating Rules

This file governs every coding-agent session in this repository. Read it before making changes.

## 1. Project identity

MandateLens is a **synthetic-data-only recurring-payment intelligence prototype**. It discovers recurring commitments from statement-like records and payment notifications, resolves raw descriptors to recognisable merchants, explains evidence-backed changes, estimates annual cost, and provides mechanism-specific cancellation guidance.

The product does **not** connect to banks, UPI networks, card networks, app stores, insurers, lenders, or payment processors. It does **not** execute cancellations, revoke mandates, block payments, initiate refunds, or contact merchants.

## 2. Required reading order

At the beginning of a new task or agent session, read:

1. `AGENTS.md`
2. `MASTER_BUILD_BRIEF.md`
3. `00_PROJECT_CHARTER.md`
4. `01_PROBLEM_STATEMENT.md`
5. `02_RESEARCH_EVIDENCE.md`
6. `03_USER_PERSONAS.md`
7. `04_USER_WORKFLOWS.md`
8. `05_PRODUCT_REQUIREMENTS.md`
9. `06_MVP_SCOPE.md`
10. `07_UX_UI_SPEC.md`
11. `08_TECHNICAL_ARCHITECTURE.md`
12. `09_DATA_MODEL.md`
13. `10_SECURITY_AND_TRUST.md`
14. `11_VALIDATION_AND_TEST_PLAN.md`
15. `12_BUILD_PLAN.md`

If the repository already contains code, inspect it before proposing or changing its structure. Preserve useful existing work. Do not overwrite unrelated files.

## 3. Mandatory phase-gated development protocol

**Never attempt to build the whole application in one prompt or one agent session.** Development is divided into the phases defined in `12_BUILD_PLAN.md`.

For every Antigravity task:

1. Read the relevant project documents and the user's latest handoff summary.
2. Identify the single phase explicitly authorised by the current prompt.
3. Work only within that phase's scope and exit criteria.
4. Do not start, partially implement, or silently prepare later phases unless the current phase explicitly requires a small interface stub.
5. Run the relevant tests and checks available for the work completed.
6. Update documentation only where the current phase requires it.
7. Return the required **Phase Handoff Summary** (format below).
8. Stop. Wait for a new user prompt before continuing.

Do not treat the presence of all requirements in the repository as permission to implement all of them. The current prompt authorises only one phase.

### Required Phase Handoff Summary

Return these headings in this exact order:

1. **Phase completed** — phase number and title.
2. **What changed** — concise list of created/modified files and purpose.
3. **Implementation details** — key decisions and behaviour implemented.
4. **Commands executed** — exact commands used.
5. **Tests and validation** — each check, result, and any skipped check with reason.
6. **Acceptance criteria status** — pass / partial / blocked for each criterion in the phase.
7. **Known issues and risks** — include errors, limitations, assumptions, and unresolved questions.
8. **Database or data changes** — migrations, seed changes, schema changes, and whether they were applied.
9. **How to run or verify** — exact steps for the user.
10. **Recommended next phase** — name only; do not implement it.
11. **Handoff notes for ChatGPT** — anything the next prompt must know, including paths, exact errors, package versions, and incomplete work.

Never claim a test passed unless you actually ran it and observed a successful result. Distinguish “not run” from “passed”.

## 4. Technology decisions — do not substitute without permission

Use the stack from the MandateLens hybrid technology-stack PDF:

| Layer | Required direction |
|---|---|
| Frontend | Next.js + TypeScript |
| UI | Tailwind CSS + shadcn/ui |
| Animation | Framer Motion where useful; optional, not a dependency for core functionality |
| Charts | Apache ECharts |
| Graph visualisation | Cytoscape.js |
| Backend API | Python + FastAPI; one primary API and orchestration service |
| Database | PostgreSQL; authoritative source of truth |
| ORM / migrations | SQLAlchemy 2.0 + Alembic |
| Relationship graph | Neo4j; optional derived projection, never required for core flows |
| Background work | Celery |
| Broker / cache | Redis |
| Data processing | Pandas; Polars may be added when beneficial |
| Merchant matching | RapidFuzz + regex + curated reference database |
| Statistical analysis | NumPy + SciPy + Statsmodels where useful |
| ML anomaly support | Scikit-learn optional; never sole basis for a financial conclusion |
| LLM | Google Gemini API optional; explanations only from verified structured outputs |
| Synthetic data | Faker + deterministic custom Python generators |
| Authentication | Choose one integrated approach. Default: FastAPI-managed session authentication for the demo; do not add Auth.js as a second identity system unless explicitly authorised |
| File input | CSV / XLSX / JSON first; PDF extraction optional later with PyMuPDF or pdfplumber |
| OCR | PaddleOCR optional and deferred unless specifically authorised |
| File storage | Local development storage; S3-compatible storage only if deployment requires it |
| Testing | Pytest + Playwright |
| Deployment | Docker + Docker Compose; cloud hosting is not required for local hackathon validation |
| Monitoring | Sentry + OpenTelemetry may be added after core workflows work |

Choose mutually compatible, currently supported dependency versions at implementation time and record exact resolved versions in lockfiles. Do not invent version compatibility claims. Avoid adding unnecessary frameworks or duplicative services.

## 5. Architecture rules

- PostgreSQL is authoritative for all core application data.
- Neo4j is a derived graph projection. PostgreSQL-backed core screens and calculations must still work if Neo4j is unavailable.
- FastAPI owns API validation, orchestration, business operations, and calls to the analytics modules.
- Python analytics must be deterministic and testable independently of the web UI.
- Celery + Redis are for longer-running or scheduled tasks; do not introduce them before a synchronous vertical slice is working unless the authorised phase requires the infrastructure.
- Keep frontend presentation separate from financial and recurrence calculations.
- Use explicit schemas and migrations. Do not rely on ad hoc database table creation in production paths.
- Keep API contracts documented and typed.

## 6. Data, evidence, and algorithm rules

- Synthetic data only. Never ask for or process a real bank statement, real card statement, actual UPI notification, real account credential, or real financial identifier.
- Every generated record must be visibly labelled synthetic and reproducible from a fixed seed.
- Preserve the original synthetic transaction descriptor. Normalisation must create a separate field; do not overwrite source evidence.
- A recurring commitment is an inference supported by transactions and/or mandate/notification evidence. Store the evidence and confidence behind it.
- Separate **Observed**, **Inferred**, **User-confirmed**, **Hypothesis**, and **Assumption** data.
- Do not call every repeated charge a subscription. Distinguish subscription, membership, utility, insurance, loan/EMI, other recurring obligation, and needs-review.
- Do not infer service usage from payment history. Usage conclusions require explicit synthetic usage coverage or user confirmation.
- Do not classify a charge as a confirmed post-cancellation charge unless a cancellation event/date is recorded and a later successful debit is linked with sufficient confidence.
- Do not confuse a variable utility bill with a subscription price increase.
- All calculations must be deterministic, traceable, and covered by tests.
- Every insight must include a reason, evidence references, confidence, and limitations.
- Gemini, if enabled, may explain structured findings. It must not invent merchant identities, financial calculations, support contacts, legal rights, cancellation routes, or source citations.

## 7. Cancellation and trust boundaries

- Cancellation guidance is informational and simulated. No real-world action may be performed by the application.
- Different mechanisms require different playbooks: UPI AutoPay, card recurring mandate, app-store subscription, direct debit/bank instruction, and insurance/loan obligations.
- Clearly distinguish cancelling the merchant service from pausing or revoking a payment mandate.
- Insurance and loan guidance must warn users to review policy/loan terms and contact the provider before stopping payments.
- Never fabricate merchant support URLs, phone numbers, policies, statutory deadlines, regulator procedures, or guaranteed outcomes.
- Merchant-specific steps need a source, verification date, region, and confidence. If not verified, label guidance as generic mechanism-level instructions.
- The app records a user's simulated checklist and evidence; it does not claim cancellation has occurred externally.

## 8. Security and engineering quality

- Do not commit secrets, API keys, cookies, real credentials, or personal data.
- Provide `.env.example` with placeholders only.
- Validate file extension, MIME type, size, encoding, and schema. Treat file contents as untrusted.
- Protect upload processing against oversized files, malformed rows, formula injection in exports, and path traversal.
- Use parameterised SQL / ORM queries; never interpolate user-controlled SQL.
- Apply least-privilege service credentials and safe CORS/session settings.
- Do not expose raw internal errors or secrets to the frontend.
- Use structured logs without sensitive payloads.
- Do not run destructive database operations without explicit authorisation and a clear backup/reset explanation.
- Add tests for important business rules and edge cases.
- Do not leave broken buttons, misleading placeholders, or fake data presented as live user data.

## 9. Scope discipline

- The current phase in `12_BUILD_PLAN.md` is the source of truth for what is authorised now.
- “Optional” means defer unless the current prompt authorises it.
- Prefer a narrow, working vertical slice over broad unfinished scaffolding.
- If a requirement conflicts with a source document, do not silently resolve it. Explain the conflict in the handoff summary and choose the safer, narrower interpretation only when necessary to proceed.
- If the workspace or environment prevents a requirement from being completed, report the blocker honestly.

## 10. Definition of done for each phase

A phase is complete only when:

- Its stated deliverables exist.
- Its exit criteria have been checked.
- Relevant automated or manual validation has been run.
- No known regression introduced by the phase remains unreported.
- The Phase Handoff Summary is complete.
- The agent has stopped without starting the next phase.
