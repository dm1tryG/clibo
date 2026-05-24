"""``clibo year`` — a calendar-year rollup across every tracker.

Sister to ``clibo today`` (today only), ``clibo week`` (last 7 days)
and ``clibo month`` (calendar month). Where month is "the recent
financial+wellness picture", year is "how was 20XX, in one screen?".

Intentionally compact relative to monthly.py — surfaces the headline
annual numbers across money, productivity, hobbies and health,
without rebuilding every per-tool breakdown the dedicated
``<tool> year`` commands already provide.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlmodel import select

from clibo.clis.books import Book
from clibo.clis.donations import Donation
from clibo.clis.expense import Expense, get_currency, money
from clibo.clis.films import Film
from clibo.clis.focus import FocusSession
from clibo.clis.gratitude import GratitudeEntry
from clibo.clis.income import IncomeEntry
from clibo.clis.journal import JournalEntry
from clibo.clis.meditate import MeditationSession
from clibo.clis.mileage import MileageEntry
from clibo.clis.sleep import SleepLog
from clibo.clis.todo import Task
from clibo.clis.weight import WeightLog
from clibo.clis.workout import Workout
from clibo.clis.writing import WritingSession
from clibo.core.db import session
from clibo.core.output import _emit_json, console


@dataclass
class YearSnapshot:
    """The annual one-screen view."""

    year: int
    start: date
    end: date
    # Money
    income_total: float
    expense_total: float
    donations_total: float
    net_cash_flow: float
    biggest_expense_month: int | None
    # Productivity
    tasks_done: int
    focus_minutes: int
    journal_entries: int
    days_journaled: int
    # Hobbies
    books_finished: int
    pages_read: int
    films_watched: int
    writing_words: int
    writing_sessions: int
    # Health
    workouts: int
    workout_minutes: int
    days_meditated: int
    meditation_minutes: int
    days_slept_logged: int
    avg_sleep_hours: float | None
    mileage_km: float
    weight_change_kg: float | None
    weight_first: float | None
    weight_last: float | None
    # Misc
    gratitude_entries: int
    currency: str

    def as_dict(self) -> dict:
        return {
            "year": self.year,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "money": {
                "income_total": self.income_total,
                "expense_total": self.expense_total,
                "donations_total": self.donations_total,
                "net_cash_flow": self.net_cash_flow,
                "biggest_expense_month": self.biggest_expense_month,
                "currency": self.currency,
            },
            "productivity": {
                "tasks_done": self.tasks_done,
                "focus_minutes": self.focus_minutes,
                "journal_entries": self.journal_entries,
                "days_journaled": self.days_journaled,
            },
            "hobbies": {
                "books_finished": self.books_finished,
                "pages_read": self.pages_read,
                "films_watched": self.films_watched,
                "writing_words": self.writing_words,
                "writing_sessions": self.writing_sessions,
            },
            "health": {
                "workouts": self.workouts,
                "workout_minutes": self.workout_minutes,
                "days_meditated": self.days_meditated,
                "meditation_minutes": self.meditation_minutes,
                "days_slept_logged": self.days_slept_logged,
                "avg_sleep_hours": self.avg_sleep_hours,
                "mileage_km": self.mileage_km,
                "weight_first": self.weight_first,
                "weight_last": self.weight_last,
                "weight_change_kg": self.weight_change_kg,
            },
            "gratitude_entries": self.gratitude_entries,
        }


def collect_year(year: int | None = None) -> YearSnapshot:
    """Aggregate one calendar year across every tracker we know about."""
    target_year = year or date.today().year
    start = date(target_year, 1, 1)
    end = date(target_year, 12, 31)
    with session() as db:
        # ── 💰 Money ──────────────────────────────────────────────────
        incomes = list(db.exec(
            select(IncomeEntry)
            .where(IncomeEntry.entry_date >= start)
            .where(IncomeEntry.entry_date <= end)
        ).all())
        expenses = list(db.exec(
            select(Expense)
            .where(Expense.entry_date >= start)
            .where(Expense.entry_date <= end)
        ).all())
        donations = list(db.exec(
            select(Donation)
            .where(Donation.entry_date >= start)
            .where(Donation.entry_date <= end)
        ).all())
        # ── ✅ Productivity ───────────────────────────────────────────
        tasks_done = list(db.exec(
            select(Task)
            .where(Task.done == True)  # noqa: E712
            .where(Task.done_at.is_not(None))  # type: ignore[union-attr]
            .where(Task.done_at >= start)
            .where(Task.done_at <= end)
        ).all())
        focus_sessions = list(db.exec(
            select(FocusSession)
            .where(FocusSession.entry_date >= start)
            .where(FocusSession.entry_date <= end)
        ).all())
        journal_entries = list(db.exec(
            select(JournalEntry)
            .where(JournalEntry.entry_date >= start)
            .where(JournalEntry.entry_date <= end)
        ).all())
        # ── 📚 Hobbies ────────────────────────────────────────────────
        books_finished = list(db.exec(
            select(Book)
            .where(Book.status == "finished")
            .where(Book.finished.is_not(None))  # type: ignore[union-attr]
            .where(Book.finished >= start)
            .where(Book.finished <= end)
        ).all())
        films_watched = list(db.exec(
            select(Film)
            .where(Film.status == "watched")
            .where(Film.watched_on.is_not(None))  # type: ignore[union-attr]
            .where(Film.watched_on >= start)
            .where(Film.watched_on <= end)
        ).all())
        writing_sessions = list(db.exec(
            select(WritingSession)
            .where(WritingSession.entry_date >= start)
            .where(WritingSession.entry_date <= end)
        ).all())
        # ── 🏋️ Health ────────────────────────────────────────────────
        workouts = list(db.exec(
            select(Workout)
            .where(Workout.entry_date >= start)
            .where(Workout.entry_date <= end)
        ).all())
        meditations = list(db.exec(
            select(MeditationSession)
            .where(MeditationSession.entry_date >= start)
            .where(MeditationSession.entry_date <= end)
        ).all())
        sleeps = list(db.exec(
            select(SleepLog)
            .where(SleepLog.entry_date >= start)
            .where(SleepLog.entry_date <= end)
        ).all())
        mileage = list(db.exec(
            select(MileageEntry)
            .where(MileageEntry.entry_date >= start)
            .where(MileageEntry.entry_date <= end)
        ).all())
        weights = list(db.exec(
            select(WeightLog)
            .where(WeightLog.entry_date >= start)
            .where(WeightLog.entry_date <= end)
            .order_by(WeightLog.entry_date)
        ).all())
        gratitudes = list(db.exec(
            select(GratitudeEntry)
            .where(GratitudeEntry.entry_date >= start)
            .where(GratitudeEntry.entry_date <= end)
        ).all())

    income_total = round(sum(e.amount for e in incomes), 2)
    expense_total = round(sum(e.amount for e in expenses), 2)
    donations_total = round(sum(e.amount for e in donations), 2)

    # Biggest expense month — which of 1–12 had the highest spend.
    by_month: dict[int, float] = {}
    for e in expenses:
        by_month[e.entry_date.month] = by_month.get(e.entry_date.month, 0) + e.amount
    biggest_expense_month = (
        max(by_month, key=lambda m: by_month[m]) if by_month else None
    )

    # Sleep average — only over the nights we actually logged.
    avg_sleep_hours = (
        round(sum(s.hours for s in sleeps) / len(sleeps), 2) if sleeps else None
    )

    weight_first = weights[0].weight_kg if weights else None
    weight_last = weights[-1].weight_kg if weights else None
    weight_change = (
        round(weight_last - weight_first, 2)
        if (weight_first is not None and weight_last is not None)
        else None
    )

    return YearSnapshot(
        year=target_year,
        start=start,
        end=end,
        income_total=income_total,
        expense_total=expense_total,
        donations_total=donations_total,
        net_cash_flow=round(income_total - expense_total - donations_total, 2),
        biggest_expense_month=biggest_expense_month,
        tasks_done=len(tasks_done),
        focus_minutes=sum(f.minutes for f in focus_sessions),
        journal_entries=len(journal_entries),
        days_journaled=len({j.entry_date for j in journal_entries}),
        books_finished=len(books_finished),
        pages_read=sum(b.pages for b in books_finished),
        films_watched=len(films_watched),
        writing_words=sum(w.words for w in writing_sessions),
        writing_sessions=len(writing_sessions),
        workouts=len(workouts),
        workout_minutes=sum(w.duration_min or 0 for w in workouts),
        days_meditated=len({m.entry_date for m in meditations}),
        meditation_minutes=sum(m.minutes for m in meditations),
        days_slept_logged=len({s.entry_date for s in sleeps}),
        avg_sleep_hours=avg_sleep_hours,
        mileage_km=round(sum(m.distance_km for m in mileage), 2),
        weight_change_kg=weight_change,
        weight_first=weight_first,
        weight_last=weight_last,
        gratitude_entries=len(gratitudes),
        currency=get_currency(),
    )


_MONTH_NAMES = [
    "—", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def render_year(year: int | None, json_out: bool) -> None:
    """Print the year snapshot to stdout."""
    snap = collect_year(year=year)
    if json_out:
        _emit_json(snap.as_dict())
        return

    console.print(f"\n📅 [bold]{snap.year}[/bold]   [dim]{snap.start} → {snap.end}[/dim]\n")

    # 💰 Money
    if snap.income_total or snap.expense_total or snap.donations_total:
        console.print("[bold]💰 Money[/bold]")
        console.print(
            f"  💵 Income     [bold green]{money(snap.income_total)}[/bold green]"
        )
        console.print(
            f"  💸 Expenses   [bold red]{money(snap.expense_total)}[/bold red]"
        )
        if snap.donations_total:
            console.print(
                f"  ❤️  Donations  [bold]{money(snap.donations_total)}[/bold]"
            )
        net_colour = "green" if snap.net_cash_flow >= 0 else "red"
        console.print(
            f"  ──  Net cash flow [bold {net_colour}]{money(snap.net_cash_flow)}[/bold {net_colour}]"
        )
        if snap.biggest_expense_month:
            console.print(
                f"  📊 Biggest spend month: [bold]{_MONTH_NAMES[snap.biggest_expense_month]}[/bold]"
            )
        console.print()

    # ✅ Productivity
    if any([snap.tasks_done, snap.focus_minutes, snap.journal_entries]):
        console.print("[bold]✅ Productivity[/bold]")
        if snap.tasks_done:
            console.print(f"  Tasks done       [cyan]{snap.tasks_done}[/cyan]")
        if snap.focus_minutes:
            console.print(
                f"  Focus            [cyan]{snap.focus_minutes:,}[/cyan] min "
                f"[dim]({round(snap.focus_minutes / 60)}h)[/dim]"
            )
        if snap.journal_entries:
            console.print(
                f"  Journal          [cyan]{snap.journal_entries}[/cyan] entries "
                f"on [cyan]{snap.days_journaled}[/cyan] days"
            )
        console.print()

    # 📚 Hobbies
    if any([snap.books_finished, snap.films_watched, snap.writing_sessions]):
        console.print("[bold]📚 Hobbies[/bold]")
        if snap.books_finished:
            console.print(
                f"  Books finished   [cyan]{snap.books_finished}[/cyan] "
                f"[dim]({snap.pages_read:,} pages)[/dim]"
            )
        if snap.films_watched:
            console.print(f"  Films watched    [cyan]{snap.films_watched}[/cyan]")
        if snap.writing_sessions:
            console.print(
                f"  Writing          [cyan]{snap.writing_words:,}[/cyan] words "
                f"across [cyan]{snap.writing_sessions}[/cyan] sessions"
            )
        console.print()

    # 🏋️ Health
    if any([snap.workouts, snap.days_meditated, snap.days_slept_logged,
            snap.mileage_km, snap.weight_change_kg is not None]):
        console.print("[bold]🏋️ Health[/bold]")
        if snap.workouts:
            console.print(
                f"  Workouts         [cyan]{snap.workouts}[/cyan] "
                f"[dim]({snap.workout_minutes:,} min)[/dim]"
            )
        if snap.days_meditated:
            console.print(
                f"  Meditation       [cyan]{snap.days_meditated}[/cyan] days "
                f"[dim]({snap.meditation_minutes:,} min)[/dim]"
            )
        if snap.days_slept_logged and snap.avg_sleep_hours:
            console.print(
                f"  Sleep            avg [cyan]{snap.avg_sleep_hours}h[/cyan] "
                f"over [cyan]{snap.days_slept_logged}[/cyan] nights"
            )
        if snap.mileage_km:
            console.print(f"  Distance covered [cyan]{snap.mileage_km:g}[/cyan] km")
        if snap.weight_change_kg is not None:
            arrow = "↓" if snap.weight_change_kg < 0 else (
                "↑" if snap.weight_change_kg > 0 else "→"
            )
            colour = "green" if snap.weight_change_kg <= 0 else "red"
            console.print(
                f"  Weight           [bold]{snap.weight_first}kg[/bold] → "
                f"[bold]{snap.weight_last}kg[/bold]   "
                f"[{colour}]{arrow} {abs(snap.weight_change_kg):g}kg[/{colour}]"
            )
        console.print()

    # 🙏 Gratitude (one-liner)
    if snap.gratitude_entries:
        console.print(
            f"  🙏 [bold]{snap.gratitude_entries}[/bold] gratitude entries\n"
        )

    if not any([snap.income_total, snap.expense_total, snap.tasks_done,
                snap.books_finished, snap.workouts, snap.writing_sessions]):
        console.print(
            f"  [dim]Nothing logged in {snap.year} yet. ✨[/dim]\n"
        )
