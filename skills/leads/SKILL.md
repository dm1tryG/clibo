---
name: clibo-leads
description: Manage a sales pipeline with the `clibo leads` CLI. Use when the user wants to add a deal, move it through pipeline stages, view the pipeline, or check win rate.
---

# 🧲 clibo leads

Sales pipeline & deals. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo leads add NAME -v VALUE` | Add a deal to the pipeline |
| `clibo leads list [-s STAGE]` | List deals |
| `clibo leads show ID` | One deal in detail |
| `clibo leads move ID STAGE` | Move a deal to a new stage |
| `clibo leads edit ID` | Edit a deal |
| `clibo leads rm ID` | Delete a deal |
| `clibo leads pipeline` | Open deals grouped by stage with value bars |
| `clibo leads stats` | Pipeline value and win rate |

Stages: `new`, `contacted`, `qualified`, `proposal`, `won`, `lost`.

## Examples

```bash
clibo leads add "Acme contract" -v 12000 -c "Acme Inc"
clibo leads move 1 qualified
clibo leads pipeline
clibo leads stats
```

## For agents

```bash
clibo leads pipeline --json
# -> { "by_stage": [ {"stage","deals","value"} ], "open_value", "currency" }

clibo leads stats --json
# -> { "open_value", "won_value", "win_rate_pct", ... }
```
