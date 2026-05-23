---
name: clibo-dashboard
description: A customizable widget dashboard via `clibo dashboard`. Distinct from `clibo today` (which is a fixed 12-section snapshot) — this one lets the user pick which widgets show, in what order. Maps "show me my dashboard" to `clibo dashboard`, "add the sleep widget" to `clibo dashboard add sleep`.
---

# 🎛️ clibo dashboard

Customizable widget dashboard. Pick which widgets show; order matters.
Different from `clibo today` (fixed snapshot). Local SQLite. Every
command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo dashboard` | Render the current dashboard |
| `clibo dashboard list` | Every widget — registered + active state |
| `clibo dashboard add NAME` | Enable a widget |
| `clibo dashboard remove NAME` | Disable a widget |
| `clibo dashboard reset` | Restore the default widget set |
| `clibo dashboard clear` | Remove every widget |

## Available widgets

`tasks`, `habits`, `water`, `calories`, `focus`, `sleep`, `mood`,
`events`, `bills`, `followups`, `plants`, `chores`, `birthdays`,
`mileage`, `gratitude`, `weight`, `expense`, `income`.

Defaults: `tasks`, `habits`, `water`, `calories`, `focus`, `events`.

## For agents

| User says | Command |
|---|---|
| "Show me my dashboard" | `clibo dashboard` |
| "Add the sleep widget" | `clibo dashboard add sleep` |
| "Take off the calorie widget" | `clibo dashboard remove calories` |
| "What widgets are available?" | `clibo dashboard list` |
| "Start over with my dashboard" | `clibo dashboard reset` |

```bash
clibo dashboard --json
# -> { "date": "2026-05-23", "widgets": [
#       { "name": "tasks", "title": "✅ Tasks", "data": { … } },
#       ...
#     ] }
```
