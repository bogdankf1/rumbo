"use client";

import type { Resume } from "@/lib/types";

export function ResumeCard({
  resume,
  onActivate,
  onDelete,
}: {
  resume: Resume;
  onActivate: () => void;
  onDelete: () => void;
}) {
  const active = resume.is_active;
  return (
    <div
      onClick={active ? undefined : onActivate}
      className={`group relative cursor-pointer rounded-lg border p-3 transition ${
        active
          ? "border-accent/70 bg-raised"
          : "border-line bg-surface hover:border-faint"
      }`}
    >
      <div className="flex items-center gap-2">
        {active && <span className="h-1.5 w-1.5 rounded-full bg-accent" />}
        <span className="text-sm font-medium">{resume.name}</span>
      </div>
      <p className="mt-0.5 text-xs text-muted">
        {resume.extracted.headline} · {resume.extracted.total_years_experience}y
      </p>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        aria-label={`Delete ${resume.name}`}
        className="absolute right-2 top-2 hidden text-faint hover:text-weak group-hover:block"
      >
        &times;
      </button>
      {active && (
        <span className="mt-1 block text-[10px] uppercase tracking-widest text-accent">
          active
        </span>
      )}
    </div>
  );
}
