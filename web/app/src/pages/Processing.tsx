import { AlertCircle, Check, Loader2 } from "lucide-react";

import type { Job, JobStage } from "../types";
import { STAGE_LABELS, STAGE_ORDER } from "../types";

interface Props {
  job: Job | null;
}

export function ProcessingScreen({ job }: Props) {
  const currentStage: JobStage = job?.stage ?? "queued";
  const failed = currentStage === "failed";
  const visibleStages: JobStage[] = STAGE_ORDER.filter((s) => s !== "queued");
  const currentIndex = visibleStages.indexOf(currentStage);

  return (
    <div className="animate-fade-in max-w-2xl mx-auto">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-semibold tracking-tight mb-2 text-ink">
          {failed ? "Pipeline failed" : "Processing your recording"}
        </h1>
        {job?.audio_filename && (
          <p className="text-ink-mute font-mono text-sm">{job.audio_filename}</p>
        )}
      </div>

      <div className="card p-8">
        <ProgressBar pct={job?.progress_pct ?? 0} failed={failed} />

        <ul className="mt-8 space-y-1">
          {visibleStages.map((stage, idx) => {
            const isDone = !failed && (currentIndex > idx || currentStage === "complete");
            const isCurrent = !failed && currentStage === stage && currentStage !== "complete";
            const isFailedHere = failed && idx === currentIndex;
            return (
              <li
                key={stage}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                  isCurrent ? "bg-gold-tint" : ""
                }`}
              >
                <span className="size-5 grid place-items-center shrink-0">
                  {isDone && <Check className="size-4 text-gold-deep" />}
                  {isCurrent && <Loader2 className="size-4 text-gold-deep animate-spin" />}
                  {isFailedHere && <AlertCircle className="size-4 text-rose-500" />}
                  {!isDone && !isCurrent && !isFailedHere && (
                    <span className="size-2 rounded-full bg-rule" />
                  )}
                </span>
                <span
                  className={`text-sm ${
                    isCurrent
                      ? "text-ink font-medium"
                      : isDone
                      ? "text-ink-soft"
                      : "text-ink-mute"
                  }`}
                >
                  {STAGE_LABELS[stage]}
                </span>
              </li>
            );
          })}
        </ul>

        {job && job.duration_ms > 0 && (
          <div className="mt-8 pt-6 border-t border-rule grid grid-cols-3 gap-4 text-center">
            <Stat label="Duration" value={`${(job.duration_ms / 60000).toFixed(1)} min`} />
            <Stat label="Utterances" value={job.utterance_count.toString()} />
            <Stat label="Clients" value={(job.segments_count || "—").toString()} />
          </div>
        )}

        {failed && job?.error && (
          <div className="mt-6 p-4 rounded-lg bg-rose-50 border border-rose-200 text-sm text-rose-800 font-mono">
            {job.error}
          </div>
        )}
      </div>
    </div>
  );
}

function ProgressBar({ pct, failed }: { pct: number; failed: boolean }) {
  return (
    <div className="space-y-2">
      <div className="flex items-end justify-between text-sm">
        <span className="text-ink-soft">{failed ? "Halted" : "Progress"}</span>
        <span className="font-mono text-ink tabular-nums">
          {Math.min(100, Math.max(0, pct))}%
        </span>
      </div>
      <div className="h-2 rounded-full bg-paper border border-rule overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            failed ? "bg-rose-400" : "bg-gold"
          }`}
          style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
        />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-ink-mute mb-1">{label}</div>
      <div className="font-mono text-ink tabular-nums">{value}</div>
    </div>
  );
}
