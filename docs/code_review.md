# Code Review Report

Comprehensive review of the PM app codebase. Issues are grouped by severity and area, with concrete action items.

---

## Critical

### 1. No error handling around AI JSON parsing

**File:** `backend/app/api/ai.py:124-125`

```python
raw = response.choices[0].message.content
parsed = json.loads(raw)
```

If the AI returns malformed JSON (or the response has no choices), this crashes with an unhandled 500. The AI model is external and its output is not guaranteed.

**Action:** Wrap in try/except. Return a user-friendly error message on parse failure. Guard `response.choices` being empty.

### 2. Database connections leak on exceptions

**Files:** `backend/app/api/board.py`, `backend/app/api/auth.py`, `backend/app/api/ai.py`, `backend/app/ai/actions.py`

Every database function follows the pattern:

```python
conn = get_connection()
# ... multiple operations ...
conn.close()
```

If any operation raises between open and close, the connection leaks. This applies to ~15 functions across the codebase.

**Action:** Add a context manager to `db/__init__.py`:

```python
from contextlib import contextmanager

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
```

Then replace all `conn = get_connection()` / `conn.close()` pairs with `with get_db() as conn:`.

### 3. E2E tests are completely broken

**File:** `frontend/tests/kanban.spec.ts`

All 3 Playwright tests fail. They were written for the pre-auth client-side-only app (Part 2-3) and never updated after login was added (Part 4). Tests navigate to `/` and expect the Kanban board immediately, but now see the login form.

**Action:** Update E2E tests to:
- Log in before each test (via API call or form interaction)
- Point at the correct server (port 3000 for dev, or port 8000 for Docker)
- Update selectors/assertions if the UI changed

---

## High

### 4. Optimistic UI updates with no rollback

**File:** `frontend/src/components/KanbanBoard.tsx`

- `handleDeleteCard` (line 129): removes card from state before API call. If the API fails, the card disappears from UI but still exists in the database.
- `handleRenameColumn` (line 91): same pattern. State updates immediately, API failure is silently caught.
- `handleDragEnd` (line 67): reorder is applied locally, API failure leaves UI and DB out of sync.

All three `.catch(handleApiError)` only handle `AuthError`; other failures are swallowed silently.

**Action:** Either (a) wait for the API response before updating state, or (b) save previous state and roll back on error. At minimum, show a user-visible error when a mutation fails.

### 5. `api.ts` does not check response status (except 401)

**File:** `frontend/src/lib/api.ts:3-12`

The `request()` wrapper only checks for 401. A 404 or 500 response is silently treated as success -- `res.json()` will either fail or return an error body that callers don't inspect.

**Action:** Add `if (!res.ok) throw new Error(...)` after the 401 check, so callers actually see failures.

### 6. Sessions never expire

**File:** `backend/app/api/auth.py:12`

`sessions: dict[str, int] = {}` grows without bound. Tokens live forever until explicit logout or server restart.

**Action:** Store a timestamp with each session. Add a TTL check (e.g. 24 hours) in `get_current_user_id`. Optionally add periodic cleanup.

### 7. Missing auth tests for mutation endpoints

**File:** `backend/tests/test_board.py`

Only `test_get_board_unauthenticated` tests the 401 path. There are no tests verifying that `POST /api/cards`, `PUT /api/cards/:id`, `DELETE /api/cards/:id`, `PUT /api/columns/:id`, or `PUT /api/board/reorder` return 401 without a session.

**Action:** Add unauthenticated tests for each mutation endpoint.

---

## Medium

### 8. Cookie missing `secure` flag

**File:** `backend/app/api/auth.py:35`

```python
response.set_cookie(key="session", value=token, httponly=True, samesite="lax")
```

Missing `secure=True`. For MVP running locally over HTTP this is fine, but should be added before any non-localhost deployment.

**Action:** Add `secure=True` when not in development mode, or add a TODO for production readiness.

### 9. Duplicate `_require_auth` / `_get_board_id` functions

**Files:** `backend/app/api/board.py:10-18` and `backend/app/api/ai.py:15-23`

The `_require_auth` helper is copy-pasted identically in both files. `_get_board_id` is defined in `board.py` and imported by `ai.py` (correctly), but the auth helper should also be shared.

**Action:** Move `_require_auth` to a shared location (e.g. `auth.py` alongside `get_current_user_id`) and import from both routers.

### 10. No input validation on reorder positions

**File:** `backend/app/api/board.py:204-265`

`target_position` is accepted as any integer. Negative values or values larger than the column's card count will create gaps or negative positions in the database, corrupting card ordering.

