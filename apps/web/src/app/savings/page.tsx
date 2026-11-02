"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import AppHeader from "@/components/navigation/AppHeader";

interface SavingsOpportunity {
  id: string;
  opportunity_type: string;
  classification: string;
  commitment_id: string;
  commitment_name: string;
  merchant_name: string;
  category: string;
  current_monthly_cost: number;
  current_annual_cost: number;
  potential_monthly_saving: number;
  potential_annual_saving: number;
  evidence_summary: string;
  insight_id: string | null;
  price_event_id: string | null;
  usage_coverage_id: string | null;
  details: Record<string, unknown>;
}

interface SavingsSummary {
  currency: string;
  total_potential_annual_savings: number;
  total_potential_monthly_savings: number;
  price_increase_savings: number;
  unused_commitment_savings: number;
  duplicate_service_savings: number;
  opportunities_count: number;
  opportunities: SavingsOpportunity[];
}

interface ProjectionResult {
  currency: string;
  baseline_annual_cost: number;
  selected_annual_savings: number;
  selected_monthly_savings: number;
  projected_annual_cost: number;
  projected_monthly_cost: number;
  percentage_reduction: number;
  selected_count: number;
  safeguards_applied: string[];
}

interface SavedScenario {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  selected_opportunity_ids: string[];
  selected_commitment_ids: string[];
  baseline_annual_cost: number;
  projected_annual_cost: number;
  annual_savings: number;
  monthly_savings: number;
  percentage_reduction: number;
  created_at: string;
}

