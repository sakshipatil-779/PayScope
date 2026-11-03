"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { PayScopeLogo } from "@/components/brand/PayScopeLogo";

export function AuthModal() {
  const { isAuthModalOpen, closeAuthModal, signInWithGoogle, signInAsGuest } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isAuthModalOpen) return null;

  const handleGoogleLogin = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await signInWithGoogle();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to sign in with Google.";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleGuestLogin = () => {
    setError(null);
    signInAsGuest();
  };

  const isOperationNotAllowed =
    error && (error.includes("operation-not-allowed") || error.includes("auth/operation-not-allowed"));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Dark frosted overlay */}
      <div
        className="fixed inset-0 bg-[#020611]/85 backdrop-blur-md transition-opacity"
        onClick={closeAuthModal}
      />

      {/* Floating Card Modal */}
      <div className="relative w-full max-w-md rounded-3xl bg-[#090D18]/95 border border-white/[0.09] p-7 sm:p-8 shadow-[0_20px_60px_rgba(0,0,0,0.85)] backdrop-blur-2xl z-10 animate-in fade-in zoom-in-95 duration-200">
        {/* Close Button */}
        <button
          onClick={closeAuthModal}
          className="absolute top-5 right-5 p-2 rounded-xl text-[#7E8B9B] hover:text-white hover:bg-white/[0.05] transition-colors cursor-pointer"
          aria-label="Close"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Content */}
        <div className="flex flex-col items-center text-center space-y-6">
          <PayScopeLogo variant="compact" size={38} />

          <div className="space-y-1.5">
            <h3 className="text-2xl font-bold tracking-tight text-white">
              Welcome to PayScope
            </h3>
            <p className="text-xs sm:text-sm text-[#7E8B9B]">
              Sign in to manage recurring payments, identify commitments, and access the financial intelligence dashboard.
            </p>
          </div>

          {/* Error / Instruction Banner */}
          {isOperationNotAllowed ? (
            <div className="w-full text-left p-4 rounded-2xl bg-amber-500/10 border border-amber-500/25 text-xs text-amber-200 space-y-3">
              <div className="font-semibold flex items-center gap-2 text-amber-300">
                <svg className="w-4 h-4 shrink-0 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>Google Sign-In is pending in Firebase</span>
              </div>
              <p className="text-[11px] leading-relaxed text-amber-200/90">
                To enable live Google login for <span className="font-mono text-white">payscope18</span>:
                <br />
                1. Open <a href="https://console.firebase.google.com/project/payscope18/authentication/providers" target="_blank" rel="noopener noreferrer" className="underline font-medium text-amber-100 hover:text-white">Firebase Console &rarr; Authentication &rarr; Sign-in method</a>.
                <br />
                2. Click <strong>Add new provider</strong> &rarr; <strong>Google</strong> &rarr; Toggle <strong>Enable</strong> &rarr; Click <strong>Save</strong>.
              </p>
              <div className="pt-1">
                <button
                  type="button"
                  onClick={handleGuestLogin}
                  className="w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-[#FF5500] to-[#FFA52B] hover:brightness-110 text-white font-semibold text-xs shadow-md transition-all cursor-pointer flex items-center justify-center gap-2"
                >
                  <span>Continue with Demo Login &rarr;</span>
                </button>
              </div>
            </div>
          ) : error ? (
            <div className="w-full text-left p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300">
              {error}
            </div>
          ) : null}

          {/* Actions */}
          <div className="w-full space-y-3">
            {/* Google Sign-in Button */}
            <button
              onClick={handleGoogleLogin}
              disabled={submitting}
              className="w-full flex items-center justify-center gap-3 py-3.5 px-4 rounded-xl bg-white hover:bg-slate-100 text-[#090D18] font-semibold text-sm transition-all shadow-[0_0_20px_rgba(255,255,255,0.15)] hover:scale-[1.01] active:scale-[0.99] cursor-pointer disabled:opacity-60"
            >
              {submitting ? (
                <span className="w-5 h-5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
              ) : (
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  />
                </svg>
              )}
              <span>Continue with Google</span>
            </button>

            {/* Divider */}
            <div className="relative w-full flex items-center justify-center pt-1 pb-1">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/[0.08]" />
              </div>
              <div className="relative px-3 bg-[#090D18] text-[11px] text-[#556272] uppercase tracking-wider font-mono">
                or
              </div>
            </div>

            {/* Instant Demo Access Button */}
            <button
              type="button"
              onClick={handleGuestLogin}
              className="w-full py-3 px-4 rounded-xl bg-white/[0.05] hover:bg-white/[0.09] border border-white/[0.1] text-xs font-semibold text-slate-200 hover:text-white transition-all flex items-center justify-center gap-2 cursor-pointer hover:border-[#00E0E0]/30"
            >
              <svg className="w-4 h-4 text-[#00E0E0]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>Instant Demo Access</span>
            </button>
          </div>

          <p className="text-[11px] text-[#556272]">
            By continuing, you agree to our{" "}
            <a href="/privacy" className="text-[#A9BBCD] hover:underline">
              Privacy Policy
            </a>
            .
          </p>
        </div>
      </div>
    </div>
  );
}

export default AuthModal;
