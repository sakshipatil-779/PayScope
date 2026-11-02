"use client";

import { getApiBaseUrl } from "@/lib/api";
import React, { useState, useEffect, useCallback, use } from "react";

import AppHeader from "@/components/navigation/AppHeader";

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

  const apiBase = getApiBaseUrl();

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
    <div className="min-h-screen flex flex-col bg-[#011633] text-[#F4F7FB] antialiased selection:bg-[#F08A00] selection:text-white">
      {/* Top Header */}
      <AppHeader />

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
        {loading ? (
          <div className="py-12 text-center text-xs text-[#A9BBCD]">
            Loading merchant profile...
          </div>
        ) : error || !merchant ? (
          <div className="py-12 text-center text-xs text-rose-400">
            {error || "Merchant not found."}
          </div>
        ) : (
          <>
            {/* Merchant Identity Card */}
            <section className="rounded-xl border border-[#164B68] bg-[#082746]/50 p-6 flex flex-col gap-6 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#164B68] pb-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-[#0B3152] text-[#F4F7FB] border border-[#164B68]">
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
                  <div className="rounded bg-[#011633] p-2.5 border border-[#164B68]">
                    <span className="text-[#A9BBCD] block text-[10px]">Aliases</span>
                    <span className="text-base font-bold text-white">{merchant.alias_count}</span>
                  </div>
                  <div className="rounded bg-[#011633] p-2.5 border border-[#164B68]">
                    <span className="text-[#A9BBCD] block text-[10px]">Linked Txns</span>
                    <span className="text-base font-bold text-emerald-400">{merchant.transaction_count}</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
                <div>
                  <span className="text-[#A9BBCD] block">Merchant ID:</span>
                  <span className="text-[#F4F7FB] break-all">{merchant.id}</span>
                </div>
                <div>
                  <span className="text-[#A9BBCD] block">Default Commitment:</span>
                  <span className="text-[#F4F7FB] capitalize">{merchant.commitment_type_default?.replace("_", " ") || "Subscription"}</span>
                </div>
                <div>
                  <span className="text-[#A9BBCD] block">Provenance:</span>
                  <span className="text-[#F4F7FB]">{merchant.reference_source || "Hand-curated fixtures"}</span>
                </div>
              </div>
            </section>

            {/* ALIASES TABLE & MANAGEMENT */}
            <section className="rounded-xl border border-[#164B68] bg-[#082746]/50 p-6 flex flex-col gap-6 shadow-sm">
              <div className="flex items-center justify-between border-b border-[#164B68] pb-4">
                <div>
                  <h3 className="text-base font-semibold text-white">
                    Known Descriptor Aliases ({aliases.length})
                  </h3>
                  <p className="text-xs text-[#A9BBCD]">
                    Raw patterns that resolve to this canonical merchant identity.
                  </p>
                </div>
              </div>

              {/* Form to Add New Alias */}
              <form onSubmit={handleAddAlias} className="rounded-lg bg-[#011633]/70 border border-[#164B68] p-4 space-y-3 text-xs">
                <h4 className="font-semibold text-[#F4F7FB]">Add New Descriptor Alias</h4>
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                  <div className="sm:col-span-2 space-y-1">
                    <label className="text-[11px] text-[#A9BBCD] block font-mono">Alias Text / Pattern</label>
                    <input
                      type="text"
                      value={newAliasText}
                      onChange={(e) => setNewAliasText(e.target.value)}
                      placeholder="e.g. POS STRMPLSE INTL"
                      className="w-full rounded border border-[#164B68] bg-[#082746] px-3 py-1.5 text-xs font-mono text-white placeholder-slate-600 focus:border-emerald-500 focus:outline-none"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] text-[#A9BBCD] block font-mono">Matcher Type</label>
                    <select
                      value={newMatcherType}
                      onChange={(e) => setNewMatcherType(e.target.value)}
                      className="w-full rounded border border-[#164B68] bg-[#082746] px-2 py-1.5 text-xs text-[#F4F7FB] focus:border-emerald-500 focus:outline-none"
                    >
                      <option value="exact">exact</option>
                      <option value="prefix">prefix</option>
                      <option value="token_pattern">token_pattern</option>
                      <option value="regex">regex</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[11px] text-[#A9BBCD] block font-mono">Confidence Band</label>
                    <select
                      value={newConfidenceBand}
                      onChange={(e) => setNewConfidenceBand(e.target.value)}
                      className="w-full rounded border border-[#164B68] bg-[#082746] px-2 py-1.5 text-xs text-[#F4F7FB] focus:border-emerald-500 focus:outline-none"
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
              <div className="overflow-x-auto rounded-lg border border-[#164B68] bg-[#011633]">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-[#082746] border-b border-[#164B68] text-[#A9BBCD]">
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
                      <tr key={al.id} className="hover:bg-[#082746]/50">
                        <td className="px-3 py-2 text-white font-medium">{al.alias_text}</td>
                        <td className="px-3 py-2 text-emerald-400">{al.normalised_alias}</td>
                        <td className="px-3 py-2">
                          <span className="px-2 py-0.5 rounded text-[10px] bg-[#0B3152] text-[#F4F7FB] border border-[#164B68]">
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
                        <td className="px-3 py-2 text-[#A9BBCD]">
                          {al.is_active ? "✓ Active" : "Disabled"}
                        </td>
                        <td className="px-3 py-2 text-[#A9BBCD] text-[11px]">
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
      <footer className="border-t border-slate-900 bg-[#011633]/80 py-6 text-center text-xs text-[#A9BBCD]">
        PayScope Prototype — Synthetic financial data only. No real banking connectivity.
      </footer>
    </div>
  );
}
