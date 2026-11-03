"use client";

import React from "react";
import Link from "next/link";
import { PayScopeLandingHeader } from "@/components/landing/PayScopeLandingHeader";

export default function AboutUsPage() {
  return (
    <div className="relative min-h-screen flex flex-col justify-between bg-[#040711] text-slate-100 overflow-x-hidden">
      {/* Background Ambient Glow */}
      <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute top-1/4 right-1/3 w-[600px] h-[600px] rounded-full bg-[#3B286D]/15 blur-[140px]" />
        <div className="absolute top-2/3 left-1/4 w-[500px] h-[500px] rounded-full bg-[#00B8C7]/10 blur-[130px]" />
      </div>

      {/* Floating Island Header */}
      <PayScopeLandingHeader />

      {/* Main Content */}
      <main className="relative z-10 flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-20 flex flex-col gap-16">
        {/* Hero Section */}
        <div className="text-left space-y-4 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-white/[0.05] border border-white/10 text-[#00E0E0]">
            <span>About PayScope</span>
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-tight">
            Find the money leaving{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-[#A9BBCD]">
              quietly.
            </span>
          </h1>
          <p className="text-base sm:text-lg text-[#8E9CAE] leading-relaxed">
            Every year, billions in recurring commitments slip under the radar through silent price hikes, forgotten subscriptions, and complex cancellation friction. PayScope brings radical clarity to every recurring expense.
          </p>
        </div>

        {/* Core Pillars */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-3xl bg-[#080C16]/85 border border-white/[0.08] backdrop-blur-xl shadow-lg hover:border-white/20 transition-all group">
            <div className="w-12 h-12 rounded-2xl bg-white/[0.06] border border-white/10 flex items-center justify-center text-[#00E0E0] mb-4 group-hover:scale-110 transition-transform">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Statement-First Intelligence</h3>
            <p className="text-sm text-[#8E9CAE] leading-relaxed">
              We ingest statement exports directly without needing permanent third-party bank linking. We normalize messy merchant descriptors into clear canonical commitments.
            </p>
          </div>

          <div className="p-6 rounded-3xl bg-[#080C16]/85 border border-white/[0.08] backdrop-blur-xl shadow-lg hover:border-white/20 transition-all group">
            <div className="w-12 h-12 rounded-2xl bg-[#FF5500]/10 border border-[#FF5500]/20 flex items-center justify-center text-[#FF5500] mb-4 group-hover:scale-110 transition-transform">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Anomaly & Price Creep Detection</h3>
            <p className="text-sm text-[#8E9CAE] leading-relaxed">
              Our pattern engine flags sustained price increases, expired trial conversions, and post-cancellation zombie debits before they accumulate.
            </p>
          </div>

          <div className="p-6 rounded-3xl bg-[#080C16]/85 border border-white/[0.08] backdrop-blur-xl shadow-lg hover:border-white/20 transition-all group">
            <div className="w-12 h-12 rounded-2xl bg-white/[0.06] border border-white/10 flex items-center justify-center text-[#00B8C7] mb-4 group-hover:scale-110 transition-transform">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Mechanism-Aware Cancellation</h3>
            <p className="text-sm text-[#8E9CAE] leading-relaxed">
              Different subscriptions demand different cancellation tactics. We guide you through merchant web portals, payment rails, UPI e-mandates, and card block protocols.
            </p>
          </div>
        </div>

        {/* Narrative Section */}
        <div className="p-8 sm:p-10 rounded-3xl bg-[#080C16]/90 border border-white/[0.08] shadow-2xl space-y-6">
          <h2 className="text-2xl sm:text-3xl font-bold text-white">Why We Built PayScope</h2>
          <div className="space-y-4 text-sm sm:text-base text-[#8E9CAE] leading-relaxed">
            <p>
              Subscription fatigue isn’t just an inconvenience — it is a structural imbalance. Companies employ complex dark patterns, hidden renewal notices, and difficult cancellation flows to keep charging customers long after value has diminished.
            </p>
            <p>
              PayScope was architected as an independent, transparent recurring payment copilot. By projecting multi-hop relationship graphs between your statement lines, payment rails, and canonical merchants, we illuminate what you are actually paying annually and empower you with actionable playbooks to stop leaks.
            </p>
          </div>

          <div className="pt-4 flex flex-wrap items-center gap-4">
            <Link
              href="/dashboard"
              className="px-6 py-3.5 rounded-xl bg-[#FF5500] hover:bg-[#FF6611] text-white font-bold text-sm shadow-[0_0_25px_rgba(255,85,0,0.35)] transition-all hover:scale-[1.02]"
            >
              Explore Unified Dashboard →
            </Link>
            <Link
              href="/commitments"
              className="px-6 py-3.5 rounded-xl bg-white/[0.06] hover:bg-white/[0.1] border border-white/10 text-white font-medium text-sm transition-all"
            >
              View Recurring Commitments
            </Link>
          </div>
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
            <Link href="/about" className="text-white font-semibold transition-colors">
              About Us
            </Link>
            <Link href="/privacy" className="hover:text-white transition-colors">
              Privacy Policy
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
