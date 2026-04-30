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
          <div className="text-xs font-medium text-emerald-400 mb-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            <span className="size-1.5 rounded-full bg-emerald-400" />
            Complete
          </div>
          <h1 className="text-3xl font-semibold tracking-tight">
            {job.results.length} client {job.results.length === 1 ? "response" : "responses"} generated
          </h1>
          <p className="text-zinc-500 text-sm mt-1 font-mono">{job.audio_filename}</p>
        </div>
        <div className="flex items-center gap-2">
          {job.zip_url && (
            <a
              href={job.zip_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-br from-accent to-accent-glow text-sm font-medium shadow-lg shadow-accent/20 hover:shadow-accent/40 transition-shadow"
            >
              <Package className="size-4" />
              Download all (.zip)
            </a>
          )}
          <button
            onClick={onReset}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-sm hover:bg-white/10 transition-colors"
          >
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
    <div className="glass rounded-2xl overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-start justify-between gap-4 p-6 hover:bg-white/5 transition-colors text-left"
      >
        <div className="flex items-start gap-4 min-w-0 flex-1">
          <div className="size-10 shrink-0 rounded-lg bg-accent/10 border border-accent/20 grid place-items-center">
            <FileText className="size-5 text-accent-glow" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-medium text-zinc-100 truncate">{r.client_display_name}</div>
            <div className="text-xs text-zinc-500 font-mono mt-0.5 truncate">{r.filename}</div>
            <div className="flex flex-wrap gap-1.5 mt-3">
              {r.topics.slice(0, 6).map((t) => (
                <span
                  key={t}
                  className="text-[11px] px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-zinc-400"
                >
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
            className="size-9 grid place-items-center rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
            title="Download markdown"
          >
            <Download className="size-4" />
          </a>
          <ChevronDown
            className={`size-5 text-zinc-500 transition-transform ${open ? "rotate-180" : ""}`}
          />
        </div>
      </button>

      {open && (
        <div className="border-t border-white/5 p-6 bg-zinc-950/40 max-h-[60vh] overflow-y-auto">
          <article className="prose-invert text-sm text-zinc-300 leading-relaxed [&_h2]:text-zinc-100 [&_h2]:font-semibold [&_h2]:text-base [&_h2]:mt-6 [&_h2]:mb-2 [&_hr]:my-4 [&_hr]:border-white/10 [&_ul]:my-2 [&_ul]:pl-5 [&_ul]:list-disc [&_p]:my-2 [&_strong]:text-zinc-100 first:[&_h2]:mt-0">
            <ReactMarkdown>{r.markdown}</ReactMarkdown>
          </article>
        </div>
      )}
    </div>
  );
}
