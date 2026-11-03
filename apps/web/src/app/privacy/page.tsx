"use client";

import React from "react";
import Link from "next/link";
import { PayScopeLandingHeader } from "@/components/landing/PayScopeLandingHeader";

export default function PrivacyPolicyPage() {
  return (
    <div className="relative min-h-screen flex flex-col justify-between bg-[#040711] text-slate-100 overflow-x-hidden">
      {/* Background Ambient Glow */}
      <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/3 w-[600px] h-[600px] rounded-full bg-[#3B286D]/15 blur-[140px]" />
        <div className="absolute top-2/3 right-1/4 w-[500px] h-[500px] rounded-full bg-[#00B8C7]/10 blur-[130px]" />
      </div>

      {/* Floating Island Header */}
      <PayScopeLandingHeader />

      {/* Main Content */}
      <main className="relative z-10 flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-20 flex flex-col gap-12">
        {/* Header Section */}
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-white/[0.05] border border-white/10 text-[#00E0E0]">
            <span>Security & Data Governance</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Privacy Policy & Data Principles
          </h1>
          <p className="text-sm sm:text-base text-[#8E9CAE]">
            Last updated: November 2026 • Effective immediately
          </p>
        </div>

        {/* Commitment Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-5 rounded-2xl bg-[#080C16]/85 border border-white/[0.08] backdrop-blur-xl">
            <div className="w-9 h-9 rounded-xl bg-white/[0.06] border border-white/10 flex items-center justify-center text-[#00E0E0] mb-3">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="font-semibold text-white text-base mb-1">Zero Bank Credential Access</h3>
            <p className="text-xs text-[#8E9CAE] leading-relaxed">
              PayScope never asks for, stores, or transmits your online banking passwords, debit card PINs, or OTPs.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-[#080C16]/85 border border-white/[0.08] backdrop-blur-xl">
            <div className="w-9 h-9 rounded-xl bg-[#FF5500]/10 border border-[#FF5500]/20 flex items-center justify-center text-[#FF5500] mb-3">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </div>
            <h3 className="font-semibold text-white text-base mb-1">Instant Data Purging</h3>
            <p className="text-xs text-[#8E9CAE] leading-relaxed">
              You retain total control over uploaded records and can purge your statement data and detected commitments at any time.
            </p>
          </div>
        </div>

        {/* Detailed Sections */}
        <div className="p-8 sm:p-10 rounded-3xl bg-[#080C16]/85 border border-white/[0.08] backdrop-blur-xl space-y-8 text-sm leading-relaxed text-[#8E9CAE]">
          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white">1. Information We Process</h2>
            <p>
              PayScope operates as an offline-first and statement-ingestion recurring expense intelligence platform. We process:
            </p>
            <ul className="list-disc pl-5 space-y-1.5">
              <li><strong className="text-white">Transaction Line Items:</strong> Transaction dates, normalized merchant strings, amounts, and currency identifiers extracted from user-supplied statement files.</li>
              <li><strong className="text-white">Recurring Metadata:</strong> Estimated cadence, recurring patterns, renewal cycles, and historical price adjustments.</li>
              <li><strong className="text-white">User Decisions:</strong> Explicit confirmations, dismissals, or cancellations marked within the portal.</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white">2. Synthetic Data Protocol</h2>
            <p>
              In sandbox and demonstration workspaces, PayScope operates exclusively on synthetic and anonymized test datasets. No real financial account, live credit card number, or Personally Identifiable Information (PII) is collected or stored during demonstration workflows.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white">3. Data Encryption & Security Standards</h2>
            <p>
              All data transmitted between the client application and API servers is protected using TLS 1.3 transport encryption. Database instances leverage AES-256 rest encryption and parameterized query bindings to strictly prevent injection vulnerabilities.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white">4. No Data Monetization</h2>
            <p>
              We do not sell, rent, or trade user financial patterns, transaction histories, or behavioral data to third-party ad networks, data brokers, or marketing intermediaries.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-bold text-white">5. Contact & Inquiries</h2>
            <p>
              For data privacy inquiries or security reports, contact our privacy engineering team at <span className="text-[#00E0E0] font-mono">security@payscope.dev</span>.
            </p>
          </section>
        </div>
      </main>

      {/* Modern Minimalist Footer */}
      <footer className="relative z-10 border-t border-white/[0.06] bg-[#040711]/90 backdrop-blur-md py-6 text-xs text-[#6F7D8E]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <span>© {new Date().getFullYear()} PayScope. All rights reserved.</span>
          <div className="flex items-center gap-6 text-xs">
            <Link href="/" className="hover:text-white transition-colors">
              Home
            </Link>
            <Link href="/about" className="hover:text-white transition-colors">
              About Us
            </Link>
            <Link href="/privacy" className="text-white font-semibold transition-colors">
              Privacy Policy
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
