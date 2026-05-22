---
name: clibo-period
description: Track menstrual cycles with the `clibo period` CLI. Use when the user wants to log a period start or end, record a past period, predict the next period and fertile window, or review cycle statistics.
---

# 🌸 clibo period

Menstrual cycle tracker with predictions. Local SQLite. Every command
accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo period start` | Log a period start (`-d` date, `-f` flow, `-n` note) |
| `clibo period end` | Set the end date of the most recent period |
| `clibo period log -s START -e END` | Record a complete past period |
| `clibo period list` | List recent periods |
| `clibo period rm ID` | Delete an entry |
| `clibo period predict` | Predict next period & fertile window |
| `clibo period stats` | Average cycle & period length |

Flow is one of `light`, `medium`, `heavy`. Predictions use the average of
logged cycles, falling back to a 28-day cycle when history is thin.

## Examples

```bash
clibo period start -d today -f medium
clibo period end -d 2026-05-05
clibo period log -s 2026-04-01 -e 2026-04-05
clibo period predict
```

## For agents

```bash
clibo period predict --json
# -> { "last_start", "avg_cycle_days", "next_predicted_start",
#      "days_until_next", "estimated_ovulation",
#      "fertile_window_start", "fertile_window_end" }
```

Note: predictions are estimates, not medical advice.
