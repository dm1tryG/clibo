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
| `clibo vitals bp SYS DIA` | Log blood pressure (auto-classified) |
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

## Examples

```bash
clibo vitals bp 120 80
clibo vitals pulse 72
clibo vitals glucose 95 -u mg/dL
clibo vitals latest
clibo vitals stats pulse --days 30
```

## For agents

```bash
clibo vitals latest --json
# -> { "bp": {...}, "pulse": {...}, ... }  one entry per recorded kind
```

Readings include a `reading` string (e.g. `120/80 mmHg`); BP readings also
include a `category`. Not medical advice.
