# High level steps for project

## Part 1: Plan

- [x] Enrich this document with detailed substeps, checklists, and success criteria
- [x] Update root AGENTS.md with frontend codebase description
- [x] Get user approval on the plan

---

## Part 2: Scaffolding

Set up Docker, FastAPI backend, and start/stop scripts serving a hello world page.

- [x] Create `backend/` structure with `pyproject.toml` (FastAPI, uvicorn, uv)
- [x] Create `backend/app/main.py` with FastAPI app serving a hello world HTML page at `/`
- [x] Create `backend/app/api/__init__.py` with a `/api/health` endpoint returning JSON
- [x] Create `Dockerfile` in project root: multi-stage build (Node for frontend, Python for backend)
- [x] Create `docker-compose.yml` with volume mount for `data/` directory
- [x] Create `scripts/start.sh` (Mac/Linux) - reads `.env`, runs docker compose up
- [x] Create `scripts/start.bat` (Windows) - reads `.env`, runs docker compose up
- [x] Create `scripts/stop.sh` (Mac/Linux) - runs docker compose down
- [x] Create `scripts/stop.bat` (Windows) - runs docker compose down
- [x] Make shell scripts executable

**Success criteria:**
- `scripts/start.sh` builds and starts the container
- Browser at `http://localhost:8000` shows hello world HTML
- `http://localhost:8000/api/health` returns `{"status": "ok"}`
- `scripts/stop.sh` stops the container
- `data/` directory is mounted as a volume

---

## Part 3: Add in Frontend

Build Next.js frontend statically and serve it via FastAPI, with the Kanban board at /.

- [x] Update `next.config.ts` to use `output: 'export'` for static HTML generation
- [x] Adjust any Next.js features incompatible with static export (if needed)
- [x] Update `Dockerfile` to build frontend with `npm run build` and copy output to backend's static directory
- [x] Update FastAPI to serve the static Next.js build at `/` using `StaticFiles`
- [x] Ensure API routes (`/api/*`) take precedence over static file serving
- [x] Verify drag-and-drop, card add/delete, column rename all work in the Docker build
- [x] Add backend unit tests (pytest) for static file serving and API health endpoint
- [x] Ensure existing frontend unit tests still pass

**Success criteria:**
- `http://localhost:8000` shows the full Kanban board with all 5 columns
- Drag-and-drop, card creation, card deletion, column renaming all work
- `/api/health` still returns `{"status": "ok"}`
- All frontend unit tests pass
- Backend tests pass

---

## Part 4: Add in a fake user sign in experience

Add login screen with hardcoded credentials, session management, and logout.

- [x] Create a `/api/auth/login` endpoint accepting `{"username", "password"}`, returning a session token
- [x] Create a `/api/auth/logout` endpoint that invalidates the session
- [x] Create a `/api/auth/me` endpoint that returns current user info if authenticated
- [x] Implement simple token-based session (stored in memory)
- [x] Create a `LoginForm` component in the frontend with username/password fields
- [x] Update the frontend to check auth state on load; show login if unauthenticated
- [x] Store the session token in an httpOnly cookie
- [x] Add logout button to the Kanban board header
- [x] Add frontend unit tests for LoginForm component
- [x] Add backend unit tests for auth endpoints (valid login, invalid login, logout, session check)

**Success criteria:**
- Visiting `/` when not logged in shows the login form
- Logging in with "user"/"password" shows the Kanban board
- Logging in with wrong credentials shows an error
- Clicking logout returns to login screen
- Refreshing the page after login keeps you logged in
- All tests pass

---

## Part 5: Database modeling

Design and document the SQLite schema for persisting Kanban data.

- [ ] Design schema supporting: users, boards, columns (ordered), cards (ordered within columns)
- [ ] Save schema as `docs/schema.json` (JSON representation of tables, columns, types, constraints)
- [ ] Document the database approach in `docs/DATABASE.md` (schema rationale, relationships, migration strategy)
- [ ] Get user sign-off on the schema

**Schema should support:**
- Multiple users (for future) with hashed passwords
- One board per user (MVP), extensible to multiple
- Columns with a position/order field
- Cards with title, details, position within column, timestamps
- Foreign key relationships enforced

**Success criteria:**
- Schema is documented and reviewed
- Schema supports all current Kanban operations (CRUD cards, reorder, move between columns, rename columns)
- Schema is normalized and supports future multi-user/multi-board extension

---

## Part 6: Backend API

Add API routes for full Kanban CRUD backed by SQLite.

