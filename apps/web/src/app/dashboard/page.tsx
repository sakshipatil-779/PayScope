"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import AppHeader from "@/components/navigation/AppHeader";

interface DashboardKPIs {
  active_commitments_count: number;
  monthly_recurring_spend: number | string;
  annualized_recurring_spend: number | string;
  open_insights_count: number;
  potential_annual_savings: number | string;
  cancellations_attention_count: number;
}

interface DashboardFinancialOverview {
  monthly_recurring_spend: number | string;
  annualized_recurring_spend: number | string;
  upcoming_month_expected: number | string;
  candidate_annual_cost: number | string;
  historical_months: string[];
  historical_amounts: (number | string)[];
}

interface DashboardTopCommitment {
  id: string;
  display_name: string;
  merchant_name?: string | null;
  category: string;
  cadence: string;
  monthly_cost: number | string;
  status: string;
  confidence_band: string;
}

interface DashboardRecentInsight {
  id: string;
  commitment_id: string;
  commitment_name: string;
  insight_type: string;
  severity: string;
  title: string;
  summary: string;
}

interface DashboardSummaryData {
  kpis: DashboardKPIs;
  financial_overview: DashboardFinancialOverview;
  top_commitments: DashboardTopCommitment[];
  category_distribution: Record<string, number | string>;
  recent_insights: DashboardRecentInsight[];
  insight_type_counts: Record<string, number>;
  cancellation_summary: Record<string, number>;
  merchant_review_pending: number;
  canonical_merchants_count: number;
}

