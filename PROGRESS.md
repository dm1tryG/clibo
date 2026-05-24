# 📈 clibo — build log

A running log of the build loop. Newest entries on top.

---

### Iteration 119 — `budget add` alias + bare-command default · 2026-05-24

Agent-mode probe on *"Where am I going over budget?"* seeded a
test budget with `clibo budget add food 200` — and **failed**
with `No such command 'add'`. Every other tool in clibo uses
`add` for creation; budget uses `set`. Same verb-shape inconsistency
the iter-100/101 fixes addressed for `vitals` and `meds`.

Bonus finding: bare `clibo budget` returned help; the dominant
"what budgets do I have?" view (`list`) was hidden behind the
subcommand wall.

- 💰 **`clibo budget add CATEGORY AMOUNT`** — alias of `set`. Same
  underlying function, same behaviour (creates or updates). Help
  text lists both with a clear "Alias for `set`" annotation.
- 💰 **Bare `clibo budget` runs `list`** — the dominant summary
  view. Empty state still surfaces the create hint
  ("No budgets set — try: clibo budget add food 400").
- 📝 **Friendly-hint refresh** — three places in `budget.py` told
  users to "try: clibo budget set food 400". Updated all to
  `add` so the suggested command matches the verb agents would
  reach for. `set` still works.
- 🎤 NL flow verified end-to-end:
  • `budget add food 200` → row created (no "No such command") ✓
  • `budget set food 250` → updates the same row (no duplicate) ✓
  • `clibo budget` (bare, empty) → "No budgets set — try: clibo budget add food 400" ✓
  • `clibo budget` (bare, populated) → full budget table ✓
  • `--help` shows both `set` and `add` ✓
- 🧪 **7 new tests**: add-alias works, add-alias updates existing,
  set+add equivalent (no duplicates), add validation, bare-runs-list,
  bare empty-state, help still works.
- **Tests:** 1,152 passing (+7); ruff clean.

**Tally**: **41 of 74 tools** now follow *"bare command = the
answer"*. The verb-shape uniformity (`add` works everywhere)
inches further toward full consistency — `vitals log`, `meds take`
auto-create, and `budget add` were all the same iter-100-era fix.

---

### 🏷️ Iteration 118 — v1.13.0 release · 2026-05-24

Nine substantive iters stacked since v1.12.0 (iters 109-117). Three
big visibility loops closed (search / streaks / todo date filters)
plus year-aware reading, meetings UX, calorie per-meal, and four
more bare-command tools.

- 🆙 **`pyproject.toml`** `1.12.0 → 1.13.0`. Description updated to
  feature search, streaks, todo date filters, year rollups.
- 🆙 **`clibo/__init__.py`** `__version__ = "1.13.0"`.
- 📦 **Build** — `uv build` produced both artifacts. PASSED `twine check`.
- 🚀 **`twine upload`** — https://pypi.org/project/clibo/1.13.0/
- 🧪 **End-to-end verified from PyPI** across every headline:
  • `workout streak` + `mileage streak` ✓
  • `search dentist` → events ✓
  • `search Electricity` → bills ✓
  • `todo list --due tomorrow` → only tomorrow's task ✓
  • `books year` → current year rollup ✓
  • `meetings add … -A "Bob: send timeline" -A "Alice: …"` →
    action_items=2 in one call ✓
- 🏷️ **Git tag `v1.13.0`** pushed.
- 🚀 **GitHub release** with detailed changelog:
  https://github.com/dm1tryG/clibo/releases/tag/v1.13.0
