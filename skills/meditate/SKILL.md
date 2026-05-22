---
name: clibo-meditate
description: Track meditation and mindfulness sessions with the `clibo meditate` CLI. Use when the user wants to log a meditation session, check today's progress toward a goal, see their streak, or review meditation stats.
---

# 🧘 clibo meditate

Meditation & mindfulness session tracker. Local SQLite. Every command
accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo meditate log MIN -k KIND` | Log a session (`-k` e.g. breathing, guided) |
| `clibo meditate today` | Today's minutes vs the daily goal |
| `clibo meditate list --days 14` | Recent sessions |
| `clibo meditate rm ID` | Delete a session |
| `clibo meditate goal --set 10` | Set the daily minutes goal |
| `clibo meditate streak` | Current consecutive-day streak |
| `clibo meditate stats --days 30` | Sessions, minutes, streak |

Default daily goal is 10 minutes.

## Examples

```bash
clibo meditate log 10 -k breathing
clibo meditate goal --set 15
clibo meditate today
clibo meditate streak
```

## For agents

```bash
clibo meditate stats --json
# -> { "sessions", "days_practised", "total_minutes",
#      "avg_minutes_per_session", "longest_session", "current_streak" }
```
