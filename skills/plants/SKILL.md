---
name: clibo-plants
description: Track houseplant watering with the `clibo plants` CLI. Use when the user wants to add a plant, mark it watered, or see which plants need watering.
---

# 🪴 clibo plants

Plant care & watering schedule. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo plants add NAME -w DAYS` | Add a plant with a watering interval |
| `clibo plants list` | All plants, thirstiest first |
| `clibo plants water PLANT` | Mark a plant watered today |
| `clibo plants thirsty` | Plants that need watering now |
| `clibo plants rm ID` | Delete a plant |
| `clibo plants stats` | Plant-care stats |

`-w/--water-every` sets the watering interval in days; `-s/--species`
and `-l/--location` are optional. `PLANT` accepts a name or ID.

## Examples

```bash
clibo plants add "Monstera" -w 7 -l "living room"
clibo plants add "Basil" -w 2 -l kitchen
clibo plants water "Monstera"
clibo plants thirsty
```

## For agents

```bash
clibo plants thirsty --json
# -> [ { "id", "name", "location", "next_water", "water_in", "status" } ]
```

Status is `thirsty`, `water today` or `ok`.
