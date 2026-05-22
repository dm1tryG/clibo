---
name: clibo-bookmark
description: Save and search bookmarks with the `clibo bookmark` CLI. Use when the user wants to save a link, find a saved bookmark, mark favorites, or open a bookmark.
---

# 🔖 clibo bookmark

Bookmarks & link saver. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo bookmark add URL -t TITLE` | Save a bookmark (`--tag`, `-c` category) |
| `clibo bookmark list` | List bookmarks (`--tag`, `-c`, `-f` favorites) |
| `clibo bookmark show ID` | One bookmark in detail |
| `clibo bookmark search QUERY` | Search titles, URLs and tags |
| `clibo bookmark open ID` | Open a bookmark in the browser |
| `clibo bookmark fav ID` / `unfav ID` | Toggle favorite |
| `clibo bookmark rm ID` | Delete a bookmark |
| `clibo bookmark stats` | Counts by category |

## Examples

```bash
clibo bookmark add https://typer.tiangolo.com -t "Typer docs" --tag ref
clibo bookmark search typer
clibo bookmark fav 1
clibo bookmark list --favorites
```

## For agents

```bash
clibo bookmark search "docs" --json
# -> [ { "id", "title", "url", "tags", "category", "favorite" } ]
```

With `--json`, `open` returns the URL instead of launching a browser.
