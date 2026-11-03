"use client";

import React from "react";
import Link from "next/link";
import AppHeader from "@/components/navigation/AppHeader";

interface PayScopeAppShellProps {
  children: React.ReactNode;
  apiConnected?: boolean;
  maxWidth?: "7xl" | "full" | "5xl";
}

export function PayScopeAppShell({
  children,
  apiConnected = true,
  maxWidth = "7xl",
}: PayScopeAppShellProps) {
  const maxWidthClass =
    maxWidth === "full" ? "max-w-full" : maxWidth === "5xl" ? "max-w-5xl" : "max-w-7xl";

  return (
    <div className="min-h-screen flex flex-col bg-[#011633] text-[#F4F7FB] selection:bg-[#F08A00] selection:text-white antialiased">
      {/* Global Header */}
      <AppHeader apiConnected={apiConnected} />

      {/* Main Content Area */}
      <main className={`flex-1 ${maxWidthClass} w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8`}>
        {children}
      </main>

      {/* Shared Footer */}
      <footer className="border-t border-[#164B68]/60 bg-[#031B38]/60 py-6 text-xs text-[#A9BBCD]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p>© {new Date().getFullYear()} PayScope — Recurring Payment Intelligence Platform.</p>
          <div className="flex items-center gap-6 text-[12px]">
            <Link href="/" className="hover:text-white transition-colors">
              Home
            </Link>
            <Link href="/about" className="hover:text-white transition-colors">
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

export default PayScopeAppShell;
