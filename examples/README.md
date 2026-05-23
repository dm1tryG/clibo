# clibo examples

Working scripts you can copy. They're written to be **starting points**, not
finished products — each is short enough to read top-to-bottom and adapt to
your own workflow.

| File | What it shows |
|---|---|
| [`daily_brief.py`](daily_brief.py) | Python: subprocess to clibo, JSON parsing, combining `today` + `week`, printing a Markdown brief. |
| [`daily_brief.sh`](daily_brief.sh) | Bash: the same brief using `jq`. |
| [`find_and_act.py`](find_and_act.py) | Python agent pattern: `search` to find something, then act on it (e.g. follow up on a contact). |

All examples assume `clibo` is on your `$PATH`. Set `CLIBO_HOME=/tmp/sandbox`
to play in a throwaway database.

## The contract these examples rely on

- Every command supports `--json` → clean stdout JSON.
- Mutations return the affected record (`clibo todo add ... --json`).
- Errors go to stderr with a non-zero exit code, so subprocess `check=True`
  surfaces them.
- Names work in place of numeric IDs for most resolve-by-name commands.

See [`AGENTS.md`](../AGENTS.md) at the repo root for the full contract.
