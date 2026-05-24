---
name: clibo-expense
description: Track personal spending with the `clibo expense` CLI. Use when the user wants to record an expense, review this month's spending by category, set the currency, or see expense stats.
---

# 💸 clibo expense

Personal expense tracker. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo expense add DESC -a AMOUNT -c CATEGORY` | Record an expense |
| `clibo expense list --days 30` | Recent expenses (`-c` filter category) |
| `clibo expense month [-m YYYY-MM]` | Spending by category for a month |
| `clibo expense year [-c CATEGORY]` | Annual breakdown; `-c food` scopes to one category |
| `clibo expense show ID` | One expense in detail |
| `clibo expense edit ID -a 15` | Edit an expense |
| `clibo expense rm ID` | Delete an expense |
| `clibo expense currency --set EUR` | Set the shared money currency |
| `clibo expense stats --days 30` | Total, average/day, top categories |

The currency is shared by all 💰 money tools (default `USD`).

## Examples

```bash
clibo expense add "coffee" -a 4.50 -c food
clibo expense add "metro" -a 2.50 -c transport
clibo expense month
clibo expense stats --days 30

# How much did I spend on food this year?
clibo expense year --category food
```

## For agents

```bash
clibo expense month --json
# -> { "month": "2026-05", "total": 68.7, "expenses": 3,
#      "by_category": [ {"category","amount","share"} ], "currency": "EUR" }
```
