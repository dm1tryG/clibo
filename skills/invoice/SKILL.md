---
name: clibo-invoice
description: Create and manage freelance invoices with the `clibo invoice` CLI. Use when the user wants to generate an invoice for a client, mark it sent or paid, render an invoice document, or review billed vs outstanding amounts.
---

# 📄 clibo invoice

Freelance invoice generator. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo invoice add CLIENT -a AMOUNT` | Create an invoice (auto-numbered) |
| `clibo invoice list [-s STATUS]` | List invoices |
| `clibo invoice show ID` | Invoice details |
| `clibo invoice render ID` | Print a formatted invoice document |
| `clibo invoice send ID` | Mark an invoice as sent |
| `clibo invoice pay ID` | Mark an invoice as paid |
| `clibo invoice rm ID` | Delete an invoice |
| `clibo invoice stats` | Billed, paid and outstanding totals |

`add` also takes `--desc`, `--tax PCT`, `--due DATE`, `--issued DATE`.
Invoices are numbered `INV-0001`, `INV-0002`, … and flow
`draft → sent → paid`.

## Examples

```bash
clibo invoice add "Acme Inc" -a 1500 --tax 20 --desc "Website redesign" --due 2026-06-15
clibo invoice render 1
clibo invoice send 1
clibo invoice pay 1
```

## For agents

```bash
clibo invoice stats --json
# -> { "invoices", "total_billed", "total_paid", "total_outstanding",
#      "paid_count", "outstanding_count", "currency" }
```

Every invoice record includes `amount` (subtotal), `tax_pct` and `total`.
