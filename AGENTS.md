# Agents guide

This file is for **AI agents** (Claude Code, Codex, Aider, OpenCode, …) that
will be calling clibo on a user's machine. If you are a human contributor,
read [`docs/ADDING_A_TOOL.md`](docs/ADDING_A_TOOL.md) instead.

## What clibo is

A box of **50 local-first CLI tools** under one `clibo` command, all writing
to a single SQLite file at `~/.clibo/clibo.db`. There is no network, no
account, no cloud — installing clibo is enough.

Each tool is a sub-command: `clibo calorie`, `clibo crm`, `clibo todo`, … Run
`clibo info --json` for the full list, or `clibo <tool> --help` for any tool.

## The contract every command keeps

| Rule | Why it matters |
|---|---|
| Every command accepts `--json`. | Stdout becomes a clean, parseable JSON document. |
| Mutations return the affected record. | `add`/`log`/`edit` emit the created/updated object — no follow-up read required. |
| Deletes return `{"deleted": ID}`. | One-shot confirmation. |
| Errors go to **stderr** with non-zero exit code. | Use the exit code and read stderr to recover. |
| Verbs are predictable. | `add` (or a domain verb like `log`, `drink`, `take`), `list`, `show`, `edit`, `rm`, `stats`. |
| Free-form IDs accept names too. | Most tools resolve a positional argument as numeric ID *or* case-insensitive name (`clibo habit check "Read 10 pages"`). |
| Dates are forgiving. | `today`, `yesterday`, `tomorrow`, `YYYY-MM-DD`, `DD.MM`, `MM/DD`. |

## Three integrating commands you'll use a lot

```bash
clibo today --json    # one snapshot across 12 tools — fastest "what's going on?"
clibo search Q --json # full-text search across 22 text-bearing tables
clibo export --json   # dump the entire local state to one JSON document
```

`clibo doctor --json` returns `{"healthy": true, ...}` — use it as a smoke
check before doing real work.

## Per-tool skills

Every tool ships a micro-skill in [`skills/<tool>/SKILL.md`](skills/) with
YAML frontmatter compatible with Claude Code Skills. Each skill has:

- a `name` and `description` for skill-selection,
- a command table with flags,
- copy-paste examples,
- a **For agents** section that documents the exact JSON output.

If you can read one file from this repo to learn a tool, read its
`skills/<tool>/SKILL.md`.

## Common agent recipes

### Log a meal

```bash
clibo calorie log "oatmeal with berries" --kcal 320 --protein 12 --carbs 48 --fat 6 -m breakfast --json
```
Returns the created entry; check `data["id"]` if you need to edit it later.

### Find every mention of a topic

```bash
clibo search "acme" --json
```
Returns `{"query": "acme", "count": N, "results": [{"source", "id", "snippet"}, ...]}`.
`source` is the tool name; `id` is the row ID in that tool's table.

### Read the whole picture

```bash
clibo today --json                                   # everything actionable today
path=$(clibo export --json | jq -r .path); cat $path # entire DB as JSON (all tables)
```

`clibo export --json` returns `{"path", "tables", "rows"}` — the dump itself
is written to `path` so it can be reused later.

### Mutate by name without a separate lookup

```bash
clibo habit check "Read 10 pages" --json
clibo crm touch "Anna Petrova" --json
clibo savings deposit "Vacation" 200 --json
```

### Detect that clibo is installed and working

```bash
clibo doctor --json | jq .healthy   # → true
```

## Things to avoid

- **Don't shell out to `sqlite3` directly.** The schema may evolve between
  versions; use the CLI. If you need bulk reads, use `clibo export --json`.
- **Don't write the database file.** Use the CLI for mutations so triggers,
  defaults and timestamps stay consistent.
- **Don't assume timezone.** All dates are local-time, naive. Use the
  command's own date parsing instead of pre-formatting.
- **Don't pre-quote `--json`.** It's a plain flag.

## Versioning

Run `clibo --version` or read `clibo doctor --json | jq .version`. Major
versions follow semver — a 1.x bump means the JSON contract for any command
may have changed; minor bumps add new tools or fields.
