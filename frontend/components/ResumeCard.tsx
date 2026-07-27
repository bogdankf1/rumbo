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
  // Fixed two-line layout: the active badge and the delete button live in the
  // top-right corner (swapping on hover), so selection never changes height
  // and items never shift.
  return (
    <div
      onClick={active ? undefined : onActivate}
      className={`group relative rounded-lg border p-3 pr-14 transition ${
        active
          ? "border-accent/70 bg-raised"
          : "cursor-pointer border-line bg-surface hover:border-faint"
      }`}
    >
      <p className="truncate text-sm font-medium">{resume.name}</p>
      <p className="mt-0.5 truncate text-xs text-muted">
        {resume.extracted.headline} · {resume.extracted.total_years_experience}y
      </p>
      {active && (
        <span className="absolute right-2.5 top-3 text-[9px] uppercase tracking-widest text-accent group-hover:hidden">
          active
        </span>
      )}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        aria-label={`Delete ${resume.name}`}
        className="absolute right-1.5 top-1.5 hidden h-5 w-5 items-center justify-center rounded-full text-faint transition hover:bg-weak/20 hover:text-weak group-hover:flex"
      >
        &times;
      </button>
    </div>
  );
}
