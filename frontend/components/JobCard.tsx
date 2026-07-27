"use client";

import { useState } from "react";
import type { Job } from "@/lib/types";
import { verdictColor } from "@/lib/types";
import { ScoreRing } from "./ScoreRing";

export function JobCard({ job, onDelete }: { job: Job; onDelete: () => void }) {
  const [open, setOpen] = useState(false);
  const fit = job.fit;

  return (
    <div
      className="group relative cursor-pointer rounded-lg border border-line bg-surface p-3 transition hover:border-faint"
      onClick={() => setOpen((v) => !v)}
    >
      <div className="flex items-center gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">
            <span className="mr-1.5 font-mono text-xs text-faint">#{job.seq}</span>
            {job.title}
          </p>
          <p className="mt-0.5 truncate text-xs text-muted">{job.company}</p>
          {fit && (
            <p
              className="mt-1 text-[10px] uppercase tracking-widest"
              style={{ color: verdictColor(fit.score) }}
            >
              {fit.verdict}
            </p>
          )}
        </div>
        {fit && <ScoreRing score={fit.score} />}
      </div>

      {open && fit && (
        <div className="mt-3 space-y-2 border-t border-line pt-2 text-xs">
          {fit.missing_required.length > 0 && (
            <div>
              <p className="mb-1 text-[10px] uppercase tracking-widest text-faint">
                missing required
              </p>
              {fit.missing_required.map((m) => (
                <div key={m.skill} className="mb-1.5 border-l-2 border-weak/70 pl-2">
                  <p className="font-medium text-ink">{m.skill}</p>
                  <p className="italic text-faint">&ldquo;{m.jd_evidence}&rdquo;</p>
                </div>
              ))}
            </div>
          )}
          <p className="text-muted">
            {fit.matched_required.length} of{" "}
            {fit.matched_required.length + fit.missing_required.length} required
            skills matched
            {fit.experience.required_years
              ? ` · asks ${fit.experience.required_years}y, has ${fit.experience.candidate_years}y`
              : ""}
          </p>
        </div>
      )}

      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        aria-label={`Delete ${job.title}`}
        className="absolute right-2 top-2 hidden text-faint hover:text-weak group-hover:block"
      >
        &times;
      </button>
    </div>
  );
}
