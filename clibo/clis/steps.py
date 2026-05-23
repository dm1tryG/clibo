"""👟 steps — daily step-count tracker (pedometer / fitness-tracker sync).

Distinct from `workout` (deliberate exercise sessions), `mileage` (explicit
cardio activities like running or cycling), and `stretches` (mobility work).
This is the *passive* daily total — what your Apple Watch / Fitbit / phone
counts as you go about your day. Each log event records one chunk of steps
and may carry a `source` tag so morning syncs and manual additions add up
correctly without double-counting.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, console, fail, ok, render_record, render_rows
from clibo.core.settings import get_setting, set_setting

NAME = "steps"
HELP = "👟 Daily step-count tracker"
EMOJI = "👟"
DEFAULT_DAILY_GOAL = 10_000


class StepEntry(SQLModel, table=True):
    """One step-count log event — sums up to a per-day total at query time."""

    __tablename__ = "step_entry"

    id: int | None = Field(default=None, primary_key=True)
    count: int
    entry_date: date = Field(default_factory=date.today, index=True)
    source: str | None = None  # e.g. "apple_watch", "fitbit", "phone", "manual"
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=True, help=HELP)


def _goal() -> int:
    return int(get_setting(NAME, "daily_goal",
                           str(DEFAULT_DAILY_GOAL)) or DEFAULT_DAILY_GOAL)


def _row(entry: StepEntry) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "count": entry.count,
        "source": entry.source,
        "note": entry.note,
    }


def _daily_totals(entries: list[StepEntry]) -> dict[date, int]:
    """Group a list of step entries by their date and sum the counts."""
    totals: dict[date, int] = {}
    for entry in entries:
        totals[entry.entry_date] = totals.get(entry.entry_date, 0) + entry.count
    return totals


def _streak(totals: dict[date, int], goal: int) -> int:
    """Consecutive days, ending today or yesterday, hitting the goal.

    A missed day breaks the streak. Today counts even if the goal isn't yet
    reached, *but only* if at least one earlier day in the streak hit the
    goal — otherwise we look back from yesterday.
    """
    today = date.today()
    # Start from the most recent goal-hit day and walk backwards.
    cursor = today
    if totals.get(today, 0) < goal:
        cursor = today - timedelta(days=1)
    streak = 0
    while totals.get(cursor, 0) >= goal:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


@app.command()
def log(
    count: int = typer.Argument(..., help="Number of steps in this log event"),
    source: str = typer.Option(None, "--source", "-s",
                                help="Where the count came from "
                                     "(e.g. apple_watch, fitbit, phone, manual)"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """👟 Log a step count for a day (multiple events per day are summed)."""
    if count <= 0:
        fail("Step count must be positive", json_out=json_out)
    entry = StepEntry(
        count=count,
        entry_date=parse_date(on),
        source=source.lower().strip() if source else None,
        note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        # Recompute today's running total.
        total = sum(
            e.count for e in db.exec(
                select(StepEntry).where(StepEntry.entry_date == entry.entry_date)
            ).all()
        )
    goal = _goal()
    src_str = f" ({source})" if source else ""
    ok(
        f"Logged {EMOJI} {count:,} steps{src_str} — {total:,}/{goal:,} today",
        json_out=json_out,
        data={**_row(entry), "total_today": total, "goal": goal},
    )


# `add` is a friendlier alias for `log` (predictable verbs across tools).
app.command(name="add", help="Alias for `log`")(log)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """👟 Today's step count and goal progress."""
    day = date.today()
    with session() as db:
        entries = list(
            db.exec(select(StepEntry).where(StepEntry.entry_date == day)).all()
        )
    total = sum(e.count for e in entries)
    goal = _goal()
    sources = Counter(e.source for e in entries if e.source)
    if json_out:
        render_record(
            {
                "date": day,
                "total": total,
                "goal": goal,
                "reached": total >= goal,
                "entries": len(entries),
                "sources": dict(sources),
            },
            json_out=True,
        )
        return
    console.print(f"\n{EMOJI} [bold]Steps today[/bold] · {day:%a %d %b}\n")
    console.print(f"  {bar(total, goal)}")
    console.print(
        f"  [bold cyan]{total:,}[/bold cyan] / {goal:,} steps   ·   "
        f"{len(entries)} entries"
    )
    if sources:
        breakdown = "   ·   ".join(f"{src}: {n}" for src, n in sources.items())
        console.print(f"  [dim]{breakdown}[/dim]")
    if total >= goal:
        console.print("  [green]✓ goal reached[/green]\n")
    else:
        console.print(f"  [yellow]{goal - total:,} steps to go[/yellow]\n")


