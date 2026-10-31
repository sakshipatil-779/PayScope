# MandateLens — Recurring Payment Intelligence Platform

> **Tagline:** Find the money leaving quietly.  
> **Prototype Data Policy:** Synthetic data only. No real bank, card, or payment provider credentials or accounts are ever connected or manipulated.

MandateLens is a statement-first recurring-payment intelligence platform prototype. It transforms messy statement descriptors and payment notifications into understandable, evidence-backed recurring commitments, highlights silent price increases and trial conversions, calculates transparent annual costs, and guides users through mechanism-specific cancellation playbooks.

---

## 1. Technology Stack

- **Frontend (`apps/web`):** Next.js 16 (App Router), TypeScript, Tailwind CSS, ESLint, Node.js (`v24.14.0`), npm (`11.9.0`).
- **Backend (`apps/api`):** Python 3.13, FastAPI, Uvicorn, Pydantic v2, `uv` package manager (`0.11.33`).
- **Persistence (Planned - Phase 2):** PostgreSQL, SQLAlchemy 2.0, Alembic migrations.
- **Testing:** Pytest & HTTPX (Backend), ESLint & Next.js production build (Frontend).

---

## 2. Monorepo Folder Structure

```text
HackFIn/
├── MandateLens_Project_Docs/       # 17 preserved specification & protocol documents
│   ├── AGENTS.md                   # Agent operating rules & mandatory phase gate
│   ├── MASTER_BUILD_BRIEF.md       # Product & architectural vision
│   ├── 00_PROJECT_CHARTER.md       # Scope, vision, objectives & non-goals
│   ├── 01_PROBLEM_STATEMENT.md     # Recurring payment pain points
│   ├── 02_RESEARCH_EVIDENCE.md     # Research notes & assumption register
│   ├── 03_USER_PERSONAS.md         # Design personas & heuristics
│   ├── 04_USER_WORKFLOWS.md        # Core user journeys
│   ├── 05_PRODUCT_REQUIREMENTS.md  # Functional & non-functional requirements (P0/P1/P2)
│   ├── 06_MVP_SCOPE.md             # MVP boundaries & 12 acceptance scenarios
│   ├── 07_UX_UI_SPEC.md            # Visual language & interaction specifications
│   ├── 08_TECHNICAL_ARCHITECTURE.md# System architecture, APIs & data flows
│   ├── 09_DATA_MODEL.md            # Relational schema (PostgreSQL) & projections
│   ├── 10_SECURITY_AND_TRUST.md    # Security, privacy & synthetic-only rules
│   ├── 11_VALIDATION_AND_TEST_PLAN.md# Verification checklist & test matrices
│   ├── 12_BUILD_PLAN.md            # 13-phase roadmap & handoff protocols
│   ├── ANTIGRAVITY_START_PROMPT.txt# Phase 0 start prompt
│   └── README.md                   # Documentation index
│
├── apps/
│   ├── web/                        # Next.js 16 App Router frontend
│   │   ├── src/app/                # Landing page & health status
│   │   ├── public/                 # Static assets
│   │   ├── package.json            # npm package dependencies
│   │   ├── tsconfig.json           # TypeScript configuration
│   │   ├── next.config.ts          # Turbopack & Tailwind setup
│   │   └── .env.local.example      # Frontend environment template
│   │
│   └── api/                        # FastAPI backend
│       ├── app/
│       │   ├── main.py             # FastAPI entry point & CORS configuration
│       │   ├── core/config.py      # Pydantic BaseSettings configuration
│       │   ├── api/v1/             # Versioned API routes
│       │   │   ├── router.py       # V1 router aggregation
│       │   │   └── routes/health.py# Health check route
│       │   └── schemas/health.py   # Pydantic response models
│       ├── tests/test_health.py    # Pytest health check test
│       ├── pyproject.toml          # uv/pip package dependencies
│       └── uv.lock                 # Deterministic dependency lockfile
│
├── .gitignore                      # Comprehensive Git exclusion rules
├── .env.example                    # Global environment variable template
└── README.md                       # Monorepo setup & execution guide
```

---

## 3. Prerequisites

The following runtimes and tools must be installed on your Windows machine:
- **Node.js:** v20+ (tested with `v24.14.0`)
- **npm:** v10+ (tested with `11.9.0`)
- **Python:** 3.11+ (tested with `3.13.1`)
- **uv:** Python package manager (tested with `0.11.33`)
- **Git:** (tested with `2.54.0`)

---

## 4. Environment Configuration

1. Copy the root environment template:
   ```powershell
   Copy-Item .env.example .env
   ```

2. (Optional) For Next.js client-side overrides:
   ```powershell
   Copy-Item apps/web/.env.local.example apps/web/.env.local
   ```

Default settings point to `http://127.0.0.1:8000` for backend API communication.

---

## 5. Backend Setup and Execution

1. Navigate to the API application directory:
   ```powershell
   cd apps/api
   ```

2. Synchronize dependencies and create the virtual environment:
   ```powershell
   uv sync --extra dev
   ```

3. Run the backend development server:
   ```powershell
   uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

The backend starts at `http://127.0.0.1:8000`.  
- **API Health Endpoint:** `http://127.0.0.1:8000/api/v1/health`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/api/v1/docs`

---

## 6. Frontend Setup and Execution

1. Open a new PowerShell terminal and navigate to the web directory:
   ```powershell
   cd apps/web
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. Start the Next.js development server:
   ```powershell
   npm run dev
   ```

The frontend will run at `http://localhost:3000`.

---

## 7. Testing Instructions

### Backend Testing (Pytest)
Run the backend test suite from `apps/api`:
```powershell
cd apps/api
uv run pytest
```
Expected output: 1 passed test verifying `GET /api/v1/health` returns HTTP 200 with `{"status":"ok","service":"mandatelens-api","version":"0.1.0"}`.

### Frontend Validation (Lint & Build)
Run ESLint and the Next.js production build from `apps/web`:
```powershell
cd apps/web
npm run lint
npm run build
```
Expected output: ESLint passes with 0 errors, and Next.js creates an optimized dynamic production build.

---

## 8. Service Verification Flow

1. Start the API backend in Terminal 1 (`apps/api` via `uv run uvicorn ...`).
2. Verify API response in browser or PowerShell:
   ```powershell
   Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
   ```
3. Start the frontend in Terminal 2 (`apps/web` via `npm run dev`).
4. Open `http://localhost:3000` in your browser.
5. The landing page makes an un-cached server-side fetch to `http://127.0.0.1:8000/api/v1/health` and displays the live **API Connected** status badge.
