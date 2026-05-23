---
name: clibo-quotes
description: Save and recall quotes with the `clibo quotes` CLI — a personal commonplace book. Distinct from `notes` (free-form) and `bookmark` (URLs). Maps "Quote: 'X' — Author" to `clibo quotes add "X" -a "Author"`.
---

# 💬 clibo quotes

A commonplace book — quotes worth keeping, with structured author and
source. Distinct from `notes` (free-form, no structure) and `bookmark`
(URLs). Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo quotes add TEXT -a AUTHOR -s SOURCE` | Save a quote (also `-t` tags) |
| `clibo quotes list [-a AUTHOR] [-t TAG]` | List quotes |
| `clibo quotes show ID` | Show one quote pretty-printed |
| `clibo quotes search QUERY` | Search text / author / source / tags |
| `clibo quotes random` | Pick one random quote — for inspiration |
| `clibo quotes rm ID` | Delete |
| `clibo quotes stats` | Counts and most-quoted authors |

## For agents

| User says | Command |
|---|---|
| "Quote: 'Make it work, make it right, make it fast' — Kent Beck" | `clibo quotes add "Make it work, make it right, make it fast" -a "Kent Beck"` |
| "Save this from the book Atomic Habits: 'You don't rise…'" | `clibo quotes add "You don't rise…" -s "Atomic Habits"` |
| "Give me a quote" | `clibo quotes random` |
| "Anything from Naval?" | `clibo quotes list -a Naval` |

```bash
clibo quotes random --json
# -> { "id", "text", "author", "source", "tags", "created_at" }
```
