"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

interface FinancialSummary {
  currency: string;
  monthly_recurring_spend: number;
  annualized_recurring_spend: number;
  total_confirmed_commitments: number;
  potential_candidate_annual_cost: number;
  total_candidate_commitments: number;
  historical_spend_12m: number;
  upcoming_30d_expected_spend: number;
  potential_annual_savings: number;
  calculation_timestamp: string;
}

interface CommitmentCostItem {
  commitment_id: string;
  merchant_id: string | null;
  merchant_name: string;
  display_name: string;
  commitment_type: string;
  cadence: string;
  amount_pattern: string;
  representative_amount: number;
  currency: string;
  normalized_monthly_cost: number;
  annualized_cost: number;
  calculation_method: string;
  confidence_band: string;
  status: string;
  is_confirmed: boolean;
  is_candidate: boolean;
  next_expected_date: string | null;
  transaction_count: number;
}

interface CategoryBreakdown {
  category: string;
  category_label: string;
  monthly_cost: number;
  annualized_cost: number;
  historical_spend_12m: number;
  percentage_of_recurring: number;
  commitment_count: number;
}

interface MerchantRanking {
  merchant_id: string | null;
  merchant_name: string;
  category: string;
  monthly_cost: number;
  annualized_cost: number;
  historical_spend_12m: number;
  percentage_of_total: number;
  commitment_count: number;
  aliases: string[];
}

interface UpcomingItem {
  commitment_id: string;
  display_name: string;
  merchant_name: string;
  expected_date: string;
  estimated_amount: number;
  currency: string;
  cadence: string;
  estimation_basis: string;
  is_confirmed: boolean;
}

interface UpcomingResponse {
  currency: string;
  total_upcoming_30d: number;
  total_upcoming_60d: number;
  items: UpcomingItem[];
}

