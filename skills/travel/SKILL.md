---
name: clibo-travel
description: Plan trips and itineraries with the `clibo travel` CLI. Use when the user wants to add a trip, build an itinerary, see upcoming travel, or track travel spending against a budget.
---

# ✈️ clibo travel

Trip planner & itinerary. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo travel add NAME` | Add a trip (`-d` destination, `--start`, `--end`, `-b` budget) |
| `clibo travel list [--all]` | Trips (default: current + upcoming) |
| `clibo travel show TRIP` | A trip with its day-by-day itinerary |
| `clibo travel plan TRIP DATE TITLE` | Add an itinerary item |
| `clibo travel upcoming` | Upcoming trips |
| `clibo travel rm ID` | Delete a trip and its itinerary |
| `clibo travel stats` | Trips, days traveled, total spending |

`plan` takes `-t/--time`, `-l/--location`, `-c/--category`
(`flight`/`hotel`/`activity`/`food`/`transport`/`note`), `--cost`.
`TRIP` accepts a trip name or numeric ID.

## Examples

```bash
clibo travel add "Paris weekend" -d Paris --start 2026-08-10 --end 2026-08-13 -b 1500
clibo travel plan "Paris weekend" 2026-08-10 "Outbound flight" -t 09:30 -c flight --cost 250
clibo travel plan "Paris weekend" 2026-08-10 "Eiffel Tower" -t 14:00 -c activity --cost 30
clibo travel show "Paris weekend"
```

## For agents

```bash
clibo travel show "Paris weekend" --json
# -> { "id", "name", "destination", "start_date", "end_date",
#      "budget", "spent", "remaining",
#      "itinerary": [ {"event_date","title","category","cost",...} ] }
```
