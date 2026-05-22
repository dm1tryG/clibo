---
name: clibo-network
description: Log people you meet while networking with the `clibo network` CLI. Use when the user wants to record someone they met, recall where and when, or search their networking contacts.
---

# 🌐 clibo network

Networking & people-you-met log. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo network add NAME` | Log someone you met (`-w` where, `-c` context) |
| `clibo network list --days 90` | People you've met recently |
| `clibo network show ID` | One connection in detail |
| `clibo network search QUERY` | Search name / company / place / context |
| `clibo network rm ID` | Delete a connection |
| `clibo network stats` | Totals and your top meeting places |

`add` also takes `--company`, `-d/--date` and `-n/--note`.

## Examples

```bash
clibo network add "Sam Lee" -w "PyCon 2026" -c "talked about CLIs" --company Acme
clibo network search pycon
clibo network stats
```

## For agents

```bash
clibo network list --json
# -> [ { "id", "name", "company", "met_where", "context",
#        "met_date", "met_ago" } ]
```
