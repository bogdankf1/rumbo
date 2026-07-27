"use client";

import { useCallback, useEffect, useState } from "react";
import { Chat } from "@/components/chat/Chat";
import { EmptyState } from "@/components/EmptyState";
import { Sidebar } from "@/components/Sidebar";
import { TopBar } from "@/components/TopBar";
import * as api from "@/lib/api";
import type { Job, Resume } from "@/lib/types";

export default function Home() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [demoLoading, setDemoLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [chatEpoch, setChatEpoch] = useState(0);

  const refresh = useCallback(async () => {
    const [r, j] = await Promise.all([api.listResumes(), api.listJobs()]);
    setResumes(r);
    setJobs(j);
    setLoaded(true);
  }, []);

  useEffect(() => {
    refresh().catch(() => setLoaded(true));
  }, [refresh]);

  async function loadDemo() {
    setDemoLoading(true);
    try {
      await api.loadDemo();
      await refresh();
      setChatEpoch((n) => n + 1); // demo wipes chat history; remount the chat
    } finally {
      setDemoLoading(false);
    }
  }

  const hasDocs = resumes.length > 0 || jobs.length > 0;

  return (
    <div className="flex h-screen flex-col">
      <TopBar onLoadDemo={loadDemo} demoLoading={demoLoading} />
      <div className="flex min-h-0 flex-1">
        <Sidebar
          resumes={resumes}
          jobs={jobs}
          onUploadResume={async (f) => {
            await api.uploadResume(f);
            await refresh();
          }}
          onUploadJobPdf={async (f) => {
            await api.uploadJobPdf(f);
            await refresh();
          }}
          onCreateJobText={async (title, text) => {
            await api.createJobText(title, text);
            await refresh();
          }}
          onActivate={(id) => api.activateResume(id).then(refresh)}
          onDeleteResume={(id) => api.deleteResume(id).then(refresh)}
          onDeleteJob={(id) => api.deleteJob(id).then(refresh)}
        />
        <main className="min-w-0 flex-1">
          {loaded && !hasDocs ? (
            <EmptyState onLoadDemo={loadDemo} demoLoading={demoLoading} />
          ) : (
            <Chat key={chatEpoch} />
          )}
        </main>
      </div>
    </div>
  );
}
