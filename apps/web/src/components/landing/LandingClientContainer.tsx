"use client";

import React, { useRef, useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { PayScopeLandingHeader } from "@/components/landing/PayScopeLandingHeader";
import { IntroSequence } from "@/components/landing/IntroSequence";

interface LandingClientContainerProps {
  apiConnected: boolean;
}

export function LandingClientContainer({ apiConnected }: LandingClientContainerProps) {
  const [introFinished, setIntroFinished] = useState(() => {
    if (typeof window !== "undefined") {
      try {
        if (sessionStorage.getItem("payscope_intro_transition_seen") === "true") {
          return true;
        }
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
          return true;
        }
      } catch {
        // Fallback
      }
    }
    return false;
  });

  const headerLogoRef = useRef<HTMLDivElement | null>(null);
  const ambientVideoRef = useRef<HTMLVideoElement | null>(null);

  // Enforce the 0s -> 4.18s ambient video segment loop in the hero background
  useEffect(() => {
    const video = ambientVideoRef.current;
    if (!video) return;

    let animId: number;

    const checkAmbientLoop = () => {
      if (video.currentTime >= 4.18) {
        video.currentTime = 0;
        video.play().catch(() => {});
      }
      animId = requestAnimationFrame(checkAmbientLoop);
    };

    animId = requestAnimationFrame(checkAmbientLoop);
    return () => cancelAnimationFrame(animId);
  }, []);

  return (
    <div className="relative min-h-screen flex flex-col justify-between bg-[#011633] text-slate-100 overflow-x-hidden select-none">
      {/* 1. CINEMATIC ONE-TIME VIDEO INTRO OVERLAY */}
      <IntroSequence
        onComplete={() => setIntroFinished(true)}
        headerLogoRef={headerLogoRef}
      />

      {/* 2. BACKGROUND: Looping Hero Picker Visual (0s to 4.18s segment) + City Visual */}
      <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">
        {/* Ambient Looping Video Layer */}
        <div className="absolute inset-0 opacity-25 brightness-90 contrast-110">
          <video
            id="ambient-hero-video"
            ref={ambientVideoRef}
            src="/videos/payscope-picker-intro.mp4"
            autoPlay
            muted
            loop
            playsInline
            preload="auto"
            className="w-full h-full object-cover object-center pointer-events-none"
          />
        </div>

        {/* Ambient City Network Fallback Backdrop */}
        <div className="absolute inset-0 opacity-20 mix-blend-screen pointer-events-none">
          <Image
            src="/images/mandatelens-fintech-hero.jpg"
            alt="City data network recurring payment intelligence visual"
            fill
            priority
            sizes="100vw"
            className="object-cover object-center scale-105"
          />
        </div>

        {/* Luminous radial glow over the central city node */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full bg-[#00B8C7]/15 blur-[120px] anim-ambient-glow" />
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[450px] h-[450px] rounded-full bg-[#00E0E0]/10 blur-[90px]" />

        {/* Deep Vignette Gradient Overlays */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#011633] via-[#011633]/70 to-[#011633]/90" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#011633]/95 via-[#011633]/40 to-[#011633]/95" />

        {/* Circular Financial Data Rings */}
        <div className="absolute top-[48%] left-1/2 pointer-events-none">
          <div className="w-[360px] h-[360px] rounded-full border border-[#00E0E0]/25 anim-ring-primary" />
          <div className="w-[520px] h-[520px] rounded-full border border-[#00B8C7]/15 border-dashed anim-ring-secondary" />
          <div className="w-[720px] h-[720px] rounded-full border border-[#00B8C7]/10" />
        </div>
      </div>

      {/* 3. HEADER: With Left Hamburger & Top-Left Target Brand Logo */}
      <PayScopeLandingHeader
        apiConnected={apiConnected}
        headerLogoRef={headerLogoRef}
        showFinalLogo={introFinished}
      />

      {/* 4. HERO SECTION: Stage 3 Product Identity & Floating Insights */}
      <main className="relative z-10 flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 flex flex-col justify-center items-center text-center py-8 lg:py-16">
        {/* Floating Insight Pill 1 (Top Left) */}
        <div className="hidden lg:flex absolute left-8 top-28 items-center gap-3 px-4 py-2.5 rounded-xl bg-[#031B38]/90 border border-[#FFA52B]/30 backdrop-blur-md shadow-[0_8px_24px_rgba(0,0,0,0.5)] anim-float-1 anim-stage-3">
          <div className="w-2.5 h-2.5 rounded-full bg-[#FFA52B] animate-pulse shadow-[0_0_8px_rgba(255,165,43,0.8)]" />
          <div className="text-left font-mono">
            <span className="text-[11px] text-[#FFA52B] font-semibold block">Sustained Price Alert</span>
            <span className="text-xs text-[#F4F7FB]">+₹200/mo CloudDesk Pro</span>
          </div>
        </div>

        {/* Floating Insight Pill 2 (Top Right) */}
        <div className="hidden lg:flex absolute right-8 top-28 items-center gap-3 px-4 py-2.5 rounded-xl bg-[#031B38]/90 border border-[#00E0E0]/30 backdrop-blur-md shadow-[0_8px_24px_rgba(0,0,0,0.5)] anim-float-2 anim-stage-3">
          <div className="w-2.5 h-2.5 rounded-full bg-[#00E0E0] animate-pulse shadow-[0_0_8px_rgba(0,224,224,0.8)]" />
          <div className="text-left font-mono">
            <span className="text-[11px] text-[#00E0E0] font-semibold block">Annual Recurring Outflow</span>
            <span className="text-xs text-[#F4F7FB]">₹14,380/yr in Confirmed Mandates</span>
          </div>
        </div>

        {/* Floating Insight Pill 3 (Bottom Center-Right) */}
        <div className="hidden lg:flex absolute right-16 bottom-16 items-center gap-3 px-4 py-2.5 rounded-xl bg-[#031B38]/90 border border-[#00B8C7]/30 backdrop-blur-md shadow-[0_8px_24px_rgba(0,0,0,0.5)] anim-float-3 anim-stage-3-delayed">
          <div className="w-2.5 h-2.5 rounded-full bg-[#00B8C7] shadow-[0_0_8px_rgba(0,184,199,0.8)]" />
          <div className="text-left font-mono">
            <span className="text-[11px] text-[#00E0E0] font-semibold block">Verified Inactivity</span>
            <span className="text-xs text-[#F4F7FB]">Cult Gym: 0 Visits / 90 Days</span>
          </div>
        </div>

        {/* Central Content Composition */}
        <div className="max-w-3xl flex flex-col items-center gap-6">
          {/* Eyebrow Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold bg-gradient-to-r from-[#00B8C7]/10 via-[#00E0E0]/15 to-[#00B8C7]/10 border border-[#00E0E0]/30 text-[#00E0E0] shadow-[0_0_20px_rgba(0,224,224,0.2)] anim-stage-3">
            <span className="w-1.5 h-1.5 rounded-full bg-[#00E0E0] animate-pulse" />
            <span>Autonomous Recurring Payment Intelligence</span>
          </div>

          {/* Primary Cinematic Headline */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-white leading-[1.08] anim-stage-3">
            Every recurring payment.{" "}
            <span className="block mt-1 text-transparent bg-clip-text bg-gradient-to-r from-[#00E0E0] via-[#00B8C7] to-[#FFA52B] drop-shadow-[0_0_35px_rgba(0,224,224,0.4)]">
              Finally, in focus.
            </span>
          </h1>

          {/* Supporting Copy */}
          <p className="text-base sm:text-xl text-[#A9BBCD] font-normal leading-relaxed max-w-2xl anim-stage-3-delayed">
            Discover hidden commitments, understand recurring costs, detect unexpected changes and take control of your financial outflows.
          </p>

          {/* Primary & Secondary Call-to-Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center gap-4 pt-4 w-full sm:w-auto anim-stage-3-delayed">
            <Link
              href="/dashboard"
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-[#F08A00] to-[#FFA52B] hover:brightness-110 text-[#011633] font-bold text-sm tracking-wide transition-all shadow-[0_0_30px_rgba(240,138,0,0.4)] hover:shadow-[0_0_45px_rgba(240,138,0,0.6)] hover:scale-[1.02] active:scale-[0.98] text-center"
            >
              Open PayScope Dashboard →
            </Link>
            <Link
              href="/financial-impact"
              className="w-full sm:w-auto px-7 py-4 rounded-xl bg-gradient-to-r from-[#00B8C7] to-[#00E0E0] hover:brightness-110 text-[#011633] font-bold text-sm tracking-wide transition-all shadow-[0_0_20px_rgba(0,224,224,0.3)] hover:scale-[1.02] active:scale-[0.98] text-center"
            >
              Financial Projections
            </Link>
            <Link
              href="/cancellations"
              className="w-full sm:w-auto px-7 py-4 rounded-xl bg-[#031B38]/90 hover:bg-[#082746] border border-[#164B68] hover:border-[#00E0E0]/50 text-[#F4F7FB] font-semibold text-sm transition-all backdrop-blur-md text-center"
            >
              Cancellation Centre
            </Link>
          </div>

          {/* Key Assurance Signals */}
          <div className="flex flex-wrap justify-center items-center gap-6 pt-6 text-xs text-[#A9BBCD] anim-stage-3-delayed">
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-[#00E0E0]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Explainable Calculations
            </span>
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-[#00E0E0]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Synthetic Data Sandbox
            </span>
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-[#00E0E0]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Evidence-Backed Auditing
            </span>
          </div>
        </div>
      </main>

      {/* 5. FOOTER */}
      <footer className="relative z-10 border-t border-[#164B68]/40 bg-[#011633]/90 backdrop-blur-sm py-4 text-xs text-[#A9BBCD]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>PayScope &bull; Intelligent Recurring Payment Platform</span>
          <div className="flex items-center gap-4 text-[11px]">
            <Link href="/financial-impact" className="hover:text-[#00E0E0] transition-colors">
              Annual Outflows
            </Link>
            <Link href="/savings" className="hover:text-[#FFA52B] transition-colors">
              What-If Calculator
            </Link>
            <Link href="/upload" className="hover:text-white transition-colors">
              Statement Ingestion
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default LandingClientContainer;
