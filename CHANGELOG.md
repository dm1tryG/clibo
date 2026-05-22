# Changelog

All notable changes to **clibo** are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
follows [Semantic Versioning](https://semver.org/).

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
