import type { Job } from "./types";

export async function createJob(audioUrl: string, filename: string): Promise<{ id: string }> {
  const res = await fetch("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ audio_url: audioUrl, filename }),
    credentials: "include",
  });
  if (!res.ok) throw new Error(`createJob failed: ${res.status}`);
  return res.json();
}

export async function getJob(jobId: string): Promise<Job> {
  const res = await fetch(`/api/jobs/${jobId}`, { credentials: "include" });
  if (!res.ok) throw new Error(`getJob failed: ${res.status}`);
  return res.json();
}

export async function checkAuth(): Promise<boolean> {
  try {
    const res = await fetch("/api/auth/check", { credentials: "include" });
    if (!res.ok) return false;
    const data = (await res.json()) as { authenticated: boolean };
    return data.authenticated;
  } catch {
    return false;
  }
}

export async function login(password: string): Promise<boolean> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
    credentials: "include",
  });
  return res.ok;
}
