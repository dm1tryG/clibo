---
name: clibo-pets
description: Track pet care with the `clibo pets` CLI. Use when the user wants to add a pet, log a vet visit, feeding, walk or grooming, or review care history.
---

# 🐾 clibo pets

Pet care, feeding & vet log. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo pets add NAME` | Add a pet (`-s` species, `-b` breed, `--birth` date) |
| `clibo pets list` | List all pets with their age and last vet visit |
| `clibo pets show PET` | A pet with their recent events |
| `clibo pets log PET KIND SUMMARY` | Log an event (`-c` cost, `-d` date) |
| `clibo pets events --days 14` | Recent events across all pets |
| `clibo pets rm ID` | Delete a pet and their history |
| `clibo pets stats` | Pet & event counts plus care spending |

`KIND` is `feeding`, `vet`, `grooming`, `walk`, `medication` or `note`.
`PET` accepts a pet name or numeric ID.

## Examples

```bash
clibo pets add "Whiskers" -s cat --birth 2022-04-15
clibo pets log Whiskers vet "Annual checkup" -c 120
clibo pets log Whiskers feeding "morning meal"
clibo pets show Whiskers
```

## For agents

```bash
clibo pets show Whiskers --json
# -> { "name", "species", "age_years", "last_vet",
#      "events": [ {"kind", "summary", "cost", ...} ] }
```
