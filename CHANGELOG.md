# Changelog

All notable changes to **clibo** are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
follows [Semantic Versioning](https://semver.org/).

## [Unreleased] — staged for `v1.1.0`

Eight polish iterations have landed on `main` since `v1.0.0`. They are tagged
and shipped by pushing a `v1.1.0` tag — the
[`Release` workflow](.github/workflows/release.yml) handles the rest.

### Added — new cross-tool commands

- 🚀 `clibo init` — one-shot onboarding. Sets the shared currency plus daily
  goals for calories, water, focus, sleep and meditation in a single call.
- 🗓️ `clibo week` — sister to `clibo today`. A 7-day rollup across sleep,
  calories, water, focus, mood, habits (vs each habit's weekly target),
  expenses (with top category) and productivity (tasks/journal/worklog).
- 🩺 `clibo doctor` — install health check: version, Python, tools built,
  database size and per-table row counts; `--json` returns a `healthy` bool.
- 📥 `clibo import PATH` — counterpart to `clibo export`. Loads a JSON dump
  back into the live database (`INSERT OR IGNORE` by default, `--replace`
  for a clean overwrite). Accepts both the v1 envelope and a bare
  `{table: [rows]}` map.

### Added — documentation & ergonomics

- 📝 `AGENTS.md` at the repo root: one-page agent guide with the universal
  contract, integrating commands, copy-paste recipes and pitfalls.
- 📁 `examples/` directory: `daily_brief.py`/`daily_brief.sh` (combine
  `today` + `week` into a Markdown brief) and `find_and_act.py` (the
  search-then-act agent pattern). All smoke-tested end-to-end.
- 🛠️ `CONTRIBUTING.md` and `.github/{ISSUE_TEMPLATE,pull_request_template}.md`
  — the four-part "done" definition for new tools, plus a maintainer
  Releasing section.
- 🤖 `.github/workflows/release.yml` — automated release on `v*.*.*` tag
  push: builds wheel + sdist, sanity-checks the tag matches `pyproject`'s
  version, creates the GitHub release with artifacts, and publishes to
  PyPI when the `PYPI_API_TOKEN` repo secret is set.
- 📦 Wheel and sdist attached to the GitHub release page.

### Tests

- 319 passing (up from 299 at v1.0.0).

[Unreleased]: https://github.com/dm1tryG/clibo/compare/v1.0.0...HEAD

## [1.0.0] — 2026-05-23

The first stable release. All 50 planned tools are shipped, every command
supports a `--json` mode for AI agents, and the project carries 299 tests.

### Added — 50 local-first CLI tools, in 5 categories

- **🏃 Health & Wellness** — `calorie`, `water`, `weight`, `workout`,
  `sleep`, `mood`, `meds`, `period`, `meditate`, `vitals`.
- **💰 Money & Finance** — `expense`, `budget`, `subs`, `bills`, `savings`,
  `debt`, `networth`, `invoice`, `split`, `wishlist`.
- **✅ Productivity & Work** — `todo`, `notes`, `habit`, `focus`, `time`,
  `journal`, `goals`, `events`, `worklog`, `bookmark`.
- **🤝 CRM & Relationships** — `crm`, `leads`, `followup`, `meetings`,
  `jobs`, `clients`, `birthdays`, `network`, `gifts`, `brag`.
- **🏠 Home & Life** — `groceries`, `pantry`, `recipes`, `meals`, `chores`,
  `plants`, `car`, `home`, `pets`, `travel`.

### Added — Cross-tool commands

- `clibo today` — a one-screen dashboard pulling from 12 tools at once:
  overdue/today tasks, habit check-offs, water/calorie/focus progress bars,
  today's events and meals, bills due, follow-ups, plants needing water,
  chores due, and today's birthdays.
- `clibo search QUERY` — one query across 13 text-bearing tables (notes,
  journal, todo, bookmark, crm, network, meetings, brag, recipes, worklog,
  gifts, expense, wishlist).
- `clibo backup [PATH]` / `clibo restore PATH` — file-level SQLite backup
  and restore, with timestamped defaults under `~/.clibo/backups/`.
- `clibo export [PATH]` — dump every clibo table to one JSON file,
  ideal for an agent to read the whole local state in one go.
- `clibo info` — progress dashboard for the project itself.

### Added — Agent-native contract

- Every command accepts `--json` for machine-readable output on stdout.
- Mutations return the affected record as JSON; deletes return
  `{"deleted": ID}`; errors go to stderr with a non-zero exit code.
- One micro-skill (`SKILL.md`) per tool in `skills/`, ready to drop into
  an AI agent's skill set.

### Added — Engineering

- Stack: Python 3.10+ · [Typer](https://typer.tiangolo.com/) ·
  [SQLModel](https://sqlmodel.tiangolo.com/) · [Rich](https://rich.readthedocs.io/).
- One SQLite file at `~/.clibo/clibo.db` (`CLIBO_HOME` / `CLIBO_DB` override).
- 299 pytest tests covering every tool and the cross-tool commands.
- GitHub Actions CI on Python 3.10/3.11/3.12.
- MIT licensed.

### Install

```bash
uv tool install --from git+https://github.com/dm1tryG/clibo.git clibo
# or
pipx install git+https://github.com/dm1tryG/clibo.git
```

[1.0.0]: https://github.com/dm1tryG/clibo/releases/tag/v1.0.0
