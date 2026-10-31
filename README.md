# MandateLens — Recurring Payment Intelligence Platform

> **Tagline:** Find the money leaving quietly.  
> **Prototype Data Policy:** Synthetic data only. No real bank, card, or payment provider credentials or accounts are ever connected or manipulated.

MandateLens is a statement-first recurring-payment intelligence platform prototype. It transforms messy statement descriptors and payment notifications into understandable, evidence-backed recurring commitments, highlights silent price increases and trial conversions, calculates transparent annual costs, and guides users through mechanism-specific cancellation playbooks.

---

## 1. Technology Stack

- **Frontend (`apps/web`):** Next.js 16 (App Router), TypeScript, Tailwind CSS, ESLint, Node.js (`v24.14.0`), npm (`11.9.0`).
- **Backend (`apps/api`):** Python 3.13, FastAPI, Uvicorn, Pydantic v2, `uv` package manager (`0.11.33`).
- **Persistence & Database (Phase 2):** PostgreSQL 16 (Docker Compose), SQLAlchemy 2.0 (typed declarative mappings, connection pooling with `pool_pre_ping`), Psycopg 3 binary driver, Alembic versioned migrations.
- **Testing:** Pytest & HTTPX with dedicated test database (`mandatelens_test`), ESLint & Next.js production build (`apps/web`).

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
│       ├── alembic/                # Alembic migration scripts
│       │   ├── env.py              # Dynamic migration environment
│       │   └── versions/           # Versioned migration revisions
│       ├── alembic.ini             # Alembic configuration file
│       ├── app/
│       │   ├── main.py             # FastAPI entry point & CORS configuration
│       │   ├── core/config.py      # Centralized Pydantic BaseSettings
│       │   ├── db/                 # Database engine, sessionmaker & Base
│       │   │   ├── base.py         # SQLAlchemy DeclarativeBase
│       │   │   └── session.py      # Connection pooling & get_db dependency
│       │   ├── models/             # Foundational domain entities (SQLAlchemy 2.0)
│       │   │   ├── demo_user.py    # Demo workspace users
│       │   │   ├── account.py      # Synthetic statement/card accounts
│       │   │   ├── import_record.py# File import provenance
│       │   │   ├── transaction.py  # Financial transactions (NUMERIC precision)
│       │   │   ├── merchant.py     # Canonical merchant reference
│       │   │   └── audit_event.py  # State transition audit log
│       │   ├── repositories/       # Clean data access layer
│       │   │   ├── user_repository.py
│       │   │   ├── account_repository.py
│       │   │   ├── import_repository.py
│       │   │   ├── transaction_repository.py
│       │   │   └── merchant_repository.py
│       │   ├── api/v1/             # Versioned API routes
│       │   │   ├── router.py       # V1 router aggregation
│       │   │   └── routes/
│       │   │       ├── health.py   # Liveness health check
│       │   │       └── ready.py    # Database readiness check (SELECT 1)
│       │   └── schemas/health.py   # Pydantic response models
│       ├── tests/                  # Integration and unit tests
│       │   ├── conftest.py         # Test database session fixture (clean truncate)
│       │   ├── test_health.py      # Liveness endpoint test
│       │   ├── test_readiness.py   # Database connectivity test
│       │   ├── test_persistence.py # Relational CRUD, FK, and unique constraint tests
│       │   └── test_migrations.py  # Alembic upgrade/downgrade cycle test
│       ├── pyproject.toml          # uv/pip package dependencies
│       └── uv.lock                 # Deterministic dependency lockfile
│
├── docker-compose.yml              # Local PostgreSQL 16 container definition
├── .gitignore                      # Comprehensive Git exclusion rules
├── .env.example                    # Global environment variable template
└── README.md                       # Monorepo setup & execution guide
```

---

## 3. Prerequisites

The following runtimes and tools must be operational on your Windows machine:
- **Docker Desktop:** v29+ / Docker Compose v5+ (Ensure Docker Desktop is running)
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

2. The default local settings in `.env` are pre-configured for the local Docker PostgreSQL instance:
   ```ini
   POSTGRES_DB=mandatelens
   POSTGRES_USER=mandatelens_dev
   POSTGRES_PASSWORD=mandatelens_dev_password
   DATABASE_URL=postgresql+psycopg://mandatelens_dev:mandatelens_dev_password@127.0.0.1:5432/mandatelens
   TEST_DATABASE_URL=postgresql+psycopg://mandatelens_dev:mandatelens_dev_password@127.0.0.1:5432/mandatelens_test
   ```

3. Ensure `.env` is also available to `apps/api`:
   ```powershell
   Copy-Item .env apps/api/.env
   ```

---

## 5. PostgreSQL Database Operations (Docker Compose)

### Start Database
Start the container in detached mode:
```powershell
docker compose up -d postgres
```

Verify container status and health:
```powershell
docker compose ps
```
The status should display `Up (healthy)` on `127.0.0.1:5432->5432/tcp`.

### Stop Database
To pause or stop the container while preserving all database data:
```powershell
docker compose stop
```

### Stop and Remove Containers
To stop and remove containers and network:
```powershell
docker compose down
```

> [!WARNING]
> Running `docker compose down -v` permanently removes Docker named volumes (`mandatelens_postgres_data`) and deletes all persisted database records. Do not run with `-v` unless a complete database wipe is intended.

### Create Dedicated Test Database
To set up the separate test database:
```powershell
docker exec mandatelens-postgres psql -U mandatelens_dev -d mandatelens -c "CREATE DATABASE mandatelens_test;"
```

---

## 6. Alembic Database Migrations

Run database migrations from the `apps/api` directory:

1. Navigate to the API application directory:
   ```powershell
   cd apps/api
   ```

2. Apply all pending migrations to the development database:
   ```powershell
   uv run alembic upgrade head
   ```

3. Verify the current applied migration revision:
   ```powershell
   uv run alembic current
   ```

4. Roll back the most recent migration:
   ```powershell
   uv run alembic downgrade -1
   ```

---

## 7. Backend Setup and Execution

1. Navigate to the API application directory:
   ```powershell
   cd apps/api
   ```

2. Synchronize dependencies and virtual environment:
   ```powershell
   uv sync --extra dev
   ```

3. Apply database migrations:
   ```powershell
   uv run alembic upgrade head
   ```

4. Run the backend development server:
   ```powershell
   uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

