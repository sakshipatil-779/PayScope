# 10 — Security, Privacy, and Trust Requirements

## 1. Trust promise

MandateLens hackathon prototype uses synthetic records only. It does not connect to or operate real financial accounts. All sample files, transactions, notifications, mandates, usage signals, and cancellation records must be generated or clearly marked synthetic.

## 2. Prohibited data and actions

Do not request, upload, store, process, or transmit:
- Real bank or card statements.
- Real UPI/SMS/payment notifications.
- Bank login credentials, card numbers, CVVs, PINs, OTPs, or passwords.
- Actual UPI IDs or account identifiers.
- Real insurance or loan account documents.
- Real financial personal data for testing.

Do not:
- Connect to bank/payment-provider APIs.
- Execute payment, refund, chargeback, mandate pause/revocation, cancellation, or dispute actions.
- Send emails/messages or call merchants on the user's behalf.
- Claim that a simulated step was performed externally.

## 3. Upload security

- Accept only allowed file types for the current phase (CSV/XLSX/JSON first).
- Verify filename extension and inspect content format where possible; MIME type alone is not sufficient.
- Enforce configurable file and row-count limits.
- Reject path traversal, macro-enabled or unsupported workbook formats, malformed archives, invalid encodings, and unexpected schema content.
- Store files outside the public web root with generated storage keys.
- Do not trust client-side validation; validate again on the backend.
- Sanitize filenames displayed in the UI.
- Escape text rendered from descriptors/notifications.
- Prevent spreadsheet formula injection when exporting text values (for example, leading formula control characters).
- Use timeouts and safe parser settings; handle corrupt files without crashing the service.
- Record row-level errors without exposing filesystem paths or stack traces.

## 4. Authentication and session controls

The supplied stack allows Auth.js or FastAPI-compatible session authentication. For the prototype, use one integrated approach: FastAPI-managed session authentication unless the user explicitly approves a change.

- Use HttpOnly cookies.
- Set Secure in production.
- Set SameSite appropriately and configure strict allowed origins.
- Use CSRF protection for cookie-authenticated state-changing requests.
- Use short-lived demo sessions and rotate identifiers on authentication boundaries.
- Never place secret tokens in browser localStorage or frontend bundles.
- Do not add two independent authentication systems.
- If a single demo workspace is used, document the reduced authentication scope and keep it isolated from any real user data.

## 5. Secrets and configuration

- Keep API keys, DB credentials, session secrets, and any Gemini key in environment variables or a secrets manager.
- Commit `.env.example` with placeholders only.
- Add `.env`, uploads, generated private data, and credentials to `.gitignore`.
- Validate required environment variables at startup.
- Never log secrets or full cookie values.
- Gemini must remain disabled when its key is absent; deterministic explanations remain available.

## 6. Database and API security

- Use SQLAlchemy parameterised queries; do not concatenate SQL with user data.
- Apply database constraints and least-privilege credentials.
- Restrict CORS to the local/deployed frontend origin.
- Validate all request bodies, query parameters, pagination, enum values, and path IDs.
- Add request IDs and structured error responses.
- Avoid returning internal stack traces, SQL errors, storage paths, or secret configuration.
- Rate-limit high-cost upload or generation endpoints if exposed beyond local development.

## 7. Financial calculation trust

- Use Decimal/Numeric for monetary values.
- Store currency explicitly and never sum different currencies without a separately defined conversion source (currency conversion is out of MVP scope).
- Every annual estimate must show cadence, representative amount, formula, source period, and limitations.
- Separate current annual committed spend, potential unused expenditure, annual price increase impact, potential savings, and realised savings.
- Do not count hypothetical cancellation savings as realised.
- Do not label a payment as fraudulent or unauthorised based only on a pattern.
- Show confidence bands as model/system confidence indicators, not calibrated probabilities unless calibration work is completed and documented.

## 8. Evidence and uncertainty

For every insight retain:
- Input transaction/notification/usage/cancellation IDs.
- Detection rule and version.
- Observed values.
- Inferred values.
- Confidence and reason codes.
- Known limitations.
- User correction/confirmation history.

A missing usage event without a documented coverage interval must produce “Usage information unavailable”, not “Unused”.

A later debit can be flagged after cancellation only when a cancellation event/date has been recorded and the later transaction is successful and sufficiently linked.

## 9. Cancellation guidance trust

- Guidance is informational and simulated.
- Distinguish a merchant-service cancellation from a payment mandate pause or revocation.
- Use generic mechanism-level steps when merchant-specific instructions are not verified.
- For merchant-specific playbooks, record source URL/description, region, verification date, and review status.
- Do not fabricate support contacts, cancellation links, notice periods, regulatory obligations, complaint escalation routes, or refund guarantees.
- Warn that insurance and loan payment changes may affect coverage, arrears, fees, or contractual obligations; users should review their agreement and contact the provider before stopping payment.
- A user-recorded “cancelled” status means only that the user recorded an external confirmation; it is not independently verified by the prototype.

## 10. Gemini boundary

If Gemini is enabled:
- Send only minimum necessary synthetic structured facts.
- Do not send uploaded file contents or identifiers.
- Ask it to explain supplied facts without adding new ones.
- Validate output and provide a deterministic fallback.
- Never let it decide recurrence, merchant identity, price change, annual totals, usage status, legal requirements, or cancellation route.
- Label generated wording as an explanation, not independent evidence.

## 11. Audit and retention

- Audit important user decisions, merchant corrections, demo resets, cancellation checklist changes, and evidence additions.
- Do not store unnecessary raw file content indefinitely.
- Provide a demo reset that affects only synthetic demo data and explains what will be reset.
- Use local non-public storage during the prototype; deployment storage requires explicit access controls and retention policy.

## 12. Incident and failure behaviour

- If an optional service (Neo4j, Redis/Celery, Gemini, OCR, S3) is unavailable, the core app should show a clear warning and continue where possible.
- If analytics fails, do not silently show stale metrics as current. Show last successful analysis time and error.
- If merchant matching is ambiguous, route to manual review.
- If playbook source is missing or stale, show generic guidance and a verification warning.
