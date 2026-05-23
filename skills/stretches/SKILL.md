---
name: clibo-stretches
description: Log mobility & flexibility sessions with the `clibo stretches` CLI. Distinct from `workout` (strength), `mileage` (running) and `meditate` (mindfulness). Captures body area, duration in minutes, optional poses and an optional 1-5 difficulty rating. Maps "I stretched my hamstrings for 10 minutes" to `clibo stretches log hamstrings -m 10`.
---

# 🧎 clibo stretches

A mobility / flexibility session log. Use this when the user did
stretching, mobility work or yoga-style flexibility — *not* a full
strength workout (`workout`), a run (`mileage`) or a meditation
session (`meditate`).

## Commands

| Command | What it does |
|---|---|
| `clibo stretches log AREA -m MIN -p POSES -D 1-5 -n NOTE` | Log a session |
| `clibo stretches add ...` | Alias for `log` |
| `clibo stretches today` | Today's sessions |
| `clibo stretches list --days 14 [--area X]` | Recent sessions |
| `clibo stretches show ID` | One session |
| `clibo stretches rm ID` | Delete |
| `clibo stretches areas --days 30` | Frequency table — which areas you neglect |
| `clibo stretches stats --days 30` | Sessions, total minutes, avg difficulty, top area |

`AREA` defaults to `full-body`. Suggested vocabulary (anything works):
`hamstrings`, `quads`, `hips`, `back`, `lower-back`, `shoulders`,
`neck`, `chest`, `calves`, `ankles`, `wrists`, `full-body`.

## For agents

| User says | Command |
|---|---|
| "I stretched my hamstrings for 10 minutes" | `clibo stretches log hamstrings -m 10` |
| "Did 15 min of hip mobility, super deep" | `clibo stretches log hips -m 15 -D 5` |
| "Quick 5-min neck stretches at my desk" | `clibo stretches log neck -m 5` |
| "Did pigeon and downward-dog for 20 min" | `clibo stretches log full-body -m 20 -p "pigeon, downward-dog"` |
| "Which areas am I neglecting?" | `clibo stretches areas --days 30` |

```bash
clibo stretches stats --json
# -> { "window_days", "sessions", "days_logged", "total_minutes",
#      "avg_minutes_per_session", "avg_difficulty", "top_area",
#      "by_area_minutes": {area: minutes, ...} }
```
