"use client";

import React from "react";
import Link from "next/link";
import { PayScopeLogo } from "@/components/brand/PayScopeLogo";

interface PayScopeLandingHeaderProps {
  apiConnected?: boolean;
  headerLogoRef?: React.RefObject<HTMLDivElement | null>;
  showFinalLogo?: boolean;
}

export function PayScopeLandingHeader({
  apiConnected = true,
  headerLogoRef,
  showFinalLogo = true,
}: PayScopeLandingHeaderProps) {
  return (
    <header className="relative z-40 border-b border-[#164B68]/60 bg-[#011633]/85 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Left Section: Navigation Links & Platform Quick Access */}
        <div className="flex items-center gap-4">
          <nav className="hidden lg:flex items-center gap-1.5 text-xs font-medium">
            <Link
              href="/dashboard"
              className="px-3 py-1.5 rounded-lg border border-[#F08A00]/40 bg-[#F08A00]/15 text-[#FFA52B] hover:bg-[#F08A00]/25 transition-all font-semibold shadow-[0_0_12px_rgba(240,138,0,0.15)]"
            >
              Dashboard
            </Link>
            <Link
              href="/financial-impact"
              className="px-3 py-1.5 rounded-lg border border-[#00B8C7]/30 bg-[#00B8C7]/10 text-[#00E0E0] hover:bg-[#00B8C7]/20 transition-all font-semibold shadow-[0_0_12px_rgba(0,184,199,0.15)]"
            >
              Financial Impact
            </Link>
            <Link
              href="/savings"
              className="px-3 py-1.5 rounded-lg border border-[#00B8C7]/30 bg-[#00B8C7]/10 text-[#00E0E0] hover:bg-[#00B8C7]/20 transition-all font-semibold"
            >
              Savings
            </Link>
            <Link
              href="/commitments"
              className="px-3 py-1.5 rounded-lg text-[#A9BBCD] hover:text-white hover:bg-[#082746]/60 transition-colors"
            >
              Commitments
            </Link>
            <Link
              href="/insights"
              className="px-3 py-1.5 rounded-lg text-[#A9BBCD] hover:text-white hover:bg-[#082746]/60 transition-colors"
            >
              Insights
            </Link>
            <Link
              href="/cancellations"
              className="px-3 py-1.5 rounded-lg text-[#A9BBCD] hover:text-white hover:bg-[#082746]/60 transition-colors"
            >
              Cancellations
            </Link>
            <Link
              href="/relationships"
              className="px-3 py-1.5 rounded-lg text-[#A9BBCD] hover:text-white hover:bg-[#082746]/60 transition-colors"
            >
              Relationships
            </Link>
            <Link
              href="/upload"
              className="px-3 py-1.5 rounded-lg text-[#A9BBCD] hover:text-white hover:bg-[#082746]/60 transition-colors"
            >
              Upload
            </Link>
          </nav>

          {/* Service Status Badge */}
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#082746] border border-[#164B68] text-[11px] text-[#A9BBCD]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00E0E0] animate-pulse" />
              Synthetic Mode
            </span>
            {apiConnected ? (
              <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                API 200 OK
              </span>
            ) : (
              <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                API Offline
              </span>
            )}
          </div>
        </div>

        {/* Top-Right Brand Anchor: Settles here after video zoom transition */}
        <div
          ref={headerLogoRef}
          id="header-target-logo"
          className="flex items-center justify-end transition-opacity duration-300"
          style={{ opacity: showFinalLogo ? 1 : 0 }}
        >
          <Link href="/" className="hover:opacity-90 transition-opacity flex items-center">
            <PayScopeLogo variant="navbar" />
          </Link>
        </div>
      </div>
    </header>
  );
}

export default PayScopeLandingHeader;
