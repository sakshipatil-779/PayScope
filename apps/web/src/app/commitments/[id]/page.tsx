"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";

import AppHeader from "@/components/navigation/AppHeader";

interface TransactionEvidence {
  id: string;
  transaction_id: string;
  relationship_role: string;
  match_confidence?: number | null;
  reason?: string | null;
  transaction_date: string;
  raw_descriptor: string;
  normalised_descriptor?: string | null;
  amount: number | string;
  currency: string;
  payment_channel: string;
  payment_reference?: string | null;
}

interface TimelineEvent {
  event_id: string;
  event_date: string;
  event_type: string;
  title: string;
  description: string;
  amount?: number | string | null;
  currency?: string | null;
  payment_channel?: string | null;
  payment_reference?: string | null;
  metadata?: Record<string, unknown> | null;
}

interface CommitmentInsightItem {
  id: string;
  insight_type: string;
  severity: string;
  status: string;
  title: string;
  summary: string;
  confidence_band: string;
  confidence_score?: number | string | null;
  detected_at: string;
  evidence_count: number;
}

interface CommitmentDetail {
  id: string;
  user_id: string;
  merchant_id?: string | null;
  display_name: string;
  commitment_type: string;
  cadence: string;
  amount_pattern: string;
  status: string;
  currency: string;
  representative_amount?: number | string | null;
  amount_min?: number | string | null;
  amount_max?: number | string | null;
  first_seen_at: string;
  last_seen_at: string;
  next_expected_date?: string | null;
  annualised_amount?: number | string | null;
  annualisation_method?: string | null;
  confidence_score?: number | string | null;
  confidence_band: string;
  detection_reason_codes?: string[] | null;
  detection_explanation?: string | null;
  detector_version: string;
  user_decision?: string | null;
  user_decision_at?: string | null;
  transaction_count: number;
  created_at: string;
  updated_at: string;
  supporting_transactions: TransactionEvidence[];
}

