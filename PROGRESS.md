# 📈 clibo — build log

A running log of the build loop. Newest entries on top.

---

### Iteration 31 — Automated release workflow · 2026-05-23

Future releases are now one command. `v1.0.0` was built and uploaded
by hand; `v1.1.0+` won't be.

- 🤖 [`.github/workflows/release.yml`](.github/workflows/release.yml)
  fires on any `v*.*.*` tag push and:
  - builds the wheel and sdist with `python -m build`,
  - sanity-checks that the tag matches `pyproject.toml`'s version (so
    a forgotten bump can't ship a mismatched artifact),
  - creates or updates the GitHub release and attaches the artifacts,
  - publishes to PyPI **only if** the `PYPI_API_TOKEN` repo secret is
    set, so the workflow is safe to merge before the token lands.
- 📝 `CONTRIBUTING.md` gains a Releasing section documenting the
  one-command flow: bump version, edit CHANGELOG, tag, push.
- **Tests:** 307 passing.

---

### Iteration 30 — Repo housekeeping + release artifacts · 2026-05-23

Open-source ergonomics around the v1.0.0 release.

- 📝 [`CONTRIBUTING.md`](CONTRIBUTING.md) — quick setup, the four-part
  definition of "done" for a new tool, commit-message rules.
- 🐛 `.github/ISSUE_TEMPLATE/bug_report.md` — repro / expected / actual
  / `clibo doctor --json` for environment.
- ✨ `.github/ISSUE_TEMPLATE/feature_request.md` — what / why / `--json`
  sketch / alternatives.
- ✅ `.github/pull_request_template.md` — the "new-tool" checklist
  matching the build-loop protocol.
- 📦 **Built wheel + sdist** (`uv build`) and attached them to the
  GitHub v1.0.0 release. Anyone can now `pip install` from the wheel
  URL even without the PyPI token landing.
- **Tests:** 307 passing.

---

### Iteration 29 — `AGENTS.md` · 2026-05-23

Post-v1.0 polish, focused on the project's primary audience.

- 📝 [`AGENTS.md`](AGENTS.md) — a one-page guide for AI agents at the
  repo root, covering: the universal contract (verbs, `--json`,
  stderr, name-or-ID resolution, forgiving date parsing); the
  integrating commands (`today` / `search` / `export` / `doctor`);
  five common agent recipes; and pitfalls to avoid (don't shell out
  to sqlite3, don't write the DB file, etc.).
- All documented recipes smoke-tested against the live CLI; the
  `export → cat path` flow was clarified after testing showed the
  command emits metadata, not the dump itself.
- README's "For AI agents" section now points at AGENTS.md.
- **Tests:** 307 passing (doc-only iteration, no test changes).

---

### Iteration 28 — `clibo import` · 2026-05-23

Another post-v1.0 polish: a seventh cross-tool command, the counterpart
to `clibo export`.

- 📥 `clibo import PATH` — load rows from a `clibo export` JSON file.
  Default mode uses `INSERT OR IGNORE` so re-importing is safe; pass
  `--replace` to wipe each table first. Tolerates the new
  `{version, tables: {...}}` envelope or a bare `{table: [rows]}` map.
- Rejects files that don't look like a clibo export (no `tables` map
  and no top-level dict-of-lists).
- Pairs with `export` to give a clean cross-machine migration path
  without copying the binary `.db` file.
- README's Cross-tool commands table updated.
- **Tests:** 307 passing (+5).

---

### Iteration 27 — `clibo doctor` · 2026-05-23

Post-v1.0 polish: a sixth cross-tool command for diagnostics.

- 🩺 `clibo doctor` — health check: version, Python version, tool
  count vs catalog, DB path + size on disk, table count, total rows,
  and a "tables with data" mini-table. `--healthy` boolean for agents.
- README: `clibo doctor` added to the Cross-tool commands table.
- **Tests:** 302 passing (+3).

---

### 🏷️ Iteration 26 — v1.0.0 release · 2026-05-23

