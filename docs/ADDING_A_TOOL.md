# 🛠️ Adding a clibo tool

Every clibo tool has the same shape. Copy [`clibo/clis/calorie.py`](../clibo/clis/calorie.py)
and adapt it. This document is the checklist.

## 1. The module — `clibo/clis/<tool>.py`

```python
"""<emoji> <tool> — one-line description."""
from __future__ import annotations
from datetime import date, datetime
import typer
from sqlmodel import Field, SQLModel, select
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "<tool>"                 # the sub-command name
HELP = "<emoji> Short help"     # shown in `clibo --help`
EMOJI = "<emoji>"

class <Model>(SQLModel, table=True):
    __tablename__ = "<tool>_<thing>"   # ALWAYS namespace the table
    id: int | None = Field(default=None, primary_key=True)
    # ... fields ...
    created_at: datetime = Field(default_factory=datetime.now)

app = typer.Typer(no_args_is_help=True, help=HELP)

# commands: add/list/show/edit/rm + tool-specific verbs + stats
```

### Rules

- **Table names are namespaced**: `<tool>_<thing>` (e.g. `crm_contact`). Never
  a bare name — all 50 tools share one database.
- **Every command takes `json_out: JsonOpt = False`** and routes output
  through `core.output` — never `print()` directly.
- **Verbs are consistent**: `add` (or a domain verb like `log`), `list`,
  `show`, `edit`, `rm`, `stats`. Use `name="list"` since `list` is a builtin.
- **Mutations return the record** via `ok(..., data=<dict>)`; `rm` returns
  `{"deleted": id}`; missing records call `fail(...)`.
- **Human output is emoji-rich**: titles like `"🍎 Food log"`, summary lines
  with emoji, progress bars via `output.bar()` where it fits.
- **Per-user config** goes in the shared store: `get_setting`/`set_setting`
  from `core.settings` — don't add a settings table per tool.
- Use `core.base.parse_date` for any date option (accepts `today`,
  `yesterday`, ISO, `DD.MM`).

## 2. Register it — `clibo/clis/__init__.py`

Add the import and append the module to `ALL`.

## 3. Tests — `tests/test_<tool>.py`

Use the `cli` fixture (`cli.run(...)`, `cli.json(...)`). Cover: create, a
read/list, the `--json` shape, `stats`, and at least one error path.

## 4. Skill — `skills/<tool>/SKILL.md`

YAML frontmatter (`name`, `description`) + a command table + examples + a
"For agents" section documenting the JSON output.

## 5. Finish

`pytest` must be green. Smoke-test the commands. Tick the box in `PLAN.md`,
log it in `PROGRESS.md`, update the README table, commit and push. Regenerate
the schema reference: `python scripts/dump_schema.py` →
[`docs/SCHEMA.md`](SCHEMA.md).
