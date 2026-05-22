---
name: clibo-todo
description: Manage tasks and to-dos with the `clibo todo` CLI. Use when the user wants to add a task, mark one done, list pending work by priority, or review task stats.
---

# ✅ clibo todo

Task & to-do manager. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo todo add TITLE -p PRIORITY` | Add a task |
| `clibo todo list [--all]` | List tasks (pending first, by priority) |
| `clibo todo done ID` | Mark a task done |
| `clibo todo undone ID` | Reopen a task |
| `clibo todo edit ID` | Edit a task |
| `clibo todo show ID` | One task in detail |
| `clibo todo rm ID` | Delete a task |
| `clibo todo stats` | Pending / done / overdue counts |

Priority is `low`, `med` or `high`. `add` also takes `-d/--due`,
`-P/--project` and `-t/--tag`. `list` filters with `--project`/`--tag`.

## Examples

```bash
clibo todo add "Ship clibo v1" -p high -d 2026-06-01 -P clibo
clibo todo add "Buy groceries" -p med
clibo todo list
clibo todo done 2
```

## For agents

```bash
clibo todo list --json
# -> [ { "id", "title", "priority", "due", "due_in", "overdue",
#        "done", "project", "tags" } ]
```

Pending tasks are sorted overdue/high-priority first.
