"use client";

import React, { useState, useEffect, useCallback, useId } from "react";
import Link from "next/link";

interface SampleFile {
  filename: string;
  format: string;
  description: string;
  size_bytes: number;
  available: boolean;
  download_url: string;
}

interface RowErrorItem {
  row: number;
  column: string;
  value: string;
  reason: string;
}

interface PreviewRow {
  date?: string;
  timestamp?: string;
  descriptor?: string;
  event_type?: string;
  merchant_hint?: string;
  amount?: number | null;
  currency?: string | null;
  direction?: string;
  channel?: string;
  mechanism?: string;
  reference?: string | null;
  mandate_ref?: string | null;
  external_id?: string;
  is_duplicate?: boolean;
}

interface PreviewResponse {
  success: boolean;
  import_type: "statement" | "notifications";
  file_info: {
    filename: string;
    size_bytes: number;
    file_type: string;
    checksum_sha256?: string;
  };
  headers: string[];
  mapping?: Record<string, string>;
  available_targets?: string[];
  total_rows: number;
  valid_count: number;
  duplicate_count: number;
  invalid_count: number;
  errors: RowErrorItem[];
  preview_rows: PreviewRow[];
  error?: string;
}

interface ImportResult {
  success: boolean;
  import_id: string;
  status: string;
  filename: string;
  total_rows: number;
  accepted_count: number;
  duplicate_count: number;
  rejected_count: number;
  errors: RowErrorItem[];
}

interface ImportHistoryItem {
  id: string;
  filename: string;
  file_type: string;
  source_label: string;
  status: string;
  row_count: number;
  accepted_count: number;
  duplicate_count: number;
  rejected_count: number;
  created_at: string | null;
  finished_at: string | null;
  error_summary: string | null;
}

