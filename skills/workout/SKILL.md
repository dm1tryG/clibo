---
name: clibo-workout
description: Log exercise and gym sessions with the `clibo workout` CLI. Use when the user wants to record strength training (sets/reps/weight) or cardio, or review workout volume and stats.
---

# 🏋️ clibo workout

Exercise & gym session log. Handles both strength (sets/reps/weight) and
cardio (minutes). Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo workout log NAME -s S -r R -w KG` | Log a strength exercise |
| `clibo workout log NAME -t MIN` | Log a cardio session (minutes) |
| `clibo workout today` | Today's exercises with total volume |
| `clibo workout list --days 14` | Recent entries (`-e` filter by exercise) |
| `clibo workout show ID` | One entry in detail |
| `clibo workout rm ID` | Delete an entry |
| `clibo workout stats --days 30` | Sessions, volume, minutes, top exercises |

Volume = sets × reps × weight (kg).

## Examples

```bash
clibo workout log "bench press" -s 5 -r 5 -w 70
clibo workout log "running" -t 30
clibo workout today
clibo workout stats --days 30
```

## For agents

```bash
clibo workout stats --json
# -> { "sessions", "exercises_logged", "total_volume_kg", "total_minutes", "top_exercises": [...] }
```

`log` returns the created entry including its computed `volume_kg`.
