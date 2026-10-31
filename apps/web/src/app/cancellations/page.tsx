"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import PayScopeLogo from "@/components/brand/PayScopeLogo";

interface PlaybookStep {
  id: string;
  step_number: number;
  title: string;
  instruction: string;
  warning?: string | null;
  verification_tip?: string | null;
  is_completed: boolean;
}

interface Playbook {
  playbook_key: string;
  title: string;
  payment_mechanism: string;
  guidance_type: string;
  official_source_url?: string | null;
  source_verification_date?: string | null;
  region: string;
  summary: string;
  important_warnings: string[];
  steps: PlaybookStep[];
  friction_level: string;
  friction_notes?: string | null;
}

interface CancellationCase {
  id: string;
  commitment_id: string;
  commitment_name: string;
  merchant_id?: string | null;
  merchant_name?: string | null;
  payment_mechanism: string;
  playbook_key: string;
  status: string;
  completed_steps: string[];
  user_notes?: string | null;
  evidence_references?: string | null;
  user_reported_at?: string | null;
  verified_at?: string | null;
  verification_notes?: string | null;
  created_at: string;
  playbook?: Playbook | null;
}

interface CommitmentOption {
  id: string;
  display_name: string;
  cadence: string;
  representative_amount?: number | null;
  status: string;
}

function CancellationCentreContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedCommitmentId = searchParams.get("commitment_id");

  const [cases, setCases] = useState<CancellationCase[]>([]);
  const [commitments, setCommitments] = useState<CommitmentOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Case Modal / Drawer
  const [selectedCommitmentId, setSelectedCommitmentId] = useState<string>(preselectedCommitmentId || "");
  const [selectedMechanism, setSelectedMechanism] = useState<string>("UPI_AUTOPAY");
  const [userNotes, setUserNotes] = useState<string>("");
  const [creatingCase, setCreatingCase] = useState(false);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  useEffect(() => {
    let ignore = false;
    async function loadData() {
      try {
        const [casesRes, commsRes] = await Promise.all([
          fetch(`${apiBase}/api/v1/cancellations`),
          fetch(`${apiBase}/api/v1/commitments`),
        ]);

        if (!ignore && casesRes.ok) {
          const cData = await casesRes.json();
          setCases(cData);
        }
        if (!ignore && commsRes.ok) {
          const commData = await commsRes.json();
          setCommitments(commData.items || commData);
        }
      } catch (err) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load cancellation cases");
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
  }, [apiBase]);

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCommitmentId) return;

    setCreatingCase(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/cancellations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          commitment_id: selectedCommitmentId,
          payment_mechanism: selectedMechanism,
          user_notes: userNotes || undefined,
        }),
      });

      if (res.ok) {
        const newCase = await res.json();
        setUserNotes("");
        router.push(`/cancellations/${newCase.id}`);
      } else {
        const errJson = await res.json();
        setError(errJson.detail || "Failed to create cancellation case.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create cancellation case.");
    } finally {
      setCreatingCase(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "VERIFIED_CANCELLED":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">Verified Cancelled</span>;
      case "USER_REPORTED_CANCELLED":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">User Reported</span>;
      case "IN_PROGRESS":
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-[#00B8C7]/15 text-[#00E0E0] border border-[#00B8C7]/30">In Progress</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">Not Started</span>;
    }
  };

  const getMechanismBadge = (mech: string) => {
    const formatted = mech.replace("_", " ");
    return (
      <span className="px-2 py-0.5 rounded text-[11px] font-mono tracking-wide bg-[#082746] text-[#00E0E0] border border-[#164B68]">
        {formatted}
      </span>
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#011633] text-[#F4F7FB] selection:bg-[#F08A00] selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-[#164B68] bg-[#031B38]/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="hover:opacity-90 transition-opacity">
              <PayScopeLogo variant="navbar" />
            </Link>
            <span className="text-[#164B68]">/</span>
            <span className="text-sm font-semibold text-[#FFA52B]">Cancellation Centre</span>
          </div>

          <nav className="flex items-center gap-3 text-xs">
            <Link href="/dashboard" className="px-3 py-1.5 rounded-lg border border-[#164B68] bg-[#082746] text-[#A9BBCD] hover:text-white hover:border-[#00B8C7] transition-colors">
              Dashboard
            </Link>
            <Link href="/commitments" className="px-3 py-1.5 rounded-lg border border-[#164B68] bg-[#082746] text-[#A9BBCD] hover:text-white hover:border-[#00B8C7] transition-colors">
              Commitments
            </Link>
            <Link href="/savings" className="px-3 py-1.5 rounded-lg border border-[#164B68] bg-[#082746] text-[#A9BBCD] hover:text-white hover:border-[#00B8C7] transition-colors">
              Savings
            </Link>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
        {/* Error notification */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="font-bold cursor-pointer">✕</button>
          </div>
        )}

        {/* Hero Notice */}
        <div className="rounded-2xl bg-gradient-to-br from-[#082746] via-[#031B38] to-[#011633] border border-[#164B68] p-6 sm:p-8 flex flex-col gap-4 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-[#F08A00]/15 text-[#FFA52B] border border-[#F08A00]/30 mb-2">
                User-Guided Cancellation Playbooks
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                Mechanism-Aware Cancellation Centre
              </h1>
              <p className="text-sm text-[#A9BBCD] mt-1 max-w-2xl">
                Structured, step-by-step guidance to stop recurring commitments across UPI AutoPay, Card Standing Instructions, and e-NACH mandates.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-[#031B38] border border-[#164B68] text-xs text-[#A9BBCD] max-w-sm flex items-start gap-2.5">
              <span className="text-[#FFA52B] font-bold text-base leading-none">🛡</span>
              <div>
                <strong className="text-white block font-medium">Informational Safety Notice:</strong>
                PayScope provides verified procedural guidance only. We do not access banking credentials, execute debit cancellations, or revoke mandates directly.
              </div>
            </div>
          </div>
        </div>

        {/* Start Cancellation Section */}
        <div className="rounded-2xl bg-[#082746] border border-[#164B68] p-6">
          <h2 className="text-lg font-bold text-[#FFA52B] mb-4 flex items-center gap-2">
            <span>Start Cancellation Guidance</span>
          </h2>
          <form onSubmit={handleCreateCase} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <div className="md:col-span-2 flex flex-col gap-1.5">
              <label htmlFor="commitment-select" className="text-xs font-medium text-[#A9BBCD]">Select Recurring Commitment</label>
              <select
                id="commitment-select"
                aria-label="Select Recurring Commitment"
                value={selectedCommitmentId}
                onChange={(e) => setSelectedCommitmentId(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#031B38] border border-[#164B68] text-sm text-white focus:outline-none focus:border-[#00B8C7]"
              >
                <option value="">-- Choose a recurring commitment --</option>
                {commitments.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.display_name} ({c.cadence}) {c.representative_amount ? `- ₹${c.representative_amount}` : ""}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="payment-mechanism-select" className="text-xs font-medium text-[#A9BBCD]">Payment Channel</label>
              <select
                id="payment-mechanism-select"
                aria-label="Payment Channel"
                value={selectedMechanism}
                onChange={(e) => setSelectedMechanism(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#031B38] border border-[#164B68] text-sm text-white focus:outline-none focus:border-[#00B8C7]"
              >
                <option value="UPI_AUTOPAY">UPI AutoPay</option>
                <option value="CARD_SI">Card Standing Instruction</option>
                <option value="E_NACH">e-NACH / Electronic Mandate</option>
                <option value="OTHER">Other / Provider Settings</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={creatingCase || !selectedCommitmentId}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#F08A00] to-[#FFA52B] hover:brightness-110 text-[#011633] font-bold text-sm transition-all disabled:opacity-50 cursor-pointer shadow-lg shadow-[#F08A00]/20"
            >
              {creatingCase ? "Loading Playbook..." : "Get Playbook →"}
            </button>
          </form>
        </div>

        {/* Existing Cancellation Cases */}
        <div className="rounded-2xl bg-[#082746] border border-[#164B68] p-6 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">Your Cancellation Cases</h2>
            <span className="text-xs text-[#A9BBCD]">{cases.length} active or recorded cases</span>
          </div>

          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center gap-3 text-[#A9BBCD]">
              <div className="w-6 h-6 border-2 border-[#00B8C7] border-t-transparent rounded-full animate-spin" />
              <span className="text-xs">Loading cases...</span>
            </div>
          ) : cases.length === 0 ? (
            <div className="py-12 border border-dashed border-[#164B68] rounded-xl text-center flex flex-col items-center gap-2">
              <span className="text-2xl">📋</span>
              <p className="text-sm font-semibold text-white">No Cancellation Cases Active</p>
              <p className="text-xs text-[#A9BBCD] max-w-sm">
                Select any recurring commitment above to generate a tailored, mechanism-aware cancellation playbook.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-[#164B68] text-xs font-semibold text-[#A9BBCD]">
                    <th className="py-3 px-4">Commitment</th>
                    <th className="py-3 px-4">Mechanism</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Progress</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#164B68]/50">
                  {cases.map((c) => {
                    const totalSteps = c.playbook?.steps?.length || 5;
                    const completed = c.completed_steps?.length || 0;
                    const pct = Math.min(100, Math.round((completed / totalSteps) * 100));

                    return (
                      <tr key={c.id} className="hover:bg-[#0B3152]/40 transition-colors">
                        <td className="py-4 px-4 font-semibold text-white">
                          <Link href={`/cancellations/${c.id}`} className="hover:text-[#00E0E0] transition-colors">
                            {c.commitment_name}
                          </Link>
                          {c.user_reported_at && (
                            <div className="text-[11px] text-[#A9BBCD] mt-0.5">
                              Reported: {new Date(c.user_reported_at).toLocaleDateString()}
                            </div>
                          )}
                        </td>
                        <td className="py-4 px-4">{getMechanismBadge(c.payment_mechanism)}</td>
                        <td className="py-4 px-4">{getStatusBadge(c.status)}</td>
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-2">
                            <div className="w-24 h-2 rounded-full bg-[#031B38] overflow-hidden border border-[#164B68]">
                              <div
                                className="h-full bg-gradient-to-r from-[#00B8C7] to-[#00E0E0] transition-all"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <span className="text-xs text-[#A9BBCD] font-mono">{pct}%</span>
                          </div>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <Link
                            href={`/cancellations/${c.id}`}
                            className="inline-flex items-center px-3 py-1.5 rounded-lg border border-[#00B8C7]/30 bg-[#00B8C7]/10 text-[#00E0E0] hover:bg-[#00B8C7]/20 text-xs font-semibold transition-colors"
                          >
                            View Checklist →
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function CancellationCentrePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#011633] text-white p-8">Loading Cancellation Centre...</div>}>
      <CancellationCentreContent />
    </Suspense>
  );
}
