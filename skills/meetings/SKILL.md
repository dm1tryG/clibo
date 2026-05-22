---
name: clibo-meetings
description: Record meeting notes and action items with the `clibo meetings` CLI. Use when the user wants to log a meeting, capture action items, mark them done, or see open actions across meetings.
---

# 🗓️ clibo meetings

Meeting notes & action items. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo meetings add TITLE` | Record a meeting (`-a` attendees, `-N` notes) |
| `clibo meetings list --days 30` | Recent meetings |
| `clibo meetings show MEETING` | A meeting with notes and action items |
| `clibo meetings action MEETING SUMMARY` | Add an action item (`-o` owner) |
| `clibo meetings check ACTION_ID` | Mark an action item done |
| `clibo meetings actions` | All open action items across meetings |
| `clibo meetings rm ID` | Delete a meeting and its actions |
| `clibo meetings stats` | Meeting and action-item counts |

`MEETING` accepts a meeting title or numeric ID.

## Examples

```bash
clibo meetings add "Q2 Planning" -a "Anna,Bob" -N "Discussed the roadmap"
clibo meetings action "Q2 Planning" "Draft the spec" -o Anna
clibo meetings actions
clibo meetings check 1
```

## For agents

```bash
clibo meetings show "Q2 Planning" --json
# -> { "id", "title", "meeting_date", "attendees", "notes",
#      "actions": [ {"id","summary","owner","done"} ] }
```
