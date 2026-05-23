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
| `clibo workout pr` | Personal records — heaviest weight per exercise |
| `clibo workout pr NAME` | One exercise: PR broken down by rep range (1RM / 3RM / 5RM …) |
| `clibo workout list --days 14` | Recent entries (`-e` filter by exercise) |
| `clibo workout show ENTRY` | One entry in detail (ID or exercise name) |
| `clibo workout rm ENTRY` | Delete (ID or exercise name → most-recent wins) |
| `clibo workout stats --days 30` | Sessions, volume, minutes, top exercises |

Volume = sets × reps × weight (kg).

## Natural language → command

| User says | Command |
|---|---|
| "Did 5×5 bench at 70kg" | `clibo workout log "bench press" -s 5 -r 5 -w 70` |
| "Ran 30 minutes" | `clibo workout log running -t 30` |
| "Hit a new bench-press PR of 90kg" | `clibo workout log "bench press" -s 1 -r 1 -w 90 -n PR` |
| "What's my bench-press PR?" | `clibo workout pr "bench press"` |
| "Show me all my PRs" | `clibo workout pr` |
| "What did I do today?" | `clibo workout today` |
| "Show only bench sessions" | `clibo workout list -e bench` |
| "Delete that last squat" | `clibo workout rm squat` |

## For agents

```bash
clibo workout pr --json
# -> [ { "exercise", "weight_kg", "reps", "sets", "entry_date", "when", "sessions" } ]

clibo workout pr "bench press" --json
# -> [ { "reps", "weight_kg", "sets", "entry_date", "when" } ]   one per rep-range

clibo workout stats --json
# -> { "sessions", "exercises_logged", "total_volume_kg", ... }
```

`pr` only counts rows with `reps>0` and `weight_kg>0` — cardio rows
are skipped. With a name argument, output is grouped by rep count
so lifters can read off their 1RM, 3RM, 5RM at a glance.
