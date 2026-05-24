---
name: clibo-meds
description: Track medications and doses with the `clibo meds` CLI. Use when the user mentions taking a dose, registering a medication, checking what's still due today, or reviewing adherence. Auto-creates medications on first `take` so one-off doses don't need pre-registration.
---

# 💊 clibo meds

Medication log & dosage reminders. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo meds add NAME -d DOSE -t N` | Register a medication explicitly (`-t` = times/day) |
| `clibo meds take NAME` | Log a dose. **Auto-creates the med if unknown** (one-off vitamins, ad-hoc painkillers). `--strict` to fail on unknown instead. |
| `clibo meds edit NAME [...]` | Set dosage / times-per-day / note / rename |
| `clibo meds today` | Today's meds and what's still due |
| `clibo meds list [--all]` | List active (or all) medications |
| `clibo meds history --days 7` | Recent dose history |
| `clibo meds stop NAME` | Stop a medication, keeping history (accepts name or ID) |
| `clibo meds rm NAME` | Delete a medication and its history (accepts name or ID) |
| `clibo meds stats --days 7` | Adherence percentage |

## Auto-create on `take`

`clibo meds take "Vitamin D"` works even when Vitamin D isn't registered yet.
It creates a minimal medication row (no dosage, 1×/day default) and logs the
dose. The success message includes a hint to set the dosage:

```
✓ Took 💊 Vitamin D — 1/1 today · new med — set dosage with:
  clibo meds edit "Vitamin D" -d '<dosage>'
```

For users who want the old "must register first" behaviour, pass `--strict`.
Numeric IDs that don't exist always fail (no fat-finger creation).

## Natural language → command

| User says | Command |
|---|---|
| "Took my morning vitamin D" | `clibo meds take "Vitamin D"` |
| "Just took an ibuprofen" | `clibo meds take Ibuprofen` |
| "Took the daily Lipitor" | `clibo meds take Lipitor` |
| "What meds do I still need today?" | `clibo meds today` |
| "How well am I sticking to my meds this week?" | `clibo meds stats --days 7` |
| "Set Lipitor to 20mg, once a day" | `clibo meds edit Lipitor -d 20mg -t 1` |
| "Stop taking Allegra" | `clibo meds stop Allegra` |

## For agents

```bash
clibo meds take "Vitamin D" --json
# -> { "id", "medication": "Vitamin D", "med_id", "auto_created": true|false,
#      "taken_today": 1, "times_per_day": 1 }

clibo meds today --json
# -> { "date": ..., "medications": [
#      { "id", "medication", "dosage", "taken", "times_per_day",
#        "done", "remaining" } ] }
```

`take.auto_created` lets agents know when a new medication was implicitly
created (vs. an existing one's dose was logged). Useful for prompting the
user to set dosage on the new row. `stats` returns `adherence_pct`.
