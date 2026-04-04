import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import type { Card, Priority } from "@/lib/kanban";

const PRIORITY_CONFIG: Record<Priority, { label: string; color: string } | null> = {
  none: null,
  low: { label: "Low", color: "bg-blue-100 text-blue-700" },
  medium: { label: "Medium", color: "bg-yellow-100 text-yellow-700" },
  high: { label: "High", color: "bg-orange-100 text-orange-700" },
  urgent: { label: "Urgent", color: "bg-red-100 text-red-700" },
};

type KanbanCardProps = {
  card: Card;
  onDelete: (cardId: string) => void;
  onEdit: (card: Card) => void;
};

function formatDueDate(due: string): string {
  const d = new Date(due + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function dueDateColor(due: string): string {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diff = (new Date(due + "T00:00:00").getTime() - today.getTime()) / (1000 * 60 * 60 * 24);
  if (diff < 0) return "text-red-600";
  if (diff <= 2) return "text-amber-600";
  return "text-[var(--gray-text)]";
}

export const KanbanCard = ({ card, onDelete, onEdit }: KanbanCardProps) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: card.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <article
      ref={setNodeRef}
      style={style}
      className={clsx(
        "cursor-pointer rounded-2xl border border-transparent bg-white px-4 py-4 shadow-[0_12px_24px_rgba(3,33,71,0.08)]",
        "transition-all duration-150",
        isDragging && "opacity-60 shadow-[0_18px_32px_rgba(3,33,71,0.16)]"
      )}
      {...attributes}
      {...listeners}
      onClick={() => onEdit(card)}
      data-testid={`card-${card.id}`}
    >
      <div className="mb-2 flex flex-wrap gap-1">
        {PRIORITY_CONFIG[card.priority] && (
          <span className={clsx("rounded-full px-2 py-0.5 text-[10px] font-semibold", PRIORITY_CONFIG[card.priority]!.color)}>
            {PRIORITY_CONFIG[card.priority]!.label}
          </span>
        )}
        {card.labels?.map((label) => (
          <span
            key={label.id}
            className="rounded-full px-2 py-0.5 text-[10px] font-semibold text-white"
            style={{ backgroundColor: label.color }}
          >
            {label.name}
          </span>
        ))}
      </div>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h4 className="font-display text-base font-semibold text-[var(--navy-dark)]">
            {card.title}
          </h4>
          {card.details && (
            <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
              {card.details}
            </p>
          )}
          {card.due_date && (
            <p
              className={clsx("mt-2 text-xs font-semibold", dueDateColor(card.due_date))}
            >
              Due {formatDueDate(card.due_date)}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(card.id);
          }}
          className="rounded-full border border-transparent px-2 py-1 text-xs font-semibold text-[var(--gray-text)] transition hover:border-[var(--stroke)] hover:text-[var(--navy-dark)]"
          aria-label={`Delete ${card.title}`}
        >
          Remove
        </button>
      </div>
      {(card.comment_count > 0 || card.checklist_total > 0 || (card.assignees && card.assignees.length > 0)) && (
        <div className="mt-2 flex items-center gap-3 border-t border-[var(--stroke)] pt-2">
          {card.checklist_total > 0 && (
            <span className={clsx(
              "text-[10px] font-semibold",
              card.checklist_done === card.checklist_total ? "text-green-600" : "text-[var(--gray-text)]"
            )}>
              {card.checklist_done}/{card.checklist_total}
            </span>
          )}
          {card.comment_count > 0 && (
            <span className="text-[10px] font-semibold text-[var(--gray-text)]">
              {card.comment_count} comment{card.comment_count !== 1 ? "s" : ""}
            </span>
          )}
          {card.assignees && card.assignees.length > 0 && (
            <div className="ml-auto flex -space-x-1">
              {card.assignees.map((a) => (
                <span
                  key={a.id}
                  title={a.display_name || a.username}
                  className="flex h-5 w-5 items-center justify-center rounded-full bg-[var(--primary-blue)] text-[9px] font-bold uppercase text-white ring-1 ring-white"
                >
                  {(a.display_name || a.username)[0]}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </article>
  );
};
