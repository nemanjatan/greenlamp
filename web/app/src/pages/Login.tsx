import { Lock } from "lucide-react";
import { useState } from "react";

import { login } from "../api";

interface Props {
  onAuthenticated: () => void;
}

export function LoginScreen({ onAuthenticated }: Props) {
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) return;
    setSubmitting(true);
    setError(null);
    try {
      const ok = await login(password);
      if (ok) {
        onAuthenticated();
      } else {
        setError("Incorrect password.");
      }
    } catch {
      setError("Couldn't reach the server. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm glass rounded-2xl p-8 shadow-2xl animate-fade-in"
      >
        <div className="size-12 rounded-xl bg-gradient-to-br from-accent to-accent-glow grid place-items-center mb-5">
          <Lock className="size-5 text-white" />
        </div>
        <h1 className="text-xl font-semibold tracking-tight mb-1">Private demo</h1>
        <p className="text-sm text-zinc-400 mb-6">
          Enter the access password to use the pipeline.
        </p>
        <input
          type="password"
          autoFocus
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-full px-4 py-2.5 rounded-lg bg-zinc-900/60 border border-white/10 text-sm placeholder:text-zinc-600 focus:outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20 transition"
        />
        {error && (
          <div className="mt-3 text-sm text-rose-300">{error}</div>
        )}
        <button
          type="submit"
          disabled={submitting || !password}
          className="mt-5 w-full px-4 py-2.5 rounded-lg bg-gradient-to-br from-accent to-accent-glow font-medium text-sm shadow-lg shadow-accent/20 hover:shadow-accent/40 transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? "Checking…" : "Continue →"}
        </button>
      </form>
    </div>
  );
}
