import { ChevronDown, Download, FileText, Package, RefreshCw } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";

import type { Job, JobResult } from "../types";

interface Props {
  job: Job;
  onReset: () => void;
}

export function ResultsScreen({ job, onReset }: Props) {
  return (
    <div className="animate-fade-in">
      <div className="flex items-start justify-between flex-wrap gap-4 mb-8">
        <div>
          <div className="text-xs font-medium text-gold-deep mb-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gold-tint border border-gold/30">
            <span className="size-1.5 rounded-full bg-gold-deep" />
            Complete
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-ink">
            {job.results.length} client {job.results.length === 1 ? "response" : "responses"} generated
          </h1>
          <p className="text-ink-mute text-sm mt-1 font-mono">{job.audio_filename}</p>
        </div>
        <div className="flex items-center gap-2">
          {job.zip_url && (
            <a
              href={job.zip_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary"
            >
              <Package className="size-4" />
              Download all (.zip)
            </a>
          )}
          <button onClick={onReset} className="btn-secondary">
            <RefreshCw className="size-4" />
            New
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {job.results.map((r) => (
          <ResultCard key={r.filename} r={r} />
        ))}
      </div>
    </div>
  );
}

function ResultCard({ r }: { r: JobResult }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="card overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-start justify-between gap-4 p-6 hover:bg-paper transition-colors text-left"
      >
        <div className="flex items-start gap-4 min-w-0 flex-1">
          <div className="size-10 shrink-0 rounded-lg bg-gold-tint border border-gold/30 grid place-items-center">
            <FileText className="size-5 text-gold-deep" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-medium text-ink truncate">{r.client_display_name}</div>
            <div className="text-xs text-ink-mute font-mono mt-0.5 truncate">{r.filename}</div>
            <div className="flex flex-wrap gap-1.5 mt-3">
              {r.topics.slice(0, 6).map((t) => (
                <span key={t} className="pill">
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <a
            href={r.cdn_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="size-9 grid place-items-center rounded-lg bg-paper border border-rule hover:bg-gold-tint transition-colors"
            title="Download markdown"
          >
            <Download className="size-4 text-ink-soft" />
          </a>
          <ChevronDown
            className={`size-5 text-ink-mute transition-transform ${open ? "rotate-180" : ""}`}
          />
        </div>
      </button>

      {open && (
        <div className="border-t border-rule p-6 bg-paper max-h-[60vh] overflow-y-auto">
          <article className="text-sm text-ink-soft leading-relaxed [&_h2]:text-ink [&_h2]:font-semibold [&_h2]:text-base [&_h2]:mt-6 [&_h2]:mb-2 [&_hr]:my-4 [&_hr]:border-rule [&_ul]:my-2 [&_ul]:pl-5 [&_ul]:list-disc [&_p]:my-2 [&_strong]:text-ink first:[&_h2]:mt-0">
            <ReactMarkdown>{r.markdown}</ReactMarkdown>
          </article>
        </div>
      )}
    </div>
  );
}