Final Polish-phase iteration that the build loop can do on its own.

- 🎬 `scripts/demo.sh` — a self-contained, recordable tour: seeds a
  throwaway database with sample data across tools, then runs the
  showcase commands. The README now embeds the captured outputs.
- 📝 `CHANGELOG.md` — proper Keep-a-Changelog entry for v1.0.0.
- ⬆️ Version bumped to **1.0.0** in `pyproject.toml` and
  `clibo/__init__.py`; classifier moved to `Production/Stable`.
- 🏷️ Annotated git tag **`v1.0.0`** pushed; GitHub release created
  with the changelog notes.
- **Tests:** 299 passing.

### Polish phase wrap-up

- [x] `clibo today` · [x] `clibo backup`/`restore`/`export`
- [x] `clibo search` · [x] Shell completion docs
- [x] Demo captures + `scripts/demo.sh`
- [x] v1.0.0 release tagged
- [ ] PyPI publish (deferred — needs PyPI token from the maintainer)

That's the loop done. clibo v1.0.0 is in the world.

---

### Iteration 25 — Polish: `clibo search` + shell completion · 2026-05-23

Second Polish-phase iteration.

- 🔍 `clibo search QUERY` — one query across 13 text-bearing tables:
  notes, journal, todo, bookmark, crm, network, meetings, brag, recipes,
  worklog, gifts, expense, wishlist. Results are grouped by source.
- ⌨️ **Shell completion** documented in the README — `clibo --install-completion`
  installs tab-completion for bash/zsh/fish (Typer wires it up for free
  via `add_completion=True`).
- **Tests:** 299 passing (+5).

**Polish phase: 4 / 7 items done.**

---

### Iteration 24 — Polish: `clibo today` + backup/export · 2026-05-23

First Polish-phase iteration: the integrating commands that turn 50 separate
trackers into one app.

- 📅 `clibo today` — a one-screen dashboard pulling from 12 tools at once:
  overdue/today tasks, habit check-offs, water/calorie/focus progress bars,
  today's events and meals, bills due, follow-ups, plants needing water,
  chores due, and birthdays today. Sections only appear if there's data.
- 💾 `clibo backup` / `clibo restore` — copy the SQLite file to a
  timestamped backup, or replace the live DB from a backup.
- 📤 `clibo export` — dump every table as one JSON file (great for an
  agent to consume the whole local state in one read).
- **Tests:** 294 passing (+11).

**Built: 50 tools + 4 polish commands.**

---

### 🎉 Iteration 23 — Pets & Travel · 2026-05-23 — **ALL 50 SHIPPED**

The final two Home & Life tools — the project's main build phase is **done**.

- 🐾 `pets` — pet care log with multiple kinds of events (feeding, vet,
  grooming, walk, medication, note), per-pet history, age and last-vet
  tracking, plus events across all pets.
- ✈️ `travel` — trip planner with day-by-day itineraries; budget vs
  spent per trip, an `upcoming` view, and travel stats.
- **Tests:** 283 passing (+12).
- Micro-skills written for both tools.

**Built: 50 / 50** — 🏠 Home & Life done. All five categories complete.

### Where we are

| | |
|---|---|
| Tools | **50** |
| Tests | **283** passing across all CLIs |
| Lines of Python | ~6.5k (tools + tests + skills) |
| SKILL.md files | 50, one per tool |

Next up: the Polish phase from PLAN.md — a `clibo today` dashboard, an
`export`/`backup` of the database, global search, demo recordings and
a v1.0 release.

---

### Iteration 22 — Car & Home · 2026-05-23

Two more Home & Life tools.

- 🚗 `car` — fuel log + service log under one tool, with spending
  stats and a per-100 fuel-economy computation across fill-ups.
- 🏠 `home` — home maintenance / repair / improvement entries with
  cost, location, contractor and per-kind/location stats.
- **Tests:** 271 passing (+11).
- Micro-skills written for both tools.