export default function UnifiedDashboardPage() {
  const [data, setData] = useState<DashboardSummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  useEffect(() => {
    let ignore = false;
    async function loadDashboard() {
      try {
        const res = await fetch(`${apiBase}/api/v1/dashboard/summary`);
        if (!ignore && res.ok) {
          const json = await res.json();
          setData(json);
        } else if (!ignore) {
          setError("Failed to load dashboard data.");
        }
      } catch (err) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Network error");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }
    loadDashboard();
    return () => {
      ignore = true;
    };
  }, [apiBase]);

  const formatINR = (val: number | string | undefined | null) => {
    const num = Number(val) || 0;
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(num);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#011633] text-[#F4F7FB] flex flex-col">
        <AppHeader />
        <div className="flex-1 max-w-7xl w-full mx-auto p-6 sm:p-8 flex flex-col gap-6 animate-pulse">
          <div className="h-20 bg-[#082746] rounded-2xl border border-[#164B68]" />
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-28 bg-[#082746] rounded-xl border border-[#164B68]" />
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="h-64 bg-[#082746] rounded-2xl border border-[#164B68]" />
            <div className="h-64 bg-[#082746] rounded-2xl border border-[#164B68]" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-[#011633] text-white flex flex-col">
        <AppHeader />
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="max-w-md w-full p-6 rounded-2xl bg-[#082746] border border-[#164B68] text-center flex flex-col gap-4">
            <h2 className="text-lg font-bold text-rose-400">Dashboard Unavailable</h2>
            <p className="text-xs text-[#A9BBCD]">{error || "Could not retrieve summary metrics."}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-xl bg-[#031B38] border border-[#164B68] text-xs font-semibold hover:border-[#00B8C7]"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const { kpis, financial_overview, top_commitments, category_distribution, recent_insights, insight_type_counts, cancellation_summary } = data;

  return (
    <div className="min-h-screen flex flex-col bg-[#011633] text-[#F4F7FB] selection:bg-[#F08A00] selection:text-white">
      <AppHeader />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
        {/* Welcome Banner */}
        <div className="rounded-2xl bg-gradient-to-r from-[#082746] via-[#0B3152] to-[#031B38] border border-[#164B68] p-6 sm:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-[#F08A00]/15 text-[#FFA52B] border border-[#F08A00]/30 mb-2">
              PayScope Intelligence Engine Active
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Financial Command Centre
            </h1>
            <p className="text-xs sm:text-sm text-[#A9BBCD] mt-1 max-w-2xl">
              Consolidated real-time monitoring of active recurring obligations, silent price increases, upcoming debits, and verified cancellation guidance.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Link
              href="/upload"
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-[#F08A00] to-[#FFA52B] hover:brightness-110 text-[#011633] font-bold text-xs transition-all shadow-md shadow-[#F08A00]/20"
            >
              + Ingest Statement
            </Link>
          </div>
        </div>

        {/* Top 6 KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {/* KPI 1 */}
          <div className="p-4 rounded-xl bg-[#082746] border border-[#164B68] flex flex-col gap-1 hover:border-[#00B8C7] transition-colors">
            <span className="text-[11px] font-medium text-[#A9BBCD]">Active Commitments</span>
            <span className="text-xl sm:text-2xl font-black text-white">{kpis.active_commitments_count}</span>
            <Link href="/commitments" className="text-[10px] text-[#00E0E0] hover:underline mt-auto">
              View all →
            </Link>
          </div>

          {/* KPI 2 */}
          <div className="p-4 rounded-xl bg-[#082746] border border-[#164B68] flex flex-col gap-1 hover:border-[#00B8C7] transition-colors">
            <span className="text-[11px] font-medium text-[#A9BBCD]">Monthly Spend</span>
            <span className="text-xl sm:text-2xl font-black text-white">{formatINR(kpis.monthly_recurring_spend)}</span>
            <span className="text-[10px] text-[#A9BBCD]">Normalized debits</span>
          </div>

          {/* KPI 3 */}
          <div className="p-4 rounded-xl bg-[#082746] border border-[#164B68] flex flex-col gap-1 hover:border-[#00B8C7] transition-colors">
            <span className="text-[11px] font-medium text-[#A9BBCD]">Annualized Spend</span>
            <span className="text-xl sm:text-2xl font-black text-white">{formatINR(kpis.annualized_recurring_spend)}</span>
            <Link href="/financial-impact" className="text-[10px] text-[#00E0E0] hover:underline mt-auto">
              Projections →
            </Link>
          </div>

          {/* KPI 4 */}
          <div className="p-4 rounded-xl bg-[#082746] border border-[#164B68] flex flex-col gap-1 hover:border-[#00B8C7] transition-colors">
            <span className="text-[11px] font-medium text-[#A9BBCD]">Open Insights</span>
            <span className={`text-xl sm:text-2xl font-black ${kpis.open_insights_count > 0 ? "text-amber-400" : "text-white"}`}>
              {kpis.open_insights_count}
            </span>
            <Link href="/insights" className="text-[10px] text-amber-300 hover:underline mt-auto">
              Inspect anomalies →
            </Link>
          </div>

          {/* KPI 5 */}
          <div className="p-4 rounded-xl bg-[#082746] border border-[#164B68] flex flex-col gap-1 hover:border-[#F08A00] transition-colors">
            <span className="text-[11px] font-medium text-[#A9BBCD]">Potential Savings</span>
            <span className="text-xl sm:text-2xl font-black text-[#FFA52B]">{formatINR(kpis.potential_annual_savings)}</span>
            <Link href="/savings" className="text-[10px] text-[#FFA52B] hover:underline mt-auto">
              What-If simulator →
            </Link>
          </div>

          {/* KPI 6 */}
          <div className="p-4 rounded-xl bg-[#082746] border border-[#164B68] flex flex-col gap-1 hover:border-[#00B8C7] transition-colors">
            <span className="text-[11px] font-medium text-[#A9BBCD]">Cancellation Focus</span>
            <span className={`text-xl sm:text-2xl font-black ${kpis.cancellations_attention_count > 0 ? "text-[#00E0E0]" : "text-white"}`}>
              {kpis.cancellations_attention_count}
            </span>
            <Link href="/cancellations" className="text-[10px] text-[#00E0E0] hover:underline mt-auto">
              Cancellation Centre →
            </Link>
          </div>
        </div>

        {/* Section A & D: Financial Overview and Savings Intelligence */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Card A: Financial Spend Trajectory */}
          <div className="p-6 rounded-2xl bg-[#082746] border border-[#164B68] flex flex-col gap-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-white">Financial Spend Trajectory</h2>
                <p className="text-xs text-[#A9BBCD] mt-0.5">Historical observed vs upcoming 30d projection</p>
              </div>
              <Link href="/financial-impact" className="text-xs text-[#00E0E0] hover:underline">
                Full Details →
              </Link>
            </div>

            <div className="grid grid-cols-3 gap-3 p-3.5 rounded-xl bg-[#031B38] border border-[#164B68] text-center">
              <div>
                <span className="text-[10px] text-[#A9BBCD] block">Upcoming 30d</span>
                <span className="text-sm font-bold text-white">{formatINR(financial_overview.upcoming_month_expected)}</span>
              </div>
              <div>
                <span className="text-[10px] text-[#A9BBCD] block">Candidate Potential</span>
                <span className="text-sm font-bold text-amber-300">{formatINR(financial_overview.candidate_annual_cost)}</span>
              </div>
              <div>
                <span className="text-[10px] text-[#A9BBCD] block">Annual Spend</span>
                <span className="text-sm font-bold text-[#00E0E0]">{formatINR(financial_overview.annualized_recurring_spend)}</span>
              </div>
            </div>

            {/* Historical Bar Graphic */}
            <div className="flex flex-col gap-2">
              <span className="text-xs font-semibold text-[#A9BBCD]">6-Month Debit Expenditure Windows</span>
              <div className="grid grid-cols-5 gap-2 pt-4 items-end h-32 border-b border-[#164B68] pb-2">
                {financial_overview.historical_months.map((month, idx) => {
                  const amt = Number(financial_overview.historical_amounts[idx]) || 0;
                  const maxAmt = Math.max(...financial_overview.historical_amounts.map(Number), 1);
                  const barHeight = Math.max(12, Math.round((amt / maxAmt) * 100));

                  return (
                    <div key={idx} className="flex flex-col items-center gap-1.5 h-full justify-end group">
                      <div className="text-[10px] text-white opacity-0 group-hover:opacity-100 transition-opacity font-mono">
                        {formatINR(amt)}
                      </div>
                      <div
                        className="w-full rounded-t-lg bg-gradient-to-t from-[#00B8C7] to-[#00E0E0] group-hover:from-[#F08A00] group-hover:to-[#FFA52B] transition-all"
                        style={{ height: `${barHeight}%` }}
                      />
                      <span className="text-[10px] text-[#A9BBCD] truncate w-full text-center">{month}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Card D: Category Distribution & Savings Opportunity */}
          <div className="p-6 rounded-2xl bg-[#082746] border border-[#164B68] flex flex-col gap-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-white">Spend by Category</h2>
                <p className="text-xs text-[#A9BBCD] mt-0.5">Recurring commitment budget allocation</p>
              </div>
              <Link href="/savings" className="text-xs text-[#FFA52B] hover:underline">
                Savings Simulator →
              </Link>
            </div>

            <div className="space-y-3">
              {Object.entries(category_distribution).map(([cat, amt]) => {
                const totalMonthly = Number(kpis.monthly_recurring_spend) || 1;
                const pct = Math.min(100, Math.round((Number(amt) / totalMonthly) * 100));

                return (
                  <div key={cat} className="flex flex-col gap-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-white">{cat}</span>
                      <span className="text-[#A9BBCD] font-mono">{formatINR(amt)}/mo ({pct}%)</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-[#031B38] overflow-hidden border border-[#164B68]">
                      <div
                        className="h-full bg-gradient-to-r from-[#00B8C7] to-[#FFA52B]"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-auto p-4 rounded-xl bg-gradient-to-r from-[#F08A00]/10 to-[#FFA52B]/10 border border-[#F08A00]/30 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-white block">Potential Annual Savings Identified</span>
                <span className="text-[11px] text-[#A9BBCD]">Based on price spikes and unused subscriptions</span>
              </div>
              <span className="text-base font-black text-[#FFA52B]">{formatINR(kpis.potential_annual_savings)}</span>
            </div>
          </div>
        </div>

        {/* Section B & C: Commitments and Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Card B: Top Commitments */}
          <div className="p-6 rounded-2xl bg-[#082746] border border-[#164B68] flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-white">Top Recurring Commitments</h2>
              <Link href="/commitments" className="text-xs text-[#00E0E0] hover:underline">
                View all ({kpis.active_commitments_count}) →
              </Link>
            </div>

            <div className="space-y-2">
              {top_commitments.map((c) => (
                <div
                  key={c.id}
                  className="p-3.5 rounded-xl bg-[#031B38] border border-[#164B68] flex items-center justify-between hover:border-[#00B8C7] transition-colors"
                >
                  <div className="flex flex-col gap-0.5">
                    <Link href={`/commitments/${c.id}`} className="text-sm font-semibold text-white hover:text-[#00E0E0]">
                      {c.display_name}
                    </Link>
                    <div className="flex items-center gap-2 text-[11px] text-[#A9BBCD]">
                      <span>{c.category}</span>
                      <span>•</span>
                      <span className="capitalize">{c.cadence}</span>
                    </div>
                  </div>

                  <div className="text-right flex flex-col items-end gap-1">
                    <span className="text-sm font-bold text-white">{formatINR(c.monthly_cost)}<span className="text-[10px] text-[#A9BBCD]">/mo</span></span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                      Confirmed
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Card C: Anomaly Insights */}
          <div className="p-6 rounded-2xl bg-[#082746] border border-[#164B68] flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-white">Active Payment Anomaly Insights</h2>
              <Link href="/insights" className="text-xs text-amber-300 hover:underline">
                View all ({kpis.open_insights_count}) →
              </Link>
            </div>

            {/* Type breakdown pills */}
            <div className="flex flex-wrap gap-2">
              <span className="text-xs px-2.5 py-1 rounded-lg bg-[#031B38] border border-[#164B68] text-[#A9BBCD]">
                Price Spikes: <strong className="text-white">{insight_type_counts["price_increase"] || 0}</strong>
              </span>
              <span className="text-xs px-2.5 py-1 rounded-lg bg-[#031B38] border border-[#164B68] text-[#A9BBCD]">
                Trial Conversions: <strong className="text-white">{insight_type_counts["trial_conversion"] || 0}</strong>
              </span>
              <span className="text-xs px-2.5 py-1 rounded-lg bg-[#031B38] border border-[#164B68] text-[#A9BBCD]">
                Unused: <strong className="text-white">{insight_type_counts["potentially_unused"] || 0}</strong>
              </span>
              <span className="text-xs px-2.5 py-1 rounded-lg bg-[#031B38] border border-[#164B68] text-[#A9BBCD]">
                Post-Cancel: <strong className="text-white">{insight_type_counts["post_cancellation_charge"] || 0}</strong>
              </span>
            </div>

            <div className="space-y-2 mt-2">
              {recent_insights.length === 0 ? (
                <div className="p-6 rounded-xl bg-[#031B38] text-center text-xs text-[#A9BBCD]">
                  No open anomalies detected. Your recurring payments are healthy.
                </div>
              ) : (
                recent_insights.map((ins) => (
                  <div
                    key={ins.id}
                    className="p-3.5 rounded-xl bg-[#031B38] border border-amber-500/30 flex items-start justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-white">{ins.title}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono">
                          {ins.insight_type.replace("_", " ")}
                        </span>
                      </div>
                      <p className="text-xs text-[#A9BBCD] mt-1 line-clamp-2">{ins.summary}</p>
                    </div>
                    <Link
                      href={`/insights/${ins.id}`}
                      className="px-2.5 py-1 rounded-lg bg-[#082746] border border-[#164B68] text-[11px] text-[#00E0E0] hover:border-[#00B8C7] shrink-0 font-medium"
                    >
                      Inspect →
                    </Link>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Section E & F: Cancellations and Merchant Review */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Card E: Cancellation Centre Snapshot */}
          <div className="p-6 rounded-2xl bg-[#082746] border border-[#164B68] flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-white">Cancellation Centre Snapshot</h2>
              <Link href="/cancellations" className="text-xs text-[#00E0E0] hover:underline">
                Open Centre →
              </Link>
            </div>

            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-3 rounded-xl bg-[#031B38] border border-[#164B68]">
                <span className="text-xs text-[#A9BBCD] block">In Progress</span>
                <span className="text-lg font-bold text-[#00E0E0]">{cancellation_summary["in_progress"] || 0}</span>
              </div>
              <div className="p-3 rounded-xl bg-[#031B38] border border-[#164B68]">
                <span className="text-xs text-[#A9BBCD] block">Reported</span>
                <span className="text-lg font-bold text-amber-400">{cancellation_summary["user_reported"] || 0}</span>
              </div>
              <div className="p-3 rounded-xl bg-[#031B38] border border-[#164B68]">
                <span className="text-xs text-[#A9BBCD] block">Verified Stop</span>
                <span className="text-lg font-bold text-emerald-400">{cancellation_summary["verified_cancelled"] || 0}</span>
              </div>
            </div>

            <p className="text-xs text-[#A9BBCD] leading-relaxed">
              Playbooks offer step-by-step guidance for UPI AutoPay, Card SI, and e-NACH revocation. Reporting cancellation establishes active surveillance against post-cancellation debit charges.
            </p>
          </div>

          {/* Card F: Merchant Intelligence & Relationships */}
          <div className="p-6 rounded-2xl bg-[#082746] border border-[#164B68] flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-white">Merchant Intelligence & Graph</h2>
              <Link href="/relationships" className="text-xs text-[#FFA52B] hover:underline">
                Relationship Explorer →
              </Link>
            </div>

            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="p-3 rounded-xl bg-[#031B38] border border-[#164B68]">
                <span className="text-xs text-[#A9BBCD] block">Canonical Merchants</span>
                <span className="text-lg font-bold text-white">{data.canonical_merchants_count}</span>
              </div>
              <div className="p-3 rounded-xl bg-[#031B38] border border-[#164B68]">
                <span className="text-xs text-[#A9BBCD] block">Pending Reviews</span>
                <span className="text-lg font-bold text-amber-400">{data.merchant_review_pending}</span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              <Link
                href="/merchant-review"
                className="text-xs font-semibold text-[#00E0E0] hover:underline"
              >
                Resolve Unmatched Descriptors →
              </Link>
              <Link
                href="/relationships"
                className="px-3.5 py-1.5 rounded-xl bg-[#031B38] border border-[#164B68] text-xs font-semibold text-white hover:border-[#00B8C7] transition-colors"
              >
                Explore Neo4j Graph →
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
