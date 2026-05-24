---
name: clibo-todo
description: Manage tasks and to-dos with the `clibo todo` CLI. Use when the user mentions adding a task, marking one done, asking what's due today/tomorrow/overdue, or reviewing pending work. Date filters (`--due today`, `--overdue`, `--due-within N`) answer the natural "what do I have to do?" questions directly.
---

# ✅ clibo todo

Task & to-do manager. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo todo add TITLE -p PRIORITY [-d DATE]` | Add a task |
| `clibo todo list` | All pending tasks (priority desc, then due) |
| `clibo todo list --due DATE` | Tasks due on a specific date |
| `clibo todo list --overdue` | Pending tasks with due date in the past |
| `clibo todo list --due-within N` | Pending tasks due in the next N days (incl. overdue + today) |
| `clibo todo done ID` | Mark a task done |
| `clibo todo undone ID` | Reopen a task |
| `clibo todo snooze ID [-d N]` | Push due date forward by N days (default 1) |
| `clibo todo edit ID` | Edit a task |
| `clibo todo show ID` | One task in detail |
| `clibo todo rm ID` | Delete a task |
| `clibo todo stats` | Pending / done / overdue counts |

Priority is `low`, `med` or `high`. `add` also takes `-d/--due`,
`-P/--project` and `-t/--tag`. `list` filters compose:
`--due` / `--overdue` / `--due-within` AND `--project` AND `--tag`.

**Precedence**: when both `--due` and `--due-within` are passed,
`--due` wins. `--overdue` is mutually exclusive with the other two
(it's a strict "past-due only" filter).

`--due` accepts the same date forms as `add`:
`today` / `tomorrow` / `yesterday` / `next monday` / `2026-06-01`.

## Natural language → command

| User says | Command |
|---|---|
| "What do I have to do today?" | `clibo todo list --due today` |
| "What's due tomorrow?" | `clibo todo list --due tomorrow` |
| "Anything overdue?" | `clibo todo list --overdue` |
| "What's coming up this week?" | `clibo todo list --due-within 7` |
| "What's on the Acme project?" | `clibo todo list -P Acme` |
| "Show me everything tagged 'urgent'" | `clibo todo list -t urgent` |
| "Tasks for Acme due this week" | `clibo todo list -P Acme --due-within 7` |
| "Mark task 3 as done" | `clibo todo done 3` |

## For agents

```bash
clibo todo list --overdue --json
# -> [ { "id", "title", "priority", "due", "due_in", "overdue": true,
#        "done": false, "project", "tags" } ]

clibo todo list --due tomorrow --json
# -> same shape, filtered to due == tomorrow
```

Pending tasks are sorted overdue/high-priority first. The `overdue`
flag in each row is computed at read time so it's always current.
