"""🧎 stretches — mobility & flexibility session log.

Distinct from `workout` (strength), `mileage` (cardio distance) and
`meditate` (mindfulness). Captures stretching/mobility sessions with
body area, duration, optional poses and an optional difficulty rating
so recurring problem areas are visible at a glance.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date, parse_minutes
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "stretches"
HELP = "🧎 Mobility & flexibility session log"
EMOJI = "🧎"

# Loose vocabulary — anything is fine, these are just the suggested set
# surfaced in --help and the empty-list hint.
AREAS = [
    "hamstrings", "quads", "hips", "back", "lower-back", "shoulders",
    "neck", "chest", "calves", "ankles", "wrists", "full-body",
]


class StretchSession(SQLModel, table=True):
    """One mobility session — area, time, optional pose list."""

    __tablename__ = "stretch_session"

    id: int | None = Field(default=None, primary_key=True)
    area: str = "full-body"
    duration_min: int = 0
    poses: str | None = None     # comma-separated free-text labels
    difficulty: int | None = None  # 1 (easy) – 5 (deep / painful)
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo stretches`` (bare) runs the ``today`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(today, json_out=json_out)


def _row(entry: StretchSession) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "area": entry.area,
        "duration_min": entry.duration_min,
        "poses": entry.poses,
        "difficulty": entry.difficulty,
        "note": entry.note,
    }


@app.command()
def log(
    area: str = typer.Argument("full-body", help=f"Body area, e.g. {', '.join(AREAS[:4])}, …"),
    minutes: str = typer.Option(
        "10", "--minutes", "-m",
        help="Duration — minutes ('10') or H:MM ('0:15')",
    ),
    poses: str = typer.Option(None, "--poses", "-p",
                              help="Comma-separated poses (e.g. 'pigeon, downward-dog')"),
    difficulty: int = typer.Option(None, "--difficulty", "-D",
                                    help="How deep / hard it felt, 1-5"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🧎 Log a stretching / mobility session."""
    parsed_min = parse_minutes(minutes)
    if parsed_min <= 0:
        fail("Minutes must be positive", json_out=json_out)
    if difficulty is not None and difficulty not in range(1, 6):
        fail("Difficulty must be 1-5", json_out=json_out)
    entry = StretchSession(
        area=area.lower().strip(),
        duration_min=parsed_min,
        poses=poses.strip() if poses else None,
        difficulty=difficulty,
        entry_date=parse_date(on),
        note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    diff_str = f" · D{difficulty}" if difficulty else ""
    ok(f"Logged {EMOJI} {parsed_min} min — {entry.area}{diff_str}",
       json_out=json_out, data=data)


# `add` is a friendlier alias for `log` (predictable verbs across tools).
app.command(name="add", help="Alias for `log`")(log)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """🧎 Today's stretching sessions."""
    day = date.today()
    with session() as db:
        entries = list(
            db.exec(select(StretchSession).where(StretchSession.entry_date == day)).all()
        )
    total = sum(e.duration_min for e in entries)
    if json_out:
        render_record(
            {"date": day, "sessions": len(entries), "total_minutes": total,
             "entries": [_row(e) for e in entries]},
            json_out=True,
        )
        return
    if not entries:
        console.print(f"\n{EMOJI} [dim]No stretches logged today.[/dim]\n")
        return
    console.print(f"\n{EMOJI} [bold]Stretches today[/bold] · {day:%a %d %b}\n")
    for entry in entries:
        diff = f" · D{entry.difficulty}" if entry.difficulty else ""
        poses = f"\n     [dim]{entry.poses}[/dim]" if entry.poses else ""
        console.print(f"  • [cyan]{entry.area}[/cyan] — {entry.duration_min} min{diff}{poses}")
    console.print(f"\n  [bold]{total}[/bold] min total\n")


@app.command(name="list")
def list_entries(
    days: int = typer.Option(14, "--days", help="Look back this many days"),
    area: str = typer.Option(None, "--area", "-a", help="Filter by body area"),
    json_out: JsonOpt = False,
) -> None:
    """🧎 List recent stretching sessions."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(StretchSession).where(StretchSession.entry_date >= since)
        if area:
            query = query.where(StretchSession.area == area.lower().strip())
        entries = list(
            db.exec(query.order_by(StretchSession.entry_date.desc(),
                                   StretchSession.id.desc())).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("area", "Area"),
         ("duration_min", "Min"), ("difficulty", "D"), ("poses", "Poses")],
        json_out=json_out,
        title=f"{EMOJI} Stretches — last {days}d",
        empty="No sessions yet — try: clibo stretches log hamstrings -m 10",
    )


@app.command()
def show(entry_id: int = typer.Argument(..., help="Session ID"), json_out: JsonOpt = False) -> None:
    """🧎 Show one stretching session."""
    with session() as db:
        entry = db.get(StretchSession, entry_id)
        if not entry:
            fail(f"No stretch session #{entry_id}", json_out=json_out)
        data = _row(entry)
    render_record(data, json_out=json_out, title=f"{EMOJI} Stretch session #{entry_id}")


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Session ID"), json_out: JsonOpt = False) -> None:
    """🧎 Delete a stretching session."""
    with session() as db:
        entry = db.get(StretchSession, entry_id)
        if not entry:
            fail(f"No stretch session #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted stretch session #{entry_id}",
       json_out=json_out, data={"deleted": entry_id})


@app.command()
def areas(
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """🧎 Frequency of each body area — find the ones you neglect."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(select(StretchSession).where(StretchSession.entry_date >= since)).all()
        )
    counts = Counter(e.area for e in entries)
    minutes_by_area: dict[str, int] = {}
    for entry in entries:
        minutes_by_area[entry.area] = minutes_by_area.get(entry.area, 0) + entry.duration_min
    rows = [
        {"area": area, "sessions": n, "total_minutes": minutes_by_area[area]}
        for area, n in counts.most_common()
    ]
    render_rows(
        rows,
        [("area", "Area"), ("sessions", "Sessions"), ("total_minutes", "Min")],
        json_out=json_out,
        title=f"🧎 Area breakdown · last {days}d",
        empty="No sessions logged in this window.",
    )


