---
name: clibo-jobs
description: Track job applications with the `clibo jobs` CLI. Use when the user wants to log a job application, update its status, see their application pipeline, or review job-search stats.
---

# 💼 clibo jobs

Job application tracker. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo jobs add COMPANY ROLE` | Track a new application |
| `clibo jobs list [-s STATUS]` | List applications |
| `clibo jobs show ID` | One application in detail |
| `clibo jobs move ID STATUS` | Update an application's status |
| `clibo jobs edit ID` | Edit an application |
| `clibo jobs rm ID` | Delete an application |
| `clibo jobs pipeline` | Application counts by status |
| `clibo jobs stats` | Job-search stats & response rate |

Statuses: `wishlist`, `applied`, `interviewing`, `offer`, `rejected`,
`accepted`. `add` also takes `--salary`, `-l/--location`, `-u/--url`.

## Examples

```bash
clibo jobs add "Acme Corp" "Senior Engineer" -l Remote --salary "120-140k"
clibo jobs move 1 interviewing
clibo jobs pipeline
```

## For agents

```bash
clibo jobs pipeline --json
# -> { "by_status": { "applied": 3, "interviewing": 1, ... }, "total": 4 }
```
