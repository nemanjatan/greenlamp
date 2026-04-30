// Mirror of web/api/schemas.py — kept in sync by hand for the MVP.

export type JobStage =
  | "queued"
  | "transcribing"
  | "cleaning"
  | "segmenting"
  | "enriching"
  | "uploading"
  | "complete"
  | "failed";

export interface JobResult {
  client_first_name: string;
  client_last_name: string;
  client_display_name: string;
  filename: string;
  markdown: string;
  cdn_url: string;
  topics: string[];
}

export interface Job {
  id: string;
  stage: JobStage;
  progress_pct: number;
  audio_filename: string;
  duration_ms: number;
  utterance_count: number;
  segments_count: number;
  results: JobResult[];
  zip_url: string | null;
  error: string | null;
  started_at: number | null;
  finished_at: number | null;
}

export const STAGE_LABELS: Record<JobStage, string> = {
  queued: "Queued",
  transcribing: "Transcribing audio",
  cleaning: "Cleaning utterances",
  segmenting: "Segmenting by client",
  enriching: "Distilling advice & principles",
  uploading: "Uploading results",
  complete: "Complete",
  failed: "Failed",
};

export const STAGE_ORDER: JobStage[] = [
  "queued",
  "transcribing",
  "cleaning",
  "segmenting",
  "enriching",
  "uploading",
  "complete",
];
