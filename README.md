<div align="center">

# 📦 clibo

### 50 local-first CLI tools for AI agents — and humans

*From a calorie tracker to a CRM. Everything in your terminal, everything in one local SQLite file.*

[![CI](https://github.com/dm1tryG/clibo/actions/workflows/ci.yml/badge.svg)](https://github.com/dm1tryG/clibo/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Built with Typer](https://img.shields.io/badge/built%20with-Typer%20%2B%20SQLModel-0a7.svg)](https://typer.tiangolo.com/)

</div>

---

## Why clibo?

AI agents are great at *deciding* — but they need **tools** to *act*. The most
useful tools aren't fancy: they're the boring, everyday ones. Track calories.
Remember a contact. Add a task. Note an expense.

**clibo** is a box of 50 such tools, each a tiny CLI. They share three things
that make them perfect for agents *and* for you:

- 🗄️ **Local-first** — one SQLite file at `~/.clibo/clibo.db`. No cloud, no account, no setup.
- 🤖 **Agent-native** — every command speaks `--json`. Pretty tables for humans, clean JSON for machines.
- 🎯 **One predictable shape** — every tool uses the same verbs: `add`, `list`, `show`, `edit`, `rm`, `stats`.

```bash
clibo calorie log "oatmeal with berries" --kcal 320 --protein 12
clibo calorie today
clibo calorie today --json        # same data, for your agent
```

## Install

clibo installs as a single `clibo` command. Pick one:

```bash
# with uv (recommended)
uv tool install --from git+https://github.com/dm1tryG/clibo.git clibo

# or with pipx
pipx install git+https://github.com/dm1tryG/clibo.git

# or the one-liner
curl -fsSL https://raw.githubusercontent.com/dm1tryG/clibo/main/install.sh | bash
```

Then:

```bash
clibo --help          # the full menu
clibo info            # what's built, what's coming
clibo calorie --help  # any tool's help
```

## The 50 tools

> Built tools are ✅. The rest ship continuously — run `clibo info` for live status.

### 🏃 Health & Wellness
| | Tool | What it does |
|---|---|---|
| ✅ | `calorie` 🍎 | Food & calorie tracker with macros |
| ✅ | `water` 💧 | Daily water intake tracker |
| ✅ | `weight` ⚖️ | Body-weight log with BMI & trend |
| ✅ | `workout` 🏋️ | Exercise & gym session log |
| ✅ | `sleep` 😴 | Sleep duration & quality tracker |
| ✅ | `mood` 🙂 | Daily mood & emotion journal |
| ✅ | `meds` 💊 | Medication log & dosage reminders |
| ✅ | `period` 🌸 | Menstrual cycle tracker |
| ✅ | `meditate` 🧘 | Meditation & mindfulness sessions |
| ✅ | `vitals` ❤️ | Blood pressure, pulse & glucose log |

### 💰 Money & Finance
`expense` 💸 · `budget` 📊 · `subs` 🔁 · `bills` 🧾 · `savings` 🐷 · `debt` 📉 · `networth` 💰 · `invoice` 📄 · `split` 🤝 · `wishlist` ⭐

### ✅ Productivity & Work
`todo` ✅ · `notes` 📝 · `habit` 🔥 · `focus` 🍅 · `time` ⏱️ · `journal` 📔 · `goals` 🎯 · `events` 📅 · `worklog` 🗒️ · `bookmark` 🔖

### 🤝 CRM & Relationships
`crm` 👥 · `leads` 🧲 · `followup` 🔔 · `meetings` 🗓️ · `jobs` 💼 · `clients` 🧑‍💼 · `birthdays` 🎂 · `network` 🌐 · `gifts` 🎁 · `brag` 🏆

### 🏠 Home & Life
`groceries` 🛒 · `pantry` 🥫 · `recipes` 👨‍🍳 · `meals` 🍽️ · `chores` 🧹 · `plants` 🪴 · `car` 🚗 · `home` 🏠 · `pets` 🐾 · `travel` ✈️

## For AI agents

Every command accepts `--json` and returns structured data on stdout. Errors
go to stderr with a non-zero exit code. That's the whole contract.

```bash
$ clibo calorie today --json
{
  "date": "2026-05-22",
  "entries": [ { "id": 1, "meal": "breakfast", "food": "oatmeal", "kcal": 320, ... } ],
  "totals": { "kcal": 320, "protein": 12.0, "carbs": 48.0, "fat": 6.0 },
  "goal_kcal": 2000
}
```

Each tool also ships a **micro-skill** in [`skills/`](skills/) — a short
`SKILL.md` describing exactly what the tool does and how to call it, ready to
drop into an agent's skill set.

## Tech

Python · [Typer](https://typer.tiangolo.com/) · [SQLModel](https://sqlmodel.tiangolo.com/) · [Rich](https://rich.readthedocs.io/). One SQLite database. Zero external services.

```
clibo/
├── clibo/
│   ├── main.py          # root command, registers every tool
│   ├── catalog.py       # the canonical list of all 50 tools
│   ├── core/            # db, config, settings, output (the shared engine)
│   └── clis/            # one module per tool
├── skills/              # one micro-skill (SKILL.md) per tool
└── tests/               # pytest coverage for every tool
```

## Contributing & project status

clibo is built in the open, one tool at a time — see [`PLAN.md`](PLAN.md) for
the roadmap and [`PROGRESS.md`](PROGRESS.md) for the live log. Adding a tool
means following the shape of [`clibo/clis/calorie.py`](clibo/clis/calorie.py):
a SQLModel table, a Typer `app`, `--json` everywhere, tests, and a `SKILL.md`.

## License

[MIT](LICENSE) © 2026 dm1tryG
