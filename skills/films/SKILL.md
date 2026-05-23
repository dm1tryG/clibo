---
name: clibo-films
description: Track movies & shows with the `clibo films` CLI. Use when the user mentions watching something, adding to a watchlist, or rating a film. Maps phrases like "I watched Dune, 5 stars" to `clibo films watched Dune -r 5`.
---

# 🎬 clibo films

Movie & show watchlist with ratings. Local SQLite. Every command
accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo films add TITLE -y YEAR -k movie\|show` | Add a film |
| `clibo films watched FILM -r RATING` | Mark watched with optional rating |
| `clibo films rate FILM RATING` | Set/change rating (1–5) |
| `clibo films list [-s STATUS] [-k KIND]` | List films |
| `clibo films rm ID` | Delete |
| `clibo films stats` | Watched count, avg rating, top-rated |

Statuses: `watchlist`, `watching`, `watched`, `dropped`.

## For agents

| User says | Command |
|---|---|
| "I watched Dune, gave it 5 stars" | `clibo films watched "Dune" -r 5` |
| "Add Oppenheimer to my watchlist" | `clibo films add "Oppenheimer" -y 2023` |
| "Started watching The Bear" | `clibo films add "The Bear" -k show -s watching` |
| "What's on my watchlist?" | `clibo films list -s watchlist` |

```bash
clibo films watched "Dune" -r 5 --json
# -> { "id", "title", "status": "watched", "rating": 5, "watched_on", ... }
```
