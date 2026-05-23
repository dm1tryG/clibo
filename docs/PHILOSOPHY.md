# Design philosophy

clibo makes a small set of deliberate trade-offs. Reading them once makes
the rest of the codebase obvious — every tool falls out of these rules.

## 1. Local-first, no exceptions

Everything lives in one SQLite file at `~/.clibo/clibo.db`. No accounts, no
sync, no telemetry, no opt-in cloud anything.

**Why.** A personal tracker should outlast any company. SQLite is a thirty-
year format. One file means backup is `cp`, migration is `scp`, audit is
`sqlite3 clibo.db`. The user owns their data with no asterisks.

**Trade-off accepted.** No multi-device sync out of the box. `clibo export`
and `clibo import` give you a one-file migration path on demand; if you
need real sync, put the DB file in iCloud / Syncthing / Dropbox.

## 2. The `--json` contract is the API

Every command supports `--json`. In that mode stdout is one parseable JSON
document, errors go to stderr with a non-zero exit code, and mutations
return the affected record. Humans get Rich tables; agents get JSON. No
third mode.

**Why.** Subprocess + `--json` is the lingua franca that works across every
language and every LLM-driven shell. It also means clibo doesn't need to
ship a Python library API to be useful from other code: the contract is the
CLI itself, and it's documented per-tool in
[`skills/<tool>/SKILL.md`](../skills) and at the top level in
[`AGENTS.md`](../AGENTS.md).

**Trade-off accepted.** Slightly slower than in-process calls. ~270 ms cold
start is fine for an interactive personal tool; tight automation loops can
use `clibo export` once and read the JSON dump.

## 3. Fifty tools, one CLI

Each life-area gets its own sub-command. They share infrastructure
(`core/db.py`, `core/output.py`, `core/settings.py`) but don't import from
each other; the integrating commands (`today`, `week`, `recent`, `search`,
`tags`, `doctor`) read from the database directly.

**Why.** A user's mental model is "I want to log a calorie" or "I need to
follow up with someone", not "I'm using a tracker framework". Discrete
sub-commands map to that. The 50 tools also keep the code grep-friendly —
each lives in one file you can read top-to-bottom.

**Trade-off accepted.** Some duplication (each tool has its own `_resolve`
by id-or-name, its own status colours, etc.). Future contributors can DRY
this into `core/` helpers if it becomes painful — it hasn't yet.

## 4. Predictable verbs everywhere

Every tool tends to expose the same shape: `add` (or a domain verb like
`log`, `drink`, `take`), `list`, `show`, `edit`, `rm`, `stats`. Names work
in place of IDs everywhere it makes sense (`clibo habit check "Read"` not
just `clibo habit check 1`).

**Why.** Once you've used three tools, you can use the other forty-seven
without re-reading any help text. The same is true for agents — once they
know the verb set, they can predict the surface of a new tool.

## 5. Dates are forgiving

Anywhere a command takes a date, it accepts `today`, `yesterday`,
`tomorrow`, ISO `YYYY-MM-DD`, `DD.MM`, `DD.MM.YYYY` and `MM/DD`. All in the
user's local timezone. No timezone abstraction.

**Why.** People (and agents) type "yesterday" more than "2026-05-22". Local
time is the only time that matters for a personal-tracker timestamp.

**Trade-off accepted.** Cross-timezone travelers will have a bad day. Open
a PR if you hit this for real.

## 6. Beautiful output is part of correctness

Tables get Rich rounded borders. Statuses get colour. Progress is a bar.
Every tool has an emoji that shows up in titles and confirmations. This is
not decoration — it's how a user verifies "the right thing happened" at a
glance. Tools that print bland output are broken in spirit.

**Why.** clibo is meant to be used every day. Daily tools have to feel
good. Rich output is also the easiest way for a human to spot a bug
("wait, why is the bar yellow?").

## 7. Tests are the safety net, not the spec

Each tool has a pytest file. The bar is: cover create, a read/list, the
`--json` shape, `stats`, and at least one error path. Not 100% coverage —
just enough that a regression would obviously break a test.

**Why.** With 50 tools, exhaustive coverage would 3× the codebase. The
shared `core/` is mature and stable; per-tool tests catch the cases that
matter (validation, json shape, idempotency).

---

These trade-offs are open to revisit — but they're the current contract.
Anything you build for clibo should fit them.
