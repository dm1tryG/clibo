---
name: clibo-home
description: Track home maintenance and repairs with the `clibo home` CLI. Use when the user wants to log a fix, paint job, or improvement at home, or review home-spending stats.
---

# 🏠 clibo home

Home maintenance & repairs. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo home add TITLE` | Log a home entry |
| `clibo home list [-k KIND]` | List entries (`-l` location filter) |
| `clibo home show ID` | One entry in detail |
| `clibo home rm ID` | Delete an entry |
| `clibo home stats` | Total spending, by kind and by location |

`-k/--kind` is `maintenance`, `repair` or `improvement`. `add` also
takes `-c/--cost`, `-l/--location`, `--contractor`, `-d/--date`,
`-n/--note`.

## Examples

```bash
clibo home add "Painted bedroom" -k improvement -c 230 -l bedroom
clibo home add "Fixed kitchen leak" -k repair -c 120 -l kitchen --contractor "ABC Plumbing"
clibo home stats
```

## For agents

```bash
clibo home stats --json
# -> { "total_entries", "total_spent",
#      "by_kind": {...}, "by_location": {...}, "currency" }
```
