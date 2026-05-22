---
name: clibo-debt
description: Track debts and loan payoff with the `clibo debt` CLI. Use when the user wants to register a debt, log a payment, check how much is left to pay, or review total debt.
---

# 📉 clibo debt

Debt & loan payoff tracker. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo debt add NAME -a AMOUNT` | Register a debt (`-c` creditor, `--apr`) |
| `clibo debt pay DEBT AMOUNT` | Log a payment toward a debt |
| `clibo debt list` | All debts with payoff progress bars |
| `clibo debt show DEBT` | A debt plus its payment history |
| `clibo debt rm ID` | Delete a debt |
| `clibo debt stats` | Total borrowed, paid and remaining |

`DEBT` accepts a debt name or numeric ID.

## Examples

```bash
clibo debt add "Car loan" -a 8000 -c "Bank" --apr 6.5
clibo debt pay "Car loan" 500
clibo debt list
clibo debt stats
```

## For agents

```bash
clibo debt list --json
# -> [ { "id", "name", "creditor", "principal", "paid",
#        "remaining", "progress_pct", "cleared", "apr" } ]
```

`pay` returns the updated debt with `cleared` set when fully paid off.
