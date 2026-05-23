# 💰 Money & finance tracking

Tools covered: `expense`, `income`, `bills`, `subs`, `donations`, `invest`,
`debt`, `tip`, `wishlist`, `budget`, `networth`, `invoice`, `savings`,
`split`.

## Daily money

```bash
clibo expense add "lunch" -a 12.50 -c food
clibo expense add "gas" -a 45 -c transport -d yesterday
clibo income add "freelance gig" -a 800 -c freelance
clibo tip log 40 -p 20 -v "Joe's Diner" -r 5    # 20% tip on a $40 bill
```

## Recurring obligations

```bash
clibo subs add "Netflix" -a 15                     # default monthly
clibo subs add "iCloud Storage" -a 99 -c yearly    # rolled up to monthly cost
clibo bills add "Rent" -a 1800 -d "2026-06-01"
clibo bills pay 1                                  # mark paid
```

## Tax-aware giving

```bash
clibo donations log "Red Cross" -a 50
clibo donations log "Political PAC" -a 100 --no-deductible
clibo donations year                               # annual summary
clibo donations top                                # most-supported orgs
```

The `year` view separates `deductible_total` from `non_deductible_total` —
exactly what your tax software wants.

## Investments

Local-first portfolio with cost-basis tracking. No live prices (clibo never
makes network calls); you update prices manually for unrealized P/L.

```bash
clibo invest buy AAPL 5 200                # 5 shares @ $200
clibo invest buy AAPL 3 220                # avg cost basis rolls up
clibo invest buy BTC 0.5 42000 -k crypto
clibo invest sell AAPL 2 250               # prints realized P/L
clibo invest price AAPL 220                # update current price
clibo invest positions                     # holdings, value, unrealized P/L
clibo invest show AAPL                     # drill into one ticker
```

## Owe / owed

```bash
clibo debt add Anna -a 50 -n "split dinner"   # I owe Anna
clibo debt pay 1 20                            # paid back $20
clibo debt list
```

## Shared expenses (Splitwise-style)

```bash
clibo split add "AirBnB" -a 600 -p Alice,Bob,Eve --paid-by Alice
clibo split balances                           # who owes who
clibo split who                                # minimal-payments suggestion
```

## End of month

```bash
clibo month                                    # money block first
clibo expense stats --days 30                  # has a Chart sparkline
clibo donations year
clibo subs list --active                       # audit subscriptions
clibo bills due --days 30                      # what's coming up
clibo invest stats                             # portfolio summary
clibo networth worth                           # assets - liabilities
```

## The agent flow

"I spent $35 at Starbucks today" →

```bash
clibo expense add "Starbucks" -a 35 -c food
```

"I tipped 20% on a $40 dinner" →

```bash
clibo tip log 40 -p 20
```

"How much should I tip on $35 at 20%?" (no save) →

```bash
clibo tip calc 35 -p 20
```

## Multi-currency

Set the active currency once:

```bash
clibo set money currency EUR
```

Every money tool reads that setting and formats with the right code.
