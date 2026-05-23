# 🏃 Health & wellness tracking

Tools covered: `weight`, `sleep`, `mood`, `caffeine`, `fasting`, `steps`,
`workout`, `meditate`, `stretches`, `mileage`, `vitals`, `meds`, `period`.

## The daily ones

Log these whenever — most accept backdating via `-d "yesterday"` /
`-d "3 days ago"`.

```bash
clibo weight log 71.5
clibo sleep log 7.5 -q 4 --bed 23:00 --wake 06:30
clibo mood log 4 -e calm,focused -n "feels like a Tuesday"
clibo caffeine log coffee                   # uses preset mg
clibo caffeine log cold-brew -m 220 -t 14:30 # custom mg, specific time
clibo steps log 8500 -s apple_watch
clibo water drink 500                       # or `water add 500`
```

## Fix a typo right after

Every daily logger accepts `edit ID|last`:

```bash
clibo weight log 75              # typo
clibo weight edit last -w 71.5   # fix the most recent without looking up the ID
clibo mood edit last -e anxious
clibo sleep edit last -H 7.8 -q 5
```

## The killer questions

```bash
# "Can I have another coffee at 4pm without breaking sleep?"
clibo caffeine cutoff                 # latest-safe-time table

# "How much caffeine is still in me at bedtime?"
clibo caffeine today                  # has 'residual_at_bedtime_mg'

# "Plot my weight trend."
clibo weight stats --days 30          # has a Chart sparkline `█▇▅▄▂▁`

# "Am I sleeping enough this week?"
clibo sleep stats --days 7

# "Am I still fasting?"
clibo fasting status                  # running clock vs target

# "How was my mood lately?"
clibo mood stats --days 14
```

## Exercise

```bash
clibo workout log "running" -t 30 -c 350     # cardio with kcal
clibo workout log "squat" -s 5 -r 5 -w 80    # strength
clibo mileage log 5 -a run -t 25             # explicit distance
clibo stretches log hamstrings -m 10
clibo meditate log 15 -k mindfulness
```

## Stats with sparklines

```bash
clibo weight stats --days 30
clibo sleep stats --days 14
clibo steps stats --days 30
clibo caffeine stats --days 30
clibo mood stats --days 30
```

Every one of these shows a Unicode sparkline (`▁▂▃▄▅▆▇█·`) on a `Chart`
row, so trend direction is one glance.

## Vitals

```bash
clibo vitals bp 120 80         # blood pressure
clibo vitals pulse 72
clibo vitals glucose 90
clibo vitals spo2 98
clibo vitals temp 36.7
```

## Health & wellness in `today` / `week` / `month`

All of the above flow into the three integration views automatically — no
extra config. `clibo today` surfaces fasting clock, caffeine residual,
mood, steps, workout count, and the **Daily check-ins** section that lists
every actively-tracked daily metric with ✓/○ status.
