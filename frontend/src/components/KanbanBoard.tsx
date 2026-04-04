"use client";

import { useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  pointerWithin,
  closestCorners,
  type CollisionDetection,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { ActivityFeed } from "@/components/ActivityFeed";
import { ChatSidebar } from "@/components/ChatSidebar";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { CardDetailModal } from "@/components/CardDetailModal";
import { LabelManager } from "@/components/LabelManager";
import { SearchBar } from "@/components/SearchBar";
import { BoardMembersPanel } from "@/components/BoardMembersPanel";
import { moveCard, type BoardData, type Card } from "@/lib/kanban";
import {
  AuthError,
  fetchBoard,
  fetchBoardById,
  renameColumn as apiRenameColumn,
  createCard as apiCreateCard,
  deleteCard as apiDeleteCard,
  reorderCard as apiReorderCard,
  createColumn as apiCreateColumn,
  deleteColumn as apiDeleteColumn,
} from "@/lib/api";

const columnFirst: CollisionDetection = (args) => {
  const pointerHits = pointerWithin(args);
  if (pointerHits.length > 0) return pointerHits;
  return closestCorners(args);
};

type Props = {
  boardId?: number;
  onLogout?: () => void;
  onAuthError?: () => void;
  onBack?: () => void;
};

export const KanbanBoard = ({ boardId, onLogout, onAuthError, onBack }: Props) => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [editingCard, setEditingCard] = useState<Card | null>(null);
  const [newColumnTitle, setNewColumnTitle] = useState("");
  const [showLabelManager, setShowLabelManager] = useState(false);
  const [showMembers, setShowMembers] = useState(false);
  const [showActivity, setShowActivity] = useState(false);

  useEffect(() => {
    const load = boardId ? fetchBoardById(boardId) : fetchBoard();
    load
      .then(setBoard)
      .catch((err) => {
        if (err instanceof AuthError) onAuthError?.();
      });
  }, [boardId, onAuthError]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const cardsById = useMemo(() => board?.cards ?? {}, [board?.cards]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!board || !over || active.id === over.id) return;

    const prevBoard = board;
    const newColumns = moveCard(
      board.columns,
      active.id as string,
      over.id as string
    );
    setBoard({ ...board, columns: newColumns });

    const cardId = active.id as string;
    for (const col of newColumns) {
      const pos = col.cardIds.indexOf(cardId);
      if (pos !== -1) {
        try {
          await apiReorderCard(cardId, col.id, pos);
        } catch (err) {
          if (err instanceof AuthError) {
            onAuthError?.();
          } else {
            setBoard(prevBoard);
          }
        }
        break;
      }
    }
  };

  const handleRenameColumn = async (columnId: string, title: string) => {
    if (!board) return;
    const prevBoard = board;
    setBoard({
      ...board,
      columns: board.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      ),
    });
    try {
      await apiRenameColumn(columnId, title);
    } catch (err) {
      if (err instanceof AuthError) {
        onAuthError?.();
      } else {
        setBoard(prevBoard);
      }
    }
  };

  const handleAddCard = async (
    columnId: string,
    title: string,
    details: string
  ) => {
    try {
      const card = await apiCreateCard(columnId, title, details || "");
      setBoard((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          cards: {
            ...prev.cards,
            [card.id]: { ...card, labels: [], priority: card.priority || "none", comment_count: 0, checklist_total: 0, checklist_done: 0, assignees: [] },
          },
          columns: prev.columns.map((column) =>
            column.id === columnId
              ? { ...column, cardIds: [...column.cardIds, card.id] }
              : column
          ),
        };
      });
    } catch (err) {
      if (err instanceof AuthError) onAuthError?.();
    }
  };

  const handleDeleteCard = async (columnId: string, cardId: string) => {
    const prevBoard = board;
    setBoard((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        cards: Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => id !== cardId)
        ),
        columns: prev.columns.map((column) =>
          column.id === columnId
            ? { ...column, cardIds: column.cardIds.filter((id) => id !== cardId) }
            : column
        ),
      };
    });
    try {
      await apiDeleteCard(cardId);
    } catch (err) {
      if (err instanceof AuthError) {
        onAuthError?.();
      } else {
        setBoard(prevBoard);
      }
    }
  };

  const handleAddColumn = async () => {
    if (!boardId || !newColumnTitle.trim()) return;
    try {
      const col = await apiCreateColumn(boardId, newColumnTitle.trim());
      setBoard((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          columns: [
            ...prev.columns,
            { id: `col-${col.id}`, title: col.title, cardIds: [] },
          ],
        };
      });
      setNewColumnTitle("");
    } catch (err) {
      if (err instanceof AuthError) onAuthError?.();
    }
  };

  const handleDeleteColumn = async (columnId: string) => {
    const prevBoard = board;
    setBoard((prev) => {
      if (!prev) return prev;
      const col = prev.columns.find((c) => c.id === columnId);
      const removedCardIds = new Set(col?.cardIds ?? []);
      return {
        ...prev,
        columns: prev.columns.filter((c) => c.id !== columnId),
        cards: Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => !removedCardIds.has(id))
        ),
      };
    });
    try {
      await apiDeleteColumn(columnId);
    } catch (err) {
      if (err instanceof AuthError) {
        onAuthError?.();
      } else {
        setBoard(prevBoard);
      }
    }
  };

  const handleCardUpdate = (updated: Card) => {
    setEditingCard(updated);
    setBoard((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        cards: { ...prev.cards, [updated.id]: updated },
      };
    });
  };

  const handleLabelsChange = (labels: BoardData["labels"]) => {
    setBoard((prev) => (prev ? { ...prev, labels } : prev));
  };

  const handleMembersChange = (members: BoardData["members"]) => {
    setBoard((prev) => (prev ? { ...prev, members } : prev));
  };

  if (!board) return null;

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Kanban Board
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Rename columns, drag cards between stages, and capture quick notes.
              </p>
            </div>
            <div className="flex items-start gap-4">
              <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                  Cards
                </p>
                <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                  {Object.keys(board.cards).length}
                </p>
              </div>
              <div className="flex flex-col gap-2">
                {onBack && (
                  <button
                    onClick={onBack}
                    className="rounded-xl border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:border-[var(--navy-dark)] hover:text-[var(--navy-dark)]"
                  >
                    All Boards
                  </button>
                )}
                {onLogout && (
                  <button
                    onClick={onLogout}
                    className="rounded-xl border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:border-[var(--navy-dark)] hover:text-[var(--navy-dark)]"
                  >
                    Sign out
                  </button>
                )}
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {boardId && (
              <>
                <div className="w-64">
                  <SearchBar boardId={boardId} onAuthError={onAuthError} />
                </div>
                <button
                  onClick={() => setShowLabelManager((v) => !v)}
                  className="rounded-xl border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
                >
                  {showLabelManager ? "Hide Labels" : "Manage Labels"}
                </button>
                <button
                  onClick={() => setShowMembers((v) => !v)}
                  className="rounded-xl border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:border-[var(--secondary-purple)] hover:text-[var(--secondary-purple)]"
                >
                  {showMembers ? "Hide Members" : "Members"}
                </button>
                <button
                  onClick={() => setShowActivity(true)}
                  className="rounded-xl border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:border-[var(--accent-yellow)] hover:text-[var(--accent-yellow)]"
                >
                  Activity
                </button>
              </>
            )}
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
                <span className="text-[var(--gray-text)]">
                  {column.cardIds.length}
                </span>
              </div>
            ))}
          </div>
          {showLabelManager && boardId && (
            <LabelManager
              boardId={boardId}
              labels={board.labels ?? []}
              onLabelsChange={handleLabelsChange}
              onClose={() => setShowLabelManager(false)}
              onAuthError={onAuthError}
            />
          )}
          {showActivity && boardId && (
            <ActivityFeed boardId={boardId} onClose={() => setShowActivity(false)} />
          )}
          {showMembers && boardId && (
            <BoardMembersPanel
              boardId={boardId}
              members={board.members ?? []}
              onMembersChange={handleMembersChange}
              onClose={() => setShowMembers(false)}
              onAuthError={onAuthError}
            />
          )}
        </header>

        <DndContext
          sensors={sensors}
          collisionDetection={columnFirst}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <section className="grid gap-6" style={{ gridTemplateColumns: `repeat(${board.columns.length + (boardId ? 1 : 0)}, minmax(0, 1fr))` }}>
            {board.columns.map((column) => (
              <KanbanColumn
                key={column.id}
                column={column}
                cards={column.cardIds.map((cardId) => board.cards[cardId])}
                onRename={handleRenameColumn}
                onAddCard={handleAddCard}
                onDeleteCard={handleDeleteCard}
                onEditCard={setEditingCard}
                onDeleteColumn={board.columns.length > 1 ? handleDeleteColumn : undefined}
              />
            ))}
            {boardId && (
              <div className="flex min-h-[520px] flex-col items-center justify-center rounded-3xl border-2 border-dashed border-[var(--stroke)] bg-[var(--surface)] p-4">
                <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
                  Add Column
                </p>
                <input
                  type="text"
                  value={newColumnTitle}
                  onChange={(e) => setNewColumnTitle(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddColumn()}
                  placeholder="Column name..."
                  className="w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm outline-none focus:border-[var(--primary-blue)]"
                />
                <button
                  onClick={handleAddColumn}
                  disabled={!newColumnTitle.trim()}
                  className="mt-2 rounded-xl bg-[var(--primary-blue)] px-4 py-2 text-xs font-semibold text-white transition hover:opacity-90 disabled:opacity-40"
                >
                  Add
                </button>
              </div>
            )}
          </section>
          <DragOverlay>
            {activeCard ? (
              <div className="w-[260px]">
                <KanbanCardPreview card={activeCard} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </main>
      <ChatSidebar onBoardUpdate={setBoard} onAuthError={onAuthError} />

      {editingCard && (
        <CardDetailModal
          card={editingCard}
          boardLabels={board.labels ?? []}
          boardMembers={board.members ?? []}
          onClose={() => setEditingCard(null)}
          onUpdate={handleCardUpdate}
          onAuthError={onAuthError}
        />
      )}
    </div>
  );
};
