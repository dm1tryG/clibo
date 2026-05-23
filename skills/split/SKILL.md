---
name: clibo-split
description: Split shared expenses between people with the `clibo split` CLI. Use when the user wants to record a group expense, see who owes whom, settle up, or get the minimal set of payments to balance everyone.
---

# 🤝 clibo split

Split shared expenses with people. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo split add DESC -a AMOUNT -b PAYER -w PEOPLE` | Log a shared expense |
| `clibo split owe PERSON AMOUNT` | Quick IOU: **I owe** PERSON |
| `clibo split lent PERSON AMOUNT` | Quick IOU: PERSON **owes me** (I lent them) |
| `clibo split list` | All shared expenses |
| `clibo split rm ID` | Delete a shared expense |
| `clibo split balances` | Each person's net balance |
| `clibo split settle FROM TO AMOUNT` | Record a settle-up payment |
| `clibo split who` | Fewest payments to settle everyone up |

`-w/--with` is a comma-separated list of everyone sharing the cost (the
expense is split equally among them). A positive balance means a person is
owed money; negative means they owe.

**`owe` and `lent`** are direct IOU shortcuts — use these when the user
says "I owe X $Y" or "Bob owes me $Z" without modeling a full bill.
Both default the ledger name to "me"; override with `--me NAME`.

## Natural language → command

| User says | Command |
|---|---|
| "I owe Anna $50 for dinner" | `clibo split owe Anna 50 --for dinner` |
| "Bob owes me $20" | `clibo split lent Bob 20` |
| "We split a $90 dinner three ways, Alice paid" | `clibo split add "dinner" -a 90 -b Alice -w "Alice,Bob,me"` |
| "I just paid Anna back the $50" | `clibo split settle me Anna 50` |
| "How much do I owe in total?" | `clibo split balances` |
| "What's the simplest way to settle up?" | `clibo split who` |

## Examples

```bash
clibo split add "Dinner" -a 90 -b Alice -w "Alice,Bob,Carol"
clibo split owe Anna 50 --for dinner
clibo split lent Bob 20 --for coffee
clibo split balances
clibo split who
clibo split settle me Anna 50
```

## For agents

```bash
clibo split who --json
# -> { "transactions": [ {"from": "Carol", "to": "Alice", "amount": 40.0} ] }

clibo split balances --json
# -> [ {"person", "balance", "status"} ]   status: is owed / owes / settled
```
