import React from "react";

export interface PayScopeLogoProps {
  variant?: "full" | "compact" | "navbar" | "favicon";
  className?: string;
  size?: number;
}

export function PayScopeLogo({
  variant = "full",
  className = "",
  size,
}: PayScopeLogoProps) {
  // Determine dimensions based on variant if size is not explicitly passed
  const getDimensions = () => {
    if (size) return { width: size, height: size };
    switch (variant) {
      case "compact":
        return { width: 36, height: 36 };
      case "navbar":
        return { width: 32, height: 32 };
      case "favicon":
        return { width: 24, height: 24 };
      case "full":
      default:
        return { width: 40, height: 40 };
    }
  };

  const { width, height } = getDimensions();

  // Programmatic SVG Symbol
  const Symbol = (
    <svg
      width={width}
      height={height}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="shrink-0 transition-transform duration-300 hover:scale-105"
      role="img"
      aria-label="PayScope Symbol"
    >
      <defs>
        {/* Teal/Cyan/Blue Gradient for the ribbon P */}
        <linearGradient id="pRibbonGrad" x1="15%" y1="10%" x2="85%" y2="90%">
          <stop offset="0%" stopColor="#00E0E0" />
          <stop offset="45%" stopColor="#00B8C7" />
          <stop offset="100%" stopColor="#006699" />
        </linearGradient>

        {/* Orange Glow/Accent for the orbital swoosh */}
        <linearGradient id="swooshGrad" x1="0%" y1="50%" x2="100%" y2="50%">
          <stop offset="0%" stopColor="#FFA52B" stopOpacity="0.2" />
          <stop offset="50%" stopColor="#F08A00" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#00E0E0" stopOpacity="0.8" />
        </linearGradient>

        {/* Ascending Analytics Bars Gradient */}
        <linearGradient id="barGrad" x1="0%" y1="100%" x2="0%" y2="0%">
          <stop offset="0%" stopColor="#00B8C7" />
          <stop offset="100%" stopColor="#00E0E0" />
        </linearGradient>
      </defs>

      {/* Background Soft Glow Disc */}
      <circle cx="50" cy="50" r="46" fill="#082746" stroke="#164B68" strokeWidth="1.5" />

      {/* Curved Orbital Swoosh wrapping dynamically around the P */}
      <path
        d="M 16 68 C 22 84, 76 86, 86 62 C 94 42, 70 20, 46 22"
        stroke="url(#swooshGrad)"
        strokeWidth="3.5"
        strokeLinecap="round"
        fill="none"
        strokeDasharray="90 10"
      />

      {/* Ribbon-like Stylized Uppercase 'P' */}
      {/* Vertical Spine */}
      <path
        d="M 30 26 C 30 24, 32 22, 34 22 L 42 22 C 44 22, 46 24, 46 26 L 46 74 C 46 76, 44 78, 42 78 L 34 78 C 32 78, 30 76, 30 74 Z"
        fill="url(#pRibbonGrad)"
      />
      {/* Upper Loop of P */}
      <path
        d="M 44 22 C 58 22, 72 26, 72 40 C 72 54, 58 58, 44 58 L 44 48 C 52 48, 60 46, 60 40 C 60 34, 52 32, 44 32 Z"
        fill="url(#pRibbonGrad)"
      />

      {/* 3 Ascending Analytics Bars nestled inside the P loop */}
      {/* Bar 1 (Short) */}
      <rect x="47" y="47" width="3.5" height="7" rx="1.5" fill="url(#barGrad)" />
      {/* Bar 2 (Medium) */}
      <rect x="52.5" y="42" width="3.5" height="12" rx="1.5" fill="url(#barGrad)" />
      {/* Bar 3 (Tall) */}
      <rect x="58" y="37" width="3.5" height="17" rx="1.5" fill="#FFA52B" />

      {/* Small Precision Node on the Swoosh */}
      <circle cx="84" cy="64" r="3" fill="#FFA52B" />
    </svg>
  );

  if (variant === "compact" || variant === "favicon") {
    return <div className={`inline-flex items-center ${className}`}>{Symbol}</div>;
  }

  // Wordmark: 'Pay' in white + 'Scope' in orange (#F08A00 / #FFA52B)
  const textSize = variant === "navbar" ? "text-xl" : "text-2xl";

  return (
    <div className={`inline-flex items-center gap-2.5 ${className}`}>
      {Symbol}
      <div className={`font-bold tracking-tight select-none ${textSize}`}>
        <span className="text-[#F4F7FB]">Pay</span>
        <span className="text-[#F08A00]">Scope</span>
      </div>
    </div>
  );
}

export default PayScopeLogo;
