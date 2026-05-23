---
name: clibo-fasting
description: Intermittent fasting tracker via `clibo fasting`. The killer view is `fasting status` — a running clock against your target window. Distinct from `calorie` (food), `water` (hydration), `sleep`. Maps "I'm starting a 16-hour fast" to `clibo fasting start --target 16`.
---

# 🕒 clibo fasting

A fast is a *time window*. Start one with `fasting start`, end it with
`fasting stop`. Between those, `fasting status` shows a running clock —
how much elapsed, how much remaining against your target.

Distinct from `calorie` (food / kcal intake), `water` (hydration timing,
not a window), `sleep` (overnight, not arbitrary hours).

## Commands

| Command | What it does |
|---|---|
| `clibo fasting start [-T HOURS] [-t HH:MM] [-n NOTE]` | Begin a fast |
| `clibo fasting stop [-t HH:MM] [-n NOTE]` | End the current fast |
| `clibo fasting status` | Are you fasting now? running clock against target |
| `clibo fasting list [--days N] [--completed]` | Recent fasts |
| `clibo fasting show ID` | One fast |
| `clibo fasting rm ID` | Delete |
| `clibo fasting target --set HOURS` | Show / set default target (16h) |
| `clibo fasting stats [--days N]` | Count, avg duration, longest, target-hit rate |

Only one fast can be in progress at a time — `start` refuses to begin a
second one. `stop` time defaults to *now*; pass `-t HH:MM` to backfill.

## For agents

| User says | Command |
|---|---|
| "Starting a 16-hour fast" | `clibo fasting start --target 16` |
| "Started fasting at 8pm last night" | `clibo fasting start -t 20:00 -d yesterday` |
| "Done — broke my fast" | `clibo fasting stop` |
| "I broke my fast at noon" | `clibo fasting stop -t 12:00` |
| "Am I still fasting?" / "How much longer?" | `clibo fasting status` |
| "Make 18 hours my default target" | `clibo fasting target --set 18` |
| "How am I doing on fasts this month?" | `clibo fasting stats` |

```bash
clibo fasting status --json
# while fasting: { "id", "start_time", "end_time": null, "target_hours",
#                  "duration_hours", "ongoing": true, "remaining_hours",
#                  "reached_target": bool, "note" }
# while not   : { "ongoing": false, "last": { ... last completed fast ... } }
```
