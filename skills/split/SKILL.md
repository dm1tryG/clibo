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
| `clibo split list` | All shared expenses |
| `clibo split rm ID` | Delete a shared expense |
| `clibo split balances` | Each person's net balance |
| `clibo split settle FROM TO AMOUNT` | Record a settle-up payment |
| `clibo split who` | Fewest payments to settle everyone up |

`-w/--with` is a comma-separated list of everyone sharing the cost (the
expense is split equally among them). A positive balance means a person is
owed money; negative means they owe.

## Examples

```bash
clibo split add "Dinner" -a 90 -b Alice -w "Alice,Bob,Carol"
clibo split add "Taxi" -a 30 -b Bob -w "Alice,Bob,Carol"
clibo split balances
clibo split who
clibo split settle Carol Alice 40
```

## For agents

```bash
clibo split who --json
# -> { "transactions": [ {"from": "Carol", "to": "Alice", "amount": 40.0} ] }

clibo split balances --json
# -> [ {"person", "balance", "status"} ]   status: is owed / owes / settled
```
