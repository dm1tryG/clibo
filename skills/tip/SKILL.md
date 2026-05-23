---
name: clibo-tip
description: Track tips with the `clibo tip` CLI. Records bill amount, tip amount, computed tip-percent, optional venue and service rating so you can see your average generosity and how it varies by venue. Maps "I left a 20% tip on a $40 dinner" to `clibo tip log 40 -p 20 -v dinner`.
---

# 🪙 clibo tip

A tipping tracker. Separate from `expense` because tipping has its own
shape — you care about *the percent*, not just the dollar amount, and
you want venue / service-rating breakdowns ("Do I tip more at
restaurants than cafés?") that don't fit a generic expense row.

## Commands

| Command | What it does |
|---|---|
| `clibo tip log BILL -p PERCENT` | Log a tip as a % of the bill |
| `clibo tip log BILL -a AMOUNT` | Log a tip as an absolute amount |
| `clibo tip add ...` | Alias for `log` |
| `clibo tip calc BILL -p PERCENT` | Quick calculator — does NOT save |
| `clibo tip today` | Today's tips |
| `clibo tip list --days 30 [--venue V]` | Recent tips |
| `clibo tip show ID` | One tip |
| `clibo tip rm ID` | Delete |
| `clibo tip stats --days 90` | Avg %, generosity weighted by bill, by-venue, by-rating |

Exactly one of `--percent / -p` and `--amount / -a` is required.
`-v / --venue` is free text; `-r / --rating` is service rating 1-5.

## For agents

| User says | Command |
|---|---|
| "I left a 20% tip on a $40 dinner" | `clibo tip log 40 -p 20 -v dinner` |
| "Tipped $10 on a $50 bill at Joe's" | `clibo tip log 50 -a 10 -v "Joe's Diner"` |
| "Great service at the café, 25% tip on $18" | `clibo tip log 18 -p 25 -v café -r 5` |
| "What's my average tip percentage?" | `clibo tip stats` |
| "How much is a 20% tip on $35?" (don't save) | `clibo tip calc 35 -p 20` |

```bash
clibo tip stats --json
# -> { "count", "total_billed", "total_tipped", "avg_tip_percent",
#      "weighted_tip_percent", "biggest_tip", "by_venue_avg_percent",
#      "by_service_rating_avg_percent", "currency" }
```

> Note: `tip` does *not* automatically create an `expense` row. If you
> also want the bill on your expense log, run `clibo expense add ...`
> separately.
