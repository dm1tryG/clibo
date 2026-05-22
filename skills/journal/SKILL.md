---
name: clibo-journal
description: Keep a daily journal or diary with the `clibo journal` CLI. Use when the user wants to write a journal entry, review past entries, search their journal, or see their journaling streak.
---

# 📔 clibo journal

Daily journal & diary. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo journal write TEXT` | Write a journal entry |
| `clibo journal today` | Today's entries |
| `clibo journal list --days 14` | Recent entries (`-d` a single date) |
| `clibo journal show ID` | An entry's full text |
| `clibo journal edit ID -b TEXT` | Edit an entry |
| `clibo journal rm ID` | Delete an entry |
| `clibo journal search QUERY` | Search entries by text |
| `clibo journal stats` | Entries, days journaled, streak |

`write` and `edit` take `-m/--mood` (1–5) and `-t/--tag`. `write` takes
`-d/--date` to backdate an entry.

## Examples

```bash
clibo journal write "Today I shipped two new tools." -m 5 -t work
clibo journal today
clibo journal search "shipped"
clibo journal stats
```

## For agents

```bash
clibo journal stats --json
# -> { "total_entries", "days_journaled", "current_streak", "avg_mood" }
```

Each entry record includes the full `body` and a short `preview`.
