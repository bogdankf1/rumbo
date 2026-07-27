"use client";

import { useState } from "react";
import type { Job, Resume } from "@/lib/types";
import { JobCard } from "./JobCard";
import { PasteJobModal } from "./PasteJobModal";
import { ResumeCard } from "./ResumeCard";
import { UploadZone } from "./UploadZone";

export function Sidebar({
  resumes,
  jobs,
  onUploadResume,
  onUploadJobPdf,
  onCreateJobText,
  onActivate,
  onDeleteResume,
  onDeleteJob,
}: {
  resumes: Resume[];
  jobs: Job[];
  onUploadResume: (f: File) => Promise<void>;
  onUploadJobPdf: (f: File) => Promise<void>;
  onCreateJobText: (title: string | null, text: string) => Promise<void>;
  onActivate: (id: string) => void;
  onDeleteResume: (id: string) => void;
  onDeleteJob: (id: string) => void;
}) {
  const [pasteOpen, setPasteOpen] = useState(false);

  return (
    <aside className="flex w-84 shrink-0 flex-col gap-6 overflow-y-auto border-r border-line bg-surface/60 p-4">
      <section>
        <h2 className="mb-2 text-[10px] uppercase tracking-[0.25em] text-faint">
          Resume
        </h2>
        <div className="space-y-2">
          {resumes.map((r) => (
            <ResumeCard
              key={r.id}
              resume={r}
              onActivate={() => onActivate(r.id)}
              onDelete={() => onDeleteResume(r.id)}
            />
          ))}
          <UploadZone
            compact={resumes.length > 0}
            label="Drop a resume PDF or click"
            pendingLabel="Reading your resume..."
            onFile={onUploadResume}
          />
        </div>
      </section>

      <section>
        <h2 className="mb-2 text-[10px] uppercase tracking-[0.25em] text-faint">
          Positions
        </h2>
        <div className="space-y-2">
          {jobs.map((j) => (
            <JobCard key={j.id} job={j} onDelete={() => onDeleteJob(j.id)} />
          ))}
          <UploadZone
            compact={jobs.length > 0}
            label="Drop a job posting PDF or click"
            pendingLabel="Reading the posting..."
            onFile={onUploadJobPdf}
          />
          <button
            onClick={() => setPasteOpen(true)}
            className="w-full rounded-lg border border-dashed border-line px-3 py-2 text-xs text-faint transition hover:border-faint hover:text-muted"
          >
            Or paste posting text
          </button>
        </div>
      </section>

      {pasteOpen && (
        <PasteJobModal
          onSubmit={onCreateJobText}
          onClose={() => setPasteOpen(false)}
        />
      )}
    </aside>
  );
}
