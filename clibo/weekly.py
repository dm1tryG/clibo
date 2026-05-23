"""``clibo week`` — a 7-day rollup across trackers.

Sister command to ``clibo today``. Where today is about *what's actionable
now*, week is about *how the last seven days actually went* — averages,
totals, streaks. Renders one screen for humans and a single dict for agents.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlmodel import select

from clibo.clis.caffeine import CaffeineEntry
from clibo.clis.calorie import CalorieEntry
from clibo.clis.donations import Donation
from clibo.clis.expense import Expense, get_currency, money
from clibo.clis.fasting import FastSession, _duration_hours
from clibo.clis.focus import FocusSession
from clibo.clis.gratitude import GratitudeEntry
from clibo.clis.habit import Habit, HabitCheck
from clibo.clis.journal import JournalEntry
from clibo.clis.meditate import MeditationSession
from clibo.clis.mileage import MileageEntry
from clibo.clis.mood import MoodLog
from clibo.clis.sleep import SleepLog
from clibo.clis.steps import StepEntry
from clibo.clis.stretches import StretchSession
from clibo.clis.todo import Task
from clibo.clis.water import WaterLog
from clibo.clis.worklog import WorkLogEntry
from clibo.clis.workout import Workout
from clibo.core.db import session
from clibo.core.output import _emit_json, bar, console
from clibo.core.settings import get_setting
from clibo.models import (
    CaffeineWeek,
    CalorieWeek,
    CategoryTotal,
    DonationsWeek,
    ExpensesWeek,
    FastingWeek,
    FocusWeek,
    GratitudeWeek,
    HabitsWeek,
    HabitWeekRow,
    JournalWeek,
    MileageWeek,
    MoodWeek,
    SleepWeek,
    StepsWeek,
    TasksWeek,
    TimedActivityWeek,
    WaterWeek,
    WeekSnapshot,
    WorklogWeek,
    WorkoutWeek,
)

WINDOW_DAYS = 7


def _round(value: float, ndigits: int = 1) -> float:
    return round(value, ndigits)


def collect_week(start: date | None = None) -> WeekSnapshot:
    """Aggregate a 7-day window across every time-series tracker.

    By default the window ends today (i.e. the last 7 days). Passing ``start``
    overrides the window so the same code can produce a *prior* week's
    rollup for comparison views like ``clibo compare``.
    """
    if start is None:
        today = date.today()
        start = today - timedelta(days=WINDOW_DAYS - 1)
    else:
        today = start + timedelta(days=WINDOW_DAYS - 1)
    water_goal = int(get_setting("water", "daily_ml", "2000") or 2000)
    calorie_goal = int(get_setting("calorie", "daily_kcal", "0") or 0)
    focus_goal = int(get_setting("focus", "daily_min", "100") or 100)

    with session() as db:
        sleeps = list(
            db.exec(select(SleepLog).where(SleepLog.entry_date >= start).where(SleepLog.entry_date <= today)).all()
        )
        calories = list(
            db.exec(select(CalorieEntry).where(CalorieEntry.entry_date >= start).where(CalorieEntry.entry_date <= today)).all()
        )
        waters = list(
            db.exec(select(WaterLog).where(WaterLog.entry_date >= start).where(WaterLog.entry_date <= today)).all()
        )
        focus = list(
            db.exec(select(FocusSession).where(FocusSession.entry_date >= start).where(FocusSession.entry_date <= today)).all()
        )
        moods = list(
            db.exec(select(MoodLog).where(MoodLog.entry_date >= start).where(MoodLog.entry_date <= today)).all()
        )
        expenses = list(
            db.exec(select(Expense).where(Expense.entry_date >= start).where(Expense.entry_date <= today)).all()
        )
        journal = list(
            db.exec(select(JournalEntry).where(JournalEntry.entry_date >= start).where(JournalEntry.entry_date <= today)).all()
        )
        worklog = list(
            db.exec(select(WorkLogEntry).where(WorkLogEntry.entry_date >= start).where(WorkLogEntry.entry_date <= today)).all()
        )
        tasks_done = list(
            db.exec(
                select(Task).where(
                    Task.done == True, Task.done_at != None,  # noqa: E711, E712
                    Task.done_at >= start,
                    Task.done_at <= today + timedelta(days=1),
                )
            ).all()
        )
        habits = list(
            db.exec(select(Habit).where(Habit.active == True)).all()  # noqa: E712
        )
        habit_checks = list(
            db.exec(select(HabitCheck).where(HabitCheck.check_date >= start).where(HabitCheck.check_date <= today)).all()
        )
        # Post-v1.0 trackers ───────────────────────────────────────────
        steps_entries = list(
            db.exec(select(StepEntry).where(StepEntry.entry_date >= start).where(StepEntry.entry_date <= today)).all()
        )
        workouts = list(
            db.exec(select(Workout).where(Workout.entry_date >= start).where(Workout.entry_date <= today)).all()
        )
        caffeines = list(
            db.exec(
                select(CaffeineEntry).where(CaffeineEntry.entry_date >= start).where(CaffeineEntry.entry_date <= today)
            ).all()
        )
        fasts = list(
            db.exec(
                select(FastSession).where(FastSession.start_time >= start)
                .where(FastSession.start_time <= today + timedelta(days=1))
                .where(FastSession.end_time.is_not(None))
            ).all()
        )
        meditations = list(
            db.exec(
                select(MeditationSession).where(MeditationSession.entry_date >= start).where(MeditationSession.entry_date <= today)
            ).all()
        )
        stretches = list(
            db.exec(
                select(StretchSession).where(StretchSession.entry_date >= start).where(StretchSession.entry_date <= today)
            ).all()
        )
        mileages = list(
            db.exec(
                select(MileageEntry).where(MileageEntry.entry_date >= start).where(MileageEntry.entry_date <= today)
            ).all()
        )
        gratitudes = list(
            db.exec(
                select(GratitudeEntry).where(GratitudeEntry.entry_date >= start).where(GratitudeEntry.entry_date <= today)
            ).all()
        )
        donations = list(
            db.exec(select(Donation).where(Donation.entry_date >= start).where(Donation.entry_date <= today)).all()
        )

    # Sleep
    sleep_summary = SleepWeek(
        nights_logged=len({s.entry_date for s in sleeps}),
        avg_hours=_round(sum(s.hours for s in sleeps) / len(sleeps)) if sleeps else None,
        avg_quality=_round(sum(s.quality for s in sleeps) / len(sleeps)) if sleeps else None,
    )
    # Calories
    cal_days = {c.entry_date for c in calories}
    calorie_summary = CalorieWeek(
        days_logged=len(cal_days),
        total_kcal=sum(c.kcal for c in calories),
        avg_kcal_per_logged_day=(
            _round(sum(c.kcal for c in calories) / len(cal_days), 0) if cal_days else None
        ),
        goal_kcal=calorie_goal or None,
    )
    # Water
    water_by_day: dict[date, int] = {}
    for w in waters:
        water_by_day[w.entry_date] = water_by_day.get(w.entry_date, 0) + w.amount_ml
    water_summary = WaterWeek(
        days_logged=len(water_by_day),
        total_ml=sum(water_by_day.values()),
        goal_ml=water_goal,
        days_goal_reached=sum(1 for ml in water_by_day.values() if ml >= water_goal),
    )
    # Focus
    focus_summary = FocusWeek(
        sessions=len(focus),
        total_minutes=sum(f.minutes for f in focus),
        days_focused=len({f.entry_date for f in focus}),
        goal_minutes_per_day=focus_goal,
    )
    # Mood
    mood_summary = MoodWeek(
        checkins=len(moods),
        avg_score=_round(sum(m.score for m in moods) / len(moods)) if moods else None,
    )
    # Expenses
    expense_total = round(sum(e.amount for e in expenses), 2)
    by_category: dict[str, float] = {}
    for entry in expenses:
        by_category[entry.category] = round(
            by_category.get(entry.category, 0) + entry.amount, 2
        )
    top_category = max(by_category.items(), key=lambda kv: kv[1], default=None)
    expense_summary = ExpensesWeek(
        entries=len(expenses),
        total=expense_total,
        avg_per_day=_round(expense_total / WINDOW_DAYS, 2),
        top_category=(
            CategoryTotal(category=top_category[0], amount=top_category[1])
            if top_category else None
        ),
        currency=get_currency(),
    )
    # Productivity
    journal_summary = JournalWeek(
        entries=len(journal),
        days_journaled=len({j.entry_date for j in journal}),
    )
    worklog_summary = WorklogWeek(
        entries=len(worklog),
        by_kind={
            kind: sum(1 for w in worklog if w.kind == kind)
            for kind in ("done", "doing", "blocked", "note")
        },
    )
    tasks_summary = TasksWeek(completed=len(tasks_done))
    # Habits — checks per habit this week, vs target
    habit_rows: list[HabitWeekRow] = []
    for habit in habits:
        done = sum(1 for c in habit_checks if c.habit_id == habit.id)
        habit_rows.append(HabitWeekRow(
            name=habit.name,
            done=done,
            target_per_week=habit.target_per_week,
            hit_target=done >= habit.target_per_week,
        ))
    habits_summary = HabitsWeek(
        tracked=len(habits),
        items=habit_rows,
        hit_target=sum(1 for h in habit_rows if h.hit_target),
    )

    # 👟 Steps
    steps_by_day: dict[date, int] = {}
    for s in steps_entries:
        steps_by_day[s.entry_date] = steps_by_day.get(s.entry_date, 0) + s.count
    steps_goal = int(get_setting("steps", "daily_goal", "10000") or 10000)
    steps_summary = StepsWeek(
        days_logged=len(steps_by_day),
        total=sum(steps_by_day.values()),
        avg_per_logged_day=(
            int(sum(steps_by_day.values()) / len(steps_by_day))
            if steps_by_day else 0
        ),
        goal=steps_goal,
        days_goal_reached=sum(1 for n in steps_by_day.values() if n >= steps_goal),
    )
    # 🏋️ Workouts
    workout_summary = WorkoutWeek(
        sessions=len(workouts),
        days_active=len({w.entry_date for w in workouts}),
        total_minutes=sum(w.duration_min for w in workouts),
        total_kcal_burned=sum(w.kcal_burned or 0 for w in workouts),
    )
    # ☕ Caffeine
    caffeine_by_day: dict[date, int] = {}
    for c in caffeines:
        caffeine_by_day[c.entry_date] = caffeine_by_day.get(c.entry_date, 0) + c.mg
    caffeine_limit = int(get_setting("caffeine", "daily_limit_mg", "400") or 400)
    caffeine_summary = CaffeineWeek(
        drinks=len(caffeines),
        days_logged=len(caffeine_by_day),
        total_mg=sum(caffeine_by_day.values()),
        avg_mg_per_logged_day=(
            _round(sum(caffeine_by_day.values()) / len(caffeine_by_day), 0)
            if caffeine_by_day else 0
        ),
        over_limit_days=sum(
            1 for mg in caffeine_by_day.values() if mg > caffeine_limit
        ),
    )
    # 🕒 Fasting
    fast_hours = [_duration_hours(f) for f in fasts]
    fast_hit_target = sum(
        1 for f, hours in zip(fasts, fast_hours, strict=True)
        if hours >= f.target_hours
    )
    fasting_summary = FastingWeek(
        completed=len(fasts),
        total_hours=_round(sum(fast_hours)),
        avg_hours=_round(sum(fast_hours) / len(fasts)) if fasts else 0,
        longest_hours=_round(max(fast_hours)) if fast_hours else 0,
        target_hits=fast_hit_target,
    )
    # 🧘 Meditation
    meditate_summary = TimedActivityWeek(
        sessions=len(meditations),
        days=len({m.entry_date for m in meditations}),
        total_minutes=sum(m.minutes for m in meditations),
    )
    # 🧎 Stretches
    stretch_summary = TimedActivityWeek(
        sessions=len(stretches),
        days=len({s.entry_date for s in stretches}),
        total_minutes=sum(s.duration_min for s in stretches),
    )
    # 🏃 Mileage
    mileage_summary = MileageWeek(
        sessions=len(mileages),
        total_km=_round(sum(m.distance_km for m in mileages)),
        by_activity={
            activity: _round(sum(m.distance_km for m in mileages
                                  if m.activity == activity))
            for activity in {m.activity for m in mileages}
        },
    )
    # 🙏 Gratitude
    gratitude_summary = GratitudeWeek(
        entries=len(gratitudes),
        days_logged=len({g.entry_date for g in gratitudes}),
    )
    # ❤️ Donations
    donation_total = round(sum(d.amount for d in donations), 2)
    donation_summary = DonationsWeek(
        entries=len(donations),
        total=donation_total,
        deductible_total=round(
            sum(d.amount for d in donations if d.tax_deductible), 2
        ),
        recipients=len({d.recipient for d in donations}),
    )

    return WeekSnapshot(
        start=start,
        end=today,
        days=WINDOW_DAYS,
        sleep=sleep_summary,
        calories=calorie_summary,
        water=water_summary,
        focus=focus_summary,
        mood=mood_summary,
        expenses=expense_summary,
        habits=habits_summary,
        journal=journal_summary,
        worklog=worklog_summary,
        tasks=tasks_summary,
        steps=steps_summary,
        workouts=workout_summary,
        caffeine=caffeine_summary,
        fasting=fasting_summary,
        meditate=meditate_summary,
        stretches=stretch_summary,
        mileage=mileage_summary,
        gratitude=gratitude_summary,
        donations=donation_summary,
    )


def render_week(json_out: bool) -> None:
    """Render the weekly rollup to stdout."""
    data: WeekSnapshot = collect_week()
    if json_out:
        _emit_json(data)
        return
    console.print(
        f"\n🗓️  [bold]Last 7 days[/bold]   [dim]{data.start:%a %d %b}[/dim] → "
        f"[dim]{data.end:%a %d %b}[/dim]\n"
    )

    # 😴 Sleep, 🍎 Calories, 💧 Water, 🍅 Focus — health metrics block
    metric_lines: list[str] = []
    if data.sleep.nights_logged:
        s = data.sleep
        metric_lines.append(
            f"😴 Sleep      [bold]{s.avg_hours}h[/bold] avg over "
            f"[cyan]{s.nights_logged}[/cyan] nights"
            + (f"   ·   quality {s.avg_quality}/5" if s.avg_quality else "")
        )
    if data.calories.days_logged:
        c = data.calories
        metric_lines.append(
            f"🍎 Calories   [bold]{c.avg_kcal_per_logged_day:g}[/bold] kcal/day "
            f"over [cyan]{c.days_logged}[/cyan] days"
        )
    if data.water.days_logged:
        w = data.water
        metric_lines.append(
            f"💧 Water      hit goal [bold]{w.days_goal_reached}/7[/bold] days   "
            f"·   {w.total_ml} ml total"
        )
    if data.focus.sessions:
        f = data.focus
        metric_lines.append(
            f"🍅 Focus      [bold]{f.total_minutes}[/bold] min across "
            f"{f.sessions} sessions, [cyan]{f.days_focused}[/cyan] days"
        )
    if data.mood.checkins:
        m = data.mood
        metric_lines.append(
            f"🙂 Mood       [bold]{m.avg_score}/5[/bold] avg over "
            f"{m.checkins} check-ins"
        )
    if data.steps.days_logged:
        st = data.steps
        metric_lines.append(
            f"👟 Steps      hit goal [bold]{st.days_goal_reached}/7[/bold] days   "
            f"·   avg {st.avg_per_logged_day:,}/day   "
            f"·   {st.total:,} total"
        )
    if data.workouts.sessions:
        wo = data.workouts
        kcal_part = f"   ·   🔥 {wo.total_kcal_burned} kcal" if wo.total_kcal_burned else ""
        metric_lines.append(
            f"🏋️ Workouts   [bold]{wo.sessions}[/bold] sessions across "
            f"[cyan]{wo.days_active}[/cyan] days   "
            f"·   {wo.total_minutes} min{kcal_part}"
        )
    if data.caffeine.drinks:
        caf = data.caffeine
        over_part = (f"   ·   [red]{caf.over_limit_days} over-limit "
                      f"day{'s' if caf.over_limit_days != 1 else ''}[/red]"
                      if caf.over_limit_days else "")
        metric_lines.append(
            f"☕ Caffeine   [bold]{caf.total_mg}[/bold] mg total   ·   "
            f"avg {caf.avg_mg_per_logged_day:g}/day{over_part}"
        )
    if data.fasting.completed:
        fa = data.fasting
        metric_lines.append(
            f"🕒 Fasting    [bold]{fa.completed}[/bold] completed   ·   "
            f"{fa.total_hours:g}h total   ·   "
            f"longest {fa.longest_hours:g}h   "
            f"·   hit target {fa.target_hits}/{fa.completed}"
        )
    if data.meditate.sessions:
        med = data.meditate
        metric_lines.append(
            f"🧘 Meditate   [bold]{med.total_minutes}[/bold] min across "
            f"{med.sessions} sessions, [cyan]{med.days}[/cyan] days"
        )
    if data.stretches.sessions:
        sr = data.stretches
        metric_lines.append(
            f"🧎 Stretches  [bold]{sr.total_minutes}[/bold] min across "
            f"{sr.sessions} sessions, [cyan]{sr.days}[/cyan] days"
        )
    if data.mileage.sessions:
        mi = data.mileage
        breakdown = (" (" + ", ".join(
            f"{a}: {km:g}" for a, km in mi.by_activity.items()
        ) + ")") if mi.by_activity else ""
        metric_lines.append(
            f"🏃 Mileage    [bold]{mi.total_km:g}[/bold] km across "
            f"{mi.sessions} sessions{breakdown}"
        )
    if metric_lines:
        for line in metric_lines:
            console.print(f"  {line}")
        console.print()

    # 🔥 Habits
    if data.habits.tracked:
        console.print(
            f"[bold]🔥 Habits[/bold]   "
            f"[cyan]{data.habits.hit_target}[/cyan]/{data.habits.tracked} hit target"
        )
        for item in data.habits.items:
            ratio = bar(item.done, item.target_per_week, width=14)
            mark = "[green]✓[/green]" if item.hit_target else "[dim]·[/dim]"
            console.print(
                f"  {mark} {item.name:<22} {ratio}  "
                f"[dim]{item.done}/{item.target_per_week}[/dim]"
            )
        console.print()

    # 💸 Expenses + ❤️ Donations (money block)
    e = data.expenses
    d = data.donations
    money_lines: list[str] = []
    if e.entries:
        line = f"💸 Expenses   {money(e.total)} total   ·   {e.entries} entries"
        if e.top_category:
            line += (
                f"   ·   top: [bold]{e.top_category.category}[/bold] "
                f"({money(e.top_category.amount)})"
            )
        money_lines.append(line)
    if d.entries:
        deductible_part = (
            f"   ·   {money(d.deductible_total)} deductible"
            if d.deductible_total != d.total else ""
        )
        money_lines.append(
            f"❤️ Donations  {money(d.total)} total   ·   "
            f"{d.entries} gift{'s' if d.entries != 1 else ''}"
            f"   ·   {d.recipients} recipient{'s' if d.recipients != 1 else ''}"
            f"{deductible_part}"
        )
    if money_lines:
        console.print("[bold]💰 Money[/bold]")
        for line in money_lines:
            console.print(f"  {line}")
        console.print()

    # ✅ Tasks, 📔 Journal, 🗒️ Worklog, 🙏 Gratitude
    gr = data.gratitude
    has_productivity = (
        data.tasks.completed or data.journal.entries
        or data.worklog.entries or gr.entries
    )
    if has_productivity:
        console.print("[bold]✅ Productivity[/bold]")
        if data.tasks.completed:
            console.print(f"  Tasks completed:  {data.tasks.completed}")
        if data.journal.entries:
            j = data.journal
            console.print(
                f"  Journal entries:  {j.entries}  "
                f"[dim]({j.days_journaled} days journaled)[/dim]"
            )
        if data.worklog.entries:
            wl = data.worklog.by_kind
            parts = [f"{kind}: {wl[kind]}" for kind in ("done", "doing", "blocked") if wl.get(kind)]
            if parts:
                console.print(f"  Worklog:          {', '.join(parts)}")
        if gr.entries:
            console.print(
                f"  Gratitude:        {gr.entries} entries  "
                f"[dim]({gr.days_logged} days)[/dim]"
            )
        console.print()

    if not metric_lines and not data.habits.tracked and not money_lines \
            and not has_productivity:
        console.print("  [dim]Nothing logged in the last 7 days yet.[/dim]\n")
