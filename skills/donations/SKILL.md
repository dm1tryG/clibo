---
name: clibo-donations
description: Track charitable giving with `clibo donations`. Distinct from `expense` — donations care about calendar-year totals (for tax filing), tax-deductibility per gift, and recipient-organisation totals. Maps "I donated $50 to Red Cross" to `clibo donations log "Red Cross" -a 50`.
---

# ❤️ clibo donations

Log charitable giving — distinct from `expense` because:

- **Calendar-year totals** matter for tax filing (separate aggregation
  from fiscal-year expense reporting).
- **Tax-deductible vs not** — political contributions, gifts to
  individuals, and many non-US NGOs aren't deductible. Default is
  deductible; pass `--no-deductible` to flag the exceptions.
- **Recipient as structured data** — repeat gifts to the same org
  cluster cleanly: "Red Cross: $250 across 5 gifts in 2026", not
  five expense rows with slightly-different descriptions.

## Commands

| Command | What it does |
|---|---|
| `clibo donations log ORG -a AMOUNT [-r RECEIPT] [--no-deductible]` | Log a donation |
| `clibo donations add ...` | Alias for `log` |
| `clibo donations list [-y YEAR] [-R RECIPIENT]` | Recent donations, newest first |
| `clibo donations year [-y YEAR]` | Annual summary with deductible total |
| `clibo donations top [--days 365]` | Top recipients by total amount |
| `clibo donations show ID` | One donation |
| `clibo donations rm ID` | Delete |
| `clibo donations stats` | Lifetime: total, deductible total, by year, top recipient |

## For agents

| User says | Command |
|---|---|
| "I donated $50 to Red Cross" | `clibo donations log "Red Cross" -a 50` |
| "Gave $200 to a friend's GoFundMe — not deductible" | `clibo donations log "GoFundMe Alice" -a 200 --no-deductible` |
| "How much did I give in 2026?" | `clibo donations year -y 2026` |
| "What's my tax-deductible total this year?" | `clibo donations year` |
| "Who do I give the most to?" | `clibo donations top` |

```bash
clibo donations year --json
# -> { "year", "count", "total", "deductible_total",
#      "non_deductible_total", "recipients",
#      "by_recipient": [ {"recipient", "amount"} ], "currency" }
```
