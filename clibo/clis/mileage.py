"""🏃 mileage — distance-based activity log (running, cycling, walking)."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, console, fail, ok, render_record, render_rows
from clibo.core.settings import get_setting, set_setting

NAME = "mileage"
HELP = "🏃 Distance log — running, cycling, walking"
EMOJI = "🏃"
DEFAULT_WEEKLY_KM = 20.0
ACTIVITIES = ["run", "walk", "cycle", "hike", "swim", "other"]


class MileageEntry(SQLModel, table=True):
    """One distance-based activity session."""

    __tablename__ = "mileage_entry"

    id: int | None = Field(default=None, primary_key=True)
    activity: str = "run"
    distance_km: float
    duration_min: int = 0
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo mileage`` (bare) runs the ``week`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(week, json_out=False)


def _pace(entry: MileageEntry) -> float | None:
    """Min/km pace if both fields are present and distance > 0."""
    if entry.duration_min and entry.distance_km > 0:
        return round(entry.duration_min / entry.distance_km, 2)
    return None


def _row(entry: MileageEntry) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "activity": entry.activity,
        "distance_km": entry.distance_km,
        "duration_min": entry.duration_min,
        "pace_min_per_km": _pace(entry),
        "note": entry.note,
    }


def _weekly_goal() -> float:
    return float(
        get_setting(NAME, "weekly_km", str(DEFAULT_WEEKLY_KM)) or DEFAULT_WEEKLY_KM
    )


@app.command()
def log(
    distance_km: float = typer.Argument(..., help="Distance in km"),
    activity: str = typer.Option("run", "--activity", "-a",
                                 help=f"{'/'.join(ACTIVITIES)}"),
    duration: int = typer.Option(0, "--duration", "-t",
                                  help="Duration in minutes (enables pace)"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🏃 Log a distance-based activity session."""
    if distance_km <= 0:
        fail("Distance must be positive", json_out=json_out)
    activity = activity.lower()
    if activity not in ACTIVITIES:
        fail(f"Activity must be one of: {', '.join(ACTIVITIES)}", json_out=json_out)
    entry = MileageEntry(
        activity=activity, distance_km=distance_km, duration_min=duration,
        entry_date=parse_date(on), note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    pace = (f" — {data['pace_min_per_km']:.2f} min/km"
            if data["pace_min_per_km"] else "")
    ok(f"Logged {EMOJI} {distance_km:g} km {activity}{pace}",
       json_out=json_out, data=data)


# `add` is a friendlier alias for `log` (predictable verbs across tools).
app.command(name="add", help="Alias for `log`")(log)


@app.command(name="list")
def list_entries(
    days: int = typer.Option(14, "--days", help="Look back this many days"),
    activity: str = typer.Option(None, "--activity", "-a", help="Filter by activity"),
    json_out: JsonOpt = False,
) -> None:
    """🏃 List recent mileage entries."""
    if activity and activity.lower() not in ACTIVITIES:
        fail(f"Activity must be one of: {', '.join(ACTIVITIES)}", json_out=json_out)
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(MileageEntry).where(MileageEntry.entry_date >= since)
        if activity:
            query = query.where(MileageEntry.activity == activity.lower())
        entries = list(
            db.exec(query.order_by(MileageEntry.entry_date.desc(),
                                   MileageEntry.id.desc())).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("activity", "Activity"),
         ("distance_km", "km"), ("duration_min", "Min"),
         ("pace_min_per_km", "Pace")],
        json_out=json_out,
        title="🏃 Mileage log",
        empty="No entries yet — try: clibo mileage log 5 -a run -t 30",
    )


