"use client";

import React, { useState, useEffect, useCallback, use } from "react";
import Link from "next/link";

interface MerchantDetail {
  id: string;
  canonical_name: string;
  category: string;
  commitment_type_default?: string | null;
  website_url?: string | null;
  support_url?: string | null;
  is_fictional_demo_merchant: boolean;
  reference_source?: string | null;
  alias_count: number;
  transaction_count: number;
  created_at: string;
  updated_at: string;
}

interface AliasItem {
  id: string;
  merchant_id: string;
  alias_text: string;
  normalised_alias: string;
  matcher_type: string;
  pattern?: string | null;
  confidence_band: string;
  reference_source?: string | null;
  is_active: boolean;
  created_at: string;
}

export default function MerchantDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const merchantId = resolvedParams.id;

  const [merchant, setMerchant] = useState<MerchantDetail | null>(null);
  const [aliases, setAliases] = useState<AliasItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // New alias form state
  const [newAliasText, setNewAliasText] = useState<string>("");
  const [newMatcherType, setNewMatcherType] = useState<string>("exact");
  const [newConfidenceBand, setNewConfidenceBand] = useState<string>("high");
  const [addingAlias, setAddingAlias] = useState<boolean>(false);
  const [aliasFormError, setAliasFormError] = useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  const fetchMerchantAndAliases = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [resM, resA] = await Promise.all([
        fetch(`${apiBase}/api/v1/merchants/${merchantId}`),
        fetch(`${apiBase}/api/v1/merchants/${merchantId}/aliases`),
      ]);

      if (!resM.ok) {
        throw new Error("Merchant not found.");
      }

      const dataM = await resM.json();
      const dataA = resA.ok ? await resA.json() : [];
      setMerchant(dataM);
      setAliases(dataA);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load merchant.");
    } finally {
      setLoading(false);
    }
  }, [apiBase, merchantId]);

  useEffect(() => {
    let ignore = false;
    async function loadInitial() {
      try {
        const [resM, resA] = await Promise.all([
          fetch(`${apiBase}/api/v1/merchants/${merchantId}`),
          fetch(`${apiBase}/api/v1/merchants/${merchantId}/aliases`),
        ]);

        if (!ignore) {
          if (!resM.ok) {
            setError("Merchant not found.");
          } else {
            const dataM = await resM.json();
            const dataA = resA.ok ? await resA.json() : [];
            setMerchant(dataM);
            setAliases(dataA);
          }
        }
      } catch (err) {
        if (!ignore) setError(err instanceof Error ? err.message : "Failed to load merchant.");
      } finally {
        if (!ignore) setLoading(false);
      }
    }
    loadInitial();
    return () => {
      ignore = true;
    };
  }, [apiBase, merchantId]);

  const handleAddAlias = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAliasText.trim()) return;

    setAddingAlias(true);
    setAliasFormError(null);

    try {
      const res = await fetch(`${apiBase}/api/v1/merchant-aliases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          merchant_id: merchantId,
          alias_text: newAliasText.trim(),
          matcher_type: newMatcherType,
          confidence_band: newConfidenceBand,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setAliasFormError(data.detail || "Failed to add alias.");
      } else {
        setNewAliasText("");
        fetchMerchantAndAliases();
      }
    } catch (err) {
      setAliasFormError(err instanceof Error ? err.message : "Network error.");
    } finally {
      setAddingAlias(false);
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
            <Link href="/merchants" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">
              Merchants
            </Link>
            <span className="text-slate-600">/</span>
            <span className="text-sm font-medium text-slate-200 truncate max-w-xs">
              {merchant?.canonical_name || "Detail"}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/merchants"
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-slate-200 transition-colors"
            >
              Back to Catalogue
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
        {loading ? (
          <div className="py-12 text-center text-xs text-slate-500">
            Loading merchant profile...
          </div>
        ) : error || !merchant ? (
          <div className="py-12 text-center text-xs text-rose-400">
            {error || "Merchant not found."}
          </div>
        ) : (
          <>
            {/* Merchant Identity Card */}
            <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-6 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {merchant.category.replace("_", " ")}
                    </span>
                    <span className="text-xs text-emerald-400 font-medium">
                      Curated Demo Entity
                    </span>
                  </div>
                  <h1 className="text-2xl font-bold text-white tracking-tight">
                    {merchant.canonical_name}
                  </h1>
                </div>

                <div className="flex items-center gap-4 text-xs font-mono">
                  <div className="rounded bg-slate-950 p-2.5 border border-slate-800">
                    <span className="text-slate-500 block text-[10px]">Aliases</span>
                    <span className="text-base font-bold text-white">{merchant.alias_count}</span>
                  </div>
                  <div className="rounded bg-slate-950 p-2.5 border border-slate-800">
                    <span className="text-slate-500 block text-[10px]">Linked Txns</span>
                    <span className="text-base font-bold text-emerald-400">{merchant.transaction_count}</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
                <div>
                  <span className="text-slate-500 block">Merchant ID:</span>
                  <span className="text-slate-300 break-all">{merchant.id}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Default Commitment:</span>
                  <span className="text-slate-300 capitalize">{merchant.commitment_type_default?.replace("_", " ") || "Subscription"}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Provenance:</span>
                  <span className="text-slate-300">{merchant.reference_source || "Hand-curated fixtures"}</span>
                </div>
              </div>
            </section>

            {/* ALIASES TABLE & MANAGEMENT */}
            <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-6 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <h3 className="text-base font-semibold text-white">
                    Known Descriptor Aliases ({aliases.length})
                  </h3>
                  <p className="text-xs text-slate-400">
                    Raw patterns that resolve to this canonical merchant identity.
                  </p>
                </div>
              </div>

              {/* Form to Add New Alias */}
              <form onSubmit={handleAddAlias} className="rounded-lg bg-slate-950/70 border border-slate-800 p-4 space-y-3 text-xs">
                <h4 className="font-semibold text-slate-300">Add New Descriptor Alias</h4>
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                  <div className="sm:col-span-2 space-y-1">
                    <label className="text-[11px] text-slate-400 block font-mono">Alias Text / Pattern</label>
                    <input
                      type="text"
                      value={newAliasText}
                      onChange={(e) => setNewAliasText(e.target.value)}
                      placeholder="e.g. POS STRMPLSE INTL"
                      className="w-full rounded border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs font-mono text-white placeholder-slate-600 focus:border-emerald-500 focus:outline-none"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] text-slate-400 block font-mono">Matcher Type</label>
                    <select
                      value={newMatcherType}
                      onChange={(e) => setNewMatcherType(e.target.value)}
                      className="w-full rounded border border-slate-800 bg-slate-900 px-2 py-1.5 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none"
                    >
                      <option value="exact">exact</option>
                      <option value="prefix">prefix</option>
                      <option value="token_pattern">token_pattern</option>
                      <option value="regex">regex</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] text-slate-400 block font-mono">Confidence Band</label>
                    <select
                      value={newConfidenceBand}
                      onChange={(e) => setNewConfidenceBand(e.target.value)}
                      className="w-full rounded border border-slate-800 bg-slate-900 px-2 py-1.5 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none"
                    >
                      <option value="high">high</option>
                      <option value="medium">medium</option>
                      <option value="low">low</option>
                    </select>
                  </div>
                </div>

                {aliasFormError && (
                  <div className="text-xs text-rose-400 pt-1">{aliasFormError}</div>
                )}

                <button
                  type="submit"
                  disabled={addingAlias || !newAliasText.trim()}
                  className="px-4 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold transition-colors"
                >
                  {addingAlias ? "Adding..." : "+ Add Alias"}
                </button>
              </form>

              {/* Aliases Table */}
              <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-900 border-b border-slate-800 text-slate-400">
                    <tr>
                      <th className="px-3 py-2">Alias String</th>
                      <th className="px-3 py-2">Normalised Alias</th>
                      <th className="px-3 py-2">Matcher</th>
                      <th className="px-3 py-2">Confidence</th>
                      <th className="px-3 py-2">Active</th>
                      <th className="px-3 py-2">Source</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-850">
                    {aliases.map((al) => (
                      <tr key={al.id} className="hover:bg-slate-900/50">
                        <td className="px-3 py-2 text-white font-medium">{al.alias_text}</td>
                        <td className="px-3 py-2 text-emerald-400">{al.normalised_alias}</td>
                        <td className="px-3 py-2">
                          <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700">
                            {al.matcher_type}
                          </span>
                        </td>
                        <td className="px-3 py-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${
                              al.confidence_band === "high"
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                            }`}
                          >
                            {al.confidence_band}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-slate-400">
                          {al.is_active ? "✓ Active" : "Disabled"}
                        </td>
                        <td className="px-3 py-2 text-slate-500 text-[11px]">
                          {al.reference_source || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-6 text-center text-xs text-slate-500">
        MandateLens Prototype — Synthetic financial data only. No real banking connectivity.
      </footer>
    </div>
  );
}
