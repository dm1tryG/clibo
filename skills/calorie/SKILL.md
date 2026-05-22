---
name: clibo-calorie
description: Track food, calories and macros with the `clibo calorie` CLI. Use when the user wants to log meals, see today's calorie intake, set a daily calorie goal, or review nutrition stats over time.
---

# 🍎 clibo calorie

Food & calorie tracker with macronutrients. Data lives in a local SQLite
database. Every command accepts `--json` for machine-readable output.

## Commands

| Command | What it does |
|---|---|
| `clibo calorie log FOOD -k KCAL` | Log a food item (also `-p` protein, `-c` carbs, `-f` fat, `-m` meal) |
| `clibo calorie today` | Today's food log with calorie & macro totals |
| `clibo calorie list --days 7` | Recent entries (or `--date`, `--meal`) |
| `clibo calorie show ID` | One entry in detail |
| `clibo calorie edit ID -k 200` | Change a logged entry |
| `clibo calorie rm ID` | Delete an entry |
| `clibo calorie goal --set 2000` | Set the daily calorie goal |
| `clibo calorie stats --days 7` | Average calories & macros |

`-m / --meal` is one of: `breakfast`, `lunch`, `dinner`, `snack`.

## Examples

```bash
clibo calorie log "oatmeal with berries" -k 320 -p 12 -c 48 -f 6 -m breakfast
clibo calorie log "black coffee" -k 5 -m breakfast
clibo calorie goal --set 2000
clibo calorie today
```

## For agents

```bash
clibo calorie today --json
# -> { "date": ..., "entries": [...], "totals": {kcal,protein,carbs,fat}, "goal_kcal": 2000 }
```

`log`/`edit` return the affected record as JSON; `rm` returns `{"deleted": ID}`.
Errors print to stderr and exit non-zero.
