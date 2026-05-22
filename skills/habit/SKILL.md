---
name: clibo-habit
description: Track daily habits and streaks with the `clibo habit` CLI. Use when the user wants to add a habit, check it off, see streaks and weekly progress, or review which habits are done today.
---

# 🔥 clibo habit

Habit tracker with streaks. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo habit add NAME -t TARGET` | Create a habit (`-t` = target days/week) |
| `clibo habit check HABIT` | Mark a habit done (also `-d` date) |
| `clibo habit uncheck HABIT` | Remove a habit's check for a day |
| `clibo habit list` | All habits with streaks & weekly progress |
| `clibo habit today` | Which habits are done / pending today |
| `clibo habit rm ID` | Delete a habit and its history |
| `clibo habit stats HABIT` | Streaks and completion rate |

`HABIT` accepts a habit name or numeric ID. `check` is idempotent —
checking the same day twice is harmless.

## Examples

```bash
clibo habit add "Read 10 pages"
clibo habit add "Exercise" -t 5
clibo habit check "Read 10 pages"
clibo habit today
clibo habit stats "Read 10 pages"
```

## For agents

```bash
clibo habit list --json
# -> [ { "id", "name", "current_streak", "longest_streak",
#        "this_week", "target_per_week", "total_checks", "done_today" } ]
```
