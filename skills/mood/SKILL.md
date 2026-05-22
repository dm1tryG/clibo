---
name: clibo-mood
description: Track daily mood and emotions with the `clibo mood` CLI. Use when the user wants to log how they feel, review today's mood, or see mood trends, distribution and common emotions over time.
---

# 🙂 clibo mood

Daily mood & emotion journal. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo mood log SCORE` | Log how you feel (score 1–5) |
| `clibo mood today` | Today's check-ins and average |
| `clibo mood list --days 14` | Recent check-ins |
| `clibo mood rm ID` | Delete a check-in |
| `clibo mood stats --days 30` | Average, distribution, top emotions |

Score: 1 😞 awful · 2 🙁 low · 3 😐 okay · 4 🙂 good · 5 😄 great.
`log` also takes `-e/--emotion` (a word like `calm`), `-n/--note`, `-d/--date`.

## Examples

```bash
clibo mood log 4 -e calm -n "productive day"
clibo mood log 2 -e stressed
clibo mood today
clibo mood stats --days 30
```

## For agents

```bash
clibo mood stats --json
# -> { "checkins", "avg_score", "best_score", "worst_score",
#      "distribution": {face: count}, "top_emotions": [...] }
```

`log` returns the created entry incl. `face` and `label`.
