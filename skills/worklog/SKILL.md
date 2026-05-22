---
name: clibo-worklog
description: Keep a work log and generate standups with the `clibo worklog` CLI. Use when the user wants to log what they worked on, review recent work, or produce a standup of yesterday's done / today's plan / blockers.
---

# 🗒️ clibo worklog

Work log & standup notes. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo worklog add SUMMARY -k KIND` | Add a work-log entry |
| `clibo worklog today` | Today's entries |
| `clibo worklog list --days 7` | Recent entries (`-P` filter project) |
| `clibo worklog standup` | Standup: yesterday done / today / blockers |
| `clibo worklog rm ID` | Delete an entry |
| `clibo worklog stats --days 7` | Entry counts by kind |

`-k/--kind` is `done`, `doing`, `blocked` or `note` (default `done`).

## Examples

```bash
clibo worklog add "Shipped the new parser" -k done
clibo worklog add "Reviewing PRs" -k doing
clibo worklog add "Waiting on design" -k blocked
clibo worklog standup
```

## For agents

```bash
clibo worklog standup --json
# -> { "date", "yesterday_done": [...], "today_doing": [...], "blockers": [...] }
```