export default function SavingsPage() {
  const [summary, setSummary] = useState<SavingsSummary | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [projection, setProjection] = useState<ProjectionResult | null>(null);
  const [savedScenarios, setSavedScenarios] = useState<SavedScenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter: all, price_increase, unused, duplicate
  const [filterType, setFilterType] = useState<string>("ALL");

  // Save Scenario Modal / Form state
  const [scenarioName, setScenarioName] = useState("");
  const [scenarioDesc, setScenarioDesc] = useState("");
  const [savingScenario, setSavingScenario] = useState(false);
  const [saveSuccessMessage, setSaveSuccessMessage] = useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  // 1. Initial Load of Opportunities & Saved Scenarios
  useEffect(() => {
    let ignore = false;

    async function loadData() {
      setLoading(true);
      setError(null);

      try {
        const [sumRes, scenRes] = await Promise.all([
          fetch(`${apiBase}/api/v1/savings/summary`),
          fetch(`${apiBase}/api/v1/savings/scenarios`),
        ]);

        if (!sumRes.ok) throw new Error("Failed to load savings summary.");

        const sumData: SavingsSummary = await sumRes.json();
        const scenData: SavedScenario[] = scenRes.ok ? await scenRes.json() : [];

        if (!ignore) {
          setSummary(sumData);
          setSavedScenarios(scenData);
          // By default, select all price increase and unused opportunities for initial simulation
          const initialSelected = sumData.opportunities
            .filter((o) => o.opportunity_type === "PRICE_INCREASE" || o.opportunity_type === "POTENTIALLY_UNUSED")
            .map((o) => o.id);
          setSelectedIds(initialSelected);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Error connecting to savings service.");
        }
      } finally {
        if (!ignore) setLoading(false);
      }
    }

    loadData();
    return () => {
      ignore = true;
    };
  }, [apiBase]);

  // 2. Recompute Projection whenever selectedIds change
  useEffect(() => {
    let ignore = false;

    async function recomputeProjection() {
      if (selectedIds.length === 0) {
        // If empty selection, calculate against 0 opportunities to get clean baseline
        try {
          const res = await fetch(`${apiBase}/api/v1/savings/calculate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ selected_opportunity_ids: [] }),
          });
          if (res.ok && !ignore) {
            setProjection(await res.json());
          }
        } catch {
          // ignore
        }
        return;
      }

      setCalculating(true);
      try {
        const res = await fetch(`${apiBase}/api/v1/savings/calculate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ selected_opportunity_ids: selectedIds }),
        });
        if (res.ok && !ignore) {
          const data: ProjectionResult = await res.json();
          setProjection(data);
        }
      } catch (err) {
        console.error("Calculation error:", err);
      } finally {
        if (!ignore) setCalculating(false);
      }
    }

    recomputeProjection();
    return () => {
      ignore = true;
    };
  }, [selectedIds, apiBase]);

  // Toggle opportunity selection
  const toggleOpportunity = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  // Select all or deselect all
  const selectAll = () => {
    if (summary) {
      setSelectedIds(summary.opportunities.map((o) => o.id));
    }
  };

  const clearSelection = () => {
    setSelectedIds([]);
  };

  // Save What-If Scenario to Backend
  const handleSaveScenario = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scenarioName.trim()) return;

    setSavingScenario(true);
    setSaveSuccessMessage(null);

    try {
      const res = await fetch(`${apiBase}/api/v1/savings/scenarios`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: scenarioName.trim(),
          description: scenarioDesc.trim() || undefined,
          selected_opportunity_ids: selectedIds,
        }),
      });

      if (!res.ok) throw new Error("Failed to persist scenario.");

      const created: SavedScenario = await res.json();
      setSavedScenarios((prev) => [created, ...prev]);
      setScenarioName("");
      setScenarioDesc("");
      setSaveSuccessMessage(`Scenario "${created.name}" saved successfully.`);
      setTimeout(() => setSaveSuccessMessage(null), 4000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Error saving scenario.");
    } finally {
      setSavingScenario(false);
    }
  };

  // Delete Saved Scenario
  const handleDeleteScenario = async (id: string) => {
    if (!confirm("Are you sure you want to delete this simulation scenario?")) return;

    try {
      const res = await fetch(`${apiBase}/api/v1/savings/scenarios/${id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setSavedScenarios((prev) => prev.filter((s) => s.id !== id));
      }
    } catch (err) {
      console.error("Delete error:", err);
    }
  };

  const filteredOpportunities = (summary?.opportunities || []).filter((opp) => {
    if (filterType === "ALL") return true;
    return opp.opportunity_type === filterType;
  });

  return (
    <div className="min-h-screen flex flex-col bg-[#011633] text-[#F4F7FB] antialiased selection:bg-teal-500 selection:text-slate-950">
      {/* Platform Header */}
      <AppHeader />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
        {/* Title */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              Savings Intelligence & What-If Financial Projections
            </h1>
            <p className="text-sm text-[#A9BBCD] mt-1">
              Simulate expenditure reductions from price increase renegotiations, verified unused cancellations, and duplicate service consolidations.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-950/60 border border-cyan-800/40 text-cyan-300">
              Deterministic Calculations
            </span>
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-950/60 border border-teal-800/40 text-teal-300">
              Anti-Double-Count Protected
            </span>
          </div>
        </div>

        {/* Classification Notice Badge */}
        <div className="rounded-xl border border-teal-500/20 bg-teal-950/20 p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs">
          <div className="flex items-start gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-teal-400 mt-1 flex-shrink-0" />
            <div>
              <span className="font-semibold text-teal-300 block">
                Evidence Classification Standard: POTENTIAL vs REALIZED
              </span>
              <p className="text-[#F4F7FB] mt-0.5">
                Every figure on this page represents a <strong className="text-white">POTENTIAL</strong> or <strong className="text-white">USER_SELECTED</strong> scenario based on historical statements. Savings are never recorded as <strong className="text-white">REALIZED</strong> without verified confirmation.
              </p>
            </div>
          </div>
        </div>

        {/* Loading and Error */}
        {loading && (
          <div className="p-12 text-center rounded-xl border border-[#164B68] bg-[#082746]/40">
            <div className="w-8 h-8 rounded-full border-2 border-teal-400 border-t-transparent animate-spin mx-auto mb-3" />
            <span className="text-sm text-[#A9BBCD] font-mono">Evaluating savings opportunities & evidence...</span>
          </div>
        )}

        {error && (
          <div className="p-6 rounded-xl border border-rose-900/50 bg-rose-950/20 text-rose-300 text-sm">
            <strong>Error:</strong> {error}
          </div>
        )}

        {!loading && summary && (
          <>
            {/* Top Savings Breakdown Cards */}
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="rounded-xl border border-teal-500/30 bg-teal-950/20 p-5 flex flex-col justify-between">
                <span className="text-xs font-semibold text-teal-300">Total Potential Annual Savings</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl lg:text-3xl font-bold text-teal-300 font-mono">
                    ₹{summary.total_potential_annual_savings.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                  <span className="text-xs text-teal-400/80 font-normal">/yr</span>
                </div>
                <div className="mt-3 pt-2 border-t border-teal-900/40 flex items-center justify-between text-[11px] text-[#A9BBCD]">
                  <span>{summary.opportunities_count} Total Opportunities</span>
                  <span className="text-teal-400 font-mono">Deduped Max</span>
                </div>
              </div>

              <div className="rounded-xl border border-[#164B68] bg-[#082746]/50 p-5 flex flex-col justify-between">
                <span className="text-xs font-medium text-[#A9BBCD]">Price Increase Reversions</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl lg:text-3xl font-bold text-amber-300 font-mono">
                    ₹{summary.price_increase_savings.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                  <span className="text-xs text-[#A9BBCD] font-normal">/yr</span>
                </div>
                <div className="mt-3 pt-2 border-t border-[#164B68] flex items-center justify-between text-[11px] text-[#A9BBCD]">
                  <span>Incremental Step Hikes</span>
                  <span className="text-amber-400/80">Sustained Alerts</span>
                </div>
              </div>

              <div className="rounded-xl border border-[#164B68] bg-[#082746]/50 p-5 flex flex-col justify-between">
                <span className="text-xs font-medium text-[#A9BBCD]">Verified Unused Cancellations</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl lg:text-3xl font-bold text-cyan-300 font-mono">
                    ₹{summary.unused_commitment_savings.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                  <span className="text-xs text-[#A9BBCD] font-normal">/yr</span>
                </div>
                <div className="mt-3 pt-2 border-t border-[#164B68] flex items-center justify-between text-[11px] text-[#A9BBCD]">
                  <span>Zero Activity Logged</span>
                  <span className="text-cyan-400">Verified Coverage</span>
                </div>
              </div>

              <div className="rounded-xl border border-[#164B68] bg-[#082746]/50 p-5 flex flex-col justify-between">
                <span className="text-xs font-medium text-[#A9BBCD]">Category Consolidation</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl lg:text-3xl font-bold text-indigo-300 font-mono">
                    ₹{summary.duplicate_service_savings.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                  <span className="text-xs text-[#A9BBCD] font-normal">/yr</span>
                </div>
                <div className="mt-3 pt-2 border-t border-[#164B68] flex items-center justify-between text-[11px] text-[#A9BBCD]">
                  <span>Overlapping Subscriptions</span>
                  <span className="text-indigo-400">Review Required</span>
                </div>
              </div>
            </section>

            {/* Interactive What-If Projection Bar */}
            {projection && (
              <section className="rounded-2xl border border-cyan-500/40 bg-gradient-to-r from-slate-900 via-slate-900/90 to-cyan-950/40 p-6 shadow-[0_0_30px_rgba(6,182,212,0.12)]">
                <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
                  <div>
                    <span className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-bold block">
                      Live Simulation Scenario
                    </span>
                    <h2 className="text-xl font-bold text-white mt-1 flex items-center">
                      Current vs Projected Annual Outflow
                      {calculating && (
                        <span className="ml-2 text-xs font-mono text-cyan-400 font-normal animate-pulse">
                          (Calculating...)
                        </span>
                      )}
                    </h2>
                    <p className="text-xs text-[#A9BBCD] mt-1 max-w-xl">
                      Formula: Projected Annual Cost = Current Annualized Outflow &minus; Selected Annual Savings.
                      Includes strict non-negative and double-counting protection.
                    </p>
                  </div>

                  {/* Comparison Figures */}
                  <div className="flex flex-wrap items-center gap-6 font-mono">
                    <div className="text-right">
                      <span className="text-[11px] text-[#A9BBCD] block font-sans">Baseline Outflow</span>
                      <span className="text-xl font-bold text-[#F4F7FB]">
                        ₹{projection.baseline_annual_cost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </span>
                    </div>

                    <div className="text-center font-sans text-xl text-cyan-400 font-light">&minus;</div>

                    <div className="text-right">
                      <span className="text-[11px] text-teal-400 block font-sans">Selected Savings ({projection.selected_count})</span>
                      <span className="text-xl font-bold text-teal-300">
                        ₹{projection.selected_annual_savings.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </span>
                    </div>

                    <div className="text-center font-sans text-xl text-cyan-400 font-light">=</div>

                    <div className="text-right p-3 rounded-xl bg-cyan-950/60 border border-cyan-500/40 shadow-inner">
                      <span className="text-[11px] text-cyan-300 font-bold block font-sans">Projected Outflow</span>
                      <span className="text-2xl font-black text-cyan-200">
                        ₹{projection.projected_annual_cost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </span>
                      <span className="text-[10px] text-teal-400 font-sans block mt-0.5">
                        &darr; {projection.percentage_reduction}% Annual Reduction
                      </span>
                    </div>
                  </div>
                </div>

                {/* Applied Safeguards List */}
                {projection.safeguards_applied.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-[#164B68]/80 flex flex-wrap items-center gap-2 text-[11px] text-[#A9BBCD]">
                    <span className="font-semibold text-[#F4F7FB]">Applied Engine Safeguards:</span>
                    {projection.safeguards_applied.map((s, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded bg-[#0B3152] border border-[#164B68]/60 text-[#F4F7FB]"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </section>
            )}

            {/* Split View: Left (Opportunities Selector) & Right (Save Scenario & Saved Scenarios) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Left Column (2 Cols): Opportunities List */}
              <div className="lg:col-span-2 flex flex-col gap-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-semibold text-white">Savings Opportunities</h3>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-[#0B3152] text-[#A9BBCD]">
                      {filteredOpportunities.length} Found
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={selectAll}
                      className="px-2.5 py-1 rounded-md text-xs text-cyan-400 hover:bg-cyan-950/40 border border-cyan-800/40 transition-colors"
                    >
                      Select All
                    </button>
                    <button
                      onClick={clearSelection}
                      className="px-2.5 py-1 rounded-md text-xs text-[#A9BBCD] hover:bg-[#0B3152] border border-[#164B68] transition-colors"
                    >
                      Deselect All
                    </button>

                    <select
                      value={filterType}
                      onChange={(e) => setFilterType(e.target.value)}
                      className="px-2.5 py-1 rounded-md bg-[#082746] border border-[#164B68] text-xs text-[#F4F7FB] focus:outline-none focus:border-cyan-500"
                    >
                      <option value="ALL">All Types</option>
                      <option value="PRICE_INCREASE">Price Increases</option>
                      <option value="POTENTIALLY_UNUSED">Unused Services</option>
                      <option value="CATEGORY_DUPLICATE">Duplicates</option>
                    </select>
                  </div>
                </div>

                {/* Opportunities Cards */}
                <div className="space-y-3">
                  {filteredOpportunities.map((opp) => {
                    const isChecked = selectedIds.includes(opp.id);
                    return (
                      <div
                        key={opp.id}
                        onClick={() => toggleOpportunity(opp.id)}
                        className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                          isChecked
                            ? "bg-[#031B38]/90 border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.08)]"
                            : "bg-[#082746]/40 border-[#164B68]/80 opacity-75 hover:opacity-100 hover:border-[#164B68]"
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => toggleOpportunity(opp.id)}
                            className="mt-1 w-4 h-4 rounded text-cyan-500 focus:ring-cyan-500 border-[#164B68] bg-[#011633] cursor-pointer"
                          />
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-white text-sm">
                                {opp.commitment_name}
                              </span>
                              <span
                                className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                                  opp.opportunity_type === "PRICE_INCREASE"
                                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                                    : opp.opportunity_type === "POTENTIALLY_UNUSED"
                                    ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
                                    : "bg-indigo-500/10 text-indigo-400 border border-indigo-500/30"
                                }`}
                              >
                                {opp.opportunity_type.replace("_", " ")}
                              </span>
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#0B3152] text-[#A9BBCD]">
                                {opp.classification}
                              </span>
                            </div>

                            <p className="text-xs text-[#F4F7FB] mt-1 max-w-lg leading-relaxed">
                              {opp.evidence_summary}
                            </p>

                            <div className="flex items-center gap-3 mt-2 text-[11px] text-[#A9BBCD]">
                              <span>Merchant: <strong className="text-[#F4F7FB]">{opp.merchant_name}</strong></span>
                              <span>Category: <strong className="text-[#F4F7FB]">{opp.category}</strong></span>
                              {opp.insight_id && (
                                <Link
                                  href={`/insights/${opp.insight_id}`}
                                  onClick={(e) => e.stopPropagation()}
                                  className="text-cyan-400 hover:underline"
                                >
                                  View Linked Insight &rarr;
                                </Link>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Cost & Savings Figures */}
                        <div className="text-right font-mono flex-shrink-0">
                          <span className="text-sm font-bold text-teal-400 block">
                            Save ₹{opp.potential_annual_saving.toLocaleString("en-IN", { minimumFractionDigits: 2 })}/yr
                          </span>
                          <span className="text-xs text-[#A9BBCD] block">
                            ₹{opp.potential_monthly_saving.toLocaleString("en-IN", { minimumFractionDigits: 2 })}/mo
                          </span>
                          <span className="text-[10px] text-[#A9BBCD] block mt-1">
                            Current: ₹{opp.current_annual_cost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}/yr
                          </span>
                        </div>
                      </div>
                    );
                  })}

                  {filteredOpportunities.length === 0 && (
                    <div className="p-8 text-center rounded-xl border border-[#164B68] text-[#A9BBCD] text-xs">
                      No savings opportunities matching the selected filter.
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column (1 Col): Save Scenario & Saved Scenarios List */}
              <div className="flex flex-col gap-6">
                {/* Save Scenario Form Card */}
                <div className="rounded-xl border border-[#164B68] bg-[#082746]/50 p-5 flex flex-col gap-4">
                  <div>
                    <h3 className="text-sm font-semibold text-white">Save Current Scenario</h3>
                    <p className="text-xs text-[#A9BBCD] mt-0.5">
                      Persist this {selectedIds.length}-item simulation for tracking or future review.
                    </p>
                  </div>

                  {saveSuccessMessage && (
                    <div className="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-xs font-medium">
                      {saveSuccessMessage}
                    </div>
                  )}

                  <form onSubmit={handleSaveScenario} className="space-y-3">
                    <div>
                      <label className="text-[11px] text-[#A9BBCD] font-medium block mb-1">
                        Scenario Name *
                      </label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. Q4 Budget Optimization"
                        value={scenarioName}
                        onChange={(e) => setScenarioName(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg bg-[#011633] border border-[#164B68] text-xs text-[#F4F7FB] placeholder:text-[#A9BBCD] focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div>
                      <label className="text-[11px] text-[#A9BBCD] font-medium block mb-1">
                        Description / Notes
                      </label>
                      <textarea
                        rows={2}
                        placeholder="Optional notes or assumptions..."
                        value={scenarioDesc}
                        onChange={(e) => setScenarioDesc(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg bg-[#011633] border border-[#164B68] text-xs text-[#F4F7FB] placeholder:text-[#A9BBCD] focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={savingScenario || selectedIds.length === 0}
                      className="w-full py-2.5 rounded-lg bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 disabled:opacity-50 text-slate-950 font-bold text-xs tracking-wide transition-all shadow-[0_0_15px_rgba(6,182,212,0.2)]"
                    >
                      {savingScenario ? "Saving Scenario..." : "Save Simulation Scenario"}
                    </button>
                  </form>
                </div>

                {/* Saved Scenarios List */}
                <div className="rounded-xl border border-[#164B68] bg-[#082746]/50 p-5 flex flex-col gap-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-white">Saved Scenarios</h3>
                    <span className="text-xs text-[#A9BBCD] font-mono">{savedScenarios.length}</span>
                  </div>

                  <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
                    {savedScenarios.map((scen) => (
                      <div
                        key={scen.id}
                        className="p-3 rounded-lg bg-[#011633]/80 border border-[#164B68] text-xs flex flex-col gap-2"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <span className="font-semibold text-white block">{scen.name}</span>
                            {scen.description && (
                              <p className="text-[11px] text-[#A9BBCD] mt-0.5">{scen.description}</p>
                            )}
                          </div>
                          <button
                            onClick={() => handleDeleteScenario(scen.id)}
                            className="text-[#A9BBCD] hover:text-rose-400 text-xs font-mono transition-colors"
                            title="Delete scenario"
                          >
                            &times;
                          </button>
                        </div>

                        <div className="pt-2 border-t border-slate-900 flex items-center justify-between text-[11px] font-mono">
                          <span className="text-teal-400 font-bold">
                            Save ₹{scen.annual_savings.toLocaleString("en-IN", { minimumFractionDigits: 2 })}/yr
                          </span>
                          <span className="text-cyan-300">
                            &darr; {scen.percentage_reduction}%
                          </span>
                        </div>
                      </div>
                    ))}

                    {savedScenarios.length === 0 && (
                      <p className="text-xs text-[#A9BBCD] text-center py-4">
                        No saved simulation scenarios yet.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
