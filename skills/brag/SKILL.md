---
name: clibo-brag
description: Keep a brag document of achievements with the `clibo brag` CLI. Use when the user wants to record an accomplishment, prepare for a performance review, or list what they've achieved since a date.
---

# 🏆 clibo brag

Achievement log ("brag document") for performance reviews. Local SQLite.
Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo brag add TITLE` | Log an achievement |
| `clibo brag list --days 90` | Recent achievements |
| `clibo brag show ID` | One achievement in detail |
| `clibo brag search QUERY` | Search title / description / impact |
| `clibo brag since DATE` | Achievements since a date (review prep) |
| `clibo brag rm ID` | Delete an achievement |
| `clibo brag stats` | Counts by category |

`add` takes `-D/--desc`, `-c/--category`, `-i/--impact`, `-t/--tag`,
`-d/--date`.

## Examples

```bash
clibo brag add "Shipped the new API" -i "Cut p95 latency by 40%" -c work
clibo brag since 2026-01-01
clibo brag search latency
```

## For agents

```bash
clibo brag since 2026-01-01 --json
# -> { "since", "count", "achievements": [ {"title","impact","category",...} ] }
```

The `since` command is ideal for assembling a performance-review summary.
