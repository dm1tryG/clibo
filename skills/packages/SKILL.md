---
name: clibo-packages
description: Shipment & parcel tracker via `clibo packages`. The daily-driver view is `packages pending` — what's still on its way, sorted with late deliveries first. Maps "Amazon order on the way, expected Tuesday" to `clibo packages add Amazon -e "Tuesday" -D "<item>"`.
---

# 📦 clibo packages

Track parcels and online orders from when you place them to when they
arrive. Distinct from `bills` (recurring money out), `events` (date with
no logistical state), `wishlist` (things you want, not in transit).

Status progresses: **`ordered`** → **`in_transit`** → **`delivered`**, with
branches to `lost` or `returned`.

## Commands

| Command | What it does |
|---|---|
| `clibo packages add SENDER [-t TRACK] [-c CARRIER] [-e EXPECTED] [-D DESC]` | Register a new package |
| `clibo packages log ...` | Alias for `add` |
| `clibo packages pending [--late]` | The daily-driver view — late first, then by ETA |
| `clibo packages received ID` | Mark delivered (sets `received_date`) |
| `clibo packages update ID [-s STATUS] [-e EXPECTED] [-t TRACK]` | Update fields |
| `clibo packages list [-s STATUS] [-c CARRIER] [--all]` | Active by default; --all includes resolved |
| `clibo packages show ID` | Full detail incl. days outstanding and late flag |
| `clibo packages rm ID` | Delete |
| `clibo packages stats` | By status, by carrier, on-time vs late, avg delivery days |

`STATUS` is one of `ordered`, `in_transit`, `delivered`, `lost`, `returned`.
`CARRIER` is free text — common values: `usps`, `ups`, `fedex`, `dhl`,
`amazon`, `royal-mail`, `deutsche-post`, `la-poste`, `other`.

## For agents

| User says | Command |
|---|---|
| "Amazon order placed, expected Tuesday" | `clibo packages add Amazon -e Tuesday` |
| "Tracked: USPS 9400... arriving in 3 days" | `clibo packages add Sender -t "9400..." -c usps -e "in 3 days"` |
| "Got the FedEx package today" | `clibo packages received 1` |
| "FedEx delay — now expected Friday" | `clibo packages update 1 -e "Friday"` |
| "What packages am I waiting on?" | `clibo packages pending` |
| "Anything late?" | `clibo packages pending --late` |

```bash
clibo packages pending --json
# -> list of {id, sender, description, carrier, expected_date,
#    expected_in, is_late, days_outstanding, tracking_number, ...}
```
