---
name: clibo-symptom
description: Structured pain & symptom tracker — intensity 1-10 (medical scale), body location, duration, triggers, relief, history with trend. Use when the user reports back pain, headaches, migraines, allergies, fatigue, IBS flare-ups, or any subjective symptom they want to track over time. Distinct from `vitals` (measurable readings like BP), `mood` (whole-person 1-5), and `journal` (freeform).
---

# 🤒 clibo symptom

Pain & symptom tracker. Local SQLite. Every command accepts `--json`.

The 1-10 scale matches the standard medical pain rating: 1-3 mild,
4-6 moderate, 7-9 severe, 10 worst possible.

## Commands

| Command | What it does |
|---|---|
| `clibo symptom log NAME -i INTENSITY [-l LOC -t MIN --triggers ... -r ...]` | Log a symptom |
| `clibo symptom today` | Today's entries with the worst score |
| `clibo symptom list --days N -N NAME` | Recent entries (optionally filtered) |
| `clibo symptom history NAME --days N` | One symptom over time — per-day max & avg + trend |
| `clibo symptom show ENTRY` | One entry (ID or symptom name; most-recent wins) |
| `clibo symptom edit ENTRY [...]` | Update an entry |
| `clibo symptom rm ENTRY` | Delete |
| `clibo symptom stats --days N` | Top complaints, days affected, worst episode |

## Natural language → command

| User says | Command |
|---|---|
| "My back's hurting — about 7/10" | `clibo symptom log "back pain" -i 7` |
| "Migraine, 9/10, frontal, ibuprofen helped" | `clibo symptom log migraine -i 9 -l frontal -r ibuprofen` |
| "Headache lasted 2 hours from too little sleep" | `clibo symptom log headache -i 5 -t 120 --triggers "poor sleep"` |
| "Is my back pain getting better?" | `clibo symptom history "back pain"` |
| "What's been bothering me this month?" | `clibo symptom stats --days 30` |
| "Show today's symptoms" | `clibo symptom today` |
| "Update — back pain is down to 3 now" | `clibo symptom edit "back pain" -i 3` |

## For agents

```bash
clibo symptom log "back pain" -i 7 -l lumbar -r ibuprofen --json
# -> { "id", "name", "intensity": 7, "intensity_label": "severe",
#      "location": "lumbar", "duration_min": 0, "relief": "ibuprofen", ... }

clibo symptom history "back pain" --json
# -> [ { "entry_date", "episodes", "avg_intensity", "max_intensity" }, ... ]

clibo symptom stats --json
# -> { "total_episodes", "days_affected", "avg_intensity",
#      "top_symptoms": [...], "worst_episode": {...} }
```

`log` returns `intensity_label` (`mild`/`moderate`/`severe`/`worst possible`)
so agents can format severity prose without bucket logic. `history` includes
a `trend` indicator (improving/worsening/steady) in the human view.

## When to use which tool

- **`symptom`** — subjective body experience: pain, fatigue, nausea, allergies
- **`vitals`** — measurable readings: blood pressure, pulse, glucose, SpO2
- **`mood`** — whole-person emotional state (1-5)
- **`meds`** — when you actually took medication
- **`journal`** — freeform daily reflection (no scale, no aggregation)

For a flare-up the natural pattern is to `symptom log` and then `meds take`
(the dose) and optionally `journal add` (the context).
