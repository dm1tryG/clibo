---
name: clibo-car
description: Track car fuel, maintenance, and driving trips with the `clibo car` CLI. Use when the user mentions filling up, getting a service, or driving somewhere — especially for business mileage that's typically tax-deductible.
---

# 🚗 clibo car

Car maintenance, fuel, and driving log. Local SQLite. Every command
accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo car fuel VOLUME [-o ODO] [-c COST]` | Log a fuel fill-up |
| `clibo car service NAME [-c COST] [-o ODO]` | Log a service / maintenance entry |
| `clibo car drive PURPOSE --km K [-c CAT]` | Log a driving trip |
| `clibo car list [-k fuel\|service\|drive]` | List all entries unified |
| `clibo car rm ID [--drive]` | Delete (use `--drive` for trip rows; IDs are per-table) |
| `clibo car stats` | Fuel/service spending, economy, plus driving totals by category |

Volumes and odometer use whatever units you prefer (L/km or gal/mi);
economy is computed per 100 in those same units. Odometer is optional
on fill-ups — fill-ups without an odometer are simply skipped when
computing economy.

The old `car fuel ODOMETER VOLUME` two-positional form is still
accepted for backward compatibility.

## Driving trips — business / personal / commute

`clibo car drive` records one trip with a purpose, distance, and a
**category**: `business`, `personal`, or `commute`. The business
category is typically tax-deductible at a per-km/per-mile rate
(varies by jurisdiction — keep that math out of clibo and do it at
tax filing time with the totals from `car stats`).

Distance can come from any of:

```bash
clibo car drive "client meeting" --km 47 -c business
clibo car drive "client meeting" --mi 30 -c business    # converted to km
clibo car drive "errands" --start-odo 50000 --end-odo 50080   # diff
```

## Natural language → command

| User says | Command |
|---|---|
| "Filled up the car — 45L for $60" | `clibo car fuel 45 -c 60` |
| "Tank fill at 52,340 km — 45.5L, $68" | `clibo car fuel 45.5 -o 52340 -c 68` |
| "Oil change cost me $80" | `clibo car service "Oil change" -c 80` |
| "Drove 47 miles for the Acme meeting" | `clibo car drive "Acme meeting" --mi 47 -c business` |
| "12 km home from work" | `clibo car drive "commute home" --km 12 -c commute` |
| "Odometer 50000 → 50080 today" | `clibo car drive "errands" --start-odo 50000 --end-odo 50080` |
| "How many business km this year?" | `clibo car stats` (see `drive_by_category`) |
| "How much have I spent on the car?" | `clibo car stats` |

## For agents

```bash
clibo car drive "client meeting" --mi 47 -c business --json
# -> { "id", "kind": "drive", "purpose", "distance_km": 75.64,
#      "category": "business", "odometer_start", "odometer_end", "note" }

clibo car stats --json
# -> { "fuel_entries", "service_entries", "fuel_spent", "service_spent",
#      "total_spent", "avg_economy_per_100",
#      "drive_entries", "drive_total_km",
#      "drive_by_category": [ {"category", "km"} ], "currency" }
```

Drives and fuel/service entries live in separate tables (separate ID
sequences). To delete a drive row, pass `--drive`: `clibo car rm 3 --drive`.
