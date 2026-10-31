"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
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

interface CancellationCaseDetail {
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

export default function CancellationCaseDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const unwrappedParams = use(params);
  const caseId = unwrappedParams.id;

  const [caseDetail, setCaseDetail] = useState<CancellationCaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Modal / Inputs
  const [reportingCancelled, setReportingCancelled] = useState(false);
  const [evidenceText, setEvidenceText] = useState("");
  const [reportingNotes, setReportingNotes] = useState("");
  const [submittingAction, setSubmittingAction] = useState(false);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  useEffect(() => {
    let ignore = false;
    async function loadCase() {
      try {
        const res = await fetch(`${apiBase}/api/v1/cancellations/${caseId}`);
        if (!ignore && res.ok) {
          const data = await res.json();
          setCaseDetail(data);
        } else if (!ignore) {
          setError("Failed to locate cancellation case.");
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

    loadCase();
    return () => {
      ignore = true;
    };
  }, [apiBase, caseId]);

  const handleStepComplete = async (stepId: string) => {
    try {
      const res = await fetch(`${apiBase}/api/v1/cancellations/${caseId}/complete-step`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step_id: stepId }),
      });
      if (res.ok) {
        const updated = await res.json();
        setCaseDetail(updated);
        setActionSuccess("Step marked as completed!");
      }
    } catch {
      setError("Failed to update step.");
    }
  };

  const handleReportCancelled = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingAction(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/cancellations/${caseId}/report-cancelled`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          evidence_references: evidenceText || undefined,
          user_notes: reportingNotes || undefined,
        }),
      });
      if (res.ok) {
        const updated = await res.json();
        setCaseDetail(updated);
        setReportingCancelled(false);
        setActionSuccess("Cancellation reported successfully. Post-cancellation monitors are now active!");
      }
    } catch {
      setError("Failed to record cancellation.");
    } finally {
      setSubmittingAction(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#011633] flex items-center justify-center text-[#A9BBCD]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-6 h-6 border-2 border-[#00B8C7] border-t-transparent rounded-full animate-spin" />
          <span className="text-sm">Loading cancellation playbook...</span>
        </div>
      </div>
    );
  }

  if (error || !caseDetail) {
    return (
      <div className="min-h-screen bg-[#011633] text-white flex items-center justify-center p-4">
        <div className="max-w-md w-full p-6 rounded-2xl bg-[#082746] border border-[#164B68] text-center flex flex-col gap-4">
          <h2 className="text-lg font-bold text-rose-400">Case Not Found</h2>
          <p className="text-xs text-[#A9BBCD]">{error || "Could not retrieve details."}</p>
          <Link href="/cancellations" className="px-4 py-2 rounded-xl bg-[#031B38] border border-[#164B68] text-xs font-semibold text-white hover:border-[#00B8C7]">
            ← Return to Cancellation Centre
          </Link>
        </div>
      </div>
    );
  }

  const pb = caseDetail.playbook;
  const completedSteps = caseDetail.completed_steps || [];
  const totalSteps = pb?.steps?.length || 5;
  const progressPct = Math.min(100, Math.round((completedSteps.length / totalSteps) * 100));

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
            <Link href="/cancellations" className="text-sm font-medium text-[#A9BBCD] hover:text-white transition-colors">
              Cancellation Centre
            </Link>
            <span className="text-[#164B68]">/</span>
            <span className="text-sm font-semibold text-[#FFA52B] truncate max-w-xs">{caseDetail.commitment_name}</span>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href={`/commitments/${caseDetail.commitment_id}`}
              className="px-3 py-1.5 rounded-lg border border-[#164B68] bg-[#082746] text-[#A9BBCD] hover:text-white text-xs font-medium transition-colors"
            >
              View Commitment
            </Link>
          </div>
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-6">
        {/* Banner Messages */}
        {actionSuccess && (
          <div className="p-4 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-sm flex items-center justify-between">
            <span>{actionSuccess}</span>
            <button onClick={() => setActionSuccess(null)} className="text-emerald-400 hover:text-emerald-200 text-xs font-bold cursor-pointer">
              ✕
            </button>
          </div>
        )}

        {/* Case Header Card */}
        <div className="rounded-2xl bg-[#082746] border border-[#164B68] p-6 sm:p-8 flex flex-col gap-4 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2.5 py-0.5 rounded text-xs font-mono font-semibold bg-[#031B38] text-[#00E0E0] border border-[#164B68]">
                  {caseDetail.payment_mechanism.replace("_", " ")}
                </span>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                  caseDetail.status === "VERIFIED_CANCELLED" ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30" :
                  caseDetail.status === "USER_REPORTED_CANCELLED" ? "bg-amber-500/15 text-amber-400 border border-amber-500/30" :
                  "bg-[#00B8C7]/15 text-[#00E0E0] border border-[#00B8C7]/30"
                }`}>
                  {caseDetail.status.replace(/_/g, " ")}
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
                {pb?.title || `Cancel ${caseDetail.commitment_name}`}
              </h1>
              <p className="text-sm text-[#A9BBCD] mt-1">
                {pb?.summary}
              </p>
            </div>

