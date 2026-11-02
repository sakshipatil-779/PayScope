"use client";

import React, { useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import PayScopeLogo from "@/components/brand/PayScopeLogo";

export interface DrawerRoute {
  label: string;
  href: string;
  description: string;
  icon: (props: { className?: string }) => React.JSX.Element;
  badge?: string;
}

export const DRAWER_ROUTES: DrawerRoute[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    description: "Command centre & key metrics",
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
      </svg>
    ),
  },
  {
    label: "Commitments",
    href: "/commitments",
    description: "Active recurring obligations & cadences",
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    label: "Insights",
    href: "/insights",
    description: "Price hikes, trial traps & anomalies",
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
  },
  {
    label: "Financial Impact",
    href: "/financial-impact",
    description: "Annual spend & forward projections",
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    ),
  },
  {
    label: "Savings",
    href: "/savings",
    description: "Reclaimable capital & recovery plans",
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    label: "Merchants",
    href: "/merchants",
    description: "Canonical merchant intelligence directory",
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
  },
  {
    label: "Merchant Review",
    href: "/merchant-review",
    description: "Resolution queue & alias matching",
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
      </svg>
    ),
  },
  {
    label: "Cancellation Centre",
    href: "/cancellations",
    description: "Step-by-step verified exit playbooks",
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    label: "Relationship Explorer",
    href: "/relationships",
    description: "Interactive Neo4j entity graph",
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
      </svg>
    ),
  },
  {
    label: "Upload Centre",
    href: "/upload",
    description: "Ingest CSV, XLSX or JSON statements",
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
      </svg>
    ),
  },
];

interface PayScopeDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export function PayScopeDrawer({ isOpen, onClose }: PayScopeDrawerProps) {
  const pathname = usePathname();
  const drawerRef = useRef<HTMLDivElement>(null);

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Lock body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden" role="dialog" aria-modal="true" aria-label="Navigation Menu">
      {/* Dimmed Backdrop */}
      <div
        className="fixed inset-0 bg-black/65 backdrop-blur-sm transition-opacity duration-300 animate-in fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-out Left Drawer Panel */}
      <div
        ref={drawerRef}
        className="fixed inset-y-0 left-0 w-80 max-w-[85vw] bg-[#031B38] border-r border-[#164B68] shadow-2xl flex flex-col z-50 transform transition-transform duration-300 ease-out animate-in slide-in-from-left"
      >
        {/* Top Header of Drawer */}
        <div className="h-16 px-5 border-b border-[#164B68] flex items-center justify-between bg-[#011633]/60">
          <Link href="/" onClick={onClose} className="hover:opacity-90 transition-opacity">
            <PayScopeLogo variant="compact" />
          </Link>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-[#082746] hover:bg-[#0B3152] border border-[#164B68] text-[#A9BBCD] hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-[#00B8C7]"
            aria-label="Close navigation menu"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Navigation Routes List */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          <div className="px-3 pb-2 text-[11px] font-bold uppercase tracking-wider text-[#00E0E0]">
            Platform Modules
          </div>
          {DRAWER_ROUTES.map((route) => {
            const isActive = pathname === route.href || (route.href !== "/" && pathname.startsWith(route.href));
            const IconComponent = route.icon;

            return (
              <Link
                key={route.href}
                href={route.href}
                onClick={onClose}
                className={`group flex items-start gap-3 px-3 py-2.5 rounded-xl transition-all ${
                  isActive
                    ? "bg-[#082746] text-[#FFA52B] border border-[#F08A00]/40 shadow-sm"
                    : "text-[#F4F7FB] hover:text-[#00E0E0] hover:bg-[#082746]/70 border border-transparent"
                }`}
              >
                <div
                  className={`mt-0.5 p-1.5 rounded-lg shrink-0 transition-colors ${
                    isActive
                      ? "bg-[#F08A00]/20 text-[#FFA52B]"
                      : "bg-[#011633] text-[#A9BBCD] group-hover:text-[#00E0E0] group-hover:bg-[#0B3152]"
                  }`}
                >
                  <IconComponent className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold tracking-tight">{route.label}</span>
                    {isActive && (
                      <span className="w-2 h-2 rounded-full bg-[#F08A00] animate-pulse shrink-0" />
                    )}
                  </div>
                  <p className="text-[11px] text-[#A9BBCD] truncate mt-0.5 group-hover:text-slate-300">
                    {route.description}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>

        {/* Drawer Bottom Status Footer */}
        <div className="p-4 border-t border-[#164B68] bg-[#011633]/80 flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[#A9BBCD]">
            <span>Mode</span>
            <span className="text-[#00E0E0] font-mono">Synthetic Bank Data</span>
          </div>
          <div className="flex items-center justify-between text-xs text-[#A9BBCD]">
            <span>Engine</span>
            <span className="text-[#FFA52B] font-mono">PayScope v1.0</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PayScopeDrawer;