**Built: 48 / 50.**

---

### Iteration 21 — Chores & Plants · 2026-05-23

Two more Home & Life tools, both built on a recurring-task pattern.

- 🧹 `chores` — household chores with a per-chore frequency, assignee,
  auto status (overdue/due/upcoming) and a `due` view.
- 🪴 `plants` — plant watering schedule with an interval per plant,
  `water` action, and a `thirsty` view of plants needing water.
- **Tests:** 260 passing (+12).
- Micro-skills written for both tools.

**Built: 46 / 50.**

---

### Iteration 20 — Recipes & Meals · 2026-05-23

Two more Home & Life tools.

- 👨‍🍳 `recipes` — a recipe book with ingredients, instructions, prep
  time and servings; search by ingredient and a `random` "what to
  cook" picker.
- 🍽️ `meals` — weekly meal planner; plan meals per day and view the
  whole week as a breakfast/lunch/dinner grid.
- **Tests:** 248 passing (+12).
- Micro-skills written for both tools.

**Built: 44 / 50.**

---

### Iteration 19 — Groceries & Pantry · 2026-05-23

Opened the 🏠 Home & Life category — the final stretch.

- 🛒 `groceries` — a shopping list with quantities and categories;
  buy/unbuy items and `clear` bought ones after shopping.
- 🥫 `pantry` — food inventory with expiry dates and locations; an
  `expiring` view flags items expired or expiring soon.
- **Tests:** 236 passing (+11).
- Micro-skills written for both tools.

**Built: 42 / 50.**

---

### Iteration 18 — Gifts & Brag · 2026-05-23

Shipped the last two CRM & Relationships tools — **category complete (10/10)**.

- 🎁 `gifts` — gift ideas tracked from idea → bought → given, filtered
  by recipient or status, with spending stats.
- 🏆 `brag` — an achievement log / brag document with impact notes and
  a `since` command for assembling performance-review summaries.
- **Tests:** 225 passing (+10).
- Micro-skills written for both tools.

**Built: 40 / 50** — 🤝 CRM & Relationships done. 4 categories of 5.

---

### Iteration 17 — Birthdays & Network · 2026-05-23

Two more CRM & Relationships tools.

- 🎂 `birthdays` — birthday & anniversary reminders; recurring yearly
  occasions with next-occurrence and age calculation, `today` and
  `upcoming` views.
- 🌐 `network` — log people you meet (where, when, context), search,
  and stats with your top meeting places.
- **Tests:** 215 passing (+11).
- Micro-skills written for both tools.

**Built: 38 / 50.**

---

### Iteration 16 — Jobs & Clients · 2026-05-23

Two more CRM & Relationships tools.

- 💼 `jobs` — job application tracker with a wishlist→accepted status
  flow, a `pipeline` view and response-rate stats.
- 🧑‍💼 `clients` — freelance client manager; log billable hours per
  client, see earnings (hours × rate), and total stats.
- **Tests:** 204 passing (+12).
- Micro-skills written for both tools.

**Built: 36 / 50.**

---

### Iteration 15 — Followup & Meetings · 2026-05-23

Two more CRM & Relationships tools.

- 🔔 `followup` — follow-up reminders for people with due dates, auto
  status (overdue/due soon), a `due` view and a `snooze` command.
- 🗓️ `meetings` — meeting notes with attendees plus action items;
  per-meeting `show`, an `actions` view of all open items, and stats.
- **Tests:** 192 passing (+11).
- Micro-skills written for both tools.

**Built: 34 / 50.**

---

### Iteration 14 — CRM & Leads · 2026-05-23

Opened the 🤝 CRM & Relationships category.

- 👥 `crm` — contacts CRM with company/email/phone/tags, lead/active/
  customer/cold status, search, and a `touch` command to log contact.
- 🧲 `leads` — sales pipeline with deals, stage transitions via `move`,
  a `pipeline` view grouping open deals by stage, and win-rate stats.