            <div className="flex flex-col sm:items-end gap-2 shrink-0">
              {caseDetail.status !== "USER_REPORTED_CANCELLED" && caseDetail.status !== "VERIFIED_CANCELLED" && (
                <button
                  onClick={() => setReportingCancelled(true)}
                  className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-[#F08A00] to-[#FFA52B] hover:brightness-110 text-[#011633] font-bold text-xs transition-all cursor-pointer shadow-lg shadow-[#F08A00]/20"
                >
                  Report Cancellation Completed →
                </button>
              )}
              {caseDetail.user_reported_at && (
                <span className="text-xs text-amber-400 font-mono">
                  Reported: {new Date(caseDetail.user_reported_at).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-4 pt-4 border-t border-[#164B68] flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#A9BBCD] font-medium">Checklist Progress</span>
              <span className="text-white font-mono font-bold">{progressPct}% ({completedSteps.length}/{totalSteps} steps completed)</span>
            </div>
            <div className="w-full h-2.5 rounded-full bg-[#031B38] overflow-hidden border border-[#164B68]">
              <div
                className="h-full bg-gradient-to-r from-[#00B8C7] to-[#00E0E0] transition-all duration-300"
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>
        </div>

        {/* Source Verification Box */}
        {pb?.official_source_url && (
          <div className="p-4 rounded-xl bg-[#031B38] border border-[#164B68] flex items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-2 text-[#A9BBCD]">
              <span className="text-emerald-400 font-bold">✓</span>
              <span>
                Verified Official Source:{" "}
                <a
                  href={pb.official_source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[#00E0E0] underline hover:text-white"
                >
                  {pb.official_source_url}
                </a>
              </span>
            </div>
            {pb.source_verification_date && (
              <span className="text-[#A9BBCD] font-mono shrink-0">
                Verified: {pb.source_verification_date}
              </span>
            )}
          </div>
        )}

        {/* Important Warnings */}
        {pb?.important_warnings && pb.important_warnings.length > 0 && (
          <div className="rounded-xl bg-amber-500/10 border border-amber-500/30 p-4 flex flex-col gap-2">
            <h3 className="text-xs font-bold text-[#FFA52B] flex items-center gap-1.5 uppercase tracking-wide">
              <span>⚠ Important Procedural Notice</span>
            </h3>
            <ul className="list-disc list-inside text-xs text-[#F4F7FB]/90 space-y-1">
              {pb.important_warnings.map((warn, idx) => (
                <li key={idx}>{warn}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Step-by-Step Checklist */}
        <div className="rounded-2xl bg-[#082746] border border-[#164B68] p-6 flex flex-col gap-4">
          <h2 className="text-lg font-bold text-white">Actionable Cancellation Checklist</h2>

          <div className="space-y-4">
            {pb?.steps.map((step) => {
              const isDone = completedSteps.includes(step.id);
              return (
                <div
                  key={step.id}
                  className={`p-4 rounded-xl border transition-all ${
                    isDone
                      ? "bg-[#031B38]/60 border-emerald-500/30 opacity-80"
                      : "bg-[#031B38] border-[#164B68] hover:border-[#00B8C7]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <button
                        onClick={() => handleStepComplete(step.id)}
                        className={`mt-0.5 w-6 h-6 rounded-lg border flex items-center justify-center font-bold text-xs transition-colors cursor-pointer shrink-0 ${
                          isDone
                            ? "bg-emerald-500 text-[#011633] border-emerald-400"
                            : "border-[#164B68] hover:border-[#00E0E0] text-transparent"
                        }`}
                      >
                        ✓
                      </button>
                      <div className="flex flex-col gap-1">
                        <span className={`text-sm font-semibold ${isDone ? "line-through text-[#A9BBCD]" : "text-white"}`}>
                          Step {step.step_number}: {step.title}
                        </span>
                        <p className="text-xs text-[#A9BBCD] leading-relaxed">
                          {step.instruction}
                        </p>
                        {step.warning && (
                          <div className="mt-1 text-[11px] text-amber-300 font-medium">
                            Note: {step.warning}
                          </div>
                        )}
                        {step.verification_tip && (
                          <div className="mt-0.5 text-[11px] text-[#00E0E0]">
                            Tip: {step.verification_tip}
                          </div>
                        )}
                      </div>
                    </div>

                    {!isDone && (
                      <button
                        onClick={() => handleStepComplete(step.id)}
                        className="px-3 py-1 rounded-lg border border-[#164B68] bg-[#082746] text-[11px] font-semibold text-[#00E0E0] hover:border-[#00B8C7] cursor-pointer shrink-0"
                      >
                        Mark Done
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Report Modal */}
        {reportingCancelled && (
          <div className="fixed inset-0 bg-[#011633]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="max-w-lg w-full bg-[#082746] border border-[#164B68] rounded-2xl p-6 shadow-2xl flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white">Record Cancellation Outcome</h3>
                <button
                  onClick={() => setReportingCancelled(false)}
                  className="text-[#A9BBCD] hover:text-white text-sm"
                >
                  ✕
                </button>
              </div>

              <p className="text-xs text-[#A9BBCD]">
                Recording this cancellation tells PayScope to flag any rogue post-cancellation debits on subsequent synthetic statements as anomalies.
              </p>

              <form onSubmit={handleReportCancelled} className="flex flex-col gap-4">
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="evidence-notes-input" className="text-xs font-semibold text-[#A9BBCD]">Evidence / Confirmation Reference</label>
                  <input
                    id="evidence-notes-input"
                    type="text"
                    placeholder="e.g. Email confirmation ref #88219 or UPI UMN screenshot"
                    value={evidenceText}
                    onChange={(e) => setEvidenceText(e.target.value)}
                    className="px-3.5 py-2.5 rounded-xl bg-[#031B38] border border-[#164B68] text-sm text-white focus:outline-none focus:border-[#00B8C7]"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label htmlFor="user-notes-input" className="text-xs font-semibold text-[#A9BBCD]">User Notes</label>
                  <textarea
                    id="user-notes-input"
                    rows={3}
                    placeholder="e.g. Cancelled via Google Pay AutoPay section; valid until end of month."
                    value={reportingNotes}
                    onChange={(e) => setReportingNotes(e.target.value)}
                    className="px-3.5 py-2.5 rounded-xl bg-[#031B38] border border-[#164B68] text-sm text-white focus:outline-none focus:border-[#00B8C7]"
                  />
                </div>

                <div className="flex items-center justify-end gap-3 mt-2">
                  <button
                    type="button"
                    onClick={() => setReportingCancelled(false)}
                    className="px-4 py-2 rounded-xl text-xs font-semibold text-[#A9BBCD] hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingAction}
                    className="px-4 py-2 rounded-xl bg-gradient-to-r from-[#F08A00] to-[#FFA52B] text-[#011633] font-bold text-xs hover:brightness-110 cursor-pointer"
                  >
                    {submittingAction ? "Saving..." : "Confirm Reported Cancellation"}
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
