"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { PayScopeLogo } from "@/components/brand/PayScopeLogo";

interface IntroSequenceProps {
  onComplete: () => void;
  headerLogoRef?: React.RefObject<HTMLDivElement | null>;
}

type Stage = "PLAYING" | "ZOOMING" | "SWAPPING" | "FLYING" | "COMPLETED";

export function IntroSequence({ onComplete, headerLogoRef }: IntroSequenceProps) {
  // Check sessionStorage and prefers-reduced-motion in initial state
  const [stage, setStage] = useState<Stage>(() => {
    if (typeof window !== "undefined") {
      try {
        if (sessionStorage.getItem("payscope_intro_seen") === "true") {
          return "COMPLETED";
        }
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
          return "COMPLETED";
        }
      } catch {
        // Continue to playing
      }
    }
    return "PLAYING";
  });

  const [skipVisible, setSkipVisible] = useState(false);
  const [flyingStyle, setFlyingStyle] = useState<React.CSSProperties>({});

  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const hasTriggeredZoomRef = useRef(false);
  const hasTriggeredSwapRef = useRef(false);

  const finishIntro = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (videoRef.current) {
      videoRef.current.pause();
    }
    try {
      sessionStorage.setItem("payscope_intro_seen", "true");
    } catch {
      // sessionStorage might fail in strict private browsing
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

  // STAGE 4: Flight from center to the top-right header logo
  const startFlight = useCallback(() => {
    setStage("FLYING");

    let targetX = window.innerWidth - 140;
    let targetY = 32;

    const targetEl =
      (headerLogoRef && headerLogoRef.current) ||
      document.getElementById("header-target-logo");

    if (targetEl) {
      const rect = targetEl.getBoundingClientRect();
      targetX = rect.left + rect.width / 2;
      targetY = rect.top + rect.height / 2;
    }

    const startX = window.innerWidth / 2;
    const startY = window.innerHeight / 2;

    const deltaX = targetX - startX;
    const deltaY = targetY - startY;

    // Apply FLIP flight styles
    setFlyingStyle({
      transform: `translate(${deltaX}px, ${deltaY}px) scale(0.68)`,
      opacity: 1,
      transition: "transform 750ms cubic-bezier(0.2, 0.8, 0.2, 1), opacity 750ms ease-in",
    });

    setTimeout(() => {
      finishIntro();
    }, 780);
  }, [finishIntro, headerLogoRef]);

  // High-precision RAF loop tracking video playback time
  useEffect(() => {
    if (stage !== "PLAYING" && stage !== "ZOOMING") return;

    const checkTiming = () => {
      const video = videoRef.current;
      if (!video) return;

      const currentTime = video.currentTime;

      // STAGE 2: Moment picker fingers close onto the PayScope card (at t ≈ 4.15s - 4.25s)
      if (currentTime >= 4.15 && !hasTriggeredZoomRef.current) {
        hasTriggeredZoomRef.current = true;
        setStage("ZOOMING");
      }

      // STAGE 3: As camera finishes zooming into the card (at t ≈ 5.15s)
      if (currentTime >= 5.15 && !hasTriggeredSwapRef.current) {
        hasTriggeredSwapRef.current = true;
        setStage("SWAPPING");

        // Hold crisp logo prominently in center for 380ms, then launch flight to top-right
        setTimeout(() => {
          startFlight();
        }, 380);
      }

      if (video.ended) {
        if (!hasTriggeredSwapRef.current) {
          startFlight();
        }
      } else {
        animationFrameRef.current = requestAnimationFrame(checkTiming);
      }
    };

    animationFrameRef.current = requestAnimationFrame(checkTiming);
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [stage, startFlight]);

  if (stage === "COMPLETED") {
    return null;
  }

  return (
    <div
      ref={containerRef}
      className={`fixed inset-0 z-50 bg-[#011633] overflow-hidden select-none transition-opacity duration-700 ${
        stage === "FLYING" ? "opacity-0 pointer-events-none" : "opacity-100"
      }`}
      style={{
        perspective: "1000px",
      }}
    >
      {/* 1. CINEMATIC VIDEO ELEMENT */}
      <div
        className="absolute inset-0 w-full h-full flex items-center justify-center transition-transform duration-1000 ease-out"
        style={{
          // Measured logo coordinates in 1280x720 video:
          // Center of PayScope logo emblem + wordmark is at 48.24% X and 70.14% Y
          transformOrigin: "48.24% 70.14%",
          transform: stage === "ZOOMING" || stage === "SWAPPING" || stage === "FLYING" ? "scale(3.4)" : "scale(1)",
          filter: stage === "ZOOMING" || stage === "SWAPPING" || stage === "FLYING" ? "contrast(1.1) brightness(1.05)" : "none",
        }}
      >
        <video
          ref={videoRef}
          src="/videos/payscope-picker-intro.mp4"
          autoPlay
          muted
          playsInline
          controls={false}
          preload="auto"
          className="w-full h-full object-contain md:object-cover pointer-events-none"
          onEnded={finishIntro}
        />
      </div>

      {/* 2. CRISP VECTOR LOGO SWAP & FLIGHT ELEMENT */}
      {(stage === "SWAPPING" || stage === "FLYING") && (
        <div
          className="fixed inset-0 pointer-events-none z-50 flex items-center justify-center"
        >
          <div
            className="flex items-center gap-4 px-6 py-4 rounded-2xl bg-gradient-to-r from-[#008299] via-[#006e82] to-[#011633] border border-[#00E0E0]/40 shadow-[0_20px_50px_rgba(0,0,0,0.8),0_0_40px_rgba(0,224,224,0.3)] backdrop-blur-sm"
            style={{
              transform: stage === "SWAPPING" ? "scale(1.35)" : flyingStyle.transform || "scale(1)",
              opacity: stage === "SWAPPING" ? 1 : flyingStyle.opacity !== undefined ? flyingStyle.opacity : 1,
              transition:
                stage === "SWAPPING"
                  ? "transform 350ms cubic-bezier(0.16, 1, 0.3, 1), opacity 200ms ease-out"
                  : flyingStyle.transition,
            }}
          >
            <PayScopeLogo variant="full" size={48} />
          </div>
        </div>
      )}

      {/* 3. ACCESSIBLE SKIP INTRO CONTROL */}
      {skipVisible && stage !== "FLYING" && (
        <button
          onClick={finishIntro}
          className="absolute top-6 right-6 z-50 px-4 py-2 rounded-full bg-[#031B38]/80 hover:bg-[#082746] border border-[#164B68] text-xs font-semibold text-[#A9BBCD] hover:text-white transition-all shadow-lg backdrop-blur-md flex items-center gap-1.5 hover:scale-105 active:scale-95"
          aria-label="Skip introduction animation"
        >
          <span>Skip intro</span>
          <span className="text-[#FFA52B]">➔</span>
        </button>
      )}

      {/* Subtle bottom lighting accent */}
      <div className="absolute bottom-0 inset-x-0 h-24 bg-gradient-to-t from-[#011633] to-transparent pointer-events-none" />
    </div>
  );
}

export default IntroSequence;
