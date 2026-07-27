"use client";

import { useEffect, useState } from "react";
import { verdictColor } from "@/lib/types";

export function ScoreRing({ score, size = 44 }: { score: number; size?: number }) {
  const [drawn, setDrawn] = useState(0);
  useEffect(() => {
    const id = requestAnimationFrame(() => setDrawn(score));
    return () => cancelAnimationFrame(id);
  }, [score]);

  const stroke = 3.5;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const color = verdictColor(score);

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="var(--color-line)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c - (c * drawn) / 100}
          style={{ transition: "stroke-dashoffset 0.9s cubic-bezier(0.22, 1, 0.36, 1)" }}
        />
      </svg>
      <span
        className="absolute inset-0 flex items-center justify-center font-mono text-xs"
        style={{ color }}
      >
        {score}
      </span>
    </div>
  );
}
