---
name: clibo-notes
description: Keep quick searchable notes with the `clibo notes` CLI. Use when the user wants to jot down a note, search their notes, pin an important one, or review them.
---

# 📝 clibo notes

Quick searchable notes. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo notes add TITLE -b BODY` | Create a note |
| `clibo notes list [-t TAG]` | List notes (pinned first, then newest) |
| `clibo notes show ID` | Show a note's full text |
| `clibo notes search QUERY` | Search titles and bodies |
| `clibo notes edit ID -b BODY` | Edit a note |
| `clibo notes pin ID` / `unpin ID` | Pin / unpin a note |
| `clibo notes rm ID` | Delete a note |
| `clibo notes stats` | Note counts |

`add` and `edit` take `-t/--tag` for comma-separated tags.

## Examples

```bash
clibo notes add "Project idea" -b "A box of 50 CLIs for AI agents" -t work
clibo notes search "CLI"
clibo notes pin 1
clibo notes show 1
```

## For agents

```bash
clibo notes search "flour" --json
# -> [ { "id", "title", "body", "preview", "tags" } ]
```

Each note record includes the full `body` and a short `preview`.
