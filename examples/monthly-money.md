# 💰 End-of-month money rollup

The case: it's the last day of the month. You want a single command that
tells you whether you spent more than you earned, where the money went,
and how this month compares to last.

## 1. The money-first view

```bash
clibo month
```

Layout:

```
🗓️  May 2026   Fri 01 → Sun 31 May   (31 days)

💰 Money
  💵 Income       5800.00 USD   ·   2 entries
  💸 Expenses     2280.00 USD   ·   4 entries   ·   top: housing (1800.00 USD)
  ❤️ Donations    75.00 USD     ·   2 gifts
  🧾 Bills        paid 1 (120.00 USD)   ·   1 unpaid (75.00 USD)
  🔁 Subs         active monthly cost ~33.25 USD
  📈 Invest       2 transactions   ·   buys 5800.00 USD
  ──  Net cash flow 3325.00 USD
```

**Net cash flow** is the headline number — income minus expenses, minus
donations, minus paid bills. Positive in green, negative in red.

## 2. Look at a past month

```bash
clibo month -y 2026 -m 4    # April 2026
clibo month -y 2025 -m 12   # December 2025
```

## 3. Drill into expense categories

```bash
clibo expense stats --days 30
```

Top categories. The new `Chart` sparkline shows your daily spending shape
over the window — spikes are visible at a glance.

## 4. Tax-deductible giving for this year

```bash
clibo donations year
```

Annual summary with **deductible_total** broken out separately from
non-deductible (political contributions, GoFundMe-to-individuals).
Ready for tax filing.

## 5. Portfolio check

```bash
clibo invest positions
```

Roll-up of every holding with avg cost basis, current price (manually
updated), market value, and green/red unrealized P/L.

```bash
clibo invest price AAPL 220       # update current price
clibo invest stats                 # lifetime realized + unrealized
```

## 6. Subscription audit

```bash
clibo subs list --active
```

Anything you're paying for that you don't actually use? `subs rm ID`.

## 7. Bills due next month

```bash
clibo bills due --days 35
```

Set follow-ups, calendar reminders, or just pay them now.

## 8. The "could I save more?" question

```bash
clibo compare    # week-over-week — sustained savings shows up here
clibo expense stats --days 90    # 3-month chart
```

---

**Why this works**: month is calendar-anchored (Jan 1 → Jan 31, not "last 30
days"), which matches how rent, salary, and bills actually flow. Net cash
flow is computed correctly only when income exists — it doesn't lie when
you've only logged outflows.
