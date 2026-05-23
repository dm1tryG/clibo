---
name: clibo-books
description: Track books with the `clibo books` CLI. Use when the user mentions reading, starting/finishing a book, logging pages, or rating one. Maps phrases like "I read 30 pages of X" to `clibo books read X 30`.
---

# 📚 clibo books

Reading log. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo books add TITLE -a AUTHOR -p PAGES` | Add a book (default status `wishlist`) |
| `clibo books read BOOK PAGES` | Log a reading session; auto-promotes wishlist → reading; auto-finishes at total pages |
| `clibo books start BOOK` | Move a book to `reading` |
| `clibo books finish BOOK -r RATING` | Mark finished with optional 1–5 rating |
| `clibo books list [-s STATUS]` | List books |
| `clibo books show BOOK` | Detail |
| `clibo books rm ID` | Delete |
| `clibo books stats` | Reading stats |

`BOOK` accepts numeric ID or a fuzzy title match. Statuses: `wishlist`,
`reading`, `finished`, `dnf`.

## For agents

Common natural-language mappings:

| User says | Command |
|---|---|
| "I read 30 pages of Atomic Habits" | `clibo books read "Atomic Habits" 30` |
| "I finished Dune, 5 stars" | `clibo books finish "Dune" -r 5` |
| "Add 'The Hobbit' to my wishlist" | `clibo books add "The Hobbit"` |
| "What am I reading?" | `clibo books list -s reading` |

```bash
clibo books read "Atomic Habits" 30 --json
# -> { "id", "title", "status", "pages_read", "progress_pct", ... }
```
