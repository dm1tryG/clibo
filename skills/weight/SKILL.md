---
name: clibo-weight
description: Track body weight with the `clibo weight` CLI. Use when the user wants to log their weight, see BMI, or review weight trend and change over time.
---

# ⚖️ clibo weight

Body-weight log with BMI and trend analysis. Local SQLite. Every command
accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo weight log WEIGHT` | Log a weight — `70.5`, `70.5kg`, or `165lb` (lb auto-converts) |
| `clibo weight list --days 30` | Recent measurements |
| `clibo weight rm ID` | Delete a measurement |
| `clibo weight height --set 178` | Set height in cm (enables BMI) |
| `clibo weight stats --days 30` | Min/max/avg, change, trend and BMI |

## Examples

```bash
clibo weight height --set 178
clibo weight log 75.5
clibo weight log 74.8 -d yesterday
clibo weight log 165lb       # pounds auto-convert to kg
clibo weight stats --days 30
```

## For agents

```bash
clibo weight stats --json
# -> { "latest_kg", "min_kg", "max_kg", "avg_kg", "change_kg", "trend", "bmi", "bmi_class" }
```

`bmi`/`bmi_class` appear only once a height is set. `bmi_class` is one of
`underweight`, `normal`, `overweight`, `obese`.
