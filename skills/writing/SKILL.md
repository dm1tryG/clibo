---
name: clibo-writing
description: Daily word-count tracker for writers — novel/blog/essay sessions, per-project totals, daily goal, streak. Use when the user mentions writing N words, wanting to track word counts, or NaNoWriMo-style daily goals. Distinct from `journal` (which is content) and `time` (which is generic minutes).
---

# ✍️ clibo writing

Daily word-count tracker. Logs one row per writing session, grouped
by project (`novel`, `blog`, `essay`, …) with a daily word goal and
consecutive-day streak. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo writing log PROJECT -w WORDS [-t MIN]` | Log a session |
| `clibo writing today` | Today's total by project, goal progress, streak |
| `clibo writing goal N` | Set daily word goal (default 500) |
| `clibo writing streak` | Current + longest streak |
| `clibo writing list -p PROJECT --days N` | Recent sessions |
| `clibo writing show ENTRY` | One entry (ID or project name) |
| `clibo writing edit ENTRY [...]` | Update an entry |
| `clibo writing rm ENTRY` | Delete |
| `clibo writing stats --days N` | Totals, avg wpm, best day, top projects |

Pace (`wpm`) is auto-computed when both `--words` and `--duration`
are set. `PROJECT` defaults to `main` if omitted.

## Natural language → command

| User says | Command |
|---|---|
| "Wrote 1200 words on the novel in 45 min" | `clibo writing log novel -w 1200 -t 45` |
| "Just wrote 400 words" | `clibo writing log -w 400` |
| "Set my goal to NaNoWriMo daily (1667)" | `clibo writing goal 1667` |
| "How much did I write today?" | `clibo writing today` |
| "What's my writing streak?" | `clibo writing streak` |
| "Show last week of writing" | `clibo writing list --days 7` |
| "Bump my last novel session to 1300 words" | `clibo writing edit novel -w 1300` |
| "Delete my last blog session" | `clibo writing rm blog` |
| "What's my best day ever?" | `clibo writing stats --days 365` (see `best_day`) |

## For agents

```bash
clibo writing log novel -w 1200 -t 45 --json
# -> { "id", "project", "words": 1200, "duration_min": 45, "wpm": 26.7,
#      "total_today": 1200, "goal_words": 500, "current_streak": 1, ... }

clibo writing today --json
# -> { "total_words", "goal_words", "reached", "sessions",
#      "by_project": [{"project","words"}], "current_streak" }

clibo writing stats --json
# -> { "total_words", "avg_wpm", "best_day", "top_projects", "current_streak" }
```

`log` returns `total_today` and `current_streak` in one call so agents
don't need a second round-trip to confirm "you hit your goal" or
"you're on day N".
