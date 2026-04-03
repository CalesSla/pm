"use client";

import { useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginForm } from "@/components/LoginForm";

type AuthState = "loading" | "authed" | "not_authed" | "network_error";

export default function Home() {
  const [authState, setAuthState] = useState<AuthState>("loading");

  useEffect(() => {
    fetch("/api/auth/me")
      .then((res) => setAuthState(res.ok ? "authed" : "not_authed"))
      .catch(() => setAuthState("network_error"));
  }, []);

  if (authState === "loading") return null;

  if (authState === "network_error") {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-semibold text-[var(--navy-dark)]">Unable to connect to server</p>
          <button
            onClick={() => {
              setAuthState("loading");
              fetch("/api/auth/me")
                .then((res) => setAuthState(res.ok ? "authed" : "not_authed"))
                .catch(() => setAuthState("network_error"));
            }}
            className="mt-4 rounded-xl bg-[var(--secondary-purple)] px-6 py-2 text-sm font-semibold text-white"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (authState === "not_authed") {
    return <LoginForm onLogin={() => setAuthState("authed")} />;
  }

  async function handleLogout() {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      setAuthState("not_authed");
    }
  }

  return (
    <KanbanBoard
      onLogout={handleLogout}
      onAuthError={() => setAuthState("not_authed")}
    />
  );
}
