---
name: clibo-books
description: Track books with the `clibo books` CLI — adding to wishlist, logging reading sessions (pages + minutes for pace), starting/finishing, ratings, and per-session history. Use when the user mentions reading, finishing, or wanting to know "what did I read last week" / "how fast do I read?".
---

# 📚 clibo books

Reading log with **per-session tracking** — every `books read` writes
both a cumulative page-count update on the book *and* a session row
recording pages, minutes, and date. That gives you pages-per-hour
pace, a `history` view, and reading-day counts. Local SQLite, every
command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo books add TITLE -a AUTHOR -p PAGES` | Add a book (default status `wishlist`) |
| `clibo books read BOOK PAGES [-t MIN] [-d DATE]` | Log a reading session; auto-promotes wishlist → reading; auto-finishes at total |
| `clibo books start BOOK` | Move a book to `reading` |
| `clibo books finish BOOK -r RATING` | Mark finished with optional 1–5 rating |
| `clibo books history [--days N] [-b BOOK]` | Recent reading sessions |
| `clibo books edit BOOK [...]` | Update any field |
| `clibo books list [-s STATUS]` | List books |
| `clibo books show BOOK` | Detail |
| `clibo books rm BOOK` | Delete (ID or title; cascades sessions) |
| `clibo books stats` | Reading stats incl. avg pages/hour |

`BOOK` accepts numeric ID or a fuzzy title (exact wins over substring).
Statuses: `wishlist`, `reading`, `finished`, `dnf`.

## Natural language → command

| User says | Command |
|---|---|
| "Read 30 pages of Atomic Habits in 45 min" | `clibo books read "Atomic Habits" 30 -t 45` |
| "I read 25 more pages of it yesterday" | `clibo books read "Atomic Habits" 25 -d yesterday` |
| "I finished Dune, 5 stars" | `clibo books finish "Dune" -r 5` |
| "Add 'The Hobbit' to my wishlist" | `clibo books add "The Hobbit" -a Tolkien` |
| "What did I read last week?" | `clibo books history --days 7` |
| "How fast do I read?" | `clibo books stats` (see `avg_pages_per_hour`) |
| "What am I reading?" | `clibo books list -s reading` |
| "Fix the page count on Atomic Habits" | `clibo books edit "Atomic Habits" -p 320` |
| "Drop Westworld — DNF" | `clibo books edit "Westworld" -s dnf` |

## For agents

```bash
clibo books read "Atomic Habits" 30 -t 45 --json
# -> { ..., "pages_read": 30, "progress_pct": 9.4,
#      "session_id", "session_pages": 30, "session_minutes": 45,
#      "session_pages_per_hour": 40.0 }

clibo books history --days 7 --json
# -> [ { "id", "entry_date", "book", "pages", "minutes", "pages_per_hour" }, ... ]

clibo books stats --json
# -> { "finished", "reading", "total_pages_read", "sessions_logged",
#      "avg_pages_per_hour", "days_read", ... }
```

`books read` returns the session row inline (`session_id`, `session_minutes`,
`session_pages_per_hour`) so agents don't need a second call to confirm.
`books rm` cascades — deleting a book also drops every session row pointing
at it.
