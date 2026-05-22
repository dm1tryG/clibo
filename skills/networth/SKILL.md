---
name: clibo-networth
description: Track assets, liabilities and net worth with the `clibo networth` CLI. Use when the user wants to add an asset or liability, see their current net worth, or track net worth over time with snapshots.
---

# 💰 clibo networth

Assets, liabilities & net-worth tracker. Local SQLite. Every command
accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo networth add NAME -a VALUE -t TYPE` | Add an asset or liability |
| `clibo networth list [-t TYPE]` | List items (filter by type) |
| `clibo networth update ID VALUE` | Update an item's current value |
| `clibo networth rm ID` | Delete an item |
| `clibo networth worth` | Current net worth |
| `clibo networth snapshot` | Save a net-worth snapshot |
| `clibo networth history` | Net worth over time |

`-t/--type` is `asset` or `liability`. Net worth = assets − liabilities.

## Examples

```bash
clibo networth add "Savings" -a 12000 -t asset -c cash
clibo networth add "Mortgage" -a 120000 -t liability
clibo networth worth
clibo networth snapshot
```

## For agents

```bash
clibo networth worth --json
# -> { "total_assets", "total_liabilities", "net_worth", "items", "currency" }
```

Take a `snapshot` periodically to build a `history` of net-worth change.
