"use client";

import { useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginForm } from "@/components/LoginForm";
import { RegisterForm } from "@/components/RegisterForm";
import { BoardSelector } from "@/components/BoardSelector";

type AppView =
  | { kind: "loading" }
  | { kind: "network_error" }
  | { kind: "login" }
  | { kind: "register" }
  | { kind: "boards" }
  | { kind: "board"; boardId: number };

export default function Home() {
  const [view, setView] = useState<AppView>({ kind: "loading" });

  function checkAuth() {
    setView({ kind: "loading" });
    fetch("/api/auth/me")
      .then((res) => setView(res.ok ? { kind: "boards" } : { kind: "login" }))
      .catch(() => setView({ kind: "network_error" }));
  }

  useEffect(checkAuth, []);

  if (view.kind === "loading") return null;

  if (view.kind === "network_error") {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-semibold text-[var(--navy-dark)]">Unable to connect to server</p>
          <button
            onClick={checkAuth}
            className="mt-4 rounded-xl bg-[var(--secondary-purple)] px-6 py-2 text-sm font-semibold text-white"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (view.kind === "login") {
    return (
      <LoginForm
        onLogin={() => setView({ kind: "boards" })}
        onSwitchToRegister={() => setView({ kind: "register" })}
      />
    );
  }

  if (view.kind === "register") {
    return (
      <RegisterForm
        onRegister={() => setView({ kind: "boards" })}
        onSwitchToLogin={() => setView({ kind: "login" })}
      />
    );
  }

  async function handleLogout() {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      setView({ kind: "login" });
    }
  }

  if (view.kind === "boards") {
    return (
      <BoardSelector
        onSelectBoard={(boardId) => setView({ kind: "board", boardId })}
        onLogout={handleLogout}
        onAuthError={() => setView({ kind: "login" })}
      />
    );
  }

  return (
    <KanbanBoard
      boardId={view.boardId}
      onLogout={handleLogout}
      onAuthError={() => setView({ kind: "login" })}
      onBack={() => setView({ kind: "boards" })}
    />
  );
}
