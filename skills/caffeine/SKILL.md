---
name: clibo-caffeine
description: Caffeine intake tracker with the `clibo caffeine` CLI. Distinct from `water` (hydration) and `calorie` (food). The killer feature is computing residual caffeine at bedtime using its known half-life — sleep researchers recommend < 10 mg residual at sleep onset. Maps "I had a coffee at 9am" to `clibo caffeine log coffee -t 09:00`.
---

# ☕ clibo caffeine

A caffeine intake tracker. Each drink is logged with its mg of caffeine
and the time consumed; the tool then computes how much of it will still
be in your system at bedtime using the canonical 5.5-hour half-life.

Built-in presets cover the common drinks (espresso, latte, matcha,
Red Bull, …) so you don't have to remember exact mg numbers. Override
with `-m / --mg` for anything custom (cold brew, double shots, etc.).

## Commands

| Command | What it does |
|---|---|
| `clibo caffeine log DRINK [-m MG] [-t HH:MM]` | Log a drink (uses preset mg if known) |
| `clibo caffeine add ...` | Alias for `log` |
| `clibo caffeine today` | Today's total + bedtime-residual estimate |
| `clibo caffeine cutoff` | Latest safe time for each drink today |
| `clibo caffeine list --days 7 [--drink X]` | Recent entries |
| `clibo caffeine show ID` | One entry |
| `clibo caffeine rm ID` | Delete |
| `clibo caffeine bedtime --set HH:MM` | Show / set bedtime (default 23:00) |
| `clibo caffeine stats --days 30` | Daily avg, by drink, over-limit days |

Presets (mg of caffeine): espresso=63, double-espresso=126,
americano=150, latte=75, cappuccino=75, flat-white=130, coffee=95,
cold-brew=200, drip=95, decaf=5, matcha=70, green-tea=30,
black-tea=50, earl-grey=50, redbull=80, monster=160, coca-cola=34,
diet-coke=46, yerba-mate=85, chocolate=12.

## The bedtime-residual model

Caffeine has a half-life of ~5.5 hours in adults, so a 95 mg coffee
at 14:00 still leaves ~30 mg by 23:00 — enough to fragment sleep.
The `today` view shows residual at bedtime; `cutoff` answers
"how late can I still drink X today?"

## For agents

| User says | Command |
|---|---|
| "I had a coffee at 9am" | `clibo caffeine log coffee -t 09:00` |
| "Double espresso just now" | `clibo caffeine log double-espresso` |
| "Cold brew, large — guessing 220mg" | `clibo caffeine log cold-brew -m 220` |
| "How much caffeine have I had today?" | `clibo caffeine today` |
| "Can I still have a coffee at 5pm?" | `clibo caffeine cutoff` |
| "My bedtime is 10pm" | `clibo caffeine bedtime --set 22:00` |

```bash
clibo caffeine today --json
# -> { "date", "drinks", "total_mg", "daily_limit_mg", "over_limit",
#      "residual_at_bedtime_mg", "bedtime", "entries": [...] }
```
