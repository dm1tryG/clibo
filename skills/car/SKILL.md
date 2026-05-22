---
name: clibo-car
description: Track car fuel and maintenance with the `clibo car` CLI. Use when the user wants to log a fill-up or service, see car-related spending, or check fuel economy.
---

# 🚗 clibo car

Car maintenance & fuel log. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo car fuel ODO VOL` | Log a fuel fill-up (`-c` cost) |
| `clibo car service NAME` | Log a service / maintenance entry (`-c` cost, `-o` odo) |
| `clibo car list [-k KIND]` | List entries (`fuel` or `service`) |
| `clibo car rm ID` | Delete an entry |
| `clibo car stats` | Fuel/service spending and average economy |

Volumes and odometer use whatever units you prefer (L/km or gal/mi);
economy is computed per 100 in those same units.

## Examples

```bash
clibo car fuel 52340 45.5 -c 68
clibo car service "Oil change" -c 80 -o 52500
clibo car stats
```

## For agents

```bash
clibo car stats --json
# -> { "fuel_entries", "service_entries", "fuel_spent", "service_spent",
#      "total_spent", "avg_economy_per_100", "currency" }
```
