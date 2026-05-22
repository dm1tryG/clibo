# 📈 clibo — build log

A running log of the build loop. Newest entries on top.

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
