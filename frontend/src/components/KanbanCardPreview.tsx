import type { Card } from "@/lib/kanban";

type KanbanCardPreviewProps = {
  card: Card;
};

export const KanbanCardPreview = ({ card }: KanbanCardPreviewProps) => (
  <article className="rounded-2xl border border-transparent bg-white px-4 py-4 shadow-[0_18px_32px_rgba(3,33,71,0.16)]">
    {card.labels && card.labels.length > 0 && (
      <div className="mb-2 flex flex-wrap gap-1">
        {card.labels.map((label) => (
          <span
            key={label.id}
            className="rounded-full px-2 py-0.5 text-[10px] font-semibold text-white"
            style={{ backgroundColor: label.color }}
          >
            {label.name}
          </span>
        ))}
      </div>
    )}
    <h4 className="font-display text-base font-semibold text-[var(--navy-dark)]">
      {card.title}
    </h4>
    {card.details && (
      <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
        {card.details}
      </p>
    )}
  </article>
);
