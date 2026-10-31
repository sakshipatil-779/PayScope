"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";

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
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<"transactions" | "timeline">("transactions");
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
        const [detRes, timeRes] = await Promise.all([
          fetch(`${apiBase}/api/v1/commitments/${commitmentId}`),
          fetch(`${apiBase}/api/v1/commitments/${commitmentId}/timeline`),
        ]);

        if (!detRes.ok) {
          throw new Error(`Failed to load commitment (${detRes.status})`);
        }

        const detData = await detRes.json();
        const timeData = timeRes.ok ? await timeRes.json() : { events: [] };

        if (!ignore) {
          setCommitment(detData);
          setTimelineEvents(timeData.events || []);
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
      const [detRes, timeRes] = await Promise.all([
        fetch(`${apiBase}/api/v1/commitments/${commitmentId}`),
        fetch(`${apiBase}/api/v1/commitments/${commitmentId}/timeline`),
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
    setError(null);
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
        setIsEditing(false);
        setActionSuccess("Commitment details updated and recorded.");
        await refreshData();
      } else {
        const data = await res.json();
        setError(data.detail || "Update failed");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Network error");
    } finally {
      setSavingEdit(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="text-slate-400">Loading commitment details...</div>
      </div>
    );
  }

  if (error || !commitment) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center gap-4">
        <div className="text-rose-400">{error || "Commitment not found"}</div>
        <Link
          href="/commitments"
          className="px-4 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-white"
        >
          Return to Commitments
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 antialiased selection:bg-emerald-500 selection:text-slate-950">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center font-bold text-emerald-400 text-lg shadow-sm group-hover:border-emerald-500 transition-colors">
                M
              </div>
              <span className="font-semibold text-lg tracking-tight text-white flex items-center gap-2">
                Mandate<span className="text-emerald-400">Lens</span>
              </span>
            </Link>
            <span className="text-slate-600">/</span>
            <Link href="/commitments" className="text-sm font-medium text-slate-400 hover:text-slate-200">
              Commitments
            </Link>
            <span className="text-slate-600">/</span>
            <span className="text-sm font-medium text-slate-300 truncate max-w-xs">{commitment.display_name}</span>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/commitments"
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-colors"
            >
              All Commitments
            </Link>
            <Link
              href="/merchants"
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-colors"
            >
              Merchants
            </Link>
          </div>
        </div>
      </header>

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

        {/* Commitment Header */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80">
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

            <p className="text-sm text-slate-400 flex items-center gap-2">
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

          {/* User Decision Controls */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => setIsEditing(true)}
              className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors cursor-pointer"
            >
              Edit Details
            </button>
            {commitment.user_decision !== "confirmed" && (
              <button
                onClick={handleConfirm}
                className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-sm transition-all cursor-pointer"
              >
                Confirm Commitment
              </button>
            )}
            {commitment.user_decision !== "not_recurring" && (
              <button
                onClick={handleMarkNotRecurring}
                className="px-3.5 py-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-medium transition-colors cursor-pointer"
              >
                Mark Not Recurring
              </button>
            )}
          </div>
        </div>

        {/* User Decision Status Callout */}
        {commitment.user_decision && (
          <div className="p-4 rounded-xl bg-slate-900 border border-emerald-500/20 flex items-center gap-3 text-xs text-slate-300">
            <svg className="w-5 h-5 text-emerald-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>
              User marked decision as <strong className="text-white uppercase">{commitment.user_decision.replace("_", " ")}</strong> on{" "}
              {new Date(commitment.user_decision_at || commitment.updated_at).toLocaleDateString("en-IN", {
                month: "short",
                day: "numeric",
                year: "numeric",
              })}
              . This decision is permanently protected against algorithmic reprocessing.
            </span>
          </div>
        )}

        {/* Statistical Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
            <span className="text-xs text-slate-400 font-medium">Representative Amount</span>
            <div className="text-xl font-bold font-mono text-white mt-1">
              ₹{Number(commitment.representative_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <span className="text-[11px] text-slate-500 capitalize">{commitment.amount_pattern} pattern</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
            <span className="text-xs text-slate-400 font-medium">Amount Range</span>
            <div className="text-base font-semibold font-mono text-slate-200 mt-1">
              ₹{Number(commitment.amount_min || 0).toLocaleString("en-IN")} – ₹{Number(commitment.amount_max || 0).toLocaleString("en-IN")}
            </div>
            <span className="text-[11px] text-slate-500">Min to max observed</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
            <span className="text-xs text-slate-400 font-medium">Cadence</span>
            <div className="text-base font-bold text-white capitalize mt-1">
              {commitment.cadence.replace("_", " ")}
            </div>
            <span className="text-[11px] text-slate-500">Inferred frequency</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
            <span className="text-xs text-slate-400 font-medium">Next Expected Due</span>
            <div className="text-base font-semibold text-emerald-400 mt-1">
              {commitment.next_expected_date ? commitment.next_expected_date : "—"}
            </div>
            <span className="text-[11px] text-slate-500">Projected billing date</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
            <span className="text-xs text-slate-400 font-medium">Annualised Obligation</span>
            <div className="text-xl font-bold font-mono text-white mt-1">
              {commitment.annualised_amount ? `₹${Number(commitment.annualised_amount).toLocaleString("en-IN")}` : "—"}
            </div>
            <span className="text-[11px] text-slate-500">{commitment.annualisation_method || "Direct multiplier"}</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800">
            <span className="text-xs text-slate-400 font-medium">History Period</span>
            <div className="text-xs font-medium text-slate-300 mt-1">
              {new Date(commitment.first_seen_at).toLocaleDateString("en-IN", { month: "short", year: "2-digit" })} –{" "}
              {new Date(commitment.last_seen_at).toLocaleDateString("en-IN", { month: "short", year: "2-digit" })}
            </div>
            <span className="text-[11px] text-slate-500">First to last debit</span>
          </div>
        </div>

        {/* Intelligence Explanation & Codes */}
        <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 flex flex-col gap-4">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            Discovery Engine Explanation
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed">
            {commitment.detection_explanation || "No detection explanation recorded."}
          </p>

          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80">
            <span className="text-xs text-slate-500 font-medium mr-1">Detection Codes:</span>
            {commitment.detection_reason_codes?.map((code) => (
              <span
                key={code}
                className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono text-[11px]"
              >
                {code}
              </span>
            ))}
            <span className="ml-auto text-[11px] text-slate-500 font-mono">
              Engine {commitment.detector_version}
            </span>
          </div>
        </div>

        {/* Tab Controls for Supporting Evidence */}
        <div className="flex items-center gap-4 border-b border-slate-800">
          <button
            onClick={() => setActiveTab("transactions")}
            className={`pb-3 text-sm font-medium transition-colors border-b-2 cursor-pointer ${
              activeTab === "transactions"
                ? "border-emerald-400 text-white"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Supporting Transactions ({commitment.supporting_transactions.length})
          </button>
          <button
            onClick={() => setActiveTab("timeline")}
            className={`pb-3 text-sm font-medium transition-colors border-b-2 cursor-pointer ${
              activeTab === "timeline"
                ? "border-emerald-400 text-white"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Chronological Timeline ({timelineEvents.length})
          </button>
        </div>

        {/* Tab 1: Supporting Transactions Table */}
        {activeTab === "transactions" && (
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-400 font-medium">
                    <th className="py-3 px-4">Date</th>
                    <th className="py-3 px-4">Raw Descriptor</th>
                    <th className="py-3 px-4">Amount</th>
                    <th className="py-3 px-4">Channel</th>
                    <th className="py-3 px-4">Reference</th>
                    <th className="py-3 px-4">Evidence Role</th>
                    <th className="py-3 px-4">Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {commitment.supporting_transactions.map((tx) => (
                    <tr key={tx.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 text-slate-300 font-sans">
                        {new Date(tx.transaction_date).toLocaleDateString("en-IN", {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        })}
                      </td>
                      <td className="py-3 px-4 text-slate-200 font-sans font-medium">
                        {tx.raw_descriptor}
                      </td>
                      <td className="py-3 px-4 font-bold text-white">
                        ₹{Number(tx.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-slate-400 font-sans uppercase text-[11px]">
                        {tx.payment_channel}
                      </td>
                      <td className="py-3 px-4 text-slate-500 text-[11px]">
                        {tx.payment_reference || "—"}
                      </td>
                      <td className="py-3 px-4 font-sans">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[11px]">
                          {tx.relationship_role.replace("_", " ")}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400 font-sans text-[11px]">
                        {tx.reason || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 2: Chronological Timeline */}
        {activeTab === "timeline" && (
          <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 flex flex-col gap-6">
            <div className="relative border-l border-slate-800 ml-4 pl-6 flex flex-col gap-6">
              {timelineEvents.map((evt) => (
                <div key={evt.event_id} className="relative flex flex-col gap-1">
                  <div className="absolute -left-[31px] top-1 w-3 h-3 rounded-full bg-emerald-400 border-2 border-slate-950" />
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-500 font-mono">
                      {new Date(evt.event_date).toLocaleDateString("en-IN", {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700">
                      {evt.event_type}
                    </span>
                  </div>
                  <h4 className="text-sm font-semibold text-white mt-0.5">{evt.title}</h4>
                  <p className="text-xs text-slate-400">{evt.description}</p>
                  {evt.amount && (
                    <span className="text-xs font-mono font-medium text-emerald-400">
                      Amount: ₹{Number(evt.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Edit Modal / Slideout */}
        {isEditing && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-md p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col gap-4">
              <h3 className="text-lg font-bold text-white">Correct Commitment Details</h3>
              <p className="text-xs text-slate-400">
                Update commitment metadata. All user corrections are marked and permanently protected against recalculation.
              </p>

              <form onSubmit={handleSaveCorrection} className="flex flex-col gap-4 mt-2">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">
                    Display Name
                  </label>
                  <input
                    type="text"
                    value={editDisplayName}
                    onChange={(e) => setEditDisplayName(e.target.value)}
                    required
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">
                    Commitment Type
                  </label>
                  <select
                    value={editType}
                    onChange={(e) => setEditType(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="subscription">Subscription</option>
                    <option value="membership">Membership</option>
                    <option value="utility">Utility</option>
                    <option value="insurance">Insurance</option>
                    <option value="loan_emi">Loan EMI</option>
                    <option value="other">Other</option>
                    <option value="needs_review">Needs Review</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">
                    Cadence
                  </label>
                  <select
                    value={editCadence}
                    onChange={(e) => setEditCadence(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="monthly">Monthly</option>
                    <option value="variable_monthly">Variable Monthly</option>
                    <option value="weekly">Weekly</option>
                    <option value="fortnightly">Fortnightly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="annual">Annual</option>
                    <option value="irregular">Irregular</option>
                    <option value="unknown">Unknown</option>
                  </select>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={savingEdit}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold cursor-pointer"
                  >
                    {savingEdit ? "Saving..." : "Save Correction"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
