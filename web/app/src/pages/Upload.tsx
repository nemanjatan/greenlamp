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
      <div className="text-center mb-12">
        <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight mb-5 text-ink">
          Turn a Zoom call into{" "}
          <span className="font-script font-bold text-gold-deep text-[1.15em] leading-none">
            per-client markdown
          </span>
          .
        </h1>
        <p className="text-ink-soft text-lg max-w-xl mx-auto leading-relaxed">
          Drop your call's audio recording. We transcribe, segment by client, distill each Q&amp;A into advice and principles, and hand you the rendered markdown.
        </p>
      </div>

      <div className="card p-8 sm:p-10">
        <div className="mb-2 flex items-baseline gap-2">
          <span className="font-script text-2xl text-gold-deep leading-none">Step 1</span>
          <span className="text-sm text-ink-mute">· Upload your call recording</span>
        </div>
        <div className="mt-4">
          <FileUploaderRegular
            pubkey={uploadcarePublicKey}
            sourceList="local"
            classNameUploader="uc-light"
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
          <div className="border-t border-rule pt-6 mt-6 animate-fade-in">
            <div className="mb-3 flex items-baseline gap-2">
              <span className="font-script text-2xl text-gold-deep leading-none">Step 2</span>
              <span className="text-sm text-ink-mute">· Process</span>
            </div>
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div className="text-sm text-ink-soft truncate flex-1">
                <span className="text-ink-mute">Ready: </span>
                <span className="font-mono text-ink">{uploaded.name}</span>
              </div>
              <button disabled={submitting} onClick={handleSubmit} className="btn-primary">
                {submitting ? "Starting…" : "Run pipeline →"}
              </button>
            </div>
          </div>
        )}
      </div>

      <p className="text-center text-xs text-ink-mute mt-6">
        Processing typically takes 2–8 minutes depending on call length
      </p>
    </div>
  );
}
