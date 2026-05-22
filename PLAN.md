# 🗺️ clibo — build plan

The goal: **50 local-first CLI tools**, one `clibo <tool>` sub-command each,
all sharing one SQLite database and a `--json` contract for AI agents.

Stack: **Python · Typer · SQLModel · Rich**.

---

## Build loop protocol

clibo is built by a `/loop` that runs every **15 minutes**. Each iteration:

1. Read `PROGRESS.md` and this file. Pick the **first unchecked tool** below.
2. Implement `clibo/clis/<tool>.py` following the pattern in
   [`docs/ADDING_A_TOOL.md`](docs/ADDING_A_TOOL.md) — use `calorie.py` as the
   reference. A SQLModel table, a Typer `app`, `--json` on every command,
   emoji-rich Rich output for humans.
3. Register it: add the import + entry to `clibo/clis/__init__.py`.
4. Write `tests/test_<tool>.py` (cover create / read / json / stats / an error).
5. Write `skills/<tool>/SKILL.md` (the micro-skill).
6. Run `pytest` — **all tests must pass**. Fix until green.
7. Manually smoke-test the new tool's commands, including `--json`.
8. Tick the box below, append an entry to `PROGRESS.md`, update the README
   table, and `git commit && git push`. **Do not add any `Co-Authored-By`
   trailer or "Generated with Claude" line to commit messages.**
9. If every tool is built, move to the **Polish phase**.

Aim for 1–2 tools per iteration. Quality over speed: a tool isn't done until
its tests are green and its skill is written.

---

## 🏃 Health & Wellness
- [x] `calorie` 🍎 — Food & calorie tracker with macros
- [x] `water` 💧 — Daily water intake tracker
- [x] `weight` ⚖️ — Body-weight log with BMI & trend
- [x] `workout` 🏋️ — Exercise & gym session log
- [x] `sleep` 😴 — Sleep duration & quality tracker
- [x] `mood` 🙂 — Daily mood & emotion journal
- [x] `meds` 💊 — Medication log & dosage reminders
- [x] `period` 🌸 — Menstrual cycle tracker & predictions
- [x] `meditate` 🧘 — Meditation & mindfulness sessions
- [x] `vitals` ❤️ — Blood pressure, pulse & glucose log

## 💰 Money & Finance
- [x] `expense` 💸 — Personal expense tracker
- [x] `budget` 📊 — Monthly budgets by category
- [x] `subs` 🔁 — Recurring subscriptions tracker
- [x] `bills` 🧾 — Bills & due-date reminders
- [x] `savings` 🐷 — Savings goals with progress
- [x] `debt` 📉 — Debt & loan payoff tracker
- [x] `networth` 💰 — Assets, liabilities & net worth
- [x] `invoice` 📄 — Freelance invoice generator
- [x] `split` 🤝 — Split shared expenses with people
- [x] `wishlist` ⭐ — Things-to-buy wishlist with prices

## ✅ Productivity & Work
- [x] `todo` ✅ — Task & to-do manager
- [x] `notes` 📝 — Quick searchable notes
- [x] `habit` 🔥 — Habit tracker with streaks
- [x] `focus` 🍅 — Pomodoro & focus sessions
- [x] `time` ⏱️ — Time tracking by project
- [x] `journal` 📔 — Daily journal & diary
- [x] `goals` 🎯 — Goals & OKRs with milestones
- [x] `events` 📅 — Events & reminders calendar
- [x] `worklog` 🗒️ — Work log & standup notes
- [x] `bookmark` 🔖 — Bookmarks & link saver

## 🤝 CRM & Relationships
- [x] `crm` 👥 — Contacts CRM
- [x] `leads` 🧲 — Sales pipeline & deals
- [x] `followup` 🔔 — Follow-up reminders for people
- [x] `meetings` 🗓️ — Meeting notes & action items
- [x] `jobs` 💼 — Job application tracker
- [x] `clients` 🧑‍💼 — Freelance client manager
- [x] `birthdays` 🎂 — Birthday & anniversary reminders
- [x] `network` 🌐 — Networking & people-you-met log
- [x] `gifts` 🎁 — Gift ideas & giving tracker
- [x] `brag` 🏆 — Achievement log for performance reviews

## 🏠 Home & Life
- [ ] `groceries` 🛒 — Grocery & shopping list
- [ ] `pantry` 🥫 — Food inventory with expiry dates
- [ ] `recipes` 👨‍🍳 — Personal recipe book
- [ ] `meals` 🍽️ — Weekly meal planner
- [ ] `chores` 🧹 — Household chores rotation
- [ ] `plants` 🪴 — Plant care & watering schedule
- [ ] `car` 🚗 — Car maintenance & fuel log
- [ ] `home` 🏠 — Home maintenance & repairs
- [ ] `pets` 🐾 — Pet care, feeding & vet log
- [ ] `travel` ✈️ — Trip planner & itinerary

---

## ✨ Polish phase (after all 50)

- [ ] `clibo today` — one-screen dashboard across all trackers
- [ ] `clibo export` / `clibo backup` — dump & restore the database
- [ ] `clibo search` — global search across tools
- [ ] Shell completion install docs
- [ ] Demo GIFs / asciinema in the README
- [ ] Publish to PyPI (`pipx install clibo`)
- [ ] Tag the `v1.0.0` release