@app.command()
def week(json_out: JsonOpt = False) -> None:
    """🗓️ This week's distance vs the weekly goal."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    with session() as db:
        entries = list(
            db.exec(select(MileageEntry).where(MileageEntry.entry_date >= monday)).all()
        )
    total = round(sum(e.distance_km for e in entries), 2)
    goal = _weekly_goal()
    by_activity: dict[str, float] = {}
    for entry in entries:
        by_activity[entry.activity] = round(
            by_activity.get(entry.activity, 0) + entry.distance_km, 2
        )
    if json_out:
        render_record(
            {
                "week_start": monday,
                "total_km": total,
                "goal_km": goal,
                "reached": total >= goal,
                "sessions": len(entries),
                "by_activity": by_activity,
            },
            json_out=True,
        )
        return
    console.print(f"\n🏃 [bold]This week[/bold]   from [dim]{monday:%a %d %b}[/dim]\n")
    console.print(f"  {bar(total, goal)}")
    console.print(
        f"  [bold cyan]{total}[/bold cyan] / {goal:g} km   ·   "
        f"{len(entries)} sessions"
    )
    if by_activity:
        breakdown = "   ·   ".join(f"{a}: {km:g}" for a, km in by_activity.items())
        console.print(f"  [dim]{breakdown}[/dim]")
    if total >= goal:
        console.print("  [green]✓ weekly goal reached[/green]\n")
    else:
        console.print(f"  [yellow]{goal - total:.1f} km to go[/yellow]\n")


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Entry ID"), json_out: JsonOpt = False) -> None:
    """🏃 Delete a mileage entry."""
    with session() as db:
        entry = db.get(MileageEntry, entry_id)
        if not entry:
            fail(f"No mileage entry #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted mileage entry #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def goal(
    set_km: float = typer.Option(None, "--set", help="Set the weekly distance goal (km)"),
    json_out: JsonOpt = False,
) -> None:
    """🎯 Show or set your weekly mileage goal."""
    if set_km is not None:
        if set_km <= 0:
            fail("Goal must be positive", json_out=json_out)
        set_setting(NAME, "weekly_km", str(set_km))
        ok(f"Weekly mileage goal set to {set_km:g} km",
           json_out=json_out, data={"weekly_km": set_km})
        return
    render_record({"weekly_km": _weekly_goal()}, json_out=json_out,
                  title="🎯 Weekly mileage goal")


def _streak(days: set[date]) -> int:
    """Current run of consecutive days with any mileage entry.

    Today counts if logged; if not, we anchor at yesterday so the
    streak doesn't reset just because today isn't done yet.
    """
    if not days:
        return 0
    cursor = date.today()
    if cursor not in days:
        cursor -= timedelta(days=1)
    if cursor not in days:
        return 0
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _longest_streak(days: set[date]) -> int:
    """Longest run of consecutive days in history."""
    if not days:
        return 0
    ordered = sorted(days)
    longest = run = 1
    for i in range(1, len(ordered)):
        run = run + 1 if (ordered[i] - ordered[i - 1]).days == 1 else 1
        longest = max(longest, run)
    return longest


@app.command()
def streak(json_out: JsonOpt = False) -> None:
    """🔥 Show the current + longest mileage streak (any activity counts)."""
    with session() as db:
        days = {e.entry_date for e in db.exec(select(MileageEntry)).all()}
    current = _streak(days)
    longest = _longest_streak(days)
    data = {
        "current_streak": current,
        "longest_streak": longest,
        "days_logged": len(days),
    }
    if json_out:
        render_record(data, json_out=True)
        return
    flame = "🔥" * min(current, 10) if current else "[dim]—[/dim]"
    console.print(
        f"\n  🏃 Mileage streak: [bold cyan]{current}[/bold cyan] days  "
        f"{flame}   [dim](longest ever: {longest})[/dim]\n"
    )


@app.command()
def stats(
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Mileage stats over the last N days."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(select(MileageEntry).where(MileageEntry.entry_date >= since)).all()
        )
    if not entries:
        fail("No mileage in this window", json_out=json_out)
    total_km = round(sum(e.distance_km for e in entries), 2)
    total_min = sum(e.duration_min for e in entries)
    longest = max(entries, key=lambda e: e.distance_km)
    paces = [p for e in entries if (p := _pace(e)) is not None]
    by_activity: dict[str, float] = {}
    for entry in entries:
        by_activity[entry.activity] = round(
            by_activity.get(entry.activity, 0) + entry.distance_km, 2
        )
    data = {
        "window_days": days,
        "sessions": len(entries),
        "total_km": total_km,
        "total_minutes": total_min,
        "longest_km": longest.distance_km,
        "avg_pace_min_per_km": round(sum(paces) / len(paces), 2) if paces else None,
        "by_activity": by_activity,
    }
    render_record(data, json_out=json_out, title=f"📊 Mileage stats · last {days}d")
