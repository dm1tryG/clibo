# 📊 Weekly retrospective — Friday afternoon or Sunday evening

The case: the week is winding down. You want a real (not hand-waved) look
at how it went, where the trends are, and what to adjust.

## 1. The rollup

```bash
clibo week
```

Sleep avg, focus minutes, mood avg, water hit-rate, steps avg + days at
goal, workouts + kcal, caffeine total + over-limit days, fasting count +
hours, meditate/stretches/mileage minutes, habits hit-target, money block
(expenses + donations), productivity block (tasks + journal + gratitude).

Everything conditional — empty trackers stay quiet.

## 2. Week-over-week comparison

```bash
clibo compare
```

Side-by-side current 7d vs prior 7d. Arrows show the actual direction;
**colour encodes "good or bad" per metric**:

```
😴 Sleep avg               6.5h   →   7.5h           ↑ 15.4%    ← green: more sleep
☕ Caffeine mg            170 mg   →   63 mg          ↓ 62.9%    ← green: less caffeine
💸 Expenses total        150.00   →   25.00          ↓ 83.3%    ← green: less spending
👟 Steps total          15,000   →   19,500         ↑ 30%      ← green: more steps
```

A red ↑ on caffeine means you drank more this week than last — bad. A
red ↓ on sleep means you slept less — also bad. No ambiguity.

## 3. Streaks check

```bash
clibo streaks
```

Habits, gratitude, step-goal, fasting, challenges — every active streak in
one motivational view, sorted strongest-first.

## 4. Drill into a metric

If `compare` shows something surprising, drill into it with `stats`:

```bash
clibo sleep stats --days 14    # Chart  ▁▂▄▅▇█·  ← visual trend
clibo mood stats --days 14
clibo caffeine stats --days 14
```

The new `Chart` row (Unicode sparkline) shows the shape of the trend in
one line. Quick to scan, no chart library needed.

## 5. What to journal

```bash
clibo journal write "Week recap: $(clibo week --json | jq -r .start)→$(clibo week --json | jq -r .end). Best: ... Worst: ... Adjust: ..."
```

Or just open journal:

```bash
clibo journal write "..."
```

## 6. Set the bar for next week

If something slipped, encode an intent now:

```bash
clibo challenge start "no late caffeine" --days 14
clibo habit add "Stretch before bed"
clibo goals add "Average 7.5h sleep next week" -d "in 7 days"
```

---

**Total time**: 5-10 minutes if you actually read what the numbers tell you.
The killer combo is `clibo compare` → `clibo streaks` → `clibo <metric> stats`
for any surprise.
