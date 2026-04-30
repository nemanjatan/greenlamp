import { useEffect, useRef, useState } from "react";

import { checkAuth, createJob, getJob } from "./api";
import { LoginScreen } from "./pages/Login";
import { ProcessingScreen } from "./pages/Processing";
import { ResultsScreen } from "./pages/Results";
import { UploadScreen } from "./pages/Upload";
import type { Job } from "./types";

type Screen =
  | { name: "upload" }
  | { name: "processing"; jobId: string }
  | { name: "results"; job: Job };

const UPLOADCARE_PUBLIC_KEY = import.meta.env.VITE_UPLOADCARE_PUBLIC_KEY ?? "595e6ddaeb54ef37ea58";

type AuthStatus = "checking" | "anonymous" | "authenticated";

export default function App() {
  const [authStatus, setAuthStatus] = useState<AuthStatus>("checking");
  const [screen, setScreen] = useState<Screen>({ name: "upload" });

  useEffect(() => {
    checkAuth().then((ok) => setAuthStatus(ok ? "authenticated" : "anonymous"));
  }, []);

  if (authStatus === "checking") {
    return <div className="min-h-screen" />;
  }
  if (authStatus === "anonymous") {
    return <LoginScreen onAuthenticated={() => setAuthStatus("authenticated")} />;
  }

  const handleUploaded = async (audioUrl: string, filename: string) => {
    const { id } = await createJob(audioUrl, filename);
    setScreen({ name: "processing", jobId: id });
  };

  const handleComplete = (job: Job) => setScreen({ name: "results", job });

  const handleReset = () => setScreen({ name: "upload" });

  return (
    <div className="min-h-screen flex flex-col">
      <Header onReset={handleReset} />
      <main className="flex-1 px-6 py-12 flex justify-center">
        <div className="w-full max-w-4xl">
          {screen.name === "upload" && (
            <UploadScreen
              uploadcarePublicKey={UPLOADCARE_PUBLIC_KEY}
              onUploaded={handleUploaded}
            />
          )}
          {screen.name === "processing" && (
            <PollingProcessingScreen jobId={screen.jobId} onComplete={handleComplete} />
          )}
          {screen.name === "results" && (
            <ResultsScreen job={screen.job} onReset={handleReset} />
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}

function PollingProcessingScreen({
  jobId,
  onComplete,
}: {
  jobId: string;
  onComplete: (job: Job) => void;
}) {
  const [job, setJob] = useState<Job | null>(null);
  const completedRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    const tick = async () => {
      try {
        const next = await getJob(jobId);
        if (cancelled) return;
        setJob(next);
        if (next.stage === "complete" && !completedRef.current) {
          completedRef.current = true;
          onComplete(next);
          return;
        }
        if (next.stage === "failed") return;
      } catch {
        // swallow transient network errors; next tick will retry
      }
      timer = setTimeout(tick, 2500);
    };
    tick();

    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [jobId, onComplete]);

  return <ProcessingScreen job={job} />;
}

function Header({ onReset }: { onReset: () => void }) {
  return (
    <header className="px-6 py-5 border-b border-white/5">
      <div className="mx-auto max-w-6xl flex items-center justify-between">
        <button
          onClick={onReset}
          className="flex items-center gap-2.5 group"
          title="Start over"
        >
          <span className="size-8 rounded-lg bg-gradient-to-br from-accent to-accent-glow grid place-items-center font-semibold text-sm text-white">
            W
          </span>
          <span className="font-semibold tracking-tight">
            Write to Freedom
            <span className="text-zinc-500 font-normal"> · Zoom Pipeline</span>
          </span>
        </button>
        <span className="text-xs text-zinc-500 hidden sm:inline">
          Drop a Zoom recording → get per-client markdown
        </span>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="px-6 py-6 text-center text-xs text-zinc-600">
      Developed by{" "}
      <a
        href="https://nemanjatanaskovic.com"
        target="_blank"
        rel="noopener noreferrer"
        className="text-zinc-400 hover:text-accent-glow transition-colors"
      >
        Nemanja Tanasković
      </a>
    </footer>
  );
}
