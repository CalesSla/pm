"use client";

import { useState } from "react";
import type { BoardMember } from "@/lib/kanban";
import {
  addBoardMember as apiAddMember,
  removeBoardMember as apiRemoveMember,
  AuthError,
} from "@/lib/api";

type Props = {
  boardId: number;
  members: BoardMember[];
  onMembersChange: (members: BoardMember[]) => void;
  onClose: () => void;
  onAuthError?: () => void;
};

export function BoardMembersPanel({ boardId, members, onMembersChange, onClose, onAuthError }: Props) {
  const [username, setUsername] = useState("");
  const [error, setError] = useState("");

  const handleAdd = async () => {
    if (!username.trim()) return;
    setError("");
    try {
      const member = await apiAddMember(boardId, username.trim());
      onMembersChange([...members, member]);
      setUsername("");
    } catch (err) {
      if (err instanceof AuthError) {
        onAuthError?.();
      } else if (err instanceof Error) {
        const msg = err.message;
        try {
          setError(JSON.parse(msg).error);
        } catch {
          setError(msg);
        }
      }
    }
  };

  const handleRemove = async (memberId: number) => {
    try {
      await apiRemoveMember(boardId, memberId);
      onMembersChange(members.filter((m) => m.id !== memberId));
    } catch (err) {
      if (err instanceof AuthError) onAuthError?.();
    }
  };

  return (
    <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface-strong)] p-6 shadow-[var(--shadow)]">
      <div className="flex items-center justify-between">
        <h3 className="font-display text-lg font-semibold text-[var(--navy-dark)]">
          Board Members
        </h3>
        <button
          onClick={onClose}
          className="rounded-lg border border-[var(--stroke)] px-3 py-1 text-xs font-semibold text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
        >
          Done
        </button>
      </div>

      <div className="mt-4 space-y-2">
        {members.map((member) => (
          <div key={member.id} className="flex items-center gap-3">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--primary-blue)] text-xs font-bold uppercase text-white">
              {(member.display_name || member.username)[0]}
            </span>
            <div className="flex-1">
              <p className="text-sm font-semibold text-[var(--navy-dark)]">
                {member.display_name || member.username}
              </p>
              <p className="text-[10px] uppercase tracking-wider text-[var(--gray-text)]">
                {member.role}
              </p>
            </div>
            {member.role !== "owner" && (
              <button
                onClick={() => handleRemove(member.id)}
                className="text-xs font-semibold text-red-500 hover:text-red-700"
              >
                Remove
              </button>
            )}
          </div>
        ))}
      </div>

      <div className="mt-4 border-t border-[var(--stroke)] pt-4">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
          Invite Member
        </p>
        {error && <p className="mb-2 text-xs text-red-500">{error}</p>}
        <div className="flex gap-2">
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            placeholder="Username..."
            className="flex-1 rounded-lg border border-[var(--stroke)] bg-white px-3 py-1.5 text-sm outline-none focus:border-[var(--primary-blue)]"
          />
          <button
            onClick={handleAdd}
            disabled={!username.trim()}
            className="rounded-lg bg-[var(--primary-blue)] px-4 py-1.5 text-xs font-semibold text-white transition hover:opacity-90 disabled:opacity-40"
          >
            Invite
          </button>
        </div>
      </div>
    </div>
  );
}
