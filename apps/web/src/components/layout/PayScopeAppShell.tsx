"use client";

import React from "react";
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
      {/* Global Header with Left Hamburger and PayScope Logo */}
      <AppHeader apiConnected={apiConnected} />

      {/* Main Content Area */}
      <main className={`flex-1 ${maxWidthClass} w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8`}>
        {children}
      </main>

      {/* Shared Footer */}
      <footer className="border-t border-[#164B68]/60 bg-[#031B38]/60 py-6 text-center text-xs text-[#A9BBCD]">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p>© {new Date().getFullYear()} PayScope — Recurring Payment Intelligence Platform.</p>
          <div className="flex items-center gap-4 text-[11px]">
            <span className="text-[#00E0E0]">Synthetic Sandbox Data Only</span>
            <span className="text-[#164B68]">•</span>
            <span className="text-[#FFA52B]">Zero Live Bank Connection</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default PayScopeAppShell;
