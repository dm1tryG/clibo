<!--
Thanks for contributing! A small checklist keeps clibo consistent across all
50+ tools. Tick whatever applies; delete sections that don't.
-->

## What this PR does

<!-- One paragraph. -->

## Checklist

### For a new tool

- [ ] Module in `clibo/clis/<tool>.py` follows `docs/ADDING_A_TOOL.md`.
- [ ] Namespaced `__tablename__` (e.g. `<tool>_<thing>`).
- [ ] Every command accepts `--json` and uses `core.output` helpers.
- [ ] Registered in `clibo/clis/__init__.py` (imports **and** `ALL`).
- [ ] Tests at `tests/test_<tool>.py` cover create, list/show, `--json` shape, stats, an error path.
- [ ] Micro-skill at `skills/<tool>/SKILL.md` with frontmatter, commands, examples, and a *For agents* section.
- [ ] Box ticked in `PLAN.md`; entry appended to `PROGRESS.md`.

### Always

- [ ] `./.venv/bin/pytest` is green.
- [ ] Smoke-tested by hand, including `--json`.
- [ ] No `Co-Authored-By` trailer, no "Generated with …" line, no LLM mentions in commit messages.
