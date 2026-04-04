"use client";

import { useEffect, useState } from "react";
import { fetchActivity, type ActivityEntry } from "@/lib/api";

type Props = {
  boardId: number;
  onClose: () => void;
};

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr + "Z").getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function ActivityFeed({ boardId, onClose }: Props) {
  const [entries, setEntries] = useState<ActivityEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchActivity(boardId, 30)
      .then(setEntries)
      .finally(() => setLoading(false));
  }, [boardId]);

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-end bg-black/20" onClick={onClose}>
      <div
        className="mt-16 mr-6 w-96 max-h-[70vh] overflow-y-auto rounded-2xl border border-[var(--stroke)] bg-white p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-lg font-semibold text-[var(--navy-dark)]">Activity</h3>
          <button onClick={onClose} className="text-[var(--gray-text)] hover:text-[var(--navy-dark)]">
            &times;
          </button>
        </div>

        {loading && <p className="text-xs text-[var(--gray-text)]">Loading...</p>}

        {!loading && entries.length === 0 && (
          <p className="text-xs text-[var(--gray-text)]">No activity yet.</p>
        )}

        <div className="space-y-3">
          {entries.map((entry) => (
            <div key={entry.id} className="border-b border-[var(--stroke)] pb-2 last:border-0">
              <p className="text-sm text-[var(--navy-dark)]">{entry.detail}</p>
              <p className="text-xs text-[var(--gray-text)]">
                {entry.user.display_name || entry.user.username}
                {" -- "}
                {entry.created_at ? timeAgo(entry.created_at) : ""}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
