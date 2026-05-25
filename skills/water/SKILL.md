---
name: clibo-water
description: Track daily water intake with the `clibo water` CLI. Use when the user wants to log drinking water, check hydration progress toward a daily goal, or review intake history.
---

# 💧 clibo water

Daily water intake tracker. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo water drink [AMOUNT]` | Log a drink — `500`, `500ml`, `16oz`, or `1L` (default 250 ml); oz and L auto-convert |
| `clibo water today` | Today's total and a goal-progress bar |
| `clibo water list --days 7` | Daily totals for the last N days |
| `clibo water rm ID` | Delete a log entry |
| `clibo water goal --set 2500` | Set the daily water goal (ml) |
| `clibo water stats --days 7` | Averages and days the goal was reached |

Default daily goal is 2000 ml until changed.

## Examples

```bash
clibo water drink 500
clibo water drink            # logs a 250 ml glass
clibo water today
clibo water goal --set 2500
```

## For agents

```bash
clibo water today --json
# -> { "date": ..., "total_ml": 750, "goal_ml": 2000, "drinks": 2, "reached": false }
```

`drink` returns `{"id", "amount_ml", "total_today", "goal_ml"}`.
