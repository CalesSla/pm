# The Project Management MVP web app

## Business Requirements

This project is building a Project Management App. Key features:
- A user can sign in
- When signed in, the user sees a Kanban board representing their project
- The Kanban board has fixed columns that can be renamed
- The cards on the Kanban board can be moved with drag and drop, and edited
- There is an AI chat feature in a sidebar; the AI is able to create / edit / move one or more cards

## Limitations

For the MVP, there will only be a user sign in (hardcoded to 'user' and 'password') but the database will support multiple users for future.

For the MVP, there will only be 1 Kanban board per signed in user.

For the MVP, this will run locally (in a docker container)

## Technical Decisions

- NextJS frontend
- Python FastAPI backend, including serving the static NextJS site at /
- Everything packaged into a Docker container
- Use "uv" as the package manager for python in the Docker container
- Use OpenRouter for the AI calls. An OPENROUTER_API_KEY is in .env in the project root
- Use `openai/gpt-oss-120b` as the model
- Use SQLite local database, stored at data/pm.db (Docker volume mount). Create the db if it doesn't exist.
- Start and Stop server scripts for Mac, PC, Linux in scripts/
- Start scripts pass .env variables into the Docker container

## Existing Frontend

The frontend/ directory contains a working Next.js demo of the Kanban board (client-side only, no backend integration).

### Architecture

- **Framework:** Next.js 16 with App Router, React 19, TypeScript (strict)
- **Styling:** Tailwind CSS v4 with CSS variables for theming, no CSS modules
- **Fonts:** Space Grotesk (headings), Manrope (body) via Google Fonts
- **Drag-and-drop:** @dnd-kit/core + @dnd-kit/sortable
- **State:** React hooks in KanbanBoard component, props drilled down, immutable updates
- **No API calls:** All data is hardcoded initial state + local mutations

### Components

- `src/app/page.tsx` - Home page, renders KanbanBoard
- `src/app/layout.tsx` - Root layout with metadata and font setup
- `src/app/globals.css` - CSS variables (color scheme) and Tailwind import
- `src/components/KanbanBoard.tsx` - Main state container, DndContext, header, grid layout
- `src/components/KanbanColumn.tsx` - Droppable column with editable title, card list, NewCardForm
- `src/components/KanbanCard.tsx` - Draggable card with title, details, delete button
- `src/components/KanbanCardPreview.tsx` - Read-only card shown in DragOverlay during drag
- `src/components/NewCardForm.tsx` - Toggle button/form to add cards to a column

### Data Model (client-side)

```typescript
type Card = { id: string, title: string, details: string }
type Column = { id: string, title: string, cardIds: string[] }
type BoardData = { columns: Column[], cards: Record<string, Card> }
```

- 5 default columns: Backlog, Discovery, In Progress, Review, Done
- 8 sample cards distributed across columns
- `moveCard()` in `src/lib/kanban.ts` handles within-column reorder and cross-column moves

### Testing

- **Unit tests:** Vitest + React Testing Library + jest-dom (src/**/*.test.{ts,tsx})
- **E2E tests:** Playwright with Chromium (tests/kanban.spec.ts)
- **Scripts:** `npm run test:unit`, `npm run test:e2e`, `npm run test:all`

### Dependencies

Runtime: next, react, react-dom, @dnd-kit/core, @dnd-kit/sortable, @dnd-kit/utilities, clsx
Dev: vitest, @testing-library/react, @playwright/test, tailwindcss, typescript, eslint

## Color Scheme

- Accent Yellow: `#ecad0a` - accent lines, highlights
- Blue Primary: `#209dd7` - links, key sections
- Purple Secondary: `#753991` - submit buttons, important actions
- Dark Navy: `#032147` - main headings
- Gray Text: `#888888` - supporting text, labels

## Coding standards

1. Use latest versions of libraries and idiomatic approaches as of today
2. Keep it simple - NEVER over-engineer, ALWAYS simplify, NO unnecessary defensive programming. No extra features - focus on simplicity.
3. Be concise. Keep README minimal. IMPORTANT: no emojis ever
4. When hitting issues, always identify root cause before trying a fix. Do not guess. Prove with evidence, then fix the root cause.

## Working documentation

All documents for planning and executing this project will be in the docs/ directory.
Please review the docs/PLAN.md document before proceeding.