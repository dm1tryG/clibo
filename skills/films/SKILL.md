---
name: clibo-films
description: Track movies & shows with the `clibo films` CLI, including season/episode progress for TV shows. Use when the user mentions watching something, adding to a watchlist, rating, or saying which episode they're on.
---

# 🎬 clibo films

Movie & show watchlist with ratings. Local SQLite. Every command
accepts `--json`. For TV shows, the tool also tracks the
**last-watched episode** as a single pointer (S/E) — no per-episode log.

## Commands

| Command | What it does |
|---|---|
| `clibo films add TITLE -y YEAR -k movie\|show [-S N -E N]` | Add a film/show |
| `clibo films progress FILM -S N -E N` | Set season/episode pointer |
| `clibo films progress FILM --bump` | Increment episode by 1 |
| `clibo films watched FILM -r RATING` | Mark watched with optional rating |
| `clibo films rate FILM RATING` | Set/change rating (1–5) |
| `clibo films show FILM` | Show one film with progress |
| `clibo films edit FILM [...]` | Edit any field |
| `clibo films list [-s STATUS] [-k KIND]` | List films |
| `clibo films rm FILM` | Delete (accepts title or ID) |
| `clibo films stats` | Watched count, avg rating, top-rated |

Statuses: `watchlist`, `watching`, `watched`, `dropped`.
`FILM` is **title or ID** everywhere (fuzzy title match, exact wins
over substring).

## Natural language → command

| User says | Command |
|---|---|
| "Watching Better Call Saul S6E5" | `clibo films add "Better Call Saul" -k show -S 6 -E 5` |
| "Just finished another BCS episode" | `clibo films progress "Better Call Saul" --bump` |
| "I'm on episode 10 of season 6 now" | `clibo films progress "Better Call Saul" -S 6 -E 10` |
| "Where was I in The Bear?" | `clibo films show "The Bear"` |
| "I watched Dune, 5 stars" | `clibo films watched "Dune" -r 5` |
| "Add Oppenheimer to my watchlist" | `clibo films add "Oppenheimer" -y 2023` |
| "Dropping Westworld" | `clibo films edit "Westworld" -s dropped` |
| "What shows am I watching?" | `clibo films list -s watching -k show` |

## For agents

```bash
clibo films progress "Better Call Saul" -S 6 -E 5 --json
# -> { "season": 6, "episode": 5, "progress": "S06E05", "status": "watching", ... }

clibo films show "Better Call Saul" --json
# -> { ..., "progress": "S06E10" }
```

Setting `--season` or `--episode` on an `add` for `-k show` auto-bumps
the status from `watchlist` to `watching` — if the user is tracking
progress they're already watching it.
