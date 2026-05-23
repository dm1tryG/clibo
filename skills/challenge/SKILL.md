---
name: clibo-challenge
description: Time-boxed challenges with daily check-ins via `clibo challenge`. Distinct from `habit` — habits are open-ended, challenges have a target duration and a pass/fail outcome. Maps "30-day no-sugar challenge" to `clibo challenge start "no sugar" --days 30`.
---

# 🚀 clibo challenge

A challenge is a **time-boxed commitment with daily check-ins** and a
clear pass/fail outcome at the end — `100 days of code`, `Dry January`,
`30 days of no sugar`, `21-day cold-shower challenge`. This is the
distinction from `habit`: a habit is open-ended ("water every day,
forever"), a challenge ends.

A miss budget (default 0 = strict) lets you tolerate N missed days
before the challenge is auto-marked failed. Pass `--miss-budget 3`
for a 30-day challenge that survives up to 3 cheat days.

## Commands

| Command | What it does |
|---|---|
| `clibo challenge start NAME --days N [-m MISSES] [-D DESC]` | Start a new challenge |
| `clibo challenge check ID [--missed] [-n NOTE]` | Check in for today (default success) |
| `clibo challenge status [ID]` | Progress bars for active challenges |
| `clibo challenge today` | Pending check-ins for today only |
| `clibo challenge list [--all]` | Active by default; --all includes finished |
| `clibo challenge show ID` | Full detail incl. check-in history |
| `clibo challenge abandon ID` | Quit early (marked `abandoned`) |
| `clibo challenge rm ID` | Delete the challenge + its check-ins |
| `clibo challenge stats` | Total, completed, failed, completion rate |

## Auto-finalization

Whenever you look at a challenge, the tool checks:
- if misses exceed the miss budget → `failed`
- if the end date is past → `completed`

You don't have to "close" anything manually; status updates lazily.

## For agents

| User says | Command |
|---|---|
| "Starting 30 days of no sugar today" | `clibo challenge start "no sugar" --days 30` |
| "100 days of code — allow me 5 cheat days" | `clibo challenge start "100 days of code" --days 100 -m 5` |
| "I stuck to no-sugar today" | `clibo challenge check 1` |
| "I cheated today on no-sugar" | `clibo challenge check 1 --missed -n "had cake at office"` |
| "How am I doing on my challenges?" | `clibo challenge status` |
| "Quit the no-sugar challenge" | `clibo challenge abandon 1` |

```bash
clibo challenge status --json
# -> { "count", "challenges": [ {id, name, days_elapsed, days_remaining,
#       hits, misses, miss_budget_remaining, today_status, status, ...} ] }
```
