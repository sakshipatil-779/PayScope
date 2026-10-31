# PayScope Production Deployment and Operations Guide

This guide provides end-to-end instructions for deploying, provisioning, and operating the PayScope recurring payment intelligence platform across cloud and containerized environments.

---

## 1. System Architecture Overview

PayScope operates on a decoupled cloud-native architecture:

```
┌────────────────────────────────────────────────────────┐
│             Next.js 16 Frontend (Vercel)              │
│       React 19 • Tailwind CSS 4 • Cytoscape.js         │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTPS / REST (JSON)
                           ▼
┌────────────────────────────────────────────────────────┐
│             FastAPI Backend (Render Web)               │
│         Python 3.13 • uv • SQLAlchemy 2.0              │
└────────────┬─────────────────────────────┬─────────────┘
             │ Psycopg 3                   │ Bolt (TLS)
             ▼                             ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│ Neon Serverless Postgres │  │  Neo4j AuraDB / Container│
│ (Relational Source Truth)│  │ (Multi-Hop Graph Topology│
└──────────────────────────┘  └──────────────────────────┘
```

- **Relational Source of Truth**: PostgreSQL stores canonical merchants, raw transactions, recurring commitments, anomaly insights, cancellation records, and savings scenarios.
- **Graph Projection Layer**: Neo4j projects entities into a directed multi-hop graph (`(User)-[:OWNS_ACCOUNT]->(Account)-[:HAS_TRANSACTION]->(Transaction)-[:PAID_TO]->(Merchant)` and `(Commitment)-[:SUPPORTED_BY]->(Transaction)`).
- **Graceful Fallback**: If Neo4j is unavailable or disabled (`NEO4J_ENABLED=false`), the API and `/relationships` explorer automatically fall back to PostgreSQL relational projection.

---

## 2. Backend Deployment on Render

### A. Deploying via Infrastructure as Code (`render.yaml`)

PayScope includes a native Render Blueprint at the workspace root:

1. Connect your GitHub repository to [Render](https://render.com).
2. Create a new **Blueprint** and select the repository.
3. Render automatically discovers `render.yaml` and provisions:
   - **Service Name**: `payscope-api`
   - **Environment**: Python 3.13
   - **Build Command**: `pip install uv && cd apps/api && uv sync`
   - **Start Command**: `cd apps/api && uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/api/v1/health`

### B. Required Environment Variables on Render

| Variable | Description | Example / Recommended Value |
|---|---|---|
| `PYTHON_VERSION` | Runtime Python version | `3.13.1` |
| `API_HOST` | Host binding interface | `0.0.0.0` |
| `API_PORT` | Listening port (or use `$PORT`) | `10000` |
| `BACKEND_CORS_ORIGINS` | Allowed frontend domains (comma-separated) | `https://payscope.vercel.app,http://localhost:3000` |
| `DATABASE_URL` | Neon or PostgreSQL connection URI | `postgresql+psycopg://user:password@ep-host.neon.tech/neondb?sslmode=require` |
| `NEO4J_URI` | Neo4j AuraDB Bolt/TLS endpoint | `neo4j+s://<dbid>.databases.neo4j.io` |
| `NEO4J_USERNAME` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `<generated-secure-password>` |
| `NEO4J_DATABASE` | Database name | `neo4j` |
| `NEO4J_ENABLED` | Toggle Neo4j integration | `true` (or `false` for relational-only) |

---

## 3. Frontend Deployment on Vercel

### A. Deployment Configuration

1. In the [Vercel Dashboard](https://vercel.com), select **Add New Project** and import the GitHub repository.
2. In **Project Settings**:
   - **Framework Preset**: Next.js
   - **Root Directory**: `apps/web`
   - **Node.js Version**: `20.x` or `22.x`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### B. Required Environment Variables on Vercel

| Variable | Description | Example Value |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Public URL of deployed FastAPI backend | `https://payscope-api.onrender.com` |

---

## 4. Neon PostgreSQL Setup & Provisioning

PayScope uses **SQLAlchemy 2.0** with the **Psycopg 3** driver (`postgresql+psycopg://`).

1. Log in to [Neon](https://neon.tech) and create a PostgreSQL 16 database.
2. Copy the connection string from your Neon dashboard:
   - For migrations and schema updates, use the **Direct Connection**:
     ```
     postgresql+psycopg://<user>:<password>@<ep-name>.neon.tech/neondb?sslmode=require
     ```
   - For high-concurrency API instances, use the **Pooled Connection** (PgBouncer):
     ```
     postgresql+psycopg://<user>:<password>@<ep-name>-pooler.neon.tech/neondb?sslmode=require
     ```
3. Run migrations against Neon:
   ```bash
   cd apps/api
   DATABASE_URL="postgresql+psycopg://<user>:<password>@<ep-name>.neon.tech/neondb?sslmode=require" uv run alembic upgrade head
   ```

---

## 5. Neo4j AuraDB Setup & Configuration

1. Log in to [Neo4j Aura](https://neo4j.com/cloud/platform/aura-graph-database/).
2. Create a **Neo4j AuraDB Free** or **Professional** instance.
3. Download the generated credentials file containing your URI and password:
   - `NEO4J_URI=neo4j+s://<instance-id>.databases.neo4j.io`
   - `NEO4J_USERNAME=neo4j`
   - `NEO4J_PASSWORD=<your-aura-password>`
4. Apply uniqueness constraints and indexes:
   The backend automatically ensures constraints (`User.id`, `Merchant.id`, `Commitment.id`, `Transaction.id`, etc.) on first sync.
5. Trigger initial synchronization:
   ```bash
   curl -X POST https://your-payscope-api.onrender.com/api/v1/graph/sync
   ```

---

## 6. Local Development via Docker Compose

To run the complete stack locally (FastAPI + Next.js + PostgreSQL + Neo4j):

```bash
# 1. Start all container services
docker compose up -d

# 2. Check running services
docker compose ps

# 3. Apply database migrations
docker compose exec api uv run alembic upgrade head

# 4. Access the platforms
# - Frontend:           http://localhost:3000
# - Backend OpenAPI:    http://localhost:8000/api/v1/docs
# - Neo4j Browser UI:   http://localhost:7474
# - Neo4j Bolt:         bolt://localhost:7687
```

---

## 7. Security & Hardening Checklist

- [x] **CORS Origin Whitelist**: Controlled via `BACKEND_CORS_ORIGINS`. Preflight checks enforced.
- [x] **Credential Redaction**: Health endpoints (`/api/v1/health`, `/api/v1/ready`, `/api/v1/graph/health`) strictly redact passwords, tokens, and internal connection strings.
- [x] **SQL Injection Prevention**: 100% of database interactions utilize SQLAlchemy 2.0 parameterized queries.
- [x] **Cypher Injection Prevention**: Neo4j queries execute exclusively through parameterized Cypher statements with dictionary parameters.
- [x] **File Upload Validation**: Ingestion router validates file extensions (`.csv`, `.xlsx`, `.json`), inspects MIME types, and caps payload sizes.
- [x] **Graceful Degradation**: Zero single-point-of-failure on graph queries; if Neo4j is offline, relational projection transparently serves `/relationships`.
