---
name: clibo-invest
description: Track investment positions with `clibo invest` — buys, sells, current price and unrealized P/L. Distinct from `networth` (single-value asset rows) by storing transactions and computing positions. Local-first — no live price feeds; update prices manually with `invest price TICKER X`. Maps "Bought 5 AAPL at $200" to `clibo invest buy AAPL 5 200`.
---

# 📈 clibo invest

Investment portfolio tracker for stocks, ETFs, crypto, bonds, funds. Stores
*transactions*; positions and P/L are derived. Local-first — no live price
feeds — but `invest price TICKER X` updates the latest known price so
unrealized P/L is whatever you want it to be.

Realized P/L on sells uses **average cost basis** (simplest defensible
model; FIFO/specific-lot is a future-iteration upgrade).

## Commands

| Command | What it does |
|---|---|
| `clibo invest buy TICKER SHARES PRICE [-k KIND] [-d DATE]` | Log a purchase |
| `clibo invest sell TICKER SHARES PRICE [-d DATE]` | Log a sale (computes realized P/L) |
| `clibo invest price TICKER PRICE` | Update current price for unrealized P/L |
| `clibo invest positions` | Net holdings — shares, avg cost, market value, P/L |
| `clibo invest history [-t TICKER] [--days N]` | Transaction log |
| `clibo invest show TICKER` | One ticker: position + every transaction |
| `clibo invest rm ID` | Delete a transaction |
| `clibo invest stats` | Total invested, realized + unrealized P/L, by kind |

`KIND` is one of: `stock`, `etf`, `crypto`, `bond`, `fund`, `other`.

## For agents

| User says | Command |
|---|---|
| "Bought 5 shares of AAPL at $200" | `clibo invest buy AAPL 5 200` |
| "Bought 0.5 BTC at $42,000" | `clibo invest buy BTC 0.5 42000 -k crypto` |
| "10 SPY at $480 last month" | `clibo invest buy SPY 10 480 -k etf -d "1 month ago"` |
| "Sold 2 AAPL at $250" | `clibo invest sell AAPL 2 250` |
| "AAPL is at $220 now" | `clibo invest price AAPL 220` |
| "What's my portfolio worth?" | `clibo invest positions` (or `stats`) |
| "Show me all my AAPL trades" | `clibo invest show AAPL` |

```bash
clibo invest positions --json
# -> a list of positions, each with: ticker, kind, shares, avg_cost,
#    cost_basis, current_price (or null), market_value, unrealized_pl
```

> ⚠️ This is bookkeeping, not financial advice. Update prices yourself —
> clibo never makes network calls.