- [ ] Create database initialization module: create tables from schema if db doesn't exist
- [ ] Seed default data for new users (5 columns, sample cards)
- [ ] Add API endpoints:
  - [ ] `GET /api/board` - get full board (columns + cards) for authenticated user
  - [ ] `PUT /api/columns/:id` - rename a column
  - [ ] `POST /api/cards` - create a card in a column
  - [ ] `PUT /api/cards/:id` - update card title/details
  - [ ] `DELETE /api/cards/:id` - delete a card
  - [ ] `PUT /api/board/reorder` - reorder cards (within/between columns)
- [ ] All endpoints require authentication
- [ ] Write pytest unit tests for each endpoint (happy path + error cases)
- [ ] Test that database is created automatically on first run

**Success criteria:**
- All CRUD operations work via API
- Database is created at `data/pm.db` on first run
- Unauthenticated requests return 401
- All backend tests pass
- Database persists across container restarts (volume mount)

---

## Part 7: Frontend + Backend Integration

Connect the frontend to the backend API so the Kanban board is persistent.

- [ ] Create an API client module in frontend (`src/lib/api.ts`)
- [ ] Replace local state initialization with `GET /api/board` fetch on mount
- [ ] Update card create/delete/edit to call backend API, then update local state
- [ ] Update column rename to call backend API
- [ ] Update drag-and-drop to call `PUT /api/board/reorder` after move
- [ ] Handle loading and error states in the UI
- [ ] Handle 401 responses by redirecting to login
- [ ] Update frontend unit tests to mock API calls
- [ ] Add E2E tests: create card, refresh page, card persists; move card, refresh, position persists

**Success criteria:**
- All Kanban operations persist across page refreshes
- Drag-and-drop changes persist
- Logging out and back in shows the same board state
- UI shows loading state while fetching
- All tests pass

---

## Part 8: AI Connectivity

Connect the backend to OpenRouter for AI calls.

- [ ] Add `openai` Python package to dependencies (OpenRouter is OpenAI-compatible)
- [ ] Create `backend/app/ai/client.py` with OpenRouter client configuration
- [ ] Create a `/api/ai/test` endpoint that sends "What is 2+2?" and returns the response
- [ ] Read `OPENROUTER_API_KEY` from environment variable
- [ ] Use model `openai/gpt-oss-120b`
- [ ] Write pytest test confirming the AI client can be initialized
- [ ] Manual test: call `/api/ai/test` and verify a sensible response

**Success criteria:**
- `/api/ai/test` returns a response from the AI model
- API key is read from environment (passed via start scripts)
- No API key hardcoded in code

---

## Part 9: AI Structured Outputs

Extend the AI integration to understand the Kanban board and return structured updates.

- [ ] Define a structured output schema for AI responses:
  - `message`: text response to the user
  - `actions`: optional list of operations (create_card, update_card, delete_card, move_card)
  - Each action includes the necessary parameters (column_id, card data, target position, etc.)
- [ ] Create `/api/ai/chat` endpoint accepting `{"message", "history"}`
- [ ] System prompt includes the current board state as JSON
- [ ] Parse the structured response and apply any actions to the database
- [ ] Return the AI message and the updated board state to the frontend
- [ ] Support multiple operations in a single AI response
- [ ] Write pytest tests with mocked AI responses to verify action parsing and application
- [ ] Test edge cases: no actions, invalid actions, multiple actions

**Success criteria:**
- AI receives the full board context with each message
- AI can create, edit, delete, and move cards via structured outputs
- Multiple operations in one response work correctly
- Conversation history is maintained
- All tests pass

---

## Part 10: AI Chat Sidebar

Add a chat sidebar to the UI for AI interaction, with live Kanban updates.

- [ ] Create `ChatSidebar` component with:
  - Toggle button to open/close
  - Message history display (user + AI messages)
  - Text input with send button
  - Loading indicator during AI response
- [ ] Style the sidebar matching the app color scheme
- [ ] Connect to `/api/ai/chat` endpoint
- [ ] After receiving AI response, if actions were applied, refresh the board state
- [ ] Maintain conversation history in component state
- [ ] Add frontend unit tests for ChatSidebar component
- [ ] Add E2E test: open chat, ask AI to create a card, verify card appears on board

**Success criteria:**
- Chat sidebar opens/closes smoothly
- Messages display correctly with visual distinction between user and AI
- AI can update the Kanban board through chat, and changes appear immediately
- Conversation history persists within the session
- All tests pass