"""``clibo month`` — a calendar-month rollup across trackers.

Sibling to ``clibo today`` (right now) and ``clibo week`` (last 7 days).
The framing here is **calendar month** — "how was your May?" — because
that's the natural unit for money (rent, salary, subs, monthly bills)
and for longer-horizon health trends (avg sleep, total steps).

Pulls data scoped to a single calendar month (``--year`` / ``--month``,
defaulting to the current month) and renders a money-first dashboard
followed by health, productivity and hobby rollups.
"""

from __future__ import annotations

from datetime import date

import typer
from sqlmodel import select

from clibo.clis.bills import Bill
from clibo.clis.books import Book
from clibo.clis.caffeine import CaffeineEntry
from clibo.clis.calorie import CalorieEntry
from clibo.clis.donations import Donation
from clibo.clis.expense import Expense, get_currency, money
from clibo.clis.fasting import FastSession, _duration_hours
from clibo.clis.films import Film
from clibo.clis.focus import FocusSession
from clibo.clis.gratitude import GratitudeEntry
from clibo.clis.habit import HabitCheck
from clibo.clis.income import IncomeEntry
from clibo.clis.invest import Transaction as InvestTransaction
from clibo.clis.journal import JournalEntry
from clibo.clis.meditate import MeditationSession
from clibo.clis.mileage import MileageEntry
from clibo.clis.mood import MoodLog
from clibo.clis.sleep import SleepLog
from clibo.clis.steps import StepEntry
from clibo.clis.stretches import StretchSession
from clibo.clis.subs import Subscription
from clibo.clis.subs import _monthly as _sub_monthly
from clibo.clis.todo import Task
from clibo.clis.water import WaterLog
from clibo.clis.workout import Workout
from clibo.core.db import session
from clibo.core.output import _emit_json, console
from clibo.core.settings import get_setting
from clibo.models import (
    BillsMonth,
    BookFinished,
    CaffeineMonth,
    CalorieMonth,
    DonationsMonth,
    ExpenseMonth,
    FastingMonth,
    FilmWatched,
    FocusMonth,
    HobbiesMonth,
    IncomeMonth,
    InvestMonth,
    MileageMonth,
    MoneyMonth,
    MonthSnapshot,
    MoodWeek,
    ProductivityMonth,
    SleepWeek,
    StepsMonth,
    TimedActivityWeek,
    WaterWeek,
    WorkoutWeek,
)


def _round(value: float, ndigits: int = 1) -> float:
    return round(value, ndigits)


def _month_bounds(year: int, month: int) -> tuple[date, date, int]:
    """Return ``(first_day, last_day, num_days)`` for the given calendar month."""
    first = date(year, month, 1)
    if month == 12:
        next_first = date(year + 1, 1, 1)
    else:
        next_first = date(year, month + 1, 1)
    last = date.fromordinal(next_first.toordinal() - 1)
    return first, last, (next_first.toordinal() - first.toordinal())


