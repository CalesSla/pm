# Database Design

## Overview

SQLite database stored at `data/pm.db`. Created automatically on first run. WAL mode for concurrent reads. Foreign keys enforced.

## Schema

Four tables: `users` -> `boards` -> `columns` -> `cards`.

### users

Stores credentials. MVP has one hardcoded user ("user"/"password") but the schema supports multiple users for future expansion. Passwords stored as bcrypt hashes.

### boards

One board per user for MVP. The `user_id` foreign key links to `users`. Extensible to multiple boards per user later.

### columns

Ordered by `position` (0-indexed). Each column belongs to a board. New users get 5 default columns: Backlog, Discovery, In Progress, Review, Done.

### cards

Ordered by `position` within their column (0-indexed). Each card belongs to a column. Moving a card between columns updates `column_id` and `position`.

## Relationships

```
users 1--* boards 1--* columns 1--* cards
```

## Ordering

Column and card order is determined by the `position` integer field. When reordering, all affected positions in the column are updated in a single transaction.

## Seeding

On first run, if the database is empty:
1. Create the "user" account with a hashed password
2. Create a default board
3. Create 5 default columns
4. Create sample cards

## Migration Strategy

For MVP, the schema is created fresh if the database file does not exist. No migration tooling needed at this stage.
