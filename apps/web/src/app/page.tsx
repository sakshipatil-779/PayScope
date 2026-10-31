import Link from "next/link";

export const dynamic = "force-dynamic";

interface HealthData {



  status: string;
  service: string;
  version: string;
}

interface HealthResult {
  connected: boolean;
  data: HealthData | null;
  error?: string;
  url: string;
  timestamp: string;
}

async function getBackendHealth(): Promise<HealthResult> {
  const baseUrl = process.env.API_BASE_URL || "http://127.0.0.1:8000";
  const healthUrl = `${baseUrl.replace(/\/+$/, "")}/api/v1/health`;
  const timestamp = new Date().toISOString();

  try {
    const res = await fetch(healthUrl, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });

    if (!res.ok) {
      return {
        connected: false,
        data: null,
        error: `HTTP ${res.status}: ${res.statusText}`,
        url: healthUrl,
        timestamp,
      };
    }

    const data: HealthData = await res.json();
    if (data.status === "ok") {
      return {
        connected: true,
        data,
        url: healthUrl,
        timestamp,
      };
    }

    return {
      connected: false,
      data,
      error: `Unexpected payload status: ${data.status}`,
      url: healthUrl,
      timestamp,
    };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Connection failed";
    return {
      connected: false,
      data: null,
      error: message,
      url: healthUrl,
      timestamp,
    };
  }
}

