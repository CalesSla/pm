# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Project Management App with a Kanban board, authentication, and AI chat sidebar. Monorepo with a Next.js frontend and Python FastAPI backend, packaged in a single Docker container.

## Commands

### Running the app
```bash
scripts/start.sh          # Build and start Docker container (requires .env with OPENROUTER_API_KEY)
scripts/stop.sh            # Stop the container
# App runs at http://localhost:8000
```

### Frontend (from frontend/)
```bash
npm run dev                # Next.js dev server
npm run build              # Static export build
npm run lint               # ESLint
npm run test:unit          # Vitest unit tests
npm run test:unit:watch    # Vitest in watch mode
npm run test:e2e           # Playwright E2E tests
npm run test:all           # Unit + E2E
```

### Backend (from backend/)
```bash
uv run pytest                          # All backend tests
uv run pytest tests/test_board.py      # Single test file
uv run pytest tests/test_board.py -k test_name  # Single test
uv run uvicorn app.main:app --reload   # Dev server on port 8000
```

## Architecture

### Two-tier monorepo
- **frontend/** - Next.js 16 (App Router, React 19, TypeScript strict, Tailwind CSS v4)
- **backend/** - FastAPI with SQLite, managed by `uv`
- In production Docker build, frontend is statically exported (`output: 'export'`) and served by FastAPI at `/`

### Backend structure (backend/app/)
- **main.py** - FastAPI app with lifespan handler (inits DB on startup), serves static frontend, mounts API router
- **db/__init__.py** - SQLite connection management, schema creation, seed data. `DB_PATH` defaults to `data/pm.db`. Table `columns_` (underscore) avoids SQLite reserved word
- **api/** - All routes under `/api` prefix. Sub-routers: `auth` (login/logout/me, in-memory sessions via httpOnly cookies), `board` (CRUD for columns/cards, reorder endpoint), `ai` (chat endpoint)
- **ai/client.py** - OpenAI-compatible client pointed at OpenRouter (`openai/gpt-oss-120b`)
- **ai/actions.py** - Parses AI structured output into board mutations (create/update/delete/move cards)

### Frontend structure (frontend/src/)
- **lib/api.ts** - API client with `AuthError` class; strips `col-`/`card-` ID prefixes via `dbId()` when sending mutations
- **lib/kanban.ts** - Pure `moveCard()` function handling within-column reorder and cross-column moves
- **components/KanbanBoard.tsx** - Main state container with DndContext; fetches board from API on mount
- **components/ChatSidebar.tsx** - AI chat sidebar; sends messages to `/api/ai/chat`, refreshes board on AI actions
- **components/LoginForm.tsx** - Login form; credentials are "user"/"password"

### Key design decisions
- Board API returns prefixed IDs (`col-1`, `card-1`) so the client-side drag-and-drop can distinguish columns from cards. The API client strips these prefixes when sending mutations back.
- Auth uses bcrypt-hashed passwords in SQLite, in-memory session store (dict of token -> user_id), httpOnly cookies
- AI receives full board state as JSON in the system prompt with each message, returns structured actions

### Testing
- **Backend:** pytest with `httpx` TestClient. `conftest.py` creates a fresh temp SQLite DB per test via `monkeypatch`. Use `authed_client` fixture for authenticated requests.
- **Frontend:** Vitest + React Testing Library + jest-dom. Tests colocated as `*.test.{ts,tsx}`.

## Coding Standards

1. Use latest library versions and idiomatic approaches
2. Keep it simple - never over-engineer, always simplify, no unnecessary defensive programming
3. Be concise. No emojis ever.
4. When hitting issues, identify root cause before trying a fix. Prove with evidence, then fix.

## Reference

- **docs/PLAN.md** - Detailed implementation plan with completed/remaining steps
- **docs/DATABASE.md** - Schema rationale and relationships
- **docs/schema.json** - SQLite schema definition
- **AGENTS.md** - Business requirements and technical decisions (source of truth for product scope)



## DETAILED PLAN

@docs/PLAN.md