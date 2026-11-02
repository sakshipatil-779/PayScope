"use client";

import { getApiBaseUrl } from "@/lib/api";
import React, { useState, useEffect } from "react";
import Link from "next/link";

import AppHeader from "@/components/navigation/AppHeader";

interface InsightItem {
  id: string;
  user_id: string;
  commitment_id: string;
  commitment_name?: string | null;
  merchant_name?: string | null;
  insight_type: string;
  severity: string;
  status: string;
  title: string;
  summary: string;
  explanation?: string | null;
  confidence_score?: number | string | null;
  confidence_band: string;
  detected_at: string;
  detector_version: string;
  user_action?: string | null;
  user_action_at?: string | null;
  user_notes?: string | null;
  evidence_count: number;
  created_at: string;
  updated_at: string;
}

interface InsightSummary {
  total_open: number;
  price_increases: number;
  trial_conversions: number;
  potentially_unused: number;
  post_cancellation_charges: number;
  unusual_amounts: number;
  high_severity: number;
  medium_severity: number;
  low_severity: number;
  estimated_monthly_impact: number | string;
}

export default function InsightsPage() {
  const [insights, setInsights] = useState<InsightItem[]>([]);
  const [summary, setSummary] = useState<InsightSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [detecting, setDetecting] = useState<boolean>(false);
  const [detectMsg, setDetectMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [activeTab, setActiveTab] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const apiBase = getApiBaseUrl();

  const refreshInsights = async () => {
    try {
      const params = new URLSearchParams();
      if (activeTab !== "all") params.append("insight_type", activeTab);
      if (severityFilter) params.append("severity", severityFilter);
      if (statusFilter) params.append("status", statusFilter);

      const [listRes, sumRes] = await Promise.all([
        fetch(`${apiBase}/api/v1/insights?${params.toString()}`),
        fetch(`${apiBase}/api/v1/insights/summary`),
      ]);

      if (listRes.ok) {
        const data = await listRes.json();
        setInsights(data);
      }
      if (sumRes.ok) {
        const sumData = await sumRes.json();
        setSummary(sumData);
      }
    } catch {
      // Ignored
    }
  };

  useEffect(() => {
    let ignore = false;
    async function loadData() {
      try {
        const params = new URLSearchParams();
        if (activeTab !== "all") params.append("insight_type", activeTab);
        if (severityFilter) params.append("severity", severityFilter);
        if (statusFilter) params.append("status", statusFilter);

        const [listRes, sumRes] = await Promise.all([
          fetch(`${apiBase}/api/v1/insights?${params.toString()}`),
          fetch(`${apiBase}/api/v1/insights/summary`),
        ]);

        if (!ignore && listRes.ok) {
          const data = await listRes.json();
          setInsights(data);
        }
        if (!ignore && sumRes.ok) {
          const sumData = await sumRes.json();
          setSummary(sumData);
        }
      } catch (err) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load insights");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    loadData();
    return () => {
      ignore = true;
    };
  }, [apiBase, activeTab, severityFilter, statusFilter]);

  const handleRunDetection = async () => {
    setDetecting(true);
    setDetectMsg(null);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/api/v1/insights/detect`, {
        method: "POST",
      });
      if (res.ok) {
        const detResult = await res.json();
        setDetectMsg(
          `Detection completed in ${detResult.duration_ms}ms: Found ${detResult.total_detected} anomalies across subscriptions.`
        );
        refreshInsights();
      } else {
        setError("Failed to run anomaly intelligence detector.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Network error during detection");
    } finally {
      setDetecting(false);
    }
  };

  const handleAcknowledge = async (id: string) => {
    try {
      const res = await fetch(`${apiBase}/api/v1/insights/${id}/acknowledge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: "Acknowledged via quick actions" }),
      });
      if (res.ok) refreshInsights();
    } catch {
      // Ignored
    }
  };

  const handleDismiss = async (id: string) => {
    try {
      const res = await fetch(`${apiBase}/api/v1/insights/${id}/dismiss`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "Dismissed by user", notes: "" }),
      });
      if (res.ok) refreshInsights();
    } catch {
      // Ignored
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev.toLowerCase()) {
      case "high":
        return (
          <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
            High Severity
          </span>
        );
      case "medium":
        return (
          <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
            Medium Severity
          </span>
        );
      case "low":
        return (
          <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
            Low Severity
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-[#0B3152] text-[#A9BBCD] border border-[#164B68]">
            {sev}
          </span>
        );
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "open":
        return (
          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
            Open
          </span>
        );
      case "acknowledged":
        return (
          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
            Acknowledged
          </span>
        );
      case "resolved":
        return (
          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Resolved
          </span>
        );
      case "dismissed":
        return (
          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-[#0B3152] text-[#A9BBCD] border border-[#164B68]">
            Dismissed
          </span>
        );
      default:
        return null;
    }
  };

  const getTypeLabel = (t: string) => {
    switch (t) {
      case "price_increase":
        return "Price Increase";
      case "trial_conversion":
        return "Trial Conversion";
      case "potentially_unused":
        return "Potentially Unused";
      case "post_cancellation_charge":
        return "Charge After Cancellation";
      case "unusual_amount":
        return "Unusual Amount";
      default:
        return t.replace("_", " ").toUpperCase();
    }
  };

  // Client-side search filter
  const filteredInsights = insights.filter((i) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      i.title.toLowerCase().includes(q) ||
      (i.commitment_name && i.commitment_name.toLowerCase().includes(q)) ||
      (i.merchant_name && i.merchant_name.toLowerCase().includes(q)) ||
      i.summary.toLowerCase().includes(q)
    );
  });

  return (
    <div className="min-h-screen flex flex-col bg-[#011633] text-[#F4F7FB] antialiased selection:bg-[#F08A00] selection:text-white">
      {/* Top Header */}
      <AppHeader />

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
        {/* Page Banner & Action */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-slate-900/80 via-slate-900 to-indigo-950/30 border border-[#164B68]/80">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              Anomaly Intelligence Centre
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                Phase 6 Engine
              </span>
            </h1>
            <p className="mt-1 text-sm text-[#A9BBCD]">
              Deterministic detection of silent price increases, free trial conversions, unused memberships, and post-cancellation charges.
            </p>
          </div>

          <button
            onClick={handleRunDetection}
            disabled={detecting}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition-all shadow-sm shadow-indigo-600/30 cursor-pointer self-start sm:self-auto shrink-0"
          >
            {detecting ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Analyzing Streams...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4 text-indigo-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>Run Intelligence Detection</span>
              </>
            )}
          </button>
        </div>

        {/* Status Alerts */}
        {detectMsg && (
          <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-sm flex items-center justify-between">
            <span>{detectMsg}</span>
            <button onClick={() => setDetectMsg(null)} className="text-indigo-400 hover:text-indigo-200 text-xs font-medium cursor-pointer">
              Dismiss
            </button>
          </div>
        )}
        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-rose-400 hover:text-rose-200 text-xs font-medium cursor-pointer">
              Dismiss
            </button>
          </div>
        )}

        {/* Summary Metric Cards */}
        {summary && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="p-4 rounded-xl bg-[#082746]/60 border border-[#164B68]">
              <div className="text-xs font-medium text-[#A9BBCD]">Total Open</div>
              <div className="mt-1 text-2xl font-bold text-white">{summary.total_open}</div>
              <div className="mt-1 text-[11px] text-[#A9BBCD]">{summary.high_severity} high priority</div>
            </div>

            <div className="p-4 rounded-xl bg-[#082746]/60 border border-[#164B68]">
              <div className="text-xs font-medium text-amber-400">Price Hikes</div>
              <div className="mt-1 text-2xl font-bold text-amber-300">{summary.price_increases}</div>
              <div className="mt-1 text-[11px] text-[#A9BBCD]">Sustained increases</div>
            </div>

            <div className="p-4 rounded-xl bg-[#082746]/60 border border-[#164B68]">
              <div className="text-xs font-medium text-sky-400">Trial Conversions</div>
              <div className="mt-1 text-2xl font-bold text-sky-300">{summary.trial_conversions}</div>
              <div className="mt-1 text-[11px] text-[#A9BBCD]">Free to paid transitions</div>
            </div>

            <div className="p-4 rounded-xl bg-[#082746]/60 border border-[#164B68]">
              <div className="text-xs font-medium text-indigo-400">Potentially Unused</div>
              <div className="mt-1 text-2xl font-bold text-indigo-300">{summary.potentially_unused}</div>
              <div className="mt-1 text-[11px] text-[#A9BBCD]">90+ days 0 activity</div>
            </div>

            <div className="p-4 rounded-xl bg-[#082746]/60 border border-[#164B68]">
              <div className="text-xs font-medium text-rose-400">Post-Cancellation</div>
              <div className="mt-1 text-2xl font-bold text-rose-300">{summary.post_cancellation_charges}</div>
              <div className="mt-1 text-[11px] text-[#A9BBCD]">Debited after cancel</div>
            </div>

            <div className="p-4 rounded-xl bg-[#082746]/60 border border-[#164B68]">
              <div className="text-xs font-medium text-emerald-400">Monthly Impact</div>
              <div className="mt-1 text-2xl font-bold text-emerald-300">
                ₹{Number(summary.estimated_monthly_impact).toLocaleString("en-IN", { minimumFractionDigits: 0 })}
              </div>
              <div className="mt-1 text-[11px] text-[#A9BBCD]">Recoverable / monthly</div>
            </div>
          </div>
        )}

        {/* Filter Navigation Tabs */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#164B68] pb-4">
          <div className="flex flex-wrap items-center gap-1.5">
            {[
              { id: "all", label: "All Insights" },
              { id: "price_increase", label: "Price Increases" },
              { id: "trial_conversion", label: "Trial Conversions" },
              { id: "potentially_unused", label: "Potentially Unused" },
              { id: "post_cancellation_charge", label: "Post-Cancellation" },
              { id: "unusual_amount", label: "Unusual Amounts" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                  activeTab === tab.id
                    ? "bg-indigo-600 text-white"
                    : "text-[#A9BBCD] hover:text-[#F4F7FB] hover:bg-[#082746]"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <input
              type="text"
              placeholder="Search anomalies..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="px-3 py-1.5 text-xs rounded-lg bg-[#082746] border border-[#164B68] text-[#F4F7FB] placeholder-[#A9BBCD]/60 focus:outline-none focus:border-indigo-500 w-44"
            />

            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="px-3 py-1.5 text-xs rounded-lg bg-[#082746] border border-[#164B68] text-[#F4F7FB] focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Severities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 text-xs rounded-lg bg-[#082746] border border-[#164B68] text-[#F4F7FB] focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="resolved">Resolved</option>
              <option value="dismissed">Dismissed</option>
            </select>
          </div>
        </div>

        {/* Insight Cards Grid */}
        {loading ? (
          <div className="p-12 text-center text-[#A9BBCD] text-sm">Loading intelligence insights...</div>
        ) : filteredInsights.length === 0 ? (
          <div className="p-12 text-center border border-dashed border-[#164B68] rounded-2xl bg-[#082746]/30">
            <h3 className="text-base font-semibold text-[#F4F7FB]">No Insights Match Filters</h3>
            <p className="mt-1 text-xs text-[#A9BBCD]">
              Run detection or adjust filter criteria to inspect subscription anomalies.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredInsights.map((ins) => (
              <div
                key={ins.id}
                className={`p-5 rounded-2xl bg-[#082746]/70 border transition-all flex flex-col justify-between gap-4 ${
                  ins.severity === "high"
                    ? "border-rose-500/30 hover:border-rose-500/50"
                    : ins.severity === "medium"
                    ? "border-amber-500/30 hover:border-amber-500/50"
                    : "border-[#164B68] hover:border-[#164B68]"
                }`}
              >
                <div className="flex flex-col gap-2.5">
                  {/* Card Header */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-semibold tracking-wider uppercase text-[#A9BBCD]">
                        {getTypeLabel(ins.insight_type)}
                      </span>
                      {getSeverityBadge(ins.severity)}
                      {getStatusBadge(ins.status)}
                    </div>
                    <span className="text-[11px] text-[#A9BBCD] font-mono">
                      {new Date(ins.detected_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
                    </span>
                  </div>

                  {/* Title & Commitment */}
                  <div>
                    <h3 className="text-base font-semibold text-white tracking-tight">{ins.title}</h3>
                    <div className="text-xs text-[#A9BBCD] flex items-center gap-2 mt-0.5">
                      <span className="text-emerald-400 font-medium">{ins.commitment_name}</span>
                      {ins.merchant_name && <span className="text-[#A9BBCD]">• {ins.merchant_name}</span>}
                    </div>
                  </div>

                  {/* Summary */}
                  <p className="text-xs text-[#F4F7FB] leading-relaxed">{ins.summary}</p>
                </div>

                {/* Footer Controls & Quick Actions */}
                <div className="pt-3 border-t border-[#164B68]/80 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 text-xs text-[#A9BBCD]">
                    <span className="px-2 py-0.5 rounded bg-[#0B3152] text-[11px] text-[#F4F7FB]">
                      {ins.evidence_count} evidence items
                    </span>
                    <span className="text-[11px] text-[#A9BBCD]">{ins.confidence_band} confidence</span>
                  </div>

                  <div className="flex items-center gap-2">
                    {ins.status === "open" && (
                      <>
                        <button
                          onClick={() => handleAcknowledge(ins.id)}
                          className="text-xs px-2.5 py-1 rounded-lg border border-[#164B68] bg-[#0B3152] text-[#F4F7FB] hover:text-white hover:bg-[#0B3152] transition-colors cursor-pointer"
                        >
                          Acknowledge
                        </button>
                        <button
                          onClick={() => handleDismiss(ins.id)}
                          className="text-xs px-2.5 py-1 rounded-lg border border-[#164B68] bg-[#082746] text-[#A9BBCD] hover:text-[#F4F7FB] transition-colors cursor-pointer"
                        >
                          Dismiss
                        </button>
                      </>
                    )}
                    <Link
                      href={`/insights/${ins.id}`}
                      className="text-xs px-3 py-1 rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/30 transition-colors font-medium"
                    >
                      Investigate &rarr;
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
