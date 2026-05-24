"""``clibo lifetime`` — all-time aggregates across every tracker.

The companion to ``clibo year``. Where year is "how was 20XX?",
lifetime is "how much have I done in total?". Useful for long-term
trackers — your total mileage, total words written, total books
finished, total income earned, etc.

Compact relative to monthly.py: surfaces the headline all-time
numbers without rebuilding per-tool breakdowns the dedicated
``<tool> stats`` commands already provide.
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
class LifetimeSnapshot:
    """The all-time one-screen view."""

    earliest_log: date | None
    years_tracking: int
    # Money
    income_total: float
    expense_total: float
    donations_total: float
    net_cash_flow: float
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
    weight_min: float | None
    weight_max: float | None
    weight_first: float | None
    weight_last: float | None
    # Misc
    gratitude_entries: int
    currency: str

    def as_dict(self) -> dict:
        return {
            "earliest_log": (
                self.earliest_log.isoformat() if self.earliest_log else None
            ),
            "years_tracking": self.years_tracking,
            "money": {
                "income_total": self.income_total,
                "expense_total": self.expense_total,
                "donations_total": self.donations_total,
                "net_cash_flow": self.net_cash_flow,
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
                "weight_min": self.weight_min,
                "weight_max": self.weight_max,
                "weight_first": self.weight_first,
                "weight_last": self.weight_last,
            },
            "gratitude_entries": self.gratitude_entries,
        }


def collect_lifetime() -> LifetimeSnapshot:
    """Aggregate every tracker across the full history."""
    with session() as db:
        # ── 💰 Money ──────────────────────────────────────────────────
        incomes = list(db.exec(select(IncomeEntry)).all())
        expenses = list(db.exec(select(Expense)).all())
        donations = list(db.exec(select(Donation)).all())
        # ── ✅ Productivity ───────────────────────────────────────────
        tasks_done = list(db.exec(
            select(Task)
            .where(Task.done == True)  # noqa: E712
            .where(Task.done_at.is_not(None))  # type: ignore[union-attr]
        ).all())
        focus_sessions = list(db.exec(select(FocusSession)).all())
        journal_entries = list(db.exec(select(JournalEntry)).all())
        # ── 📚 Hobbies ────────────────────────────────────────────────
        books_finished = list(db.exec(
            select(Book).where(Book.status == "finished")
        ).all())
        films_watched = list(db.exec(
            select(Film).where(Film.status == "watched")
        ).all())
        writing_sessions = list(db.exec(select(WritingSession)).all())
        # ── 🏋️ Health ────────────────────────────────────────────────
        workouts = list(db.exec(select(Workout)).all())
        meditations = list(db.exec(select(MeditationSession)).all())
        sleeps = list(db.exec(select(SleepLog)).all())
        mileage = list(db.exec(select(MileageEntry)).all())
        weights = list(
            db.exec(select(WeightLog).order_by(WeightLog.entry_date)).all()
        )
        gratitudes = list(db.exec(select(GratitudeEntry)).all())

    income_total = round(sum(e.amount for e in incomes), 2)
    expense_total = round(sum(e.amount for e in expenses), 2)
    donations_total = round(sum(e.amount for e in donations), 2)

    avg_sleep_hours = (
        round(sum(s.hours for s in sleeps) / len(sleeps), 2) if sleeps else None
    )

    # Earliest log across every dated table — anchors `years_tracking`.
    earliest_candidates: list[date] = []
    if incomes:
        earliest_candidates.append(min(e.entry_date for e in incomes))
    if expenses:
        earliest_candidates.append(min(e.entry_date for e in expenses))
    if donations:
        earliest_candidates.append(min(e.entry_date for e in donations))
    if journal_entries:
        earliest_candidates.append(min(e.entry_date for e in journal_entries))
    if workouts:
        earliest_candidates.append(min(w.entry_date for w in workouts))
    if writing_sessions:
        earliest_candidates.append(min(w.entry_date for w in writing_sessions))
    if weights:
        earliest_candidates.append(weights[0].entry_date)
    if sleeps:
        earliest_candidates.append(min(s.entry_date for s in sleeps))
    earliest_log = min(earliest_candidates) if earliest_candidates else None
    today = date.today()
    years_tracking = (
        max(1, (today - earliest_log).days // 365 + 1)
        if earliest_log else 0
    )

    weight_min = min((w.weight_kg for w in weights), default=None)
    weight_max = max((w.weight_kg for w in weights), default=None)

    return LifetimeSnapshot(
        earliest_log=earliest_log,
        years_tracking=years_tracking,
        income_total=income_total,
        expense_total=expense_total,
        donations_total=donations_total,
        net_cash_flow=round(income_total - expense_total - donations_total, 2),
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
        weight_min=weight_min,
        weight_max=weight_max,
        weight_first=weights[0].weight_kg if weights else None,
        weight_last=weights[-1].weight_kg if weights else None,
        gratitude_entries=len(gratitudes),
        currency=get_currency(),
    )


def render_lifetime(json_out: bool) -> None:
    """Print the lifetime snapshot to stdout."""
    snap = collect_lifetime()
    if json_out:
        _emit_json(snap.as_dict())
        return

    if snap.earliest_log:
        console.print(
            f"\n♾️  [bold]Lifetime[/bold]   "
            f"[dim]since {snap.earliest_log} "
            f"({snap.years_tracking} year"
            f"{'s' if snap.years_tracking != 1 else ''})[/dim]\n"
        )
    else:
        console.print("\n♾️  [bold]Lifetime[/bold]\n")
        console.print("  [dim]Nothing logged yet. ✨[/dim]\n")
        return

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
        console.print()

    # ✅ Productivity
    if any([snap.tasks_done, snap.focus_minutes, snap.journal_entries]):
        console.print("[bold]✅ Productivity[/bold]")
        if snap.tasks_done:
            console.print(f"  Tasks done       [cyan]{snap.tasks_done:,}[/cyan]")
        if snap.focus_minutes:
            console.print(
                f"  Focus            [cyan]{snap.focus_minutes:,}[/cyan] min "
                f"[dim]({snap.focus_minutes // 60:,}h)[/dim]"
            )
        if snap.journal_entries:
            console.print(
                f"  Journal          [cyan]{snap.journal_entries:,}[/cyan] entries "
                f"on [cyan]{snap.days_journaled:,}[/cyan] days"
            )
        console.print()

    # 📚 Hobbies
    if any([snap.books_finished, snap.films_watched, snap.writing_sessions]):
        console.print("[bold]📚 Hobbies[/bold]")
        if snap.books_finished:
            console.print(
                f"  Books finished   [cyan]{snap.books_finished:,}[/cyan] "
                f"[dim]({snap.pages_read:,} pages)[/dim]"
            )
        if snap.films_watched:
            console.print(f"  Films watched    [cyan]{snap.films_watched:,}[/cyan]")
        if snap.writing_sessions:
            console.print(
                f"  Writing          [cyan]{snap.writing_words:,}[/cyan] words "
                f"across [cyan]{snap.writing_sessions:,}[/cyan] sessions"
            )
        console.print()

    # 🏋️ Health
    if any([snap.workouts, snap.days_meditated, snap.days_slept_logged,
            snap.mileage_km, snap.weight_min is not None]):
        console.print("[bold]🏋️ Health[/bold]")
        if snap.workouts:
            console.print(
                f"  Workouts         [cyan]{snap.workouts:,}[/cyan] "
                f"[dim]({snap.workout_minutes:,} min)[/dim]"
            )
        if snap.days_meditated:
            console.print(
                f"  Meditation       [cyan]{snap.days_meditated:,}[/cyan] days "
                f"[dim]({snap.meditation_minutes:,} min)[/dim]"
            )
        if snap.days_slept_logged and snap.avg_sleep_hours:
            console.print(
                f"  Sleep            avg [cyan]{snap.avg_sleep_hours}h[/cyan] "
                f"over [cyan]{snap.days_slept_logged:,}[/cyan] nights"
            )
        if snap.mileage_km:
            console.print(f"  Distance covered [cyan]{snap.mileage_km:g}[/cyan] km")
        if snap.weight_min is not None and snap.weight_max is not None:
            range_str = (
                f"{snap.weight_min:g}–{snap.weight_max:g}kg"
                if snap.weight_min != snap.weight_max
                else f"{snap.weight_min:g}kg"
            )
            console.print(
                f"  Weight range     [bold]{range_str}[/bold]   "
                f"[dim]({snap.weight_first}kg → {snap.weight_last}kg)[/dim]"
            )
        console.print()

    if snap.gratitude_entries:
        console.print(
            f"  🙏 [bold]{snap.gratitude_entries:,}[/bold] gratitude entries\n"
        )
