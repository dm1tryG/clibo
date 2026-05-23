"""``clibo compare`` — week-over-week diffs across every tracker.

The view answers "how did this week compare to last?". Re-uses
:func:`collect_week` twice (current 7-day window and the 7 days
prior) and renders the headline metrics side-by-side with deltas.

For each row we mark the direction as **better/worse/neutral** based
on a per-metric `more_is_better` polarity:

* sleep avg, mood avg, steps total, workouts, meditate, journal,
  gratitude → more is better → green ↑ / red ↓
* expenses total, caffeine total → less is better → green ↓ / red ↑
* mileage, focus → more is better
* Anything else displays the raw delta without colour.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from clibo.models import MonthSnapshot, WeekSnapshot
from clibo.monthly import collect_month
from clibo.weekly import WINDOW_DAYS, collect_week


@dataclass(frozen=True)
class _Metric:
    """One side-by-side row in the comparison view."""

    label: str
    emoji: str
    extract: Callable[[WeekSnapshot], float | None]
    format: Callable[[float], str]
    # +1 if more is better, -1 if less is better, 0 if neutral.
    polarity: int = 0


def _fmt_int(v: float) -> str:
    return f"{int(v):,}"


def _fmt_float(v: float) -> str:
    return f"{v:g}"


def _fmt_minutes(v: float) -> str:
    return f"{int(v)} min"


def _fmt_money(v: float) -> str:
    # The currency suffix is added by render code; keep this neutral.
    return f"{v:.2f}"


METRICS: list[_Metric] = [
    _Metric("Sleep avg", "😴",
            lambda w: w.sleep.avg_hours,
            lambda v: f"{v:g}h", polarity=+1),
    _Metric("Calories avg", "🍎",
            lambda w: w.calories.avg_kcal_per_logged_day,
            lambda v: f"{int(v):,} kcal", polarity=0),
    _Metric("Water days @ goal", "💧",
            lambda w: float(w.water.days_goal_reached),
            lambda v: f"{int(v)}/7", polarity=+1),
    _Metric("Focus min", "🍅",
            lambda w: float(w.focus.total_minutes),
            _fmt_minutes, polarity=+1),
    _Metric("Mood avg", "🙂",
            lambda w: w.mood.avg_score,
            lambda v: f"{v:g}/5", polarity=+1),
    _Metric("Steps total", "👟",
            lambda w: float(w.steps.total),
            _fmt_int, polarity=+1),
    _Metric("Workouts", "🏋️",
            lambda w: float(w.workouts.sessions),
            lambda v: f"{int(v)}", polarity=+1),
    _Metric("Caffeine mg", "☕",
            lambda w: float(w.caffeine.total_mg),
            lambda v: f"{int(v)} mg", polarity=-1),
    _Metric("Fasts completed", "🕒",
            lambda w: float(w.fasting.completed),
            lambda v: f"{int(v)}", polarity=+1),
    _Metric("Meditate min", "🧘",
            lambda w: float(w.meditate.total_minutes),
            _fmt_minutes, polarity=+1),
    _Metric("Stretches min", "🧎",
            lambda w: float(w.stretches.total_minutes),
            _fmt_minutes, polarity=+1),
    _Metric("Mileage km", "🏃",
            lambda w: w.mileage.total_km,
            lambda v: f"{v:g} km", polarity=+1),
    _Metric("Expenses total", "💸",
            lambda w: w.expenses.total,
            _fmt_money, polarity=-1),
    _Metric("Donations total", "❤️",
            lambda w: w.donations.total,
            _fmt_money, polarity=+1),
    _Metric("Habits hit target", "🔥",
            lambda w: float(w.habits.hit_target),
            lambda v: f"{int(v)}/{int(_metric_habit_total)}", polarity=+1),
    _Metric("Journal entries", "📔",
            lambda w: float(w.journal.entries),
            lambda v: f"{int(v)}", polarity=+1),
    _Metric("Gratitude entries", "🙏",
            lambda w: float(w.gratitude.entries),
            lambda v: f"{int(v)}", polarity=+1),
    _Metric("Tasks completed", "✅",
            lambda w: float(w.tasks.completed),
            lambda v: f"{int(v)}", polarity=+1),
]
# The habit-target formatter wants the *current* tracked count, which is a
# per-snapshot value — we patch it in at render time. This sentinel makes
# the static formatter survive `repr` if ever logged.
_metric_habit_total = 0


@dataclass(frozen=True)
class CompareRow:
    """One row produced by :func:`compare_weeks` for rendering."""

    label: str
    emoji: str
    current: float | None
    prior: float | None
    current_display: str
    prior_display: str
    delta: float | None
    delta_pct: float | None
    direction: str  # "better" / "worse" / "neutral" / "n/a"


def _direction(
    current: float | None, prior: float | None, polarity: int
) -> str:
    if current is None or prior is None:
        return "n/a"
    if current == prior:
        return "neutral"
    if polarity == 0:
        return "neutral"
    better = (current > prior) if polarity > 0 else (current < prior)
    return "better" if better else "worse"


def compare_weeks(
    current_start: date | None = None,
) -> tuple[WeekSnapshot, WeekSnapshot, list[CompareRow]]:
    """Compare the current 7-day window against the 7 days before it.

    Returns ``(current_snapshot, prior_snapshot, rows)``. ``rows`` is a
    list of :class:`CompareRow` ready for rendering.
    """
    if current_start is None:
        current_start = date.today() - timedelta(days=WINDOW_DAYS - 1)
    prior_start = current_start - timedelta(days=WINDOW_DAYS)
    current = collect_week(start=current_start)
    prior = collect_week(start=prior_start)
    rows: list[CompareRow] = []
    for metric in METRICS:
        cur = metric.extract(current)
        pri = metric.extract(prior)
        if metric.label == "Habits hit target":
            # Format wants /{tracked}; use the current tracked count.
            tracked = current.habits.tracked
            cur_str = (f"{int(cur)}/{tracked}" if cur is not None else "—")
            pri_str = (f"{int(pri)}/{prior.habits.tracked}"
                       if pri is not None else "—")
        else:
            cur_str = metric.format(cur) if cur is not None else "—"
            pri_str = metric.format(pri) if pri is not None else "—"
        delta = (cur - pri) if (cur is not None and pri is not None) else None
        delta_pct = None
        if delta is not None and pri:
            delta_pct = round(100 * delta / pri, 1)
        rows.append(CompareRow(
            label=metric.label,
            emoji=metric.emoji,
            current=cur,
            prior=pri,
            current_display=cur_str,
            prior_display=pri_str,
            delta=delta,
            delta_pct=delta_pct,
            direction=_direction(cur, pri, metric.polarity),
        ))
    return current, prior, rows


MONTH_METRICS: list[_Metric] = [
    _Metric("Income", "💵",
            lambda m: m.money.income.total,
            _fmt_money, polarity=+1),
    _Metric("Expenses", "💸",
            lambda m: m.money.expenses.total,
            _fmt_money, polarity=-1),
    _Metric("Donations", "❤️",
            lambda m: m.money.donations.total,
            _fmt_money, polarity=+1),
    _Metric("Bills paid", "🧾",
            lambda m: float(m.money.bills.paid),
            lambda v: f"{int(v)}", polarity=0),
    _Metric("Net cash flow", "💰",
            lambda m: m.money.net_cash_flow,
            _fmt_money, polarity=+1),
    _Metric("Invest buys", "📈",
            lambda m: m.money.invest.buys_total,
            _fmt_money, polarity=0),
    _Metric("Sleep avg", "😴",
            lambda m: m.sleep.avg_hours,
            lambda v: f"{v:g}h", polarity=+1),
    _Metric("Steps total", "👟",
            lambda m: float(m.steps.total),
            _fmt_int, polarity=+1),
    _Metric("Workouts", "🏋️",
            lambda m: float(m.workouts.sessions),
            lambda v: f"{int(v)}", polarity=+1),
    _Metric("Caffeine mg", "☕",
            lambda m: float(m.caffeine.total_mg),
            lambda v: f"{int(v)} mg", polarity=-1),
    _Metric("Fasts completed", "🕒",
            lambda m: float(m.fasting.completed),
            lambda v: f"{int(v)}", polarity=+1),
    _Metric("Meditate min", "🧘",
            lambda m: float(m.meditate.total_minutes),
            _fmt_minutes, polarity=+1),
    _Metric("Mileage km", "🏃",
            lambda m: m.mileage.total_km,
            lambda v: f"{v:g} km", polarity=+1),
    _Metric("Mood avg", "🙂",
            lambda m: m.mood.avg_score,
            lambda v: f"{v:g}/5", polarity=+1),
    _Metric("Focus min", "🍅",
            lambda m: float(m.productivity.focus.total_minutes),
            _fmt_minutes, polarity=+1),
    _Metric("Tasks completed", "✅",
            lambda m: float(m.productivity.tasks_completed),
            lambda v: f"{int(v)}", polarity=+1),
    _Metric("Journal entries", "📔",
            lambda m: float(m.productivity.journal_entries),
            lambda v: f"{int(v)}", polarity=+1),
    _Metric("Gratitude entries", "🙏",
            lambda m: float(m.productivity.gratitude_entries),
            lambda v: f"{int(v)}", polarity=+1),
    _Metric("Books finished", "📚",
            lambda m: float(len(m.hobbies.books_finished)),
            lambda v: f"{int(v)}", polarity=+1),
]


def _prior_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def compare_months(
    year: int | None = None, month: int | None = None,
) -> tuple[MonthSnapshot, MonthSnapshot, list[CompareRow]]:
    """Compare a calendar month against the month before it.

    Defaults to the current month vs the previous month. Pass ``year`` /
    ``month`` to compare any past month against its predecessor.
    """
    today = date.today()
    cur_year = year or today.year
    cur_month = month or today.month
    prior_year, prior_month_num = _prior_month(cur_year, cur_month)
    current = collect_month(cur_year, cur_month)
    prior = collect_month(prior_year, prior_month_num)
    rows: list[CompareRow] = []
    for metric in MONTH_METRICS:
        cur = metric.extract(current)
        pri = metric.extract(prior)
        cur_str = metric.format(cur) if cur is not None else "—"
        pri_str = metric.format(pri) if pri is not None else "—"
        delta = (cur - pri) if (cur is not None and pri is not None) else None
        delta_pct = None
        if delta is not None and pri:
            delta_pct = round(100 * delta / pri, 1)
        rows.append(CompareRow(
            label=metric.label,
            emoji=metric.emoji,
            current=cur,
            prior=pri,
            current_display=cur_str,
            prior_display=pri_str,
            delta=delta,
            delta_pct=delta_pct,
            direction=_direction(cur, pri, metric.polarity),
        ))
    return current, prior, rows


def _render_rows_table(prior_label: str, current_label: str,
                       rows: list[CompareRow]) -> None:
    """Shared rendering for week- and month-compare."""
    from clibo.core.output import console
    console.print(
        f"\n⚖️  [bold]Comparison[/bold]   "
        f"[dim]{prior_label}  vs  {current_label}[/dim]\n"
    )
    visible = [
        r for r in rows
        if not (r.current in (None, 0, 0.0) and r.prior in (None, 0, 0.0))
    ]
    if not visible:
        console.print("  [dim]Nothing logged in either window.[/dim]\n")
        return
    for r in visible:
        if r.delta is None or r.delta == 0:
            arrow = "·"
        elif r.delta > 0:
            arrow = "↑"
        else:
            arrow = "↓"
        if r.direction == "better":
            arrow_colour = "green"
        elif r.direction == "worse":
            arrow_colour = "red"
        else:
            arrow_colour = "dim"
        if r.delta_pct is not None and r.delta is not None and r.delta != 0:
            delta_str = (f"[{arrow_colour}]{arrow} "
                         f"{abs(r.delta_pct):g}%[/{arrow_colour}]")
        elif r.delta is not None and r.delta != 0:
            delta_str = (f"[{arrow_colour}]{arrow} "
                         f"{abs(r.delta):g}[/{arrow_colour}]")
        else:
            delta_str = "[dim]·[/dim]"
        label = f"{r.emoji} {r.label}"
        console.print(
            f"  {label:<22}  [dim]{r.prior_display:>12}[/dim]   →   "
            f"[bold]{r.current_display:<12}[/bold]   {delta_str}"
        )
    console.print()


def render_compare(json_out: bool, current_start: date | None = None) -> None:
    """Render the side-by-side week comparison to stdout."""
    from clibo.core.output import _emit_json, console

    current, prior, rows = compare_weeks(current_start=current_start)
    if json_out:
        _emit_json({
            "current": {"start": current.start, "end": current.end},
            "prior": {"start": prior.start, "end": prior.end},
            "rows": [
                {
                    "label": r.label,
                    "emoji": r.emoji,
                    "current": r.current,
                    "prior": r.prior,
                    "current_display": r.current_display,
                    "prior_display": r.prior_display,
                    "delta": r.delta,
                    "delta_pct": r.delta_pct,
                    "direction": r.direction,
                }
                for r in rows
            ],
        })
        return
    console.print(
        f"\n⚖️  [bold]Week-over-week comparison[/bold]   "
        f"[dim]({prior.start:%a %d %b} → {prior.end:%a %d %b})  vs  "
        f"({current.start:%a %d %b} → {current.end:%a %d %b})[/dim]\n"
    )
    # Skip rows where both sides are empty (no data at all this period).
    visible = [
        r for r in rows
        if not (r.current in (None, 0, 0.0) and r.prior in (None, 0, 0.0))
    ]
    if not visible:
        console.print("  [dim]Nothing logged in either window.[/dim]\n")
        return
    for r in visible:
        # Arrow reflects the actual numeric direction (↑ = went up, ↓ = went
        # down); colour encodes whether that direction is good or bad.
        if r.delta is None or r.delta == 0:
            arrow = "·"
        elif r.delta > 0:
            arrow = "↑"
        else:
            arrow = "↓"
        if r.direction == "better":
            arrow_colour = "green"
        elif r.direction == "worse":
            arrow_colour = "red"
        else:
            arrow_colour = "dim"
        if r.delta_pct is not None and r.delta is not None and r.delta != 0:
            delta_str = (f"[{arrow_colour}]{arrow} "
                         f"{abs(r.delta_pct):g}%[/{arrow_colour}]")
        elif r.delta is not None and r.delta != 0:
            delta_str = (f"[{arrow_colour}]{arrow} "
                         f"{abs(r.delta):g}[/{arrow_colour}]")
        else:
            delta_str = "[dim]·[/dim]"
        label = f"{r.emoji} {r.label}"
        console.print(
            f"  {label:<22}  [dim]{r.prior_display:>12}[/dim]   →   "
            f"[bold]{r.current_display:<12}[/bold]   {delta_str}"
        )
    console.print()


def render_compare_months(
    json_out: bool,
    year: int | None = None,
    month: int | None = None,
) -> None:
    """Render the side-by-side month-over-month comparison."""
    from clibo.core.output import _emit_json
    current, prior, rows = compare_months(year=year, month=month)
    if json_out:
        _emit_json({
            "current": {
                "year": current.year, "month": current.month,
                "month_name": current.month_name,
            },
            "prior": {
                "year": prior.year, "month": prior.month,
                "month_name": prior.month_name,
            },
            "rows": [
                {
                    "label": r.label, "emoji": r.emoji,
                    "current": r.current, "prior": r.prior,
                    "current_display": r.current_display,
                    "prior_display": r.prior_display,
                    "delta": r.delta, "delta_pct": r.delta_pct,
                    "direction": r.direction,
                }
                for r in rows
            ],
        })
        return
    _render_rows_table(
        prior_label=prior.month_name,
        current_label=current.month_name,
        rows=rows,
    )
