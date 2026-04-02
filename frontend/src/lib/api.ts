import type { BoardData } from "./kanban";

async function request(url: string, options?: RequestInit) {
  const res = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (res.status === 401) {
    throw new AuthError();
  }
  return res;
}

/** Strip "col-" or "card-" prefix to get the numeric DB id */
function dbId(prefixedId: string): number {
  return Number(prefixedId.replace(/^(col-|card-)/, ""));
}

export class AuthError extends Error {
  constructor() {
    super("Not authenticated");
  }
}

export async function fetchBoard(): Promise<BoardData> {
  const res = await request("/api/board");
  return res.json();
}

export async function renameColumn(columnId: string, title: string) {
  await request(`/api/columns/${dbId(columnId)}`, {
    method: "PUT",
    body: JSON.stringify({ title }),
  });
}

export async function createCard(
  columnId: string,
  title: string,
  details: string
): Promise<{ id: string; title: string; details: string }> {
  const res = await request("/api/cards", {
    method: "POST",
    body: JSON.stringify({ column_id: dbId(columnId), title, details }),
  });
  const data = await res.json();
  return { id: `card-${data.id}`, title: data.title, details: data.details };
}

export async function updateCard(
  cardId: string,
  data: { title?: string; details?: string }
) {
  await request(`/api/cards/${dbId(cardId)}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteCard(cardId: string) {
  await request(`/api/cards/${dbId(cardId)}`, { method: "DELETE" });
}

export async function reorderCard(
  cardId: string,
  targetColumnId: string,
  targetPosition: number
) {
  await request("/api/board/reorder", {
    method: "PUT",
    body: JSON.stringify({
      card_id: dbId(cardId),
      target_column_id: dbId(targetColumnId),
      target_position: targetPosition,
    }),
  });
}
