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
  const [stage, setStage] = useState<Stage>(() => {
    try {
      if (
        sessionStorage.getItem("payscope_intro_transition_seen") === "true" ||
        window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ) {
        return "COMPLETED";
      }
    } catch {
      // Ignore
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

  // High-precision video frame listener for seamless 4.18s transition
  useEffect(() => {
    if (stage !== "PLAYING") return;

    const video = videoRef.current;
    if (!video) return;

    const checkTimestamp = () => {
      if (!video) return;

      if (video.currentTime >= CARD_PICK_TIMESTAMP && !hasTriggeredEmergeRef.current) {
        hasTriggeredEmergeRef.current = true;
        setStage("EMERGING");

        setTimeout(() => {
          if (!headerLogoRef?.current) {
            finishIntro();
            return;
          }

          const targetRect = headerLogoRef.current.getBoundingClientRect();
          const targetX = targetRect.left + targetRect.width / 2;
          const targetY = targetRect.top + targetRect.height / 2;

          const currentX = window.innerWidth * 0.4934;
          const currentY = window.innerHeight * 0.6951;

          const deltaX = targetX - currentX;
          const deltaY = targetY - currentY;
          const scaleRatio = targetRect.height / 52;

          setFlyingStyle({
            transform: `translate3d(${deltaX}px, ${deltaY}px, 0) scale(${scaleRatio})`,
            transition: "transform 650ms cubic-bezier(0.22, 1, 0.36, 1), opacity 350ms ease-in-out",
            opacity: 1,
          });

          setStage("FLYING");

          setTimeout(() => {
            finishIntro();
          }, 650);
        }, 150);
      }

      if (stage === "PLAYING") {
        animationFrameRef.current = requestAnimationFrame(checkTimestamp);
      }
    };

    animationFrameRef.current = requestAnimationFrame(checkTimestamp);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [stage, finishIntro, headerLogoRef]);

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
      {/* 1. CINEMATIC VIDEO BACKGROUND */}
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
          preload="auto"
          className="w-full h-full object-contain md:object-cover pointer-events-none"
        />

        <div className="absolute bottom-0 inset-x-0 h-24 bg-gradient-to-t from-[#011633] to-transparent pointer-events-none" />
      </div>

      {/* 2. 3D EMERGING BRAND LOGO OVERLAY */}
      {(stage === "EMERGING" || stage === "FLYING") && (
        <div
          className="absolute inset-0 pointer-events-none z-30"
          style={{
            perspective: "1200px",
          }}
        >
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
