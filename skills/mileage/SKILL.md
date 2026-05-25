---
name: clibo-mileage
description: Track distance-based activities (running, cycling, walking) with the `clibo mileage` CLI. Use when the user mentions kilometers/miles of movement — distinct from `workout` which is strength-focused. Maps "I ran 5km in 30 min" to `clibo mileage log 5 -a run -t 30`.
---

# 🏃 clibo mileage

Distance-based activity log — running, cycling, walking, hiking, swimming.
Distinct from `workout` (which is for strength/reps). Local SQLite. Every
command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo mileage log DISTANCE -a ACTIVITY -t MIN` | Log a session — `5`, `5km`, or `3.1mi` (miles auto-convert); duration accepts H:MM |
| `clibo mileage list --days 14 [-a ACTIVITY]` | Recent sessions |
| `clibo mileage week` | This week's distance vs the weekly goal |
| `clibo mileage goal --set 25` | Set weekly km goal (default 20) |
| `clibo mileage rm ID` | Delete a session |
| `clibo mileage stats --days 30` | Totals, avg pace, longest run, by activity |

Activities: `run`, `walk`, `cycle`, `hike`, `swim`, `other`.
Pace (`min/km`) is auto-computed when both km and minutes are given.

## For agents

| User says | Command |
|---|---|
| "I ran 5km this morning, took 30 minutes" | `clibo mileage log 5 -a run -t 30` |
| "Walked 2km" | `clibo mileage log 2 -a walk` |
| "Cycled 18km yesterday" | `clibo mileage log 18 -a cycle -d yesterday` |
| "How much did I run this week?" | `clibo mileage week` |

```bash
clibo mileage week --json
# -> { "week_start", "total_km", "goal_km", "reached",
#      "sessions", "by_activity": {"run": ..., "walk": ...} }
```
