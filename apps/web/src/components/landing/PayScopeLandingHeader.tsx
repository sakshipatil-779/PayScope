"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { PayScopeLogo } from "@/components/brand/PayScopeLogo";
import { useAuth } from "@/context/AuthContext";

interface PayScopeLandingHeaderProps {
  apiConnected?: boolean;
  headerLogoRef?: React.RefObject<HTMLDivElement | null>;
  showFinalLogo?: boolean;
}

export function PayScopeLandingHeader({
  headerLogoRef,
  showFinalLogo = true,
}: PayScopeLandingHeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const { user, openAuthModal, signOut } = useAuth();

  const navLinks = [
    { name: "Home", href: "/" },
    { name: "About Us", href: "/about" },
    { name: "Privacy Policy", href: "/privacy" },
  ];

  const handleGetStarted = () => {
    if (user) {
      router.push("/dashboard");
    } else {
      openAuthModal();
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full pt-3 sm:pt-5 px-3 sm:px-6 pointer-events-none">
      {/* Floating Island Navbar Capsule (inspired by modern fintech design) */}
      <div className="max-w-6xl mx-auto rounded-2xl sm:rounded-full bg-[#080C16]/85 border border-white/[0.09] backdrop-blur-2xl shadow-[0_12px_40px_rgba(0,0,0,0.75)] px-4 sm:px-6 py-2.5 sm:py-3 flex items-center justify-between pointer-events-auto transition-all">
        {/* LEFT: PayScope Brand Logo */}
        <div
          ref={headerLogoRef}
          id="header-target-logo"
          className="flex items-center transition-opacity duration-300 shrink-0"
          style={{ opacity: showFinalLogo ? 1 : 0 }}
        >
          <Link
            href="/"
            className="flex items-center gap-1 focus:outline-none focus:ring-2 focus:ring-[#00E0E0] rounded-xl p-0.5"
          >
            <PayScopeLogo variant="navbar" size={28} />
          </Link>
        </div>

        {/* CENTER: Clean Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-1 lg:gap-2">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.name}
                href={link.href}
                className={`px-3.5 py-1.5 rounded-full text-xs lg:text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? "text-white bg-white/[0.08] shadow-inner"
                    : "text-[#8E9CAE] hover:text-white hover:bg-white/[0.04]"
                }`}
              >
                {link.name}
              </Link>
            );
          })}
        </nav>

        {/* RIGHT: Auth & Actions */}
        <div className="flex items-center gap-2 sm:gap-3">
          {user ? (
            /* Logged In State */
            <div className="flex items-center gap-2 sm:gap-3">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-white/[0.08] hover:bg-white/[0.14] border border-white/10 transition-all hover:scale-[1.02]"
              >
                <span>Dashboard</span>
                <svg className="w-3.5 h-3.5 text-[#00E0E0]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </Link>

              <div className="flex items-center gap-2 pl-1">
                {user.photoURL ? (
                  <Image
                    src={user.photoURL}
                    alt={user.displayName || "User avatar"}
                    width={30}
                    height={30}
                    className="w-7 h-7 sm:w-8 sm:h-8 rounded-full border border-white/20 object-cover"
                  />
                ) : (
                  <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-[#FF5500] text-white flex items-center justify-center text-xs font-bold">
                    {user.displayName?.[0] || user.email?.[0] || "U"}
                  </div>
                )}
                <button
                  onClick={signOut}
                  title="Sign out"
                  className="p-1.5 text-xs text-[#8E9CAE] hover:text-white hover:bg-white/[0.06] rounded-lg transition-colors cursor-pointer"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                </button>
              </div>
            </div>
          ) : (
            /* Logged Out State: Log in & Get Started buttons */
            <div className="flex items-center gap-1.5 sm:gap-2.5">
              <button
                onClick={openAuthModal}
                className="px-3 sm:px-4 py-2 text-xs sm:text-sm font-medium text-[#8E9CAE] hover:text-white transition-colors cursor-pointer"
              >
                Log in
              </button>

              <button
                onClick={handleGetStarted}
                className="px-4 sm:px-5 py-2 rounded-xl text-xs sm:text-sm font-semibold text-white bg-white/[0.08] hover:bg-white/[0.14] border border-white/10 hover:border-white/20 transition-all hover:scale-[1.02] active:scale-[0.98] shadow-sm cursor-pointer"
              >
                Get started
              </button>
            </div>
          )}

          {/* Mobile Menu Toggle Button */}
          <button
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            className="md:hidden p-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 text-[#8E9CAE] hover:text-white transition-colors focus:outline-none focus:ring-1 focus:ring-white/20 ml-1"
            aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
          >
            {mobileMenuOpen ? (
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Responsive Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden max-w-6xl mx-auto mt-2 rounded-2xl bg-[#080C16]/95 border border-white/[0.09] backdrop-blur-2xl p-4 space-y-2 pointer-events-auto shadow-2xl animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex flex-col space-y-1">
            {navLinks.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.name}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`px-3 py-2.5 rounded-xl text-xs sm:text-sm font-medium transition-colors ${
                    isActive
                      ? "text-white bg-white/[0.08]"
                      : "text-[#8E9CAE] hover:text-white hover:bg-white/[0.04]"
                  }`}
                >
                  {link.name}
                </Link>
              );
            })}
          </div>

          <div className="pt-2 border-t border-white/[0.06] flex flex-col gap-2">
            {user ? (
              <Link
                href="/dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full py-2.5 rounded-xl text-xs font-semibold text-center text-white bg-white/[0.08] border border-white/10"
              >
                Go to Dashboard
              </Link>
            ) : (
              <>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    openAuthModal();
                  }}
                  className="w-full py-2.5 rounded-xl text-xs font-semibold text-white bg-white/[0.08] border border-white/10"
                >
                  Log in with Google
                </button>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    openAuthModal();
                  }}
                  className="w-full py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-[#FF5500] to-[#FFA52B] shadow-lg"
                >
                  Get started
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}

export default PayScopeLandingHeader;
