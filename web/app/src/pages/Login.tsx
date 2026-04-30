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
        className="w-full max-w-sm card p-8 animate-fade-in"
      >
        <div className="size-11 rounded-lg bg-gold-tint border border-gold/30 grid place-items-center mb-5">
          <Lock className="size-5 text-gold-deep" />
        </div>
        <h1 className="text-xl font-semibold tracking-tight mb-1 text-ink">Private demo</h1>
        <p className="text-sm text-ink-soft mb-6">
          Enter the access password to use the pipeline.
        </p>
        <input
          type="password"
          autoFocus
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-full px-4 py-2.5 rounded-lg bg-paper border border-rule text-sm placeholder:text-ink-mute focus:outline-none focus:border-gold focus:ring-2 focus:ring-gold/20 transition"
        />
        {error && <div className="mt-3 text-sm text-rose-600">{error}</div>}
        <button
          type="submit"
          disabled={submitting || !password}
          className="mt-5 w-full btn-primary"
        >
          {submitting ? "Checking…" : "Continue →"}
        </button>
      </form>
    </div>
  );
}
