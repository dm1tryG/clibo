---
name: clibo-recipes
description: Keep a personal recipe book with the `clibo recipes` CLI. Use when the user wants to save a recipe, look one up, search by ingredient, or get a random suggestion for what to cook.
---

# 👨‍🍳 clibo recipes

Personal recipe book. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo recipes add NAME` | Save a recipe |
| `clibo recipes list` | List recipes (`-c` category, `-t` tag) |
| `clibo recipes show ID` | Show a full recipe |
| `clibo recipes search QUERY` | Search by name, ingredients or tags |
| `clibo recipes edit ID` | Edit a recipe |
| `clibo recipes rm ID` | Delete a recipe |
| `clibo recipes random` | Pick a random recipe to cook |
| `clibo recipes stats` | Recipe-book stats |

`add` takes `-i/--ingredients`, `-I/--instructions`, `-s/--servings`,
`-p/--prep` (minutes), `-c/--category`, `-t/--tag`.

## Examples

```bash
clibo recipes add "Pasta Carbonara" -i "spaghetti, eggs, pancetta" -s 2 -p 25
clibo recipes search eggs
clibo recipes random
clibo recipes show 1
```

## For agents

```bash
clibo recipes show 1 --json
# -> { "id", "name", "ingredients", "instructions",
#      "servings", "prep_minutes", "category", "tags" }
```