export default function CommitmentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const commitmentId = resolvedParams.id;

  const [commitment, setCommitment] = useState<CommitmentDetail | null>(null);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [insights, setInsights] = useState<CommitmentInsightItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<"transactions" | "timeline" | "insights">("transactions");
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Edit modal / form state
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editDisplayName, setEditDisplayName] = useState<string>("");
  const [editType, setEditType] = useState<string>("subscription");
  const [editCadence, setEditCadence] = useState<string>("monthly");
  const [savingEdit, setSavingEdit] = useState<boolean>(false);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  useEffect(() => {
    let ignore = false;
    async function loadDetail() {
      try {
        const [detRes, timeRes, insRes] = await Promise.all([
          fetch(`${apiBase}/api/v1/commitments/${commitmentId}`),
          fetch(`${apiBase}/api/v1/commitments/${commitmentId}/timeline`),
          fetch(`${apiBase}/api/v1/commitments/${commitmentId}/insights`),
        ]);

        if (!detRes.ok) {
          throw new Error(`Failed to load commitment (${detRes.status})`);
        }

        const detData = await detRes.json();
        const timeData = timeRes.ok ? await timeRes.json() : { events: [] };
        const insData = insRes.ok ? await insRes.json() : [];

        if (!ignore) {
          setCommitment(detData);
          setTimelineEvents(timeData.events || []);
          setInsights(insData || []);
          setEditDisplayName(detData.display_name);
          setEditType(detData.commitment_type);
          setEditCadence(detData.cadence);
        }
      } catch (err) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Error loading commitment");
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
  }, [apiBase, commitmentId]);

  const refreshData = async () => {
    try {
      const [detRes, timeRes, insRes] = await Promise.all([
        fetch(`${apiBase}/api/v1/commitments/${commitmentId}`),
        fetch(`${apiBase}/api/v1/commitments/${commitmentId}/timeline`),
        fetch(`${apiBase}/api/v1/commitments/${commitmentId}/insights`),
      ]);
      if (detRes.ok) {
        const detData = await detRes.json();
        setCommitment(detData);
        setEditDisplayName(detData.display_name);
        setEditType(detData.commitment_type);
        setEditCadence(detData.cadence);
      }
      if (timeRes.ok) {
        const timeData = await timeRes.json();
        setTimelineEvents(timeData.events || []);
      }
      if (insRes.ok) {
        const insData = await insRes.json();
        setInsights(insData || []);
      }
    } catch {
      // Ignore background refresh errors
    }
  };

  const handleConfirm = async () => {
    try {
      const res = await fetch(`${apiBase}/api/v1/commitments/${commitmentId}/confirm`, {
        method: "POST",
      });
      if (res.ok) {
        setActionSuccess("Commitment confirmed as recurring obligation.");
        await refreshData();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to confirm");
    }
  };

  const handleMarkNotRecurring = async () => {
    try {
      const res = await fetch(`${apiBase}/api/v1/commitments/${commitmentId}/mark-not-recurring`, {
        method: "POST",
      });
      if (res.ok) {
        setActionSuccess("Commitment marked as not recurring.");
        await refreshData();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to mark not recurring");
    }
  };

  const handleSaveCorrection = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingEdit(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/commitments/${commitmentId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          display_name: editDisplayName,
          commitment_type: editType,
          cadence: editCadence,
        }),
      });
      if (res.ok) {
        setActionSuccess("Commitment details corrected successfully.");
        setIsEditing(false);
        await refreshData();
      } else {
        setError("Failed to save correction.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Network error");
    } finally {
      setSavingEdit(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#011633] text-[#A9BBCD]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-medium">Loading recurring commitment...</span>
        </div>
      </div>
    );
  }

  if (error || !commitment) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#011633] text-[#F4F7FB] p-4">
        <div className="max-w-md w-full p-6 rounded-2xl bg-[#082746] border border-[#164B68] text-center flex flex-col gap-4">
          <div className="w-12 h-12 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center mx-auto text-xl font-bold">
            !
          </div>
          <h2 className="text-xl font-bold">Commitment Not Found</h2>
          <p className="text-xs text-[#A9BBCD]">{error || "Could not locate this recurring obligation."}</p>
          <Link
            href="/commitments"
            className="mt-2 inline-flex items-center justify-center px-4 py-2 rounded-xl text-xs font-semibold bg-[#0B3152] hover:bg-[#0B3152] text-white transition-colors"
          >
            ← Back to All Commitments
          </Link>
        </div>
      </div>
    );
  }

  const openInsights = insights.filter((i) => i.status === "open");

  return (
    <div className="min-h-screen flex flex-col bg-[#011633] text-[#F4F7FB] antialiased selection:bg-[#F08A00] selection:text-white">
      {/* Top Header */}
      <AppHeader />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
        {/* Notification Banner */}
        {actionSuccess && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex items-center justify-between">
            <span>{actionSuccess}</span>
            <button
              onClick={() => setActionSuccess(null)}
              className="text-emerald-400 hover:text-emerald-200 text-xs font-medium cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Anomaly / Insight Alert Banner */}
        {openInsights.length > 0 && (
          <div className="p-5 rounded-2xl bg-gradient-to-r from-amber-500/10 via-rose-500/10 to-slate-900 border border-amber-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-300 text-lg font-bold shrink-0">
                ⚠
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">
                  {openInsights[0].title}
                </h3>
                <p className="text-xs text-[#A9BBCD] mt-0.5">
                  {openInsights[0].summary}
                </p>
              </div>
            </div>
            <Link
              href={`/insights/${openInsights[0].id}`}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 transition-colors shrink-0 self-start sm:self-auto"
            >
              Investigate Anomaly &rarr;
            </Link>
          </div>
        )}

        {/* Commitment Header */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 p-6 rounded-2xl bg-[#082746]/60 border border-[#164B68]/80">
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                {commitment.display_name}
              </h1>
              {/* Status Badge */}
              <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                {commitment.user_decision ? commitment.user_decision.replace("_", " ") : commitment.status.replace("_", " ")}
              </span>
              {/* Confidence Badge */}
              <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                {commitment.confidence_band} Confidence ({commitment.confidence_score}%)
              </span>
            </div>

            <p className="text-sm text-[#A9BBCD] flex items-center gap-2">
              <span className="capitalize">{commitment.commitment_type.replace("_", " ")}</span>
              <span>•</span>
              <span className="capitalize">{commitment.cadence.replace("_", " ")}</span>
              <span>•</span>
              <span>Observed across {commitment.supporting_transactions.length} debits</span>
              {commitment.merchant_id && (
                <>
                  <span>•</span>
                  <Link
                    href={`/merchants/${commitment.merchant_id}`}
                    className="text-emerald-400 hover:underline text-xs"
                  >
                    View Canonical Merchant →
                  </Link>
                </>
              )}
            </p>
          </div>

          {/* User Review Action Buttons */}
          <div className="flex flex-wrap items-center gap-2.5">
            {commitment.user_decision !== "confirmed" && (
              <button
                onClick={handleConfirm}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors cursor-pointer shadow-sm shadow-emerald-600/20"
              >
                Confirm Recurring
              </button>
            )}
            {commitment.user_decision !== "not_recurring" && (
              <button
                onClick={handleMarkNotRecurring}
                className="px-4 py-2 rounded-xl text-xs font-medium bg-[#0B3152] hover:bg-[#0B3152] text-[#F4F7FB] transition-colors cursor-pointer border border-[#164B68]"
              >
                Mark Not Recurring
              </button>
            )}
            <Link
              href={`/cancellations?commitment_id=${commitment.id}`}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#F08A00]/20 hover:bg-[#F08A00]/30 text-[#FFA52B] border border-[#F08A00]/40 transition-colors cursor-pointer flex items-center gap-1.5"
            >
              <span>View cancellation guidance →</span>
            </Link>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="px-3 py-2 rounded-xl text-xs font-medium bg-[#082746] hover:bg-[#0B3152] text-[#A9BBCD] hover:text-[#F4F7FB] transition-colors border border-[#164B68] cursor-pointer"
            >
              {isEditing ? "Close Correction" : "Correct Details"}
            </button>
          </div>
        </div>

        {/* Correction Form Dropdown */}
        {isEditing && (
          <form
            onSubmit={handleSaveCorrection}
            className="p-6 rounded-2xl bg-[#082746] border border-emerald-500/30 flex flex-col gap-4 animate-in fade-in duration-200"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white">Correct Commitment Intelligence Metadata</h3>
              <span className="text-xs text-[#A9BBCD]">Overrides detector classification</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-[#A9BBCD] mb-1.5">Display Name</label>
                <input
                  type="text"
                  value={editDisplayName}
                  onChange={(e) => setEditDisplayName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-[#011633] border border-[#164B68] text-sm text-white focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-[#A9BBCD] mb-1.5">Commitment Type</label>
                <select
                  value={editType}
                  onChange={(e) => setEditType(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-[#011633] border border-[#164B68] text-sm text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="subscription">Subscription</option>
                  <option value="utility">Utility</option>
                  <option value="loan_emi">Loan EMI</option>
                  <option value="insurance">Insurance</option>
                  <option value="membership">Membership</option>
                  <option value="other_recurring">Other Recurring</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-[#A9BBCD] mb-1.5">Cadence Schedule</label>
                <select
                  value={editCadence}
                  onChange={(e) => setEditCadence(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-[#011633] border border-[#164B68] text-sm text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                  <option value="annual">Annual</option>
                  <option value="weekly">Weekly</option>
                  <option value="fortnightly">Fortnightly</option>
                  <option value="variable_monthly">Variable Monthly</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 rounded-xl text-xs font-medium text-[#A9BBCD] hover:text-[#F4F7FB]"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={savingEdit}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors cursor-pointer"
              >
                {savingEdit ? "Saving..." : "Save Correction"}
              </button>
            </div>
          </form>
        )}

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-[#082746]/60 border border-[#164B68]/80">
            <div className="text-xs font-medium text-[#A9BBCD]">Representative Amount</div>
            <div className="mt-2 text-2xl font-bold tracking-tight text-white">
              ₹{Number(commitment.representative_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <div className="mt-1 text-xs text-[#A9BBCD]">
              Pattern: <span className="capitalize">{commitment.amount_pattern}</span>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-[#082746]/60 border border-[#164B68]/80">
            <div className="text-xs font-medium text-[#A9BBCD]">Annualised Impact</div>
            <div className="mt-2 text-2xl font-bold tracking-tight text-emerald-400">
              ₹{Number(commitment.annualised_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <div className="mt-1 text-xs text-[#A9BBCD]">
              Method: {commitment.annualisation_method ? commitment.annualisation_method.replace("_", " ") : "standard"}
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-[#082746]/60 border border-[#164B68]/80">
            <div className="text-xs font-medium text-[#A9BBCD]">Observed Range</div>
            <div className="mt-2 text-2xl font-bold tracking-tight text-[#F4F7FB]">
              ₹{Number(commitment.amount_min || commitment.representative_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 0 })}
              {" – "}
              ₹{Number(commitment.amount_max || commitment.representative_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 0 })}
            </div>
            <div className="mt-1 text-xs text-[#A9BBCD]">Historical Min / Max</div>
          </div>

          <div className="p-5 rounded-2xl bg-[#082746]/60 border border-[#164B68]/80">
            <div className="text-xs font-medium text-[#A9BBCD]">Next Expected Debit</div>
            <div className="mt-2 text-2xl font-bold tracking-tight text-sky-400">
              {commitment.next_expected_date ? (
                new Date(commitment.next_expected_date).toLocaleDateString("en-IN", {
                  day: "numeric",
                  month: "short",
                  year: "numeric",
                })
              ) : (
                "Not Projected"
              )}
            </div>
            <div className="mt-1 text-xs text-[#A9BBCD]">Estimated renewal date</div>
          </div>
        </div>

        {/* Discovery Engine Explanation Panel */}
        <div className="p-6 rounded-2xl bg-[#082746]/40 border border-[#164B68]/80 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <span>Why PayScope Flagged This as Recurring</span>
            </h3>
            <span className="text-xs text-[#A9BBCD] font-mono">
              First Seen: {new Date(commitment.first_seen_at).toLocaleDateString("en-IN", { month: "short", year: "numeric" })} • Last Seen: {new Date(commitment.last_seen_at).toLocaleDateString("en-IN", { month: "short", year: "numeric" })}
            </span>
          </div>

          <p className="text-xs leading-relaxed text-[#F4F7FB] bg-[#011633]/50 p-4 rounded-xl border border-[#164B68]/60">
            {commitment.detection_explanation || "Recurring obligation identified based on cadence interval consistency and transaction matching."}
          </p>

          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-[11px] text-[#A9BBCD]">Reason Codes:</span>
            {commitment.detection_reason_codes && commitment.detection_reason_codes.length > 0 ? (
              commitment.detection_reason_codes.map((code) => (
                <span key={code} className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#0B3152] text-[#A9BBCD] border border-[#164B68]">
                  {code}
                </span>
              ))
            ) : (
              <span className="text-[10px] text-[#164B68] font-mono">CADENCE_MATCH</span>
            )}
            <span className="ml-auto text-[11px] text-[#A9BBCD] font-mono">
              Engine {commitment.detector_version}
            </span>
          </div>
        </div>

        {/* Tab Controls for Supporting Evidence */}
        <div className="flex items-center gap-4 border-b border-[#164B68]">
          <button
            onClick={() => setActiveTab("transactions")}
            className={`pb-3 text-sm font-medium transition-colors border-b-2 cursor-pointer ${
              activeTab === "transactions"
                ? "border-emerald-400 text-white"
                : "border-transparent text-[#A9BBCD] hover:text-[#F4F7FB]"
            }`}
          >
            Supporting Transactions ({commitment.supporting_transactions.length})
          </button>
          <button
            onClick={() => setActiveTab("timeline")}
            className={`pb-3 text-sm font-medium transition-colors border-b-2 cursor-pointer ${
              activeTab === "timeline"
                ? "border-emerald-400 text-white"
                : "border-transparent text-[#A9BBCD] hover:text-[#F4F7FB]"
            }`}
          >
            Chronological Timeline ({timelineEvents.length})
          </button>
          <button
            onClick={() => setActiveTab("insights")}
            className={`pb-3 text-sm font-medium transition-colors border-b-2 cursor-pointer flex items-center gap-2 ${
              activeTab === "insights"
                ? "border-emerald-400 text-white"
                : "border-transparent text-[#A9BBCD] hover:text-[#F4F7FB]"
            }`}
          >
            <span>Insights & Anomalies</span>
            {insights.length > 0 && (
              <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                openInsights.length > 0 ? "bg-rose-500/20 text-rose-300" : "bg-[#0B3152] text-[#A9BBCD]"
              }`}>
                {insights.length}
              </span>
            )}
          </button>
        </div>

        {/* Tab 1: Supporting Transactions Table */}
        {activeTab === "transactions" && (
          <div className="rounded-xl border border-[#164B68] bg-[#082746]/50 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#164B68] bg-[#082746]/80 text-[#A9BBCD] font-medium">
                    <th className="py-3 px-4">Date</th>
                    <th className="py-3 px-4">Raw Descriptor</th>
                    <th className="py-3 px-4">Amount</th>
                    <th className="py-3 px-4">Channel</th>
                    <th className="py-3 px-4">Reference</th>
                    <th className="py-3 px-4">Evidence Role</th>
                    <th className="py-3 px-4">Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#164B68]/60 font-mono">
                  {commitment.supporting_transactions.map((tx) => (
                    <tr key={tx.id} className="hover:bg-[#0B3152]/30 transition-colors">
                      <td className="py-3 px-4 text-[#F4F7FB] font-sans">
                        {new Date(tx.transaction_date).toLocaleDateString("en-IN", {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        })}
                      </td>
                      <td className="py-3 px-4 text-[#F4F7FB] font-sans font-medium">
                        {tx.raw_descriptor}
                      </td>
                      <td className="py-3 px-4 font-bold text-white">
                        ₹{Number(tx.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-[#A9BBCD] font-sans uppercase text-[11px]">
                        {tx.payment_channel}
                      </td>
                      <td className="py-3 px-4 text-[#A9BBCD] text-[11px]">
                        {tx.payment_reference || "—"}
                      </td>
                      <td className="py-3 px-4 font-sans">
                        <span className="px-2 py-0.5 rounded bg-[#0B3152] text-[#F4F7FB] border border-[#164B68] text-[11px]">
                          {tx.relationship_role.replace("_", " ")}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-[#A9BBCD] font-sans text-[11px]">
                        {tx.reason || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 2: Chronological Timeline View */}
        {activeTab === "timeline" && (
          <div className="rounded-2xl border border-[#164B68] bg-[#082746]/40 p-6">
            {timelineEvents.length === 0 ? (
              <div className="py-8 text-center text-[#A9BBCD] text-xs">
                No chronological events recorded yet for this commitment.
              </div>
            ) : (
              <div className="relative pl-6 space-y-8 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#0B3152]">
                {timelineEvents.map((evt) => {
                  let dotColor = "bg-emerald-500";
                  if (evt.event_type === "notification") dotColor = "bg-sky-500";
                  if (evt.event_type === "user_decision") dotColor = "bg-indigo-500";
                  if (evt.event_type === "amount_change") dotColor = "bg-amber-500";

                  return (
                    <div key={evt.event_id} className="relative group">
                      <div
                        className={`absolute -left-[27px] top-1 w-3.5 h-3.5 rounded-full border-2 border-slate-950 ${dotColor} shadow-sm`}
                      />
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-white">{evt.title}</span>
                          <span className="px-1.5 py-0.5 text-[10px] font-mono uppercase rounded bg-[#0B3152] text-[#A9BBCD]">
                            {evt.event_type}
                          </span>
                        </div>
                        <span className="text-[11px] font-mono text-[#A9BBCD]">
                          {new Date(evt.event_date).toLocaleDateString("en-IN", {
                            day: "numeric",
                            month: "short",
                            year: "numeric",
                          })}
                        </span>
                      </div>
                      <p className="text-xs text-[#F4F7FB] mt-1 leading-relaxed">{evt.description}</p>
                      {evt.amount && (
                        <div className="mt-2 text-xs font-mono font-medium text-emerald-400">
                          ₹{Number(evt.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                          {evt.payment_channel && (
                            <span className="text-[#A9BBCD] ml-2 uppercase font-sans text-[11px]">
                              via {evt.payment_channel}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Insights & Anomalies Tab */}
        {activeTab === "insights" && (
          <div className="flex flex-col gap-4">
            {insights.length === 0 ? (
              <div className="p-8 text-center rounded-2xl border border-dashed border-[#164B68] bg-[#082746]/30 text-xs text-[#A9BBCD]">
                No anomalies or intelligence insights detected for this commitment.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {insights.map((ins) => (
                  <div
                    key={ins.id}
                    className={`p-5 rounded-2xl bg-[#082746]/70 border flex flex-col justify-between gap-3 ${
                      ins.severity === "high" ? "border-rose-500/30" :
                      ins.severity === "medium" ? "border-amber-500/30" :
                      "border-[#164B68]"
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[11px] uppercase font-semibold text-[#A9BBCD]">
                          {ins.insight_type.replace("_", " ")}
                        </span>
                        <span className="text-[11px] font-mono text-[#A9BBCD]">
                          {new Date(ins.detected_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
                        </span>
                      </div>
                      <h4 className="text-sm font-semibold text-white mt-1">{ins.title}</h4>
                      <p className="text-xs text-[#F4F7FB] mt-1">{ins.summary}</p>
                    </div>

                    <div className="pt-3 border-t border-[#164B68]/80 flex items-center justify-between">
                      <span className="text-[11px] text-[#A9BBCD]">{ins.confidence_band} confidence</span>
                      <Link
                        href={`/insights/${ins.id}`}
                        className="text-xs px-3 py-1 rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/30 transition-colors font-medium"
                      >
                        Deep Dive &rarr;
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
