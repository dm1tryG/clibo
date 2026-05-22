---
name: clibo-events
description: Track events and reminders with the `clibo events` CLI. Use when the user wants to add an event, see what's on today, list upcoming events, or manage their calendar.
---

# 📅 clibo events

Events & reminders calendar. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo events add TITLE -d DATE` | Add an event (`-t` time, `-l` location) |
| `clibo events list [--all]` | Upcoming events (`--all` includes past) |
| `clibo events today` | Today's events |
| `clibo events upcoming --days 7` | Events in the next N days |
| `clibo events show ID` | One event in detail |
| `clibo events edit ID` | Edit an event |
| `clibo events rm ID` | Delete an event |
| `clibo events stats` | Event counts and the next event |

## Examples

```bash
clibo events add "Dentist" -d 2026-06-01 -t 09:00 -l "Main St Clinic"
clibo events today
clibo events upcoming --days 14
```

## For agents

```bash
clibo events upcoming --json
# -> [ { "id", "title", "event_date", "event_time", "when",
#        "days_until", "location" } ]
```

`when` is a relative label like `today`, `in 3d` or `tomorrow`.
