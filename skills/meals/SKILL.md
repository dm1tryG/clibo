---
name: clibo-meals
description: Plan meals for the week with the `clibo meals` CLI. Use when the user wants to plan what to eat on a given day, see today's meals, or view the week's meal grid.
---

# 🍽️ clibo meals

Weekly meal planner. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo meals plan DATE MEAL DISH` | Plan a meal for a day |
| `clibo meals today` | Today's planned meals |
| `clibo meals week` | The week's plan as a grid |
| `clibo meals list --days 7` | Planned meals around today |
| `clibo meals rm ID` | Delete a planned meal |
| `clibo meals clear DATE` | Clear all meals for a day |
| `clibo meals stats` | Meal-planning stats |

`MEAL` is `breakfast`, `lunch`, `dinner` or `snack`. Dates accept
`today`, `tomorrow` or `YYYY-MM-DD`.

## Examples

```bash
clibo meals plan today dinner "Pasta carbonara"
clibo meals plan tomorrow lunch "Greek salad"
clibo meals week
```

## For agents

```bash
clibo meals week --json
# -> { "week_start": "2026-05-18",
#      "days": [ {"date", "breakfast", "lunch", "dinner"} ] }
```
