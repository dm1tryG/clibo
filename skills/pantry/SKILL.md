---
name: clibo-pantry
description: Track a food inventory with expiry dates using the `clibo pantry` CLI. Use when the user wants to record what food they have, where it's stored, or see what's expiring soon.
---

# 🥫 clibo pantry

Food inventory with expiry dates. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo pantry add NAME` | Add an item (`-e` expiry, `-l` location, `-q` qty) |
| `clibo pantry list [-l LOCATION]` | List pantry items |
| `clibo pantry expiring --days 7` | Items expired or expiring soon |
| `clibo pantry show ID` | One item in detail |
| `clibo pantry rm ID` | Remove an item (used up / discarded) |
| `clibo pantry stats` | Counts, expired and expiring |

Location is free text (typically `pantry`, `fridge`, `freezer`). Each item
gets a status: `fresh`, `expiring` (≤3 days), `expired`, or `none`.

## Examples

```bash
clibo pantry add "olive oil" -l pantry -q "1 bottle"
clibo pantry add yogurt -l fridge -e 2026-06-01
clibo pantry expiring --days 7
```

## For agents

```bash
clibo pantry expiring --json
# -> [ { "id", "name", "location", "expiry", "expiry_in", "status" } ]
```