### API Endpoints
- **Liveness Health Check:** `GET http://127.0.0.1:8000/api/v1/health` (Independent of DB)
- **Database Readiness Check:** `GET http://127.0.0.1:8000/api/v1/ready` (Verifies DB connection via `SELECT 1`)
- **Interactive Swagger Documentation:** `http://127.0.0.1:8000/api/v1/docs`

---

## 8. Frontend Setup and Execution

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

## 9. Testing Instructions

### Backend Test Suite (Pytest)
Run all unit and PostgreSQL integration tests from `apps/api`:
```powershell
cd apps/api
uv run pytest -v
```
All tests execute against the dedicated, isolated `mandatelens_test` database and automatically clean up after themselves.

Tests cover:
- Database connectivity (`SELECT 1`)
- Liveness (`/health`) and Readiness (`/ready`) endpoints (success and simulated failure)
- Relational persistence (User, Account, Transaction, Import, Merchant)
- Fixed-precision `NUMERIC(18, 2)` calculations
- Foreign key constraints (cascade on user deletion, restrict/null on account/import)
- Unique constraints (`(user_id, external_synthetic_id)` duplicate prevention)
- Alembic downgrade-to-base and re-upgrade cycle

### Frontend Validation (Lint & Build)
From `apps/web`:
```powershell
cd apps/web
npm run lint
npm run build
```
