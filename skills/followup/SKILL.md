---
name: clibo-followup
description: Track follow-up reminders for people with the `clibo followup` CLI. Use when the user wants to remember to get back to someone, see who they owe a follow-up, or snooze a reminder.
---

# 🔔 clibo followup

Follow-up reminders for people. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo followup add PERSON -d DUE` | Add a follow-up (`-r` reason) |
| `clibo followup list [--all]` | Pending (or all) follow-ups |
| `clibo followup done ID` | Mark a follow-up done |
| `clibo followup due --days 7` | Overdue + due-soon follow-ups |
| `clibo followup snooze ID --days 7` | Push the due date later |
| `clibo followup rm ID` | Delete a follow-up |
| `clibo followup stats` | Pending and overdue counts |

Each follow-up has a status: `done`, `overdue`, `due soon` (≤2 days) or
`upcoming`.

## Examples

```bash
clibo followup add "Anna Petrova" -d 2026-06-01 -r "send the contract"
clibo followup due --days 7
clibo followup snooze 1 --days 3
clibo followup done 1
```

## For agents

```bash
clibo followup due --json
# -> [ { "id", "person", "reason", "due_date", "due_in",
#        "days_until_due", "status" } ]
```
