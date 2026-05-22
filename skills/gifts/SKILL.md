---
name: clibo-gifts
description: Track gift ideas and giving with the `clibo gifts` CLI. Use when the user wants to note a gift idea for someone, mark a gift bought or given, or see what they've planned.
---

# 🎁 clibo gifts

Gift ideas & giving tracker. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo gifts add RECIPIENT IDEA` | Add a gift idea |
| `clibo gifts list` | List gifts (`-r` recipient, `-s` status) |
| `clibo gifts show ID` | One gift in detail |
| `clibo gifts bought ID` | Mark a gift as bought |
| `clibo gifts given ID` | Mark a gift as given |
| `clibo gifts rm ID` | Delete a gift idea |
| `clibo gifts stats` | Counts by status and total spent |

Status flows `idea → bought → given`. `add` also takes `-o/--occasion`,
`-p/--price` and `-u/--url`.

## Examples

```bash
clibo gifts add "Mom" "cookbook" -o birthday -p 35
clibo gifts bought 1
clibo gifts list -r Mom
```

## For agents

```bash
clibo gifts list --json
# -> [ { "id", "recipient", "idea", "occasion", "price", "status" } ]
```
