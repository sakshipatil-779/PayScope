"use client";

import React, { useState } from "react";
import Link from "next/link";
import { PayScopeLogo } from "@/components/brand/PayScopeLogo";
import PayScopeDrawer from "@/components/navigation/PayScopeDrawer";

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
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <>
      <header className="relative z-40 border-b border-[#164B68]/60 bg-[#011633]/85 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* LEFT SIDE: [Hamburger Menu] [PayScope Logo + Wordmark at TOP-LEFT] */}
          <div className="flex items-center gap-3 sm:gap-4">
            <button
              onClick={() => setDrawerOpen(true)}
              className="p-2 rounded-xl bg-[#082746] hover:bg-[#0B3152] border border-[#164B68] text-[#A9BBCD] hover:text-[#00E0E0] transition-colors focus:outline-none focus:ring-2 focus:ring-[#00B8C7] cursor-pointer flex items-center justify-center shadow-sm"
              aria-label="Open navigation menu"
              aria-expanded={drawerOpen}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            {/* Top-Left Target Logo Anchor: Settles here after 3D emergence transition */}
            <div
              ref={headerLogoRef}
              id="header-target-logo"
              className="flex items-center transition-opacity duration-300"
              style={{ opacity: showFinalLogo ? 1 : 0 }}
            >
              <Link href="/" className="hover:opacity-90 transition-opacity flex items-center">
                <PayScopeLogo variant="navbar" />
              </Link>
            </div>
          </div>

          {/* RIGHT SIDE: Essential Service Status Badges */}
          <div className="flex items-center gap-2.5">
            <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#082746] border border-[#164B68] text-[11px] text-[#A9BBCD]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00E0E0] animate-pulse" />
              Synthetic Mode
            </span>
            {apiConnected ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                API 200 OK
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                API Offline
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Global Slide-out Drawer */}
      <PayScopeDrawer isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </>
  );
}

export default PayScopeLandingHeader;
