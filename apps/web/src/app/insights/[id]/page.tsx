"use client";

import { getApiBaseUrl } from "@/lib/api";
import React, { useState, useEffect, use } from "react";
import Link from "next/link";

import AppHeader from "@/components/navigation/AppHeader";

interface EvidenceItem {
  id: string;
  insight_id: string;
  evidence_type: string;
  role: string;
  weight?: number | null;
  summary: string;
  timestamp?: string | null;
  transaction_id?: string | null;
  notification_id?: string | null;
  usage_coverage_id?: string | null;
  usage_event_id?: string | null;
  cancellation_event_id?: string | null;
  created_at: string;
}

interface PriceEvent {
  id: string;
  commitment_id: string;
  event_type: string;
  previous_amount: number | string;
  new_amount: number | string;
  currency: string;
  absolute_change: number | string;
  percentage_change: number | string;
  effective_or_detected_at: string;
  confidence_band: string;
  explanation?: string | null;
  detector_version: string;
  created_at: string;
}

interface InsightDetail {
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
  commitment_representative_amount?: number | string | null;
  commitment_cadence?: string | null;
  price_event?: PriceEvent | null;
  evidence_items: EvidenceItem[];
  created_at: string;
  updated_at: string;
}

export default function InsightDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const insightId = resolvedParams.id;

  const [insight, setInsight] = useState<InsightDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Review action inputs
  const [reviewNote, setReviewNote] = useState<string>("");
  const [dismissReason, setDismissReason] = useState<string>("Intended to continue paid tier");
  const [actionSubmitting, setActionSubmitting] = useState<boolean>(false);

  const apiBase = getApiBaseUrl();

  const refreshDetail = async () => {
    try {
      const res = await fetch(`${apiBase}/api/v1/insights/${insightId}`);
      if (res.ok) {
        const data = await res.json();
        setInsight(data);
      }
    } catch {
      // Ignored
    }
  };

  useEffect(() => {
    let ignore = false;
    async function loadDetail() {
      try {
        const res = await fetch(`${apiBase}/api/v1/insights/${insightId}`);
        if (!ignore && res.ok) {
          const data = await res.json();
          setInsight(data);
        } else if (!ignore) {
          setError(`Failed to retrieve insight (HTTP ${res.status})`);
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

    loadDetail();
    return () => {
      ignore = true;
    };
  }, [apiBase, insightId]);

  const handleAcknowledge = async () => {
    setActionSubmitting(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/insights/${insightId}/acknowledge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: reviewNote || "Acknowledged by user" }),
      });
      if (res.ok) {
        setActionSuccess("Insight acknowledged.");
        refreshDetail();
      }
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleDismiss = async () => {
    setActionSubmitting(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/insights/${insightId}/dismiss`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: dismissReason, notes: reviewNote }),
      });
      if (res.ok) {
        setActionSuccess("Insight dismissed.");
        refreshDetail();
      }
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleResolve = async () => {
    setActionSubmitting(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/insights/${insightId}/resolve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resolution_action: "Action taken with merchant", notes: reviewNote }),
      });
      if (res.ok) {
        setActionSuccess("Insight marked as resolved.");
        refreshDetail();
      }
    } finally {
      setActionSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#011633] text-[#A9BBCD] text-sm">
        Loading anomaly deep-dive...
      </div>
    );
  }

  if (error || !insight) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#011633] text-[#F4F7FB] p-6 gap-4">
        <h2 className="text-xl font-bold text-rose-400">Insight Not Found</h2>
        <p className="text-sm text-[#A9BBCD]">{error || "Requested insight does not exist."}</p>
        <Link href="/insights" className="px-4 py-2 bg-[#0B3152] text-white rounded-lg text-sm hover:bg-[#0B3152]">
          &larr; Back to Insights
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#011633] text-[#F4F7FB] antialiased selection:bg-[#F08A00] selection:text-white">
      {/* Top Header */}
      <AppHeader />

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
        {/* Banner Alert */}
        {actionSuccess && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex items-center justify-between">
            <span>{actionSuccess}</span>
            <button onClick={() => setActionSuccess(null)} className="text-emerald-400 hover:text-emerald-200 text-xs font-medium cursor-pointer">
              Dismiss
            </button>
          </div>
        )}

        {/* Insight Header Card */}
        <div className="p-6 rounded-2xl bg-[#082746]/70 border border-[#164B68] flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs font-semibold tracking-wider uppercase px-2.5 py-0.5 rounded-full bg-[#0B3152] text-[#F4F7FB] border border-[#164B68]">
                {insight.insight_type.replace("_", " ").toUpperCase()}
              </span>
              <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                insight.severity === "high" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" :
                insight.severity === "medium" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
                "bg-sky-500/10 text-sky-400 border border-sky-500/20"
              }`}>
                {insight.severity.toUpperCase()} SEVERITY
              </span>
              <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${
                insight.status === "open" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" :
                insight.status === "acknowledged" ? "bg-sky-500/10 text-sky-400 border border-sky-500/20" :
                insight.status === "resolved" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                "bg-[#0B3152] text-[#A9BBCD] border border-[#164B68]"
              }`}>
                {insight.status.toUpperCase()}
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mt-1">
              {insight.title}
            </h1>

            <div className="text-xs text-[#A9BBCD] flex items-center gap-2">
              <span className="text-emerald-400 font-medium">{insight.commitment_name}</span>
              {insight.merchant_name && <span className="text-[#A9BBCD]">• {insight.merchant_name}</span>}
              <span className="text-[#A9BBCD]">• Detected on {new Date(insight.detected_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row md:flex-col gap-2 shrink-0">
            <div className="p-3 rounded-xl bg-[#011633]/60 border border-[#164B68] text-right">
              <div className="text-[11px] text-[#A9BBCD]">Detector Version</div>
              <div className="text-xs font-mono font-medium text-[#F4F7FB]">{insight.detector_version}</div>
            </div>
            <div className="p-3 rounded-xl bg-[#011633]/60 border border-[#164B68] text-right">
              <div className="text-[11px] text-[#A9BBCD]">Confidence Band</div>
              <div className="text-xs font-medium text-emerald-400">{insight.confidence_band.toUpperCase()} ({insight.confidence_score}%)</div>
            </div>
          </div>
        </div>

        {/* Deep Explanation Card */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 p-6 rounded-2xl bg-[#082746]/60 border border-[#164B68] flex flex-col gap-4">
            <h2 className="text-base font-semibold text-white">Algorithmic Rationale & Explanation</h2>
            <div className="p-4 rounded-xl bg-[#011633]/60 border border-[#164B68] text-[#F4F7FB] text-sm leading-relaxed whitespace-pre-line">
              {insight.explanation || insight.summary}
            </div>

            {/* Price Event Details If Available */}
            {insight.price_event && (
              <div className="mt-2 p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 flex flex-col gap-3">
                <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
                  Structured Price Regime Transition
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                  <div>
                    <div className="text-[#A9BBCD]">Previous Regime</div>
                    <div className="text-sm font-semibold text-white mt-0.5">₹{insight.price_event.previous_amount}</div>
                  </div>
                  <div>
                    <div className="text-[#A9BBCD]">New Regime</div>
                    <div className="text-sm font-semibold text-amber-300 mt-0.5">₹{insight.price_event.new_amount}</div>
                  </div>
                  <div>
                    <div className="text-[#A9BBCD]">Change</div>
                    <div className="text-sm font-semibold text-rose-400 mt-0.5">
                      +₹{insight.price_event.absolute_change} (+{Number(insight.price_event.percentage_change).toFixed(1)}%)
                    </div>
                  </div>
                  <div>
                    <div className="text-[#A9BBCD]">Effective Date</div>
                    <div className="text-sm font-semibold text-white mt-0.5">
                      {new Date(insight.price_event.effective_or_detected_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* User Review Action Panel */}
          <div className="p-6 rounded-2xl bg-[#082746]/60 border border-[#164B68] flex flex-col justify-between gap-6">
            <div className="flex flex-col gap-4">
              <h2 className="text-base font-semibold text-white">Review & Actions</h2>
              <p className="text-xs text-[#A9BBCD]">
                Record your decision to either acknowledge this change, dismiss it as expected, or resolve it after contacting the provider.
              </p>

              <div className="flex flex-col gap-2">
                <label className="text-xs text-[#A9BBCD]">Add User Notes (Optional)</label>
                <textarea
                  value={reviewNote}
                  onChange={(e) => setReviewNote(e.target.value)}
                  placeholder="e.g. Plan upgrade accepted on call..."
                  rows={2}
                  className="px-3 py-2 text-xs rounded-lg bg-[#011633] border border-[#164B68] text-[#F4F7FB] placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
              </div>

              {insight.status === "open" && (
                <div className="flex flex-col gap-2">
                  <label className="text-xs text-[#A9BBCD]">Dismiss Reason (if dismissing)</label>
                  <select
                    value={dismissReason}
                    onChange={(e) => setDismissReason(e.target.value)}
                    className="px-3 py-2 text-xs rounded-lg bg-[#011633] border border-[#164B68] text-[#F4F7FB] focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Intended to continue paid tier">Intended to continue paid tier</option>
                    <option value="Agreed with price increase">Agreed with price increase</option>
                    <option value="Still actively using facility/service">Still actively using facility/service</option>
                    <option value="Re-subscribed after cancellation">Re-subscribed after cancellation</option>
                    <option value="Other / Not an issue">Other / Not an issue</option>
                  </select>
                </div>
              )}
            </div>

            <div className="flex flex-col gap-2 pt-4 border-t border-[#164B68]">
              {insight.status === "open" ? (
                <>
                  <button
                    onClick={handleAcknowledge}
                    disabled={actionSubmitting}
                    className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition-colors cursor-pointer"
                  >
                    Acknowledge Anomaly
                  </button>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={handleResolve}
                      disabled={actionSubmitting}
                      className="py-2 px-3 rounded-xl text-xs font-medium text-emerald-300 bg-emerald-500/10 border border-emerald-500/30 hover:bg-emerald-500/20 disabled:opacity-50 transition-colors cursor-pointer"
                    >
                      Mark Resolved
                    </button>
                    <button
                      onClick={handleDismiss}
                      disabled={actionSubmitting}
                      className="py-2 px-3 rounded-xl text-xs font-medium text-[#A9BBCD] bg-[#0B3152] border border-[#164B68] hover:text-white disabled:opacity-50 transition-colors cursor-pointer"
                    >
                      Dismiss
                    </button>
                  </div>
                </>
              ) : (
                <div className="p-3 rounded-xl bg-[#011633] border border-[#164B68] text-xs text-[#A9BBCD] text-center">
                  Insight status is <span className="text-white font-medium">{insight.status.toUpperCase()}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Supporting Evidence Ledger */}
        <div className="p-6 rounded-2xl bg-[#082746]/60 border border-[#164B68] flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              Supporting Evidence Ledger
              <span className="px-2 py-0.5 rounded-full text-xs font-normal bg-[#0B3152] text-[#A9BBCD]">
                {insight.evidence_items.length} records
              </span>
            </h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-[#164B68] text-[#A9BBCD] uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="pb-3 font-semibold">Evidence Role</th>
                  <th className="pb-3 font-semibold">Type</th>
                  <th className="pb-3 font-semibold">Timestamp</th>
                  <th className="pb-3 font-semibold">Summary & Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#164B68]/60 text-[#F4F7FB]">
                {insight.evidence_items.map((ev) => (
                  <tr key={ev.id} className="hover:bg-[#0B3152]/20">
                    <td className="py-3 font-mono text-[11px] text-indigo-400 font-medium">
                      {ev.role}
                    </td>
                    <td className="py-3">
                      <span className="px-2 py-0.5 rounded bg-[#0B3152] text-[#A9BBCD] text-[11px]">
                        {ev.evidence_type}
                      </span>
                    </td>
                    <td className="py-3 text-[#A9BBCD] font-mono text-[11px]">
                      {ev.timestamp
                        ? new Date(ev.timestamp).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })
                        : "—"}
                    </td>
                    <td className="py-3 text-[#F4F7FB]">
                      {ev.summary}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
