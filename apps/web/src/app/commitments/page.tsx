"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";

import AppHeader from "@/components/navigation/AppHeader";

interface CommitmentItem {
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
}

interface CommitmentSummary {
  total_commitments: number;
  active_commitments: number;
  candidate_commitments: number;
  review_required_commitments: number;
  confirmed_commitments: number;
  total_monthly_spend: number | string;
  total_annualised_spend: number | string;
  by_cadence: Record<string, number>;
  by_commitment_type: Record<string, number>;
  by_confidence_band: Record<string, number>;
}

export default function CommitmentsPage() {
  const [commitments, setCommitments] = useState<CommitmentItem[]>([]);
  const [summary, setSummary] = useState<CommitmentSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [discovering, setDiscovering] = useState<boolean>(false);
  const [discoveryMsg, setDiscoveryMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [cadenceFilter, setCadenceFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [confidenceFilter, setConfidenceFilter] = useState<string>("");

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  // Fetch commitments with filters
  const fetchCommitments = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (searchQuery.trim()) params.append("search", searchQuery.trim());
      if (cadenceFilter) params.append("cadence", cadenceFilter);
      if (typeFilter) params.append("commitment_type", typeFilter);
      if (statusFilter) params.append("status", statusFilter);
      if (confidenceFilter) params.append("confidence_band", confidenceFilter);

      const [listRes, sumRes] = await Promise.all([
        fetch(`${apiBase}/api/v1/commitments?${params.toString()}`),
        fetch(`${apiBase}/api/v1/commitments/summary`),
      ]);

      if (listRes.ok) {
        const data = await listRes.json();
        setCommitments(data);
      }
      if (sumRes.ok) {
        const sumData = await sumRes.json();
        setSummary(sumData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load commitments");
    } finally {
      setLoading(false);
    }
  }, [apiBase, searchQuery, cadenceFilter, typeFilter, statusFilter, confidenceFilter]);

  useEffect(() => {
    let ignore = false;
    async function loadData() {
      try {
        const params = new URLSearchParams();
        if (searchQuery.trim()) params.append("search", searchQuery.trim());
        if (cadenceFilter) params.append("cadence", cadenceFilter);
        if (typeFilter) params.append("commitment_type", typeFilter);
        if (statusFilter) params.append("status", statusFilter);
        if (confidenceFilter) params.append("confidence_band", confidenceFilter);

        const [listRes, sumRes] = await Promise.all([
          fetch(`${apiBase}/api/v1/commitments?${params.toString()}`),
          fetch(`${apiBase}/api/v1/commitments/summary`),
        ]);

        if (!ignore && listRes.ok) {
          const data = await listRes.json();
          setCommitments(data);
        }
        if (!ignore && sumRes.ok) {
          const sumData = await sumRes.json();
          setSummary(sumData);
        }
      } catch (err) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load commitments");
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
  }, [apiBase, searchQuery, cadenceFilter, typeFilter, statusFilter, confidenceFilter]);

  // Run discovery
  const handleDiscover = async () => {
    setDiscovering(true);
    setDiscoveryMsg(null);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/api/v1/commitments/discover`, {
        method: "POST",
      });
      const data = await res.json();
      if (res.ok) {
        setDiscoveryMsg(data.message);
        await fetchCommitments();
      } else {
        setError(data.detail || "Discovery execution failed");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Network error during discovery");
    } finally {
      setDiscovering(false);
    }
  };

  // Quick Confirm
  const handleConfirm = async (id: string) => {
    try {
      const res = await fetch(`${apiBase}/api/v1/commitments/${id}/confirm`, {
        method: "POST",
      });
      if (res.ok) {
        await fetchCommitments();
      }
    } catch {
      // Ignore background error
    }
  };

  // Quick Mark Not Recurring
  const handleMarkNotRecurring = async (id: string) => {
    try {
      const res = await fetch(`${apiBase}/api/v1/commitments/${id}/mark-not-recurring`, {
        method: "POST",
      });
      if (res.ok) {
        await fetchCommitments();
      }
    } catch {
      // Ignore background error
    }
  };

  const getConfidenceBadge = (band: string) => {
    switch (band) {
      case "high":
        return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">High</span>;
      case "medium":
        return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">Medium</span>;
      case "low":
        return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">Low</span>;
      case "needs_review":
        return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Needs Review</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-[#0B3152] text-[#A9BBCD] border border-[#164B68]">{band}</span>;
    }
  };

  const getStatusBadge = (status: string, user_decision?: string | null) => {
    if (user_decision === "confirmed" || status === "user_confirmed") {
      return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Confirmed</span>;
    }
    if (user_decision === "not_recurring" || status === "marked_not_recurring") {
      return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-[#0B3152] text-[#A9BBCD] border border-[#164B68]">Not Recurring</span>;
    }
    if (status === "candidate") {
      return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">Candidate</span>;
    }
    if (status === "review_required" || status === "needs_review") {
      return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">Review Required</span>;
    }
    return <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Active</span>;
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#011633] text-[#F4F7FB] antialiased selection:bg-[#F08A00] selection:text-white">
      {/* Top Header */}
      <AppHeader />

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
        {/* Title and Discovery Action */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Recurring Commitments &amp; Subscriptions
            </h1>
            <p className="mt-1 text-sm text-[#A9BBCD]">
              Explainable recurring payment discovery, cadence inference, and commitment lifecycle intelligence.
            </p>
          </div>

          <button
            onClick={handleDiscover}
            disabled={discovering}
            className="px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold shadow-sm transition-all flex items-center gap-2 self-start sm:self-auto cursor-pointer"
          >
            {discovering ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Analyzing Payment Streams...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Discover Recurring Commitments
              </>
            )}
          </button>
        </div>

        {/* Discovery Notification Banner */}
        {discoveryMsg && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5 text-emerald-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>{discoveryMsg}</span>
            </div>
            <button
              onClick={() => setDiscoveryMsg(null)}
              className="text-emerald-400 hover:text-emerald-200 text-xs font-medium"
            >
              Dismiss
            </button>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
            {error}
          </div>
        )}

        {/* Summary Metrics Bar */}
        {summary && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-[#082746]/60 border border-[#164B68]/80 flex flex-col">
              <span className="text-xs font-medium text-[#A9BBCD]">Total Commitments</span>
              <span className="text-2xl font-bold text-white mt-1">{summary.total_commitments}</span>
              <span className="text-[11px] text-[#A9BBCD] mt-1">Discovered recurring payees</span>
            </div>
            <div className="p-4 rounded-xl bg-[#082746]/60 border border-[#164B68]/80 flex flex-col">
              <span className="text-xs font-medium text-[#A9BBCD]">Active Commitments</span>
              <span className="text-2xl font-bold text-emerald-400 mt-1">{summary.active_commitments}</span>
              <span className="text-[11px] text-[#A9BBCD] mt-1">{summary.confirmed_commitments} user-confirmed</span>
            </div>
            <div className="p-4 rounded-xl bg-[#082746]/60 border border-[#164B68]/80 flex flex-col">
              <span className="text-xs font-medium text-[#A9BBCD]">Est. Monthly Spend</span>
              <span className="text-2xl font-bold text-white mt-1">
                ₹{Number(summary.total_monthly_spend).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span className="text-[11px] text-[#A9BBCD] mt-1">
                Annualised: ₹{Number(summary.total_annualised_spend).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
              </span>
            </div>
            <div className="p-4 rounded-xl bg-[#082746]/60 border border-[#164B68]/80 flex flex-col">
              <span className="text-xs font-medium text-[#A9BBCD]">Review &amp; Candidates</span>
              <span className="text-2xl font-bold text-amber-400 mt-1">
                {summary.candidate_commitments + summary.review_required_commitments}
              </span>
              <span className="text-[11px] text-[#A9BBCD] mt-1">
                {summary.candidate_commitments} candidate(s), {summary.review_required_commitments} review
              </span>
            </div>
          </div>
        )}

        {/* Filters and Search Bar */}
        <div className="p-4 rounded-xl bg-[#082746]/40 border border-[#164B68] flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="w-full md:w-72 relative">
            <input
              type="text"
              placeholder="Search payees or merchants..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3.5 py-2 rounded-lg bg-[#011633] border border-[#164B68] text-sm text-[#F4F7FB] placeholder-[#A9BBCD]/60 focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>

          <div className="w-full md:w-auto flex flex-wrap items-center gap-3">
            {/* Cadence Filter */}
            <select
              value={cadenceFilter}
              onChange={(e) => setCadenceFilter(e.target.value)}
              className="px-3 py-2 rounded-lg bg-[#011633] border border-[#164B68] text-xs text-[#F4F7FB] focus:outline-none focus:border-emerald-500"
            >
              <option value="">All Cadences</option>
              <option value="monthly">Monthly</option>
              <option value="variable_monthly">Variable Monthly</option>
              <option value="weekly">Weekly</option>
              <option value="fortnightly">Fortnightly</option>
              <option value="quarterly">Quarterly</option>
              <option value="annual">Annual</option>
              <option value="irregular">Irregular</option>
            </select>

            {/* Type Filter */}
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-3 py-2 rounded-lg bg-[#011633] border border-[#164B68] text-xs text-[#F4F7FB] focus:outline-none focus:border-emerald-500"
            >
              <option value="">All Types</option>
              <option value="subscription">Subscription</option>
              <option value="membership">Membership</option>
              <option value="utility">Utility</option>
              <option value="insurance">Insurance</option>
              <option value="loan_emi">Loan EMI</option>
              <option value="needs_review">Needs Review</option>
              <option value="other">Other</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 rounded-lg bg-[#011633] border border-[#164B68] text-xs text-[#F4F7FB] focus:outline-none focus:border-emerald-500"
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="user_confirmed">User Confirmed</option>
              <option value="candidate">Candidate</option>
              <option value="review_required">Review Required</option>
              <option value="marked_not_recurring">Marked Not Recurring</option>
            </select>

            {/* Confidence Filter */}
            <select
              value={confidenceFilter}
              onChange={(e) => setConfidenceFilter(e.target.value)}
              className="px-3 py-2 rounded-lg bg-[#011633] border border-[#164B68] text-xs text-[#F4F7FB] focus:outline-none focus:border-emerald-500"
            >
              <option value="">All Confidence</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="needs_review">Needs Review</option>
            </select>
          </div>
        </div>

        {/* Commitments Table */}
        <div className="rounded-xl border border-[#164B68] bg-[#082746]/50 overflow-hidden shadow-sm">
          {loading ? (
            <div className="p-12 text-center text-[#A9BBCD]">Loading commitments...</div>
          ) : commitments.length === 0 ? (
            <div className="p-12 text-center flex flex-col items-center justify-center gap-3">
              <svg className="w-12 h-12 text-[#164B68]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p className="text-sm font-medium text-[#F4F7FB]">No recurring commitments found</p>
              <p className="text-xs text-[#A9BBCD] max-w-sm">
                Import statements in the Upload Centre and click &ldquo;Discover Recurring Commitments&rdquo; to analyze recurring payments.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#164B68] bg-[#082746]/80 text-[#A9BBCD] font-medium">
                    <th className="py-3 px-4">Payee / Commitment</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Cadence</th>
                    <th className="py-3 px-4">Representative Amount</th>
                    <th className="py-3 px-4">Annualised</th>
                    <th className="py-3 px-4">Confidence</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Next Due</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#164B68]/60">
                  {commitments.map((c) => (
                    <tr key={c.id} className="hover:bg-[#0B3152]/30 transition-colors group">
                      <td className="py-3.5 px-4 font-medium text-white">
                        <Link
                          href={`/commitments/${c.id}`}
                          className="hover:text-emerald-400 transition-colors flex flex-col"
                        >
                          <span className="font-semibold text-sm text-[#F4F7FB] group-hover:text-emerald-400">
                            {c.display_name}
                          </span>
                          <span className="text-[11px] text-[#A9BBCD] font-normal">
                            {c.transaction_count} supporting debit{c.transaction_count === 1 ? "" : "s"}
                          </span>
                        </Link>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="capitalize px-2 py-0.5 rounded bg-[#0B3152]/80 text-[#F4F7FB] border border-[#164B68]/60 text-[11px]">
                          {c.commitment_type.replace("_", " ")}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="capitalize text-[#F4F7FB] font-medium">
                          {c.cadence.replace("_", " ")}
                        </span>
                        {c.amount_pattern === "variable" && (
                          <span className="block text-[10px] text-amber-400">variable amounts</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 font-mono font-medium text-[#F4F7FB]">
                        ₹{Number(c.representative_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[#A9BBCD]">
                        {c.annualised_amount ? `₹${Number(c.annualised_amount).toLocaleString("en-IN")}` : "—"}
                      </td>
                      <td className="py-3.5 px-4">
                        {getConfidenceBadge(c.confidence_band)}
                      </td>
                      <td className="py-3.5 px-4">
                        {getStatusBadge(c.status, c.user_decision)}
                      </td>
                      <td className="py-3.5 px-4 text-[#A9BBCD]">
                        {c.next_expected_date ? c.next_expected_date : "—"}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Link
                            href={`/commitments/${c.id}`}
                            className="px-2.5 py-1 rounded bg-[#0B3152] hover:bg-[#0B3152] text-[#F4F7FB] hover:text-white transition-colors text-[11px] font-medium"
                          >
                            Details
                          </Link>
                          {c.status !== "user_confirmed" && c.user_decision !== "confirmed" && (
                            <button
                              onClick={() => handleConfirm(c.id)}
                              className="px-2 py-1 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 transition-colors text-[11px] font-medium cursor-pointer"
                              title="Confirm as recurring"
                            >
                              Confirm
                            </button>
                          )}
                          {c.status !== "marked_not_recurring" && c.user_decision !== "not_recurring" && (
                            <button
                              onClick={() => handleMarkNotRecurring(c.id)}
                              className="px-2 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 transition-colors text-[11px] font-medium cursor-pointer"
                              title="Mark not recurring"
                            >
                              Dismiss
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
