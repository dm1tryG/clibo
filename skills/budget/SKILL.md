---
name: clibo-budget
description: Manage monthly category budgets with the `clibo budget` CLI. Use when the user wants to set a spending limit for a category, check budget progress, or see whether they are over budget this month.
---

# 📊 clibo budget

Monthly budgets by category. Reads the 💸 `expense` tool's data to show
**live** spending against each budget. Local SQLite. Every command
accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo budget set CATEGORY AMOUNT` | Set/update a category's monthly limit |
| `clibo budget list` | All budgets with this month's spending |
| `clibo budget check CATEGORY` | One category's budget status |
| `clibo budget status` | Overall month summary |
| `clibo budget rm CATEGORY` | Delete a budget |

Spending is computed from expenses in the current calendar month, matched
by category — so budgets and `clibo expense` stay in sync automatically.

## Examples

```bash
clibo budget set food 400
clibo budget set transport 60
clibo expense add "groceries" -a 60 -c food
clibo budget list
clibo budget status
```

## For agents

```bash
clibo budget list --json
# -> { "month": "2026-05", "budgets": [
#      { "category", "limit", "spent", "remaining", "used_pct", "over_budget" } ] }
```
