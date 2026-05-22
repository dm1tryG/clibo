---
name: clibo-wishlist
description: Keep a things-to-buy wishlist with the `clibo wishlist` CLI. Use when the user wants to add something they want to buy, prioritise their wishlist, mark an item purchased, or see the total cost of what's left.
---

# ⭐ clibo wishlist

Things-to-buy wishlist with prices and priorities. Local SQLite. Every
command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo wishlist add NAME -p PRICE -P PRIORITY` | Add a wished-for item |
| `clibo wishlist list [--all]` | Wishlist, highest priority first |
| `clibo wishlist show ID` | One item in detail |
| `clibo wishlist buy ID` | Mark an item as purchased |
| `clibo wishlist rm ID` | Delete an item |
| `clibo wishlist stats` | Total pending cost & breakdown |

`-P/--priority` is 1 (low) – 5 (high), default 3. `add` also takes
`-u/--url` and `-c/--category`.

## Examples

```bash
clibo wishlist add "Standing desk" -p 350 -P 4 -c office
clibo wishlist add "Mechanical keyboard" -p 120 -P 5 -u https://example.com
clibo wishlist list
clibo wishlist buy 1
```

## For agents

```bash
clibo wishlist stats --json
# -> { "total_items", "pending", "purchased", "pending_cost",
#      "by_priority", "currency" }
```

`list` is sorted by priority (then price) descending.
