---
name: clibo-lessons
description: Capture lessons learned with the `clibo lessons` CLI. Structured takeaway + context — distinct from `brag` (achievements) and `journal` (free-form). Maps "Lesson: X" to `clibo lessons add "X"`.
---

# 📓 clibo lessons

Lessons learned, structured. Each lesson is a **takeaway** plus an
optional **context** that says where you learned it. Distinct from
`brag` (achievements, positive) and `journal` (free-form daily).

## Commands

| Command | What it does |
|---|---|
| `clibo lessons add TAKEAWAY -x CONTEXT -c CATEGORY -t TAG` | Capture a lesson |
| `clibo lessons list [--days N] [-c CATEGORY] [-t TAG]` | List lessons |
| `clibo lessons show ID` | Pretty-printed detail |
| `clibo lessons search QUERY` | Search takeaway / context / tags |
| `clibo lessons random` | Re-encounter one random lesson |
| `clibo lessons rm ID` | Delete |
| `clibo lessons stats` | Counts by category |

`-x/--context` is the situation, not a date. Common categories:
`work`, `life`, `coding`, `health`, `general`.

## For agents

| User says | Command |
|---|---|
| "Lesson: always set max-attempts on retry logic" | `clibo lessons add "always set max-attempts on retry logic"` |
| "Learned from prod incident: small batches" | `clibo lessons add "ship in small batches" -x "prod incident" -c work` |
| "Show me a random lesson" | `clibo lessons random` |
| "What did I learn about coding?" | `clibo lessons list -c coding` |

```bash
clibo lessons random --json
# -> { "id", "entry_date", "takeaway", "context", "category", "tags" }
```
