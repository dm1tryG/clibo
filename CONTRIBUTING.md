# Contributing to clibo

Thanks for thinking about contributing — clibo is built to grow.

## Quick setup

```bash
git clone https://github.com/dm1tryG/clibo.git
cd clibo
uv venv .venv             # or python -m venv .venv
uv pip install --python .venv -e ".[dev]"
./.venv/bin/pytest        # 300+ tests
./.venv/bin/ruff check    # lint
```

CI runs both `ruff check` and `pytest` — keep both green locally before opening
a PR. Ruff config lives in `pyproject.toml`.

The full developer guide for adding a new clibo tool lives at
[`docs/ADDING_A_TOOL.md`](docs/ADDING_A_TOOL.md) — read it before you start.
[`clibo/clis/calorie.py`](clibo/clis/calorie.py) is the canonical reference.
[`docs/SCHEMA.md`](docs/SCHEMA.md) lists every existing table; regenerate it
with `python scripts/dump_schema.py` after adding a new model.

## What a "done" tool looks like

A tool is not done until **all four** of these are true:

1. The module in `clibo/clis/<tool>.py` follows the pattern in
   `docs/ADDING_A_TOOL.md`: namespaced table name, Typer `app`, predictable
   verbs, `--json` on every command, output routed through `core.output`.
2. It is registered in `clibo/clis/__init__.py` (both the import block and
   the `ALL` list).
3. There is a pytest file at `tests/test_<tool>.py` that covers create, a
   read/list, the `--json` shape, `stats`, and at least one error path.
4. There is a micro-skill at `skills/<tool>/SKILL.md` with the YAML
   frontmatter (`name`, `description`), a command table, examples, and a
   **For agents** section documenting the JSON output.

`./.venv/bin/pytest` must be green. Smoke-test the new tool by hand,
including `--json`, before opening a PR.

## Commit messages

Plain, present-tense, one short subject line. No `Co-Authored-By` trailers,
no "Generated with …" lines, no mentions of any LLM.

## PR checklist

A short [pull-request template](.github/pull_request_template.md) is
auto-filled when you open a PR — please tick the boxes honestly.

## Releasing (maintainers)

Cutting a new version is one command on a clean `main`:

1. Bump `version` in `pyproject.toml` **and** `__version__` in
   `clibo/__init__.py`.
2. Add a `## [X.Y.Z] — YYYY-MM-DD` section at the top of `CHANGELOG.md`.
3. Commit the bump, then:

   ```bash
   git tag -a vX.Y.Z -m "clibo vX.Y.Z"
   git push origin main --follow-tags
   ```

The [`Release` workflow](.github/workflows/release.yml) takes it from there:
builds the wheel and sdist, sanity-checks the tag matches the pyproject
version, creates the GitHub release, attaches the artifacts, and (if the
`PYPI_API_TOKEN` repo secret is set) publishes to PyPI.

## Code of conduct

Be kind. Assume good faith. We follow the
[Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)
in spirit; no formal document needed at this size.
