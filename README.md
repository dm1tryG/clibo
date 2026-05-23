<div align="center">

# 📦 clibo

### 50+ local-first CLI tools for AI agents — and humans

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
clibo init --currency USD --calorie-goal 2000 --water-goal-ml 2500  # one-shot onboarding
clibo --help          # the full menu
clibo today           # a dashboard of everything actionable today
clibo info            # what's built, what's coming
clibo calorie --help  # any tool's help
```

## Demos

[`scripts/demo.sh`](scripts/demo.sh) populates a throwaway database and runs
the showcase commands — perfect for recording an asciinema or for seeing
what clibo actually looks like:

```bash
CLIBO=./.venv/bin/clibo bash scripts/demo.sh
```

### 📅 `clibo today`

```
📅 Today · Saturday 23 May 2026

✅ Tasks
  ● today    Ship clibo v1  (high)

🔥 Habits  1/2 done
  ✓ Read 10 pages
  ○ Exercise

  💧 Water    ███████░░░░░░░░░░░  38%  750/2000 ml
  🍎 Calories ████████░░░░░░░░░░  42%  845/2000 kcal
  🍅 Focus    █████████░░░░░░░░░  50%  45/90 min

📅 Events
  10:00  Team standup

🧾 Bills due
  ⚠ overdue  Electricity  (2026-05-22)

🪴 Plants needing water
  Basil  (kitchen)
```

### 🍎 `clibo calorie today`

```
🍎 Food log · Sat 23 May
╭──────────┬──────────────────────┬──────┬─────┬─────┬────╮
│Meal      │ Food                 │ Kcal │ P·g │ C·g │ F·g│
├──────────┼──────────────────────┼──────┼─────┼─────┼────┤
│breakfast │ oatmeal with berries │ 320  │ 12  │ 48  │ 6  │
│breakfast │ black coffee         │ 5    │ 0   │ 0   │ 0  │
│lunch     │ chicken salad        │ 520  │ 38  │ 22  │ 24 │
╰──────────┴──────────────────────┴──────┴─────┴─────┴────╯
🔥 845 kcal    🥩 50g    🍚 70g    🧈 30g
🎯 ██████████░░░░░░░░░░░░░░  42%  845/2000 kcal
```

### 🧲 `clibo leads pipeline`

```
📊 Pipeline
╭──────────┬───────┬────────────────────────────────────╮
│Stage     │ Deals │ Value                              │
├──────────┼───────┼────────────────────────────────────┤
│qualified │ 1     │ 4000.00 USD  ████░░░░░░░░░░░░  25% │
│proposal  │ 1     │ 12000.00 USD  ████████████░░░░  75%│
╰──────────┴───────┴────────────────────────────────────╯
  💰 Open pipeline value: 16000.00 USD
```

### 🔍 `clibo search acme`

```
🔍 3 matches for 'acme'

