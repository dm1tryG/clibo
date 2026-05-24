---
name: clibo-meetings
description: Record meeting notes and action items with the `clibo meetings` CLI. Use when the user mentions a call/meeting, discussion points, or action items. The natural flow — "we discussed X, Bob will do Y" — works in one command via inline `-A` flags.
---

# 🗓️ clibo meetings

Meeting notes & action items. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo meetings add TITLE` | Record a meeting (`-a` attendees, `-N` notes, **`-A` action items**) |
| `clibo meetings action MEETING SUMMARY` | Add an action item later (`-o` owner) |
| `clibo meetings edit MEETING` | Update title / date / attendees / notes |
| `clibo meetings show MEETING` | Meeting with notes + action items |
| `clibo meetings list --days 30` | Recent meetings |
| `clibo meetings check ACTION_ID` | Mark an action item done |
| `clibo meetings actions` | All open action items across meetings |
| `clibo meetings rm MEETING` | Delete a meeting (cascades action items) |
| `clibo meetings stats` | Meeting and action-item counts |

`MEETING` accepts a meeting title (fuzzy substring match, most-recent
wins) or numeric ID.

## Inline action items at creation

The natural flow is *"we discussed X, here's who's doing Y"* — both in
the same breath. Pass `--action` / `-A` one or more times on `add`:

```bash
clibo meetings add "Acme Q3 roadmap" \
  -a "Bob,Alice,me" \
  -N "Discussed Q3 priorities" \
  -A "Bob: send timeline" \
  -A "Alice: draft proposal" \
  -A "me: schedule the follow-up"
```

Each `-A` accepts plain text or `OWNER: summary` to set the owner
inline. Empty strings are silently skipped.

## Natural language → command

| User says | Command |
|---|---|
| "Just finished a Zoom with Acme — discussed Q3, Bob to send timeline" | `clibo meetings add "Acme Q3" -a Acme -N "discussed Q3" -A "Bob: send timeline"` |
| "Add an action item to the Acme meeting" | `clibo meetings action Acme "review the contract" -o me` |
| "What action items are open?" | `clibo meetings actions` |
| "Bob sent the timeline — mark that done" | `clibo meetings check <id>` |
| "Show me the Acme meeting" | `clibo meetings show Acme` |
| "Delete the cancelled meeting" | `clibo meetings rm "cancelled"` |

## For agents

```bash
clibo meetings add "Acme Q3" -A "Bob: send timeline" --json
# -> { "id", "title", "meeting_date", "attendees", "notes",
#      "action_items": 1, "open_actions": 1 }

clibo meetings show "Acme" --json
# -> { ..., "actions": [ {"id","summary","owner","done"} ] }
```

`MEETING` arguments on `action`, `show`, `edit`, `rm` all resolve via
ID → exact title → substring (most-recent wins). The agent doesn't need
to know the exact title or the numeric ID — partial matches work.
