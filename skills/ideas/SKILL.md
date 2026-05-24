---
name: clibo-ideas
description: Capture ideas with a lifecycle (raw → exploring → validated → shipped/abandoned) using the `clibo ideas` CLI. Use when the user expresses an idea, side-project thought, or a "what if". Distinct from `notes` (free-form) and `goals` (already-committed). Maps "Idea: build a marketplace" to `clibo ideas add "build a marketplace"`.
---

# 💡 clibo ideas

Idea capture with a status lifecycle. Distinct from `notes` (free-form,
no lifecycle) and `goals` (already-committed, with milestones). Local
SQLite. Every command accepts `--json`.

## Statuses

`raw` → just captured · `exploring` → actively thinking · `validated` →
confirmed worth pursuing · `shipped` → built/done · `abandoned` → dropped.

## Commands

| Command | What it does |
|---|---|
| `clibo ideas add TITLE -D DESC -t TAGS` | Capture an idea |
| `clibo ideas list [-s STATUS] [--open]` | List ideas (`--open` excludes shipped & abandoned) |
| `clibo ideas show ID` | Show one idea |
| `clibo ideas move ID STATUS` | Move through the lifecycle |
| `clibo ideas edit ID` | Edit title/desc/tags |
| `clibo ideas search QUERY` | Search title/desc/tags |
| `clibo ideas rm ID` | Delete |
| `clibo ideas stale [-d N]` | Open ideas not touched in N days (default 30) |
| `clibo ideas pipeline` | Counts by status |
| `clibo ideas stats` | Open / shipped / abandoned summary |

## For agents

| User says | Command |
|---|---|
| "Idea: build a clibo plugin marketplace" | `clibo ideas add "clibo plugin marketplace"` |
| "Thinking about adding tags to ideas" | `clibo ideas add "tags on ideas" -s exploring` |
| "I shipped the new pomodoro mode" | `clibo ideas move <id> shipped` |
| "Decided not to pursue the side project" | `clibo ideas move <id> abandoned` |
| "What ideas am I exploring?" | `clibo ideas list -s exploring` |
| "What have I been sitting on?" | `clibo ideas stale` |

```bash
clibo ideas pipeline --json
# -> { "by_status": {"raw": 5, "exploring": 2, "validated": 1, ...}, "total": 10 }
```
