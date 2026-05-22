---
name: clibo-focus
description: Track pomodoro and focus sessions with the `clibo focus` CLI. Use when the user wants to run a pomodoro timer, log focus time, check today's focus against a goal, or review focus stats.
---

# 🍅 clibo focus

Pomodoro & focus-session tracker. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo focus timer -m 25 -t TASK` | Run a live pomodoro timer, then log it |
| `clibo focus log MINUTES -t TASK` | Log an already-completed session |
| `clibo focus today` | Today's focus time vs the daily goal |
| `clibo focus list --days 7` | Recent focus sessions |
| `clibo focus rm ID` | Delete a session |
| `clibo focus goal --set 120` | Set the daily focus-minutes goal |
| `clibo focus stats --days 7` | Sessions, total time, averages |

A pomodoro defaults to 25 minutes; the daily goal defaults to 100 minutes.
With `--json`, `timer` skips the live countdown and just logs the session.

## Examples

```bash
clibo focus timer -m 25 -t "write report"
clibo focus log 50 -t "deep work"
clibo focus today
clibo focus stats --days 7
```

## For agents

```bash
clibo focus today --json
# -> { "date", "sessions", "total_minutes", "goal_minutes", "reached" }
```

Agents should use `clibo focus log` rather than the interactive `timer`.
