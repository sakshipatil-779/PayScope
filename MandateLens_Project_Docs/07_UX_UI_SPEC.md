# 07 — UX / UI Specification

## 1. Experience goals

The interface should feel like a trustworthy financial intelligence workspace: calm, analytical, readable, and transparent about uncertainty. It should help a user understand a record rather than pressure them to cancel everything.

## 2. Design direction

- Desktop-first responsive SaaS dashboard with usable mobile layouts.
- Deep midnight navy / slate surfaces or a carefully balanced light-neutral surface system.
- Clear text contrast, restrained accent colours, consistent spacing, subtle borders, and limited shadows.
- Emerald for positive/confirmed savings outcomes, amber for review/warning, and coral/red for high-priority attention. Do not rely on colour alone.
- Use a consistent modern sans-serif font and Lucide icon set.
- Use Framer Motion only for subtle, meaningful transitions; reduced-motion preferences must be respected.
- Use ECharts for real API-backed metrics and Cytoscape.js for the optional graph.

Avoid visual clutter, excessive gradients, meaningless animation, fabricated figures, decorative charts, and oversized empty dashboard cards.

## 3. Global navigation

Suggested sidebar:

1. Overview
2. My Commitments
3. Transactions
4. Insights & Alerts
5. Annual Impact
6. Cancellation Centre
7. Relationship Graph (only when enabled)
8. Upload Centre
9. Settings / Demo Data

Global elements:
- Product name and synthetic-demo marker.
- Current demo workspace indicator.
- Search where applicable.
- Clear loading/error status.
- Help text for confidence and annual estimates.

## 4. Screen specifications

### 4.1 Overview dashboard

Show KPI cards:
- Active commitments.
- Estimated annual committed spend.
- Potential annual savings (not realised savings).
- Open insights/alerts.
- Potentially unused commitments (only with usage coverage).

Charts:
- Monthly recurring spend trend.
- Annual cost by category.
- Commitment type/mechanism distribution.
- Price-change history.

Supporting areas:
- Recent discoveries.
- Upcoming estimated billing dates when cadence supports it.
- Highest-priority review items.
- Data coverage notice and last import date.

Each card/chart must be API-backed and have loading, empty, and error states. Use currency-aware formatting. Never use hardcoded demo values as if they were live calculations.

### 4.2 My Commitments

Table/list columns:
- Merchant / raw descriptor preview.
- Category / commitment type.
- Estimated amount and cadence.
- Estimated annual cost (or “Not enough data”).
- Payment mechanism.
- Confidence / review status.
- Insight badges.
- Last observed payment.

Filters: category, type, mechanism, cadence, status, confidence, price increase, possible unused, unknown merchant. Search by canonical name or raw descriptor. Sorting must be deterministic.

### 4.3 Commitment detail

Sections:
- Merchant identity and match explanation.
- Raw descriptor aliases.
- Commitment type and inferred cadence.
- Representative amount and variation.
- Annual estimate and formula.
- Linked transaction timeline.
- Related notification and mandate evidence.
- Price/other event timeline.
- Usage coverage and last recorded usage, if available.
- Cancellation playbook and simulated status.
- Confidence, limitations, and user correction controls.

### 4.4 Transaction explorer

Show date, raw descriptor, resolved merchant, signed amount, currency, status, channel, linked commitment, import source, and review status. Support search/filter/sort/pagination. Keep raw and resolved text visually distinct.

### 4.5 Insights and alerts

Insight types: price increase, trial-to-paid, billing frequency change, potential unused, post-cancellation charge, unusual amount, and unresolved merchant. Each insight card must show “Why this was flagged”, evidence links, confidence, and what remains unknown.

### 4.6 Annual Impact

Display annual committed spend, category breakdown, subscriptions vs other obligations, price increase impact, potential unused expenditure, and potential savings. Explain the calculation formula and data coverage. Separate estimated potential savings from user-confirmed realised savings. Allow a hypothetical selection scenario with a clear “What-if estimate” label.

### 4.7 Cancellation Centre

Display mechanism, merchant, commitment, amount/cadence, caveats, step-by-step guide, checklist, evidence items, and simulated request status. The primary CTA must say “Open guide” or “Record step”, not “Cancel now” if no actual action occurs.

For UPI AutoPay, explain service cancellation versus mandate pause/revocation. For insurance/loan, show a prominent caution before any mandate-related step.

### 4.8 Upload Centre

Include synthetic-data-only banner, drag/drop, file picker, accepted type/size information, preview, column mapping, validation summary, progress, row error report, and import history. Provide downloadable synthetic sample files.

### 4.9 Settings / Demo Data

Show synthetic dataset status, load/reset demo data, seed version, and safe reset confirmation. Explain what is reset. Never imply a real account is connected.

### 4.10 Relationship graph (optional)

Cytoscape.js canvas with node-type legend, zoom/pan, selection, and side panel. Graph must be sourced from actual related records and must degrade gracefully when Neo4j is disabled.

## 5. Status language

Prefer precise labels:
- “Observed transaction”
- “Likely recurring”
- “Needs review”
- “Merchant match suggested”
- “User confirmed”
- “No usage recorded during covered period”
- “Usage information unavailable”
- “Charge detected after recorded cancellation”
- “Potential annual savings”
- “Simulated checklist status”

Avoid unsupported labels such as “fraud”, “scam”, “definitely unused”, “cancelled successfully” (unless only described as user-recorded external confirmation), or “guaranteed savings”.

## 6. Interaction requirements

- Every visible primary button must perform a real action or be clearly disabled with an explanation.
- Use confirmation for destructive demo resets.
- Use optimistic updates only when rollback/error handling exists.
- Preserve filters when opening and returning from details where practical.
- Show actionable inline errors and retry options.
- Use skeletons for data loading and helpful empty states.
- Ensure forms have labels, validation messages, keyboard access, and focus management.

## 7. Accessibility and responsive behaviour

- Use semantic headings, tables, forms, and landmarks.
- Support keyboard navigation and visible focus.
- Meet readable colour contrast; do not rely on red/green alone.
- Provide text labels or icons with accessible names.
- Respect reduced motion.
- On small screens, tables should become accessible stacked rows or horizontally scrollable regions with clear labels.
- Charts need accessible summaries or data tables.

## 8. Content tone

Plain English, calm and factual. Explain technical terms such as mandate, descriptor, cadence, annualised, pause, and revoke. Avoid fear-based language and pressure to cancel. The product's job is to inform the user, not decide for them.
