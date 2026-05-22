---
name: clibo-time
description: Track time by project with the `clibo time` CLI. Use when the user wants to start/stop a timer, log hours against a project, or see a time report broken down by project.
---

# ⏱️ clibo time

Time tracking by project. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo time start PROJECT` | Start a running timer (`-t` task) |
| `clibo time stop` | Stop the timer and log the elapsed time |
| `clibo time status` | Whether a timer is running, and for how long |
| `clibo time log PROJECT MINUTES` | Log time manually |
| `clibo time list --days 7` | Recent time entries |
| `clibo time rm ID` | Delete an entry |
| `clibo time report --days 7` | Time per project with share bars |
| `clibo time stats --days 7` | Totals and averages |

Only one timer runs at a time — `start` fails if one is already running.

## Examples

```bash
clibo time start clibo -t coding
clibo time status
clibo time stop
clibo time log clibo 90 -t docs
clibo time report --days 7
```

## For agents

```bash
clibo time report --json
# -> { "window_days", "total_minutes",
#      "by_project": [ {"project","minutes","hours","share"} ] }
```
