---
name: clibo-birthdays
description: Track birthdays and anniversaries with the `clibo birthdays` CLI. Use when the user wants to remember someone's birthday, see whose occasion is today, or list upcoming birthdays and anniversaries.
---

# 🎂 clibo birthdays

Birthday & anniversary reminders. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo birthdays add PERSON -d DATE` | Add a birthday or anniversary |
| `clibo birthdays list [-k KIND]` | All occasions, soonest first |
| `clibo birthdays today` | Whose occasion is today |
| `clibo birthdays upcoming --days 30` | Occasions in the next N days |
| `clibo birthdays rm ID` | Delete an occasion |
| `clibo birthdays stats` | Counts and the next occasion |

`-d/--date` is `MM-DD` or `YYYY-MM-DD` (a year enables age). `-k/--kind`
is `birthday` or `anniversary`.

## Examples

```bash
clibo birthdays add "Mom" -d 1965-04-15
clibo birthdays add "Wedding" -d 08-10 -k anniversary
clibo birthdays upcoming --days 30
```

## For agents

```bash
clibo birthdays upcoming --json
# -> [ { "id", "person", "kind", "next_date", "days_until", "turning" } ]
```

`turning` is the age/years at the next occurrence (null if no year set).
