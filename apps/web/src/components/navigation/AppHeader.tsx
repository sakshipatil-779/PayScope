"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import PayScopeLogo from "@/components/brand/PayScopeLogo";

export interface NavItem {
  label: string;
  href: string;
  badge?: number | string;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Commitments", href: "/commitments" },
  { label: "Insights", href: "/insights" },
  { label: "Financial Impact", href: "/financial-impact" },
  { label: "Savings", href: "/savings" },
  { label: "Merchants", href: "/merchants" },
  { label: "Review Queue", href: "/merchant-review" },
  { label: "Cancellations", href: "/cancellations" },
  { label: "Relationships", href: "/relationships" },
  { label: "Upload", href: "/upload" },
];

export function AppHeader() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="border-b border-[#164B68] bg-[#031B38]/90 backdrop-blur-md sticky top-0 z-50 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <div className="flex items-center gap-6">
          <Link href="/" className="hover:opacity-90 transition-opacity flex items-center">
            <PayScopeLogo variant="navbar" />
          </Link>
        </div>

        {/* Desktop Nav */}
        <nav className="hidden xl:flex items-center gap-1.5 text-xs font-medium">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`px-3 py-1.5 rounded-lg transition-colors ${
                  isActive
                    ? "bg-[#082746] text-[#FFA52B] border border-[#F08A00]/40 font-semibold shadow-sm"
                    : "text-[#A9BBCD] hover:text-white hover:bg-[#082746]/60 border border-transparent"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Mobile menu button */}
        <div className="flex xl:hidden items-center gap-2">
          <Link
            href="/dashboard"
            className="text-xs px-3 py-1.5 rounded-lg bg-[#082746] border border-[#164B68] text-[#00E0E0] font-semibold"
          >
            Dashboard
          </Link>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg bg-[#082746] border border-[#164B68] text-[#A9BBCD] hover:text-white"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? "✕" : "☰"}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="xl:hidden border-t border-[#164B68] bg-[#031B38] px-4 py-3 flex flex-col gap-1 shadow-2xl">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`px-3 py-2 rounded-lg text-xs font-medium flex items-center justify-between ${
                  isActive
                    ? "bg-[#082746] text-[#FFA52B] border border-[#F08A00]/30"
                    : "text-[#A9BBCD] hover:bg-[#082746] hover:text-white"
                }`}
              >
                <span>{item.label}</span>
                {isActive && <span className="text-[10px] text-[#00E0E0]">●</span>}
              </Link>
            );
          })}
        </div>
      )}
    </header>
  );
}

export default AppHeader;
