---
name: clibo-groceries
description: Manage a grocery shopping list with the `clibo groceries` CLI. Use when the user wants to add items to buy, check them off while shopping, or clear the list afterward.
---

# 🛒 clibo groceries

Grocery & shopping list. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo groceries add NAME` | Add an item (`-q` quantity, `-c` category) |
| `clibo groceries list [--all]` | Show the list (pending, or all) |
| `clibo groceries buy ID` | Mark an item as bought |
| `clibo groceries unbuy ID` | Put a bought item back on the list |
| `clibo groceries rm ID` | Delete an item |
| `clibo groceries clear` | Remove all bought items |
| `clibo groceries stats` | Pending / bought counts |

## Examples

```bash
clibo groceries add milk -q "2 L" -c dairy
clibo groceries add bananas -q "1 bunch" -c produce
clibo groceries buy 1
clibo groceries clear
```

## For agents

```bash
clibo groceries list --json
# -> [ { "id", "name", "quantity", "category", "bought" } ]
```
