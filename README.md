<div align="center">

# 💳 PayScope
### Autonomous Recurring Payment Intelligence Platform

*Find the money leaving quietly.*

[![Next.js](https://img.shields.io/badge/Next.js-16.4.3-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.0.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![Neo4j AuraDB](https://img.shields.io/badge/Neo4j-AuraDB_5-008CC1?style=for-the-badge&logo=neo4j&logoColor=white)](https://neo4j.com/cloud/platform/aura-graph-database/)
[![Firebase](https://img.shields.io/badge/Firebase-Auth_OAuth2-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4_Alpha-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

</div>

---

## 📌 Executive Overview

**PayScope** is a privacy-first, autonomous recurring payment intelligence platform. It transforms messy bank statements, credit card exports, and invoice records into transparent, evidence-backed recurring commitments—without requiring live bank credentials or screen scraping.

PayScope detects **hidden subscription drift**, flags **silent price increases**, exposes **free-trial conversions**, projects **annualized financial outflows**, maps complex financial relationships in a **Neo4j Knowledge Graph**, and generates **mechanism-specific cancellation playbooks** (UPI Autopay, e-Mandates, Card recurring billing, and Web portals).

---

## ✨ Key Capabilities & Highlights

| Feature | Description |
| :--- | :--- |
| 🔍 **Cadence & Commitment Engine** | High-precision recurring detection across weekly, monthly, quarterly, and annual intervals with tolerance window algorithms. |
| 📈 **Silent Price Creep & Anomaly Detection** | Surfaces subtle unannounced price hikes (e.g. ₹699 &rarr; ₹799) and trial conversions before cumulative drain occurs. |
| 🕸️ **Neo4j AuraDB Knowledge Graph** | Maps users, merchants, commitments, accounts, and cancellation channels as nodes and directed relationships for visual relationship analytics. |
| 🔐 **Firebase OAuth & Protected Dashboard** | Secure Google Sign-In via Firebase Auth with route guards and an instant zero-setup guest demo access mode. |
| 🛑 **Mechanism-Aware Cancellation Playbooks** | Step-by-step guidance tailored to the exact payment railway (NPCI UPI Autopay, SI-Hub, Card Mandates, or Merchant Portals). |
| 💰 **Annualized Outflows & What-If Simulator** | Simulates long-term savings by toggling non-essential commitments and calculating compound savings over 1, 3, and 5-year horizons. |
| 📄 **Statement File Ingestion** | Robust parsing engine for synthetic CSVs and bank statements with merchant descriptor normalization. |
| 🎨 **Modern Fintech UI** | Asymmetric left-aligned hero layout, floating island capsule navigation, vivid full-bleed 3D ambient video, and responsive dark theme. |

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Layer (apps/web - Next.js 16)"]
        UI["Modern UI / Floating Island Nav"]
        Auth["Firebase Auth (Google OAuth & Demo)"]
        Landing["Vivid 3D Video Hero Landing"]
        Dash["Protected Intelligence Dashboard"]
        GraphView["Interactive Relationship Explorer"]
    end

    subgraph API ["Application Layer (apps/api - FastAPI)"]
        Gateway["FastAPI Gateway (/api/v1)"]
        CommitmentEngine["Commitment & Cadence Analyzer"]
        InsightsEngine["Price Creep & Drift Detector"]
        CancellationEngine["Mechanism Playbook Resolver"]
        GraphService["Neo4j Knowledge Graph Driver"]
    end

    subgraph Data ["Data & Persistence Layer"]
        Postgres[("PostgreSQL / Relational Store\nSQLAlchemy 2.0 + Psycopg 3")]
        Neo4jAura[("Neo4j AuraDB Cloud\nCypher Graph Engine")]
        FirebaseCloud[("Firebase Cloud Services\nAuthentication & Token Verifier")]
    end

    UI --> Auth
    Auth --> FirebaseCloud
    UI --> Landing
    Auth -->|Authenticated Token| Dash
    Dash -->|REST / JSON| Gateway
    GraphView -->|Graph Endpoints| Gateway

    Gateway --> CommitmentEngine
    Gateway --> InsightsEngine
    Gateway --> CancellationEngine
    Gateway --> GraphService

    CommitmentEngine --> Postgres
    InsightsEngine --> Postgres
    GraphService -->|Bolt+s / Cypher| Neo4jAura
```

---

## 🗂️ Monorepo Structure

```text
PayScope/
├── apps/
│   ├── api/                          # FastAPI Backend Application
│   │   ├── alembic/                  # Database migration revisions
│   │   ├── app/
│   │   │   ├── analytics/            # Financial impact, savings & cadence engines
│   │   │   │   ├── cancellations/    # Cancellation playbook handlers
│   │   │   │   ├── financial_impact/ # Annualized projection simulator
│   │   │   │   └── insights/         # Price creep & zombie detection algorithms
│   │   │   ├── api/v1/               # Versioned REST API endpoints
│   │   │   │   ├── routes/           # Health, Commitments, Imports, Graph, etc.
│   │   │   │   └── router.py         # Route aggregator
│   │   │   ├── core/                 # Centralized configuration (Pydantic BaseSettings)
│   │   │   ├── db/                   # SQLAlchemy engine, session maker & models
│   │   │   ├── graph/                # Neo4j AuraDB connection manager & Cypher queries
│   │   │   ├── ingestion/            # Statement parsers & normalizers
│   │   │   ├── models/               # Domain entities (User, Commitment, Merchant, etc.)
│   │   │   ├── repositories/         # Clean data access layer
│   │   │   └── schemas/              # Pydantic request/response schemas
│   │   ├── tests/                    # Pytest integration and unit test suite
│   │   └── pyproject.toml            # Python dependencies (uv / pip)
│   │
│   └── web/                          # Next.js 16 Web Application
│       ├── public/
│       │   └── videos/               # High-fidelity ambient background & intro videos
│       ├── src/
│       │   ├── app/                  # Next.js App Router pages
│       │   │   ├── about/            # About Us page
│       │   │   ├── cancellations/    # Playbook views
│       │   │   ├── commitments/      # Subscription commitment details
│       │   │   ├── dashboard/        # Protected main intelligence dashboard
│       │   │   ├── financial-impact/ # What-if simulator
│       │   │   ├── insights/         # Anomaly alerts
│       │   │   ├── privacy/          # Privacy Policy & synthetic safety statement
│       │   │   ├── relationships/    # Interactive graph exploration
│       │   │   ├── upload/           # Statement dropzone
│       │   │   ├── layout.tsx        # Root layout with AuthProvider & AppShell
│       │   │   └── page.tsx          # Landing page with video background & capsule nav
│       │   ├── components/
│       │   │   ├── auth/             # AuthModal & ProtectedRoute gate
│       │   │   ├── brand/            # PayScope SVG vector logos
│       │   │   ├── landing/          # Hero, Capsule Header & Ambient Video
│       │   │   ├── layout/           # AppShell & sidebar navigation
│       │   │   └── util/             # ClientOnly wrapper (React 19 useSyncExternalStore)
│       │   ├── context/              # AuthContext (Firebase & Demo session management)
│       │   └── lib/                  # Firebase SDK client initialization
│       ├── package.json              # npm dependencies & scripts
│       └── next.config.ts            # Next.js & Turbopack configuration
│
├── docker-compose.yml                # Local PostgreSQL container service
├── .env.example                      # Root environment template
└── README.md                         # Comprehensive documentation
```

---

## 🚀 Getting Started

### Prerequisites

* **Node.js:** `v20+` (tested with `v24.14.0`) & **npm:** `v10+`
* **Python:** `3.11+` (tested with `3.13.1`)
* **uv:** Fast Python package installer (`pip install uv` or standalone installer)
* **Git:** Installed and available in PATH

---

### 1. Repository Setup

```bash
git clone https://github.com/sakshipatil-779/PayScope.git
cd PayScope
```

---

### 2. Backend Setup (FastAPI + Neo4j)

1. **Navigate to the API folder:**
   ```powershell
   cd apps/api
   ```

2. **Install Python dependencies:**
   ```powershell
   uv sync --extra dev
   # OR using pip:
   pip install -r pyproject.toml
   ```

3. **Configure Environment Variables:**
   Create `.env` in `apps/api/.env` (or project root `.env`):
   ```env
   # API & Database Settings
   API_V1_STR=/api/v1
   PROJECT_NAME="PayScope API"
   ENVIRONMENT=development
   DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/payscope

   # Neo4j AuraDB Knowledge Graph Configuration
   NEO4J_ENABLED=true
   NEO4J_URI=neo4j+s://090796b3.databases.neo4j.io
   NEO4J_USERNAME=090796b3
   NEO4J_PASSWORD=97A7SJ7RJp-r1hXmjSpBgSQai7Skcm6tMU1h4aSbP_E
   NEO4J_DATABASE=090796b3
   ```

4. **Launch the FastAPI Server:**
   ```powershell
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Verify Backend Health:**
   * Liveness: `http://127.0.0.1:8000/api/v1/health`
   * Neo4j AuraDB Health: `http://127.0.0.1:8000/api/v1/graph/health`
   * Interactive Swagger Docs: `http://127.0.0.1:8000/api/v1/docs`

---

### 3. Frontend Setup (Next.js 16 + Firebase)

1. **Navigate to the Web folder:**
   ```powershell
   cd apps/web
   ```

2. **Install dependencies:**
   ```powershell
   npm install
   ```

3. **Configure Frontend Environment Variables:**
   Create `apps/web/.env.local`:
   ```env
   # Backend Connectivity
   API_BASE_URL=http://127.0.0.1:8000
   NEXT_PUBLIC_APP_NAME="PayScope"
   NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
   NEXT_PUBLIC_API_URL=http://127.0.0.1:8000

   # Firebase Google Authentication Configuration
   NEXT_PUBLIC_FIREBASE_API_KEY="AIzaSyCMi4MDAtJhPfqCgBhXNYQgHaglgSQf0vA"
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN="payscope18.firebaseapp.com"
   NEXT_PUBLIC_FIREBASE_PROJECT_ID="payscope18"
   NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET="payscope18.firebasestorage.app"
   NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID="104812680638"
   NEXT_PUBLIC_FIREBASE_APP_ID="1:104812680638:web:f68d549e42ef8a845015ef"
   ```

4. **Start the Next.js Development Server:**
   ```powershell
   npm run dev
   ```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🔑 Firebase Google Authentication Setup

If you receive the error `auth/operation-not-allowed` when clicking **"Continue with Google"**, Google Sign-In needs to be toggled ON in your Firebase project console:

1. Open the [Firebase Console &rarr; payscope18 &rarr; Authentication &rarr; Sign-in method](https://console.firebase.google.com/project/payscope18/authentication/providers).
2. Under **Sign-in providers**, click **Add new provider** and select **Google**.
3. Toggle **Enable**, choose your support email from the dropdown, and click **Save**.
4. In the **Authorized domains** tab, make sure `localhost` is listed.

> [!TIP]
> PayScope also includes a built-in **"Instant Demo Access"** button in the login modal, allowing instant access to the dashboard without any initial Firebase configuration.

---

## 🌐 Neo4j AuraDB Knowledge Graph Integration

PayScope integrates directly with Neo4j AuraDB Cloud to model financial networks:

```cypher
(:User)-[:SUBSCRIBES_TO]->(:Commitment)-[:BILLED_BY]->(:Merchant)
(:Commitment)-[:PROCESSED_VIA]->(:CancellationMechanism)
(:Commitment)-[:RECORDED_IN]->(:Transaction)
```

### AuraDB Graph Endpoints:
* `GET /api/v1/graph/health` — Verifies connection pool, active database status, node count, and edge count.
* `GET /api/v1/graph/overview` — Retrieves full network nodes and relationships for client graph visualizations.
* `POST /api/v1/graph/sync/{user_id}` — Re-synchronizes Postgres commitments and merchant nodes into AuraDB.

---

## 📡 REST API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/v1/health` | `GET` | Service liveness health check |
| `/api/v1/ready` | `GET` | Database readiness check |
| `/api/v1/graph/health` | `GET` | Neo4j AuraDB live connectivity & node statistics |
| `/api/v1/dashboard/summary` | `GET` | Unified dashboard KPIs (outflows, active mandates, alerts) |
| `/api/v1/commitments` | `GET` | List recurring commitments with cadences and amounts |
| `/api/v1/commitments/{id}` | `GET` | Single commitment detail with historical transactions |
| `/api/v1/insights` | `GET` | Active price creep, zombie subscriptions, and trial conversion warnings |
| `/api/v1/financial-impact` | `GET` | Calculated annualized outflows and potential savings |
| `/api/v1/cancellations/{id}` | `GET` | Mechanism-specific cancellation playbook for a commitment |
| `/api/v1/imports/upload` | `POST` | Upload and parse CSV / PDF synthetic statement |
| `/api/v1/demo/seed` | `POST` | Seed realistic synthetic test commitments and merchants |

---

## 🧪 Testing & Validation

### Backend Test Suite (Pytest)
```powershell
cd apps/api
uv run pytest -v
```
Tests cover:
* Relational persistence & `NUMERIC(18, 2)` arithmetic safety
* Liveness (`/health`) and readiness checks
* Recurrence detection tolerance thresholds
* Cancellation playbook schema validation
* Neo4j AuraDB connection lifecycle

### Frontend Validation (Lint & Build)
```powershell
cd apps/web
npm run lint
npm run build
```
* **Linting:** ESLint with strict React 19 rules (0 errors, 0 warnings).
* **Turbopack Build:** Clean compilation without hydration mismatches.

---

## 🔒 Privacy & Synthetic Data Isolation

PayScope adheres to strict privacy-by-design standards:
* **Zero Live Bank Access:** No credentials, Open Banking tokens, or live aggregators (Plaid/Yodlee) are requested or stored.
* **Isolated Processing:** Statement data is analyzed locally and stored strictly in synthetic development namespaces.
* **Granular OAuth Scopes:** Firebase Google Authentication requests minimal profile identity (`email`, `displayName`, `photoURL`) exclusively for user workspace segregation.

---

## 👥 Contributors & Acknowledgements

* **Project Name:** PayScope
* **Repository:** [https://github.com/sakshipatil-779/PayScope](https://github.com/sakshipatil-779/PayScope)
* **Author / Maintainer:** [sakshipatil-779](https://github.com/sakshipatil-779) & [vinaybhadane](https://github.com/vinaybhadane)

---

<div align="center">
<sub>Designed with care for clean, transparent, and autonomous financial clarity.</sub>
</div>
