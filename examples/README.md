# clibo · examples

Real-world use cases for the 72-tool kit. Each `.md` here is a self-contained
walkthrough of one **case** or one **category** — copy the commands, adapt
to your own data.

## By case

| Walkthrough | What it shows |
|---|---|
| [`morning-checkin.md`](morning-checkin.md) | A 60-second morning routine — `clibo checkin`, `clibo today`, logging water + coffee + mood + weight. |
| [`evening-wrapup.md`](evening-wrapup.md) | Closing the day — journal, gratitude, sleep prep, start a fast. |
| [`weekly-retrospective.md`](weekly-retrospective.md) | Friday/Sunday review — `clibo week`, `clibo compare`, `clibo streaks`. |
| [`monthly-money.md`](monthly-money.md) | End-of-month money rollup — `clibo month`, income vs expense vs net cash flow. |
| [`agent-daily-brief.md`](agent-daily-brief.md) | How an AI agent assembles a personalised daily brief from `--json` output. |

## By category

| Walkthrough | Tools covered |
|---|---|
| [`health-tracking.md`](health-tracking.md) | `weight`, `sleep`, `mood`, `caffeine`, `fasting`, `steps`, `workout`, `meditate`, `stretches`, `mileage` |
| [`money-tracking.md`](money-tracking.md) | `expense`, `income`, `bills`, `subs`, `donations`, `invest`, `debt`, `tip`, `networth` |
| [`productivity.md`](productivity.md) | `todo`, `focus`, `habit`, `challenge`, `journal`, `worklog`, `notes`, `goals`, `bookmark`, `ideas` |
| [`relationships.md`](relationships.md) | `crm`, `network`, `followup`, `meetings`, `birthdays`, `gifts`, `brag`, `cv`, `jobs`, `leads`, `clients` |
| [`home-life.md`](home-life.md) | `groceries`, `pantry`, `recipes`, `meals`, `chores`, `plants`, `car`, `home`, `pets`, `travel`, `packages`, `documents` |
| [`hobbies.md`](hobbies.md) | `books`, `films`, `quotes`, `gratitude`, `lessons`, `flashcards`, `dreams`, `dashboard` |

## Working scripts

If you'd rather copy code than walkthroughs:

| File | What it does |
|---|---|
| [`daily_brief.py`](daily_brief.py) | Python: combines `clibo today --json` + `clibo week --json` into a Markdown brief. |
| [`find_and_act.py`](find_and_act.py) | Agent pattern: `clibo search QUERY --json`, then suggests a follow-up action. |

## The contract every example relies on

- Every command supports `--json` → clean stdout JSON.
- Mutations return the affected record (`clibo todo add ... --json`).
- Errors go to stderr with a non-zero exit code.
- Names work in place of numeric IDs for most resolve-by-name commands.
- `last` works as the ID argument on edit/rm for the most-edited daily trackers.

See [`AGENTS.md`](../AGENTS.md) for the full contract.

> Set `CLIBO_HOME=/tmp/sandbox` to experiment in a throwaway database.