notes  (1)            todo  (1)              crm  (1)
╭────┬───────────────╮ ╭────┬──────────────╮ ╭────┬────────────────────────╮
│ID  │ Match         │ │ID  │ Match        │ │ID  │ Match                  │
├────┼───────────────┤ ├────┼──────────────┤ ├────┼────────────────────────┤
│1   │ Acme contract │ │2   │ Reply to Acme│ │1   │ Anna Petrova · Acme Inc│
╰────┴───────────────╯ ╰────┴──────────────╯ ╰────┴────────────────────────╯
```

## Cross-tool commands

A handful of root commands tie all 50 tools together:

| Command | What it does |
|---|---|
| `clibo init` | Set common defaults in one call — currency, height (for BMI), calorie/water/focus/sleep/meditation goals. |
| `clibo today` | A one-screen dashboard pulling from every tool — tasks, habits, meals, events, bills, water/calorie/focus progress, plants & chores due, today's birthdays. |
| `clibo week` | 7-day rollup: sleep avg & quality, focus minutes, habit progress vs target, expenses by category, tasks completed, journal entries. |
| `clibo recent` | A chronological activity feed across every tool — newest first, with relative timestamps ("just now", "yesterday"). |
| `clibo backup [PATH]` | Copy the local SQLite database to a timestamped `.db` backup (default: `~/.clibo/backups/`). |
| `clibo restore PATH` | Replace the live database with a backup. |
| `clibo export [PATH]` | Dump every clibo table to one JSON file — ideal for an agent to read the whole local state in one go. |
| `clibo import PATH` | Load rows from a `clibo export` JSON file; `--replace` wipes each table first. |
| `clibo search QUERY` | One query across notes, journal, tasks, bookmarks, contacts, meetings, achievements, recipes, worklog, network, gifts, expenses and the wishlist. |
| `clibo tags` | Every tag used across notes, todo, bookmark, crm, brag, recipes and journal — with counts and source breakdown. |
| `clibo doctor` | Health check — version, paths, DB size and row counts per table. |

## Shell completion

clibo ships with completion for `bash`, `zsh` and `fish` — Typer wires it up
for you. Install it once:

```bash
clibo --install-completion          # auto-detects your shell
clibo --install-completion zsh      # or pick one explicitly
clibo --show-completion             # print the script (don't install)
```

Then re-open the shell. You'll get tab-completion for every tool, every
sub-command and every flag.

## The tools

> 🎉 **All 50 tools are built.** Run `clibo info` for a live menu.

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
| | Tool | What it does |
|---|---|---|
| ✅ | `expense` 💸 | Personal expense tracker |
| ✅ | `budget` 📊 | Monthly budgets by category |
| ✅ | `subs` 🔁 | Recurring subscriptions tracker |
| ✅ | `bills` 🧾 | Bills & due-date reminders |
| ✅ | `savings` 🐷 | Savings goals with progress |
| ✅ | `debt` 📉 | Debt & loan payoff tracker |
| ✅ | `networth` 💰 | Assets, liabilities & net worth |
| ✅ | `invoice` 📄 | Freelance invoice generator |
| ✅ | `split` 🤝 | Split shared expenses with people |
| ✅ | `wishlist` ⭐ | Things-to-buy wishlist with prices |
| ✅ | `income` 💵 | Income tracker — counterpart to expense |

### ✅ Productivity & Work
| | Tool | What it does |
|---|---|---|
| ✅ | `todo` ✅ | Task & to-do manager |
| ✅ | `notes` 📝 | Quick searchable notes |
| ✅ | `habit` 🔥 | Habit tracker with streaks |
| ✅ | `focus` 🍅 | Pomodoro & focus sessions |
| ✅ | `time` ⏱️ | Time tracking by project |
| ✅ | `journal` 📔 | Daily journal & diary |
| ✅ | `goals` 🎯 | Goals & OKRs with milestones |
| ✅ | `events` 📅 | Events & reminders calendar |
| ✅ | `worklog` 🗒️ | Work log & standup notes |
| ✅ | `bookmark` 🔖 | Bookmarks & link saver |

### 🤝 CRM & Relationships
| | Tool | What it does |
|---|---|---|
| ✅ | `crm` 👥 | Contacts CRM |
| ✅ | `leads` 🧲 | Sales pipeline & deals |
| ✅ | `followup` 🔔 | Follow-up reminders for people |
| ✅ | `meetings` 🗓️ | Meeting notes & action items |
| ✅ | `jobs` 💼 | Job application tracker |
| ✅ | `clients` 🧑‍💼 | Freelance client manager |
| ✅ | `birthdays` 🎂 | Birthday & anniversary reminders |
| ✅ | `network` 🌐 | Networking & people-you-met log |
| ✅ | `gifts` 🎁 | Gift ideas & giving tracker |
| ✅ | `brag` 🏆 | Achievement log for reviews |

### 🏠 Home & Life
| | Tool | What it does |
|---|---|---|
| ✅ | `groceries` 🛒 | Grocery & shopping list |
| ✅ | `pantry` 🥫 | Food inventory with expiry dates |
| ✅ | `recipes` 👨‍🍳 | Personal recipe book |
| ✅ | `meals` 🍽️ | Weekly meal planner |
| ✅ | `chores` 🧹 | Household chores rotation |
| ✅ | `plants` 🪴 | Plant care & watering schedule |
| ✅ | `car` 🚗 | Car maintenance & fuel log |
| ✅ | `home` 🏠 | Home maintenance & repairs |
| ✅ | `pets` 🐾 | Pet care, feeding & vet log |
| ✅ | `travel` ✈️ | Trip planner & itinerary |

### 🎨 Hobbies & Culture *(beyond the original 50)*
| | Tool | What it does |
|---|---|---|
| ✅ | `books` 📚 | Reading log with progress & ratings |
| ✅ | `films` 🎬 | Movie & show watchlist with ratings |
| ✅ | `mileage` 🏃 | Running, cycling, walking distance log |
| ✅ | `gratitude` 🙏 | Daily gratitude practice with streaks |

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

[**`AGENTS.md`**](AGENTS.md) is the one-page guide for agents: the contract,
the integrating commands (`today` / `search` / `export` / `doctor`), and
copy-paste recipes for the most common things you'll want to do.

[**`examples/`**](examples/) has working scripts that build on the contract:
a daily-brief renderer (Python + Bash) and a `search`-then-act agent pattern.

[**`docs/PHILOSOPHY.md`**](docs/PHILOSOPHY.md) explains the seven design
trade-offs every clibo tool is built on — read this before suggesting bigger
changes.

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
