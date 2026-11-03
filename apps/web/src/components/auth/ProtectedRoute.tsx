"use client";

import React, { useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { PayScopeLandingHeader } from "@/components/landing/PayScopeLandingHeader";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading, openAuthModal } = useAuth();

  useEffect(() => {
    if (!loading && !user) {
      openAuthModal();
    }
  }, [loading, user, openAuthModal]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050811] flex items-center justify-center text-[#A9BBCD]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-2 border-[#00E0E0] border-t-transparent rounded-full animate-spin" />
          <p className="text-sm font-medium">Verifying authorization...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-[#050811] text-slate-100 flex flex-col justify-between">
        <PayScopeLandingHeader />

        <div className="flex-1 flex items-center justify-center p-4">
          <div className="max-w-md w-full p-8 rounded-3xl bg-[#090D18]/90 border border-white/[0.08] backdrop-blur-2xl text-center space-y-6 shadow-2xl">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-[#FF5500]/10 border border-[#FF5500]/20 flex items-center justify-center text-[#FF5500]">
              <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>

            <div className="space-y-2">
              <h2 className="text-2xl font-bold tracking-tight text-white">
                Dashboard Locked
              </h2>
              <p className="text-sm text-[#7E8B9B] leading-relaxed">
                Please log in with Google to access recurring payment intelligence and financial commitments.
              </p>
            </div>

            <button
              onClick={openAuthModal}
              className="w-full py-3.5 px-5 rounded-xl bg-gradient-to-r from-[#FF5500] to-[#FFA52B] hover:brightness-110 text-white font-bold text-sm shadow-[0_0_25px_rgba(255,85,0,0.35)] transition-all hover:scale-[1.02] cursor-pointer"
            >
              Log In with Google
            </button>
          </div>
        </div>

        <footer className="border-t border-white/[0.05] py-6 text-center text-xs text-[#556272]">
          © {new Date().getFullYear()} PayScope. All rights reserved.
        </footer>
      </div>
    );
  }

  return <>{children}</>;
}

export default ProtectedRoute;

