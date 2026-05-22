---
name: clibo-goals
description: Track goals and OKRs with milestones using the `clibo goals` CLI. Use when the user wants to set a goal, break it into milestones, check off progress, or review how their goals are going.
---

# 🎯 clibo goals

Goals & OKRs with milestones. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo goals add NAME` | Create a goal (`-D` desc, `--deadline`) |
| `clibo goals milestone GOAL NAME` | Add a milestone to a goal |
| `clibo goals list [--all]` | Goals with milestone-progress bars |
| `clibo goals show GOAL` | A goal plus its milestones |
| `clibo goals check MILESTONE_ID` | Mark a milestone done |
| `clibo goals uncheck MILESTONE_ID` | Reopen a milestone |
| `clibo goals complete GOAL` | Mark the whole goal achieved |
| `clibo goals rm ID` | Delete a goal and its milestones |
| `clibo goals stats` | Goal & milestone counts |

`GOAL` accepts a goal name or ID. Progress is the share of milestones done.

## Examples

```bash
clibo goals add "Learn Spanish" -D "Reach B1" --deadline 2026-12-31
clibo goals milestone "Learn Spanish" "Finish beginner course"
clibo goals check 1
clibo goals show "Learn Spanish"
```

## For agents

```bash
clibo goals list --json
# -> [ { "id", "name", "deadline", "milestones_total",
#        "milestones_done", "progress_pct", "done" } ]
```
