---
name: clibo-gratitude
description: Track daily gratitude practice with the `clibo gratitude` CLI. Use when the user expresses thankfulness about something. Distinct from `journal` — short, dated entries with a streak. Maps "I'm grateful for X" to `clibo gratitude add "X"`.
---

# 🙏 clibo gratitude

Daily gratitude practice with streaks. Distinct from `journal`: short
dated entries (often 1–3 per day), tracked as a streak. Local SQLite.
Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo gratitude add TEXT` | Log one thing (also `-d` date) |
| `clibo gratitude today` | Today's entries + current streak |
| `clibo gratitude list --days 14` | Recent entries |
| `clibo gratitude streak` | Current and longest streaks |
| `clibo gratitude rm ID` | Delete an entry |
| `clibo gratitude stats --days 30` | Entries, days practised, streak |

## For agents

| User says | Command |
|---|---|
| "I'm grateful for sunshine today" | `clibo gratitude add "sunshine"` |
| "Grateful for my morning coffee" | `clibo gratitude add "morning coffee"` |
| "What's my gratitude streak?" | `clibo gratitude streak` |
| "What did I write down yesterday?" | `clibo gratitude list --days 2` |

Common compound: when a user lists multiple things, log each as its own
entry so the daily count and streak both stay meaningful.

```bash
clibo gratitude streak --json
# -> { "current_streak", "longest_streak", "days_practiced" }
```
