---
name: clibo-dreams
description: Keep a dream journal with the `clibo dreams` CLI. Captures vividness 1-5, an optional lucid flag, and tag-style symbols so recurring patterns can be tracked. Maps "Strange dream about flying over the city" to `clibo dreams add "flying over the city"`.
---

# 🌙 clibo dreams

Dream journal. Distinct from `journal` (general daily writing) — dreams
have their own structure: vividness (1-5), a lucid-dream flag, and
symbol tags that let you see recurring patterns.

## Commands

| Command | What it does |
|---|---|
| `clibo dreams add SUMMARY -D DESC -v 1-5 --lucid -s sym1,sym2` | Log a dream |
| `clibo dreams today` | Today's dreams (full detail) |
| `clibo dreams list --days 14 [--lucid]` | Recent dreams |
| `clibo dreams show ID` | One dream, pretty-printed |
| `clibo dreams search QUERY` | Search summary / description / symbols |
| `clibo dreams symbols` | Symbol frequency (recurring patterns) |
| `clibo dreams rm ID` | Delete |
| `clibo dreams stats` | Counts, lucid rate, avg vividness, top symbols |

`--vivid/-v` defaults to 3; `--lucid` is off by default. Symbols are
comma-separated free-text tags (e.g. `flying`, `water`, `chase`).

## For agents

| User says | Command |
|---|---|
| "Strange dream about flying over the city last night" | `clibo dreams add "flying over the city" -s flying,city` |
| "I had a lucid dream about water" | `clibo dreams add "water dream" --lucid -s water` |
| "Super vivid one — chased through a forest" | `clibo dreams add "chased through a forest" -v 5 -s chase,forest` |
| "What symbols keep showing up in my dreams?" | `clibo dreams symbols` |

```bash
clibo dreams stats --json
# -> { "total", "lucid", "lucid_rate_pct", "avg_vividness",
#      "days_logged", "top_symbols": [{"symbol","count"}, ...] }
```
