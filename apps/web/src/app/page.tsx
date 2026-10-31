import Image from "next/image";
import Link from "next/link";
import PayScopeLogo from "@/components/brand/PayScopeLogo";

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
    <div className="relative min-h-screen flex flex-col justify-between bg-slate-950 text-slate-100 overflow-hidden select-none">
      {/* ==================================================================== */}
      {/* BACKGROUND: Cinematic City / Data-Network Visual (Supplied Asset)    */}
      {/* Masked with deep navy and cyan luminous gradient overlays            */}
      {/* ==================================================================== */}
      <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">
        {/* Supplied Image Asset */}
        <div className="absolute inset-0 anim-stage-2">
          <Image
            src="/images/mandatelens-fintech-hero.jpg"
            alt="City data network recurring payment intelligence visual"
            fill
            priority
            sizes="100vw"
            className="object-cover object-center scale-105 opacity-40 brightness-75 contrast-125"
          />
        </div>

        {/* Luminous radial glow over the central city node */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full bg-cyan-500/15 blur-[120px] anim-ambient-glow" />
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[450px] h-[450px] rounded-full bg-teal-400/10 blur-[90px]" />

        {/* Deep Vignette Gradient Overlays for perfect typographic contrast */}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/70 to-slate-950/90" />
        <div className="absolute inset-0 bg-gradient-to-r from-slate-950/95 via-slate-950/40 to-slate-950/95" />

        {/* Circular Financial Data Rings around central focal point */}
        <div className="absolute top-[48%] left-1/2 pointer-events-none">
          <div className="w-[360px] h-[360px] rounded-full border border-cyan-400/25 anim-ring-primary" />
          <div className="w-[520px] h-[520px] rounded-full border border-teal-500/15 border-dashed anim-ring-secondary" />
          <div className="w-[720px] h-[720px] rounded-full border border-cyan-500/10" />
        </div>
      </div>

      {/* ==================================================================== */}
      {/* HEADER: Stage 1 Reveal Navigation Bar                                */}
      {/* ==================================================================== */}
      <header className="relative z-50 border-b border-slate-800/60 bg-slate-950/70 backdrop-blur-md anim-stage-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Brand Identity */}
          <Link href="/" className="hover:opacity-90 transition-opacity">
            <PayScopeLogo variant="navbar" />
          </Link>

          {/* Primary Platform Navigation */}
          <nav className="hidden lg:flex items-center gap-1.5 text-xs font-medium">
            <Link
              href="/dashboard"
              className="px-3 py-1.5 rounded-lg border border-[#F08A00]/40 bg-[#F08A00]/15 text-[#FFA52B] hover:bg-[#F08A00]/25 transition-all font-semibold shadow-[0_0_12px_rgba(240,138,0,0.15)]"
            >
              Dashboard
            </Link>
            <Link
              href="/financial-impact"
              className="px-3 py-1.5 rounded-lg border border-cyan-500/30 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20 hover:border-cyan-400 transition-all font-semibold shadow-[0_0_12px_rgba(6,182,212,0.15)]"
            >
              Financial Impact
            </Link>
            <Link
              href="/savings"
              className="px-3 py-1.5 rounded-lg border border-teal-500/30 bg-teal-500/10 text-teal-300 hover:bg-teal-500/20 transition-all font-semibold"
            >
              Savings
            </Link>
            <Link
              href="/commitments"
              className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-900/60 transition-colors"
            >
              Commitments
            </Link>
            <Link
              href="/insights"
              className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-900/60 transition-colors"
            >
              Insights
            </Link>
            <Link
              href="/cancellations"
              className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-900/60 transition-colors"
            >
              Cancellations
            </Link>
            <Link
              href="/relationships"
              className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-900/60 transition-colors"
            >
              Relationships
            </Link>
            <Link
              href="/upload"
              className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-900/60 transition-colors"
            >
              Upload
            </Link>
          </nav>

          {/* Service Status Indicator */}
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-800 text-[11px] text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
              Synthetic Mode
            </span>
            {health.connected ? (
              <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                API 200 OK
              </span>
            ) : (
              <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                API Offline
              </span>
            )}
          </div>
        </div>
      </header>

      {/* ==================================================================== */}
      {/* HERO SECTION: Stage 3 Product Identity & Floating Insights           */}
      {/* STRICTLY NO SCROLLING EFFECTS — Fits in initial viewport             */}
      {/* ==================================================================== */}
      <main className="relative z-10 flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 flex flex-col justify-center items-center text-center py-8 lg:py-16">
        {/* Floating Insight Pill 1 (Top Left) */}
        <div className="hidden lg:flex absolute left-8 top-28 items-center gap-3 px-4 py-2.5 rounded-xl bg-slate-900/80 border border-amber-500/30 backdrop-blur-md shadow-[0_8px_24px_rgba(0,0,0,0.4)] anim-float-1 anim-stage-3">
          <div className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(251,191,36,0.8)]" />
          <div className="text-left font-mono">
            <span className="text-[11px] text-amber-300 font-semibold block">Sustained Price Alert</span>
            <span className="text-xs text-slate-200">+₹200/mo CloudDesk Pro</span>
          </div>
        </div>

        {/* Floating Insight Pill 2 (Top Right) */}
        <div className="hidden lg:flex absolute right-8 top-28 items-center gap-3 px-4 py-2.5 rounded-xl bg-slate-900/80 border border-cyan-500/30 backdrop-blur-md shadow-[0_8px_24px_rgba(0,0,0,0.4)] anim-float-2 anim-stage-3">
          <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
          <div className="text-left font-mono">
            <span className="text-[11px] text-cyan-300 font-semibold block">Annual Recurring Outflow</span>
            <span className="text-xs text-slate-200">₹14,380/yr in Confirmed Mandates</span>
          </div>
        </div>

        {/* Floating Insight Pill 3 (Bottom Center-Right) */}
        <div className="hidden lg:flex absolute right-16 bottom-16 items-center gap-3 px-4 py-2.5 rounded-xl bg-slate-900/80 border border-teal-500/30 backdrop-blur-md shadow-[0_8px_24px_rgba(0,0,0,0.4)] anim-float-3 anim-stage-3-delayed">
          <div className="w-2.5 h-2.5 rounded-full bg-teal-400 shadow-[0_0_8px_rgba(20,184,166,0.8)]" />
          <div className="text-left font-mono">
            <span className="text-[11px] text-teal-300 font-semibold block">Verified Inactivity</span>
            <span className="text-xs text-slate-200">Cult Gym: 0 Visits / 90 Days</span>
          </div>
        </div>

        {/* Central Content Composition */}
        <div className="max-w-3xl flex flex-col items-center gap-6">
          {/* Eyebrow Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold bg-gradient-to-r from-teal-500/10 via-cyan-500/15 to-teal-500/10 border border-cyan-400/30 text-cyan-300 shadow-[0_0_20px_rgba(6,182,212,0.2)] anim-stage-3">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            <span>Autonomous Recurring Payment Intelligence</span>
          </div>

          {/* Primary Cinematic Headline */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-white leading-[1.08] anim-stage-3">
            Every recurring payment.{" "}
            <span className="block mt-1 text-transparent bg-clip-text bg-gradient-to-r from-teal-300 via-cyan-400 to-cyan-200 drop-shadow-[0_0_35px_rgba(6,182,212,0.4)]">
              Finally, in focus.
            </span>
          </h1>

          {/* Supporting Copy */}
          <p className="text-base sm:text-xl text-slate-300 font-normal leading-relaxed max-w-2xl anim-stage-3-delayed">
            Discover hidden commitments, understand recurring costs, detect unexpected changes and take control of your financial outflows.
          </p>

          {/* Primary & Secondary Call-to-Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center gap-4 pt-4 w-full sm:w-auto anim-stage-3-delayed">
            <Link
              href="/dashboard"
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-[#F08A00] to-[#FFA52B] hover:brightness-110 text-[#011633] font-bold text-sm tracking-wide transition-all shadow-[0_0_30px_rgba(240,138,0,0.4)] hover:shadow-[0_0_45px_rgba(240,138,0,0.6)] hover:scale-[1.02] active:scale-[0.98] text-center"
            >
              Open PayScope Dashboard →
            </Link>
            <Link
              href="/financial-impact"
              className="w-full sm:w-auto px-7 py-4 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold text-sm tracking-wide transition-all shadow-[0_0_20px_rgba(6,182,212,0.3)] hover:scale-[1.02] active:scale-[0.98] text-center"
            >
              Financial Projections
            </Link>
            <Link
              href="/cancellations"
              className="w-full sm:w-auto px-7 py-4 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 hover:border-cyan-500/50 text-slate-200 hover:text-white font-semibold text-sm transition-all backdrop-blur-md text-center"
            >
              Cancellation Centre
            </Link>
          </div>

          {/* Key Assurance Signals */}
          <div className="flex flex-wrap justify-center items-center gap-6 pt-6 text-xs text-slate-400 anim-stage-3-delayed">
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Explainable Calculations
            </span>
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Synthetic Data Sandbox
            </span>
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Evidence-Backed Auditing
            </span>
          </div>
        </div>
      </main>

      {/* ==================================================================== */}
      {/* FOOTER: Discreet System & Attribution Bar                            */}
      {/* ==================================================================== */}
      <footer className="relative z-10 border-t border-slate-900 bg-slate-950/80 backdrop-blur-sm py-4 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>PayScope &bull; Intelligent Recurring Payment Platform</span>
          <div className="flex items-center gap-4 text-[11px]">
            <Link href="/financial-impact" className="hover:text-cyan-400 transition-colors">
              Annual Outflows
            </Link>
            <Link href="/savings" className="hover:text-teal-400 transition-colors">
              What-If Calculator
            </Link>
            <Link href="/upload" className="hover:text-slate-300 transition-colors">
              Statement Ingestion
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
