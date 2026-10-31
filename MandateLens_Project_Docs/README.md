# MandateLens Project Documentation Pack

This pack contains the 15 requested project documents plus the initial Antigravity prompt.

- `AGENTS.md` — agent rules and mandatory phase gate.
- `MASTER_BUILD_BRIEF.md` — product and architecture north star.
- `00_PROJECT_CHARTER.md` through `12_BUILD_PLAN.md` — product, research, requirements, architecture, data, security, tests, and build phases.
- `ANTIGRAVITY_START_PROMPT.txt` — copy-paste prompt for Phase 0 only.

**Workflow:** Give Antigravity `ANTIGRAVITY_START_PROMPT.txt`. It must complete Phase 0 only and stop with a handoff summary. Share that summary with ChatGPT to get the Phase 1 prompt. Repeat one phase at a time.

All product examples and records must remain synthetic. PostgreSQL is the source of truth; Neo4j, Celery/Redis, Gemini, OCR, and cloud storage are added only in their authorised later phases.
