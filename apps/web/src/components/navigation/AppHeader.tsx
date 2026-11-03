"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import PayScopeLogo from "@/components/brand/PayScopeLogo";
import PayScopeDrawer from "@/components/navigation/PayScopeDrawer";
import { useAuth } from "@/context/AuthContext";

export interface AppHeaderProps {
  apiConnected?: boolean;
}

export function AppHeader({}: AppHeaderProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const pathname = usePathname();
  const { user, signOut, openAuthModal } = useAuth();

  return (
    <>
      <header className="border-b border-white/[0.08] bg-[#070B16]/90 backdrop-blur-2xl sticky top-0 z-40 transition-all">
        {/* Subtle top ambient glowing hairline */}
        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-[#00E0E0]/20 to-transparent pointer-events-none" />

        <div className="w-full px-4 sm:px-6 h-16 flex items-center justify-between">
          {/* LEFT SIDE: [Drawer Toggle for workspace navigation] [PayScope Logo] */}
          <div className="flex items-center gap-3 sm:gap-4">
            <button
              onClick={() => setDrawerOpen(true)}
              className="p-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] border border-white/10 text-[#8E9CAE] hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-[#00E0E0] cursor-pointer flex items-center justify-center shadow-sm"
              aria-label="Open navigation menu"
              aria-expanded={drawerOpen}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            <Link href="/" className="hover:opacity-90 transition-opacity flex items-center">
              <PayScopeLogo variant="navbar" size={28} />
            </Link>
          </div>

          {/* RIGHT SIDE: Clean modern navigation links + User profile */}
          <div className="flex items-center gap-2 sm:gap-4 text-xs sm:text-sm font-medium">
            <Link
              href="/"
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                pathname === "/" ? "text-white bg-white/[0.08]" : "text-[#8E9CAE] hover:text-white"
              }`}
            >
              Home
            </Link>
            <Link
              href="/about"
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                pathname === "/about" ? "text-white bg-white/[0.08]" : "text-[#8E9CAE] hover:text-white"
              }`}
            >
              About Us
            </Link>
            <Link
              href="/privacy"
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                pathname === "/privacy" ? "text-white bg-white/[0.08]" : "text-[#8E9CAE] hover:text-white"
              }`}
            >
              Privacy Policy
            </Link>

            {user ? (
              <div className="flex items-center gap-2 pl-2 border-l border-white/[0.08]">
                {user.photoURL ? (
                  <Image
                    src={user.photoURL}
                    alt={user.displayName || "User avatar"}
                    width={28}
                    height={28}
                    className="w-7 h-7 rounded-full border border-white/20 object-cover"
                  />
                ) : (
                  <div className="w-7 h-7 rounded-full bg-[#FF5500] text-white flex items-center justify-center text-xs font-bold">
                    {user.displayName?.[0] || user.email?.[0] || "U"}
                  </div>
                )}
                <span className="hidden md:inline text-xs font-medium text-[#D4DEE8]">
                  {user.displayName || user.email?.split("@")[0]}
                </span>
                <button
                  onClick={signOut}
                  title="Sign out"
                  className="p-1.5 text-xs text-[#8E9CAE] hover:text-rose-400 hover:bg-white/[0.05] rounded-lg transition-colors cursor-pointer"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                </button>
              </div>
            ) : (
              <button
                onClick={openAuthModal}
                className="px-3.5 py-1.5 rounded-xl bg-white/[0.08] hover:bg-white/[0.14] text-white text-xs font-semibold border border-white/10"
              >
                Log in
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Global Slide-out Drawer */}
      <PayScopeDrawer isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </>
  );
}

export default AppHeader;