export default async function Home() {
  const health = await getBackendHealth();



  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 antialiased selection:bg-emerald-500 selection:text-slate-950">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center font-bold text-emerald-400 text-lg shadow-sm">
              M
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-lg tracking-tight text-white flex items-center gap-2">
                Mandate<span className="text-emerald-400">Lens</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 font-normal">
                  v0.4.0 (Phase 4)
                </span>
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs font-medium">
            <Link
              href="/merchants"
              className="px-3 py-1.5 rounded-md border border-slate-800 bg-slate-900 text-slate-300 hover:text-white transition-colors"
            >
              Merchants
            </Link>
            <Link
              href="/merchant-review"
              className="px-3 py-1.5 rounded-md border border-amber-500/30 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 transition-colors"
            >
              Review Queue
            </Link>
            <Link
              href="/upload"
              className="px-3 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-sm transition-colors"
            >
              Upload Centre
            </Link>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/70 border border-slate-700/60 text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              Synthetic Data Only
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-12 flex flex-col gap-12">
        {/* Hero Section */}
        <section className="flex flex-col items-start gap-4 max-w-3xl pt-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span>Find the money leaving quietly.</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-bold tracking-tight text-white leading-tight">
            Recurring Payment Intelligence Platform
          </h1>
          <p className="text-base sm:text-lg text-slate-300 leading-relaxed">
            Discover recurring payments, understand hidden charges, detect silent price increases and take control of your financial commitments.
          </p>
        </section>

        {/* Live Connectivity Card */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm flex flex-col justify-between gap-6">
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Backend Service Health
                </span>
                {health.connected ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    API Connected
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    <span className="w-2 h-2 rounded-full bg-rose-400" />
                    API Unavailable
                  </span>
                )}
              </div>
              <h2 className="text-xl font-semibold text-white">
                FastAPI Health Check Endpoint
              </h2>
              <p className="text-sm text-slate-400">
                Server-side communication test against <code className="text-slate-200 font-mono bg-slate-800 px-1.5 py-0.5 rounded text-xs">{health.url}</code> (non-cached).
              </p>
            </div>

            <div className="rounded-lg bg-slate-950/70 border border-slate-800/80 p-4 font-mono text-xs text-slate-300 space-y-1.5">
              <div className="flex justify-between">
                <span className="text-slate-500">Target Endpoint:</span>
                <span className="text-slate-200">{health.url}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Status Response:</span>
                <span className={health.connected ? "text-emerald-400 font-semibold" : "text-rose-400 font-semibold"}>
                  {health.connected ? "200 OK — " + JSON.stringify(health.data) : "Unreachable (" + (health.error || "offline") + ")"}
                </span>
              </div>
              {health.connected && health.data && (
                <>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Registered Service:</span>
                    <span className="text-slate-200">{health.data.service}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">API Version:</span>
                    <span className="text-slate-200">{health.data.version}</span>
                  </div>
                </>
              )}
              <div className="flex justify-between">
                <span className="text-slate-500">Checked At:</span>
                <span className="text-slate-400">{health.timestamp}</span>
              </div>
            </div>

            {!health.connected && (
              <div className="rounded-lg bg-rose-950/30 border border-rose-900/40 p-4 text-xs text-rose-200 space-y-2">
                <p className="font-semibold text-rose-300">How to start the FastAPI backend:</p>
                <pre className="bg-slate-950 p-2 rounded text-slate-300 overflow-x-auto">
cd apps/api{"\n"}
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
                </pre>
                <p className="text-slate-400">Once started, refresh this page to establish the live server connection.</p>
              </div>
            )}
          </div>

          {/* Quick Specifications Card */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm flex flex-col justify-between gap-4">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Phase 1 Foundation
              </span>
              <h2 className="text-lg font-semibold text-white mt-1">
                Monorepo Architecture
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Clean separation between web presentation and Python financial analytics.
              </p>
            </div>

            <ul className="text-xs space-y-2 text-slate-300">
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                <span><strong>apps/web:</strong> Next.js 16 (App Router, TypeScript, Tailwind CSS)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                <span><strong>apps/api:</strong> FastAPI + Uvicorn (Python 3.13, Pydantic v2)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-600 mt-1.5 flex-shrink-0" />
                <span><strong>Persistence:</strong> PostgreSQL + SQLAlchemy 2.0 (Phase 2)</span>
              </li>
            </ul>

            <div className="pt-2 border-t border-slate-800">
              <span className="text-[11px] text-slate-500 block">
                Operating strictly under AGENTS.md phase-gated protocol.
              </span>
            </div>
          </div>
        </section>

        {/* Project Roadmap & Current Status */}
        <section className="rounded-xl border border-slate-800 bg-slate-900/30 p-6 flex flex-col gap-6">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Implementation Roadmap
            </span>
            <h2 className="text-xl font-semibold text-white">
              Phased Build Status
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div className="p-4 rounded-lg bg-slate-900/70 border border-slate-800 flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-200">Phase 0: Audit</span>
                <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px]">Complete</span>
              </div>
              <p className="text-slate-400 text-[11px]">Workspace audited, toolchains verified, documentation aligned.</p>
            </div>

            <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-800/40 flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-emerald-300">Phase 1: Skeleton</span>
                <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px]">Active</span>
              </div>
              <p className="text-slate-300 text-[11px]">Monorepo established, Next.js & FastAPI runnable shells verified.</p>
            </div>

            <div className="p-4 rounded-lg bg-slate-900/70 border border-slate-800 flex flex-col gap-2 opacity-70">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-300">Phase 2: Database</span>
                <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px]">Next</span>
              </div>
              <p className="text-slate-400 text-[11px]">PostgreSQL, SQLAlchemy 2.0, Alembic migrations, demo user workspace.</p>
            </div>

            <div className="p-4 rounded-lg bg-slate-900/70 border border-slate-800 flex flex-col gap-2 opacity-70">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-300">Phases 3–12</span>
                <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px]">Upcoming</span>
              </div>
              <p className="text-slate-400 text-[11px]">Synthetic data, merchant resolution, recurrence engine, playbooks.</p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/40 mt-auto">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>
            MandateLens Prototype — Synthetic-Data-Only Recurring-Payment Intelligence.
          </p>
          <p>
            No real banking credentials or financial transactions are ever requested or processed.
          </p>
        </div>
      </footer>
    </div>
  );
}