- **Tests:** 181 passing (+12).
- Micro-skills written for both tools.

**Built: 32 / 50.**

---

### Iteration 13 — Worklog & Bookmark · 2026-05-23

Shipped the last two Productivity & Work tools — **category complete (10/10)**.

- 🗒️ `worklog` — work-log entries tagged done/doing/blocked/note, plus
  a `standup` command that buckets them into yesterday/today/blockers.
- 🔖 `bookmark` — save links with tags and categories, full-text
  search, favorites, and open-in-browser.
- **Tests:** 169 passing (+11).
- Micro-skills written for both tools.

**Built: 30 / 50** — ✅ Productivity & Work done. 3 categories of 5.

---

### Iteration 12 — Goals & Events · 2026-05-22

Two more Productivity & Work tools.

- 🎯 `goals` — goals/OKRs with milestones; progress bars driven by
  milestone completion, check/uncheck, mark a whole goal achieved.
- 📅 `events` — events & reminders calendar with `today`, `upcoming`,
  relative "when" labels and edit support.
- **Tests:** 158 passing (+13).
- Micro-skills written for both tools.

**Built: 28 / 50.**

---

### Iteration 11 — Time & Journal · 2026-05-22

Two more Productivity & Work tools.

- ⏱️ `time` — time tracking by project with a start/stop running timer,
  manual logging, and a per-project `report` with share bars.
- 📔 `journal` — daily journal/diary with mood, tags, full-text search,
  a `today` view and a journaling-streak stat.
- **Tests:** 145 passing (+12).
- Micro-skills written for both tools.

**Built: 26 / 50.**

---

### Iteration 10 — Habit & Focus · 2026-05-22

Two more Productivity & Work tools.

- 🔥 `habit` — habit tracker with current/longest streaks, weekly
  targets, idempotent check/uncheck, a `today` view and per-habit stats.
- 🍅 `focus` — pomodoro & focus sessions with a live countdown `timer`,
  manual `log`, a daily goal with progress bar, and stats.
- **Tests:** 133 passing (+13).
- Micro-skills written for both tools.

**Built: 24 / 50.**

---

### Iteration 9 — Todo & Notes · 2026-05-22

Opened the ✅ Productivity & Work category.

- ✅ `todo` — task manager with low/med/high priority, due dates,
  projects and tags; pending tasks sort overdue/high-priority first,
  with done/undone, edit and stats.
- 📝 `notes` — quick notes with tags, full-text `search`, pinning,
  and a one-line preview in the list view.
- **Tests:** 120 passing (+13).
- Micro-skills written for both tools.

**Built: 22 / 50.**

---

### Iteration 8 — Split & Wishlist · 2026-05-22

Shipped the last two Money & Finance tools — **category complete (10/10)**.

- 🤝 `split` — shared expenses split equally; per-person `balances`,
  settle-up payments, and a `who` solver for the fewest payments to
  square everyone up.
- ⭐ `wishlist` — things-to-buy list with prices and 1–5 star
  priorities; mark items purchased, plus total-pending-cost stats.
- **Tests:** 107 passing (+10).
- Micro-skills written for both tools.

**Built: 20 / 50** — 💰 Money & Finance done.

---

### Iteration 7 — Net Worth & Invoice · 2026-05-22

Two more Money & Finance tools.

- 💰 `networth` — track assets and liabilities, see current net worth,
  and save dated snapshots to build a net-worth history.
- 📄 `invoice` — freelance invoices with auto-numbering (INV-0001…),
  tax, a draft→sent→paid flow, a formatted `render` document, and
  billed/paid/outstanding stats.
- **Tests:** 97 passing (+11).
- Micro-skills written for both tools.

**Built: 18 / 50.**

---

### Iteration 6 — Savings & Debt · 2026-05-22

Two more Money & Finance tools, both built on a goal + contributions model.

- 🐷 `savings` — savings goals with deposits/withdrawals; `list` shows a
  progress bar per goal, `show` adds deposit history, plus overall stats.
