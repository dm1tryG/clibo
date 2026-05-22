---
name: clibo-bills
description: Track bills and due dates with the `clibo bills` CLI. Use when the user wants to add a bill, mark one paid, see what's overdue or due soon, or review unpaid totals.
---

# 🧾 clibo bills

Bills & due-date reminders. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo bills add NAME -d DUE -a AMOUNT` | Add a bill with a due date |
| `clibo bills list [--all]` | Unpaid (or all) bills, soonest first |
| `clibo bills pay ID` | Mark a bill paid |
| `clibo bills unpay ID` | Mark a bill unpaid again |
| `clibo bills rm ID` | Delete a bill |
| `clibo bills due --days 7` | Overdue + due-soon bills |
| `clibo bills stats` | Unpaid total and overdue count |

Each bill gets a status: `paid`, `overdue`, `due soon` (≤3 days) or
`upcoming`.

## Examples

```bash
clibo bills add "Electricity" -d 2026-06-01 -a 65 -c utilities
clibo bills due --days 7
clibo bills pay 1
```

## For agents

```bash
clibo bills due --json
# -> [ { "id", "name", "amount", "due_date", "status",
#        "days_until_due", "due_in" } ]
```

`stats` returns `unpaid`, `overdue`, `unpaid_amount`, `overdue_amount`.
