---
name: clibo-documents
description: Track important documents and their expiry dates with the `clibo documents` CLI. Passports, driver's licenses, insurance policies, professional certs, visas, warranties. The killer view is `documents expiring` — what's coming up in the next N days. Maps "My passport expires June 2030" to `clibo documents add Passport -e 2030-06 -k passport`.
---

# 📑 clibo documents

A registry of important documents that have expiry dates. Distinct from
`events` (one-off dates) and `bills` (recurring due dates with amounts).
The thing this tool prevents: showing up at the airport with an
expired passport because nobody told you in time.

## Commands

| Command | What it does |
|---|---|
| `clibo documents add NAME -e EXPIRES [-k KIND] [-i ISSUED] [-# NUMBER]` | Add a document |
| `clibo documents list [-k KIND] [--expired]` | List documents, soonest expiry first |
| `clibo documents expiring [--days 90]` | Documents expiring within N days |
| `clibo documents expired` | Documents that have already expired |
| `clibo documents show ID` | Full detail for one document |
| `clibo documents rm ID` | Delete |
| `clibo documents stats` | Counts by kind, soonest / farthest expiry, urgency buckets |

`-e/--expires` accepts everything `parse_date` accepts — `2030-06-15`,
`June 2030` (treated as the 1st), `in 3 years`, `next month`, etc.

`KIND` is one of: `passport`, `license`, `id`, `insurance`, `cert`,
`visa`, `membership`, `warranty`, `lease`, `other`.

## Urgency colour code (in tables)

- 🔴 **critical** — ≤ 30 days
- 🟡 **soon** — ≤ 90 days
- 🟢 **watch** — ≤ 1 year
- 🟢 **ok** — > 1 year
- ❌ **expired**

## For agents

| User says | Command |
|---|---|
| "My passport expires June 15 2030" | `clibo documents add Passport -e "June 15 2030" -k passport` |
| "Add my driver's license, expires next March" | `clibo documents add "Driver's license" -e "March" -k license` |
| "Insurance #ACME-1234 valid until 2027-01" | `clibo documents add "Car insurance" -e 2027-01-01 -k insurance -# ACME-1234` |
| "What's expiring soon?" | `clibo documents expiring --days 90` |
| "Show me everything that's already expired" | `clibo documents expired` |

```bash
clibo documents expiring --json
# -> a list of {id, name, kind, expires, days_until, humanized, urgency, …}
#    sorted by soonest expiry first.
```
