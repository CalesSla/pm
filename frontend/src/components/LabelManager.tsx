"use client";

import { useState } from "react";
import type { Label } from "@/lib/kanban";
import {
  createLabel as apiCreateLabel,
  updateLabel as apiUpdateLabel,
  deleteLabel as apiDeleteLabel,
  AuthError,
} from "@/lib/api";

const PRESET_COLORS = [
  "#ef4444", "#f97316", "#eab308", "#22c55e",
  "#3b82f6", "#8b5cf6", "#ec4899", "#6b7280",
];

type Props = {
  boardId: number;
  labels: Label[];
  onLabelsChange: (labels: Label[]) => void;
  onClose: () => void;
  onAuthError?: () => void;
};

export function LabelManager({ boardId, labels, onLabelsChange, onClose, onAuthError }: Props) {
  const [newName, setNewName] = useState("");
  const [newColor, setNewColor] = useState(PRESET_COLORS[4]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editColor, setEditColor] = useState("");

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      const label = await apiCreateLabel(boardId, newName.trim(), newColor);
      onLabelsChange([...labels, label]);
      setNewName("");
    } catch (err) {
      if (err instanceof AuthError) onAuthError?.();
    }
  };

  const handleUpdate = async (labelId: number) => {
    if (!editName.trim()) return;
    try {
      const updated = await apiUpdateLabel(labelId, { name: editName.trim(), color: editColor });
      onLabelsChange(labels.map((l) => (l.id === labelId ? updated : l)));
      setEditingId(null);
    } catch (err) {
      if (err instanceof AuthError) onAuthError?.();
    }
  };

  const handleDelete = async (labelId: number) => {
    try {
      await apiDeleteLabel(labelId);
      onLabelsChange(labels.filter((l) => l.id !== labelId));
    } catch (err) {
      if (err instanceof AuthError) onAuthError?.();
    }
  };

  return (
    <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface-strong)] p-6 shadow-[var(--shadow)]">
      <div className="flex items-center justify-between">
        <h3 className="font-display text-lg font-semibold text-[var(--navy-dark)]">
          Board Labels
        </h3>
        <button
          onClick={onClose}
          className="rounded-lg border border-[var(--stroke)] px-3 py-1 text-xs font-semibold text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
        >
          Done
        </button>
      </div>

      <div className="mt-4 space-y-2">
        {labels.map((label) => (
          <div key={label.id} className="flex items-center gap-2">
            {editingId === label.id ? (
              <>
                <div className="flex gap-1">
                  {PRESET_COLORS.map((c) => (
                    <button
                      key={c}
                      onClick={() => setEditColor(c)}
                      className="h-5 w-5 rounded-full border-2 transition"
                      style={{
                        backgroundColor: c,
                        borderColor: editColor === c ? "var(--navy-dark)" : "transparent",
                      }}
                    />
                  ))}
                </div>
                <input
                  autoFocus
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleUpdate(label.id)}
                  className="flex-1 rounded-lg border border-[var(--stroke)] bg-white px-2 py-1 text-sm outline-none"
                />
                <button
                  onClick={() => handleUpdate(label.id)}
                  className="text-xs font-semibold text-[var(--primary-blue)]"
                >
                  Save
                </button>
                <button
                  onClick={() => setEditingId(null)}
                  className="text-xs font-semibold text-[var(--gray-text)]"
                >
                  Cancel
                </button>
              </>
            ) : (
              <>
                <span
                  className="h-4 w-4 rounded-full"
                  style={{ backgroundColor: label.color }}
                />
                <span className="flex-1 text-sm font-medium text-[var(--navy-dark)]">
                  {label.name}
                </span>
                <button
                  onClick={() => {
                    setEditingId(label.id);
                    setEditName(label.name);
                    setEditColor(label.color);
                  }}
                  className="text-xs font-semibold text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(label.id)}
                  className="text-xs font-semibold text-red-500 hover:text-red-700"
                >
                  Delete
                </button>
              </>
            )}
          </div>
        ))}
      </div>

      <div className="mt-4 border-t border-[var(--stroke)] pt-4">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
          New Label
        </p>
        <div className="flex gap-1">
          {PRESET_COLORS.map((c) => (
            <button
              key={c}
              onClick={() => setNewColor(c)}
              className="h-5 w-5 rounded-full border-2 transition"
              style={{
                backgroundColor: c,
                borderColor: newColor === c ? "var(--navy-dark)" : "transparent",
              }}
            />
          ))}
        </div>
        <div className="mt-2 flex gap-2">
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            placeholder="Label name..."
            className="flex-1 rounded-lg border border-[var(--stroke)] bg-white px-3 py-1.5 text-sm outline-none focus:border-[var(--primary-blue)]"
          />
          <button
            onClick={handleCreate}
            disabled={!newName.trim()}
            className="rounded-lg bg-[var(--primary-blue)] px-4 py-1.5 text-xs font-semibold text-white transition hover:opacity-90 disabled:opacity-40"
          >
            Add
          </button>
        </div>
      </div>
    </div>
  );
}
