# 🤖 Agent-driven daily brief

The case: you have an AI agent (Claude, GPT, whatever) and you want it to
write you a personalised brief every morning based on your real clibo data.

## The pattern

Every `clibo` command supports `--json`. Errors go to stderr with non-zero
exit codes. That's the entire contract — your agent calls `clibo X --json`,
parses, summarises, asks follow-up questions.

## The three commands your agent needs

```bash
clibo today --json         # what's actionable right now
clibo checkin --json       # pending check-ins per active tracker
clibo streaks --json       # motivational momentum view
```

`today --json` returns a `TodaySnapshot` with:

```json
{
  "date": "2026-05-23",
  "tasks": {"pending": 3, "overdue": [...], "due_today": [...]},
  "habits": {"total": 4, "done_today": 1, "items": [...]},
  "water": {"total_ml": 800, "goal_ml": 2000},
  "calories": {"total_kcal": 1200, "goal_kcal": 2000},
  "focus": {"total_minutes": 25, "goal_minutes": 100},
  "steps": {"total": 6500, "goal": 10000, "reached": false},
  "mood": {"score": 4, "emotion": "calm", "checkins": 1},
  "fasting": null,
  "challenges_pending": [{"id": 1, "name": "no sugar", "day": 5, "target_days": 30}],
  "packages": {"pending": 2, "late": [{"sender": "Amazon", "expected_date": "2026-05-22"}]},
  "documents_expiring": [{"name": "Passport", "expires": "2026-06-17", "days_until": 25}],
  "checkins": [...]
}
```

`checkin --json` gives your agent the structured questions to ask:

```json
{
  "pending_count": 3,
  "pending": [
    {"name": "Weight", "question": "What's your weight today?",
     "command": "clibo weight log <kg>", "last_value": "71 kg", "last_days_ago": 1},
    ...
  ]
}
```

## A simple Python driver

See [`daily_brief.py`](daily_brief.py) for working code. The pattern:

```python
import subprocess, json

def clibo(*args):
    out = subprocess.run(["clibo", *args, "--json"], capture_output=True, check=True, text=True)
    return json.loads(out.stdout)

today = clibo("today")
checkins = clibo("checkin")
streaks = clibo("streaks")

# Now hand `today`, `checkins`, `streaks` to your LLM with a prompt like:
# "Write a one-paragraph morning brief from these dicts. Mention any
#  late packages, pending challenge check-ins, or expiring documents.
#  End with the top 2 pending checkin questions, phrased conversationally."
```

## Suggested agent loops

**Morning brief** (cron at 7am):
1. Call `today`, `streaks`, `checkin` (JSON each).
2. LLM summarises into 5 lines: streak status, water/steps/calorie progress,
   today's tasks, fasting clock if active, one or two open check-ins.
3. Push to your preferred notification channel.

**Evening reflection** (cron at 10pm):
1. Call `today`, `week`, `compare` (JSON each).
2. LLM asks one journaling prompt based on the data ("Your mood dropped by
   1 point from yesterday — what changed?").
3. Pipe the answer to `clibo journal write "..."`.

**Conversational logging** (always on):
1. User says: "I had a coffee at 9am."
2. LLM emits: `clibo caffeine log coffee -t 09:00`.
3. clibo's success line ("13.5 mg residual at 23:00 bedtime") goes back
   to the LLM, which can warn or affirm.

## What clibo does *not* do

- No notifications — that's the agent's job (or a cron + shell).
- No network calls — every clibo command runs locally against
  `~/.clibo/clibo.db`.
- No LLM keys needed — clibo doesn't talk to OpenAI/Anthropic. Your
  agent does.

The boundary is: clibo is the **memory + verbs**, your agent is the
**conversation + cadence**.
