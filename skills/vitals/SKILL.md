---
name: clibo-vitals
description: Log vital signs — blood pressure, pulse, glucose, temperature, blood oxygen — with the `clibo vitals` CLI. Use when the user wants to record a health measurement, see their latest vitals, or review trends for one vital.
---

# ❤️ clibo vitals

Vital-signs log: blood pressure, pulse, glucose, temperature and SpO₂.
Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo vitals log KIND VALUE` | **Generic logger** — works for every kind |
| `clibo vitals bp 120/80` (or `bp 120 80`) | Log blood pressure (auto-classified) |
| `clibo vitals pulse BPM` | Log heart rate |
| `clibo vitals glucose VALUE` | Log blood glucose (`-u` unit) |
| `clibo vitals temp CELSIUS` | Log body temperature |
| `clibo vitals spo2 PERCENT` | Log blood-oxygen saturation |
| `clibo vitals latest` | Most recent reading of each vital |
| `clibo vitals list --kind bp` | Recent readings (filter by kind) |
| `clibo vitals rm ID` | Delete a reading |
| `clibo vitals stats KIND` | Avg/min/max for one vital |

All log commands take `-d/--date` and `-n/--note`. Blood pressure is
classified as `normal`, `elevated`, `stage 1/2 hypertension` or
`hypertensive crisis`.

The **`log` dispatcher** accepts every kind so agents whose mental
model is *"every clibo tool has a `log` verb"* work without thinking
about which form vitals expects. Identical to the kind-specific form
under the hood — writes to the same table.

## Natural language → command

| User says | Command |
|---|---|
| "I have a fever — 39.2°C" | `clibo vitals log temp 39.2` |
| "BP today is 120/80" | `clibo vitals log bp 120/80` |
| "BP 140 over 90" | `clibo vitals log bp 140 90` |
| "Resting pulse 60" | `clibo vitals log pulse 60` |
| "Blood sugar 5.5 mmol/L" | `clibo vitals log glucose 5.5 -u mmol/L` |
| "SpO₂ is 98%" | `clibo vitals log spo2 98` |
| "Latest readings?" | `clibo vitals latest` |
| "BP trend this month" | `clibo vitals stats bp --days 30` |

## For agents

```bash
clibo vitals log temp 39.2 --json
# -> { "id", "kind": "temp", "value": 39.2, "unit": "°C",
#      "reading": "39.2 °C", "entry_date", ... }

clibo vitals log bp 120/80 --json
# -> { "kind": "bp", "value": 120, "value2": 80,
#      "reading": "120/80 mmHg", "category": "stage 1 hypertension", ... }

clibo vitals latest --json
# -> { "bp": {...}, "pulse": {...}, ... }  one entry per recorded kind
```

Readings include a `reading` string (e.g. `120/80 mmHg`); BP readings also
include a `category`. Not medical advice.
