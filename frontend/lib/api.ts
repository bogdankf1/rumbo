import type { ChatMessage, Job, Resume } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, init);
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      detail = (await resp.json()).detail ?? detail;
    } catch {
      // keep statusText
    }
    throw new Error(detail);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

export const listResumes = () => request<Resume[]>("/api/resumes");

export function uploadResume(file: File): Promise<Resume> {
  const body = new FormData();
  body.append("file", file);
  return request("/api/resumes", { method: "POST", body });
}

export const activateResume = (id: string) =>
  request<Resume>(`/api/resumes/${id}/activate`, { method: "POST" });

export const deleteResume = (id: string) =>
  request<void>(`/api/resumes/${id}`, { method: "DELETE" });

export const listJobs = () => request<Job[]>("/api/jobs");

export function uploadJobPdf(file: File): Promise<Job> {
  const body = new FormData();
  body.append("file", file);
  return request("/api/jobs", { method: "POST", body });
}

export const createJobText = (title: string | null, text: string) =>
  request<Job>("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, text }),
  });

export const deleteJob = (id: string) =>
  request<void>(`/api/jobs/${id}`, { method: "DELETE" });

export const loadDemo = () =>
  request<{ resumes: number; jobs: number }>("/api/demo", { method: "POST" });

export const listMessages = () => request<ChatMessage[]>("/api/chat/messages");
