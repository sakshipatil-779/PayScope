import React from "react";

export interface PayScopeLogoProps {
  variant?: "full" | "compact" | "navbar" | "favicon";
  className?: string;
  size?: number;
  showWordmark?: boolean;
}

export function PayScopeLogo({
  variant = "full",
  className = "",
  size,
  showWordmark = true,
}: PayScopeLogoProps) {
  // Dimensions tailored to variants
  const getDimensions = () => {
    if (size) return { iconSize: size, textClass: "text-lg", gap: "gap-2" };
    switch (variant) {
      case "compact":
        return { iconSize: 34, textClass: "text-lg", gap: "gap-2" };
      case "navbar":
        return { iconSize: 32, textClass: "text-xl", gap: "gap-2.5" };
      case "favicon":
        return { iconSize: 24, textClass: "text-sm", gap: "gap-1.5" };
      case "full":
      default:
        return { iconSize: 42, textClass: "text-2xl", gap: "gap-3" };
    }
  };

  const { iconSize, textClass, gap } = getDimensions();
  const shouldDisplayWordmark = variant !== "compact" && variant !== "favicon" && showWordmark;

  // The authentic multicolour ribbon P emblem from the reference video
  const Symbol = (
    <svg
      width={iconSize}
      height={(iconSize * 1.1).toFixed(1)}
      viewBox="0 0 100 110"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="shrink-0 transition-transform duration-300 hover:scale-105"
      role="img"
      aria-label="PayScope Ribbon Symbol"
    >
      <defs>
        {/* 1. Front Vertical Stem Gradient: Violet -> Fuchsia -> Coral -> Amber */}
        <linearGradient id="psStemArchGrad" x1="0%" y1="100%" x2="50%" y2="0%">
          <stop offset="0%" stopColor="#9333EA" />
          <stop offset="20%" stopColor="#C026D3" />
          <stop offset="42%" stopColor="#EA580C" />
          <stop offset="68%" stopColor="#F97316" />
          <stop offset="88%" stopColor="#F59E0B" />
          <stop offset="100%" stopColor="#FBBF24" />
        </linearGradient>

        {/* 2. Upper Arch & Right Bowl Gradient: Amber -> Lime -> Emerald -> Cyan -> Teal */}
        <linearGradient id="psBowlGrad" x1="15%" y1="0%" x2="85%" y2="95%">
          <stop offset="0%" stopColor="#FBBF24" />
          <stop offset="20%" stopColor="#84CC16" />
          <stop offset="42%" stopColor="#10B981" />
          <stop offset="68%" stopColor="#06B6D4" />
          <stop offset="88%" stopColor="#00B8C7" />
          <stop offset="100%" stopColor="#0284C7" />
        </linearGradient>

        {/* 3. Return Under-Pass & Lower Loop Gradient: Blue -> Azure -> Indigo -> Violet */}
        <linearGradient id="psLowerLoopGrad" x1="100%" y1="20%" x2="0%" y2="80%">
          <stop offset="0%" stopColor="#0284C7" />
          <stop offset="35%" stopColor="#2563EB" />
          <stop offset="65%" stopColor="#4F46E5" />
          <stop offset="85%" stopColor="#7C3AED" />
          <stop offset="100%" stopColor="#9333EA" />
        </linearGradient>

        {/* Ribbon Depth Shadow filter */}
        <filter id="psRibbonShadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="1" dy="3.5" stdDeviation="3" floodColor="#002b3a" floodOpacity="0.45" />
        </filter>
      </defs>

      <g filter="url(#psRibbonShadow)">
        {/* ORBITAL SWOOSH: Curved digital trajectory accent */}
        <path
          d="M 12 78 C 16 98, 52 110, 84 92 C 98 84, 102 62, 94 44 C 88 30, 76 20, 64 16"
          stroke="url(#psBowlGrad)"
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeDasharray="4 3"
          opacity="0.65"
        />

        {/* THREE ASCENDING ANALYTICS BARS: Inside/beside the lower bowl */}
        <rect x="52" y="50" width="3.5" height="12" rx="1.75" fill="#00E0E0" opacity="0.85" />
        <rect x="58.5" y="42" width="3.5" height="20" rx="1.75" fill="#00B8C7" opacity="0.9" />
        <rect x="65" y="32" width="3.5" height="30" rx="1.75" fill="#F08A00" opacity="0.95" />

        {/* BACK/LOWER LAYER: Ribbon passes under the vertical stem to lower-left loop */}
        <path
          d="M 64 66 C 54 68, 40 68, 30 76 C 18 88, 14 104, 25 106 C 36 108, 44 98, 44 84"
          stroke="url(#psLowerLoopGrad)"
          strokeWidth="19"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* UPPER BOWL: Curves from top of stem around to the right and back in to meet the loop */}
        <path
          d="M 44 34 C 44 16, 62 10, 76 16 C 92 24, 96 44, 88 58 C 82 70, 68 70, 52 66"
          stroke="url(#psBowlGrad)"
          strokeWidth="19"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* FRONT VERTICAL STEM: Rises cleanly from the lower fold up to the top arch */}
        <path
          d="M 28 100 C 34 92, 44 84, 44 70 L 44 24"
          stroke="url(#psStemArchGrad)"
          strokeWidth="19"
          strokeLinecap="round"
        />
      </g>
    </svg>
  );

  return (
    <div className={`inline-flex items-center ${gap} ${className}`}>
      {Symbol}
      {shouldDisplayWordmark && (
        <span
          className={`font-black tracking-tight select-none ${textClass}`}
          style={{ letterSpacing: "-0.025em" }}
        >
          <span className="text-[#F4F7FB]">Pay</span>
          <span className="text-[#F08A00]">Scope</span>
        </span>
      )}
    </div>
  );
}

export default PayScopeLogo;
