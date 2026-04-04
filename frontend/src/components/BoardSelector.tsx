"use client";

import { useEffect, useState } from "react";
import type { BoardSummary } from "@/lib/kanban";
import { UserProfileModal } from "@/components/UserProfileModal";
import {
  listBoards,
  createBoard,
  deleteBoard,
  renameBoard,
  fetchBoardStats,
  AuthError,
  type BoardStats,
} from "@/lib/api";

type Props = {
  onSelectBoard: (boardId: number) => void;
  onLogout: () => void;
  onAuthError: () => void;
};

export function BoardSelector({ onSelectBoard, onLogout, onAuthError }: Props) {
  const [boards, setBoards] = useState<BoardSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [newTitle, setNewTitle] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [showProfile, setShowProfile] = useState(false);
  const [userInfo, setUserInfo] = useState<{ username: string; display_name: string } | null>(null);
  const [stats, setStats] = useState<Record<number, BoardStats>>({});

  useEffect(() => {
    listBoards()
      .then((boardsList) => {
        setBoards(boardsList);
        boardsList.forEach((b) =>
          fetchBoardStats(b.id).then((s) =>
            setStats((prev) => ({ ...prev, [b.id]: s }))
          )
        );
      })
      .catch((err) => {
        if (err instanceof AuthError) onAuthError();
      })
      .finally(() => setLoading(false));
    fetch("/api/auth/me")
      .then((r) => r.ok ? r.json() : null)
      .then((data) => data && setUserInfo(data));
  }, [onAuthError]);

  const handleCreate = async () => {
    const title = newTitle.trim() || "New Board";
    try {
      const board = await createBoard(title);
      setBoards((prev) => [...prev, { id: board.id, title: board.title, created_at: new Date().toISOString() }]);
      setNewTitle("");
    } catch (err) {
      if (err instanceof AuthError) onAuthError();
    }
  };

  const handleDelete = async (boardId: number) => {
    try {
      await deleteBoard(boardId);
      setBoards((prev) => prev.filter((b) => b.id !== boardId));
    } catch (err) {
      if (err instanceof AuthError) onAuthError();
    }
  };

  const handleRename = async (boardId: number) => {
    if (!editTitle.trim()) return;
    try {
      await renameBoard(boardId, editTitle.trim());
      setBoards((prev) =>
        prev.map((b) => (b.id === boardId ? { ...b, title: editTitle.trim() } : b))
      );
      setEditingId(null);
    } catch (err) {
      if (err instanceof AuthError) onAuthError();
    }
  };

  if (loading) return null;

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[900px] flex-col gap-8 px-6 pb-16 pt-12">
        <header className="flex items-start justify-between rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
              Project Management
            </p>
            <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
              Your Boards
            </h1>
            <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
              Select a board to start working, or create a new one.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowProfile(true)}
              className="rounded-xl border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:border-[var(--navy-dark)] hover:text-[var(--navy-dark)]"
            >
              Profile
            </button>
            <button
              onClick={onLogout}
              className="rounded-xl border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:border-[var(--navy-dark)] hover:text-[var(--navy-dark)]"
            >
              Sign out
            </button>
          </div>
        </header>

        <div className="flex gap-3">
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            placeholder="New board name..."
            className="flex-1 rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm outline-none focus:border-[var(--primary-blue)]"
          />
          <button
            onClick={handleCreate}
            className="rounded-xl bg-[var(--secondary-purple)] px-6 py-3 text-sm font-semibold text-white transition hover:opacity-90"
          >
            Create Board
          </button>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {boards.map((board) => (
            <div
              key={board.id}
              className="group flex flex-col gap-3 rounded-2xl border border-[var(--stroke)] bg-[var(--surface-strong)] p-5 shadow-[var(--shadow)] transition hover:border-[var(--primary-blue)]"
            >
              {editingId === board.id ? (
                <input
                  autoFocus
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleRename(board.id);
                    if (e.key === "Escape") setEditingId(null);
                  }}
                  onBlur={() => handleRename(board.id)}
                  className="rounded-lg border border-[var(--primary-blue)] bg-white px-3 py-1.5 text-lg font-semibold text-[var(--navy-dark)] outline-none"
                />
              ) : (
                <h2
                  className="cursor-pointer text-lg font-semibold text-[var(--navy-dark)]"
                  onClick={() => onSelectBoard(board.id)}
                >
                  {board.title}
                </h2>
              )}
              <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-[var(--gray-text)]">
                <span>Created {new Date(board.created_at).toLocaleDateString()}</span>
                {stats[board.id] && (
                  <>
                    <span>{stats[board.id].total_cards} cards</span>
                    <span>{stats[board.id].member_count} {stats[board.id].member_count === 1 ? "member" : "members"}</span>
                  </>
                )}
              </div>
              {stats[board.id]?.columns.length > 0 && (
                <div className="flex gap-1 mt-1">
                  {stats[board.id].columns.map((col) => (
                    <div
                      key={col.title}
                      className="flex-1 rounded bg-[var(--surface)] px-1.5 py-1 text-center"
                      title={`${col.title}: ${col.card_count} cards`}
                    >
                      <p className="text-[10px] font-medium text-[var(--gray-text)] truncate">{col.title}</p>
                      <p className="text-xs font-semibold text-[var(--navy-dark)]">{col.card_count}</p>
                    </div>
                  ))}
                </div>
              )}
              <div className="mt-auto flex items-center gap-2 pt-2">
                <button
                  onClick={() => onSelectBoard(board.id)}
                  className="rounded-lg bg-[var(--primary-blue)] px-4 py-1.5 text-xs font-semibold text-white transition hover:opacity-90"
                >
                  Open
                </button>
                <button
                  onClick={() => {
                    setEditingId(board.id);
                    setEditTitle(board.title);
                  }}
                  className="rounded-lg border border-[var(--stroke)] px-3 py-1.5 text-xs font-semibold text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
                >
                  Rename
                </button>
                {boards.length > 1 && (
                  <button
                    onClick={() => handleDelete(board.id)}
                    className="rounded-lg border border-[var(--stroke)] px-3 py-1.5 text-xs font-semibold text-red-500 transition hover:bg-red-50"
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {boards.length === 0 && (
          <p className="text-center text-sm text-[var(--gray-text)]">
            No boards yet. Create one to get started.
          </p>
        )}
      </main>

      {showProfile && userInfo && (
        <UserProfileModal
          username={userInfo.username}
          displayName={userInfo.display_name}
          onClose={() => setShowProfile(false)}
          onUpdate={(name) => setUserInfo((prev) => prev ? { ...prev, display_name: name } : prev)}
        />
      )}
    </div>
  );
}
