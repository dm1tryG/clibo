---
name: clibo-savings
description: Track savings goals with the `clibo savings` CLI. Use when the user wants to create a savings goal, deposit money toward it, check progress, or review overall savings.
---

# 🐷 clibo savings

Savings goals with progress tracking. Local SQLite. Every command
accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo savings add NAME -t TARGET` | Create a savings goal |
| `clibo savings deposit GOAL AMOUNT` | Put money toward a goal |
| `clibo savings withdraw GOAL AMOUNT` | Take money back out |
| `clibo savings list` | All goals with progress bars |
| `clibo savings show GOAL` | A goal plus its deposit history |
| `clibo savings rm ID` | Delete a goal |
| `clibo savings stats` | Total saved vs total target |

`GOAL` accepts a goal name or numeric ID. `add` also takes `--deadline`.

## Examples

```bash
clibo savings add "Vacation" -t 1500 --deadline 2026-08-01
clibo savings deposit Vacation 200
clibo savings list
clibo savings show Vacation
```

## For agents

```bash
clibo savings list --json
# -> [ { "id", "name", "target", "saved", "remaining",
#        "progress_pct", "achieved", "deadline" } ]
```

`deposit`/`withdraw` return the updated goal with `achieved` set when the
target is reached.
