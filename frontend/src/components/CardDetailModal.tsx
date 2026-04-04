"use client";

import { useEffect, useRef, useState } from "react";
import type { BoardMember, Card, ChecklistItem, Comment, Label, Priority } from "@/lib/kanban";
import {
  updateCard as apiUpdateCard,
  addCardLabel,
  removeCardLabel,
  listComments,
  createComment as apiCreateComment,
  deleteComment as apiDeleteComment,
  assignCard as apiAssignCard,
  unassignCard as apiUnassignCard,
  listChecklistItems,
  createChecklistItem as apiCreateChecklistItem,
  updateChecklistItem as apiUpdateChecklistItem,
  deleteChecklistItem as apiDeleteChecklistItem,
  AuthError,
} from "@/lib/api";

const PRIORITIES: { value: Priority; label: string }[] = [
  { value: "none", label: "None" },
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "urgent", label: "Urgent" },
];

type Props = {
  card: Card;
  boardLabels: Label[];
  boardMembers: BoardMember[];
  onClose: () => void;
  onUpdate: (card: Card) => void;
  onAuthError?: () => void;
};

export function CardDetailModal({ card, boardLabels, boardMembers, onClose, onUpdate, onAuthError }: Props) {
  const [title, setTitle] = useState(card.title);
  const [details, setDetails] = useState(card.details);
  const [dueDate, setDueDate] = useState(card.due_date || "");
  const [priority, setPriority] = useState<Priority>(card.priority || "none");
  const [saving, setSaving] = useState(false);
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState("");
  const [checklistItems, setChecklistItems] = useState<ChecklistItem[]>([]);
  const [newChecklistItem, setNewChecklistItem] = useState("");
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    dialogRef.current?.showModal();
  }, []);

  useEffect(() => {
    listComments(card.id)
      .then(setComments)
      .catch((err) => {
        if (err instanceof AuthError) onAuthError?.();
      });
    listChecklistItems(card.id)
      .then(setChecklistItems)
      .catch((err) => {
        if (err instanceof AuthError) onAuthError?.();
      });
  }, [card.id, onAuthError]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiUpdateCard(card.id, {
        title,
        details,
        due_date: dueDate || null,
        priority,
      });
      onUpdate({
        ...card,
        title,
        details,
        due_date: dueDate || null,
        priority,
      });
      onClose();
    } catch (err) {
      if (err instanceof AuthError) onAuthError?.();
    } finally {
      setSaving(false);
    }
  };

  const handleToggleLabel = async (label: Label) => {
    const hasLabel = card.labels.some((l) => l.id === label.id);
    try {
      if (hasLabel) {
        await removeCardLabel(card.id, label.id);
        const updated = { ...card, labels: card.labels.filter((l) => l.id !== label.id) };
        onUpdate(updated);
      } else {
        await addCardLabel(card.id, label.id);
        const updated = { ...card, labels: [...card.labels, label] };
        onUpdate(updated);
      }
    } catch (err) {
      if (err instanceof AuthError) onAuthError?.();
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    try {
      const comment = await apiCreateComment(card.id, newComment.trim());
      setComments((prev) => [...prev, comment]);
      setNewComment("");
      onUpdate({ ...card, comment_count: card.comment_count + 1 });
    } catch (err) {
      if (err instanceof AuthError) onAuthError?.();
    }
  };

  const handleDeleteComment = async (commentId: number) => {
    try {
      await apiDeleteComment(commentId);
      setComments((prev) => prev.filter((c) => c.id !== commentId));
      onUpdate({ ...card, comment_count: Math.max(0, card.comment_count - 1) });
    } catch (err) {
      if (err instanceof AuthError) onAuthError?.();
    }
  };

  const handleToggleAssignee = async (member: BoardMember) => {
    const isAssigned = card.assignees?.some((a) => a.id === member.id);
    try {
      if (isAssigned) {
        await apiUnassignCard(card.id, member.id);
        onUpdate({ ...card, assignees: card.assignees.filter((a) => a.id !== member.id) });
      } else {
        await apiAssignCard(card.id, member.id);
        onUpdate({ ...card, assignees: [...(card.assignees || []), member] });
      }
    } catch (err) {
      if (err instanceof AuthError) onAuthError?.();
    }
  };

  const handleAddChecklistItem = async () => {
    if (!newChecklistItem.trim()) return;
    try {
      const item = await apiCreateChecklistItem(card.id, newChecklistItem.trim());
      setChecklistItems((prev) => [...prev, item]);
      setNewChecklistItem("");
      onUpdate({ ...card, checklist_total: card.checklist_total + 1 });
    } catch (err) {
      if (err instanceof AuthError) onAuthError?.();
    }
  };

  const handleToggleChecklistItem = async (item: ChecklistItem) => {
    const newChecked = !item.checked;
    setChecklistItems((prev) =>
      prev.map((i) => (i.id === item.id ? { ...i, checked: newChecked } : i))
    );
    try {
      await apiUpdateChecklistItem(item.id, { checked: newChecked });
      const delta = newChecked ? 1 : -1;
      onUpdate({ ...card, checklist_done: card.checklist_done + delta });
    } catch (err) {
      if (err instanceof AuthError) onAuthError?.();
      else setChecklistItems((prev) =>
        prev.map((i) => (i.id === item.id ? { ...i, checked: !newChecked } : i))
      );
    }
  };

  const handleDeleteChecklistItem = async (itemId: number) => {
    const item = checklistItems.find((i) => i.id === itemId);
    try {
      await apiDeleteChecklistItem(itemId);
      setChecklistItems((prev) => prev.filter((i) => i.id !== itemId));
      onUpdate({
        ...card,
        checklist_total: card.checklist_total - 1,
        checklist_done: card.checklist_done - (item?.checked ? 1 : 0),
      });
    } catch (err) {
      if (err instanceof AuthError) onAuthError?.();
    }
  };

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      className="w-full max-w-2xl rounded-3xl border border-[var(--stroke)] bg-[var(--surface-strong)] p-0 shadow-[0_24px_48px_rgba(3,33,71,0.2)] backdrop:bg-black/40"
    >
      <div className="max-h-[85vh] overflow-y-auto p-8">
        <div className="flex items-start justify-between gap-4">
          <h2 className="font-display text-xl font-semibold text-[var(--navy-dark)]">
            Edit Card
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg border border-[var(--stroke)] px-3 py-1 text-xs font-semibold text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
          >
            Close
          </button>
        </div>

        <label className="mt-6 block">
          <span className="text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
            Title
          </span>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm outline-none focus:border-[var(--primary-blue)]"
          />
        </label>

        <label className="mt-4 block">
          <span className="text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
            Details
          </span>
          <textarea
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            rows={4}
            className="mt-1 w-full resize-none rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm outline-none focus:border-[var(--primary-blue)]"
          />
        </label>

        <div className="mt-4 grid grid-cols-2 gap-4">
          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
              Due Date
            </span>
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm outline-none focus:border-[var(--primary-blue)]"
            />
          </label>

          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
              Priority
            </span>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as Priority)}
              className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm outline-none focus:border-[var(--primary-blue)]"
            >
              {PRIORITIES.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </label>
        </div>

        {boardLabels.length > 0 && (
          <div className="mt-4">
            <span className="text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
              Labels
            </span>
            <div className="mt-2 flex flex-wrap gap-2">
              {boardLabels.map((label) => {
                const active = card.labels.some((l) => l.id === label.id);
                return (
                  <button
                    key={label.id}
                    type="button"
                    onClick={() => handleToggleLabel(label)}
                    className="rounded-full px-3 py-1 text-xs font-semibold transition"
                    style={{
                      backgroundColor: active ? label.color : "transparent",
                      color: active ? "white" : label.color,
                      border: `2px solid ${label.color}`,
                    }}
                  >
                    {label.name}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {boardMembers.length > 0 && (
          <div className="mt-4">
            <span className="text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
              Assignees
            </span>
            <div className="mt-2 flex flex-wrap gap-2">
              {boardMembers.map((member) => {
                const isAssigned = card.assignees?.some((a) => a.id === member.id);
                return (
                  <button
                    key={member.id}
                    type="button"
                    onClick={() => handleToggleAssignee(member)}
                    className={`flex items-center gap-1.5 rounded-full border-2 px-3 py-1 text-xs font-semibold transition ${
                      isAssigned
                        ? "border-[var(--primary-blue)] bg-[var(--primary-blue)] text-white"
                        : "border-[var(--stroke)] text-[var(--gray-text)] hover:border-[var(--primary-blue)]"
                    }`}
                  >
                    <span className="flex h-4 w-4 items-center justify-center rounded-full bg-white/20 text-[9px] font-bold uppercase">
                      {(member.display_name || member.username)[0]}
                    </span>
                    {member.display_name || member.username}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        <div className="mt-6 border-t border-[var(--stroke)] pt-4">
          <span className="text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
            Checklist {checklistItems.length > 0 && `(${checklistItems.filter((i) => i.checked).length}/${checklistItems.length})`}
          </span>
          {checklistItems.length > 0 && (
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-[var(--stroke)]">
              <div
                className="h-full rounded-full bg-[var(--primary-blue)] transition-all"
                style={{ width: `${(checklistItems.filter((i) => i.checked).length / checklistItems.length) * 100}%` }}
              />
            </div>
          )}
          <div className="mt-3 space-y-1">
            {checklistItems.map((item) => (
              <div key={item.id} className="group flex items-center gap-2 rounded-lg px-2 py-1 hover:bg-[var(--surface)]">
                <input
                  type="checkbox"
                  checked={item.checked}
                  onChange={() => handleToggleChecklistItem(item)}
                  className="h-4 w-4 rounded border-[var(--stroke)] accent-[var(--primary-blue)]"
                />
                <span className={`flex-1 text-sm ${item.checked ? "text-[var(--gray-text)] line-through" : "text-[var(--navy-dark)]"}`}>
                  {item.title}
                </span>
                <button
                  onClick={() => handleDeleteChecklistItem(item.id)}
                  className="text-[10px] font-semibold text-red-400 opacity-0 transition hover:text-red-600 group-hover:opacity-100"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
          <div className="mt-2 flex gap-2">
            <input
              type="text"
              value={newChecklistItem}
              onChange={(e) => setNewChecklistItem(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddChecklistItem()}
              placeholder="Add checklist item..."
              className="flex-1 rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2 text-sm outline-none focus:border-[var(--primary-blue)]"
            />
            <button
              onClick={handleAddChecklistItem}
              disabled={!newChecklistItem.trim()}
              className="rounded-xl bg-[var(--primary-blue)] px-4 py-2 text-xs font-semibold text-white transition hover:opacity-90 disabled:opacity-40"
            >
              Add
            </button>
          </div>
        </div>

        <div className="mt-6 border-t border-[var(--stroke)] pt-4">
          <span className="text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
            Comments ({comments.length})
          </span>
          <div className="mt-3 space-y-3">
            {comments.map((comment) => (
              <div key={comment.id} className="rounded-xl bg-[var(--surface)] p-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[var(--navy-dark)]">
                    {comment.user.display_name || comment.user.username}
                  </span>
                  <div className="flex items-center gap-2">
                    {comment.created_at && (
                      <span className="text-[10px] text-[var(--gray-text)]">
                        {new Date(comment.created_at).toLocaleDateString()}
                      </span>
                    )}
                    <button
                      onClick={() => handleDeleteComment(comment.id)}
                      className="text-[10px] font-semibold text-red-400 hover:text-red-600"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                <p className="mt-1 text-sm text-[var(--navy-dark)]">{comment.content}</p>
              </div>
            ))}
          </div>
          <div className="mt-3 flex gap-2">
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddComment()}
              placeholder="Add a comment..."
              className="flex-1 rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2 text-sm outline-none focus:border-[var(--primary-blue)]"
            />
            <button
              onClick={handleAddComment}
              disabled={!newComment.trim()}
              className="rounded-xl bg-[var(--primary-blue)] px-4 py-2 text-xs font-semibold text-white transition hover:opacity-90 disabled:opacity-40"
            >
              Post
            </button>
          </div>
        </div>

        <div className="mt-8 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="rounded-xl border border-[var(--stroke)] px-5 py-2.5 text-sm font-semibold text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !title.trim()}
            className="rounded-xl bg-[var(--secondary-purple)] px-5 py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </dialog>
  );
}