export default function UploadPage() {
  const fileInputId = useId();
  // State
  const [syntheticConfirmed, setSyntheticConfirmed] = useState<boolean>(false);
  const [importType, setImportType] = useState<"statement" | "notifications">("statement");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  // Sample files
  const [sampleFiles, setSampleFiles] = useState<SampleFile[]>([]);
  const [loadingSamples, setLoadingSamples] = useState<boolean>(false);

  // Preview & Processing
  const [loadingPreview, setLoadingPreview] = useState<boolean>(false);
  const [previewData, setPreviewData] = useState<PreviewResponse | null>(null);
  const [columnOverrides, setColumnOverrides] = useState<Record<string, string>>({});
  const [previewError, setPreviewError] = useState<string | null>(null);

  // Execution
  const [importing, setImporting] = useState<boolean>(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);

  // History
  const [historyItems, setHistoryItems] = useState<ImportHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  // Fetch sample files on demand
  const fetchSampleFiles = useCallback(async () => {
    setLoadingSamples(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/demo/sample-files`);
      if (res.ok) {
        const data: SampleFile[] = await res.json();
        setSampleFiles(data);
      }
    } catch {
      // Ignore background sample loading errors
    } finally {
      setLoadingSamples(false);
    }
  }, [apiBase]);

  // Fetch import history on demand
  const fetchHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/imports?limit=20`);
      if (res.ok) {
        const data = await res.json();
        setHistoryItems(data.items || []);
      }
    } catch {
      // Ignore background history loading errors
    } finally {
      setLoadingHistory(false);
    }
  }, [apiBase]);

  useEffect(() => {
    let ignore = false;
    async function loadInitialData() {
      try {
        const [resSamples, resHist] = await Promise.all([
          fetch(`${apiBase}/api/v1/demo/sample-files`),
          fetch(`${apiBase}/api/v1/imports?limit=20`),
        ]);
        if (!ignore && resSamples.ok) {
          const data: SampleFile[] = await resSamples.json();
          setSampleFiles(data);
        }
        if (!ignore && resHist.ok) {
          const data = await resHist.json();
          setHistoryItems(data.items || []);
        }
      } catch {
        // Ignore background initialization errors
      }
    }
    loadInitialData();
    return () => {
      ignore = true;
    };
  }, [apiBase]);

  // Handle preview generation
  const handleGeneratePreview = async (
    fileToPreview: File,
    typeToPreview: "statement" | "notifications",
    overrides?: Record<string, string>
  ) => {
    if (!syntheticConfirmed) {
      setPreviewError("Please check the synthetic data confirmation box before uploading.");
      return;
    }

    setLoadingPreview(true);
    setPreviewError(null);
    setPreviewData(null);
    setImportResult(null);
    setExecutionError(null);

    const formData = new FormData();
    formData.append("file", fileToPreview);
    formData.append("import_type", typeToPreview);
    formData.append("synthetic_confirmed", "true");
    if (overrides && Object.keys(overrides).length > 0) {
      formData.append("column_overrides", JSON.stringify(overrides));
    }

    try {
      const res = await fetch(`${apiBase}/api/v1/imports/preview`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        setPreviewError(data.detail || data.error || "Failed to generate preview.");
      } else {
        setPreviewData(data);
        if (data.mapping) {
          setColumnOverrides(data.mapping);
        }
      }
    } catch (err) {
      setPreviewError(err instanceof Error ? err.message : "Failed to connect to backend server.");
    } finally {
      setLoadingPreview(false);
    }
  };

  // File selection
  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    // Auto-detect import type from extension
    const ext = file.name.split(".").pop()?.toLowerCase();
    const detectedType = ext === "json" ? "notifications" : "statement";
    setImportType(detectedType);

    if (syntheticConfirmed) {
      handleGeneratePreview(file, detectedType);
    }
  };

  // Re-run preview when column mapping changes
  const handleApplyMapping = () => {
    if (selectedFile) {
      handleGeneratePreview(selectedFile, importType, columnOverrides);
    }
  };

  // Execute actual import
  const handleConfirmImport = async () => {
    if (!selectedFile || !syntheticConfirmed) return;

    setImporting(true);
    setExecutionError(null);

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("import_type", importType);
    formData.append("synthetic_confirmed", "true");
    if (Object.keys(columnOverrides).length > 0) {
      formData.append("column_overrides", JSON.stringify(columnOverrides));
    }

    try {
      const res = await fetch(`${apiBase}/api/v1/imports`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        setExecutionError(data.detail || data.error || "Failed to persist import.");
      } else {
        setImportResult(data);
        fetchHistory(); // Refresh history table
      }
    } catch (err) {
      setExecutionError(err instanceof Error ? err.message : "Network error during import persistence.");
    } finally {
      setImporting(false);
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
            <span className="text-sm font-medium text-slate-300">Upload Centre</span>
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
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-colors"
            >
              Merchants
            </Link>
            <Link
              href="/merchant-review"
              className="text-xs px-3 py-1.5 rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 transition-colors"
            >
              Review Queue
            </Link>
            <Link
              href="/"
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-colors"
            >
              Home
            </Link>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              Synthetic Prototype Mode
            </span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
        {/* Title & Introduction */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Upload Centre & Ingestion Pipeline
          </h1>
          <p className="mt-1 text-sm sm:text-base text-slate-400">
            Ingest synthetic bank statements (CSV, XLSX) or simulated payment notifications (JSON) to feed the MandateLens recurring intelligence engine.
          </p>
        </div>

        {/* SECTION A: Synthetic Data Disclaimer Banner */}
        <section className="rounded-xl border border-amber-500/40 bg-gradient-to-r from-amber-950/40 to-slate-900/60 p-5 shadow-sm flex flex-col gap-4">
          <div className="flex items-start gap-3.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0 mt-0.5">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-amber-300">
                Prototype Constraint: Strict Synthetic Data Enforcement
              </h3>
              <p className="text-xs text-amber-200/80 leading-relaxed">
                MandateLens is a developmental prototype designed for research and testing. It operates solely on synthetic or anonymised test fixtures. <strong>Do NOT upload real bank statements, real credit card bills, or actual financial records containing personally identifiable data.</strong>
              </p>
            </div>
          </div>

          <label className="flex items-center gap-3 pt-2 border-t border-amber-500/20 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={syntheticConfirmed}
              onChange={(e) => {
                setSyntheticConfirmed(e.target.checked);
                if (e.target.checked && selectedFile && !previewData) {
                  handleGeneratePreview(selectedFile, importType);
                }
              }}
              className="w-4 h-4 rounded border-amber-500/50 bg-slate-950 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-slate-950 cursor-pointer"
            />
            <span className="text-xs sm:text-sm font-medium text-slate-200">
              I explicitly confirm that this file contains <span className="text-amber-300 font-semibold">ONLY synthetic demo data</span> and no real personal financial records.
            </span>
          </label>
        </section>

        {/* SECTION B: Sample Dataset Downloads */}
        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                Download Synthetic Demo Files
              </h2>
              <p className="text-xs text-slate-400">
                Ready-to-use synthetic test files containing 12 distinct recurring payment scenarios and 80+ records.
              </p>
            </div>
            <button
              onClick={fetchSampleFiles}
              disabled={loadingSamples}
              className="text-xs px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-750 transition-colors w-fit"
            >
              {loadingSamples ? "Refreshing..." : "Check Status"}
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {sampleFiles.map((sf) => (
              <a
                key={sf.filename}
                href={`${apiBase}${sf.download_url}`}
                download
                className="group p-4 rounded-lg border border-slate-800 bg-slate-950/70 hover:border-emerald-500/50 hover:bg-slate-900/80 transition-all flex flex-col justify-between gap-3"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
                      {sf.format}
                    </span>
                    <span className="text-xs text-slate-500 font-mono">
                      {sf.size_bytes ? `${Math.round(sf.size_bytes / 1024)} KB` : "Ready"}
                    </span>
                  </div>
                  <h4 className="text-xs font-semibold text-white group-hover:text-emerald-300 transition-colors break-all">
                    {sf.filename}
                  </h4>
                  <p className="text-[11px] text-slate-400 line-clamp-2">
                    {sf.description}
                  </p>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium pt-2 border-t border-slate-800/80">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  <span>Download File</span>
                </div>
              </a>
            ))}
          </div>
        </section>

        {/* SECTION C & D: Import Configuration & Drag/Drop Upload */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Import Type & Settings */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-5">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              1. Import Specification
            </h3>

            {/* Type selector */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-300">File Ingestion Category</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setImportType("statement");
                    setPreviewData(null);
                  }}
                  className={`p-3 rounded-lg border text-left flex flex-col gap-1 transition-all ${
                    importType === "statement"
                      ? "border-emerald-500 bg-emerald-500/10 text-white"
                      : "border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  <span className="text-xs font-semibold">Bank Statement</span>
                  <span className="text-[11px] text-slate-400">CSV or Excel (XLSX)</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setImportType("notifications");
                    setPreviewData(null);
                  }}
                  className={`p-3 rounded-lg border text-left flex flex-col gap-1 transition-all ${
                    importType === "notifications"
                      ? "border-emerald-500 bg-emerald-500/10 text-white"
                      : "border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  <span className="text-xs font-semibold">Notifications</span>
                  <span className="text-[11px] text-slate-400">JSON payload</span>
                </button>
              </div>
            </div>

            {/* File guidelines info */}
            <div className="rounded-lg bg-slate-950/80 border border-slate-800/80 p-3 text-xs text-slate-400 space-y-2">
              <div className="flex justify-between">
                <span>Maximum File Size:</span>
                <span className="text-slate-200 font-mono">10 MB</span>
              </div>
              <div className="flex justify-between">
                <span>Accepted Formats:</span>
                <span className="text-slate-200 font-mono">.csv, .xlsx, .json</span>
              </div>
              <div className="flex justify-between">
                <span>Idempotency Check:</span>
                <span className="text-emerald-400 font-medium">Enabled</span>
              </div>
            </div>
          </div>

          {/* Right 2 Columns: File Dropzone */}
          <div className="lg:col-span-2 rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col justify-between gap-5">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              2. Select or Drop File
            </h3>

            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragging(false);
                if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                  handleFileSelect(e.dataTransfer.files[0]);
                }
              }}
              className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center gap-3 transition-colors ${
                isDragging
                  ? "border-emerald-500 bg-emerald-500/5"
                  : selectedFile
                  ? "border-emerald-500/50 bg-slate-950/60"
                  : "border-slate-800 hover:border-slate-700 bg-slate-950/40"
              }`}
            >
              <div className="w-12 h-12 rounded-full bg-slate-800/80 flex items-center justify-center text-slate-400">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>

              {selectedFile ? (
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-white break-all">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-slate-400 font-mono">
                    {(selectedFile.size / 1024).toFixed(1)} KB — {selectedFile.type || "unknown mime"}
                  </p>
                  <button
                    onClick={() => {
                      setSelectedFile(null);
                      setPreviewData(null);
                      setPreviewError(null);
                    }}
                    className="text-xs text-rose-400 hover:underline pt-2 block mx-auto"
                  >
                    Remove File
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm text-slate-300">
                    Drag and drop your statement or notification file here, or browse
                  </p>
                  <label
                    htmlFor={fileInputId}
                    className="inline-block px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-colors cursor-pointer shadow-sm"
                  >
                    Select File
                  </label>
                  <input
                    id={fileInputId}
                    type="file"
                    accept=".csv,.xlsx,.json"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        handleFileSelect(e.target.files[0]);
                      }
                    }}
                    className="hidden"
                  />
                  <p className="text-[11px] text-slate-500">
                    Supports CSV, XLSX, and JSON up to 10 MB.
                  </p>
                </div>
              )}
            </div>

            {/* Error alerts */}
            {previewError && (
              <div className="rounded-lg bg-rose-950/40 border border-rose-800/60 p-3 text-xs text-rose-300 flex items-center justify-between">
                <span>{previewError}</span>
                <button onClick={() => setPreviewError(null)} className="text-rose-400 hover:text-white">✕</button>
              </div>
            )}

            {/* Preview trigger button */}
            {selectedFile && !previewData && (
              <button
                type="button"
                onClick={() => handleGeneratePreview(selectedFile, importType)}
                disabled={loadingPreview || !syntheticConfirmed}
                className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-semibold transition-colors"
              >
                {loadingPreview ? "Analyzing File..." : "Preview File Records"}
              </button>
            )}
          </div>
        </section>

        {/* SECTION E: Ingestion Preview & Column Mapping */}
        {previewData && (
          <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-base font-semibold text-white">
                  3. Ingestion Preview & Validation Summary
                </h3>
                <p className="text-xs text-slate-400">
                  Review detected columns, duplicates, and validated rows before committing to PostgreSQL.
                </p>
              </div>

              {/* Validation Summary Badges */}
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-3 py-1 rounded-md bg-slate-800 text-slate-300 text-xs font-medium border border-slate-700">
                  Total Rows: <strong className="text-white">{previewData.total_rows}</strong>
                </span>
                <span className="px-3 py-1 rounded-md bg-emerald-500/10 text-emerald-400 text-xs font-medium border border-emerald-500/20">
                  Valid: <strong>{previewData.valid_count}</strong>
                </span>
                {previewData.duplicate_count > 0 && (
                  <span className="px-3 py-1 rounded-md bg-amber-500/10 text-amber-400 text-xs font-medium border border-amber-500/20">
                    Duplicates: <strong>{previewData.duplicate_count}</strong>
                  </span>
                )}
                {previewData.invalid_count > 0 && (
                  <span className="px-3 py-1 rounded-md bg-rose-500/10 text-rose-400 text-xs font-medium border border-rose-500/20">
                    Errors: <strong>{previewData.invalid_count}</strong>
                  </span>
                )}
              </div>
            </div>

            {/* Column Mapping Section (for statements) */}
            {previewData.import_type === "statement" && previewData.mapping && previewData.available_targets && (
              <div className="rounded-lg bg-slate-950/70 border border-slate-800 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                    Column Mapping Adjustment
                  </h4>
                  <button
                    onClick={handleApplyMapping}
                    disabled={loadingPreview}
                    className="text-xs px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
                  >
                    Re-evaluate Mapping
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {previewData.available_targets.map((target) => (
                    <div key={target} className="space-y-1">
                      <label className="text-[11px] font-mono text-slate-400 block">
                        {target} {["transaction_date", "raw_descriptor", "amount"].includes(target) && <span className="text-rose-400">*</span>}
                      </label>
                      <select
                        value={columnOverrides[target] || ""}
                        onChange={(e) => {
                          setColumnOverrides({
                            ...columnOverrides,
                            [target]: e.target.value,
                          });
                        }}
                        className="w-full text-xs rounded border border-slate-800 bg-slate-900 text-slate-200 px-2 py-1.5 focus:border-emerald-500 focus:outline-none font-mono"
                      >
                        <option value="">(Not mapped / default)</option>
                        {previewData.headers.map((h) => (
                          <option key={h} value={h}>
                            {h}
                          </option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Row Validation Errors (if any) */}
            {previewData.errors && previewData.errors.length > 0 && (
              <div className="rounded-lg bg-rose-950/30 border border-rose-900/50 p-4 space-y-2">
                <h4 className="text-xs font-semibold text-rose-300 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-rose-500" />
                  Validation Failures ({previewData.errors.length} detected)
                </h4>
                <div className="max-h-40 overflow-y-auto space-y-1 text-xs font-mono text-rose-200">
                  {previewData.errors.map((err, idx) => (
                    <div key={idx} className="flex gap-2">
                      <span className="text-rose-400">Row {err.row}:</span>
                      <span>[{err.column}] {err.reason} (value: &ldquo;{err.value}&rdquo;)</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Preview Data Table */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Sample Record Preview (First {previewData.preview_rows.length} rows)
              </h4>
              <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900 border-b border-slate-800 text-slate-400 font-mono">
                    <tr>
                      <th className="px-3 py-2">Status</th>
                      <th className="px-3 py-2">Date / Time</th>
                      <th className="px-3 py-2">Descriptor / Event</th>
                      <th className="px-3 py-2">Amount</th>
                      <th className="px-3 py-2">Channel / Mechanism</th>
                      <th className="px-3 py-2">Reference / UMN</th>
                      <th className="px-3 py-2">Synthetic ID</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-850">
                    {previewData.preview_rows.map((row, idx) => (
                      <tr key={idx} className={row.is_duplicate ? "bg-amber-950/10" : ""}>
                        <td className="px-3 py-2">
                          {row.is_duplicate ? (
                            <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                              Duplicate
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                              New Valid
                            </span>
                          )}
                        </td>
                        <td className="px-3 py-2 font-mono text-slate-300">
                          {row.date || row.timestamp?.slice(0, 10)}
                        </td>
                        <td className="px-3 py-2 text-slate-200 max-w-xs truncate">
                          {row.descriptor || `${row.event_type} (${row.merchant_hint || ""})`}
                        </td>
                        <td className="px-3 py-2 font-mono text-slate-200">
                          {row.amount !== null && row.amount !== undefined
                            ? `${row.currency || "INR"} ${row.amount.toFixed(2)}`
                            : "—"}
                        </td>
                        <td className="px-3 py-2 text-slate-400">
                          {row.channel || row.mechanism || "—"}
                        </td>
                        <td className="px-3 py-2 font-mono text-slate-400 text-[11px] truncate max-w-[120px]">
                          {row.reference || row.mandate_ref || "—"}
                        </td>
                        <td className="px-3 py-2 font-mono text-slate-500 text-[10px]">
                          {row.external_id || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* SECTION F: Confirm Import Button */}
            <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-xs text-slate-400">
                {previewData.valid_count > 0 ? (
                  <span>
                    Ready to persist <strong className="text-emerald-400">{previewData.valid_count}</strong> records to PostgreSQL.
                    {previewData.duplicate_count > 0 && ` (${previewData.duplicate_count} existing records will be skipped).`}
                  </span>
                ) : (
                  <span className="text-amber-400">
                    No new valid records to persist ({previewData.duplicate_count} duplicates, {previewData.invalid_count} errors).
                  </span>
                )}
              </div>

              <button
                type="button"
                onClick={handleConfirmImport}
                disabled={importing || !syntheticConfirmed || (previewData.valid_count === 0 && previewData.duplicate_count === 0)}
                className="w-full sm:w-auto px-6 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-semibold shadow-md transition-all flex items-center justify-center gap-2"
              >
                {importing ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Persisting to Database...</span>
                  </>
                ) : (
                  <span>Confirm & Import to Workspace</span>
                )}
              </button>
            </div>

            {executionError && (
              <div className="rounded-lg bg-rose-950/40 border border-rose-800 p-3 text-xs text-rose-300">
                {executionError}
              </div>
            )}
          </section>
        )}

        {/* SECTION G: Import Result Card */}
        {importResult && (
          <section className="rounded-xl border border-emerald-500/40 bg-emerald-950/20 p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                  ✓
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">
                    Import Succeeded
                  </h3>
                  <p className="text-xs text-slate-400 font-mono">
                    Import ID: {importResult.import_id}
                  </p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-mono font-semibold uppercase">
                {importResult.status}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
              <div className="rounded bg-slate-900/80 p-3 border border-slate-800">
                <span className="text-[11px] text-slate-400 block">Total Rows</span>
                <span className="text-lg font-bold text-white font-mono">{importResult.total_rows}</span>
              </div>
              <div className="rounded bg-slate-900/80 p-3 border border-slate-800">
                <span className="text-[11px] text-emerald-400 block">Accepted & Saved</span>
                <span className="text-lg font-bold text-emerald-400 font-mono">{importResult.accepted_count}</span>
              </div>
              <div className="rounded bg-slate-900/80 p-3 border border-slate-800">
                <span className="text-[11px] text-amber-400 block">Duplicates Skipped</span>
                <span className="text-lg font-bold text-amber-400 font-mono">{importResult.duplicate_count}</span>
              </div>
              <div className="rounded bg-slate-900/80 p-3 border border-slate-800">
                <span className="text-[11px] text-rose-400 block">Rejected Errors</span>
                <span className="text-lg font-bold text-rose-400 font-mono">{importResult.rejected_count}</span>
              </div>
            </div>
          </section>
        )}

        {/* SECTION H: Import History */}
        <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-white">
                Import History & Ingestion Log
              </h3>
              <p className="text-xs text-slate-400">
                Past uploads recorded in PostgreSQL with audit status and row breakdown.
              </p>
            </div>
            <button
              onClick={fetchHistory}
              disabled={loadingHistory}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
            >
              {loadingHistory ? "Refreshing..." : "Refresh History"}
            </button>
          </div>

          {historyItems.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-lg">
              No previous imports found in this workspace. Upload a synthetic statement above to populate.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900 border-b border-slate-800 text-slate-400 font-mono">
                  <tr>
                    <th className="px-3 py-2">Timestamp</th>
                    <th className="px-3 py-2">Filename</th>
                    <th className="px-3 py-2">Source</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Accepted</th>
                    <th className="px-3 py-2">Duplicates</th>
                    <th className="px-3 py-2">Rejected</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850 font-mono">
                  {historyItems.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-900/50 transition-colors">
                      <td className="px-3 py-2 text-slate-400">
                        {item.created_at ? new Date(item.created_at).toLocaleString() : "—"}
                      </td>
                      <td className="px-3 py-2 text-white font-sans font-medium">
                        {item.filename}
                      </td>
                      <td className="px-3 py-2 text-slate-400 font-sans">
                        {item.source_label}
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] uppercase font-semibold border ${
                            item.status === "completed"
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : item.status === "partially_completed"
                              ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                              : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-emerald-400 font-bold">
                        {item.accepted_count}
                      </td>
                      <td className="px-3 py-2 text-amber-400">
                        {item.duplicate_count}
                      </td>
                      <td className="px-3 py-2 text-rose-400">
                        {item.rejected_count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-6 text-center text-xs text-slate-500">
        MandateLens Prototype — Synthetic financial data only. No real banking connectivity.
      </footer>
    </div>
  );
}