def _streak(days: set[date]) -> int:
    """Current run of consecutive days with any stretching session."""
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
    """Longest consecutive-day stretching run in history."""
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
    """🔥 Show the current + longest stretching streak."""
    with session() as db:
        days = {e.entry_date for e in db.exec(select(StretchSession)).all()}
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
        f"\n  🧎 Stretching streak: [bold cyan]{current}[/bold cyan] days  "
        f"{flame}   [dim](longest ever: {longest})[/dim]\n"
    )


@app.command()
def stats(
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Stretching stats over the last N days."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(select(StretchSession).where(StretchSession.entry_date >= since)).all()
        )
    if not entries:
        fail("No stretches in this window", json_out=json_out)
    minutes_by_area: dict[str, int] = {}
    for entry in entries:
        minutes_by_area[entry.area] = minutes_by_area.get(entry.area, 0) + entry.duration_min
    difficulties = [e.difficulty for e in entries if e.difficulty is not None]
    days_logged = len({e.entry_date for e in entries})
    top_area = max(minutes_by_area.items(), key=lambda kv: kv[1])[0]
    # Longest single session — *"what's my longest stretch ever?"*. Same
    # shape as best_session in writing/focus/mileage.
    longest = max(entries, key=lambda e: e.duration_min)
    data = {
        "window_days": days,
        "sessions": len(entries),
        "days_logged": days_logged,
        "total_minutes": sum(e.duration_min for e in entries),
        "avg_minutes_per_session": round(
            sum(e.duration_min for e in entries) / len(entries), 1
        ),
        "avg_difficulty": (
            round(sum(difficulties) / len(difficulties), 2) if difficulties else None
        ),
        "top_area": top_area,
        "by_area_minutes": minutes_by_area,
        "longest_session": {
            "id": longest.id,
            "entry_date": longest.entry_date,
            "area": longest.area,
            "minutes": longest.duration_min,
            "difficulty": longest.difficulty,
        },
    }
    render_record(data, json_out=json_out, title=f"📊 Stretching · last {days}d")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