@app.command(name="list")
def list_entries(
    days: int = typer.Option(14, "--days", help="Look back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """👟 Daily step totals for the last N days."""
    since = date.today() - timedelta(days=days - 1)
    goal = _goal()
    with session() as db:
        entries = list(
            db.exec(select(StepEntry).where(StepEntry.entry_date >= since)).all()
        )
    totals = _daily_totals(entries)
    rows = [
        {"date": d, "total": n, "goal": goal, "reached": n >= goal}
        for d, n in sorted(totals.items(), reverse=True)
    ]
    render_rows(
        rows,
        [("date", "Date"), ("total", "Steps"), ("reached", "Goal?")],
        json_out=json_out,
        title=f"{EMOJI} Step totals — last {days}d",
        empty="No steps logged yet — try: clibo steps log 8500 -s phone",
        formatters={"total": lambda v, r: f"{v:,}"},
    )


@app.command()
def week(json_out: JsonOpt = False) -> None:
    """🗓️ This week's daily steps vs the goal — with a streak count."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    goal = _goal()
    # Pull a 60-day window so we can compute a streak that may extend before
    # this week (without scanning the entire table).
    since = today - timedelta(days=60)
    with session() as db:
        entries = list(
            db.exec(select(StepEntry).where(StepEntry.entry_date >= since)).all()
        )
    all_totals = _daily_totals(entries)
    week_totals = {d: n for d, n in all_totals.items() if d >= monday}
    streak = _streak(all_totals, goal)
    week_total = sum(week_totals.values())
    week_hits = sum(1 for n in week_totals.values() if n >= goal)
    if json_out:
        render_record(
            {
                "week_start": monday,
                "total": week_total,
                "goal_per_day": goal,
                "days_logged": len(week_totals),
                "goal_hits": week_hits,
                "streak": streak,
                "by_day": {str(d): n for d, n in sorted(week_totals.items())},
            },
            json_out=True,
        )
        return
    console.print(
        f"\n{EMOJI} [bold]This week[/bold]   from [dim]{monday:%a %d %b}[/dim]\n"
    )
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, name in enumerate(weekday_names):
        day = monday + timedelta(days=i)
        n = week_totals.get(day, 0)
        marker = "[green]✓[/green]" if n >= goal else " "
        console.print(f"  {name}  {bar(n, goal)}  [bold]{n:>6,}[/bold]  {marker}")
    console.print(
        f"\n  [bold]{week_total:,}[/bold] this week   ·   "
        f"{week_hits}/{len(week_totals)} days on target"
    )
    if streak:
        console.print(f"  🔥 [bold]{streak}-day[/bold] streak\n")
    else:
        console.print()


@app.command()
def show(entry_id: int = typer.Argument(..., help="Entry ID"),
         json_out: JsonOpt = False) -> None:
    """👟 Show one step-log entry."""
    with session() as db:
        entry = db.get(StepEntry, entry_id)
        if not entry:
            fail(f"No step entry #{entry_id}", json_out=json_out)
        data = _row(entry)
    render_record(data, json_out=json_out, title=f"{EMOJI} Step entry #{entry_id}")


@app.command()
def edit(
    target: str = typer.Argument(..., help="Entry ID or 'last' for the most recent"),
    count: int = typer.Option(None, "--count", "-c", help="New step count"),
    source: str = typer.Option(None, "--source", "-s", help="New source label"),
    on: str = typer.Option(None, "--date", "-d", help="New date"),
    note: str = typer.Option(None, "--note", "-n", help="New note"),
    json_out: JsonOpt = False,
) -> None:
    """👟 Edit an existing step-log entry."""
    from clibo.core.base import resolve_id
    with session() as db:
        entry = resolve_id(target, StepEntry, db)
        if not entry:
            fail(f"No step entry matching {target!r}", json_out=json_out)
        if count is not None:
            if count <= 0:
                fail("Step count must be positive", json_out=json_out)
            entry.count = count
        if source is not None:
            entry.source = source.lower().strip() or None
        if on is not None:
            entry.entry_date = parse_date(on)
        if note is not None:
            entry.note = note
        db.add(entry)
        db.flush()
        data = _row(entry)
    ok(f"Updated step entry #{entry.id} — {entry.count:,}",
       json_out=json_out, data=data)


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Entry ID"),
       json_out: JsonOpt = False) -> None:
    """👟 Delete a step-log entry."""
    with session() as db:
        entry = db.get(StepEntry, entry_id)
        if not entry:
            fail(f"No step entry #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted step entry #{entry_id}",
       json_out=json_out, data={"deleted": entry_id})


@app.command()
def goal(
    set_count: int = typer.Option(None, "--set",
                                   help="Set the daily step goal"),
    json_out: JsonOpt = False,
) -> None:
    """🎯 Show or set your daily step goal."""
    if set_count is not None:
        if set_count <= 0:
            fail("Goal must be positive", json_out=json_out)
        set_setting(NAME, "daily_goal", str(set_count))
        ok(f"Daily step goal set to {set_count:,}",
           json_out=json_out, data={"daily_goal": set_count})
        return
    render_record({"daily_goal": _goal()}, json_out=json_out,
                  title="🎯 Daily step goal")


@app.command()
def stats(
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Step stats — total, daily avg, goal-hit rate, longest streak."""
    since = date.today() - timedelta(days=days - 1)
    goal = _goal()
    with session() as db:
        entries = list(
            db.exec(select(StepEntry).where(StepEntry.entry_date >= since)).all()
        )
    if not entries:
        fail("No steps in this window", json_out=json_out)
    totals = _daily_totals(entries)
    total_steps = sum(totals.values())
    days_logged = len(totals)
    goal_hits = sum(1 for n in totals.values() if n >= goal)
    best_day, best_count = max(totals.items(), key=lambda kv: kv[1])
    # longest streak in the window (any consecutive run of goal hits)
    days_sorted = sorted(totals)
    longest = current = 0
    prev_day = None
    for d in days_sorted:
        if totals[d] >= goal:
            if prev_day is not None and (d - prev_day).days == 1:
                current += 1
            else:
                current = 1
            longest = max(longest, current)
            prev_day = d
        else:
            current = 0
            prev_day = None
    data = {
        "window_days": days,
        "days_logged": days_logged,
        "total_steps": total_steps,
        "avg_per_logged_day": round(total_steps / days_logged) if days_logged else 0,
        "goal": goal,
        "days_goal_hit": goal_hits,
        "goal_hit_rate_pct": round(100 * goal_hits / days_logged, 1)
            if days_logged else 0.0,
        "best_day": {"date": best_day, "count": best_count},
        "current_streak": _streak(totals, goal),
        "longest_streak": longest,
    }
    render_record(data, json_out=json_out, title=f"📊 Steps · last {days}d")
