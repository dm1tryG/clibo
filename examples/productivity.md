# ✅ Productivity

Tools covered: `todo`, `focus`, `habit`, `challenge`, `journal`, `worklog`,
`notes`, `goals`, `bookmark`, `ideas`, `events`, `followup`.

## The morning triage

```bash
clibo today                            # what's overdue + due today
clibo todo list --pending              # the backlog
clibo events upcoming --days 7         # this week's calendar
```

## Capture-fast

Three lightweight inboxes — log first, organise never:

```bash
clibo notes add "API rate limits" -b "Stripe: 100 req/s, GitHub: 5000/hr" -t reference
clibo ideas add "clibo plugins" -d "let third parties add tools" -s raw
clibo bookmark add "https://example.com/article" -t "Long-form on CRDTs" --tag ai
```

## Focus blocks

```bash
clibo focus timer 25                   # live pomodoro timer
clibo focus log 90                     # backfill a 90-min block
clibo focus stats --days 7
```

## Habits

```bash
clibo habit add "Read 30 min"
clibo habit check "Read 30 min"
clibo habit today                      # what's still open today
clibo habit stats "Read 30 min"        # streak, completion %
```

## Challenges (bounded vs. open-ended)

A challenge is a habit with a target duration and a pass/fail outcome.

```bash
clibo challenge start "no sugar" --days 30
clibo challenge start "100 days of code" --days 100 -m 5    # allow 5 misses
clibo challenge check 1                  # today's check-in
clibo challenge check 2 --missed -n "had cake"
clibo challenge status                   # progress bars + miss budget
```

## Journal + worklog

```bash
clibo journal write "..."                # free-form daily entry
clibo worklog done "Shipped auth refactor"
clibo worklog blocked "Waiting on infra review"
```

## Tasks

```bash
clibo todo add "Email Stripe" -p high -d "in 3 days"
clibo todo done 1
clibo todo undone 1
clibo todo stats
```

## Goals + milestones

```bash
clibo goals add "Ship v2 by July" -d "2026-07-01"
clibo goals milestone "Ship v2" "Auth refactor merged"
clibo goals show "Ship v2"
```

## Cross-cutting questions

```bash
clibo search "auth"                    # search across notes/todo/bookmarks/...
clibo recent -n 20                     # chronological feed across all tools
clibo tags                             # every tag used + counts
clibo streaks                          # every active streak
```
