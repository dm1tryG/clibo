---
name: clibo-car
description: Track car fuel and maintenance with the `clibo car` CLI. Use when the user wants to log a fill-up or service, see car-related spending, or check fuel economy. Maps "filled up for $60" to `clibo car fuel 45 -c 60` (odometer optional).
---

# 🚗 clibo car

Car maintenance & fuel log. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo car fuel VOLUME [-o ODO] [-c COST]` | Log a fuel fill-up (odometer optional) |
| `clibo car service NAME [-c COST] [-o ODO]` | Log a service / maintenance entry |
| `clibo car list [-k KIND]` | List entries (`fuel` or `service`) |
| `clibo car rm ID` | Delete an entry |
| `clibo car stats` | Fuel/service spending and average economy |

Volumes and odometer use whatever units you prefer (L/km or gal/mi);
economy is computed per 100 in those same units. Odometer is optional
on fill-ups — fill-ups without an odometer are simply skipped when
computing economy.

The old `car fuel ODOMETER VOLUME` two-positional form is still
accepted for backward compatibility.

## For agents

| User says | Command |
|---|---|
| "Filled up the car — 45L for $60" | `clibo car fuel 45 -c 60` |
| "Just filled up, 12.5 gallons at $52" | `clibo car fuel 12.5 -c 52` |
| "Tank fill at 52,340 km — 45.5L, $68" | `clibo car fuel 45.5 -o 52340 -c 68` |
| "Oil change cost me $80" | `clibo car service "Oil change" -c 80` |
| "How much have I spent on the car?" | `clibo car stats` |

```bash
clibo car stats --json
# -> { "fuel_entries", "service_entries", "fuel_spent", "service_spent",
#      "total_spent", "avg_economy_per_100", "currency" }
```
