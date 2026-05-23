# 📈 clibo — build log

A running log of the build loop. Newest entries on top.

---

### Iteration 53 — polish: `add` is now a universal alias for `log` · 2026-05-23

Agent-mode self-test: a user saying "I felt anxious today" or "I weigh
78kg" wants `clibo mood add ...` / `clibo weight add ...` — but those
tools (and 8 more) only exposed `log`, breaking the predictable-verb
promise the README makes ("`add`, `list`, `show`, `edit`, `rm`,
`stats`").

```
$ clibo mood add 4 -e calm    → No such command 'add'.
$ clibo weight add 78         → No such command 'add'.
```

- 🪄 **One-line `app.command(name="add")(log)` alias** added to ten
  time-stamped tools: `mood`, `weight`, `sleep`, `calorie`, `focus`,
  `meditate`, `mileage`, `period`, `time`, `workout`. `log` still
  works (it's the semantically right primary verb for these); `add`
  is the friendly one agents reach for.
- 🛑 **NOT aliased**: `clients` and `pets` — both already have an
  `add` command meaning "add a new entity" (a client, a pet), which is
  the right meaning for those nouns. Their `log` (touchpoint /
  vet-visit) stays separate.
- 🧪 New file `tests/test_add_alias.py` — parametrized test covering
  all 10 aliased tools, plus two behavioural tests confirming
  `mood add` and `weight add` actually persist a row.
- 🎤 NL flow re-verified end-to-end:
  • "I felt anxious today" → `mood add 2 -e anxious` ✓
  • "I weigh 78kg" → `weight add 78` ✓
  • "I slept 7.5 hours" → `sleep add 7.5` ✓
- **Tests:** 431 passing (+12); ruff clean.

---

### Iteration 52 — polish: search / tags now index the beyond-50 tools · 2026-05-23

Agent-mode smoke test exposed a silent regression: every tool added
after v1.0 (books, films, mileage, gratitude, income, ideas, quotes,
flashcards, lessons, cv, dreams, dashboard) was registered in `recent`
but **invisible** to the two cross-tool integrators — `clibo search`
and `clibo tags`.

```
clibo search "Atomic Habits"  → No matches for 'Atomic'.
clibo search inspiration      → No matches.
clibo tags                    → No tags yet (lists only 8 sources)
```

- 🔍 **`clibo/search.py`** — SOURCES grew from 13 → 22: added `books`,
  `films`, `income`, `ideas`, `quotes`, `lessons`, `cv`, `dreams`,
  `gratitude`. Each with snippet formatter and the right text columns.
- 🏷️ **`clibo/tags.py`** — TAG_SOURCES grew from 7 → 11: added
  `ideas`, `quotes`, `lessons`, `cv` (the four post-v1.0 tools that
  carry a `tags` column).
- 🧪 Two new tests pin this behaviour so it can't silently regress
  again: `test_search_covers_beyond_50_tools` and
  `test_tags_covers_beyond_50_tools` — both seed every new source
  with a shared keyword and assert the integrator picks it up.
- 📖 `AGENTS.md` quick-reference updated (13 → 22 text-bearing tables).
- 🎤 NL flow re-verified end-to-end:
  • "Atomic Habits" → `search atomic` → 3 hits across books, dreams,
    gratitude.
  • tagged 4 post-v1.0 records with `-t marketing` →
    `tags` → "marketing 4 · cv (1), ideas (1), lessons (1), quotes (1)".
- **Tests:** 419 passing (+2); ruff clean.

---

### Iteration 51 — `dreams` (dream journal) · 2026-05-23

Self-test: "Strange dream about flying over the city" went to `journal`
— workable, but dreams have specific structure (vividness, lucid flag,
recurring symbols) that `journal` can't express.

- 🌙 **New tool `dreams` (62nd)** — dream journal with `vividness`
  (1-5), `lucid` flag, and comma-separated **symbols** so recurring
  motifs are queryable.
- Commands: `add SUMMARY -D DESC -v VIVID --lucid -s SYMBOLS` /
  `today` (full detail) / `list [--lucid]` / `show ID` (stars +
  symbols + narrative) / `search` (summary/description/symbols) /
  **`symbols`** (frequency table — the recurring-pattern view) /
  `rm` / `stats` (lucid rate, avg vividness, top symbols).
- 📜 `recent` picks up dreams with optional 🪄 prefix for lucid.
- 📄 `docs/SCHEMA.md` regenerated (74 tables).
- 🎤 NL flow verified:
  • "Strange dream about flying over the city" → `dreams add "flying over the city" -s flying,city`
  • "Had a lucid dream about water" → `dreams add "water dream" --lucid -s water`
  • "What symbols keep showing up?" → `dreams symbols`
- **Tests:** 424 passing (+7); ruff clean.

---

### Iteration 50 — `cv` (career history) · 2026-05-23

Self-test surfaced: "Add CV entry: 2024-2026 Senior Engineer at Acme"
had no real home — `jobs` is for *applying*, not for past career.

- 📜 **New tool `cv` (61st)** — résumé as living data. Distinct from
  `jobs` (applications). Filed under CRM & Relationships alongside
  it.
- Model has month-precision dates: omit `--end` for currently-running,
  use `YYYY-MM` for résumé-style "2024-01 — 2026-04" rendering.
- Commands: `add TITLE -o ORG -k KIND --start --end` / `achieve ID
  'bullet'` (append a highlight) / `current` / `list [-k KIND]` /
  `show ID` (pretty CV detail) / `timeline` (chronological,
  newest-first, CV-ready) / `end ID` (close out a current entry) /
  `edit` / `rm` / `stats` (counts + approx job years).
- Kinds: `job`, `education`, `project`, `cert`, `other`.
- 📜 `recent` picks up CV entries.
- 📄 `docs/SCHEMA.md` regenerated (73 tables).
- 🎤 NL flow verified end-to-end:
  • "2024-2026 Senior Engineer at Acme" → `cv add "Senior Engineer" -o Acme -k job --start 2024-01 --end 2026-04`
  • "Currently Founder at MyCo since June 2025" → `cv add Founder -o MyCo -k job --start 2025-06`
  • "Add bullet: Shipped search, cut latency 40%" → `cv achieve <id> "Shipped search..."`
  • "Show my CV" → `cv timeline`
- **Tests:** 417 passing (+9); ruff clean.

---

### Iteration 49 — `clibo dashboard` (configurable widgets) · 2026-05-23

User request: customizable dashboard distinct from the fixed `clibo today`.

- 🎛️ **New tool `dashboard` (60th)** — pick which widgets show, save
  the selection, render. Sub-commands: `add NAME` / `remove NAME` /
  `list` (every widget with active state) / `reset` / `clear`. The
  base `clibo dashboard` command (no sub-command) renders the saved
  widget set.
- 🧩 New `clibo/widgets.py` registry — **18 widgets** so far: tasks,
  habits, water, calories, focus, sleep, mood, events, bills,
  followups, plants, chores, birthdays, mileage, gratitude, weight,
  expense, income. Each is a small function returning
  `{title, lines, data}` so adding a 19th widget is one entry.
- ⚙️ Widget selection stored in shared settings (`dashboard.widgets`)
  so it survives across calls; defaults to a sensible 6-widget set.
- 🧪 Renamed the old `tests/test_dashboard.py` → `test_today.py`
  (it had always been testing `clibo today`, never the new
  dashboard command).
- 📄 `docs/SCHEMA.md` regenerated (72 tables, no new tables — the
  widget config rides in the shared `clibo_setting` KV store).
- 🎤 Demo: `clibo dashboard` shows tasks/habits/water/calories/focus/
  events out of the box; `clibo dashboard add sleep mileage` extends
  it to 8 widgets next call.
- **Tests:** 408 passing (+7); ruff clean.

---

### Iteration 48 — `lessons` (structured takeaways) · 2026-05-23

Self-test pass: "Lesson: retry logic should always have max-attempts"
ended up in `journal` with a tag — workable but unstructured. Closing
the gap with a tool that has dedicated `takeaway` + `context` fields.

- 📓 **New tool `lessons` (59th)** — structured takeaway + context.
  Distinct from `brag` (achievements, positive) and `journal`
  (free-form daily). Pretty-printed `show` separates the lesson
  from the situation it came from.
- Commands: `add TAKEAWAY -x CONTEXT -c CATEGORY -t TAG` / `list
  [--days N] [-c CATEGORY]` / `show` (formatted) / `search` (across
  takeaway/context/tags) / `random` (re-encounter) / `rm` /
  `stats`.
- 🐛 Ruff caught `E741 Ambiguous variable name 'l'` × 4 in
  comprehensions; renamed to `ls`. Real find — `l` ambiguous with
  the digit `1`.
- 📜 `recent` picks up lessons as `[category] takeaway`.
- 📄 `docs/SCHEMA.md` regenerated (72 tables).
- 🎤 NL mapping verified:
  • "Lesson: always set max-attempts" → `lessons add "always set max-attempts"`
  • "From prod incident: small batches" → `lessons add "ship small batches" -x "prod incident"`
  • "Show me a random lesson" → `lessons random`
- **Tests:** 401 passing (+7); ruff clean.

---

### Iteration 47 — `flashcards` (spaced repetition) · 2026-05-23

Closing the third gap from iter 46's self-test ("Spanish: día = day").

- 🃏 **New tool `flashcards` (58th)** — Leitner-style spaced
  repetition. Boxes 0-4 with intervals 1/3/7/14/30 days. `right`
  promotes; `wrong` resets to box 0.
- Commands: `add FRONT BACK -d DECK` / `due [-d DECK]` / `grade ID
  right|wrong` / `list [-d DECK]` / `decks` (counts per deck with
  due count) / `rm` / `stats` (box distribution + accuracy).
- Agent flow documented in SKILL.md: `due --json` → loop with the
  user → `grade ID right|wrong`.
- 📜 `recent` picks up new cards as `[deck] front → back`.
- 📄 `docs/SCHEMA.md` regenerated (71 tables).
- 🎤 NL mapping verified end-to-end:
  • "Spanish vocab: día = day" → `flashcards add "día" "day" -d spanish`
  • "Let's review my Spanish"  → `flashcards due -d spanish`
  • "Got that right"           → `flashcards grade <id> right` (→ box 1, due in 3d)
- **Tests:** 394 passing (+7); ruff clean.

---

### Iteration 46 — `quotes` (commonplace book) · 2026-05-23

Self-test surfaced three new gaps (quotes, lessons, flashcards); closing
the most ergonomic — quotes is a classic ask and structurally distinct
from `notes` (no structure) and `bookmark` (URLs).

- 💬 **New tool `quotes` (57th)** — a personal commonplace book with
  structured `text / author / source / tags`.
- Commands: `add` / `list -a AUTHOR -t TAG` / `show ID` (pretty italic
  block with attribution) / `search` (across all four fields) /
  `random` (inspiration pick, like `recipes random`) / `rm` / `stats`
  (top authors).
- 📜 `recent` picks up quotes with text snippet + author.
- 📄 `docs/SCHEMA.md` regenerated (70 tables).
- 🐛 **Fixed test regression** in `test_dump_schema.py` — assertion
  `"0 tables in total" not in text` was a substring trap ("70 tables"
  contains "0 tables"). Tightened to the exact italic empty-state
  phrase.
- 🎤 NL mappings:
  • "Quote: 'X' — Kent Beck" → `quotes add "X" -a "Kent Beck"`
  • "Give me a quote"        → `quotes random`
- **Tests:** 387 passing (+7); ruff clean.

---

### Iteration 45 — `ideas` with lifecycle · 2026-05-23

Self-test: "Idea: build a marketplace" only fit via `notes add` — but
ideas have a lifecycle (raw → exploring → validated → shipped/abandoned)
that notes can't express. Closing that.

- 💡 **New tool `ideas` (56th)** — idea capture with status flow,
  modeled after `leads`/`jobs`: `add` / `move ID STATUS` / `list --open`
  / `search` / `pipeline` (counts by status) / `edit` / `rm` / `stats`.
- Filed under **Productivity & Work** (expanding past the original 10,
  same way `income` expanded Money & Finance).
- 📜 `recent` picks up ideas with `[status] title` so you can see
  lifecycle moves in the activity feed.
- 📄 `docs/SCHEMA.md` regenerated (69 tables).
- 🎤 NL mappings work end-to-end:
  • "Idea: build a clibo plugin marketplace" → `ideas add "clibo plugin marketplace"`
  • "Thinking about tags on ideas"           → `ideas add "tags on ideas" -s exploring`
  • "I shipped the pomodoro variant"         → `ideas move <id> shipped`
- **Tests:** 380 passing (+6); ruff clean.

---

### Iteration 44 — Closed the income gap · 2026-05-23

Last iteration's self-test flagged "Got 500 USD from freelance gig" had
no real home (`savings deposit` was a hack). Closing that now.

- 💵 **New tool `income` (55th)** — counterpart to `expense`. Tracks
  money coming in by source + category (salary / freelance / gift /
  refund / dividend / other). Same shape as `expense`: `add`, `list`,
  `month` with share bars, `show`, `edit`, `rm`, `stats`.
- Shares the `money/currency` setting so amounts render consistently
  with the rest of the money group.
- 📁 Filed under **💰 Money & Finance** in the catalog (not Hobbies)
  — it's a true money tool, just expanding the original 10-per-cat
  symmetry.
- 📜 `recent` picks up income events with a different verb ("received
  N from …") so you can spot inflow vs outflow at a glance.
- 📄 `docs/SCHEMA.md` regenerated (68 tables).
- 🎤 All three NL inputs map cleanly:
  • "Got 500 USD from freelance gig" → `income add "freelance gig" -a 500 -c freelance`
  • "Salary landed: 3200"            → `income add salary -a 3200 -c salary`
  • "Mom sent 100 for my birthday"   → `income add "Mom — birthday" -a 100 -c gift`
- **Tests:** 374 passing (+5); ruff clean.

---

### Iteration 43 — Self-test → added `gratitude` · 2026-05-23

Agent self-test of 3 NL inputs surfaced two gaps; closing the first one.

- 🎤 Self-tested ① "I'm grateful for sunshine" — only fits via
  `journal write` which is overkill (free-form, no daily focus, no
  streak); ② "Got 500 USD from a freelance gig" — works only as a
  hack via `savings deposit`; ③ "Tipped 5 USD at dinner" — fits
  `expense` cleanly.
- 🙏 **New tool `gratitude` (54th)** — daily gratitude practice
  distinct from `journal`: short dated entries, day-level streak
  (current + longest), `today` view with flames per streak day.
  Tests verify streak after `parse_date` backfill ("10 days ago").
- 📜 `recent` now picks up `gratitude` and `mileage` events.
- 📄 `docs/SCHEMA.md` regenerated (67 tables).
- 🎤 All three NL inputs now map cleanly; income-tracking gap noted
  for next iteration.
- **Tests:** 369 passing (+6); ruff clean.

---

### Iteration 42 — Self-test → fixed `parse_date` & added `mileage` · 2026-05-23

Agent-mode self-test caught **two real gaps** in one pass.

- 🎤 Self-tested 4 natural-language inputs: ① "Met Sarah at PyCon
  7 days ago" — failed because `parse_date` didn't know `"N days ago"`;
  ② "I owe Anna 50 USD" — worked via `debt`; ③ "I ran 5km this morning"
  — silently lost the distance (workout has no km field); ④ "Cycled
  12km yesterday" — same problem.
- 🛠️ **Fixed `parse_date`** to accept relative phrasings: `"N days ago"`,
  `"N weeks from now"`, `"last week"`, `"next month"`, etc. Covers
  days/weeks/months/years × ago/from now × singular/plural. 7 new
  unit tests in `test_parse_date.py`.
- 🏃 **New tool `mileage` (53rd)** — distance-based activity log:
  run/walk/cycle/hike/swim with auto-computed pace, weekly distance
  goal with progress bar, per-activity breakdown.
- 📜 `recent` now picks up books, films, mileage.
- 📄 `docs/SCHEMA.md` regenerated (66 tables).
- 🎤 **All 4 NL inputs now map cleanly** end-to-end on the second pass.
- **Tests:** 357 passing (+13); ruff clean.

---

### Iteration 41 — Beyond 50: agent-mode + books + films · 2026-05-23

New direction from the maintainer: keep going past 50 tools, add what's
genuinely useful, and use **me as the agent** that maps natural-language
requests to clibo commands.

- 🐛 **Fixed real install bug**: `clibo --version` returned an error; only
  `clibo version` worked. Now both work, via a `--version`/`-V` callback.
  Caught by literally typing `clibo --version` like a new user would.
- 📚 **`books`** (51st tool) — reading log with `add` / `read N pages` /
  `start` / `finish -r RATING` / `list -s STATUS` / `stats`. `read` auto-
  promotes wishlist → reading and auto-finishes when pages_read ≥ total.
- 🎬 **`films`** (52nd tool) — movie & show watchlist with `add` /
  `watched -r RATING` / `rate` / `list -k movie|show` / `stats`.
- 🎨 New catalog category **"Hobbies & Culture"** for tools beyond the
  original 50 grouping.
- 📜 `clibo recent` source list extended to pick up new books/films
  events so they show in the activity feed.
- 🎤 **Agent-mode demo** in the commit history: three natural-language
  inputs ("I ate grilled chicken with rice for lunch", "I read 30 pages
  of Atomic Habits", "I watched Oppenheimer, 5 stars") mapped to the
  right CLI by reasoning about the request, estimating params and
  invoking via subprocess. Worked end-to-end.
- 📄 `docs/SCHEMA.md` regenerated (now 65 tables).
- 🔄 README updated: header now reads "50+", new Hobbies & Culture
  table appended.
- 🧹 Lint and tests pass; new SKILL.md files for both tools document
  the natural-language → command mappings agents should use.
- **Tests:** 344 passing (+12).

---

### Iteration 40 — `docs/PHILOSOPHY.md` + CHANGELOG catch-up · 2026-05-23

Two pieces of honest documentation upkeep.

- 🎯 `docs/PHILOSOPHY.md` — the seven design trade-offs every clibo
  tool is built on, articulated for the first time: local-first, the
  `--json` contract as the API, 50 tools rather than a library,
  predictable verbs, forgiving dates, beautiful output as part of
  correctness, and the pragmatic test bar. Each gives the *why* and
  the trade-off we accepted.
- 📝 `CHANGELOG.md` `[Unreleased]` section rewritten to match what's
  actually on `main` since v1.0.0: six new cross-tool commands
  (init/week/recent/tags/doctor/import), four new docs (AGENTS,
  PHILOSOPHY, SCHEMA, examples/), CONTRIBUTING/templates, automated
  release workflow, ruff in CI. 332 tests vs 299 at v1.0.0.
- 🔗 README and CONTRIBUTING link to `PHILOSOPHY.md` so it shows up
  before contributors propose big changes.
- **Tests:** 332 passing; ruff clean.

---

### Iteration 39 — Ruff lint config + CI step · 2026-05-23

Maintenance: 50 cli modules can drift in style fast without a linter.
Adding ruff catches that *and* surfaced 12 real issues on the first run.

- 🧹 Added `ruff>=0.5` to `[project.optional-dependencies.dev]`.
- ⚙️ `[tool.ruff]` config in `pyproject.toml`: line length 100,
  Python 3.10 target, rules `E/W/F/I/UP/B/SIM` enabled, with the
  opinionated `SIM108`/`B007`/`B008` and unfair `E501` disabled.
- 🔧 Fixed 12 real issues ruff caught: 8 unused imports across 6 cli
  modules (auto-fix), 1 unused local in `jobs.py` stats, 2 unused
  test locals, 1 `typing.Callable` → `collections.abc.Callable`
  upgrade, 1 import sort issue.
- 🤖 New `Lint with ruff` step in `.github/workflows/ci.yml` runs
  before pytest on every push/PR.
- 📝 `CONTRIBUTING.md` quick-setup now includes `ruff check`.
- **Tests:** 332 passing; ruff clean.

---

### Iteration 38 — `docs/SCHEMA.md` · 2026-05-23

Real maintenance artifact for contributors and agents writing analytics:
a single Markdown reference for all 63 tables clibo writes to.

- 📜 `scripts/dump_schema.py` walks `SQLModel.metadata`, groups tables by
  catalog category, and emits a tidy Markdown reference per column with
  PK / NOT NULL / indexed / default / FK flags.
- 📄 [`docs/SCHEMA.md`](docs/SCHEMA.md) — generated output (63 tables,
  794 lines). Living reference whenever new tools are added; regenerate
  with `python scripts/dump_schema.py`.
- 🔗 `CONTRIBUTING.md` and `docs/ADDING_A_TOOL.md` both point at the
  new reference and the regen command.
- ✅ Smoke test (`tests/test_dump_schema.py`) runs the script as a
  subprocess and checks that representative tables across categories
  show up in the output — catches schema drift before it ships.
- **Tests:** 332 passing (+1).

---

### Iteration 37 — `clibo recent` · 2026-05-23

Third integrating view — `today` is categorical, `week` is aggregate,
`recent` is just a chronological feed.

- 📜 `clibo recent --limit N` pulls the most-recent entries across 40+
  tables (every tool with a `created_at` or domain-specific timestamp
  column), formats each as a one-liner with an emoji and relative
  "just now / 9h ago / yesterday" label, and shows them newest-first.
- Uses raw SQLite + PRAGMA schema introspection so the feed survives
  schema tweaks; `habit_check` uses `check_date` instead of
  `created_at` via a small override map.
- Tests caught and fixed a missing-column case (`habit_check` lacks
  `created_at`) before commit.
- README's Cross-tool commands table lists `recent` next to `week`.
- **Tests:** 331 passing (+6).

---

### Iteration 36 — `clibo tags` · 2026-05-23

A real gap closed: seven tools accept `-t/--tag`, but nothing told you
which tags you'd actually used. Now `clibo tags` does.

- 🏷️ `clibo tags` walks the tag column of every tag-bearing table
  (notes, todo, bookmark, crm, brag, recipes, journal), normalises
  to lowercase, and shows tag · count · per-source breakdown.
- Defensive PRAGMA-based column check skips tables that exist but
  don't have a `tags` column (e.g. `network` & `gifts` use `notes`
  only).
- Tests caught a real bug on the first run: `network_connection`
  was in the source list but lacks a `tags` column — removed and
  guarded against.
- README's Cross-tool commands table lists `tags` next to `search`.
- **Tests:** 325 passing (+6).

---

### Iteration 35 — Stage `v1.1.0` in the changelog · 2026-05-23

Honest natural stop. Eight polish iterations have landed on `main` since
v1.0.0 — they're material enough to warrant a v1.1.0 release whenever the
maintainer is ready to push the tag.

- 📝 `CHANGELOG.md` gains an **`[Unreleased]` — staged for v1.1.0**
  section above the v1.0.0 entry, listing every post-v1.0 addition:
  `init`, `week`, `doctor`, `import`, `AGENTS.md`, `examples/`,
  `CONTRIBUTING.md` + templates, the release workflow, attached
  artifacts.
- Cutting v1.1.0 is one command on a clean `main`: bump
  `pyproject.toml` and `clibo/__init__.py` to `1.1.0`, rename the
  Unreleased heading to `[1.1.0] — YYYY-MM-DD`, then
  `git tag -a v1.1.0 -m "clibo v1.1.0" && git push origin main --follow-tags`.
  The Release workflow handles the rest.
- The build loop has now finished both PLAN's main phase (50 tools) and
  its Polish phase, plus eight extra polish iterations. The remaining
  open item (PyPI publishing) is blocked on a maintainer token.
  Stopping the loop with `CronDelete 2b630fc4` is the intended next
  step.
- **Tests:** 319 passing (doc-only iteration).

---

### Iteration 34 — `examples/` and a startup-time check · 2026-05-23

Quality pass — measure performance, then add real, runnable examples.

- ⏱️ **Startup time** measured at ~270 ms for `clibo --help` across five
  runs. With 50 sub-apps loaded at import, that's well within "feels
  instant" for a personal tool — no lazy-loading work needed.
- 📁 New [`examples/`](examples/) directory with:
  - `daily_brief.py` — Python subprocess pattern: calls `clibo today
    --json` and `clibo week --json`, formats a Markdown brief.
  - `daily_brief.sh` — same idea in Bash with `jq`.
  - `find_and_act.py` — the search-then-act agent pattern, finds
    everything matching a query and suggests a CRM follow-up.
  - `README.md` explaining what's there and the contract they rely on.
- All examples smoke-tested end-to-end against the real CLI.
- README's "For AI agents" section now links to `examples/` alongside
  `AGENTS.md` and `skills/`.
- **Tests:** 319 passing (no source changes).

---

### Iteration 33 — `clibo week` · 2026-05-23

Sister command to `clibo today` — a 7-day rollup across the trackers
with time-series data.

- 🗓️ `clibo week` rolls up the last 7 days: avg sleep hours + quality,
  calorie avg/day, water days that hit the goal, focus minutes &
  sessions, mood average, habit progress vs each habit's weekly
  target (with mini-bars), top expense category, tasks completed,
  journal entries, worklog breakdown.
- Sections are skipped when their tool has no data — the output stays
  short on sparse weeks instead of showing a wall of dashes.
- Same agent contract as the rest: rich panels in human mode, one
  structured dict in `--json` mode.
- README's Cross-tool commands table lists it next to `clibo today`.
- **Tests:** 319 passing (+6).

---

### Iteration 32 — `clibo init` · 2026-05-23

Onboarding command — turns six per-tool `goal --set` calls into one.

- 🚀 `clibo init` accepts `--currency`, `--height-cm`, `--calorie-goal`,
  `--water-goal-ml`, `--focus-goal-min`, `--sleep-goal-hours` and
  `--meditate-goal-min`. With no flags it just prints the current
  defaults — handy as `clibo init --json` for an agent to read the
  user's profile at once.
- Sets the shared `money/currency` and writes per-tool goal settings
  that the individual `goal` commands already read from.
- Mismatch validation (negative numbers, blank currency) fails fast.
- README's Cross-tool commands table now leads with `clibo init`;
  install section suggests one-shot onboarding.
- **Tests:** 313 passing (+6).

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
