---
name: clibo-cv
description: Maintain a career history with the `clibo cv` CLI — jobs, education, projects, certifications. Distinct from `clibo jobs` (which is for *applying* to jobs). Maps "CV entry: 2024-2026 Senior Engineer at Acme" to `clibo cv add "Senior Engineer" -o Acme --start 2024 --end 2026`.
---

# 📜 clibo cv

Career history — your résumé as living data. Distinct from `clibo jobs`
(which is for *applying* to jobs). Local SQLite. Every command accepts
`--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo cv add TITLE -o ORG -k KIND --start YYYY-MM --end YYYY-MM` | Add an entry |
| `clibo cv achieve ID 'bullet'` | Append a highlight bullet to an entry |
| `clibo cv current` | Show ongoing entries (no end date) |
| `clibo cv list [-k KIND]` | List entries newest-start first |
| `clibo cv show ID` | Pretty-printed CV-style detail |
| `clibo cv timeline` | Chronological CV-ready timeline |
| `clibo cv end ID --on YYYY-MM` | Close out a current entry |
| `clibo cv edit ID` | Edit title / org / desc / location / tags |
| `clibo cv rm ID` | Delete |
| `clibo cv stats` | Counts by kind + approx job years |

Kinds: `job`, `education`, `project`, `cert`, `other`.
Dates accept `YYYY-MM` (month precision, typical for résumés) or any
date `parse_date` understands. Omit `--end` for currently-running.

## For agents

| User says | Command |
|---|---|
| "Add CV entry: 2024-2026 Senior Engineer at Acme" | `clibo cv add "Senior Engineer" -o Acme --start 2024-01 --end 2026-01 -k job` |
| "Currently I'm a Founder at MyCo since June 2025" | `clibo cv add Founder -o MyCo --start 2025-06` (no `--end`) |
| "Add bullet: shipped the search feature" | `clibo cv achieve <id> "shipped the search feature"` |
| "I left Acme last month" | `clibo cv end <id> --on last month` |
| "Show my CV" | `clibo cv timeline` |

```bash
clibo cv timeline --json
# -> { "entries": [ {"id","kind","title","org","period","start_date",
#       "end_date","current","description","achievements","tags"}, ... ] }
```
