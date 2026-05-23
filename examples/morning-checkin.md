# 🌅 Morning check-in — a 60-second routine

The case: it's 7:30am, you've just made coffee. You want to wake your brain
up with a tiny intentional pass over what matters today.

## 1. See what's pending across every active tracker

```bash
clibo checkin
```

`clibo` watches which tools have ≥ 2 entries in the last 14 days and treats
those as "active". Anything you log regularly that doesn't have today's
entry yet shows up as a pending question with a copy-pasteable command and
the last known value.

```
📋 Today's check-ins   0 done   ·   3 pending

  ⚖️  Weight
      ❓ What's your weight today?
      💡 last 71 kg, 1d ago
      ➤  clibo weight log <kg>

  😴  Sleep
      ❓ How many hours did you sleep last night?
      💡 last 7.1h (quality 4/5), 1d ago
      ➤  clibo sleep log <hours> -q <1-5>
```

## 2. Answer them one at a time

```bash
clibo weight log 71.5
clibo sleep log 7.2 -q 4
clibo mood log 4 -e calm,focused
```

## 3. Get the dashboard

```bash
clibo today
```

Today now shows your fresh check-ins inline alongside everything else
that's actionable — water/focus/steps progress, fasting clock, pending
challenges, late packages, expiring documents, tasks due.

## 4. Log your morning coffee with bedtime awareness

```bash
clibo caffeine log coffee
```

The success line reads `Logged ☕ coffee (95 mg) at 08:00 — 13.5 mg residual at
23:30`. You know whether you can have a second cup at 2pm without breaking
your sleep.

## 5. (Optional) Start a fast

```bash
clibo fasting start --target 16
clibo fasting status
```

`status` is the running clock. Check it from `clibo today` later — there's
a progress bar that updates every time you look.

---

**Total typing**: ~30 seconds. **Why it works**: every command takes a single
positional argument plus optional flags, no menus, no modal dialogues. An AI
agent can drive the whole flow via `clibo checkin --json` and ask you each
question conversationally.