- 📉 `debt` — debts/loans with logged payments; payoff progress bars,
  payment history, a `cleared` flag and overall debt stats.
- **Tests:** 86 passing (+12).
- Micro-skills written for both tools.

**Built: 16 / 50.**

---

### Iteration 5 — Subs & Bills · 2026-05-22

Two more Money & Finance tools.

- 🔁 `subs` — track recurring subscriptions; every billing cycle
  (weekly/monthly/yearly) is normalised to a monthly cost, with
  `total`, `upcoming` reminders, cancel/delete and category stats.
- 🧾 `bills` — bills with due dates and paid/unpaid state; auto status
  (overdue / due soon / upcoming), a `due` reminder view, and stats.
- **Tests:** 74 passing (+11).
- Micro-skills written for both tools.

**Built: 14 / 50.**

---

### Iteration 4 — Expense & Budget · 2026-05-22

Opened the 💰 Money & Finance category — and the first cross-tool integration.

- 💸 `expense` — record expenses, monthly breakdown by category with
  share bars, a shared currency setting, edit/delete, and stats.
- 📊 `budget` — set per-category monthly limits; `list`/`check`/`status`
  read the expense tool's data live to show real spending vs each budget,
  flagging over-budget categories.
- **Tests:** 63 passing (+12).
- Micro-skills written for both tools.

**Built: 12 / 50.**

---

### Iteration 3 — Meditate & Vitals · 2026-05-22

Shipped the last two Health & Wellness tools — **category complete (10/10)**.

- 🧘 `meditate` — log sessions by minutes & kind, daily goal with a
  progress bar, consecutive-day streak, and stats.
- ❤️ `vitals` — log blood pressure (auto-classified), pulse, glucose,
  temperature and SpO₂; `latest` per vital and per-kind stats.
- **Tests:** 51 passing (+11).
- Micro-skills written for both tools.

**Built: 10 / 50** — 🏃 Health & Wellness done.

---

### Iteration 2 — Meds & Period · 2026-05-22

Shipped two more Health & Wellness tools.

- 💊 `meds` — register medications (dosage, times/day), `take` doses by
  name or ID, a `today` view showing what's still due, dose history,
  `stop`/`rm`, and adherence stats.
- 🌸 `period` — log period `start`/`end` or a complete past period,
  `predict` the next period + fertile window from cycle history, and
  cycle/length stats.
- **Tests:** 40 passing (+12).
- Micro-skills written for both tools.

**Built: 8 / 50.**

---

### Iteration 1 — Sleep & Mood · 2026-05-22

Shipped two more Health & Wellness tools.

- 😴 `sleep` — log hours + quality (1–5), bedtime/wake times, nightly goal,
  `last` night view with a progress bar, and stats.
- 🙂 `mood` — 1–5 mood check-ins with emoji faces, emotion tags, `today`
  view, and stats with score distribution + top emotions.
- **Tests:** 28 passing (+10).
- Micro-skills written for both tools.

**Built: 6 / 50.**

---

### Iteration 0 — Foundation · 2026-05-22

Scaffolded the whole project and shipped the first 4 tools.

- **Core engine** — `core/config.py` (paths), `core/db.py` (SQLite engine +
  sessions), `core/settings.py` (shared key/value store), `core/base.py`
  (date parsing), `core/output.py` (Rich tables + `--json` for agents).
- **Root command** — `clibo` with `info` (progress dashboard) and `version`.
- **Catalog** — all 50 tools defined in `catalog.py`.
- **Tools shipped (4):** 🍎 `calorie`, 💧 `water`, ⚖️ `weight`, 🏋️ `workout`.
- **Tests:** 18 passing.
- **Skills:** micro-skill `SKILL.md` written for each of the 4 tools.
- **Packaging:** `pyproject.toml`, `install.sh`, MIT license, CI workflow.

**Built: 4 / 50.**

---

*Each loop iteration appends here: which tool(s) shipped, test count, notes.*
