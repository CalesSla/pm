"use client";

import { useState } from "react";
import { register, ApiError } from "@/lib/api";

type Props = {
  onRegister: () => void;
  onSwitchToLogin: () => void;
};

export function RegisterForm({ onRegister, onSwitchToLogin }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(username, password, displayName);
      onRegister();
    } catch (err) {
      if (err instanceof ApiError) {
        const body = JSON.parse(err.message);
        setError(body.error || "Registration failed");
      } else {
        setError("Registration failed");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm rounded-3xl border border-[var(--stroke)] bg-[var(--surface-strong)] p-8 shadow-[var(--shadow)]"
      >
        <h1 className="font-display text-2xl font-semibold text-[var(--navy-dark)]">
          Create account
        </h1>
        <p className="mt-2 text-sm text-[var(--gray-text)]">
          Sign up to start managing your projects.
        </p>

        {error && (
          <p className="mt-4 text-sm font-semibold text-red-600" role="alert">
            {error}
          </p>
        )}

        <label className="mt-6 block">
          <span className="text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
            Username
          </span>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm outline-none focus:border-[var(--primary-blue)]"
            autoFocus
          />
        </label>

        <label className="mt-4 block">
          <span className="text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
            Display Name
          </span>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Optional"
            className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm outline-none focus:border-[var(--primary-blue)]"
          />
        </label>

        <label className="mt-4 block">
          <span className="text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
            Password
          </span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm outline-none focus:border-[var(--primary-blue)]"
          />
        </label>

        <button
          type="submit"
          disabled={loading}
          className="mt-6 w-full rounded-xl bg-[var(--secondary-purple)] px-4 py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "Creating account..." : "Create account"}
        </button>

        <p className="mt-4 text-center text-sm text-[var(--gray-text)]">
          Already have an account?{" "}
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="font-semibold text-[var(--primary-blue)] hover:underline"
          >
            Sign in
          </button>
        </p>
      </form>
    </div>
  );
}
