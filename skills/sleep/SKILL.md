---
name: clibo-sleep
description: Track sleep duration and quality with the `clibo sleep` CLI. Use when the user wants to log how long and how well they slept, check last night's sleep, set a sleep goal, or review sleep stats.
---

# 😴 clibo sleep

Sleep duration & quality tracker. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo sleep log HOURS -q 4` | Log a night's sleep (`7.5` or `7:30`; omit if `-b/-w` given) |
| `clibo sleep log -b 23:30 -w 07:00` | Derive hours from bedtime + wake (wraps midnight) |
| `clibo sleep last` | Show your most recent night |
| `clibo sleep list --days 7` | Recent nights |
| `clibo sleep rm ID` | Delete an entry |
| `clibo sleep goal --set 8` | Set the nightly sleep goal (hours) |
| `clibo sleep stats --days 7` | Average hours, quality, nights vs goal |

`log` also takes `-b/--bedtime`, `-w/--wake`, `-d/--date`, `-n/--note`.
Quality is 1 (terrible) – 5 (great). Default goal is 8 hours.

## Examples

```bash
clibo sleep log 7.5 -q 4 -b 23:30 -w 07:00
clibo sleep last
clibo sleep goal --set 8
clibo sleep stats --days 7
```

## For agents

```bash
clibo sleep stats --json
# -> { "nights_logged", "avg_hours", "min_hours", "max_hours",
#      "avg_quality", "nights_goal_reached", "goal_hours" }
```

`log` returns the created entry incl. `quality_label`.
