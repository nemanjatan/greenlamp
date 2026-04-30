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
        <h1 className="text-3xl font-semibold tracking-tight mb-2">
          {failed ? "Pipeline failed" : "Processing your recording"}
        </h1>
        {job?.audio_filename && (
          <p className="text-zinc-500 font-mono text-sm">{job.audio_filename}</p>
        )}
      </div>

      <div className="glass rounded-2xl p-8 shadow-2xl">
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
                  isCurrent ? "bg-accent/10" : ""
                }`}
              >
                <span className="size-5 grid place-items-center shrink-0">
                  {isDone && <Check className="size-4 text-emerald-400" />}
                  {isCurrent && <Loader2 className="size-4 text-accent-glow animate-spin" />}
                  {isFailedHere && <AlertCircle className="size-4 text-rose-400" />}
                  {!isDone && !isCurrent && !isFailedHere && (
                    <span className="size-2 rounded-full bg-zinc-700" />
                  )}
                </span>
                <span
                  className={`text-sm ${
                    isCurrent
                      ? "text-zinc-100 font-medium"
                      : isDone
                      ? "text-zinc-300"
                      : "text-zinc-500"
                  }`}
                >
                  {STAGE_LABELS[stage]}
                </span>
              </li>
            );
          })}
        </ul>

        {job && job.duration_ms > 0 && (
          <div className="mt-8 pt-6 border-t border-white/5 grid grid-cols-3 gap-4 text-center">
            <Stat label="Duration" value={`${(job.duration_ms / 60000).toFixed(1)} min`} />
            <Stat label="Utterances" value={job.utterance_count.toString()} />
            <Stat label="Clients" value={(job.segments_count || "—").toString()} />
          </div>
        )}

        {failed && job?.error && (
          <div className="mt-6 p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-sm text-rose-200 font-mono">
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
        <span className="text-zinc-400">{failed ? "Halted" : "Progress"}</span>
        <span className="font-mono text-zinc-300 tabular-nums">
          {Math.min(100, Math.max(0, pct))}%
        </span>
      </div>
      <div className="h-2 rounded-full bg-zinc-800/80 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            failed
              ? "bg-rose-500"
              : "bg-gradient-to-r from-accent to-accent-glow bg-[length:200%_100%] animate-shimmer"
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
      <div className="text-xs text-zinc-500 mb-1">{label}</div>
      <div className="font-mono text-zinc-200 tabular-nums">{value}</div>
    </div>
  );
}
