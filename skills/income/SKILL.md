---
name: clibo-income
description: Track money coming in with the `clibo income` CLI. Counterpart to `expense` (which is outgoings). Use when the user receives a salary, freelance payment, refund, gift or any other income. Maps "I got 500 from a freelance gig" to `clibo income add "gig" -a 500 -c freelance`.
---

# 💵 clibo income

Income tracker — the counterpart to `expense`. Local SQLite. Every
command accepts `--json`. Uses the same shared `money/currency` setting.

## Commands

| Command | What it does |
|---|---|
| `clibo income add SOURCE -a AMOUNT -c CATEGORY` | Log an income event |
| `clibo income list --days 30 [-c CATEGORY]` | Recent income |
| `clibo income month [-m YYYY-MM]` | This month's breakdown by category |
| `clibo income year [-c CATEGORY] [-s SOURCE]` | Annual breakdown; filter to one category or source |
| `clibo income show ID` | Detail |
| `clibo income edit ID` | Edit an entry |
| `clibo income rm ID` | Delete |
| `clibo income stats --days 30` | Totals, top categories |

Common categories: `salary`, `freelance`, `gift`, `refund`, `dividend`,
`other`. Anything is fine — the field is free text.

## For agents

| User says | Command |
|---|---|
| "Got 500 USD from a freelance gig" | `clibo income add "freelance gig" -a 500 -c freelance` |
| "Salary landed today, 3200" | `clibo income add "salary" -a 3200 -c salary` |
| "Mom sent me 100 for my birthday" | `clibo income add "Mom — birthday" -a 100 -c gift` |
| "Refund from Amazon, 23.50" | `clibo income add "Amazon refund" -a 23.50 -c refund` |
| "What did I earn this month?" | `clibo income month` |
| "How much salary did I get this year?" | `clibo income year -c salary` |
| "How much did Acme pay me this year?" | `clibo income year -s acme` |

```bash
clibo income month --json
# -> { "month": "2026-05", "total": 3700.0, "entries": 3,
#      "by_category": [ {"category", "amount", "share"} ], "currency": "USD" }
```