**Action:** Clamp `target_position` to `[0, card_count]` before applying the reorder.

### 11. AI action schema is overly flat

**File:** `backend/app/ai/client.py:23-51`

All fields (`column_id`, `card_id`, `title`, `details`, `position`) are required for every action type, even when irrelevant (e.g. `card_id` for `create_card`). They're all nullable to work around this. This means the AI can send nonsensical combinations (e.g. `delete_card` with a `title`).

**Action:** This works for MVP since `actions.py` ignores irrelevant fields. Consider refactoring to per-action-type schemas if AI sends bad combinations in practice.

### 12. Race condition in card position calculation

**File:** `backend/app/api/board.py:123-125` and `backend/app/ai/actions.py:35-37`

New card position is calculated as `COUNT(*)` before insert. Concurrent requests could get the same count, producing duplicate positions. SQLite's default serialized writes mostly prevent this, but it's not guaranteed under WAL mode.

**Action:** Acceptable for single-user MVP. For multi-user, wrap in a transaction with an explicit lock or use `MAX(position) + 1`.

### 13. `get_ai_client()` creates a new client on every request

**File:** `backend/app/ai/client.py:62-67`

A new `OpenAI()` client is instantiated per request. This creates a new HTTP connection pool each time.

**Action:** Create the client once at module level or cache it.

### 14. Network errors on auth check treated as logged-out

**File:** `frontend/src/app/page.tsx:11-13`

```typescript
fetch("/api/auth/me")
  .then((res) => setAuthed(res.ok))
  .catch(() => setAuthed(false));
```

A network error (server down, timeout) sets `authed = false`, showing the login form instead of an error message.

**Action:** Distinguish between "not authenticated" (401) and "can't reach server" (network error). Show an appropriate message for each.

---

## Low

### 15. Inconsistent error response format

**Files:** `backend/app/api/auth.py`, `board.py`, `ai.py`

Some endpoints return `Response(content='{"error":"..."}', ...)` while others return dicts. The 401 responses use raw JSON strings; Pydantic-validated endpoints return dicts. This makes client-side error parsing inconsistent.

**Action:** Standardize on `HTTPException` or a consistent error dict pattern.

### 16. `handleLogout` has no error handling

**File:** `frontend/src/app/page.tsx:22-25`

```typescript
async function handleLogout() {
  await fetch("/api/auth/logout", { method: "POST" });
  setAuthed(false);
}
```

If the logout request fails, the user is shown the login form but their session is still valid on the server.

**Action:** Wrap in try/catch; still show login form (user intent is clear) but log the error.

### 17. `ChatSidebar` XSS is a non-issue (React auto-escapes)

The agent flagged `{msg.content}` as XSS-vulnerable. This is incorrect -- React's JSX expression rendering (`{}`) auto-escapes strings. There is no `dangerouslySetInnerHTML` usage anywhere. No action needed.

### 18. Playwright config needs update for integrated app

**File:** `frontend/playwright.config.ts:10-17`

```typescript
baseURL: "http://127.0.0.1:3000",
webServer: {
  command: "npm run dev -- --hostname 127.0.0.1 --port 3000",
```

E2E tests point at the Next.js dev server (port 3000), which only serves the frontend without the backend API. For integration testing, tests should run against the Docker container (port 8000) or a local backend.

**Action:** Update config to either (a) run against Docker on port 8000, or (b) start both frontend and backend for E2E. Related to issue #3.

---

## Action Summary

| # | Issue | Severity | Effort |
|---|-------|----------|--------|
| 1 | Wrap AI JSON parsing in try/except | Critical | Small |
| 2 | Add DB connection context manager | Critical | Medium |
| 3 | Fix E2E tests for auth flow | Critical | Medium |
| 4 | Add rollback or error feedback for optimistic updates | High | Medium |
| 5 | Check `res.ok` in `api.ts` request wrapper | High | Small |
| 6 | Add session TTL | High | Small |
| 7 | Add auth tests for mutation endpoints | High | Small |
| 8 | Add `secure` flag to session cookie | Medium | Small |
| 9 | Deduplicate `_require_auth` | Medium | Small |
| 10 | Validate reorder position bounds | Medium | Small |
| 11 | Consider per-type AI action schemas | Medium | Medium |
| 12 | Transaction-safe position calculation | Medium | Small |
| 13 | Cache AI client instance | Medium | Small |
| 14 | Distinguish network error from 401 on auth check | Medium | Small |
| 15 | Standardize error response format | Low | Medium |
| 16 | Add error handling to logout | Low | Small |
| 17 | XSS false alarm (no action) | -- | -- |
| 18 | Update Playwright config for backend | Low | Small |
