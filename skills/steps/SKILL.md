---
name: clibo-steps
description: Daily step-count tracker with the `clibo steps` CLI. Distinct from `workout` (exercise sessions), `mileage` (explicit cardio distance) and `stretches` (mobility). This is the passive daily total from a pedometer or fitness tracker. Maps "I did 8500 steps today" to `clibo steps log 8500`.
---

# 👟 clibo steps

Daily step-count tracker. Each log event records one chunk of steps; the
tool sums them per day. Use this for the passive daily total from your
Apple Watch / Fitbit / phone — *not* for explicit workouts (`workout`)
or runs (`mileage`).

## Commands

| Command | What it does |
|---|---|
| `clibo steps log COUNT [-s SOURCE] [-d DATE]` | Log a step count |
| `clibo steps add ...` | Alias for `log` |
| `clibo steps today` | Today's total + goal progress |
| `clibo steps list --days 14` | Daily totals |
| `clibo steps week` | This week per-day + streak |
| `clibo steps show ID` | One entry |
| `clibo steps rm ID` | Delete |
| `clibo steps goal --set N` | Show / set the daily goal (default 10,000) |
| `clibo steps stats --days 30` | Avg, hit-rate, best day, longest streak |

`SOURCE` is free text — useful values: `apple_watch`, `fitbit`, `garmin`,
`phone`, `manual`. Multiple logs in one day are summed, so you can sync
twice a day or mix sources without losing data.

## For agents

| User says | Command |
|---|---|
| "I did 8500 steps today" | `clibo steps log 8500` |
| "Apple Watch shows 12,400 steps today" | `clibo steps log 12400 -s apple_watch` |
| "Phone said I walked 3200 yesterday" | `clibo steps log 3200 -s phone -d yesterday` |
| "Set my step goal to 7000" | `clibo steps goal --set 7000` |
| "How am I doing on steps this week?" | `clibo steps week` |
| "What's my longest goal streak?" | `clibo steps stats` |

```bash
clibo steps stats --json
# -> { "window_days", "days_logged", "total_steps", "avg_per_logged_day",
#      "goal", "days_goal_hit", "goal_hit_rate_pct", "best_day",
#      "current_streak", "longest_streak" }
```
