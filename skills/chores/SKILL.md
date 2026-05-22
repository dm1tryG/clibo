---
name: clibo-chores
description: Track recurring household chores with the `clibo chores` CLI. Use when the user wants to add a chore, mark it done, see what chores are due, or manage a chore rotation.
---

# 🧹 clibo chores

Household chores rotation. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo chores add NAME -e DAYS` | Add a recurring chore |
| `clibo chores list` | All chores with next-due dates |
| `clibo chores done CHORE` | Mark a chore done today |
| `clibo chores due` | Chores that are due or overdue |
| `clibo chores rm ID` | Delete a chore |
| `clibo chores stats` | Chore counts |

`-e/--every` sets the repeat interval in days; `-a/--assignee` sets who
does it. `CHORE` accepts a chore name or ID. A chore's next-due date is
its last-done date plus the interval.

## Examples

```bash
clibo chores add "Vacuum" -e 7 -a Anna
clibo chores add "Take out trash" -e 3
clibo chores done "Vacuum"
clibo chores due
```

## For agents

```bash
clibo chores due --json
# -> [ { "id", "name", "assignee", "next_due", "due_in", "status" } ]
```

Status is `overdue`, `due` (today) or `upcoming`.
