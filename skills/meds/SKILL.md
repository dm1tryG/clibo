---
name: clibo-meds
description: Track medications and doses with the `clibo meds` CLI. Use when the user wants to register a medication, log that they took a dose, see what's still due today, or review adherence.
---

# 💊 clibo meds

Medication log & dosage reminders. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo meds add NAME -d DOSE -t N` | Register a medication (`-t` = times/day) |
| `clibo meds take NAME\|ID` | Log a dose taken (also `-d` date) |
| `clibo meds today` | Today's meds and what's still due |
| `clibo meds list [--all]` | List active (or all) medications |
| `clibo meds history --days 7` | Recent dose history |
| `clibo meds stop ID` | Stop a medication, keeping history |
| `clibo meds rm ID` | Delete a medication and its history |
| `clibo meds stats --days 7` | Adherence percentage |

## Examples

```bash
clibo meds add "Vitamin D" -d 1000IU -t 1
clibo meds add "Omega-3" -d 1g -t 2
clibo meds take "Omega-3"
clibo meds today
```

## For agents

```bash
clibo meds today --json
# -> { "date": ..., "medications": [
#      { "id", "medication", "dosage", "taken", "times_per_day", "done", "remaining" } ] }
```

`take` accepts a medication name or numeric ID and returns
`{"taken_today", "times_per_day"}`. `stats` returns `adherence_pct`.