export default function FinancialImpactPage() {
  const [summary, setSummary] = useState<FinancialSummary | null>(null);
  const [commitments, setCommitments] = useState<CommitmentCostItem[]>([]);
  const [categories, setCategories] = useState<CategoryBreakdown[]>([]);
  const [merchants, setMerchants] = useState<MerchantRanking[]>([]);
  const [upcoming, setUpcoming] = useState<UpcomingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tab filter: all, confirmed, candidates
  const [activeTab, setActiveTab] = useState<"all" | "confirmed" | "candidates">("confirmed");
  const [searchQuery, setSearchQuery] = useState("");

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  useEffect(() => {
    let ignore = false;

    async function loadFinancialData() {
      setLoading(true);
      setError(null);

      try {
        const [sumRes, comRes, catRes, merRes, upRes] = await Promise.all([
          fetch(`${apiBase}/api/v1/financial-impact/summary`),
          fetch(`${apiBase}/api/v1/financial-impact/commitments`),
          fetch(`${apiBase}/api/v1/financial-impact/categories`),
          fetch(`${apiBase}/api/v1/financial-impact/merchants`),
          fetch(`${apiBase}/api/v1/financial-impact/upcoming`),
        ]);

        if (!sumRes.ok || !comRes.ok) {
          throw new Error("Failed to load financial impact calculations.");
        }

        const [sumData, comData, catData, merData, upData] = await Promise.all([
          sumRes.json(),
          comRes.json(),
          catRes.ok ? catRes.json() : [],
          merRes.ok ? merRes.json() : [],
          upRes.ok ? upRes.json() : null,
        ]);

        if (!ignore) {
          setSummary(sumData);
          setCommitments(comData);
          setCategories(catData);
          setMerchants(merData);
          setUpcoming(upData);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Error connecting to backend API.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    loadFinancialData();
    return () => {
      ignore = true;
    };
  }, [apiBase]);

  const filteredCommitments = commitments.filter((item) => {
    if (activeTab === "confirmed" && !item.is_confirmed) return false;
    if (activeTab === "candidates" && !item.is_candidate) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        item.display_name.toLowerCase().includes(q) ||
        item.merchant_name.toLowerCase().includes(q) ||
        item.commitment_type.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 antialiased selection:bg-cyan-500 selection:text-slate-950">
      {/* Platform Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center font-bold text-cyan-400 text-lg shadow-sm">
              M
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-lg tracking-tight text-white flex items-center gap-2">
                Mandate<span className="text-cyan-400">Lens</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 font-normal">
                  Annual Outflows
                </span>
              </span>
            </div>
          </Link>

          <nav className="flex items-center gap-2 text-xs font-medium">
            <Link
              href="/financial-impact"
              className="px-3 py-1.5 rounded-md border border-cyan-500/30 bg-cyan-500/10 text-cyan-300 font-semibold shadow-sm"
            >
              Financial Impact
            </Link>
            <Link
              href="/savings"
              className="px-3 py-1.5 rounded-md border border-teal-500/30 bg-teal-500/10 text-teal-300 hover:bg-teal-500/20 transition-colors font-semibold"
            >
              Savings & Projections
            </Link>
            <Link
              href="/commitments"
              className="px-3 py-1.5 rounded-md text-slate-300 hover:text-white hover:bg-slate-800/50 transition-colors"
            >
              Commitments
            </Link>
            <Link
              href="/insights"
              className="px-3 py-1.5 rounded-md text-slate-300 hover:text-white hover:bg-slate-800/50 transition-colors"
            >
              Insights
            </Link>
            <Link
              href="/upload"
              className="px-3 py-1.5 rounded-md text-slate-300 hover:text-white hover:bg-slate-800/50 transition-colors"
            >
              Upload
            </Link>
          </nav>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
        {/* Title & Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              Annual Financial Impact & Expenditure
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Normalized monthly recurring costs, annualized commitments, category distributions, and upcoming obligations.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/savings"
              className="px-4 py-2 rounded-lg bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold text-xs tracking-wide transition-all shadow-[0_0_15px_rgba(6,182,212,0.3)] flex items-center gap-2"
            >
              <span>Explore Savings Scenarios &rarr;</span>
            </Link>
          </div>
        </div>

        {/* Loading and Error States */}
        {loading && (
          <div className="p-12 text-center rounded-xl border border-slate-800 bg-slate-900/40">
            <div className="w-8 h-8 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin mx-auto mb-3" />
            <span className="text-sm text-slate-400 font-mono">Computing financial impact metrics...</span>
          </div>
        )}

        {error && (
          <div className="p-6 rounded-xl border border-rose-900/50 bg-rose-950/20 text-rose-300 text-sm">
            <strong>Error loading calculations:</strong> {error}
          </div>
        )}

        {!loading && summary && (
          <>
            {/* Top Metrics Cards */}
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {/* Monthly Recurring Spend */}
              <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-5 backdrop-blur-sm flex flex-col justify-between">
                <span className="text-xs font-medium text-slate-400">Monthly Recurring Outflow</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl lg:text-3xl font-bold text-white font-mono">
                    ₹{summary.monthly_recurring_spend.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                  <span className="text-xs text-slate-500 font-normal">/mo</span>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
                  <span>{summary.total_confirmed_commitments} Confirmed Mandates</span>
                  <span className="text-cyan-400">Fixed & Regular</span>
                </div>
              </div>

              {/* Annualized Recurring Spend */}
              <div className="rounded-xl border border-cyan-500/30 bg-gradient-to-b from-cyan-950/20 to-slate-900/50 p-5 backdrop-blur-sm flex flex-col justify-between shadow-[0_0_20px_rgba(6,182,212,0.08)]">
                <span className="text-xs font-semibold text-cyan-300">Annualized Recurring Outflow</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl lg:text-3xl font-bold text-cyan-300 font-mono">
                    ₹{summary.annualized_recurring_spend.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                  <span className="text-xs text-cyan-400/70 font-normal">/yr</span>
                </div>
                <div className="mt-3 pt-2 border-t border-cyan-900/40 flex items-center justify-between text-[11px] text-slate-400">
                  <span>Normalized Projection</span>
                  <span className="text-cyan-300">Baseline</span>
                </div>
              </div>

              {/* Historical 12M Actual Spend */}
              <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-5 backdrop-blur-sm flex flex-col justify-between">
                <span className="text-xs font-medium text-slate-400">Historical 12M Debits</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl lg:text-3xl font-bold text-slate-200 font-mono">
                    ₹{summary.historical_spend_12m.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
                  <span>Observed Bank Debits</span>
                  <span className="text-emerald-400">Excludes Failed</span>
                </div>
              </div>

              {/* Upcoming 30D Expected */}
              <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-5 backdrop-blur-sm flex flex-col justify-between">
                <span className="text-xs font-medium text-slate-400">Upcoming 30D Expected</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl lg:text-3xl font-bold text-amber-300 font-mono">
                    ₹{summary.upcoming_30d_expected_spend.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
                  <span>Next 30 Days Due</span>
                  <span className="text-amber-400/80 font-mono">Cadence Queue</span>
                </div>
              </div>

              {/* Potential Annual Savings */}
              <div className="rounded-xl border border-teal-500/40 bg-teal-950/20 p-5 backdrop-blur-sm flex flex-col justify-between shadow-[0_0_20px_rgba(20,184,166,0.12)]">
                <span className="text-xs font-semibold text-teal-300">Potential Annual Savings</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl lg:text-3xl font-bold text-teal-300 font-mono">
                    ₹{summary.potential_annual_savings.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                  <span className="text-xs text-teal-400/80 font-normal">/yr</span>
                </div>
                <div className="mt-3 pt-2 border-t border-teal-900/40 flex items-center justify-between text-[11px] text-teal-400">
                  <span>Opportunities Detected</span>
                  <Link href="/savings" className="underline hover:text-white">
                    Simulate &rarr;
                  </Link>
                </div>
              </div>
            </section>

            {/* Candidate Obligations Banner (Suraksha General Insurance etc.) */}
            {summary.total_candidate_commitments > 0 && (
              <div className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-400 mt-1 flex-shrink-0 animate-pulse" />
                  <div>
                    <h4 className="text-sm font-semibold text-amber-300">
                      {summary.total_candidate_commitments} Candidate Obligation Separated (₹{summary.potential_candidate_annual_cost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}/yr)
                    </h4>
                    <p className="text-xs text-slate-300 mt-0.5">
                      Single annual transactions (e.g. Suraksha General Insurance) are preserved as candidates and excluded from confirmed recurring totals until verified.
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setActiveTab("candidates")}
                  className="px-3 py-1.5 rounded-lg border border-amber-500/40 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 text-xs font-medium whitespace-nowrap transition-colors"
                >
                  Review Candidate Obligations
                </button>
              </div>
            )}

            {/* Visual Analytics Grid: Category Distribution & Merchant Rankings */}
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Category Breakdown */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold text-white">Expenditure by Category</h3>
                  <span className="text-xs text-slate-400">{categories.length} Categories Active</span>
                </div>

                <div className="space-y-4 pt-2">
                  {categories.map((cat) => (
                    <div key={cat.category} className="space-y-1.5">
                      <div className="flex justify-between text-xs font-mono">
                        <span className="text-slate-300 font-sans font-medium">{cat.category_label}</span>
                        <div className="flex items-center gap-3">
                          <span className="text-slate-400 font-sans">{cat.commitment_count} services</span>
                          <span className="text-cyan-300 font-bold">
                            ₹{cat.annualized_cost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}/yr
                          </span>
                          <span className="text-slate-500 text-[11px] w-12 text-right">({cat.percentage_of_recurring}%)</span>
                        </div>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-teal-500 to-cyan-400 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(100, Math.max(5, cat.percentage_of_recurring))}%` }}
                        />
                      </div>
                    </div>
                  ))}
                  {categories.length === 0 && (
                    <span className="text-xs text-slate-500">No confirmed commitments categorized yet.</span>
                  )}
                </div>
              </div>

              {/* Merchant Cost Rankings */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold text-white">Top Merchants by Recurring Outflow</h3>
                  <span className="text-xs text-slate-400">Canonical Identity Ranking</span>
                </div>

                <div className="space-y-3 pt-2">
                  {merchants.slice(0, 5).map((m, idx) => (
                    <div
                      key={m.merchant_id || idx}
                      className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs"
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-5 h-5 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center font-mono text-[10px] font-bold">
                          {idx + 1}
                        </span>
                        <div>
                          <span className="font-semibold text-white block">{m.merchant_name}</span>
                          <span className="text-[11px] text-slate-400">
                            {m.commitment_count} mandate &bull; {m.category}
                          </span>
                        </div>
                      </div>

                      <div className="text-right font-mono">
                        <span className="text-cyan-300 font-bold block">
                          ₹{m.annualized_cost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}/yr
                        </span>
                        <span className="text-[11px] text-slate-500">
                          ₹{m.monthly_cost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}/mo
                        </span>
                      </div>
                    </div>
                  ))}
                  {merchants.length === 0 && (
                    <span className="text-xs text-slate-500">No merchant rankings available.</span>
                  )}
                </div>
              </div>
            </section>

            {/* Upcoming Payment Obligations */}
            {upcoming && upcoming.items.length > 0 && (
              <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-base font-semibold text-white">Upcoming Cadence Queue (Next 60 Days)</h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Expected payment schedule derived from verified recurrence cadence.
                    </p>
                  </div>
                  <span className="text-xs font-mono px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
                    60D Total: ₹{upcoming.total_upcoming_60d.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
                  {upcoming.items.slice(0, 8).map((up) => (
                    <div
                      key={up.commitment_id}
                      className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 flex flex-col justify-between text-xs font-mono"
                    >
                      <div className="flex justify-between items-start gap-2">
                        <span className="font-sans font-semibold text-slate-200 truncate">{up.display_name}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950/80 border border-cyan-800/40 text-cyan-300 uppercase">
                          {up.cadence}
                        </span>
                      </div>
                      <div className="mt-2 flex justify-between items-baseline">
                        <span className="text-amber-400 font-bold">
                          ₹{up.estimated_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </span>
                        <span className="text-[11px] text-slate-400">{up.expected_date}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Commitment Cost Table */}
            <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h3 className="text-base font-semibold text-white">Recurring Commitment Directory</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Individual commitment calculations, cadences, and monthly normalized equivalents.
                  </p>
                </div>

                {/* Filter Controls */}
                <div className="flex items-center gap-2">
                  <div className="flex rounded-lg bg-slate-950 border border-slate-800 p-0.5 text-xs font-medium">
                    <button
                      onClick={() => setActiveTab("confirmed")}
                      className={`px-3 py-1 rounded-md transition-all ${
                        activeTab === "confirmed"
                          ? "bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30"
                          : "text-slate-400 hover:text-white"
                      }`}
                    >
                      Confirmed ({commitments.filter((c) => c.is_confirmed).length})
                    </button>
                    <button
                      onClick={() => setActiveTab("candidates")}
                      className={`px-3 py-1 rounded-md transition-all ${
                        activeTab === "candidates"
                          ? "bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30"
                          : "text-slate-400 hover:text-white"
                      }`}
                    >
                      Candidates ({commitments.filter((c) => c.is_candidate).length})
                    </button>
                    <button
                      onClick={() => setActiveTab("all")}
                      className={`px-3 py-1 rounded-md transition-all ${
                        activeTab === "all"
                          ? "bg-slate-800 text-white font-bold"
                          : "text-slate-400 hover:text-white"
                      }`}
                    >
                      All ({commitments.length})
                    </button>
                  </div>

                  <input
                    type="text"
                    placeholder="Search commitment..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="px-3 py-1 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              {/* Table */}
              <div className="overflow-x-auto rounded-lg border border-slate-800/80">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase text-[11px] font-mono">
                    <tr>
                      <th className="py-3 px-4">Merchant & Commitment</th>
                      <th className="py-3 px-4">Cadence</th>
                      <th className="py-3 px-4">Representative Amt</th>
                      <th className="py-3 px-4">Monthly Normalized</th>
                      <th className="py-3 px-4">Annualized Cost</th>
                      <th className="py-3 px-4">Confidence</th>
                      <th className="py-3 px-4">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredCommitments.map((c) => (
                      <tr key={c.commitment_id} className="hover:bg-slate-900/60 transition-colors">
                        <td className="py-3 px-4">
                          <Link
                            href={`/commitments/${c.commitment_id}`}
                            className="font-medium text-white hover:text-cyan-400 transition-colors block"
                          >
                            {c.display_name}
                          </Link>
                          <span className="text-[11px] text-slate-400 block">
                            {c.merchant_name} &bull; {c.commitment_type}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono capitalize text-slate-300">
                          {c.cadence.replace("_", " ")}
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-300">
                          ₹{c.representative_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4 font-mono font-semibold text-cyan-300">
                          ₹{c.normalized_monthly_cost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}/mo
                        </td>
                        <td className="py-3 px-4 font-mono font-bold text-white">
                          ₹{c.annualized_cost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}/yr
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                              c.confidence_band === "high"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                : c.confidence_band === "medium"
                                ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
                                : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                            }`}
                          >
                            {c.confidence_band}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono capitalize ${
                              c.is_confirmed
                                ? "bg-emerald-950/40 text-emerald-300 border border-emerald-800/40"
                                : "bg-amber-950/40 text-amber-300 border border-amber-800/40"
                            }`}
                          >
                            {c.is_confirmed ? "Confirmed" : "Candidate"}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {filteredCommitments.length === 0 && (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-slate-500 text-xs">
                          No commitments match the selected filter.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