def collect_month(year: int | None = None, month: int | None = None) -> MonthSnapshot:
    """Aggregate one calendar month across the trackers."""
    today = date.today()
    year = year or today.year
    month = month or today.month
    start, end, num_days = _month_bounds(year, month)

    water_goal = int(get_setting("water", "daily_ml", "2000") or 2000)
    calorie_goal = int(get_setting("calorie", "daily_kcal", "0") or 0)
    steps_goal = int(get_setting("steps", "daily_goal", "10000") or 10000)
    caffeine_limit = int(get_setting("caffeine", "daily_limit_mg", "400") or 400)
    currency = get_currency()

    with session() as db:
        # 💸 Money in
        incomes = list(
            db.exec(
                select(IncomeEntry)
                .where(IncomeEntry.entry_date >= start)
                .where(IncomeEntry.entry_date <= end)
            ).all()
        )
        # 💸 Money out
        expenses = list(
            db.exec(
                select(Expense)
                .where(Expense.entry_date >= start)
                .where(Expense.entry_date <= end)
            ).all()
        )
        donations = list(
            db.exec(
                select(Donation)
                .where(Donation.entry_date >= start)
                .where(Donation.entry_date <= end)
            ).all()
        )
        bills_due = list(
            db.exec(
                select(Bill)
                .where(Bill.due_date >= start)
                .where(Bill.due_date <= end)
            ).all()
        )
        subs = list(
            db.exec(select(Subscription).where(Subscription.active == True)).all()  # noqa: E712
        )
        invest_txns = list(
            db.exec(
                select(InvestTransaction)
                .where(InvestTransaction.txn_date >= start)
                .where(InvestTransaction.txn_date <= end)
            ).all()
        )
        # Health
        sleeps = list(
            db.exec(
                select(SleepLog)
                .where(SleepLog.entry_date >= start)
                .where(SleepLog.entry_date <= end)
            ).all()
        )
        calories = list(
            db.exec(
                select(CalorieEntry)
                .where(CalorieEntry.entry_date >= start)
                .where(CalorieEntry.entry_date <= end)
            ).all()
        )
        waters = list(
            db.exec(
                select(WaterLog)
                .where(WaterLog.entry_date >= start)
                .where(WaterLog.entry_date <= end)
            ).all()
        )
        steps_entries = list(
            db.exec(
                select(StepEntry)
                .where(StepEntry.entry_date >= start)
                .where(StepEntry.entry_date <= end)
            ).all()
        )
        workouts = list(
            db.exec(
                select(Workout)
                .where(Workout.entry_date >= start)
                .where(Workout.entry_date <= end)
            ).all()
        )
        caffeines = list(
            db.exec(
                select(CaffeineEntry)
                .where(CaffeineEntry.entry_date >= start)
                .where(CaffeineEntry.entry_date <= end)
            ).all()
        )
        fasts = list(
            db.exec(
                select(FastSession)
                .where(FastSession.start_time >= start)
                .where(FastSession.start_time <= end)
                .where(FastSession.end_time.is_not(None))
            ).all()
        )
        meditations = list(
            db.exec(
                select(MeditationSession)
                .where(MeditationSession.entry_date >= start)
                .where(MeditationSession.entry_date <= end)
            ).all()
        )
        stretches = list(
            db.exec(
                select(StretchSession)
                .where(StretchSession.entry_date >= start)
                .where(StretchSession.entry_date <= end)
            ).all()
        )
        mileages = list(
            db.exec(
                select(MileageEntry)
                .where(MileageEntry.entry_date >= start)
                .where(MileageEntry.entry_date <= end)
            ).all()
        )
        moods = list(
            db.exec(
                select(MoodLog)
                .where(MoodLog.entry_date >= start)
                .where(MoodLog.entry_date <= end)
            ).all()
        )
        focus_sessions = list(
            db.exec(
                select(FocusSession)
                .where(FocusSession.entry_date >= start)
                .where(FocusSession.entry_date <= end)
            ).all()
        )
        habit_checks = list(
            db.exec(
                select(HabitCheck)
                .where(HabitCheck.check_date >= start)
                .where(HabitCheck.check_date <= end)
            ).all()
        )
        journal = list(
            db.exec(
                select(JournalEntry)
                .where(JournalEntry.entry_date >= start)
                .where(JournalEntry.entry_date <= end)
            ).all()
        )
        gratitudes = list(
            db.exec(
                select(GratitudeEntry)
                .where(GratitudeEntry.entry_date >= start)
                .where(GratitudeEntry.entry_date <= end)
            ).all()
        )
        tasks_done = list(
            db.exec(
                select(Task).where(
                    Task.done == True, Task.done_at != None,  # noqa: E711, E712
                    Task.done_at >= start, Task.done_at <= end,
                )
            ).all()
        )
        # Books finished this month
        books_finished = list(
            db.exec(
                select(Book)
                .where(Book.finished != None)  # noqa: E711
                .where(Book.finished >= start)
                .where(Book.finished <= end)
            ).all()
        )
        # Films watched this month
        films_watched = list(
            db.exec(
                select(Film)
                .where(Film.watched_on != None)  # noqa: E711
                .where(Film.watched_on >= start)
                .where(Film.watched_on <= end)
            ).all()
        )

    # ── Money rollups ──────────────────────────────────────────────
    income_total = round(sum(i.amount for i in incomes), 2)
    by_income_category: dict[str, float] = {}
    for i in incomes:
        by_income_category[i.category] = round(
            by_income_category.get(i.category, 0) + i.amount, 2
        )
    expense_total = round(sum(e.amount for e in expenses), 2)
    by_expense_category: dict[str, float] = {}
    for e in expenses:
        by_expense_category[e.category] = round(
            by_expense_category.get(e.category, 0) + e.amount, 2
        )
    donation_total = round(sum(d.amount for d in donations), 2)
    # Use the same cycle-to-monthly conversion the subs tool uses.
    subs_monthly_total = round(sum(_sub_monthly(s) for s in subs), 2)
    bills_paid = [b for b in bills_due if b.paid]
    bills_unpaid = [b for b in bills_due if not b.paid]
    invest_bought = round(
        sum(t.shares * t.price_per_share for t in invest_txns if t.action == "buy"),
        2,
    )
    invest_sold = round(
        sum(t.shares * t.price_per_share for t in invest_txns if t.action == "sell"),
        2,
    )
    net_cash = round(
        income_total - expense_total - donation_total - sum(b.amount for b in bills_paid),
        2,
    )

    money_summary = MoneyMonth(
        income=IncomeMonth(
            total=income_total,
            entries=len(incomes),
            by_category=by_income_category,
        ),
        expenses=ExpenseMonth(
            total=expense_total,
            entries=len(expenses),
            by_category=by_expense_category,
            top_category=(
                max(by_expense_category.items(), key=lambda kv: kv[1])
                if by_expense_category else None
            ),
        ),
        donations=DonationsMonth(
            total=donation_total,
            entries=len(donations),
            deductible_total=round(
                sum(d.amount for d in donations if d.tax_deductible), 2
            ),
        ),
        bills=BillsMonth(
            paid=len(bills_paid),
            unpaid=len(bills_unpaid),
            paid_total=round(sum(b.amount for b in bills_paid), 2),
            unpaid_total=round(sum(b.amount for b in bills_unpaid), 2),
        ),
        subs_monthly_total=subs_monthly_total,
        invest=InvestMonth(
            transactions=len(invest_txns),
            buys_total=invest_bought,
            sells_total=invest_sold,
        ),
        net_cash_flow=net_cash,
        currency=currency,
    )

    # ── Health rollups ─────────────────────────────────────────────
    sleep_summary = SleepWeek(
        nights_logged=len({s.entry_date for s in sleeps}),
        avg_hours=_round(sum(s.hours for s in sleeps) / len(sleeps)) if sleeps else None,
        avg_quality=_round(sum(s.quality for s in sleeps) / len(sleeps)) if sleeps else None,
    )
    cal_days = {c.entry_date for c in calories}
    calorie_summary = CalorieMonth(
        days_logged=len(cal_days),
        total_kcal=sum(c.kcal for c in calories),
        avg_per_day=_round(
            sum(c.kcal for c in calories) / len(cal_days), 0
        ) if cal_days else None,
        goal_kcal=calorie_goal or None,
    )
    water_by_day: dict[date, int] = {}
    for w in waters:
        water_by_day[w.entry_date] = water_by_day.get(w.entry_date, 0) + w.amount_ml
    water_summary = WaterWeek(
        days_logged=len(water_by_day),
        total_ml=sum(water_by_day.values()),
        goal_ml=water_goal,
        days_goal_reached=sum(1 for ml in water_by_day.values() if ml >= water_goal),
    )
    steps_by_day: dict[date, int] = {}
    for s in steps_entries:
        steps_by_day[s.entry_date] = steps_by_day.get(s.entry_date, 0) + s.count
    steps_summary = StepsMonth(
        days_logged=len(steps_by_day),
        total=sum(steps_by_day.values()),
        avg_per_logged_day=(
            int(sum(steps_by_day.values()) / len(steps_by_day))
            if steps_by_day else 0
        ),
        goal=steps_goal,
        days_goal_reached=sum(1 for n in steps_by_day.values() if n >= steps_goal),
    )
    workout_summary = WorkoutWeek(
        sessions=len(workouts),
        days_active=len({w.entry_date for w in workouts}),
        total_minutes=sum(w.duration_min for w in workouts),
        total_kcal_burned=sum(w.kcal_burned or 0 for w in workouts),
    )
    caffeine_by_day: dict[date, int] = {}
    for c in caffeines:
        caffeine_by_day[c.entry_date] = caffeine_by_day.get(c.entry_date, 0) + c.mg
    caffeine_summary = CaffeineMonth(
        drinks=len(caffeines),
        days_logged=len(caffeine_by_day),
        total_mg=sum(caffeine_by_day.values()),
        over_limit_days=sum(
            1 for mg in caffeine_by_day.values() if mg > caffeine_limit
        ),
    )
    fast_hours = [_duration_hours(f) for f in fasts]
    fasting_summary = FastingMonth(
        completed=len(fasts),
        total_hours=_round(sum(fast_hours)),
        longest_hours=_round(max(fast_hours)) if fast_hours else 0,
        target_hits=sum(
            1 for f, h in zip(fasts, fast_hours, strict=True)
            if h >= f.target_hours
        ),
    )
    meditate_summary = TimedActivityWeek(
        sessions=len(meditations),
        total_minutes=sum(m.minutes for m in meditations),
        days=len({m.entry_date for m in meditations}),
    )
    stretches_summary = TimedActivityWeek(
        sessions=len(stretches),
        total_minutes=sum(s.duration_min for s in stretches),
        days=len({s.entry_date for s in stretches}),
    )
    mileage_summary = MileageMonth(
        sessions=len(mileages),
        total_km=_round(sum(m.distance_km for m in mileages)),
    )
    mood_summary = MoodWeek(
        checkins=len(moods),
        avg_score=_round(sum(m.score for m in moods) / len(moods)) if moods else None,
    )

    # ── Productivity rollups ───────────────────────────────────────
    focus_summary = FocusMonth(
        sessions=len(focus_sessions),
        total_minutes=sum(f.minutes for f in focus_sessions),
        days=len({f.entry_date for f in focus_sessions}),
    )
    productivity = ProductivityMonth(
        focus=focus_summary,
        habit_checks=len(habit_checks),
        journal_entries=len(journal),
        journal_days=len({j.entry_date for j in journal}),
        gratitude_entries=len(gratitudes),
        gratitude_days=len({g.entry_date for g in gratitudes}),
        tasks_completed=len(tasks_done),
    )

    # ── Hobbies rollups ────────────────────────────────────────────
    hobbies = HobbiesMonth(
        books_finished=[
            BookFinished(title=b.title, author=b.author, rating=b.rating)
            for b in books_finished
        ],
        films_watched=[
            FilmWatched(title=f.title, rating=f.rating, kind=f.kind)
            for f in films_watched
        ],
    )

    return MonthSnapshot(
        year=year,
        month=month,
        month_name=start.strftime("%B %Y"),
        start=start,
        end=end,
        days=num_days,
        money=money_summary,
        sleep=sleep_summary,
        calories=calorie_summary,
        water=water_summary,
        steps=steps_summary,
        workouts=workout_summary,
        caffeine=caffeine_summary,
        fasting=fasting_summary,
        meditate=meditate_summary,
        stretches=stretches_summary,
        mileage=mileage_summary,
        mood=mood_summary,
        productivity=productivity,
        hobbies=hobbies,
    )


