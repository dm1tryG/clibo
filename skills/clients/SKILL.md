---
name: clibo-clients
description: Manage freelance clients and billable hours with the `clibo clients` CLI. Use when the user wants to add a client, log hours worked, see earnings per client, or review client stats.
---

# 🧑‍💼 clibo clients

Freelance client manager. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo clients add NAME -r RATE` | Add a client with an hourly rate |
| `clibo clients log CLIENT HOURS` | Log hours worked for a client |
| `clibo clients list [-s STATUS]` | List clients with hours & earnings |
| `clibo clients show CLIENT` | A client plus their hours log |
| `clibo clients edit ID` | Edit a client |
| `clibo clients rm ID` | Delete a client and their hours |
| `clibo clients stats` | Total hours and earnings |

`CLIENT` accepts a client name or numeric ID. Status is `prospect`,
`active` or `past`. Earnings = logged hours × hourly rate.

## Examples

```bash
clibo clients add "Acme Inc" -r 90 -e billing@acme.com
clibo clients log "Acme Inc" 8 -D "Sprint work"
clibo clients show "Acme Inc"
clibo clients stats
```

## For agents

```bash
clibo clients list --json
# -> [ { "id", "name", "hourly_rate", "status",
#        "hours_logged", "earnings" } ]
```