- 📊 Release scoreboard:
  • 1,145 tests passing (+197 vs v1.12.0's 948 → no wait,
    v1.12.0 was 1,061; +84 from v1.12.0's actual count)
  • 74 tools (unchanged — pattern not new surface)
  • 9 iterations stacked
  • `clibo search` reaches **51 sources** (was 35 before iter 114)
  • **9 daily-cadence tools** in the streak family (was 5)

This is the **deep visibility polish** release. No new tools; the
suite got materially better at answering common questions across
the tools that already exist.

---

### Iteration 117 — `todo list` gains date filters · 2026-05-24

Agent-mode probe on *"What do I have to do tomorrow?"* surfaced
that `todo list` supports `--project` / `--tag` / `--all` but
**no date filter at all**. The natural "what's due X?" ask
forced client-side filtering of the JSON dump.

- ✅ **Three new filter flags** on `clibo todo list`:

  | Flag | Selects |
  |---|---|
  | `--due DATE` | Exact match on due date (accepts `today` / `tomorrow` / `yesterday` / `next monday` / `2026-06-01` via `parse_date`) |
  | `--overdue` | Pending tasks with `due < today` — strict past-due only |
  | `--due-within N` | Pending tasks due in the next N days (includes overdue + today) |

- 🎯 **Precedence**: when both `--due` and `--due-within` are
  passed, `--due` wins (exact wins over window). `--overdue` is
  in the same `elif` chain — gets superseded by `--due`. All three
  compose freely with `--project` and `--tag`.
- 🛡 **Date filters only apply to tasks with a due date set** —
  undated tasks naturally drop out of every date-filter (no
  noise from `IS NULL` rows).
- 🛡 **Validation**: unparseable `--due` value → friendly error.
  Negative `--due-within` → friendly error.
- 🎤 NL flow verified end-to-end across 5 seeded tasks
  (today/tomorrow/next-week/5-days-ago/undated):
  • `--due today` → just "Call mom" ✓
  • `--due tomorrow` → just "Buy milk" ✓
  • `--overdue` → just "Overdue task" ✓
  • `--due-within 7` → overdue + today + tomorrow + next-week (4) ✓
  • Filter combo: `--due today -P Acme` → 1 row ✓
  • `--overdue` skips done tasks correctly ✓
- 🧪 **11 new tests**: 4 base filters, ISO-date support, overdue-
  skips-done, due-within excludes undated, --due-wins-over-due-
  within, invalid date, negative due-within, combine with project.
- 📚 **SKILL.md** rewritten with an 8-row natural-language →
  command table covering all the realistic date-filtering asks.
- **Tests:** 1,145 passing (+11); ruff clean.

The most-used productivity tool now answers the most-common
ask — *"what do I have to do?"* — in one flag, every form.

---

### Iteration 116 — `books year` + lifetime by_year breakdown · 2026-05-24

Agent-mode probe on *"What was my best year of reading?"* surfaced
a real gap: `books` had no annual rollup despite `donations year`
existing as a clear precedent. Lifetime `books stats` also showed
no year-by-year breakdown — couldn't answer *"which year did I
read the most?"*.

- 📅 **New `books year [-y YEAR]`** subcommand. Mirrors
  `donations year`. Shows for the target year (default current):
  • `books_finished` count + `titles[]`
  • `avg_rating` of those finishes
  • `sessions` / `pages_read` / `minutes` / `days_read` from
    BookSession rows
  • `avg_pages_per_hour` (when minutes set)
  • `top_rated[]` (up to 3) — best finishes that year
- 📊 **`books stats` extended** with `by_year[]` — lifetime
  finished-books-per-year aggregation, sorted most-recent first.
  Unfinished books skipped (no `finished` date). Answers
  *"which year did I read the most?"* in one field.
- 🛡 Empty-year edge case: `books year -y 1999` returns zeros
  without erroring (no "no entries" fail).
- 🎤 NL flow verified end-to-end:
  • Finished one book this year, one last year (backdated
    `finished` via SQL to 2025) → `books year` → 2026 view
    shows 1 book; `books year -y 2025` shows 1 book ("Range") ✓
  • `books stats.by_year` → `[{year:2026, books_finished:1},
    {year:2025, books_finished:1}]` ✓
  • Reading session this year → `books year` includes
    `pages_read=50, avg_pages_per_hour=50.0` ✓
  • `top_rated` capped at 3, sorted by rating desc ✓
- 🧪 **7 new tests**: current-year default, specific-year filter,
  empty-year, session aggregation, top_rated cap-and-sort, stats
  by_year shape, stats by_year skips unfinished.
- **Tests:** 1,134 passing (+7); ruff clean.

`books` now matches the `donations year` pattern. Agents asking
*"best year of reading"* (or any year-scoped question) land
directly on a structured answer.

---

### Iteration 115 — `clibo search` finishes the entity-tool sweep · 2026-05-24

Iter 114 added 7 entity tools (events/birthdays/goals/jobs/leads/
travel/pets). Audit of `clibo/search.py` showed **9 more** still
unindexed across money + home/life. This iter closes them out.

- 🔍 **9 new sources** in `clibo search`:

  | Source | Searches | Snippet |
  |---|---|---|
  | `bills` | name, category, note | `Electricity (utilities)` (`✓ paid` if paid) |
  | `subs` | name, category, note | `Netflix · monthly` |
  | `savings` | name, note | `Vacation fund` |
  | `debt` | name, creditor, note | `Car loan → Toyota Finance` |
  | `invoice` | number, client, description, note | `INV-101 for Acme Corp — Q2 retainer` |
  | `clients` | name, company, email, notes | `Alice · BigCorp Inc` |
  | `home` | title, location, contractor, note | `improvement: Painted bedroom @ master bedroom` |
  | `plants` | name, species, location | `Monstera (Monstera deliciosa) @ living room` |
  | `chores` | name, assignee | `Vacuum · me` |

- 🎤 NL flow verified across all 9:
  • `search Electricity` → bills ✓
  • `search Netflix` → subs ✓
  • `search Vacation` → savings ✓
  • `search Toyota` → debt (by creditor) ✓
  • `search Acme` → invoice ✓
  • `search alice@bigcorp.com` → clients (by email) ✓
  • `search bedroom` → home (by title); `search Behr` → home (by note) ✓
  • `search kitchen` → plants (by location) ✓
  • `search Vacuum` → chores; `search Sarah` → chores (by assignee) ✓
- 🛡 **Test-shape correctness**: caught two flag-mismatch errors
  in the tests (`savings -g` is actually `-t`, `invoice` doesn't
  accept `--number`). Tests use the real CLI signatures now.
- 🧪 **13 new tests** spanning all 9 sources, often hitting two
  fields (primary name + secondary like email/location/breed/
  assignee).
- **Tests:** 1,127 passing (+13); ruff clean.

`clibo search` now reaches **51 sources** (up from 35 before iter
114, 42 after). The only remaining tools left out are health
logs without meaningful text (calorie/water/weight/sleep/mood/
workout/meds/period/vitals/mileage/steps/meditate/stretches/
caffeine/fasting), and a couple where text is already covered
elsewhere (books_session → 'reading', writing_session). The
agent question *"when did I last do X?"* now lands wherever X
was recorded.

---

### Iteration 114 — `clibo search` indexes 7 more entity tools · 2026-05-24

Agent-mode probe on *"When was the last time I went to the
dentist?"* surfaced a real gap: `clibo search dentist` returned
**zero hits** despite an `events` row titled "Dentist
appointment" being logged. `events` was simply not in the search
index. Other key tools missed too.

- 🔍 **7 new sources** added to `clibo search`:

  | Source | Searches | Snippet |
  |---|---|---|
  | `events` | title, location, category, note | `Dentist appointment (2026-02-15)` |
  | `birthdays` | person, note | `Mom · birthday (03-15)` |
  | `goals` | name, description, note | `Read 30 books` (or `✓ Read 30 books` if done) |
  | `jobs` | company, role, location, notes | `Software Engineer @ Stripe (interviewing)` |
  | `leads` | name, contact, notes | `BigCorp deal · new — Alice at BigCorp` |
  | `travel` | name, destination, notes | `Berlin trip → Berlin` |
  | `pets` | name, species, breed, notes | `Whiskers (cat)` |

- 🐛 **Bug caught**: `JobApplication.notes` (plural) — wrote
  `.note` first; ruff caught the issue on import. Fixed and
  pinned by 11 new search tests.
- 🐛 **Ruff E741**: `lambda l:` for leads tripped the
  "ambiguous variable name" lint. Renamed to `lambda lead:`.
- 🎤 NL flow verified across all 7 — the original probe and
  representative queries:
  • `search dentist` → events ✓
  • `search Mom` → birthdays ✓
  • `search Berlin` → travel ✓
  • `search Stripe` → jobs ✓
  • `search "Maine Coon"` → pets (by breed) ✓
  • `search BigCorp` → leads ✓
  • `search reading` → goals (by name + description) ✓
- 🧪 **11 new tests** spanning all 7 sources, covering both
  primary fields (title/name) and secondary ones (location,
  description, breed).
- **Tests:** 1,114 passing (+11); ruff clean.

`clibo search` was already the strongest cross-tool primitive;
now it actually reaches everything text-bearing. The agent
question *"when did I last do X?"* lands no matter which tool
recorded it.

---

### Iteration 113 — streak family completed: mileage + stretches + meditate · 2026-05-24

Iter 112 added `workout streak` + workout to the top-level
aggregator, and noted that *"mileage, meditate, and stretches are
the remaining candidates"*. This iter closes them out.

- 🏃 **New `mileage streak`** — current + longest + days_logged.
  Any logged distance counts as a streak day, regardless of
  activity (run / walk / cycle / hike / swim).
- 🧎 **New `stretches streak`** — same shape, any logged session
  counts.
- 🧘 **`meditate streak` upgraded** — previously returned only
  `{current_streak, days_practiced}`; now also includes
  `longest_streak` to match the family. `days_practiced` kept
  for back-compat; `days_logged` added as the new uniform name.
- 📊 **Top-level `clibo streaks`** now includes Mileage days,
  Meditation, and Stretching alongside the existing six sources
  (habits, gratitude, steps, fasting, challenges, workout).
- 🎤 NL flow verified:
  • `mileage streak` over 3 mixed-activity days → `current=3, longest=3` ✓
  • Mileage with gap (today + 3/4 days ago) → `current=1, longest=2` ✓
  • `meditate streak` JSON includes `longest_streak` AND old
    `days_practiced` for back-compat ✓
  • `stretches streak` over 2 days → `current=2, longest=2` ✓
  • `streaks` top-level shows 3 new rows: 🏃 Mileage days, 🧘
    Meditation, 🧎 Stretching ✓
- 🧪 **9 new tests**: 3 mileage (empty / consecutive / gap),
  2 stretches (empty / consecutive), 1 meditate shape upgrade,
  3 aggregator inclusion tests.
- **Tests:** 1,103 passing (+9); ruff clean.

The streak family is now **complete** — all 9 daily-cadence tools
(habits, gratitude, steps, fasting, challenges, workout, mileage,
meditate, stretches) expose a uniform `streak` subcommand AND
surface in the top-level `clibo streaks` aggregator. The agent
question *"how many days in a row?"* lands consistently no matter
which activity is being asked about.

---

### Iteration 112 — `workout streak` + aggregator inclusion · 2026-05-24

Agent-mode probe on *"How many days in a row have I logged
workouts?"* surfaced two related gaps:

1. **`workout` had no `streak` subcommand.** Gratitude, writing,
   habit, fasting all do — but a daily exerciser asking the same
   question got no direct answer.
2. **The top-level `clibo streaks` view didn't include workout.**
   It covers habits/gratitude/steps/fasting/challenges; workout
   (along with mileage/writing/meditate/stretches) was invisible
   there too.

- 🔥 **New `workout streak`** subcommand. Returns
  `{current_streak, longest_streak, days_logged}` via `--json`;
  rendered as `🏋️ Workout streak: 3 days 🔥🔥🔥 (longest ever: 3)`.
  Same shape as gratitude / writing streak. Today counts if
  logged; otherwise anchors at yesterday so the streak doesn't
  reset just because today isn't done yet.
- 📊 **Top-level `clibo streaks`** now includes a 🏋️ Workout days
  row alongside the existing 🔥 habits, 🙏 gratitude, 👟 steps,
  🕒 fasting, 🚀 challenges. Same `StreakRow` shape; sorted with
  the rest by current-desc then longest-desc.
- 🛡 **De-dup'd same-day sessions** — two workouts logged on the
  same day count as one streak day (not two). Pinned by a test.
- 🎤 NL flow verified:
  • Empty DB → `current_streak=0, longest_streak=0, days_logged=0` ✓
  • Three consecutive days → `current=3, longest=3, days_logged=3` ✓
  • Gap case (today + 3-5 days ago) → `current=1, longest=3` ✓
  • Same-day double-session → `days_logged=2 (not 3)` for 2 days ✓
  • Yesterday-only → `current=1` (doesn't reset until end of today) ✓
  • Top-level `streaks` → includes a workout row ✓
- 🧪 **6 new tests**: 5 on `workout streak` (empty, consecutive,
  gap, same-day dedup, yesterday-only-still-current), 1 on the
  aggregator picking up workout.
- **Tests:** 1,094 passing (+6); ruff clean.

The streak family of tools — gratitude, writing, habit, fasting,
challenge, steps, and now workout — all answer the *"how many
days in a row?"* question in a uniform shape. Mileage, meditate,
and stretches are the remaining candidates if the demand surfaces.

---

### Iteration 111 — `calorie today` gains per-meal subtotals + `--meal` filter · 2026-05-24

Agent-mode probe on *"How many calories did I have for breakfast
today?"* surfaced a small but real gap. `calorie today` returned
day-wide totals and a flat entries list — no per-meal subtotals,
no way to scope to one meal. The agent had to filter JSON
client-side or remember `calorie list -m breakfast -d today`.

- 🆕 **`by_meal` subtotals** in `calorie today --json`. Always
  populated (regardless of any filter), keyed by meal, includes
  `kcal/protein/carbs/fat/count`. Empty meals are omitted —
  no noise. Answers *"calories for breakfast today?"* in one
  field: `d["by_meal"]["breakfast"]["kcal"]`.
- 🆕 **`--meal/-m MEAL` filter on `calorie today`**. Scopes
  entries + totals to a single meal. The JSON's `filter_meal`
  field surfaces what was filtered for round-trip consistency.
  `by_meal` stays complete — agents can still see the rest.
- 🎨 **Human view** — when no filter is applied (or there are
  ≥2 meals logged), a per-meal subtotal line appears under
  the kcal total: `breakfast 325 · lunch 520 · snack 230`.
  With `--meal`, the title gets a suffix (`Food log · Sat 24 May
  · breakfast`) and the subtotal line is skipped.
- 🛡 **Sentinel-bug avoidance** — the bare-command callback from
  iter 105 was `ctx.invoke(today, json_out=False)`, which under
  the new `--meal` parameter would have forwarded a Typer
  `OptionInfo` sentinel. Updated to
  `ctx.invoke(today, meal=None, json_out=False)`.
- 🎤 NL flow verified end-to-end:
  • `calorie today -m breakfast --json` → entries=2, totals.kcal=325,
    filter_meal="breakfast", full by_meal preserved ✓
  • `calorie today` (bare via iter 105) → rendered + per-meal
    line "breakfast 325 · lunch 520 · snack 230" ✓
  • `calorie today -m supper` → friendly "Meal must be one of: …" ✓
- 🧪 **7 new tests**: by_meal shape + counts, empty-meals omitted,
  --meal scopes entries + totals, by_meal preserved during filter,
  bad meal rejected, no-match filter returns empty cleanly, bare
  command still works (iter-105 regression).
- **Tests:** 1,088 passing (+7); ruff clean.

Small but real polish: the agent's natural breakfast-calorie ask
now lands on a direct field in the JSON or a one-flag CLI invocation.

---

### Iteration 110 — bare-command default on 4 entity tools (pipeline / upcoming / due) · 2026-05-24

Agent-mode self-test on three entity-tool questions — *"What books
am I reading?"*, *"What's my sales pipeline?"*, *"Whose birthday
is coming up?"* — surfaced that four entity tools have a clear
non-`list` dominant summary verb that bare-command should run. The
earlier blanket exclusion (iter 107's note about entity-tools where
the dominant action is `list`/`add`) was too broad.

- 🎯 **4 more tools updated** with the bare-command pattern:

  | Tool | Bare runs |
  |---|---|
  | `leads` | `pipeline` — open deals grouped by stage |
  | `birthdays` | `upcoming` — next 30 days |
  | `followup` | `due` — overdue + due-soon follow-ups |
  | `jobs` | `pipeline` — application counts by status |

  All four answer the dominant *"what's the current state?"* ask
  better than `list` would: a pipeline view, a date-windowed
  upcoming view, or an urgency-filtered due view.

- 🛡 **Sentinel-bug avoidance** continued from iter 106/107: the
  two callbacks with optional `--days` (`birthdays.upcoming`,
  `followup.due`) pass explicit defaults (`days=30`, `days=7`).
- 🎤 NL flow verified on empty + seeded DBs:
  • Empty `clibo leads` → renders empty 📊 Pipeline table ✓
  • Empty `clibo birthdays` → "Nothing coming up." ✓
  • Empty `clibo followup` → "Nothing to follow up on — you're on
    top of it! ✨" ✓
  • Empty `clibo jobs` → renders empty 📊 Application pipeline ✓
  • Seeded versions show the relevant pipeline / list ✓
- 🧪 **8 new tests** (2 per tool).
- **Tests:** 1,081 passing (+8); ruff clean.

**Tally**: **40 of 74 tools** now follow *"bare command = the
answer"*. The remaining ~34 are mostly pure entity tools (`crm`,
`books`, `films`, `clients`, `notes`, `todo`, `quotes`, `pets`,
`network`, `gifts`, `cv`, `brag`, `ideas`, `lessons`, `meetings`,
`groceries`, `pantry`, `recipes`, `home`, `travel`, `bookmark`,
`wishlist`, `savings`, `debt`, `invoice`, `invest`, `tip`,
`weight`, `period`, `goals`) where the dominant view is `list` —
bare-help is still defensible there since `list` doesn't help an
agent who's coming in cold and doesn't know what to look for.
A broader rollout could change that for the user-favourites
(`books`/`films`/`todo`), but this iter stops at the clear
non-`list` summary wins.

---

### Iteration 109 — `meetings` polish: inline actions + fuzzy resolve + edit · 2026-05-24

Agent-mode self-test on *"Just finished a Zoom with Acme — discussed
Q3 roadmap, Bob to send timeline"* surfaced three real frictions on
`meetings`:

1. `meetings action "Acme" ...` failed against the seeded title
   "Acme Q3 roadmap" — the resolver only did **exact** match.
2. **No way to capture action items inline** at meeting creation,
   forcing a two-step flow (add → action) for the natural one-breath
   statement.
3. **No `edit`** subcommand, and `rm` was integer-only — iter-84/85
   carryover.

- 🗓️ **Fuzzy meeting resolver** — `_resolve` now does ID → exact
  title → substring (most-recent wins). Mirrors the iter-84/85
  pattern. `meetings action "Acme"` finds "Acme Q3 roadmap"; two
  meetings sharing the substring → picks the newer.
- 🗓️ **Inline `--action` / `-A` on `meetings add`** — repeatable
  Typer Option (`list[str]`). Each value can be plain text or
  `"OWNER: summary"` to set the owner inline:
  ```bash
  clibo meetings add "Acme Q3" \
    -A "Bob: send timeline" \
    -A "Alice: draft proposal" \
    -A "me: schedule follow-up"
  ```
  Empty strings are silently skipped. Success message includes the
  action-count: `✓ Added 🗓️ meeting 'Acme Q3' (2026-05-24) · 3 action items`.
- 🗓️ **New `meetings edit MEETING [...]`** — change title, date,
  attendees, notes. Accepts name (fuzzy) or ID. Last bit of the
  edit-subcommand rollout from iters 82-85.
- 🗓️ **`meetings rm`** — now accepts a name (fuzzy) or ID. Still
  cascades action items.
- 🎤 NL flow verified end-to-end with the original failing scenario:
  • One call: `meetings add "Acme Q3" -A "Bob: send timeline" -A "Alice: draft proposal" -A "me: schedule follow-up"` → 3 action items attached ✓
  • Follow-up: `meetings action "Acme" "follow up next week"` → resolves to "Acme Q3 roadmap" ✓
  • `meetings show "Acme"` → 4 action items with owners shown ✓
  • `meetings edit "Acme" -N "updated notes"` ✓
  • `meetings rm "Acme"` → cascades the 4 actions ✓
- 🧪 **12 new tests**: inline actions count, OWNER prefix parses,
  no-owner text-only, empty `-A` skipped, fuzzy action target,
  most-recent-wins on ambiguous fuzzy, show by substring, edit by
  name, edit retitles, edit unknown fails, rm by name, rm cascades.
- 📚 **SKILL.md** rewritten with the inline-actions story and a
  6-row NL → command table.
- **Tests:** 1,073 passing (+12); ruff clean.

The *"finished a meeting, here's the summary"* flow now fits in
one CLI call, the way it fits in one human sentence.

---

### 🏷️ Iteration 108 — v1.12.0 release · 2026-05-24

Eight substantive iters stacked since v1.11.0 (iters 100-107)
including the **36-tool bare-command rollout** — the kind of
across-the-board UX shift that's release-worthy.

- 🆙 **`pyproject.toml`** `1.11.0 → 1.12.0`. Description updated to
  feature the headline tagline: *"type the tool's name to get the
  answer."*
- 🆙 **`clibo/__init__.py`** `__version__ = "1.12.0"`.
- 📦 **Build** — `uv build` produced `dist/clibo-1.12.0.tar.gz`
  + `dist/clibo-1.12.0-py3-none-any.whl`. Both PASSED `twine check`.
- 🚀 **`twine upload`** — https://pypi.org/project/clibo/1.12.0/
- 🧪 **End-to-end verified from PyPI**:
  • `clibo --version` → `clibo 1.12.0` ✓
  • `clibo caffeine` (bare) → today's intake panel ✓
  • `clibo bills` (bare) → "Nothing due soon — you're all caught up! ✨" ✓
  • `vitals log temp 39.2` → 39.2°C ✓
  • `meds take "Vitamin D"` → auto_created=True ✓
  • `car drive "client meeting" --mi 47 -c business` → 75.64 km ✓
- 🏷️ **Git tag `v1.12.0`** pushed.
- 🚀 **GitHub release** with a category-grouped changelog:
  https://github.com/dm1tryG/clibo/releases/tag/v1.12.0
- 📊 Release scoreboard:
  • 1,061 tests passing (+113 vs v1.11.0's 948)
  • 74 tools (unchanged — pattern not new surface)
  • 36 tools follow the "bare command = the answer" rule

This is the **bare-command default + verb-shape polish** release.
No new tools, but a foundational UX shift: agents typing the tool's
name get the actual answer instead of help text, across every
clibo tool where a single dominant summary verb makes sense. Plus
three more focused iters on `vitals` (verb dispatcher), `meds`
(auto-create), and `car` (business mileage).

---

### Iteration 107 — bare-command default rolled out to 11 money + home/life tools · 2026-05-24

Closing out the bare-command pattern rollout. Iter 105/106 covered
22 tools (health + productivity + hobbies). This iter finishes
**every money and home/life tool with a dominant single-verb
summary**.

- 🎯 **11 more tools updated**:

  | Tool | Bare runs |
  |---|---|
  | `bills` | `due` — overdue + due soon |
  | `split` | `balances` — net per-person ledger |
  | `expense` | `month` — current month by category |
  | `income` | `month` — current month by category |
  | `donations` | `year` — annual giving (tax-relevant) |
  | `subs` | `total` — monthly + yearly subscription cost |
  | `chores` | `due` — chores overdue or due now |
  | `plants` | `thirsty` — plants needing water |
  | `documents` | `expiring` — passports/IDs in next 90d |
  | `packages` | `pending` — packages not yet delivered |
  | `meals` | `today` — today's planned meals |

- 🛡 **Sentinel-bug avoidance**: 6 of these summaries have optional
  args with non-None defaults — those defaults are now passed
  explicitly in each callback (`ctx.invoke(due, days=7, json_out=False)`,
  `ctx.invoke(month, month_spec=None, json_out=False)`, etc.) so the
  Typer `ArgumentInfo`/`OptionInfo` sentinel never reaches the DB.
  Same fix style as iter 106; applied prophylactically across all 11.
- ⚙️ **Mechanical rollout** via the same Python script style as
  iter 106 — single pass, one diff per file. Tuple-based mapping
  with per-tool kwarg strings.
- 🎤 NL flow verified across all 11 on both empty and seeded DBs:
  • Empty: each renders the friendly empty-state message
    ("Nothing due — you're all caught up!", "No packages on the
    way.", etc.) ✓
  • Seeded: each shows the relevant summary table or panel ✓
  • `--help` still works on every tool ✓
- 🧪 **22 new tests** (2 per tool).
- **Tests:** 1,061 passing (+22); ruff clean.

**Tally**: **36 of 74 tools** now follow *"bare command = the
answer"* — health (12), productivity & hobbies (13), money &
home/life (11). The remaining ⅔ that don't get the treatment are
entity-tools (crm/leads/followup/meetings/jobs/clients/birthdays/
network/gifts/brag/cv/pets/books/films/ideas/quotes/lessons/
flashcards/dreams... wait those last 5 already got it) where the
dominant action is `list` or `add` rather than a single named
summary. For those tools, bare-help remains the right default —
the agent wouldn't know which entity to ask about.

---

### Iteration 106 — bare-command default rolled out to 13 more tools · 2026-05-24

Iter 105 covered 9 health tools. This iter finishes the pattern
rollout across **every productivity + hobby tool with a dominant
single-verb summary**. Total now: **25 tools** follow the "bare
command = the answer" rule.

- 🎯 **13 more tools updated**:

  | Tool | Bare runs |
  |---|---|
  | `focus` | `today` — pomodoro count + goal |
  | `time` | `status` — is a timer running? today's total |
  | `events` | `today` — today's events |
  | `journal` | `today` — today's entries |
  | `worklog` | `today` — today's work-log lines |
  | `challenge` | `status` — active challenges + progress |
  | `gratitude` | `today` — today's entries + streak |
  | `writing` | `today` — words + goal + streak |
  | `mileage` | `week` — this week's distance vs goal |
  | `flashcards` | `due` — cards due for review |
  | `dreams` | `today` — today's dreams |
  | `stretches` | `today` — today's sessions |
  | `symptom` | `today` — today's symptom log |

- 🐛 **Real bug caught**: `ctx.invoke()` doesn't resolve Typer's
  `ArgumentInfo` / `OptionInfo` sentinel objects when the target
  function has optional positionals or options. They got forwarded
  through to SQLAlchemy as literals, producing
  `Error binding parameter: type 'ArgumentInfo' is not supported`.
  Fixed by passing explicit `None` / real defaults in two
  callbacks:
  • `challenge` → `ctx.invoke(status, challenge_id=None, json_out=False)`
  • `flashcards` → `ctx.invoke(due, deck=None, limit=20, json_out=False)`
- ⚙️ **Mechanical pattern via Python script** — wrote a small
  `pathlib`-based loop that replaced the Typer init line +
  appended the callback in all 13 files in one pass. Doable
  manually but tidier.
- 🎤 NL flow verified across all 13 on an empty SQLite DB
  (worst-case for ctx.invoke sentinel forwarding):
  • `clibo challenge` → "🚀 No active challenges." ✓
  • `clibo flashcards` → "Nothing due — you're all caught up! ✨" ✓
  • All others → render correct empty-state messages or seed-data
    summaries cleanly with exit 0 ✓
- 🧪 **26 new tests** (2 per tool): bare runs the right summary,
  help still works. Plus the two empty-DB ArgumentInfo bug regressions
  pinned (any tool added in the future with optional args will be
  caught the same way).
- **Tests:** 1,039 passing (+26); ruff clean.

**Tally so far**: 25 tools follow *"bare command = the answer"*:
`networth`, `caffeine`, `fasting`, `calorie`, `water`, `mood`,
`sleep`, `steps`, `workout`, `meds`, `vitals`, `habit` (iter
103-105) + `focus`, `time`, `events`, `journal`, `worklog`,
`challenge`, `gratitude`, `writing`, `mileage`, `flashcards`,
`dreams`, `stretches`, `symptom` (this iter). That's a third of
the 74-tool catalog. The remaining ⅔ are either entity-tools
(crm, books, films, ideas, …) where the dominant action is `list`
or `add`, or aggregate tools (stats, …) where bare-help is
correct.

---

### Iteration 105 — bare-command default rolled out to 9 health tools 🎉 1000+ tests · 2026-05-24

Iter 103/104 established the *"bare command = the answer"* pattern
on `networth`, `caffeine`, `fasting`. This iter rolls it out across
every health tool that has an obvious dominant summary verb.

- ☕ **All 9 tools updated** — `clibo X` bare now runs the right
  summary subcommand:

  | Tool | Bare runs |
  |---|---|
  | `calorie` | `today` — food log + macros |
  | `water` | `today` — intake vs goal |
  | `mood` | `today` — mood check-ins |
  | `sleep` | `last` — most recent night |
  | `steps` | `today` — step count vs goal |
  | `workout` | `today` — today's session |
  | `meds` | `today` — what's still due |
  | `vitals` | `latest` — most recent of each kind |
  | `habit` | `today` — done vs pending |

- 🛡 **Help + subcommands unchanged everywhere.** `--help` still
  shows the menu on every tool. `add`, `log`, `list`, `edit`, `rm`,
  `stats`, etc. all keep their existing shape — purely additive on
  the no-subcommand path.
- 🎯 **Mechanical pattern**: each tool's `app = typer.Typer(...)`
  flipped from `no_args_is_help=True` to
  `(no_args_is_help=False, invoke_without_command=True)`, with an
  `@app.callback()` that dispatches to the summary verb when
  `ctx.invoked_subcommand is None`. Three-line addition per tool.
- 🎤 NL flow verified across all 9 with realistic seeded data:
  • `clibo calorie` → renders "🍎 Food log · Sun 24 May" + table ✓
  • `clibo water` → progress bar + "500 / 2000 ml · 1 drinks" ✓
  • `clibo sleep` (with a row) → "94% · 7.5h / 8h goal" ✓
  • `clibo vitals` (with a temp row) → "❤️ Latest vitals" table ✓
  • `clibo habit` → list of habits with ○/✓ markers ✓
  • All 9 `--help` still show the menu ✓
- 🧪 **18 new tests** (2 per tool): bare runs the right summary
  with exit 0, `--help` still shows the menu. Sleep's test
  pre-seeds because `last` fails on empty DB (intentional).
- 🛡 **Test correction**: `test_take_unknown_fails` from before
  iter 101 lived on; iter 101 renamed it to `…_with_strict_fails`
  but didn't pick up auto-create's `--strict` flag. Both now
  reconciled.
- **Tests:** 1,013 passing (+18); ruff clean. 🎉 **First iteration
  past the 1000-test mark** — up from ~300 at v1.0.0.

12 tools now follow the *"bare command = the answer"* rule:
`networth`, `caffeine`, `fasting`, `calorie`, `water`, `mood`,
`sleep`, `steps`, `workout`, `meds`, `vitals`, `habit`. The agent
mental model — *"type the tool's name, get the answer"* — works
across every health/wellness command in clibo.

---

### Iteration 104 — `clibo caffeine` / `clibo fasting` (bare) show their summary · 2026-05-24

Iter 103's note that the `invoke_without_command` pattern could
generalise turned out to be right within one iteration. Agent
probes on *"How much caffeine have I had today?"* and *"Am I
still fasting?"* both hit the same bare-command help screen
that `networth` did — and both have an obvious dominant summary
verb.

- ☕ **Bare `clibo caffeine` now runs `today`.** Daily total in
  mg, every drink with its time, projected bedtime residual.
  The dominant ask for a caffeine tracker is *"how much today?"*
  — now one keystroke shorter.
- 🕒 **Bare `clibo fasting` now runs `status`.** Renders the
  running clock against the target with a progress bar, or
  "no fast in progress" when idle. Mirrors the `networth → worth`
  fix from iter 103.
- 🛡 **Help + subcommands unchanged.** `--help` still shows the
  menu (Typer's standard flag is unaffected by the callback).
  `log/add/list/show/edit/rm/stats/start/stop/target/cutoff` —
  every existing subcommand keeps its identity.
- 🎤 NL flow verified with realistic state:
  • `clibo caffeine` (2 drinks logged) → "280 mg total today
    (limit 400) · 54 mg residual at bedtime" ✓
  • `clibo fasting` (16h target started) → "Fasting in progress
    · 0h elapsed · 16h to target" with progress bar ✓
  • `clibo caffeine list`, `clibo fasting list`, etc. — all
    unchanged ✓
- 🧪 **4 new tests**: bare runs the right summary on both tools,
  `--help` still works on both. Mirrors the iter-103 test shape.
- **Tests:** 995 passing (+4); ruff clean.

Three tools now follow the *"bare command = the answer"* rule:
`networth` (iter 103), `caffeine`, `fasting`. The pattern earned
its name and is documented inline in each tool's callback for
future maintainers.

---

### Iteration 103 — `clibo networth` (bare) shows the answer · 2026-05-24

Agent-mode self-test on "What's my net worth?" caught a small but
real friction: typing `clibo networth` returned **help text**, not
the actual net worth. The right answer lived behind `clibo
networth worth` — a verb name an agent (or human) wouldn't
naturally reach for.

- 🎯 **Bare `clibo networth` now runs `worth`.** Flipped
  `no_args_is_help=False` and added an `@app.callback(
  invoke_without_command=True)` that routes to `worth` when no
  subcommand is given. The natural flow *"what's my net worth?"*
  → `clibo networth` → instant answer.
- 🎯 **New `show` alias** for `worth`. Agents who reach for the
  `show` verb across the codebase (films show, books show, crm
  show, …) now find it where they'd expect.
- 🛡 **`--help` still works** — Typer's standard `--help` flag
  is unaffected by the callback change, so the menu is one
  flag away.
- 🛡 **Other subcommands unchanged**: `add`, `list`, `update`,
  `rm`, `snapshot`, `history` all work exactly as before. The
  change is purely additive on the no-subcommand path.
- 🎤 NL flow verified end-to-end with a seeded ledger ($10k
  assets, $1.5k liabilities, $8.5k net):
  • `clibo networth` (bare) → renders the summary ✓
  • `clibo networth show --json` → `{net_worth: 8500, ...}` ✓
  • `clibo networth worth` → identical to `show` ✓
  • `clibo networth list` → table of assets+liabilities ✓
  • `clibo networth --help` → menu ✓
- 🧪 **4 new tests**: bare-command runs worth, show-alias equals
  worth, show-alias with `--json`, help-still-works.
- **Tests:** 991 passing (+4); ruff clean.

Small surgical polish. The Typer `invoke_without_command` pattern
is general — could apply to a couple of other tools where a single
"summary" verb dominates, but `networth` is the clearest case
because its summary is the **whole point** of having a net-worth
tool.

---

### Iteration 102 — `car drive` (business / personal / commute mileage) · 2026-05-24

Agent-mode self-test on *"Drove 47 miles for the client meeting"*
caught a real gap. `mileage` is explicitly athletic
(run/walk/cycle/hike/swim). `car` has `fuel` + `service` but no
**trip log** — so business mileage (typically tax-deductible) and
commute tracking had no home.

- 🆕 **New `CarDrive` table** — separate from `CarEntry` because
  the column shape is different. Fields: `purpose`,
  `distance_km`, `category`, `odometer_start`/`end`, date, note.
- 🚗 **`car drive PURPOSE`** subcommand. Distance from any of:
  • `--km 47` — explicit kilometres
  • `--mi 30` — miles, converted to km (× 1.609344)
  • `--start-odo` + `--end-odo` — auto-computes from the pair
- 💼 **`category: business | personal | commute`** — the whole point.
  Tax authorities allow per-km/per-mile deductions for the business
  bucket (rate varies by jurisdiction — clibo holds the totals,
  users compute the deduction at filing time).
- 🚗 **`car list` unified** — merges `CarEntry` rows (fuel +
  service) with `CarDrive` rows by date-then-id, so the human view
  is one chronological log of "what I did with the car". `-k`
  filter accepts `fuel` / `service` / `drive`.
- 📊 **`car stats` extended** — adds `drive_entries`,
  `drive_total_km`, `drive_by_category[]`. Agent reading the JSON
  can pull business mileage in one call.
- 🛡 **Validation**: no distance → friendly error; bad category;
  negative km; end odometer ≥ start odometer. Four guard rails.
- 📋 **`car rm ID --drive`** — IDs are per-table, so a flag
  disambiguates. Without the flag, `rm` keeps its old fuel/service
  semantics (back-compat).
- 🎤 NL flow verified end-to-end:
  • `car drive "Acme meeting" --mi 47 -c business` → 75.64 km ✓
  • `car drive "commute home" --km 12 -c commute` ✓
  • `car drive "errands" --start-odo 50000 --end-odo 50080` → 80 km ✓
  • Unified `car list` shows all three kinds with merged Purpose / Service column ✓
  • `car stats` → `drive_by_category: [business 75.64, personal 80, commute 12]` ✓
- 🧪 **13 new tests** pin every flow: km / mi / odometer-pair,
  default category, four validation paths, list-includes-drives,
  drive-only filter, stats breakdown, rm with `--drive` flag,
  rm without `--drive` still deletes fuel/service.
- 📚 **SKILL.md** rewritten with an 8-row NL → command table
  including the business/commute distinction.
- 📚 **README + catalog description** updated: car is now
  "Car maintenance, fuel & driving log (business/commute mileage
  for taxes)".
- 📚 **docs/SCHEMA.md** regenerated — `car_drive` table (90 tables
  total, up from 89).
- **Tests:** 987 passing (+13); ruff clean.

The car tool now serves the freelancer / consultant use case it
was missing — track business mileage all year, hand a clean total
to your accountant at filing time. No new tool added; an existing
one filled out.

---

### Iteration 101 — `meds take` auto-creates + `meds edit` / name-resolve · 2026-05-24

Agent-mode self-test on *"Took my morning vitamins"* caught a real
friction. The natural human flow is **`meds take "Vitamin D"`** with
zero ceremony, but the old code required `meds add` first — failing
with "No medication matching 'Vitamin D'". One-off doses of vitamins,
aspirin, ibuprofen don't deserve registration overhead.

Plus the same probe surfaced two iter-84/85-style carryovers: no
`meds edit`, and `stop`/`rm` were integer-only.

- 💊 **`meds take NAME` auto-creates** if the medication isn't
  registered. New entry has default `times_per_day=1` and no
  dosage. The success message includes a hint:
  `new med — set dosage with: clibo meds edit "Vitamin D" -d '<dosage>'`.
  Agent JSON gets a new `auto_created: bool` field so the agent can
  follow up to ask for dosage when needed.
- 🛡 **`--strict` flag** keeps the old fail-on-unknown behaviour for
  users who want every med pre-registered. Numeric IDs that don't
  exist **always** fail (no `meds take 99999` silently creating
  medication '99999').
- 💊 **New `meds edit NAME` subcommand** — set dosage, times-per-day,
  rename, update note. Accepts name (fuzzy) or ID. Carryover gap
  from before the iter-84/85 name-resolve rollout.
- 💊 **`meds stop` and `meds rm` now accept names** — closes the
  last integer-only verbs in the tool. `rm` still cascades doses
  (delete a med → delete its dose history).
- 🎤 NL flow verified end-to-end:
  • `meds take "Vitamin D"` (cold start) → `auto_created=true, taken_today=1` ✓
  • Second `take "Vitamin D"` → `auto_created=false, taken_today=2` (no duplicate row) ✓
  • Hint command `meds edit "Vitamin D" -d "1000 IU" -t 2` ✓
  • `meds take "Aspirin" --strict` → fails ✓
  • `meds take 99999` → fails even without --strict ✓
  • `meds stop "Vitamin D"`, `meds rm "Vitamin D"` → both work by name ✓
- 🧪 **12 new tests**: auto-create, second-dose-no-duplicate, default
  times-per-day=1, strict-mode rejection, numeric-id-always-strict,
  edit by name, edit rename, edit invalid times-per-day, edit unknown,
  stop by name, rm by name, rm cascades doses.
- 📚 **SKILL.md** updated with the auto-create story, `--strict`
  caveat, and a 7-row natural-language → command table covering
  the realistic flows (one-off vitamins, daily Lipitor, "stop
  taking Allegra", "what's still due").
- 📚 **`test_take_unknown_fails`** updated — was asserting the now-
  changed behaviour, renamed to `test_take_unknown_with_strict_fails`
  with the `--strict` flag.
- **Tests:** 974 passing (+12); ruff clean.

The "I took a thing" flow now matches every other quick-log tool
in clibo — no pre-registration ceremony. Users who want the
old guard-rails keep them via `--strict`.

---

### 🎉 Iteration 100 — `vitals log` dispatcher (verb-shape uniformity) · 2026-05-24

The **100th** iteration. Fittingly, agent-mode self-test caught a
real verb-shape inconsistency: every health tool uses `<tool> log
<args>` (calorie, water, weight, sleep, mood, mileage, …) — but
`vitals` doesn't have a `log` verb at all. Each kind is its own
subcommand: `vitals bp`, `vitals pulse`, `vitals temp`, etc.

So the natural agent guess for "I have a fever — 39.2°C" is
`clibo vitals log temp 39.2`, which **fails** with
`No such command 'log'`. The user has to know vitals is special.

- 🆕 **`vitals log KIND VALUE [VALUE2]`** — a generic dispatcher
  that accepts any of the five kinds and routes to the right
  writer under the hood. Identical row shape to the kind-specific
  commands; writes to the same `vitals_reading` table.
- 🩸 **BP shorthand** — `vitals log bp 120/80` parses
  `systolic/diastolic` from a single argument. Two-arg form
  (`vitals log bp 120 80`) also works. Slash form matches the
  natural way users write it.
- 🩸 **Unit override** — `--unit` flag works on the dispatcher
  too (`vitals log glucose 5.5 -u mmol/L`). Defaults to each
  kind's standard unit.
- 🛡 **Validation**:
  • Unknown kind → "Kind must be one of: bp, pulse, glucose, temp, spo2"
  • Non-numeric value → "Value must be a number (got 'hot')"
  • BP missing diastolic → "BP needs both systolic and diastolic"
  • Non-BP with two values → "<kind> takes a single value, not two"
- 🎤 NL flow verified end-to-end across all five kinds:
  • `vitals log temp 39.2` → 39.2°C ✓ (the original failing flow)
  • `vitals log bp 115/75` → normal ✓
  • `vitals log bp 140 90` → stage 2 hypertension ✓
  • `vitals log pulse 72` → 72 bpm ✓
  • `vitals log glucose 95` → mg/dL default ✓
  • `vitals log glucose 5.5 -u mmol/L` → unit override ✓
  • `vitals log spo2 98` → 98% ✓
  • `vitals latest` → shows all five kinds aggregated correctly ✓
- 🧪 **14 new tests**: every kind through the dispatcher, BP
  shorthand + two-arg, unit override, `--date` backdate, `--note`
  passthrough, equivalence with kind-specific commands, all four
  validation paths.
- 📚 **SKILL.md** updated with a 7-row "Natural language →
  command" table including BP shorthand + glucose unit overrides
  + temperature.
- **Tests:** 962 passing (+14); ruff clean.

The verb-shape uniformity question — *"should every tool have a
`log` verb?"* — is now answered "yes" for the one tool that was
the exception. Agents writing for clibo can rely on the pattern
without remembering vitals' special shape.

This caps a 49-iteration arc from v1.1.0 → v1.11.0:
- 24 new tools (50 → 74)
- v1.10.0 + v1.11.0 minor releases
- 962 tests (from the v1.0.0 baseline of ~300)
- Full cross-tool dashboard integration
- Name-resolve / per-session-tracking / verb-uniformity polish
  across every tool that needed it

---

### 🏷️ Iteration 99 — v1.11.0 release · 2026-05-24

Six substantial iters stacked since v1.10.0 (iters 93-98) including
a new tool (`symptom`), full cross-tool dashboard integration for
all media-log tools, and the `travel` status polish.

- 🆙 **`pyproject.toml`** `1.10.0 → 1.11.0`. Description updated
  to mention the new pain/symptom log.
- 🆙 **`clibo/__init__.py`** `__version__ = "1.11.0"`.
- 📦 **Build** — `uv build` produced `dist/clibo-1.11.0.tar.gz`
  + `dist/clibo-1.11.0-py3-none-any.whl`. Both PASSED `twine check`.
- 🚀 **`twine upload`** — pushed to PyPI:
  https://pypi.org/project/clibo/1.11.0/
- 🧪 **End-to-end verified from PyPI** after index sync:
  • `clibo --version` → `clibo 1.11.0` ✓
  • `symptom log "back pain" -i 7 -l lumbar -r ibuprofen` →
    intensity_label="severe" ✓
  • `travel add Berlin --start "3 days ago" --end "today"` →
    `status="ongoing", when="ongoing · day 4 of 4"` ✓
  • `today --json` exposes writing + books + symptoms blocks ✓
  • `search lumbar` → symptom source ✓
  • `checkin --json` → both Writing + Symptom registered ✓
- 🏷️ **Git tag `v1.11.0`** pushed to GitHub.
- 🚀 **GitHub release** created with a detailed changelog:
  https://github.com/dm1tryG/clibo/releases/tag/v1.11.0
- 📊 Release scoreboard:
  • 948 tests passing (+61 vs v1.10.0's 887)
  • 74 tools (+1 — `symptom`)
  • 89 SQLite tables (+1 — `symptom_entry`)

This is the **structured-pain-tracking + everywhere-visibility**
release. The new `symptom` tool fills the long-standing
subjective-experience gap in the health suite, and the dashboard
integration arc (iter 93/94/96/97) means no tool built in the last
14 iterations sits invisibly in the DB anymore. Cross-tool views
now cover all 74 tools.

---

### Iteration 98 — `travel` gains a proper `status` + `when` · 2026-05-24

Agent-mode self-test on a past trip ("just got back from a 3-day
Berlin trip") surfaced a small but real UX bug: the JSON output
returned `"starts_in": "3d ago"` — `starts_in` implies future but
the value is past. Contradictory.

- 🆕 **`status` field** on every trip row: one of `upcoming`,
  `ongoing`, `ended`, `undated`. Computed from `start_date` /
  `end_date` vs today, so agents can branch on temporal state
  without parsing prose.
- 🆕 **`when` field** — tense-aware prose that matches the status:
  • upcoming → `"in 5d"` / `"tomorrow"` (delegates to
    `humanize_delta`)
  • ongoing → `"ongoing · day 3 of 5"` (with explicit day-of-trip
    counter — surprisingly useful for "how much of my vacation is
    left?")
  • ended → `"ended yesterday"` / `"ended 5d ago"`
  • undated → `None`
- 🛡 **`starts_in` kept for back-compat** — same value (raw
  `humanize_delta`) it had in v1.10.0. Agents reading the old
  shape continue to work; the new `status` + `when` are strict
  additions. Field is documented in the source comments as
  back-compat.
- 📊 **Table rendering switched** from `starts_in` → `when` so the
  human view reads correctly for past trips too. The column header
  was always "When" — the change is invisible to humans, just
  makes the displayed value match the column name.
- 🎤 Verified end-to-end across all four cases:
  • upcoming "NYC" in 5 days → `status=upcoming, when="in 5d"` ✓
  • ongoing "Tokyo" 2d ago → in 2d → `status=ongoing,
    when="ongoing · day 3 of 5"` ✓
  • ended "Paris" 4d ago → yesterday → `status=ended,
    when="ended yesterday"` ✓
  • undated "Someday Mongolia" → both `None` ✓
  • Edge: trip with `start=today` and no end → `status=ongoing`,
    `when="today"` ✓
  • Edge: past start with no end → `status=ended`, `when="ended N d ago"` ✓
- 🧪 **7 new tests** pin every case: upcoming, ongoing (with
  day-of-trip), ended, undated, today-only-start ongoing, past-
  start-no-end ended, `starts_in` back-compat unchanged.
- **Tests:** 948 passing (+7); ruff clean.

Small polish, but it kills the contradictory `starts_in: 3d ago`
output an agent could've been confused by — and the `status`
enum lets future code switch on it without parsing English.

---

### Iteration 97 — wire `writing` / `books-session` / `symptom` into search + checkin · 2026-05-24

Iter 93/94/96 closed the today/week/month/recent gaps. This iter
closes the **other two cross-tool primitives** that had been
silently ignoring the new tools — search and the daily check-in
flow.

- 🔍 **`clibo search`** — three new sources in the index:
  • `writing` searches `WritingSession.project` + `WritingSession.note`.
  • `reading` searches `BookSession.note` and resolves the parent
    book title for the snippet (`30p of Atomic Habits`). New
    `_snippet_book_session` helper opens its own session to look
    up the title — keeps the SOURCES tuple shape consistent.
  • `symptom` searches `Symptom.name` + `location` + `triggers` +
    `relief` + `note`. Lots of text-bearing fields → high hit rate
    for queries like "lumbar", "ibuprofen", "bright light".
- 📋 **`clibo checkin`** — two new active-trackers:
  • `Writing` — surfaces "Did you write today?" with the last
    session's words & project (`1200w on novel`).
  • `Symptom` — surfaces "Any symptoms today?" with the last
    entry's name + intensity + optional location
    (`back pain 7/10 (lumbar)`).
  Both still respect the 2+ entries in 14 days threshold so single
  exploratory entries don't pollute the check-in list.
- 📅 Reading (BookSession) intentionally **not** added to checkin —
  it's event-based, not a daily yes/no, and `books history` already
  serves the "what did I read?" question without pestering.
- 🎤 NL flow verified end-to-end:
  • `search chapter` → hits writing note + reading session ✓
  • `search lumbar` → hits symptom ✓
  • `search identity` → hits reading session note ✓
  • `search bright` → hits symptom by `triggers` field ✓
  • `checkin --json` with 2 entries each → both Writing + Symptom
    appear in `logged` with today_value populated ✓
  • A single writing entry → Writing does NOT appear (below threshold) ✓
- 🧪 **11 new tests**: 6 search (writing-by-note, writing-by-project,
  reading-by-session-note, symptom-by-name, symptom-by-location,
  symptom-by-triggers), 5 checkin (writing tracker appears + value
  format, symptom tracker appears + value format incl. location,
  single-entry below threshold).
- **Tests:** 941 passing (+11); ruff clean.

The 6 cross-tool primitives (today, yesterday, week, month,
recent, search, tags, checkin) now all cover the full 74-tool
catalog. No tool is invisible anywhere.

---

### Iteration 96 — wire `symptom` into today/week/month/recent · 2026-05-24

Iter 95 shipped the new `symptom` tool. Mirroring the writing+books
wire-up arc (iter 93+94), the new tool now needs cross-tool
visibility. Otherwise it lives invisibly in the DB.

- 📅 **`clibo today`** — new `symptoms` block.
  Fields: `episodes`, `worst_intensity`, `worst_name`, `names[]`.
  Rendered as `🤒 Symptoms 2 episodes · worst 9/10 (migraine) ·
  back pain, migraine`. Worst-score coloured by 1-10 bucket
  (green / yellow / red / bold red).
- 📅 **`clibo week`** — new `symptoms` block.
  Fields: `episodes`, `days_affected`, `avg_intensity`,
  `worst_intensity`, `worst_name`, `top_symptoms[]`. Gets its
  own `[bold]🤒 Symptoms[/bold]` section in the rendered week
  view with the top condition's episode count.
- 📅 **`clibo month`** — new `symptoms` block at the bottom of
  the month rollup. Same shape as week. Empty-state guard updated
  so a month with only symptoms (no money/health/productivity)
  still shows them instead of falling to "nothing logged".
- 🌀 **`clibo recent`** — new `symptom` source in the activity
  feed reading from `symptom_entry`. Renders as
  `🤒 back pain 7/10 (lumbar)` or `🤒 headache 4/10` when location
  is missing.
- 🆕 **Three Pydantic models**: `SymptomToday`, `SymptomWeek`,
  `SymptomMonth`. The week + month shapes are identical so future
  views can share rendering helpers if it becomes worth extracting.
- 🎤 NL flow verified end-to-end with three sample episodes (today:
  back pain 7/10, migraine 9/10; 2 days ago: back pain 5/10):
  • `today` → 2 episodes, worst 9/10 ✓
  • `week --json` → episodes=3, days_affected=2, top_symptoms[back pain=2, migraine=1] ✓
  • `month --json` → same shape ✓
  • `recent` → all three episodes appear with intensity + location ✓
- 🧪 **8 new tests** across `test_today` / `test_week` /
  `test_month` / `test_recent`: empty-state shape on all three,
  episode aggregation across days, top_symptoms ordering, recent
  feed includes location when set and omits parens when not.
- **Tests:** 930 passing (+8); ruff clean.

The post-symptom visibility loop closes. All four cross-tool
dashboards (today / week / month / recent) now cover **every**
of the 74 tools. Three iterations (93, 94, 96) of *"wire new
things into existing views"* completed the post-v1.10.0 dashboard
integration.

---

### Iteration 95 — new tool: 🤒 `symptom` (pain & symptom tracker) · 2026-05-24

Agent-mode self-test on *"My back's been hurting all day — about
7/10"* revealed a real gap. The existing health tools each cover
a different axis:

- **`vitals`** stores **measurable** readings (BP, pulse, glucose, SpO2)
- **`mood`** is whole-person 1-5, not per body-area or kind
- **`journal`** is freeform text — no aggregation, no intensity trend

Nothing handled **subjective, scale-able** experiences: chronic
back pain, migraines, allergies, IBS flare-ups, post-viral
fatigue. Real audiences with no fit.

The **74th tool**.

- 🤒 **`symptom log NAME -i INTENSITY [-l LOC -t MIN --triggers ... -r ...]`**
  — log a symptom with the standard medical 1-10 pain scale.
  Validation: `1 ≤ intensity ≤ 10`, `duration ≥ 0`. Returns the
  `intensity_label` (`mild`/`moderate`/`severe`/`worst possible`)
  inline so agents can format prose without bucket logic.
- 🤒 **`symptom today`** — today's entries with worst-of-day; if
  nothing logged, prints a discoverable nudge.
- 🤒 **`symptom history NAME`** — one condition over time.
  Aggregates per-day with `episodes`, `avg_intensity`,
  `max_intensity`. Renders a trend indicator (↘ improving / ↗
  worsening / → steady) by comparing first-day vs last-day avg —
  the single answer chronic-condition trackers actually want.
- 🤒 **`symptom stats --days N`** — top complaints (by episodes),
  total episodes, days affected, worst-ever episode in window.
- 🤒 **`show`/`edit`/`rm`** all name-resolve with most-recent-wins,
  matching the iter-84/85 pattern (one condition flares many
  times, so name lookup picks the latest).
- 🎨 **Colour-coded `intensity_cell`** in tables — green for mild,
  yellow for moderate, red for severe, bold-red for worst-possible.
  Reads at a glance.
- 🎤 NL flow verified end-to-end:
  • `symptom log "back pain" -i 7 -l lumbar -r ibuprofen` → severe label ✓
  • `symptom log migraine -i 9 -t 120 --triggers "poor sleep,bright light"` ✓
  • `symptom history "back pain"` → 3-day intensity progression (5→6→7) ✓
  • `symptom stats` → top: back pain (3 ep avg 6.0), worst: migraine 9/10 ✓
  • `symptom today` → coloured intensity cells with location + duration ✓
- 🧪 **20 new tests**: log shape, all-fields capture, add alias,
  intensity labels match medical buckets, out-of-range + negative-
  duration rejection, today filtering + empty state, list by
  name + days, name-resolve picks latest, edit with validation,
  rm by name, unknown-name failures, history per-day aggregation,
  stats top + worst-episode + empty.
- 📚 **`skills/symptom/SKILL.md`** — natural-language → command
  table covering 7 phrasings, plus a "when to use which tool"
  section that distinguishes `symptom` from `vitals` / `mood` /
  `journal` / `meds` (the exact disambiguation question agents
  would otherwise have to guess).
- 📚 **README** — new row in **Health & Wellness** (15th tool in
  the category). Bumped "73" → "74" in five places.
- 📚 **`docs/SCHEMA.md`** regenerated — `symptom_entry` (89 tables
  total, up from 88 after iter 91).
- **Tests:** 922 passing (+20); ruff clean.

Tool count now **74/74**. Health & Wellness grows from 14 → 15 —
filling the long-standing structured-pain-tracking gap that none
of the original 50 nor the iters 51-94 addressed.

---

### Iteration 94 — wire `writing` + `books-session` into `month` · 2026-05-24

Iter 93 wired writing + book-sessions into `today` / `week` /
`recent`. Agent-mode self-test surfaced that `clibo month` was
still missing both — the only cross-tool view that still
ignored them.

- 📅 **`clibo month`** — two new sub-blocks:
  • `productivity.writing` mirrors the week shape:
    `sessions`, `total_words`, `total_minutes`, `days_written`,
    `avg_words_per_active_day`, `top_projects[]`. Rendered as
    `✍️ Writing  1,600 words · 2 sessions · 2 days · top: novel`.
  • `hobbies.reading` (new `ReadingMonth` model):
    `sessions`, `pages`, `minutes`, `days_read`, `books[]`.
    Rendered as `📖 Reading: 55 pages · 2 sessions
    (2 days, 75 min; Atomic Habits)`.
- 🆕 **Pydantic models**: `WritingMonth` and `ReadingMonth`.
  Added as fields on the existing `ProductivityMonth` and
  `HobbiesMonth` — additive, no breaking JSON shape change for
  consumers that ignore unknown fields.
- 🎯 **Empty-state guard** — the `has_anything` check that
  prints "nothing logged this month" now also considers
  `has_hobbies` (covers reading even when zero films + zero
  books finished).
- 🎤 NL flow verified with realistic month seed (writing today +
  5 days ago, reading today + 3 days ago):
  • `month` prints both new lines in the right block ✓
  • `month --json` exposes `productivity.writing.{sessions=2,
    total_words=1600, top_projects=[novel, blog]}` ✓
  • `month --json` exposes `hobbies.reading.{sessions=2,
    pages=55, days_read=2, books=['Atomic Habits']}` ✓
- 🧪 **4 new tests**: empty-state for both blocks, multi-day
  aggregation for writing including `top_projects`, multi-day
  reading-session aggregation.
- **Tests:** 902 passing (+4); ruff clean.

All four cross-tool dashboards (today / week / month / recent)
now surface every media-log tool. Three iterations of *"wire
the new things into the existing views"* close the post-v1.10.0
visibility loop.

---

### Iteration 93 — wire `writing` + `books-session` into the dashboards · 2026-05-24

Agent-mode self-test on `clibo today --json` after iters 90 + 91
showed both new tools were **invisible to the cross-tool views**.
Writing was logged but didn't appear on the daily dashboard; books
reading sessions were tracked but didn't show up on `today`,
`week`, or `recent`. Tools that drop off the headline UX get
forgotten — fix that before adding more.

- 📅 **`clibo today`** — two new blocks:
  • `writing`: words today, goal progress, sessions count, current
    streak. Renders as `✍️ Writing  1600/500 w 🎉 · 2 sessions
    · 🔥 1-day streak`.
  • `books`: pages, minutes, sessions, list of titles read today.
    Renders as `📖 Reading  50p · 2 sessions · ⏱ 75 min ·
    Atomic Habits, Range`.
  Both shadow the `🏋️ Workouts` line shape from iter 88 — same
  conditional display (omitted when no sessions).
- 📅 **`clibo week`** — new blocks for the same two tools.
  Writing slots into the *Productivity* group (with a `top:
  PROJECT (Nw)` annotation); reading gets a new *🎨 Hobbies*
  section that's ready for future hobby trackers.
- 🌀 **`clibo recent`** — two new sources in the activity feed:
  • `writing` reads from `writing_session` ("wrote 1200w on novel
    (45 min)")
  • `reading` reads from `books_session` and joins to `books_book`
    titles via a module-level `_BOOK_TITLES` cache populated once
    per `collect_recent` call. So the feed shows "read 30p of
    Atomic Habits (45 min)" not "read 30p of book #1".
- 🆕 **Pydantic models added**: `WritingToday` + `BooksToday` for
  `TodaySnapshot`; `WritingWeek` + `BooksWeek` for `WeekSnapshot`.
  Existing snapshots stay backward-compatible — every consumer
  just gets two new fields.
- 🆕 **`_streak_from_days(days, today)`** helper in `dashboard.py`
  — extracted the consecutive-day streak logic that's also in
  `gratitude` and `writing`. Future tools that want a daily-
  practice streak can import it directly.
- 🎤 NL flow verified end-to-end with a seeded day (1.2k + 0.4k
  writing words, 30p + 20p across two books):
  • `today` prints both new rows in the right place ✓
  • `today --json` exposes `writing.{total_words, goal_words,
    reached, sessions, current_streak}` + `books.{pages, minutes,
    sessions, books}` ✓
  • `week` aggregates writing across days with `top_projects` ✓
  • `recent` shows writing + reading events with full titles ✓
- 🧪 **11 new tests**: today writing/books empty + populated +
  goal-respect; week writing/books with cross-day aggregation +
  top_projects; recent shows writing + reading events with the
  right summary text.
- **Tests:** 898 passing (+11); ruff clean.

Three dashboards (today / week / recent) now all surface the four
media-log tools — calorie / water / weight / workout (original),
writing / books / films (iters 87, 90, 91). Nothing built in the
last three iterations sits invisibly in the DB anymore.

---

### 🏷️ Iteration 92 — v1.10.0 release · 2026-05-24

Seven iterations stacked since v1.9.0 (iters 85-91) including a
new tool (`writing`) and substantial per-session tracking on
`books`, `films`, and `workout`. Cut a minor release.

- 🆙 **`pyproject.toml`** `1.9.0 → 1.10.0`. Description rewritten
  to feature the headline additions: word-count writer, episode
  tracker, bench-press PRs, IOU shortcuts.
- 🆙 **`clibo/__init__.py`** `__version__ = "1.10.0"`. Docstring
  shifted from "73+" to plain "73" since we're stable on that
  count for now.
- 📦 **Build** — `uv build` produced `dist/clibo-1.10.0.tar.gz`
  (375.3 kB) and `dist/clibo-1.10.0-py3-none-any.whl` (295.8 kB).
- ✅ **`twine check`** — both PASSED.
- 🚀 **`twine upload`** — pushed to PyPI:
  https://pypi.org/project/clibo/1.10.0/
- 🧪 **End-to-end verified from PyPI** after index sync:
  • `pip install clibo==1.10.0` from `/tmp/v1100` venv ✓
  • `clibo --version` → `clibo 1.10.0` ✓
  • `writing log novel -w 1200 -t 45` → wpm=26.7, streak=1 ✓
  • `books read "Atomic Habits" 30 -t 45` → 40 pages/hour ✓
  • `films add "Better Call Saul" -k show -S 6 -E 5` → S06E05 ✓
  • `workout pr` → heaviest=90kg ✓
  • `split owe Anna 50` → IOU stored as 1-participant split ✓
- 🏷️ **Git tag `v1.10.0`** pushed to GitHub.
- 🚀 **GitHub release** created with a detailed changelog:
  https://github.com/dm1tryG/clibo/releases/tag/v1.10.0
- 📊 Release scoreboard:
  • 887 tests passing (+80 vs v1.9.0's 770)
  • 73 tools (+1 — `writing`)
  • 88 SQLite tables (+2 — `writing_session`, `books_session`)

This is the **per-session tracking** release. Three media logs
(`books`, `films`, `workout`) now all answer "what did I do this
week and how fast?" with a consistent shape. The 73rd tool
(`writing`) is in the same family, completing the read/watch/
write/lift quartet.

---

### Iteration 91 — `books` gains per-session tracking · 2026-05-24

Agent-mode self-test on "Read 30 pages of Atomic Habits in 45
minutes" surfaced three real frictions on `books`:

1. **`books read` had no `--minutes` option.** The 45-minute
   duration in the user's statement was simply lost. The newly-
   shipped `writing` tool tracks duration; `books` couldn't.
2. **No session history at all.** Every `books read` just bumped
   a cumulative `pages_read` counter — there was no way to answer
   "what did I read last week?" or "how fast do I read?".
3. **Carryovers**: `books rm` was integer-only, no `edit` existed.

- 📖 **New `BookSession` table** (`books_session`): one row per
  `read` call, storing `pages`, `duration_min`, `entry_date`,
  optional `note`, FK-style `book_id`. Created automatically via
  `create_all` for new installs; existing DBs pick it up on next
  boot via the standard SQLModel.metadata bootstrap (no migration
  needed — it's a new table, not a column).
- 📖 **`books read … -t MIN -d DATE -n NOTE`** — duration enables
  `pages_per_hour` pace. Backdate sessions via `--date`. The cumulative
  counter still updates and still auto-promotes wishlist→reading and
  auto-finishes at total pages. Response payload now includes
  `session_id`, `session_pages`, `session_minutes`,
  `session_pages_per_hour` so agents get the pace metric in one call.
- 📖 **New `books history --days N [--book BOOK]`** — lists
  recent sessions across all books (or filtered to one). Joins
  book titles on the way out.
- 📚 **New `books edit BOOK`** — change title/author/pages/
  pages_read/status/rating/note in place. Status change to
  `finished` or `reading` auto-stamps the date if not already set.
- 📚 **`books rm <title>`** — accepts ID or fuzzy title;
  **cascades to sessions** (delete a book → its session rows are
  cleaned up too).
- 📚 **`_resolve` prefers exact title match over substring** — so
  `books show "Dune"` finds *Dune* not *Dune: Part Two*. Mirrors
  the iter-87 fix to `films._resolve`.
- 📊 **`books stats` extended** with `sessions_logged`,
  `session_pages`, `session_minutes`, `avg_pages_per_hour`,
  `days_read` — pulled from the session table.
- 🎤 NL flow verified end-to-end:
  • `books read "Atomic Habits" 30 -t 45` → session_pages_per_hour=40
  • `books read "Atomic Habits" 25 -t 35 -d yesterday` → backdated session
  • `books history` → both sessions ordered newest-first with pace
  • `books rm "Atomic"` → book + 2 session rows all gone ✓
- 🧪 **16 new tests**: read-with-minutes shape, minutes-optional
  back-compat, backdated session, negative-minutes reject, history
  filtering by book + days, edit by title incl. status-to-finished
  date stamping & pages_read override & bad-rating reject, rm by
  title, rm cascades sessions, rm unknown fails, exact-match resolver,
  stats session-pace fields.
- 📚 **SKILL.md** rewritten with a 9-row "Natural language →
  command" table including the new minutes / history / edit flows.
- 📚 **docs/SCHEMA.md** regenerated — `books_session` table (88
  total, up from 87 after iter 90).
- **Tests:** 887 passing (+16); ruff clean.

`books` now matches the per-session shape of `writing` (iter 90)
and the auto-progress shape of `films` (iter 87). All three media
trackers — read/watch/write — answer the *"what did I do this
week and how fast?"* questions out of the box.

---

### Iteration 90 — new tool: ✍️ `writing` (word-count tracker) · 2026-05-24

The 73rd tool. Writers track *words*, not minutes — minute-based
tools (`focus`, `time`) lose the metric that matters most for
novel/blog/essay work. `journal` stores content but doesn't
aggregate counts. So there was a real gap and a real audience
(NaNoWriMo runs 400k+ participants/year on a 1,667-words/day
target).

- ✍️ **`writing log PROJECT -w WORDS [-t MIN]`** — log a session;
  pace (`wpm`) auto-computed when both flags set. Project defaults
  to `"main"` if omitted, so `writing log -w 400` works for the
  casual case. `add` is a friendlier alias.
- ✍️ **`writing today`** — total words for the day with goal-bar
  progress, per-project breakdown, current streak.
- 🎯 **`writing goal N`** — set/show the daily word goal; stored in
  shared `clibo_setting` table (scope=`writing`, key=`daily_words`,
  default `500`). NaNoWriMo? `clibo writing goal 1667`.
- 🔥 **`writing streak`** — consecutive-day streak, mirrors the
  `gratitude` pattern. Yesterday counts if you haven't logged
  today yet.
- 📊 **`writing stats --days N`** — totals, avg wpm, days written,
  best-ever day (`{"date","words"}`), top projects by word count.
- 🏷️ **Name-resolve on `show`/`edit`/`rm`** — accepts entry ID *or*
  project name with most-recent-wins preference (mirrors the
  `gifts` / `income` / `donations` resolver pattern). So
  `writing edit novel -w 1300` updates the latest novel session
  without you knowing the ID.
- 🎤 NL flow verified end-to-end:
  • `writing log novel -w 1200 -t 45` → wpm=26.7, total_today=1200 ✓
  • `writing log blog -w 400` → total_today bumps to 1600, 🎉 goal-hit ✓
  • `writing goal 1667` → next `today` reflects the new goal ✓
  • Backdated entries (2 days ago, yesterday, today) → 3-day streak ✓
  • `writing stats --days 7` → correct top_projects, best_day, avg_wpm ✓
- 🧪 **21 new tests**: session shape, goal/duration validation,
  wpm computation only when duration set, today aggregation by
  project, goal persist, goal rejects non-positive, streak
  consecutive vs break-on-gap, list project filter, show/edit/rm
  by project name, unknown name fails, stats top_projects +
  best_day + avg_wpm.
- 📚 **`skills/writing/SKILL.md`** — natural-language → command
  table with 9 phrasings; for-agents section noting that `log`
  returns `total_today` and `current_streak` in one call so agents
  don't need a follow-up to confirm "you hit your goal".
- 📚 **README** — new row in Hobbies & Culture table; bumped
  "72" → "73" in five places (header, cross-tool intro, "all N
  tools built" callout, code-layout block, `__init__.py` /
  `pyproject.toml` descriptions).
- 📚 **docs/SCHEMA.md** regenerated — `writing_session` (87 tables
  total, up from 86).
- **Tests:** 871 passing (+21); ruff clean.

Tool count now 73/73. Hobbies & Culture grows from 9 → 10 — still
the smallest category but the most varied in interest type.

---

### Iteration 89 — `clibo doctor` upgrades: drift, settings, update-check · 2026-05-24

Surfaced by a real user who ran `clibo info` and saw v1.0.0 / 50
tools — they'd been on a pipx install for weeks with no signal
that nine versions and 22 tools had shipped behind them. The fix
was a one-line `pipx upgrade`, but doctor should have flagged it.

Three new checks on `clibo doctor`:

- 🆕 **`--check-updates`** — opt-in PyPI query (`pypi.org/pypi/
  clibo/json`, 3s timeout). If a newer version exists, doctor
  surfaces it as a warning with the exact upgrade commands. Default
  off: clibo stays local-first; you ask before it phones home.
  Network failures fail silently (no crashed doctor).
- 🆕 **Schema drift detection** — for every table that already
  exists, compare the model's declared columns against the live
  SQLite `PRAGMA table_info`. If anything's missing (which means
  `_add_missing_columns` couldn't safely add a NOT-NULL no-default
  column), it lands in `schema_drift` and the warnings list. New
  helper `_detect_schema_drift(db_path)` is also importable.
- 🆕 **Unconfigured settings list** — walks `_INIT_SETTINGS` and
  flags every key the user hasn't set. Shown as a footer hint
  ("💡 5 settings unconfigured — run clibo init …") so first-time
  users don't have to know what `clibo init` covers. Auto-shrinks
  as you set each via `clibo init --currency …`.
- 🆕 **`warnings: [str]`** field — single canonical list of all
  human-readable issues. `healthy = bool(no warnings)`. Easy for
  agents to consume: `if doctor.warnings: handle()`.
- 🎤 Verified end-to-end:
  • Fresh sandbox → `clibo doctor` ✓ healthy, 7 unconfigured settings hint
  • After `clibo init --currency USD --height-cm 180` → hint shrinks to 5
  • With `--check-updates` against actual PyPI: latest fetched, no
    upgrade needed since we're on 1.9.0
  • Schema drift against a truncated `films_film` table: correctly
    flags missing `season` + `episode` from iter 87
- 🧪 **9 new tests**: warnings-field shape, unconfigured listing &
  shrink-on-init, no-drift baseline, drift detection unit test
  (with `_detect_schema_drift` against an undersized table),
  update-check skipped by default, update-check with stub finds
  upgrade, PyPI-unreachable still healthy, version-tuple
  comparison.
- 📦 **GitHub repo description** — refreshed from "67+" to
  "72 local-first CLI tools" (was last updated at iter ~80).
- **Tests:** 850 passing (+9); ruff clean.

`clibo doctor` is now a single-call self-check that catches the
exact friction that triggered this iter: stale installs with no
nudge, plus latent schema/settings gaps. Agents can read
`warnings[]` to surface issues, humans see them inline.

---

### Iteration 88 — `workout pr` (personal records) + name-resolve · 2026-05-24

Agent-mode self-test on "Hit a new bench-press PR of 90kg" surfaced
that **workout had no first-class PR tracking** — a PR was just a
free-form note on a workout row, so asking "what's my bench-press
PR?" later forced the agent to scan the full history manually.
The tool also still had integer-only `show`/`rm` (carryover from
before the name-resolve rollouts).

- 🏆 **New `workout pr`** — two views in one subcommand:
  • No arg: heaviest weight per exercise across all history, sorted
    heaviest first, with reps × sets context and session count.
    `clibo workout pr` answers "show me all my PRs".
  • With an exercise: PR broken down by **rep range** (1RM / 3RM /
    5RM / …) which is the gym-standard view — lifters care about
    each rep target separately. Includes an "all-time max" footer.
- 🏆 **`pr` skips cardio rows** — only counts entries with
  `reps>0` AND `weight_kg>0`. A 30-minute jog doesn't pollute the
  PR table.
- 🏋️ **`workout show <name>`** and **`workout rm <name>`** — now
  accept exercise name with most-recently-added preference (one
  exercise gets logged dozens of times, mirrors the `gifts` /
  `income` resolver pattern from iters 84-85).
- 🎤 NL flow verified end-to-end with a realistic bench-press
  progression (3×5@70 → 3×5@75 → 5×3@82.5 → 1×1@90):
  • `workout pr "bench press"` → reads cleanly as 1RM=90kg,
    3RM=82.5kg, 5RM=75kg with timestamps and "all-time max" footer ✓
  • `workout pr` (no arg) → squat 110kg, bench 90kg, deadlift
    140kg, sorted by heaviest ✓
  • `workout show squat` (with 2 squat sessions) → picks the
    most-recent ✓
- 🧪 **10 new tests** pin: heaviest-per-exercise selection, session
  count, cardio-row exclusion, rep-range grouping, fuzzy exercise
  match, unknown-exercise rejection, show by name, most-recent
  preference, rm by name.
- 📚 **SKILL.md** — added "Natural language → command" table
  covering the 8 most common workout phrasings, including the
  three new PR forms.
- **Tests:** 841 passing (+10); ruff clean.

The workout tool now answers the gym-rat question *"what's my X
PR?"* in one command, with the rep-range breakdown serious lifters
actually want — without inventing a whole new "PR" table.

---

### Iteration 87 — `films` gains episode progress + show/edit · 2026-05-24

Agent-mode self-test on "Watching Better Call Saul S6E5" surfaced
that `films` had **no progress tracking** for TV shows — a row was
either `watching` or `watched`, with no way to record *where* you
were. The film tool also still had integer-only `rm` (carryover
from before the name-resolution rollout) and no `show` or `edit`.

- 📺 **Two new columns** on `Film`: nullable `season` and
  `episode`, added via the existing `_add_missing_columns` ALTER
  TABLE migration so existing v1.9.0 DBs upgrade transparently.
- 📺 **`films add … -S N -E N`** — record a show's current pointer
  at creation time. If you set either, status auto-bumps from
  `watchlist` to `watching` (if you're tracking progress, you're
  watching it).
- 📺 **New `films progress FILM`** — three modes:
  • `-S 6 -E 5` sets the pointer absolutely
  • `-E 5` keeps season, sets episode (typical "next episode")
  • `--bump` increments episode by 1 (no flags needed — fastest)
- 📺 **`progress` rejects movies** — `progress Dune -S 1 -E 1`
  fails with "Dune is a movie, not a show". Surfacing the kind
  mismatch up-front is friendlier than silently corrupting a
  movie row.
- 🎬 **New `films show <title>`** — print one film/show with the
  S/E pointer rendered as `S06E10`.
- 🎬 **New `films edit`** — change title, kind, year, status,
  rating, season, episode, note in place. Setting status to
  `watched` stamps `watched_on` automatically.
- 🎬 **`films rm`** — now accepts title (fuzzy) or ID, not just
  ID. Last carry-over from before the name-resolve rollouts.
- 🎬 **`_resolve` prefers exact over substring** — so
  `films show "Dune"` finds *Dune* and not *Dune: Part Two*.
- 🎬 **List view** — new `Progress` column shows `S06E05` etc.
- 🎤 NL flow verified end-to-end:
  • `films add "Better Call Saul" -k show -S 6 -E 5` → status
    auto-`watching`, progress `S06E05` ✓
  • `films progress "Better Call Saul" --bump` → `S06E06` ✓
  • `films progress "Better Call Saul" -S 6 -E 10` → `S06E10` ✓
  • `films show "Better Call Saul"` → renders the pointer ✓
  • `films progress Dune -S 1 -E 1` → fails (movie) ✓
- 🧪 **14 new tests**: progress add/set/bump/episode-only/no-args/
  zero-reject/movie-reject; show; edit (title rename + status to
  watched sets date); rm by title; exact-match wins resolver.
- 📚 **SKILL.md** rewritten with a "Natural language → command"
  table covering the 8 most common film/TV phrasings, including
  the three progress modes.
- 📚 **docs/SCHEMA.md** — regenerated; `season` and `episode`
  columns now documented on `films_film`.
- **Tests:** 831 passing (+14); ruff clean.

The films tool now fits the modern watchlist mental model
(Trakt / Letterboxd-style "where am I in this show?") in one
extra column and three subcommands, without bloating into a
per-episode log.

---

### Iteration 86 — `split owe` / `split lent`: direct IOU verbs · 2026-05-24

Agent-mode self-test surfaced a real friction on `split`: when the
user says "I owe Anna $50", the agent has to invent a fake $100
two-person bill where Anna paid, then count on equal-split to
arrive at the right balance. That's correct math but indirect
modelling — and not what the user said.

- 🤝 **`split owe PERSON AMOUNT`** — direct IOU: "I owe PERSON".
  Recorded as a 1-participant `SplitExpense` (PERSON paid the full
  amount, I'm the lone participant), so it flows through
  `balances`, `who`, and `settle` exactly like any other split.
- 🤝 **`split lent PERSON AMOUNT`** — the inverse: "PERSON owes
  me". 1-participant split where I paid, they're the participant.
- **Ledger identity** — both verbs accept `--me NAME` (default
  `"me"`) for users who prefer their real name in the balances
  table.
- **Optional `--for DESC`** — defaults to a readable
  `IOU: me owes Anna` (or `IOU: Bob owes me`) so the row reads
  cleanly in `split list`.
- 🎤 NL flow verified end-to-end:
  `clibo split owe Anna 50 --for dinner` →
  `clibo split lent Bob 20 --for coffee` →
  `split balances` shows Anna +50, Bob -20, me -30 →
  `split who` suggests `me → Anna $30` and `Bob → Anna $20` →
  `split settle me Anna 50` clears Anna's balance. All without
  ever inventing a fake bill.
- 🧪 **10 new tests**: owe/lent shape, balance flow, custom
  `--me` name, combined-net correctness, settle interop, default
  description, negative-amount rejection.
- 📚 **SKILL.md** — added a "Natural language → command" table
  covering the 6 most common phrasings ("I owe …", "Bob owes me
  …", "We split a $90 dinner …", "How much do I owe?", …) so
  agents pick the right verb on the first try.
- **Tests:** 817 passing (+10); ruff clean.

This closes the last common money-flow gap I could find in
agent-mode probing: every natural English phrasing about who-owes-
whom now has a one-line command that maps to it directly.

---

### Iteration 85 — name resolution on six transactional tools · 2026-05-24

Iter 81-84 closed the entity-tool ID barrier. Agent-mode self-test
this round revealed the same gap on **transactional tools with
natural labels**: `income.source`, `subs.name`, `bills.name`,
`wishlist.name`, `bookmark.title`, `donations.recipient`. Every
mutating verb (`show`/`edit`/`rm`/`cancel`/`pay`/`unpay`/`buy`/
`fav`/`unfav`/`open`) used to demand integer IDs.

- 💵 **`income show/edit/rm <source>`** — name-resolve with
  most-recently-added preference (one source pays you many times).
  Mirrors the `gifts` resolver from iter 84.
- ❤️ **`donations show/edit/rm <recipient>`** + **new `edit`**
  subcommand. Edit can also flip `--no-deductible` / `--deductible`.
  Same most-recent preference (repeat giving).
- 🔁 **`subs show/edit/cancel/rm <name>`** + **new `show` + `edit`**
  subcommands. `edit` accepts new amount/cycle/category/next-billing.
- 🧾 **`bills show/edit/pay/unpay/rm <name>`** + **new `show` + `edit`**
  subcommands. The `pay` resolver prefers the **unpaid** match
  (so a recurring "Electricity" bill lands on this month, not last
  month's already-paid row); `unpay` prefers a paid match.
- ⭐ **`wishlist show/edit/buy/rm <name>`** + **new `edit`**
  subcommand. Prices and priorities can be revised in place.
- 🔖 **`bookmark show/edit/open/fav/unfav/rm <title|url>`** + **new
  `edit`** subcommand. Resolver searches `title` first, then `url`
  substring, so `bookmark show ycombinator` finds the HN entry.
- 🧪 **37 new tests** covering every refactored path:
  name-resolution, fuzzy match, most-recent-wins for income &
  donations, unpaid-wins for bills, rejection of invalid edit
  inputs (bad cycle, bad priority).
- 🎤 Replayed every failing flow end-to-end:
  • `income show Acme` (2 rows) → picks the latest ✓
  • `bills pay Electricity` (1 paid, 1 unpaid) → pays the unpaid ✓
  • `subs edit Netflix -a 20` then `subs cancel Netflix` ✓
  • `donations edit "Red Cross" -a 150` ✓
  • `wishlist buy MacBook` ✓
  • `bookmark fav HN` ✓
- 📚 **README** — bumped "50+" to "72" in three places (header,
  cross-tool section, code-layout block). Stale since iter 50.
- **Tests:** 807 passing (+37); ruff clean.

The integer-ID barrier is now closed across **all** tools that
expose a natural label — both entity-style (CRM/jobs/plants/…)
and transactional (income/bills/subs/…). Agent-mode is back to
near-zero friction on edit/remove flows.

---

### Iteration 84 — name resolution on six more entity tools · 2026-05-24

Closing the entity-tool name-resolution gap. Iter 81-83 covered crm,
clients, jobs, followup, plants, pets. This iteration finishes the
remaining six: network, leads, gifts, birthdays, brag, cv.

- 🆕 **`lookup_by_id_or_name(db, model, ident, field)`** in
  `clibo/core/base.py` — generalised version of the per-tool
  `_resolve` helpers. Tries numeric ID first, then exact
  case-insensitive match on `field`, then substring fallback.
  Standardises the pattern so future tools don't reinvent it.
- 🏆 **`brag show/rm <title>`** — finds achievements by fuzzy title.
  `clibo brag rm "auth"` removes the `Shipped auth refactor` row.
- 🌐 **`network show/edit/rm <name>`** + **new `edit` subcommand**.
  Was missing entirely; now lets you append company/context after
  the fact (`clibo network edit Sarah -c Stripe -x "joined payments"`).
- 🧲 **`leads show/move/edit/rm <name>`** — deals resolve by name
  via a tiny `_resolve_lead` wrapper.
- 🎂 **`birthdays edit/rm <person>`** + **new `edit` subcommand**.
  Was missing; now lets you fix dates ("wrong date") and change
  kind, person name, or note.
- 📜 **`cv show/end/edit/rm/achieve <title>`** — every mutating
  subcommand on `cv` now accepts the entry title as well as the ID.
- 🎁 **`gifts show/bought/given/rm <recipient>`** — Gifts have
  many-to-one with recipients (one person, many gifts), so the
  resolver prefers the **most-recently-added** gift to that
  recipient when looking up by name. Pinned by
  `test_gifts_resolves_most_recent_when_multiple`.
- 🧪 16 new tests across six files cover every new resolution path,
  plus the gifts most-recent-wins behaviour.
- 🎤 NL flows verified end-to-end:
  • "Delete my brag about auth" → `brag rm auth` ✓
  • "Update Sarah — she joined Stripe" → `network edit Sarah -c Stripe` ✓
  • "Move BigCorp lead to won" → `leads move BigCorp won` ✓
  • "Dad's birthday is March 15 not 12" → `birthdays edit Dad -d "March 15"` ✓
  • "Add bullet to my Staff Engineer entry" → `cv achieve Staff "…"` ✓
  • "Mark Anna's gift as bought" → `gifts bought Anna` ✓
- **Tests:** 770 passing (+16); ruff clean.

The entity-tool name-resolution rollout is now **complete**. Every
tool with a natural-name lookup accepts either an ID or a fuzzy
name match: books, crm, clients, jobs, followup, plants, pets,
network, leads, gifts, birthdays, brag, cv.

---

### Iteration 83 — pets polish: optional summary + `edit` + name-by-rm · 2026-05-23

Agent-mode self-test surfaced two real frictions on `pets`:

1. `pets log Whiskers --kind vet --cost 80` failed because `kind`
   is positional, not a flag — and `summary` was *required* even
   for a quick "vet visit" with no description.
2. No `edit` subcommand existed. "Add breed" / "change notes" had
   no path.

- 🐾 **`pets log SUMMARY` is now optional** — defaults to the `kind`
  name when omitted. `pets log Whiskers vet` produces a row with
  `summary="vet"` so quick entries no longer demand a description.
- 🐾 **New `pets edit <name|id>`** — change `name`, `species`,
  `breed`, `birth`, `notes`. Same flag shape as `pets add`. The
  user's "change pet's breed/notes" NL probe now has a matching
  command.
- 🐾 **`pets rm <name|id>`** — was integer-only; now uses
  `_resolve`. So `clibo pets rm Whiskers` works.
- 🔧 **`_resolve` updated** — was `ilike(ident)` exact-only; now
  tries exact then substring so `clibo pets show Whisk` finds
  `Whiskers`.
- 🧪 7 new tests: summary defaults to kind, summary kept when
  given, edit by name, rename via edit, unknown-name fail, rm by
  name, fuzzy substring match.
- 🎤 End-to-end: `pets log Whiskers vet -c 80 -d yesterday` →
  row created with `summary="vet"`. `pets edit Whiskers --breed
  "Maine Coon"` → row updated. `pets show Whisk` → fuzzy find.
- **Tests:** 754 passing (+7); ruff clean.

Remaining entity tools without name-resolve (or similar friction):
`network`, `leads`, `birthdays`, `brag`, `gifts`, `cv`. Same pattern
on demand.

---

### Iteration 82 — name resolution on clients, jobs, followup, plants · 2026-05-23

Iter 81 added name-resolve to `crm` (the most-asked tool) but noted
10 others had the same gap. This iteration extends the pattern to
the next-most-used entity tools.

- 👥 **`clients edit/rm`** — now accept name or ID (already had it on
  `show`/`log`).
- 💼 **`jobs show/move/edit/rm`** — resolve by **company name**
  ("Stripe") not just integer ID. New `_resolve` finds by
  case-insensitive substring match on `company`.
- 🔔 **`followup done/snooze/rm`** — resolve by **person name** with
  pending-first preference. When a person has multiple follow-ups,
  `clibo followup done Alice` picks the soonest pending one
  automatically. Pinned by `test_followup_done_prefers_pending`.
- 🪴 **`plants edit/rm`** — name resolution + a new `edit` subcommand
  (was previously missing — "move Basil to kitchen" had no command).
- 🔧 **`_resolve` updated in clients + plants** — was using
  `ilike(ident)` (exact match) only. Now tries exact first, then
  substring fallback. So `clients edit Acme` finds `Acme Corp`.
- 🧪 13 new tests pin every refactored path: name-resolution,
  fuzzy substring, unknown-name failure, followup-done prefers
  pending, plants new edit command rejects bad inputs.
- 🎤 Confirmed NL flows end-to-end:
  • `clibo plants edit Basil -l kitchen` ✓
  • `clibo clients edit Acme -r 200` ✓
  • `clibo jobs move Stripe interviewing` ✓
  • `clibo followup done Alice` ✓ (the pending one)
- **Tests:** 747 passing (+13); ruff clean.

Remaining entity tools without name-resolve: `network`, `pets`,
`leads`, `birthdays`, `brag`, `gifts`, `cv`. Same `_resolve` pattern
when they're asked for next.

---

### Iteration 81 — `crm show/edit/rm/touch <name>` (name-based resolution) · 2026-05-23

Persistent gap from agent-mode self-test: "Edit my CRM — Bob got
promoted" failed because the four `crm` mutating commands all
required integer `CONTACT_ID`. `books` already has this pattern via
a small `_resolve` helper; mirroring it onto `crm`.

- 🆕 **`_resolve(db, ident)`** on `clibo/clis/crm.py` — tries
  `int(ident)` first, falls back to case-insensitive substring
  match on `Contact.name`.
- ✏️ **`crm show / edit / rm / touch`** now take a `contact: str`
  positional that's either a numeric ID or a name. The agent
  flow `clibo crm edit Bob -c "Acme Corp"` works end-to-end.
  Backward-compatible: passing a numeric ID still works.
- 🧪 7 new tests pin the behaviour: show by name + by ID still
  work, edit by name, unknown name fails, rm by name, touch by
  name, fuzzy substring match (e.g. "Smith" matches "Bob Smith").
- 🎤 Visual smoke confirms the headline case — `clibo crm edit Bob
  -c "Acme Corp"` updates the row and `clibo crm show Smith` finds
  the same record via partial name.
- **Tests:** 734 passing (+7); ruff clean.

Future-iteration note: ~10 other entity-style tools (network,
clients, pets, plants, jobs, leads, etc.) have the same gap. The
`_resolve` pattern is now established — easy to extend on demand.

---

### Iteration 80 — `clibo compare --month` (calendar-month deltas) · 2026-05-23

Agent-mode self-test surfaced "compare to last month" twice now —
`clibo compare` only did week-over-week. Filling that gap.

- ✏️ **`clibo compare --month`** — calendar-month vs the previous
  calendar month. With `-y YEAR -m MONTH` for any past pair.
  January 2026 correctly wraps to December 2025 as the prior month.
- 🆕 **`MONTH_METRICS`** in `clibo/compare.py` — 19 metrics tuned
  for the monthly framing: income (good ↑), expenses (bad ↑),
  donations (good ↑), bills paid count, **net cash flow** (good ↑),
  invest buys, sleep avg, steps total, workouts, caffeine, fasts,
  meditate, mileage, mood, focus, tasks, journal, gratitude,
  books finished. Same green/red colour-by-polarity logic as the
  week comparison.
- 🆕 **`compare_months(year, month)`** returns the same
  `(current, prior, rows)` triple shape as `compare_weeks` so the
  rendering helper is shared via `_render_rows_table`.
- 🆕 **`render_compare_months(json_out, year, month)`** — same JSON
  shape as week mode, just keyed by `month_name` in the headers.
- 🧪 4 new tests pin month-mode: default = current vs prior, arbitrary
  pair via `-y -m`, January-wraps-to-December edge case, donations
  direction encoding.
- 🎤 Visual smoke confirms the headline metric — `Net cash flow`
  surfaces correctly with green/red colour and a delta-percent
  reading.
- **Tests:** 727 passing (+4); ruff clean.

---

### Iteration 79 — `clibo export --csv` (one file per table) · 2026-05-23

Agent-mode self-test: "I want to export to CSV for Excel" — only JSON
export existed. Spreadsheet users hit a wall there.

- 🆕 **`clibo/admin.py: export_csv(dest)`** — writes one CSV per
  table to a target directory (defaults to
  `~/.clibo/clibo-csv-<timestamp>/`). Empty tables still get a
  header-only CSV via `PRAGMA table_info`, so the schema is visible
  even before logging anything.
- 🛠️ **`clibo export --csv [DIR]`** — single flag on the existing
  `export` command. Default JSON behaviour unchanged when `--csv`
  is absent (existing tests + agent contracts intact).
- 🧪 4 new tests pin the behaviour: empty DB → one CSV per table
  (header-only), populated DB → header + data rows, summary
  counts match, the JSON path still works unchanged.
- 🎤 Visual smoke: 86 CSV files produced, ready to drop into
  Excel / Numbers / Sheets.
- **Tests:** 723 passing (+4); ruff clean.

This unlocks a workflow the JSON dump couldn't: long-form
spreadsheet analysis of any single tracker. `clibo export --csv
~/Desktop/clibo` and double-click any file.

---

### Iteration 78 — examples: drop `.sh`, replace with 11 use-case `.md` files · 2026-05-23

User request: "improve examples — drop there sh scripts — just add .md
files with use cases by categories or case".

- 🗑️ Deleted `examples/daily_brief.sh` (the jq/bash twin of
  `daily_brief.py`). Python scripts stay as working code.
- 📚 Added **11 use-case markdown files**, organised both ways:

  By *case*:
  • `morning-checkin.md` — 60-second morning routine
  • `evening-wrapup.md` — closing the day
  • `weekly-retrospective.md` — Fri/Sun review using
    `clibo week`/`compare`/`streaks`
  • `monthly-money.md` — calendar-month money rollup
  • `agent-daily-brief.md` — patterns for an AI driving clibo
    from `--json` output

  By *category*:
  • `health-tracking.md` — weight, sleep, mood, caffeine, fasting,
    steps, workout, meditate, stretches, mileage, vitals, meds
  • `money-tracking.md` — expense, income, bills, subs, donations,
    invest, debt, tip, etc.
  • `productivity.md` — todo, focus, habit, challenge, journal,
    worklog, notes, goals, bookmark, ideas
  • `relationships.md` — crm, network, followup, meetings,
    birthdays, gifts, brag, cv, jobs, leads, clients
  • `home-life.md` — groceries, pantry, recipes, meals, chores,
    plants, car, home, pets, travel, packages, documents
  • `hobbies.md` — books, films, quotes, gratitude, lessons,
    flashcards, dreams, dashboard

- 🗂️ **`examples/README.md`** rewritten as a two-way index (by case
  / by category) plus a "working scripts" section for `daily_brief.py`
  + `find_and_act.py`.
- 1037 lines of new docs total, each file ~70-110 lines so they're
  scannable in one sitting and read top-to-bottom.

---

### Iteration 77 — `clibo streaks` — every active streak in one view · 2026-05-23

Agent-mode self-test: "Show me a streak summary across everything" —
habit stats showed per-habit streaks but nothing aggregated streaks
from habits + gratitude + step goal + fasting + challenges into one
motivational view.

- 🆕 **`clibo/streaks.py`** — `collect_streaks()` aggregates from
  five sources and returns rows sorted current-desc:
  • 🔥 Habits (per active habit, with target/wk if non-default)
  • 🙏 Gratitude (global streak across all entries)
  • 👟 Step-goal (consecutive days at goal)
  • 🕒 Fasting (consecutive completed fasts hitting target)
  • 🚀 Challenges (per active challenge, with `day N/M` note)
- 🆕 **`clibo streaks`** top-level command renders inline with
  green-bold ≥7-day streaks. JSON output too.
- 🧪 8 new tests covering empty state, per-source surfacing,
  current-desc sorting, abandoned challenges excluded, below-goal
  steps not surfacing a phantom streak.
- 🎤 Visual smoke confirms the motivational close-of-day view:
  ```
  🔥 Streaks   5 active
    🔥  Read                       5   ·
    🔥  Walk                       5   ·
    🙏  Daily gratitude            5   ·
    👟  Step goal                  5   ·   (goal 10,000/day)
    🚀  no sugar                   1   ·   (day 1/30)
  ```
- **Tests:** 719 passing (+8); ruff clean.

---

### Iteration 76 — ASCII sparklines in six `stats` commands · 2026-05-23

Agent-mode self-test: "I want to plot my weight over time" — the
`stats` views show numbers, no visual trend. A tiny inline sparkline
(`█▇▅▄▂▁`) gives a glance-able shape without any external plotting
library or leaving the terminal.

- 🆕 **`clibo/core/sparkline.py`** — two pure helpers:
  • `sparkline(values)` — flat sequence → block-character line.
    Constant series renders mid-level; `None` entries become `·`.
  • `sparkline_days(by_date, start, end)` — daily-metric variant
    that gap-fills missing days as `·` so time progression stays
    honest.
- ✨ **Wired into 6 stats commands** as a `chart` field:
  • `weight stats` — last N weighing measurements
  • `sleep stats` — daily hours
  • `steps stats` — daily totals
  • `mood stats` — daily average score
  • `caffeine stats` — daily mg
  • `expense stats` — daily spending
- 🎨 Uses Unicode block-element chars `▁▂▃▄▅▆▇█` for 8 brightness
  levels — enough resolution to see direction at a glance.
- 🧪 13 new tests: 7 unit tests for the helper (empty input,
  constant series, monotonic rise, None-gap handling, day-range
  gap-fill) + 6 integration tests confirming each stats command
  now exposes a `chart` field in its JSON output.
- 🎤 Visual smoke confirms the killer view — `clibo weight stats`
  now shows `Chart  █▇▅▄▂▁` (declining over 6 days).
- **Tests:** 711 passing (+13); ruff clean.

---

### Iteration 75 — `clibo compare` (week-over-week) + info header fix + v1.6.0 to PyPI · 2026-05-23

Agent-mode self-test: "Show me this week vs last week" — no matching
command. The `week` view shows the current 7 days; nothing showed
how that compared to the 7 before. Also discovered `clibo info`
still printed "50 local-first CLI tools" — stale since v1.0 even
though `CATALOG` has 72.

- 🐛 **`clibo info` header** — was hardcoded `50 local-first CLI
  tools`; now reads `f"{len(CATALOG)} local-first CLI tools"` so it
  always reflects reality.
- 🆕 **`clibo compare`** — side-by-side current 7d vs prior 7d for
  every key metric. Sleep avg, mood avg, steps, workouts, caffeine,
  expenses, donations, fasting, meditate, stretches, mileage,
  habits-hit, journal entries, gratitude entries, tasks done. Each
  row shows `prior → current   ↑/↓ delta%` with **green/red colour
  encoding good vs bad direction** (more sleep = green ↑; more
  caffeine = red ↑; less caffeine = green ↓).
- 🔧 **`collect_week(start: date | None = None)`** — parameterized
  to accept any 7-day window's start date. All ~20 queries now
  carry an explicit upper bound (`<= today_local`) so backdated
  windows don't leak in entries from the future.
- 🎨 **Arrow + colour split** is the small UX touch: arrow
  reflects the *actual numeric direction* (went up or down), colour
  reflects whether that direction is *good or bad* for the metric.
  No more confusing green-↑ on a caffeine increase.
- 🧪 8 new compare tests + the rendering arrow-direction fix.
- 🎤 Visual smoke confirms: caffeine 170 → 63 shows as ↓ 62.9%
  green; expenses 150 → 25 shows as ↓ 83.3% green; sleep 6.5h →
  7.5h shows as ↑ 15.4% green.

**Release: v1.6.0 → PyPI** — bundles iter 73 (`edit ID|last`) +
iter 74 (`today --on / yesterday`) + iter 75 (`compare` + info fix).
Three new user-facing commands since v1.5.0 warrants a minor bump.

- **Tests:** 698 passing (+8); ruff clean.

---

### Iteration 74 — `today --on DATE` + `clibo yesterday` shortcut · 2026-05-23

Agent-mode self-test: "Show me what I logged yesterday" had no
matching command. The `today` view was hardcoded to `date.today()`,
so a user wanting to audit a past day had to read the raw JSON
sources or scan `clibo recent`.

- 🆕 **`today --on DATE`** — accepts any string `parse_date` knows
  (`yesterday`, `3 days ago`, `2026-05-15`, `last Friday`, …). Falls
  back to today when omitted.
- 🆕 **`clibo yesterday`** — thin one-word alias for the natural-
  language case. Same renderer, same JSON shape.
- 🎯 **Smart header** — title reads "Today" / "Yesterday" / "Friday"
  / etc. depending on how close the requested date is to today, so
  the user instantly sees what they're looking at.
- 🔧 **`collect_today(on: date | None = None)`** is now the typed
  signature; `render_today(json_out, on=None)` threads it through.
  All forward-looking sections (pending tasks, late packages,
  expiring documents) compute relative to the requested date.
- 🧪 4 new tests pin the new behaviours: `today --on yesterday`
  surfaces yesterday's mood, ISO dates work, the default still
  targets today, `clibo yesterday` is the proper alias.
- 🎤 NL flow verified:
  • "Show me what I logged yesterday" → `clibo yesterday` ✓
  • "How did I do on May 15?" → `clibo today --on 2026-05-15` ✓
- **Tests:** 690 passing (+4); ruff clean.

---

### Iteration 73 — `edit ID|last` on six daily trackers · 2026-05-23

Agent-mode self-test surfaced the user's exact words:
> "Edit my last weight entry — typo, was 71.5 not 75"

`clibo weight edit` didn't exist. A survey showed ~30 tools without
an `edit` subcommand. Fixed for the six most-edited daily trackers
where typos are common.

- 🆕 **`clibo/core/base.py: resolve_id(target, model_class, db)`** —
  small helper that takes either a numeric ID or the keyword
  ``last`` and returns the matching row (or the most-recent if
  ``last``). Raises a clear `typer.BadParameter` for bad input.
- ✏️ **`edit ID|last` added to six tools**: weight, mood, sleep,
  caffeine, steps, gratitude. Each has field-level optional flags
  that override when provided and validates inputs (positive,
  in-range, non-empty).
- 🎯 **`last` keyword** lets the user "fix what I just typed"
  without looking up an ID:
  • `clibo weight edit last -w 71.5` (the user's exact case) ✓
  • `clibo mood edit last -s 4 -e calm,focused` ✓
  • `clibo gratitude edit last -t "coffee, dog, sunshine"` ✓
- 🧪 16 new tests covering the headline use case (`edit last`),
  edit-by-ID, unknown ID failures, validation failures (zero hours,
  out-of-range score, empty text), and the normalisation behaviours
  (case-folding, slug-ifying drink names).
- 🎤 NL flow re-verified: the user's "typo, was 71.5 not 75"
  scenario maps cleanly to `weight edit last -w 71.5`.
- **Tests:** 686 passing (+16); ruff clean.

Future-iteration note: 24 other tools still lack `edit`. Those are
mostly entity-style (people, chores, plants) where the field set is
larger and the edit boilerplate would be substantial — better to
add them on-demand as users hit specific gaps.

---

### Iteration 72 — Pydantic models for the integration views, no more `data["..."]` · 2026-05-23

User request: "rewrite all to Pydantic models, no `data['...']` usage,
add typehints everywhere". Executed as a leveraged refactor of the
four integration-view producers and renderers.

- 🆕 **`clibo/models.py`** — 40 Pydantic v2 models covering every
  shape that the `today`, `week`, `month` and `checkin` views
  construct. Each has explicit fields with types, replacing the
  previously-implicit dict schemas.
- 🛠️ **`clibo/dashboard.py`** — `collect_today() -> TodaySnapshot` and
  `render_today` now use `.field` attribute access throughout.
  Every nested level (tasks → overdue → TaskSummary) is typed.
- 🛠️ **`clibo/weekly.py`** — `collect_week() -> WeekSnapshot` and
  `render_week` similarly refactored. ~25 dict accesses replaced.
- 🛠️ **`clibo/monthly.py`** — `collect_month() -> MonthSnapshot` and
  `render_month` refactored. ~19 dict accesses replaced.
- 🛠️ **`clibo/checkins.py`** — `collect_checkins()` returns
  `list[CheckinStatus]` instead of `list[dict]`.
- 🔌 **`clibo/core/output.py`** — `_emit_json` now serializes Pydantic
  models via `.model_dump(mode="json")`, and `_coerce` does the same
  for nested Pydantic values that show up via `default=`. Same JSON
  output shape as before; every existing test still consumes JSON
  correctly.
- ✅ **All 670 tests pass** — no behavioural changes, only structure.
  The producer-consumer contract is now compiler-checkable.
- ✅ **Ruff clean.**

This was a leveraged refactor: 90+ `data["..."]` accesses across four
files replaced by attribute access against typed models. Producers
can no longer construct malformed data; consumers can no longer typo
a key; IDEs surface field names via autocomplete.

---

### Iteration 71 — Daily check-ins on `today` + new `clibo checkin` command · 2026-05-23

User feedback: "show more widgets on today, show all logged
categories not only pomodoro and water — show all I am logging
constantly. Also `clibo checkin` so an agent asks the questions I
track."

- 📊 **New `clibo/checkins.py`** — declarative `TRACKERS` config for
  11 trackers (weight, sleep, mood, steps, workout, caffeine,
  meditate, stretches, mileage, journal, gratitude, fasting).
  `collect_checkins(db, today, days=14)` returns one dict per
  *actively-used* tracker: a tracker is "active" if it has **≥ 2
  entries in the last 14 days**. Single exploratory entries don't
  pollute the list.
- 🎛️ **`today` gains a "📊 Daily check-ins" section** — every active
  tracker, ✓ if logged today (with today's value bolded) or ○ if
  pending (with last value + how many days ago). Counts shown in
  the header: `2/5 logged`. The section is conditional — a brand-new
  user sees nothing here until they've started tracking.
- 📋 **New top-level command `clibo checkin`** — surfaces only the
  *pending* check-ins as questions, one per active tracker, each
  with a copy-pasteable command and the last known value. The
  `--json` form gives an agent everything it needs to ask the user
  one question per pending tracker and then run the suggested log
  command:
  ```json
  {"pending": [{"name":"Weight", "question":"What's your weight today?",
    "command":"clibo weight log <kg>", "last_value":"71 kg",
    "last_days_ago":1, ...}], ...}
  ```
- 🧪 8 new tests cover: inactive trackers (< 2 entries) don't surface,
  active ones do, today's log flips the `logged_today` flag, multiple
  trackers surface in parallel, and the `checkin` command's pending
  vs logged split.
- 🎤 Visual smoke on a populated 14-day database: today now shows the
  full check-in row (`✓ 8500 steps · ○ not logged today, last 71 kg`)
  and `clibo checkin` reads like a tiny morning standup the agent
  can drive.
- **Tests:** 670 passing (+8); ruff clean.

---

### Iteration 70 — `month` view (calendar-month rollup, money-first) + v1.4.0 to PyPI · 2026-05-23

Closes the aggregation trilogy: `today` (right now), `week` (last 7
days), `month` (this calendar month). Different framings, different
emphases — `today` is actionable, `week` is averages-and-totals,
`month` is the calendar-anchored unit that money actually lives on.

- 🗓️ **New top-level command `clibo month`** — `clibo/monthly.py`.
  Defaults to the current calendar month; pass `-y YEAR -m MONTH` to
  view any past month (e.g. `clibo month -y 2025 -m 12` for last
  December).
- 💰 **Money-first layout** — Income, Expenses, Donations, Bills (paid
  vs unpaid), Subscriptions (monthly cost rolled up via the existing
  `_monthly()` helper), Investments (transaction count + buys/sells
  total), and a **Net cash flow** line when both inflows and outflows
  exist. The number that actually answers "how was my financial
  month?"
- 🏃 **Health & wellness block** — sleep avg, calorie avg, water/steps
  hit-goal days over the calendar window, workouts (sessions + kcal),
  caffeine total + over-limit days, fasting (completed + hours + hit
  rate), meditate, mileage, mood avg.
- ✅ **Productivity block** — focus minutes, habit check-ins, tasks
  completed, journal + gratitude entries (with day counts).
- 🎨 **Hobbies block** — books finished this month (with titles), films
  watched count. The natural "what did I read/watch in May?" answer.
- 🧪 10 new tests covering empty state, money rollups + top category,
  net-cash-flow math, health aggregates, productivity counts, invest
  transactions, specific year/month lookups, invalid month rejection,
  books finished, and calendar arithmetic (31-day / 28-day / leap
  Feb).
- 🎤 Visual smoke on a populated database confirms all sections render
  correctly with sensible units and the Net cash flow line.

**Release: v1.4.0 → PyPI** — `pip install --upgrade clibo` now ships
fasting (iter 67) + `today` enhancements (iter 68) + `week`
enhancements (iter 69) + this `month` view (iter 70). The pair of
iter-68/69 already closed the gap of post-v1.0 tools not surfacing in
the integration views; iter 70 extends the family to the next natural
window.

- **Tests:** 662 passing (+10); ruff clean.

---

### Iteration 69 — `week` view now surfaces every post-v1.0 tool too · 2026-05-23

Parallel polish to iter 68: the `clibo today` fix exposed that
`clibo week` had the same structural gap. Sleep, focus, mood, water,
habits, expenses, journal, worklog, tasks — that's where the rollup
stopped. Steps, workouts, caffeine, fasting, meditate, stretches,
mileage, gratitude, donations all had no weekly story.

- 🛠️ **`clibo/weekly.py` extended** to aggregate + render 9 more
  trackers, with sensible 7-day rollups for each:
  • 👟 **steps** — days hit goal, daily avg, weekly total
  • 🏋️ **workouts** — sessions, days active, total minutes, 🔥 kcal
  • ☕ **caffeine** — total mg, avg/day, over-limit days (red)
  • 🕒 **fasting** — completed count, total + longest hours, target
    hit rate
  • 🧘 **meditate** — sessions across days, total minutes
  • 🧎 **stretches** — sessions across days, total minutes
  • 🏃 **mileage** — total km + by-activity breakdown (run/cycle/walk)
  • 🙏 **gratitude** — entries + days logged (productivity block)
  • ❤️ **donations** — total + deductible total + recipient count
    (sits next to expenses in a new "💰 Money" block)
- ✨ **All conditional** — empty entries stay hidden, so a user who
  doesn't track caffeine doesn't see a "0 mg" line.
- 🎨 **Money block** introduced — expenses and donations now share a
  bordered heading, since they're conceptually a money rollup. Old
  empty-state check updated to consider the new sources.
- 🧪 9 new tests pin every new aggregation field. Existing 6 week
  tests untouched.
- 🎤 Visual smoke on a populated 7-day database — every metric line
  shows up correctly with proper units and conditional rendering.
- **Tests:** 652 passing (+9); ruff clean.

The pair (iter 68 today + iter 69 week) closes the loop: every tool
added since v1.0 now surfaces in both daily and weekly aggregation
views without users having to discover them one at a time.

---

### Iteration 68 — `today` view now surfaces every post-v1.0 tool · 2026-05-23

Agent-mode self-test exposed a structural gap: I'd added 17+ tools
since v1.0 and **none of them were in the `today` view**. `clibo today`
was still showing the v1.0 set (tasks, habits, water, calories, focus,
events, meals, bills, follow-ups, plants, chores, birthdays). The
killer "what's actionable today?" view was lying by omission.

- 🛠️ **`clibo/dashboard.py` extended** to surface:
  • 👟 **steps** — daily total + goal in the metric-bars row
  • 🕒 **fasting** — running-clock with progress bar against target
    (only when a fast is open — high-value real-time info)
  • 🙂 **mood** — today's latest score + emotion (with check-in count
    if there were multiple)
  • ☕ **caffeine** — today's mg + **residual at bedtime** (yellow
    warning if > 10 mg, the sleep-research threshold)
  • 🏋️ **workouts** — today's session count + total minutes + kcal
    burned
  • 🚀 **challenges pending check-in** — actionable list with the
    exact `clibo challenge check ID` command to copy
  • 📦 **late packages** — surfaced with ⚠ marker (or a quiet
    "N packages on the way" if none are late)
  • 📑 **documents expiring** — within 30 days, colour-coded by
    urgency
- ✨ **Everything is conditional** — empty sections stay quiet so the
  view doesn't grow into noise. The empty-state cheer ("nothing on
  the radar today — enjoy! ✨") now correctly considers the new
  sources too.
- 🧪 11 new tests pin every new field on `collect_today()`:
  mood present / absent, steps default goal, workouts aggregation,
  caffeine total + residual, fasting in-progress vs none, pending
  challenge check-ins (and they disappear after `check`), late
  packages flagging, documents expiring within 30d.
- 🎤 NL flow re-verified end-to-end on a populated database — every
  post-v1.0 activity shows up in the right section.
- **Tests:** 643 passing (+11); ruff clean.

---

### Iteration 67 — `fasting` (intermittent fasting with running clock) + v1.3.0 to PyPI · 2026-05-23

User said "continue releasing and development" — v1.3.0 went live at
the end of iter 66 with invest + packages + polish. Now back to the
build loop.

Agent-mode self-test: "I'm starting a 16-hour fast" had no home.
`calorie` is food intake, `water` is hydration, `sleep` is overnight
sleep — none capture a *time window* with a target duration and a
"still going?" state.

- 🕒 **New tool `fasting` (72nd, Health & Wellness)** — `fast_session`
  table with `start_time`, `end_time` (nullable while in progress),
  `target_hours`, `note`. Exactly one fast can be in progress at a
  time — `start` refuses if there's already an open one.
- ⏱️ **`status` is the killer view** — running clock with a progress
  bar against target. While fasting: "21.48h elapsed · ✓ target
  reached!" or "8.2h to target". While not fasting: shows the last
  completed fast as context.
- 📐 **Smart datetime parsing** — `_parse_when` accepts `HH:MM` (today),
  a date phrase alone, or *a date phrase followed by HH:MM*. So
  `--at "yesterday 08:00"`, `--at "3 days ago 22:00"` all work — and
  this is what makes backdated fasts feasible in tests too.
- Commands: `start [-T HOURS] [-t TIME]` / `stop [-t TIME] [-n NOTE]` /
  `status` / `list [--days N] [--completed]` / `show` / `rm` /
  `target --set HOURS` (default 16h) / `stats` (count, avg, longest,
  hit-rate vs target).
- 🔌 Integrated: `recent.py` (with `start_time` time-column override
  so backdated fasts sort correctly), `search.py` (note indexed),
  `catalog.py` (Health & Wellness — 13 tools), README.
- 📄 `docs/SCHEMA.md` regenerated (86 tables).
- 🧪 17 new tests covering start/stop validation, concurrent-fast
  rejection, the not-fasting-with-history status path, target
  set/get, list filtering, stats computation across multiple
  completed fasts, and integration with `search` + `recent`.
- 🎤 NL flow verified:
  • "Starting a 16-hour fast" → `fasting start --target 16` ✓
  • "Started fasting at 8pm last night" →
    `fasting start -t "yesterday 20:00"` ✓
  • "Done, broke my fast" → `fasting stop` ✓
  • "How much longer?" → `fasting status` ✓
- **Tests:** 632 passing (+17); ruff clean.

---

### Iteration 66 — `packages` (parcel tracker with late detection) · 2026-05-23

Agent-mode self-test: "Amazon order coming Tuesday" / "Where's my
FedEx package?" had no home. `bills` is recurring money out, `events`
is one-off dates with no logistical state, `wishlist` is things you
want (not in transit). Real new use case.

- 📦 **New tool `packages` (71st, Home & Life)** — one table
  `package_entry` with sender, tracking_number, carrier, description,
  ordered_date, expected_date, received_date, status, note.
  Status progresses **`ordered`** → **`in_transit`** → **`delivered`**
  with branches to `lost` / `returned`.
- 🚨 **`pending` is the daily-driver view** — sorts late packages
  first (with ⚠ marker), then by ETA ascending, then by order date.
  `--late` filters to just the late ones. Computed `is_late` flag
  fires when `expected_date < today` AND the package isn't resolved.
- ✅ **`received ID`** convenience — single command to mark
  delivered and set today as `received_date`.
- 🔧 **`update`** for status changes and ETA revisions
  ("FedEx pushed delivery to Friday" → `update 1 -e Friday`).
- 📊 **`stats`** — total, by status, by carrier, on-time vs late
  arrivals in the window, avg delivery days, currently pending.
- 🪄 **`log` alias for `add`** from day one (predictable verbs).
- 🔌 Integrated: `recent.py`, `search.py` (sender + description +
  tracking_number + carrier + note all indexed — so `clibo search
  TRACK-XYZ` finds the package), `catalog.py` (Home & Life — now 12
  tools), README.
- 📄 `docs/SCHEMA.md` regenerated (85 tables).
- 🧪 20 new tests covering add validation, log alias, received,
  update validation, pending sorting + late detection, --late filter,
  status filter, carrier filter, --all flag, stats arithmetic, and
  integration with `search` + `recent`.
- 🎤 NL flow verified:
  • "Amazon order placed, expected Tuesday" →
    `packages add Amazon -e Tuesday` ✓
  • "Tracked: USPS 9400... arriving in 3 days" →
    `packages add Sender -t "9400..." -c usps -e "in 3 days"` ✓
  • "Got the FedEx package today" → `packages received 1` ✓
  • "What packages am I waiting on?" → `packages pending` ✓
  • "Anything late?" → `packages pending --late` ✓
- **Tests:** 615 passing (+20); ruff clean.

---

### Iteration 65 — polish: mood multi-emotion, goals `-d`, events `--category` filter · 2026-05-23

Three small rough edges surfaced by agent-mode self-test, all real,
all touched by recent NL probes — bundled into one focused polish
iteration (same theme: agent-friendly defaults).

- 🙂 **`mood log` now keeps every emotion you pass.** Was silently
  dropping all but the last `-e`. New behaviour: `--emotion/-e` is a
  list option — repeat the flag (`-e anxious -e excited`) **or**
  pass a comma-separated value (`-e "anxious,excited"`). Both forms
  normalise to comma-separated, deduplicated and lower-cased.
- 🎯 **`goals add -d`** is now a shortcut for `--deadline`. Was
  the natural agent translation of "by Friday" / "in 6 months" but
  the option had no short flag, so `-d` came back as `No such option`.
- 📅 **`events list -c/--category`** filter — schema has a `category`
  field, but `list` had no way to filter on it. "Show my dentist
  appointments" now works (`events list -c health`).
- 🧪 8 new tests (mood multi-emotion via repeat + comma + case-
  insensitivity + dedup, goals deadline shortcut, events category
  filter happy + neutral paths).
- 🎤 NL flow re-verified:
  • "Mood 3 with anxiety and excitement" →
    `mood log 3 -e anxious -e excited` ✓ (both stored)
  • "Goal: run a marathon in 6 months" →
    `goals add "Run a marathon" -d "in 6 months"` ✓
  • "What dentist appointments do I have?" →
    `events list -c health` ✓
- **Tests:** 595 passing (+7); ruff clean.

---

### Iteration 64 — `invest` (positions with cost basis + unrealized P/L) · 2026-05-23

Agent-mode self-test: "I bought 5 shares of AAPL at $200" had no
clean home. `networth` stores a single value per asset row; an
investment portfolio needs *transactions* (buys + sells), and you
want cost basis preserved across multiple buys at different prices.

- 📈 **New tool `invest` (70th, Money & Finance)** — two tables:
  `invest_transaction` (id, ticker, kind, action [buy/sell], shares,
  price_per_share, txn_date, note) and `invest_latest_price` (ticker,
  price, updated_at — for unrealized P/L).
- 💰 **Cost basis & P/L done right:**
  • Multiple buys at different prices roll up into a single position
    using **average cost basis** (simplest defensible model — FIFO /
    specific-lot is a future upgrade).
  • Sells **validate** that you have enough shares first, then
    compute realized P/L against avg cost and reduce the position
    proportionally.
  • Fully-sold positions disappear from `positions` but stay in
    `history` and the lifetime realized-P/L total.
- 🚫 **No live price feeds** — clibo is local-first. Update prices
  manually with `invest price TICKER X` whenever you want a fresh
  number. `positions` shows `—` for unpriced tickers.
- Commands: `buy TICKER SHARES PRICE [-k KIND] [-d DATE]` /
  `sell TICKER SHARES PRICE [-d DATE]` (with realized-P/L printout) /
  `price TICKER PRICE` / **`positions`** (the headline, with avg cost,
  market value and green/red P/L) / `history [-t TICKER]` / `show
  TICKER` / `rm ID` / `stats` (active count, total invested basis,
  realized lifetime P/L, unrealized P/L, by-kind basis split).
- Six kinds supported: `stock`, `etf`, `crypto`, `bond`, `fund`,
  `other`. Tickers normalised to uppercase.
- 🔌 Integrated: `recent.py`, `search.py` (ticker + note indexed),
  `catalog.py` (Money & Finance), README. Uses the shared
  `money/currency` setting.
- 📄 `docs/SCHEMA.md` regenerated (84 tables: 82 + 2 new tables).
- 🧪 20 new tests covering buy/sell math, rollup of multiple buys at
  different prices, sell validation (can't sell more than owned),
  price updates and unrealized-P/L computation, by-kind basis,
  history filtering, full show drill-down, and integration with
  `search` + `recent`.
- 🎤 NL flow verified:
  • "Bought 5 AAPL at $200" → `invest buy AAPL 5 200` ✓
  • "Bought 0.5 BTC at $42,000" →
    `invest buy BTC 0.5 42000 -k crypto` ✓
  • "Sold 2 AAPL at $250" → `invest sell AAPL 2 250` ✓
    (prints realized P/L)
  • "AAPL is at $220" → `invest price AAPL 220` ✓
  • "What's my portfolio worth?" → `invest positions` ✓
- **Tests:** 588 passing (+20); ruff clean.

---

### Iteration 63 — `donations` (charitable giving with tax-year aggregation) · 2026-05-23

Agent-mode self-test: "I donated $50 to Red Cross" — could go through
`expense` with category=donation, but giving has its own shape that
doesn't fit a generic expense row.

- ❤️ **New tool `donations` (69th, Money & Finance)** — three things
  that make it distinct from `expense`:
  • **Calendar-year totals** matter for tax filing — `year`
    subcommand aggregates by Jan 1 → Dec 31 boundaries, separate
    from fiscal-year expense reporting.
  • **Tax-deductible vs not** as a per-gift flag (default deductible;
    `--no-deductible` for political gifts, GoFundMe-to-individual,
    non-US NGOs). `year` reports deductible vs non-deductible split.
  • **Recipient as structured data** — repeat giving to the same
    org clusters cleanly: "Red Cross: $250 across 5 gifts" instead
    of five expense rows with slightly-different descriptions.
- Commands: `log RECIPIENT -a AMOUNT [-r RECEIPT] [--no-deductible]`
  (with `add` alias from day one) / `list [-y YEAR] [-R RECIPIENT]` /
  **`year [-y YEAR]`** (the headline view — annual summary with
  deductible total for tax filing) / **`top --days 365`** (most-
  supported recipients) / `show` / `rm` / `stats` (lifetime: by
  year, top recipient, deductible total).
- 🔌 Integrated: `recent.py`, `search.py` (recipient + receipt + note
  indexed — so the receipt number actually finds the donation),
  `catalog.py` (Money & Finance), README. Uses the shared
  `money/currency` setting.
- 📄 `docs/SCHEMA.md` regenerated (82 tables).
- 🎤 NL flow verified:
  • "I donated $50 to Red Cross" →
    `donations log "Red Cross" -a 50` ✓
  • "Gave $200 to a friend's GoFundMe — not deductible" →
    `donations log "GoFundMe Alice" -a 200 --no-deductible` ✓
  • "How much did I give in 2025?" → `donations year -y 2025` ✓
- **Tests:** 568 passing (+14); ruff clean.

---

### Iteration 62 — `challenge` (30-day, 100-day, … with miss budget) + v1.1.1 to PyPI · 2026-05-23

User asked to "release to pypi" mid-iteration. Done — v1.1.1 is live
at https://pypi.org/project/clibo/1.1.1/. `pip install clibo` works.
Token wired into `PYPI_API_TOKEN` repo secret; `.github/workflows/
publish.yml` will auto-publish every future GitHub release.

README install instructions promoted to the very top of the file.

Then back to the build loop. Agent-mode self-test surfaced
"Starting 30 days of no sugar today" with no home. `habit` is for
open-ended commitments (streaks count up indefinitely); a challenge
has a target duration and a binary pass/fail outcome — different
shape.

- 🚀 **New tool `challenge` (68th, Productivity & Work)** — two
  tables: `challenge_entry` (name, start, target_days, miss_budget,
  status, finished_at) and `challenge_checkin` (daily success/miss
  with optional note).
- 🎯 **Miss budget** — `--miss-budget/-m N` lets you survive N
  missed days (default 0 = strict). Exceed it and the tool
  auto-marks the challenge `failed`.
- ✨ **Auto-finalization** — every read (`status` / `list` / `show` /
  `stats`) checks if the end date is past (→ `completed`) or if
  misses exceed the budget (→ `failed`) and updates the row. No
  manual "close" step needed.
- Commands: `start NAME --days N [-m MISSES] [-D DESC]` /
  `check ID [--missed]` (idempotent — re-checking the same day
  overwrites) / **`status [ID]`** (progress bars + miss budget) /
  **`today`** (pending check-ins only) / `list [--all]` (active by
  default) / `show ID` (full history) / `abandon ID` / `rm` /
  `stats` (completion rate over finalised challenges).
- 🔌 Integrated: `recent.py`, `search.py` (name + description
  indexed), `catalog.py` (Productivity & Work), README.
- 📄 `docs/SCHEMA.md` regenerated (81 tables: 79 + 2 from challenge).
- 🧪 19 new tests covering start validation, check success/miss
  paths, idempotent re-checks, miss-budget tolerance, auto-fail when
  exceeded, abandon, list filtering, cascade-delete of check-ins,
  stats math, and integration with `search` + `recent`.
- 🎤 NL flow verified:
  • "30 days of no sugar" → `challenge start "no sugar" --days 30` ✓
  • "100 days of code, 5 cheat days" →
    `challenge start "100 days of code" --days 100 -m 5` ✓
  • "I cheated today" →
    `challenge check 1 --missed -n "had cake"` ✓
  • "How am I doing?" → `challenge status` ✓
- **Tests:** 554 passing (+19); ruff clean.

---

### Iteration 61 — polish: workout `--calories`, books `log` alias, forward-compat migration · 2026-05-23

Agent-mode self-test surfaced the same persistent gap for the third
iteration in a row — "I burned 350 kcal jogging" had nowhere to go on
the `workout` tool. Plus "I read 30 pages of Atomic Habits" failed
because the agent kept trying `books log`, but the real verb was
`books read`. Finally cleared both.

- 🔥 **`workout log --calories/-c`** — new nullable `kcal_burned`
  column on `workout_entry`. `today` includes `🔥 N kcal` in its
  summary line; `today --json` adds `total_kcal`; `stats` adds
  `total_kcal_burned`. Validates non-negative.
- 📖 **`books log`** is now an alias for `books read` — natural
  agent translation of "I read N pages today". Same one-line
  `app.command(name="log")(read)` pattern.
- 🛠️ **Forward-compatible migrations** — `init_db()` now runs
  `_add_missing_columns()` after `create_all()`. For every existing
  table, it ALTERs in any columns the model declares but the DB is
  missing (nullable or default-having columns only — SQLite refuses
  NOT NULL without default for safety). This is leverage: every
  future column-add benefits automatically.
- 🧪 3 new tests pin migration behaviour: adds a missing nullable
  column, is idempotent (re-running doesn't dup), skips unknown
  tables. Plus 5 new workout tests for the calories field and 1
  for the books log alias.
- 📄 `docs/SCHEMA.md` regenerated (still 79 tables — column added
  to existing one).
- 🎤 NL flow re-verified:
  • "I burned 350 kcal jogging for 30 min" →
    `workout log jogging -t 30 -c 350` ✓
  • "I read 30 pages of Atomic Habits" →
    `books log "Atomic Habits" 30` ✓
- **Tests:** 535 passing (+10); ruff clean.

---

### Iteration 60 — `documents` (expiry tracker for passport, license, etc.) · 2026-05-23

Agent-mode self-test: "My passport expires June 2030" had no home.
`events` is for one-off dates, `bills` is recurring due dates with
amounts — neither fits "things that quietly expire and ruin a trip if
you miss them". A real high-cost-of-failure gap.

- 📑 **New tool `documents` (67th, Home & Life)** — registry of
  expiring documents (passport / license / id / insurance / cert /
  visa / membership / warranty / lease / other). Stores name, kind,
  optional issued + serial number + note, and a required expiry date.
- ⏳ **`expiring` subcommand** — the headline view. Lists documents
  expiring within N days (default 90), sorted soonest first, with
  urgency colour coding: 🔴 critical (≤ 30d), 🟡 soon (≤ 90d),
  watch (≤ 1y), 🟢 ok (> 1y).
- `expired` — separate view for anything already past.
- Validates that `issued` (if given) is before `expires`.
- 📅 **Free natural-language dates** thanks to iter 57: `-e "June 15 2030"`,
  `-e "next March"`, `-e "in 14 days"` all just work. Pinned by a
  dedicated test.
- 🔌 Integrated: `recent.py`, `search.py` (name + kind + number +
  note indexed — so searching by policy number finds the document),
  `catalog.py` (Home & Life — 11 tools now).
- 📄 `docs/SCHEMA.md` regenerated (79 tables).
- 🎤 NL flow verified:
  • "My passport expires June 15 2030" →
    `documents add Passport -e "June 15 2030" -k passport` ✓
  • "Insurance #POL-9999 expires in 2 weeks" →
    `documents add "Travel insurance" -e "in 14 days" -k insurance -# POL-9999` ✓
  • "What's expiring soon?" → `documents expiring --days 90` ✓
- **Tests:** 525 passing (+16); ruff clean.

---

### Iteration 59 — `caffeine` (intake tracker with bedtime-residual model) · 2026-05-23

Agent-mode self-test: "Had a coffee at 9am" had nowhere to go.
`water` is hydration, `calorie` is food kcal, `meds` is prescribed
medication. None capture caffeine specifically — and none of them
would compute *the* number that actually matters: how much will still
be in your system at bedtime.

- ☕ **New tool `caffeine` (66th, Health & Wellness)** — per-drink log
  with the canonical 5.5-hour half-life decay model. The headline
  number on every `log` and on `today` is **residual at bedtime**, not
  raw mg. A 95 mg coffee at 14:00 leaves ~30 mg by 23:00 — enough to
  fragment sleep; this tool puts that number in front of the user
  every time they log.
- 🧮 **20 built-in presets** so agents don't have to invent mg numbers:
  `espresso`=63, `coffee`=95, `latte`=75, `cold-brew`=200, `matcha`=70,
  `redbull`=80, `monster`=160, etc. (USDA / FDA / manufacturer values.)
  Override with `-m / --mg` for custom drinks; an unknown drink without
  `-m` fails loudly with the preset list.
- 🕘 **`cutoff` subcommand** — the killer view: for every preset,
  compute the latest time today you can still drink it and stay under
  10 mg residual at bedtime (`hours = half_life × log₂(mg / 10)`).
- Commands: `log DRINK [-m MG] [-t HH:MM]` (with `add` alias from day
  one) / `today` / **`cutoff`** / `list [--drink X]` / `show` / `rm` /
  `bedtime --set HH:MM` (default 23:00) / `stats`.
- 🔌 Integrated: `recent.py` (with `consumed_at` time-column override
  so backdated entries sort correctly), `search.py` (drink + note
  indexed), `catalog.py` (Health & Wellness), README.
- 📄 `docs/SCHEMA.md` regenerated (78 tables).
- 🧪 21 new tests — preset mg lookup, mg override, unknown-drink
  failure, time-of-day parsing, residual-at-bedtime presence, the
  residual-decays-with-time property, cutoff table coverage, bedtime
  set/get with validation, and a direct half-life math sanity check
  (50% after one half-life, 25% after two).
- 🎤 NL flow verified:
  • "Had a coffee at 9am" → `caffeine log coffee -t 09:00` ✓
  • "Cold brew, guessing 220mg" → `caffeine log cold-brew -m 220` ✓
  • "Can I still have a coffee?" → `caffeine cutoff` ✓
  • "My bedtime is 10pm" → `caffeine bedtime --set 22:00` ✓
- **Tests:** 509 passing (+21); ruff clean.

---

### Iteration 58 — `steps` (daily step-count tracker with streaks) · 2026-05-23

Agent-mode self-test: "My step count was 8500 today" → no tool. The
existing exercise tools all model *deliberate* activity (`workout` for
strength, `mileage` for explicit cardio, `stretches` for mobility),
but the single most-tracked passive health metric in 2026 — the daily
step count from your watch or phone — had no home.

- 👟 **New tool `steps` (65th, Health & Wellness)** — per-event step
  log that sums to a per-day total. Multiple syncs in one day add up
  (morning + afternoon + manual additions without double-counting).
  Free-text `source` field tags where the count came from
  (`apple_watch`, `fitbit`, `phone`, `manual`).
- Commands: `log COUNT [-s SOURCE]` (with `add` alias from day one) /
  `today` / `list --days N` / **`week`** (per-day bars with streak
  callout) / `show` / `rm` / `goal --set N` (default 10,000) / `stats`
  (window total, avg, hit-rate, best day, current + longest streak).
- 🔥 **Streak logic** — consecutive goal-hit days ending today (or
  yesterday if today's count is still below goal — the day isn't
  "broken" until tomorrow). Pinned by a test that flips streak from 2
  to 0 when both yesterday and today are below the goal.
- 🔌 Integrated: `recent.py`, `search.py` (source + note indexed),
  `catalog.py` (Health & Wellness), README.
- 📄 `docs/SCHEMA.md` regenerated (77 tables).
- 🎤 NL flow verified:
  • "I did 8500 steps today" → `steps log 8500` ✓
  • "Apple Watch shows 12,400 today" → `steps log 12400 -s apple_watch` ✓
  • "Set my goal to 7000" → `steps goal --set 7000` ✓
  • "How am I doing this week?" → `steps week` ✓ (bars + streak)
- **Tests:** 488 passing (+15); ruff clean.

---

### Iteration 57 — polish: `parse_date` learns weekday names, "in N units", month names · 2026-05-23

Agent-mode self-test surfaced three distinct NL inputs that fell over
because the shared `parse_date()` helper didn't understand them:

```
$ clibo birthdays add Dad -d "March 12"      → Unrecognized date
$ clibo events add ... -d "next Tuesday"     → Unrecognized date
$ clibo followup add ... -d "in 2 weeks"     → Unrecognized date
```

These weren't tool bugs — they were missing vocabulary in the shared
parser every `-d/--date` flag delegates to. One central fix unblocks
flows across **every** tool.

- 📆 **`parse_date` extended** with three new natural-language forms:
  • Weekday names — bare (`monday` → next Monday), `next friday`,
    `this wednesday` (allows today), `last tuesday`. Common
    abbreviations work too (`mon`, `tue`, `wed`, `thu`, `fri`,
    `sat`, `sun`).
  • `in N <unit>` — `in 14 days`, `in 2 weeks`, `in 1 month`,
    `in 3 years` (synonym for the existing `N <unit> from now`).
  • Month-name forms — `March 12`, `12 march`, `Mar 12 1985`,
    `Mar. 12 1985`, with year defaulting to the current year.
    Implemented as a locale-independent English month dict (the
    obvious `strptime("%B")` approach silently breaks under any
    non-English `LC_TIME`).
- 🎂 **`birthdays add`** now also accepts the month-name forms — its
  separate `_parse_md` helper (which has year-optional semantics)
  delegates month-name parsing to the same central function. So
  "March 12" works *and* `data["turning"]` stays `None` when no
  year was given, matching existing behaviour.
- 🧪 **12 new parse_date tests** (`test_parse_date.py`) pin every
  new form: weekday alone / next / this / last / abbreviations,
  `in N` for all units, month-name with and without year, case
  insensitivity, the trailing-dot ("Mar. 12") common typo, and the
  invalid-day raises path. Plus one new birthdays test confirming
  the integration end-to-end.
- 🎤 NL flow re-verified — five different tools that were blocked
  now work without any per-tool changes:
  • `birthdays add Dad -d "March 12"` ✓
  • `events add "Doctor appointment" -d "next Tuesday"` ✓
  • `followup add Alice -r email -d "in 2 weeks"` ✓
  • `workout log running -t 30 -d "last Friday"` ✓
  • `bills add Rent -a 1200 -d "in 1 month"` ✓
- **Tests:** 473 passing (+12); ruff clean.

---

### Iteration 56 — polish: `car fuel` odometer is now optional · 2026-05-23

Agent-mode self-test: "Filled up the car — 45L for $60" died with
"missing argument ODOMETER". Most users don't remember the odometer
reading in the moment, but the old signature `clibo car fuel ODO VOL`
made it the *first* required positional. Real ergonomic blocker.

- ⛽ **Refactored `car fuel`** — `VOLUME` is now the single required
  positional; `--odometer/-o` is optional. Fill-ups without an
  odometer are silently skipped by the economy calculation rather
  than crashing it.
- 🛟 **Back-compat preserved** — the old two-positional form
  `car fuel ODOMETER VOLUME` is still accepted (hidden second
  positional triggers the legacy path). Existing tests, scripts and
  user muscle-memory all still work.
- 🧪 4 new tests — friendly form, odometer-only flag form, legacy
  back-compat form, mixed-entries economy.
- 📖 `skills/car/SKILL.md` rewritten with the new form first, the
  legacy form documented as still supported.
- 🎤 NL flow re-verified:
  • "Filled up for $60" → `car fuel 45 -c 60` ✓
  • "12.5 gallons at $52" → `car fuel 12.5 -c 52` ✓
  • "Tank fill at 52,340 km — 45.5L" → `car fuel 45.5 -o 52340` ✓
- **Tests:** 461 passing (+4); ruff clean.

---

### Iteration 55 — `tip` (tipping tracker with venue / service-rating stats) · 2026-05-23

Agent-mode self-test: "I left a 20% tip on a $40 dinner" had no good
home. `expense` captures the total but loses the percent and the
venue's tipping history. So this is the tool for *tipping behaviour*,
not generic spending.

- 🪙 **New tool `tip` (64th, Money & Finance)** — bill + tip with
  whichever side the user knows (percent or absolute), an optional
  venue and a 1-5 service rating. Stores `tip_percent` so "what's my
  avg tip %?" is a one-shot query.
- Commands: `log BILL -p PERCENT` / `log BILL -a AMOUNT` (with the
  `add` alias from day one) / **`calc`** (no-save quick calculator —
  "how much is 20% on $35?") / `today` / `list [--venue X]` /
  `show ID` / `rm` / `stats` (count, totals, **avg %**, **weighted %**
  — weighted by bill amount, the truer figure, biggest tip, most
  generous %, by-venue avg %, by-service-rating avg %).
- 🔌 Integrated: `recent.py`, `search.py` (venue + note indexed),
  `catalog.py` (Money & Finance), README. Uses the shared
  `money/currency` setting via `clibo.clis.expense.money()`.
- 📄 `docs/SCHEMA.md` regenerated (76 tables).
- 🎤 NL flow verified end-to-end:
  • "I left a 20% tip on a $40 dinner" → `tip log 40 -p 20 -v dinner` ✓
  • "Tipped $10 on $50" → `tip log 50 -a 10` ✓
  • "How much is 20% on $35?" → `tip calc 35 -p 20` ✓ (no save)
  • "What's my avg tip %?" → `tip stats` ✓
- **Tests:** 457 passing (+14); ruff clean.

---

### Iteration 54 — `stretches` (mobility log) + water `add` alias · 2026-05-23

Agent-mode self-test surfaced two gaps:

```
$ clibo stretches log hamstrings 10 → No such command 'stretches'.
$ clibo water add 500              → No such command 'add'.
```

`workout` is for strength, `mileage` is for cardio distance,
`meditate` is for mindfulness — but nothing tracked a stretching /
mobility session, which has its own shape (which body area, how deep
it felt, optional pose list).

- 🧎 **New tool `stretches` (63rd)** — mobility / flexibility log.
  Schema: `area`, `duration_min`, optional comma-separated `poses`,
  optional `difficulty` 1-5, plus the usual `entry_date` /
  `created_at` / `note`. Suggested area vocabulary (free text):
  `hamstrings`, `quads`, `hips`, `back`, `lower-back`, `shoulders`,
  `neck`, `chest`, `calves`, `ankles`, `wrists`, `full-body`.
- Commands: `log AREA -m MIN -p POSES -D 1-5` (with `add` alias from
  day one) / `today` / `list [--area X]` / `show ID` / `rm` /
  **`areas`** (frequency table — find the area you neglect) /
  `stats` (sessions, total min, avg difficulty, top area).
- 🔌 Integrated everywhere: `recent.py`, `search.py` (area + poses +
  note are indexed), `catalog.py` (Health & Wellness), README.
- 💧 **Water polish** — `clibo water add 500` now works as an alias
  for `clibo water drink 500`. Same one-line pattern as iter 53.
  Pinned by a regression test in `test_add_alias.py`.
- 📄 `docs/SCHEMA.md` regenerated (75 tables).
- 🎤 NL flow verified end-to-end:
  • "I stretched my hamstrings for 10 minutes" → `stretches log hamstrings -m 10`
  • "Did 15 min of hip mobility, super deep" → `stretches log hips -m 15 -D 5`
  • "Which areas am I neglecting?" → `stretches areas --days 30`
  • "I drank 500ml" → `water add 500` ✓
- **Tests:** 443 passing (+12); ruff clean.

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
