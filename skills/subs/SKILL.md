---
name: clibo-subs
description: Track recurring subscriptions with the `clibo subs` CLI. Use when the user wants to add a subscription, see total monthly/yearly cost, list what's billing soon, or cancel a subscription.
---

# 🔁 clibo subs

Recurring subscriptions tracker. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo subs add NAME -a AMOUNT -c CYCLE` | Add a subscription |
| `clibo subs list [--all]` | List active (or all) subscriptions |
| `clibo subs total` | Total monthly & yearly cost |
| `clibo subs upcoming --days 14` | Subscriptions billing soon |
| `clibo subs cancel ID` | Mark a subscription cancelled |
| `clibo subs rm ID` | Delete a subscription |
| `clibo subs stats` | Cost breakdown by category |

Cycle is `weekly`, `monthly` or `yearly`; every charge is normalised to a
monthly cost. Pass `--next DATE` to enable `upcoming` reminders.

## Examples

```bash
clibo subs add Netflix -a 12.99 -c monthly --category streaming
clibo subs add Domain -a 120 -c yearly
clibo subs total
clibo subs upcoming --days 14
```

## For agents

```bash
clibo subs total --json
# -> { "active_subscriptions", "monthly_cost", "yearly_cost", "currency" }
```

Each subscription row includes a normalised `monthly_cost`.