def render_month(
    year: int | None = None,
    month: int | None = None,
    json_out: bool = False,
) -> None:
    """Render the calendar-month rollup to stdout."""
    data: MonthSnapshot = collect_month(year, month)
    if json_out:
        _emit_json(data)
        return
    console.print(f"\n🗓️  [bold]{data.month_name}[/bold]   "
                   f"[dim]{data.start:%a %d} → {data.end:%a %d %b}   "
                   f"({data.days} days)[/dim]\n")

    m = data.money
    money_lines: list[str] = []
    if m.income.entries:
        money_lines.append(
            f"💵 Income       [bold]{money(m.income.total)}[/bold]   ·   "
            f"{m.income.entries} "
            f"entr{'ies' if m.income.entries != 1 else 'y'}"
        )
    if m.expenses.entries:
        line = (f"💸 Expenses     [bold]{money(m.expenses.total)}[/bold]   ·   "
                f"{m.expenses.entries} entries")
        if m.expenses.top_category:
            cat, amt = m.expenses.top_category
            line += f"   ·   top: [bold]{cat}[/bold] ({money(amt)})"
        money_lines.append(line)
    if m.donations.entries:
        money_lines.append(
            f"❤️ Donations    [bold]{money(m.donations.total)}[/bold]   ·   "
            f"{m.donations.entries} gift"
            f"{'s' if m.donations.entries != 1 else ''}"
        )
    if m.bills.paid or m.bills.unpaid:
        money_lines.append(
            f"🧾 Bills        paid {m.bills.paid} ({money(m.bills.paid_total)})"
            + (
                f"   ·   [red]{m.bills.unpaid} unpaid "
                f"({money(m.bills.unpaid_total)})[/red]"
                if m.bills.unpaid else ""
            )
        )
    if m.subs_monthly_total:
        money_lines.append(
            f"🔁 Subs         active monthly cost ~"
            f"[bold]{money(m.subs_monthly_total)}[/bold]"
        )
    if m.invest.transactions:
        money_lines.append(
            f"📈 Invest       {m.invest.transactions} transactions   ·   "
            f"buys {money(m.invest.buys_total)}"
            + (f"   ·   sells {money(m.invest.sells_total)}"
               if m.invest.sells_total else "")
        )
    if money_lines:
        console.print("[bold]💰 Money[/bold]")
        for line in money_lines:
            console.print(f"  {line}")
        # Show net only if there were both income and outflows
        if m.income.entries and (
            m.expenses.entries or m.bills.paid or m.donations.entries
        ):
            colour = "green" if m.net_cash_flow >= 0 else "red"
            console.print(
                f"  ──  [{colour}]Net cash flow {money(m.net_cash_flow)}[/{colour}]"
            )
        console.print()

    # Health
    health_lines: list[str] = []
    if data.sleep.nights_logged:
        s = data.sleep
        health_lines.append(
            f"😴 Sleep        [bold]{s.avg_hours}h[/bold] avg over "
            f"{s.nights_logged} nights"
        )
    if data.calories.days_logged:
        c = data.calories
        health_lines.append(
            f"🍎 Calories     [bold]{c.avg_per_day:g}[/bold] kcal/day "
            f"over {c.days_logged} days"
        )
    if data.water.days_logged:
        w = data.water
        health_lines.append(
            f"💧 Water        hit goal [bold]{w.days_goal_reached}/{data.days}[/bold] days"
        )
    if data.steps.days_logged:
        st = data.steps
        health_lines.append(
            f"👟 Steps        [bold]{st.total:,}[/bold] total   ·   "
            f"hit goal {st.days_goal_reached}/{data.days} days"
        )
    if data.workouts.sessions:
        wo = data.workouts
        kcal_part = f"   ·   🔥 {wo.total_kcal_burned} kcal" if wo.total_kcal_burned else ""
        health_lines.append(
            f"🏋️ Workouts     [bold]{wo.sessions}[/bold] sessions   ·   "
            f"{wo.total_minutes} min{kcal_part}"
        )
    if data.caffeine.drinks:
        caf = data.caffeine
        over = (f"   ·   [red]{caf.over_limit_days} over-limit days[/red]"
                if caf.over_limit_days else "")
        health_lines.append(
            f"☕ Caffeine     [bold]{caf.total_mg}[/bold] mg   ·   "
            f"{caf.drinks} drinks{over}"
        )
    if data.fasting.completed:
        fa = data.fasting
        health_lines.append(
            f"🕒 Fasting      [bold]{fa.completed}[/bold] completed   ·   "
            f"{fa.total_hours:g}h total   ·   "
            f"hit target {fa.target_hits}/{fa.completed}"
        )
    if data.meditate.sessions:
        med = data.meditate
        health_lines.append(
            f"🧘 Meditate     [bold]{med.total_minutes}[/bold] min   ·   "
            f"{med.sessions} sessions over {med.days} days"
        )
    if data.mileage.sessions:
        mi = data.mileage
        health_lines.append(
            f"🏃 Mileage      [bold]{mi.total_km:g}[/bold] km   ·   "
            f"{mi.sessions} sessions"
        )
    if data.mood.checkins:
        mo = data.mood
        health_lines.append(
            f"🙂 Mood         [bold]{mo.avg_score}/5[/bold] avg over "
            f"{mo.checkins} check-ins"
        )
    if health_lines:
        console.print("[bold]🏃 Health & wellness[/bold]")
        for line in health_lines:
            console.print(f"  {line}")
        console.print()

    # Productivity
    p = data.productivity
    prod_lines: list[str] = []
    if p.focus.sessions:
        prod_lines.append(
            f"🍅 Focus        [bold]{p.focus.total_minutes}[/bold] min   ·   "
            f"{p.focus.sessions} sessions"
        )
    if p.habit_checks:
        prod_lines.append(f"🔥 Habits       {p.habit_checks} check-ins")
    if p.tasks_completed:
        prod_lines.append(f"✅ Tasks        {p.tasks_completed} completed")
    if p.journal_entries:
        prod_lines.append(
            f"📔 Journal      {p.journal_entries} entries   ·   "
            f"{p.journal_days} days"
        )
    if p.gratitude_entries:
        prod_lines.append(
            f"🙏 Gratitude    {p.gratitude_entries} entries   ·   "
            f"{p.gratitude_days} days"
        )
    if prod_lines:
        console.print("[bold]✅ Productivity[/bold]")
        for line in prod_lines:
            console.print(f"  {line}")
        console.print()

    # Hobbies
    hob = data.hobbies
    if hob.books_finished or hob.films_watched:
        console.print("[bold]🎨 Hobbies[/bold]")
        if hob.books_finished:
            console.print(
                f"  📚 Books finished:   [bold]{len(hob.books_finished)}[/bold] "
                + (" — " + ", ".join(b.title for b in hob.books_finished[:3])
                   if hob.books_finished else "")
            )
        if hob.films_watched:
            console.print(
                f"  🎬 Films watched:    [bold]{len(hob.films_watched)}[/bold]"
            )
        console.print()

    # Empty state
    has_anything = any([
        money_lines, health_lines, prod_lines,
        hob.books_finished, hob.films_watched,
    ])
    if not has_anything:
        console.print(f"  [dim]Nothing logged in {data.month_name}.[/dim]\n")


def month_command(
    year: int = typer.Option(None, "--year", "-y",
                              help="Calendar year (default: current)"),
    month: int = typer.Option(None, "--month", "-m",
                               help="Calendar month 1-12 (default: current)"),
    json_out: bool = typer.Option(False, "--json",
                                   help="Machine-readable JSON output."),
) -> None:
    """🗓️ A calendar-month rollup: money first, then health and productivity."""
    if month is not None and not 1 <= month <= 12:
        typer.echo("Month must be 1-12", err=True)
        raise typer.Exit(code=2)
    render_month(year=year, month=month, json_out=json_out)
