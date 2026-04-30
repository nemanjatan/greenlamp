import { FileUploaderRegular } from "@uploadcare/react-uploader";
import "@uploadcare/react-uploader/core.css";
import { useState } from "react";

interface UploadedFileInfo {
  cdnUrl: string | null;
  name: string | null;
}

interface Props {
  uploadcarePublicKey: string;
  onUploaded: (audioUrl: string, filename: string) => void | Promise<void>;
}

export function UploadScreen({ uploadcarePublicKey, onUploaded }: Props) {
  const [uploaded, setUploaded] = useState<UploadedFileInfo | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!uploaded?.cdnUrl) return;
    setSubmitting(true);
    try {
      await onUploaded(uploaded.cdnUrl, uploaded.name ?? "recording");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="text-center mb-10">
        <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight mb-4">
          Turn a Zoom call into <span className="bg-gradient-to-r from-accent to-accent-glow bg-clip-text text-transparent">per-client markdown</span>.
        </h1>
        <p className="text-zinc-400 text-lg max-w-xl mx-auto">
          Drop an MP4 or M4A. We transcribe, segment by client, distill each Q&amp;A into advice and principles, and hand you the rendered markdown.
        </p>
      </div>

      <div className="glass rounded-2xl p-8 sm:p-10 shadow-2xl">
        <div className="mb-6">
          <h2 className="text-sm font-medium text-zinc-400 mb-3">Step 1 · Upload your call recording</h2>
          <FileUploaderRegular
            pubkey={uploadcarePublicKey}
            sourceList="local"
            classNameUploader="uc-dark"
            multiple={false}
            onChange={(e) => {
              const f = e.allEntries.find((entry) => entry.status === "success");
              if (f) {
                setUploaded({ cdnUrl: f.cdnUrl, name: f.name ?? f.fileInfo?.originalFilename ?? null });
              }
            }}
          />
        </div>

        {uploaded?.cdnUrl && (
          <div className="border-t border-white/5 pt-6 animate-fade-in">
            <h2 className="text-sm font-medium text-zinc-400 mb-3">Step 2 · Process</h2>
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div className="text-sm text-zinc-300 truncate flex-1">
                <span className="text-zinc-500">Ready: </span>
                <span className="font-mono">{uploaded.name}</span>
              </div>
              <button
                disabled={submitting}
                onClick={handleSubmit}
                className="px-6 py-2.5 rounded-lg bg-gradient-to-br from-accent to-accent-glow font-medium text-sm shadow-lg shadow-accent/20 hover:shadow-accent/40 transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? "Starting…" : "Run pipeline →"}
              </button>
            </div>
          </div>
        )}
      </div>

      <p className="text-center text-xs text-zinc-600 mt-6">
        Processing typically takes 2–8 minutes depending on call length
      </p>
    </div>
  );
}
