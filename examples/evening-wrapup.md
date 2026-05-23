# 🌙 Evening wrap-up — closing the day

The case: 10pm, you're winding down. Three minutes to capture what
happened, what you're grateful for, and set yourself up for tomorrow.

## 1. Journal the day

Free-form, takes anything — a sentence, a paragraph, an emotion dump.

```bash
clibo journal write "Big feature shipped. Tired but happy. Tomorrow:
deep work block first thing, no meetings before 11."
```

## 2. Three things you're grateful for

```bash
clibo gratitude add "the team rallied, the puppy sat with me, finished the chapter"
```

One entry per day is enough — the streak fires when you do it consistently.

## 3. Tomorrow's most-important task

```bash
clibo todo add "Ship the auth refactor" -p high -d tomorrow
```

## 4. Check tomorrow's calendar

```bash
clibo events upcoming --days 1
clibo today --on tomorrow   # forward-looking view: pending tasks, expiring docs
```

## 5. Stop the fast (or start one)

If you've been fasting:

```bash
clibo fasting stop
```

If you're starting overnight:

```bash
clibo fasting start --target 16 -t "20:00"
```

## 6. Mark habits that close at end of day

```bash
clibo habit today          # see what's still open
clibo habit check "Read 30 min"
clibo habit check "Stretch 10 min"
```

## 7. Glance at streaks

```bash
clibo streaks
```

Seeing every active streak in one place is the motivational close to the
day. Tomorrow morning, it'll be one day longer.

---

**Why this works**: every command above is non-blocking and `--json`-able.
An AI agent can ask "anything to journal tonight?" and pipe your answer
straight into `clibo journal write`. The wrap-up takes longer with the agent
talking back to you than it does typing — both are < 3 minutes.
