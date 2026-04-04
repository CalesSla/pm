import type { BoardData, BoardMember, BoardSummary, ChecklistItem, Comment, Priority } from "./kanban";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request(url: string, options?: RequestInit) {
  const res = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (res.status === 401) {
    throw new AuthError();
  }
  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body || `Request failed: ${res.status}`);
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

// ── Auth ────────────────────────────────────────────────────────────

export async function register(
  username: string,
  password: string,
  displayName?: string,
): Promise<{ username: string; display_name: string }> {
  const res = await request("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password, display_name: displayName || "" }),
  });
  return res.json();
}

export async function updateProfile(displayName: string): Promise<{ display_name: string }> {
  const res = await request("/api/auth/profile", {
    method: "PUT",
    body: JSON.stringify({ display_name: displayName }),
  });
  return res.json();
}

export async function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<void> {
  await request("/api/auth/password", {
    method: "PUT",
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}

// ── Boards ──────────────────────────────────────────────────────────

export async function listBoards(): Promise<BoardSummary[]> {
  const res = await request("/api/boards");
  const data = await res.json();
  return data.boards;
}

export async function createBoard(title: string): Promise<{ id: number; title: string }> {
  const res = await request("/api/boards", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
  return res.json();
}

export async function renameBoard(boardId: number, title: string) {
  await request(`/api/boards/${boardId}`, {
    method: "PUT",
    body: JSON.stringify({ title }),
  });
}

export async function deleteBoard(boardId: number) {
  await request(`/api/boards/${boardId}`, { method: "DELETE" });
}

export type BoardStats = {
  total_cards: number;
  member_count: number;
  columns: { title: string; card_count: number }[];
};

export async function fetchBoardStats(boardId: number): Promise<BoardStats> {
  const res = await request(`/api/boards/${boardId}/stats`);
  return res.json();
}

export async function fetchBoardById(boardId: number): Promise<BoardData> {
  const res = await request(`/api/boards/${boardId}`);
  return res.json();
}

// ── Legacy single-board ─────────────────────────────────────────────

export async function fetchBoard(): Promise<BoardData> {
  const res = await request("/api/board");
  return res.json();
}

// ── Columns ─────────────────────────────────────────────────────────

export async function renameColumn(columnId: string, title: string) {
  await request(`/api/columns/${dbId(columnId)}`, {
    method: "PUT",
    body: JSON.stringify({ title }),
  });
}

export async function createColumn(
  boardId: number,
  title: string,
): Promise<{ id: number; title: string; position: number }> {
  const res = await request("/api/columns", {
    method: "POST",
    body: JSON.stringify({ board_id: boardId, title }),
  });
  return res.json();
}

export async function deleteColumn(columnId: string) {
  await request(`/api/columns/${dbId(columnId)}`, { method: "DELETE" });
}

// ── Search ──────────────────────────────────────────────────────────

export type SearchResult = {
  id: string;
  title: string;
  details: string;
  due_date: string | null;
  column_id: string;
  column_title: string;
};

export async function searchCards(
  boardId: number,
  query: string,
): Promise<SearchResult[]> {
  const res = await request(`/api/boards/${boardId}/search?q=${encodeURIComponent(query)}`);
  const data = await res.json();
  return data.results;
}

// ── Activity ───────────────────────────────────────────────────────

export type ActivityEntry = {
  id: number;
  action: string;
  detail: string;
  card_id: string | null;
  created_at: string;
  user: { username: string; display_name: string };
};

export async function fetchActivity(boardId: number, limit = 20): Promise<ActivityEntry[]> {
  const res = await request(`/api/boards/${boardId}/activity?limit=${limit}`);
  const data = await res.json();
  return data.activity;
}

// ── Cards ───────────────────────────────────────────────────────────

export async function createCard(
  columnId: string,
  title: string,
  details: string,
  dueDate?: string | null,
  priority?: Priority,
): Promise<{ id: string; title: string; details: string; due_date: string | null; priority: Priority }> {
  const res = await request("/api/cards", {
    method: "POST",
    body: JSON.stringify({
      column_id: dbId(columnId),
      title,
      details,
      due_date: dueDate || null,
      priority: priority || "none",
    }),
  });
  const data = await res.json();
  return { id: `card-${data.id}`, title: data.title, details: data.details, due_date: data.due_date, priority: data.priority };
}

export async function updateCard(
  cardId: string,
  data: { title?: string; details?: string; due_date?: string | null; priority?: Priority },
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
  targetPosition: number,
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

// ── Labels ──────────────────────────────────────────────────────────

export async function createLabel(
  boardId: number,
  name: string,
  color: string,
): Promise<{ id: number; name: string; color: string }> {
  const res = await request("/api/labels", {
    method: "POST",
    body: JSON.stringify({ board_id: boardId, name, color }),
  });
  return res.json();
}

export async function updateLabel(
  labelId: number,
  data: { name?: string; color?: string },
): Promise<{ id: number; name: string; color: string }> {
  const res = await request(`/api/labels/${labelId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function deleteLabel(labelId: number) {
  await request(`/api/labels/${labelId}`, { method: "DELETE" });
}

export async function addCardLabel(cardId: string, labelId: number) {
  await request("/api/cards/labels", {
    method: "POST",
    body: JSON.stringify({ card_id: dbId(cardId), label_id: labelId }),
  });
}

export async function removeCardLabel(cardId: string, labelId: number) {
  await request(`/api/cards/${dbId(cardId)}/labels/${labelId}`, {
    method: "DELETE",
  });
}

// ── Comments ───────────────────────────────────────────────────────

export async function listComments(cardId: string): Promise<Comment[]> {
  const res = await request(`/api/cards/${dbId(cardId)}/comments`);
  const data = await res.json();
  return data.comments;
}

export async function createComment(cardId: string, content: string): Promise<Comment> {
  const res = await request(`/api/cards/${dbId(cardId)}/comments`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
  return res.json();
}

export async function deleteComment(commentId: number) {
  await request(`/api/comments/${commentId}`, { method: "DELETE" });
}

// ── Board members ──────────────────────────────────────────────────

export async function listBoardMembers(boardId: number): Promise<BoardMember[]> {
  const res = await request(`/api/boards/${boardId}/members`);
  const data = await res.json();
  return data.members;
}

export async function addBoardMember(
  boardId: number,
  username: string,
  role?: string,
): Promise<BoardMember> {
  const res = await request(`/api/boards/${boardId}/members`, {
    method: "POST",
    body: JSON.stringify({ username, role: role || "member" }),
  });
  return res.json();
}

export async function removeBoardMember(boardId: number, memberId: number) {
  await request(`/api/boards/${boardId}/members/${memberId}`, { method: "DELETE" });
}

// ── Card assignments ───────────────────────────────────────────────

export async function assignCard(cardId: string, userId: number): Promise<BoardMember> {
  const res = await request(`/api/cards/${dbId(cardId)}/assign`, {
    method: "POST",
    body: JSON.stringify({ user_id: userId }),
  });
  return res.json();
}

export async function unassignCard(cardId: string, userId: number) {
  await request(`/api/cards/${dbId(cardId)}/assign/${userId}`, { method: "DELETE" });
}

// ── Checklist ─────────────────────────────────────────────────────

export async function listChecklistItems(cardId: string): Promise<ChecklistItem[]> {
  const res = await request(`/api/cards/${dbId(cardId)}/checklist`);
  const data = await res.json();
  return data.items;
}

export async function createChecklistItem(
  cardId: string,
  title: string,
): Promise<ChecklistItem> {
  const res = await request(`/api/cards/${dbId(cardId)}/checklist`, {
    method: "POST",
    body: JSON.stringify({ title }),
  });
  return res.json();
}

export async function updateChecklistItem(
  itemId: number,
  data: { title?: string; checked?: boolean },
): Promise<ChecklistItem> {
  const res = await request(`/api/checklist/${itemId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function deleteChecklistItem(itemId: number) {
  await request(`/api/checklist/${itemId}`, { method: "DELETE" });
}

// ── Chat ────────────────────────────────────────────────────────────

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type ChatResponse = {
  message: string;
  actions: unknown[];
  action_results: unknown[];
  board: BoardData;
};

export async function sendChatMessage(
  message: string,
  history: ChatMessage[],
): Promise<ChatResponse> {
  const res = await request("/api/ai/chat", {
    method: "POST",
    body: JSON.stringify({ message, history }),
  });
  return res.json();
}
