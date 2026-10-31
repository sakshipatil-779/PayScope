"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";

interface CandidatePayload {
  merchant_id: string;
  canonical_name: string;
  category: string;
  score: number;
  method: string;
  confidence_band: string;
}

interface ReviewItem {
  id: string;
  user_id: string;
  transaction_id?: string | null;
  item_type: string;
  raw_descriptor: string;
  normalised_descriptor: string;
  suggested_merchant_id?: string | null;
  suggested_merchant_name?: string | null;
  similarity_score?: number | null;
  confidence_band?: string | null;
  match_method?: string | null;
  explanation?: string | null;
  reason_code: string;
  status: string;
  candidates?: CandidatePayload[] | null;
  user_selected_merchant_id?: string | null;
  decision_notes?: string | null;
  created_at: string;
  reviewed_at?: string | null;
}

interface MerchantOption {
  id: string;
  canonical_name: string;
  category: string;
}

export default function ManualReviewPage() {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [merchants, setMerchants] = useState<MerchantOption[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("open");
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Correction state for an item
  const [correctingItemId, setCorrectingItemId] = useState<string | null>(null);
  const [selectedMerchantId, setSelectedMerchantId] = useState<string>("");
  const [createAlias, setCreateAlias] = useState<boolean>(true);
  const [correctionNotes, setCorrectionNotes] = useState<string>("");

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  // Fetch reviews and merchants
  const fetchReviews = useCallback(async () => {
    setLoading(true);
    try {
      const url = statusFilter === "all"
        ? `${apiBase}/api/v1/merchant-reviews?limit=50`
        : `${apiBase}/api/v1/merchant-reviews?status=${statusFilter}&limit=50`;

      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setReviews(data);
      }
    } catch {
      // Ignore background error
    } finally {
      setLoading(false);
    }
  }, [apiBase, statusFilter]);

  useEffect(() => {
    let ignore = false;
    async function loadInitial() {
      try {
        const url = statusFilter === "all"
          ? `${apiBase}/api/v1/merchant-reviews?limit=50`
          : `${apiBase}/api/v1/merchant-reviews?status=${statusFilter}&limit=50`;

        const [resR, resM] = await Promise.all([
          fetch(url),
          fetch(`${apiBase}/api/v1/merchants?limit=100`),
        ]);

        if (!ignore && resR.ok) {
          const dataR = await resR.json();
          setReviews(dataR);
        }
        if (!ignore && resM.ok) {
          const dataM = await resM.json();
          setMerchants(dataM.map((m: { id: string; canonical_name: string; category: string }) => ({
            id: m.id,
            canonical_name: m.canonical_name,
            category: m.category,
          })));
        }
      } catch {
        // Ignore
      } finally {
        if (!ignore) setLoading(false);
      }
    }
    loadInitial();
    return () => {
      ignore = true;
    };
  }, [apiBase, statusFilter]);

  // Actions
  const handleAccept = async (reviewId: string) => {
    setActionLoading(reviewId);
    try {
      const res = await fetch(`${apiBase}/api/v1/merchant-reviews/${reviewId}/accept`, {
        method: "POST",
      });
      if (res.ok) {
        fetchReviews();
      }
    } catch {
      // Ignore
    } finally {
      setActionLoading(null);
    }
  };

  const handleCorrect = async (reviewId: string) => {
    if (!selectedMerchantId) return;

    setActionLoading(reviewId);
    try {
      const res = await fetch(`${apiBase}/api/v1/merchant-reviews/${reviewId}/correct`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          merchant_id: selectedMerchantId,
          create_alias: createAlias,
          decision_notes: correctionNotes.trim() || undefined,
        }),
      });
      if (res.ok) {
        setCorrectingItemId(null);
        setSelectedMerchantId("");
        setCorrectionNotes("");
        fetchReviews();
      }
    } catch {
      // Ignore
    } finally {
      setActionLoading(null);
    }
  };

  const handleDismiss = async (reviewId: string) => {
    setActionLoading(reviewId);
    try {
      const res = await fetch(`${apiBase}/api/v1/merchant-reviews/${reviewId}/dismiss`, {
        method: "POST",
      });
      if (res.ok) {
        fetchReviews();
      }
    } catch {
      // Ignore
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 antialiased selection:bg-emerald-500 selection:text-slate-950">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
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
            <span className="text-sm font-medium text-slate-300">Manual Review Queue</span>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/insights"
              className="text-xs px-3 py-1.5 rounded-lg border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 hover:bg-indigo-500/20 transition-colors font-medium"
            >
              Insights
            </Link>
            <Link
              href="/commitments"
              className="text-xs px-3 py-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20 transition-colors font-semibold"
            >
              Commitments
            </Link>
            <Link
              href="/merchants"
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-slate-200 transition-colors"
            >
              Merchant Catalogue
            </Link>
            <Link
              href="/upload"
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-slate-200 transition-colors"
            >
              Upload Centre
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
        {/* Title */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Merchant Manual Review Queue
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Audit and resolve ambiguous, low-confidence, or payment gateway aggregator descriptors.
            </p>
          </div>

          <button
            onClick={fetchReviews}
            disabled={loading}
            className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors self-start sm:self-auto"
          >
            {loading ? "Refreshing..." : "Refresh Queue"}
          </button>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-3 text-xs overflow-x-auto">
          {[
            { id: "open", label: "Open Reviews" },
            { id: "accepted", label: "Accepted" },
            { id: "corrected", label: "Corrected" },
            { id: "dismissed", label: "Dismissed" },
            { id: "all", label: "All Items" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                statusFilter === tab.id
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "bg-slate-900/60 text-slate-400 hover:text-slate-200 hover:bg-slate-850"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Review Items List */}
        {loading ? (
          <div className="py-12 text-center text-xs text-slate-500">
            Loading review queue...
          </div>
        ) : reviews.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl space-y-2">
            <p className="text-sm font-medium text-slate-400">No review items found in this view.</p>
            <p className="text-slate-500">
              When statements with ambiguous or aggregator descriptors (e.g. Razorpay/BillDesk) are uploaded, they appear here for user confirmation.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {reviews.map((item) => (
              <div
                key={item.id}
                className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-5 shadow-sm"
              >
                {/* Card Top: Descriptors and Status Badges */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 border-b border-slate-800 pb-4">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-semibold border ${
                          item.status === "open"
                            ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                            : item.status === "accepted"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : item.status === "corrected"
                            ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                            : "bg-slate-800 text-slate-400 border-slate-700"
                        }`}
                      >
                        {item.status}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">
                        Reason: {item.reason_code}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold font-mono text-white break-all">
                      {item.raw_descriptor}
                    </h3>
                    <p className="text-xs font-mono text-emerald-400">
                      Normalised: {item.normalised_descriptor}
                    </p>
                  </div>

                  <div className="text-right text-xs font-mono text-slate-500 shrink-0">
                    <span>{new Date(item.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {/* Card Middle: Match Explanation & Suggested Merchant */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 space-y-2">
                    <span className="text-slate-500 font-mono text-[11px] block">Suggested Merchant</span>
                    {item.suggested_merchant_name ? (
                      <div className="space-y-1">
                        <p className="text-sm font-semibold text-white">
                          {item.suggested_merchant_name}
                        </p>
                        <div className="flex items-center gap-3 text-slate-400 font-mono text-[11px]">
                          <span>Score: <strong className="text-emerald-400">{item.similarity_score}%</strong></span>
                          <span>Confidence: <strong>{item.confidence_band}</strong></span>
                          <span>Method: <strong>{item.match_method}</strong></span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-slate-400 italic">No candidate merchant identified.</p>
                    )}
                  </div>

                  <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 space-y-1.5">
                    <span className="text-slate-500 font-mono text-[11px] block">Resolution Explanation</span>
                    <p className="text-slate-300 text-[11px] leading-relaxed">
                      {item.explanation || "Descriptor routed to manual review based on similarity thresholds."}
                    </p>
                  </div>
                </div>

                {/* Candidate Breakdown (if available) */}
                {item.candidates && item.candidates.length > 0 && (
                  <div className="space-y-1 text-xs font-mono">
                    <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Candidate Matches</span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {item.candidates.map((cand, idx) => (
                        <div key={idx} className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800/80 text-[11px]">
                          <span className="text-slate-300 font-sans">{cand.canonical_name}</span>
                          <span className="font-bold text-emerald-400">{cand.score}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Correction Form Dropdown (when correcting) */}
                {correctingItemId === item.id && (
                  <div className="rounded-lg bg-slate-950 p-4 border border-blue-500/40 space-y-3 text-xs">
                    <h4 className="font-semibold text-blue-300">Select Correct Merchant</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <select
                        value={selectedMerchantId}
                        onChange={(e) => setSelectedMerchantId(e.target.value)}
                        className="rounded border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-white focus:border-blue-500 focus:outline-none"
                      >
                        <option value="">Select known merchant...</option>
                        {merchants.map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.canonical_name} ({m.category})
                          </option>
                        ))}
                      </select>

                      <input
                        type="text"
                        value={correctionNotes}
                        onChange={(e) => setCorrectionNotes(e.target.value)}
                        placeholder="Optional decision notes..."
                        className="rounded border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-white placeholder-slate-600 focus:border-blue-500 focus:outline-none"
                      />
                    </div>

                    <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                      <input
                        type="checkbox"
                        checked={createAlias}
                        onChange={(e) => setCreateAlias(e.target.checked)}
                        className="rounded border-slate-800 bg-slate-900 text-blue-500 cursor-pointer"
                      />
                      <span>Save &ldquo;{item.raw_descriptor}&rdquo; as a permanent descriptor alias for this merchant</span>
                    </label>

                    <div className="flex items-center gap-2 pt-2">
                      <button
                        onClick={() => handleCorrect(item.id)}
                        disabled={!selectedMerchantId || actionLoading === item.id}
                        className="px-4 py-1.5 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold text-xs transition-colors"
                      >
                        Confirm Correction
                      </button>
                      <button
                        onClick={() => setCorrectingItemId(null)}
                        className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 text-xs transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {/* Card Actions (if open) */}
                {item.status === "open" && correctingItemId !== item.id && (
                  <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-800/80">
                    {item.suggested_merchant_id && (
                      <button
                        onClick={() => handleAccept(item.id)}
                        disabled={actionLoading === item.id}
                        className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-sm transition-colors flex items-center gap-1.5"
                      >
                        ✓ Accept Match
                      </button>
                    )}

                    <button
                      onClick={() => {
                        setCorrectingItemId(item.id);
                        setSelectedMerchantId(item.suggested_merchant_id || "");
                      }}
                      disabled={actionLoading === item.id}
                      className="px-3.5 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 text-xs font-semibold transition-colors"
                    >
                      Select Different Merchant
                    </button>

                    <button
                      onClick={() => handleDismiss(item.id)}
                      disabled={actionLoading === item.id}
                      className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-750 text-slate-400 hover:text-slate-200 text-xs transition-colors"
                    >
                      Dismiss / Mark Unknown
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-6 text-center text-xs text-slate-500">
        MandateLens Prototype — Synthetic financial data only. No real banking connectivity.
      </footer>
    </div>
  );
}
