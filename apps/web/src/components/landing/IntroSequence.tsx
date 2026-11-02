"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { PayScopeLogo } from "@/components/brand/PayScopeLogo";

interface IntroSequenceProps {
  onComplete: () => void;
  headerLogoRef?: React.RefObject<HTMLDivElement | null>;
}

type Stage = "PLAYING" | "EMERGING" | "FLYING" | "COMPLETED";

// Exact card pick moment in 1280x720 24FPS video (finger pads contact and grip card)
const CARD_PICK_TIMESTAMP = 4.18;

export function IntroSequence({ onComplete, headerLogoRef }: IntroSequenceProps) {
  // Check sessionStorage and prefers-reduced-motion in initial state
  const [stage, setStage] = useState<Stage>(() => {
    if (typeof window !== "undefined") {
      try {
        if (sessionStorage.getItem("payscope_intro_transition_seen") === "true") {
          return "COMPLETED";
        }
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
          return "COMPLETED";
        }
      } catch {
        // Fallback to playing
      }
    }
    return "PLAYING";
  });

  const [skipVisible, setSkipVisible] = useState(false);
  const [flyingStyle, setFlyingStyle] = useState<React.CSSProperties>({});

  const videoRef = useRef<HTMLVideoElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const hasTriggeredEmergeRef = useRef(false);

  const finishIntro = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (videoRef.current) {
      videoRef.current.pause();
    }
    try {
      sessionStorage.setItem("payscope_intro_transition_seen", "true");
    } catch {
      // Ignore strict private browsing errors
    }
    setStage("COMPLETED");
    onComplete();
  }, [onComplete]);

  // If initial stage is already COMPLETED, notify parent
  useEffect(() => {
    if (stage === "COMPLETED") {
      onComplete();
    }
  }, [stage, onComplete]);

  // Autoplay handler with graceful fallback
  useEffect(() => {
    if (stage !== "PLAYING" || !videoRef.current) return;

    const skipTimer = setTimeout(() => setSkipVisible(true), 600);

    const playPromise = videoRef.current.play();
    if (playPromise !== undefined) {
      playPromise.catch((err) => {
        console.warn("Autoplay blocked or failed, skipping intro sequence:", err);
        finishIntro();
      });
    }

    return () => clearTimeout(skipTimer);
  }, [stage, finishIntro]);

  // STAGE 3: Flight from emerging card position into the TOP-LEFT header logo target
  const startFlightToTopLeft = useCallback(() => {
    setStage("FLYING");

    // Default top-left target fallback beside hamburger (x: ~160px, y: 32px)
    let targetX = 160;
    let targetY = 32;

    const targetEl =
      (headerLogoRef && headerLogoRef.current) ||
      document.getElementById("header-target-logo");

    if (targetEl) {
      const rect = targetEl.getBoundingClientRect();
      targetX = rect.left + rect.width / 2;
      targetY = rect.top + rect.height / 2;
    }

    // Start coordinates: Exactly at the card center (49.34% X, 69.51% Y)
    const startX = window.innerWidth * 0.4934;
    const startY = window.innerHeight * 0.6951;

    const deltaX = targetX - startX;
    const deltaY = targetY - startY;

    // Apply FLIP flight styles: Up and to the LEFT into header beside hamburger
    setFlyingStyle({
      transform: `translate(${deltaX}px, ${deltaY}px) scale(0.68)`,
      opacity: 1,
      transition: "transform 750ms cubic-bezier(0.16, 1, 0.3, 1), opacity 750ms ease-in",
    });

    setTimeout(() => {
      finishIntro();
    }, 780);
  }, [finishIntro, headerLogoRef]);

  // High-precision RAF loop tracking video playback time and enforcing the 0 -> 4.18s segment loop
  useEffect(() => {
    if (stage !== "PLAYING") return;

    const checkTiming = () => {
      const video = videoRef.current;
      if (!video) return;

      const currentTime = video.currentTime;

      // STAGE 2: Moment picker fingers close onto the PayScope card (at t ≈ 4.18s)
      if (currentTime >= CARD_PICK_TIMESTAMP && !hasTriggeredEmergeRef.current) {
        hasTriggeredEmergeRef.current = true;
        setStage("EMERGING");

        // Hold the video paused at the exact grip frame so the emerging card lifts directly from the scene
        video.pause();

        // Hold crisp emerging 3D logo prominently in position for 450ms, then launch flight to TOP-LEFT
        setTimeout(() => {
          startFlightToTopLeft();
        }, 450);
        return;
      }

      animationFrameRef.current = requestAnimationFrame(checkTiming);
    };

    animationFrameRef.current = requestAnimationFrame(checkTiming);
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [stage, startFlightToTopLeft]);

  if (stage === "COMPLETED") {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 overflow-hidden select-none pointer-events-none"
      style={{
        perspective: "1200px",
      }}
    >
      {/* 1. CINEMATIC VIDEO BACKDROP (Fades out during flight so homepage content reveals smoothly) */}
      <div
        className={`absolute inset-0 bg-[#011633] transition-opacity duration-700 ${
          stage === "FLYING" ? "opacity-0" : "opacity-100"
        }`}
      >
        <video
          id="intro-video"
          ref={videoRef}
          src="/videos/payscope-picker-intro.mp4"
          autoPlay
          muted
          playsInline
          controls={false}
          preload="auto"
          className="w-full h-full object-contain md:object-cover pointer-events-none"
        />
        {/* Subtle bottom lighting accent */}
        <div className="absolute bottom-0 inset-x-0 h-24 bg-gradient-to-t from-[#011633] to-transparent pointer-events-none" />
      </div>

      {/* 2. 3D EMERGING VECTOR LOGO & WORDMARK LOCKUP (Emerges forward from card position, then flies to top-left) */}
      {(stage === "EMERGING" || stage === "FLYING") && (
        <div
          className="fixed inset-0 pointer-events-none z-50"
          style={{
            perspective: "1200px",
          }}
        >
          {/* Card positioned at measured coordinates: X = 49.34%, Y = 69.51% */}
          <div
            className="absolute -translate-x-1/2 -translate-y-1/2 flex items-center gap-3.5 px-6 py-4 rounded-2xl bg-gradient-to-r from-[#008299] via-[#006e82] to-[#011633] border border-[#00E0E0]/60 shadow-[0_25px_60px_rgba(0,0,0,0.85),0_0_40px_rgba(0,224,224,0.35)] backdrop-blur-md"
            style={{
              left: "49.34%",
              top: "69.51%",
              transform:
                stage === "EMERGING"
                  ? "translate3d(0, -18px, 100px) scale(1.15)"
                  : flyingStyle.transform || "scale(1)",
              opacity: 1,
              transition:
                stage === "EMERGING"
                  ? "transform 400ms cubic-bezier(0.16, 1, 0.3, 1), opacity 250ms ease-out"
                  : flyingStyle.transition,
              transformStyle: "preserve-3d",
            }}
          >
            {/* PayScope Emblem and Wordmark combined as ONE brand lockup */}
            <PayScopeLogo variant="full" size={44} />
          </div>
        </div>
      )}

      {/* 3. ACCESSIBLE SKIP INTRO CONTROL */}
      {skipVisible && stage !== "FLYING" && (
        <button
          onClick={finishIntro}
          className="absolute top-6 right-6 z-50 pointer-events-auto px-4 py-2 rounded-full bg-[#031B38]/85 hover:bg-[#082746] border border-[#164B68] text-xs font-semibold text-[#A9BBCD] hover:text-white transition-all shadow-lg backdrop-blur-md flex items-center gap-1.5 hover:scale-105 active:scale-95 cursor-pointer"
          aria-label="Skip introduction animation"
        >
          <span>Skip intro</span>
          <span className="text-[#FFA52B]">⏭</span>
        </button>
      )}
    </div>
  );
}

export default IntroSequence;
