"""✍️ writing — daily word-count tracker for writers."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import (
    JsonOpt,
    bar,
    console,
    fail,
    ok,
    render_record,
    render_rows,
)
from clibo.core.settings import get_setting, set_setting

NAME = "writing"
HELP = "✍️ Daily word-count tracker (novel, blog, essays)"
EMOJI = "✍️"

DEFAULT_GOAL = 500  # words per day (gentle baseline; NaNoWriMo is 1,667)


class WritingSession(SQLModel, table=True):
    """One writing session — N words on a named project on a given day.

    Writers track *words*, not minutes — minute-based tools (focus, time)
    lose the metric that matters most. Optional ``duration_min`` lets you
    compute pace (words / minute) but isn't required.
    """

    __tablename__ = "writing_session"

    id: int | None = Field(default=None, primary_key=True)
    project: str = "main"
    words: int
    duration_min: int = 0
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo writing`` (bare) runs the ``today`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(today, json_out=json_out)


def _goal() -> int:
    """Daily word goal (settings · ``writing.daily_words``)."""
    return int(get_setting(NAME, "daily_words", str(DEFAULT_GOAL)) or DEFAULT_GOAL)


def _resolve(db, ident: str) -> WritingSession | None:
    """Resolve a CLI arg to a session by ID or project name (most-recent wins)."""
    from clibo.core.base import lookup_by_id_or_name
    if ident.isdigit():
        entry = db.get(WritingSession, int(ident))
        if entry:
            return entry
    return db.exec(
        select(WritingSession)
        .where(WritingSession.project.ilike(f"%{ident}%"))
        .order_by(WritingSession.id.desc())
    ).first() or lookup_by_id_or_name(
        db, WritingSession, ident, WritingSession.project
    )


def _row(entry: WritingSession) -> dict:
    pace = (
        round(entry.words / entry.duration_min, 1) if entry.duration_min else None
    )
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "project": entry.project,
        "words": entry.words,
        "duration_min": entry.duration_min,
        "wpm": pace,
        "note": entry.note,
    }


def _streak(days: set[date]) -> int:
    """Current run of consecutive days with any writing logged."""
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
    if not days:
        return 0
    ordered = sorted(days)
    longest = run = 1
    for i in range(1, len(ordered)):
        run = run + 1 if (ordered[i] - ordered[i - 1]).days == 1 else 1
        longest = max(longest, run)
    return longest


@app.command()
def log(
    project: str = typer.Argument("main", help="Project name (e.g. 'novel', 'blog')"),
    words: int = typer.Option(..., "--words", "-w", help="Words written this session"),
    duration_min: int = typer.Option(
        0, "--duration", "-t", help="Minutes spent (enables wpm pace)"
    ),
    on: str = typer.Option("today", "--date", "-d", help="Date written"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """✍️ Log a writing session — words written on a project."""
    if words < 0:
        fail("Words cannot be negative", json_out=json_out)
    if duration_min < 0:
        fail("Duration cannot be negative", json_out=json_out)
    entry = WritingSession(
        project=project.strip(),
        words=words,
        duration_min=duration_min,
        entry_date=parse_date(on),
        note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        # Today's total + streak for the flash message
        today_total = sum(
            e.words for e in db.exec(
                select(WritingSession).where(
                    WritingSession.entry_date == entry.entry_date
                )
            ).all()
        )
        days = {e.entry_date for e in db.exec(select(WritingSession)).all()}
        data = _row(entry) | {
            "total_today": today_total,
            "goal_words": _goal(),
            "current_streak": _streak(days),
        }
    streak = data["current_streak"]
    flair = f" — 🔥 {streak}-day streak" if streak > 1 else ""
    progress = f"{today_total}/{_goal()}w today"
    ok(f"Logged {EMOJI} {words}w on {project} · {progress}{flair}",
       json_out=json_out, data=data)


# `add` is the friendlier verb in agent flows.
app.command(name="add", help="Alias for `log`")(log)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """✍️ Today's writing — words by project, goal progress."""
    day = date.today()
    with session() as db:
        entries = list(
            db.exec(
                select(WritingSession)
                .where(WritingSession.entry_date == day)
                .order_by(WritingSession.created_at)
            ).all()
        )
        all_days = {e.entry_date for e in db.exec(select(WritingSession)).all()}
    total = sum(e.words for e in entries)
    goal = _goal()
    by_project: dict[str, int] = {}
    for entry in entries:
        by_project[entry.project] = by_project.get(entry.project, 0) + entry.words
    by_project_rows = [
        {"project": p, "words": w}
        for p, w in sorted(by_project.items(), key=lambda kv: -kv[1])
    ]
    streak = _streak(all_days)
    if json_out:
        render_record(
            {
                "date": day,
                "total_words": total,
                "goal_words": goal,
                "reached": total >= goal,
                "sessions": len(entries),
                "by_project": by_project_rows,
                "current_streak": streak,
            },
            json_out=True,
        )
        return
    flame = "🔥" * min(streak, 7) if streak else "[dim]—[/dim]"
    console.print(
        f"\n✍️ [bold]Today[/bold] · {day:%a %d %b}   "
        f"streak [cyan]{streak}[/cyan]  {flame}\n"
    )
    console.print(f"  {bar(total, goal)}")
    suffix = " 🎉 goal hit!" if total >= goal else f"   {max(0, goal - total)}w to go"
    console.print(
        f"  [bold cyan]{total}[/bold cyan] / {goal} words   ·   "
        f"{len(entries)} session(s){suffix}\n"
    )
    if by_project_rows:
        for row in by_project_rows:
            console.print(f"  · [bold]{row['project']}[/bold]   {row['words']}w")
        console.print()


@app.command(name="list")
def list_entries(
    days: int = typer.Option(14, "--days", help="Look back this many days"),
    project: str = typer.Option(
        None, "--project", "-p", help="Filter by project (fuzzy)"
    ),
    json_out: JsonOpt = False,
) -> None:
    """✍️ Recent writing sessions."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(WritingSession).where(WritingSession.entry_date >= since)
        if project:
            query = query.where(WritingSession.project.ilike(f"%{project}%"))
        entries = list(
            db.exec(
                query.order_by(
                    WritingSession.entry_date.desc(), WritingSession.id.desc()
                )
            ).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("project", "Project"),
         ("words", "Words"), ("duration_min", "Min"), ("wpm", "wpm")],
        json_out=json_out,
        title="✍️ Writing log",
        formatters={
            "wpm": lambda v, r: f"{v}" if v else "[dim]—[/dim]",
            "duration_min": lambda v, r: f"{v}" if v else "[dim]—[/dim]",
        },
        empty="Nothing logged yet — try: clibo writing log novel -w 500",
    )


@app.command()
def show(
    entry: str = typer.Argument(..., help="Entry ID or project name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """✍️ Show one writing session. Accepts an ID or a project name."""
    with session() as db:
        target = _resolve(db, entry)
        if not target:
            fail(f"No writing session matching {entry!r}", json_out=json_out)
        data = _row(target) | {"created_at": target.created_at}
    render_record(data, json_out=json_out, title=f"✍️ Session #{target.id}")


@app.command()
def edit(
    entry: str = typer.Argument(..., help="Entry ID or project name (fuzzy)"),
    project: str = typer.Option(None, "--project", "-p", help="Rename project"),
    words: int = typer.Option(None, "--words", "-w"),
    duration_min: int = typer.Option(None, "--duration", "-t"),
    on: str = typer.Option(None, "--date", "-d"),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """✍️ Edit a writing session."""
    with session() as db:
        target = _resolve(db, entry)
        if not target:
            fail(f"No writing session matching {entry!r}", json_out=json_out)
        if project is not None:
            target.project = project.strip()
        if words is not None:
            if words < 0:
                fail("Words cannot be negative", json_out=json_out)
            target.words = words
        if duration_min is not None:
            if duration_min < 0:
                fail("Duration cannot be negative", json_out=json_out)
            target.duration_min = duration_min
        if on is not None:
            target.entry_date = parse_date(on)
        if note is not None:
            target.note = note
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Updated writing session #{target.id}", json_out=json_out, data=data)


@app.command()
def rm(
    entry: str = typer.Argument(..., help="Entry ID or project name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """✍️ Delete a writing session."""
    with session() as db:
        target = _resolve(db, entry)
        if not target:
            fail(f"No writing session matching {entry!r}", json_out=json_out)
        eid = target.id
        db.delete(target)
    ok(f"Deleted writing session #{eid}", json_out=json_out, data={"deleted": eid})


@app.command()
def goal(
    words: int = typer.Argument(None, help="Set the daily word goal"),
    json_out: JsonOpt = False,
) -> None:
    """🎯 Show or set the daily word goal (stored in clibo settings)."""
    if words is not None:
        if words <= 0:
            fail("Goal must be positive", json_out=json_out)
        set_setting(NAME, "daily_words", str(words))
        ok(f"Daily word goal set to {words}w",
           json_out=json_out, data={"daily_words": words})
        return
    current = _goal()
    if json_out:
        render_record({"daily_words": current}, json_out=True)
        return
    console.print(f"\n  🎯 Daily word goal: [bold cyan]{current}[/bold cyan] words\n")


@app.command()
def streak(json_out: JsonOpt = False) -> None:
    """🔥 Show the current and longest writing streaks."""
    with session() as db:
        days = {e.entry_date for e in db.exec(select(WritingSession)).all()}
    current = _streak(days)
    longest = _longest_streak(days)
    if json_out:
        render_record(
            {"current_streak": current, "longest_streak": longest,
             "days_written": len(days)},
            json_out=True,
        )
        return
    flame = "🔥" * min(current, 10) if current else "[dim]—[/dim]"
    console.print(
        f"\n  ✍️ Writing streak: [bold cyan]{current}[/bold cyan] days  "
        f"{flame}   [dim](longest ever: {longest})[/dim]\n"
    )


@app.command()
def stats(
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Writing stats — totals, avg/day, top projects, streaks."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(
                select(WritingSession).where(WritingSession.entry_date >= since)
            ).all()
        )
        all_days = {e.entry_date for e in db.exec(select(WritingSession)).all()}
    days_written = {e.entry_date for e in entries}
    total_words = sum(e.words for e in entries)
    total_minutes = sum(e.duration_min for e in entries)
    by_project: dict[str, int] = {}
    daily: dict[date, int] = {}
    for entry in entries:
        by_project[entry.project] = by_project.get(entry.project, 0) + entry.words
        daily[entry.entry_date] = daily.get(entry.entry_date, 0) + entry.words
    top_projects = sorted(by_project.items(), key=lambda kv: kv[1], reverse=True)[:5]
    best_day = max(daily.items(), key=lambda kv: kv[1]) if daily else None
    data = {
        "window_days": days,
        "sessions": len(entries),
        "total_words": total_words,
        "total_minutes": total_minutes,
        "avg_wpm": (
            round(total_words / total_minutes, 1) if total_minutes else None
        ),
        "days_written": len(days_written),
        "avg_words_per_active_day": (
            round(total_words / len(days_written), 1) if days_written else 0.0
        ),
        "best_day": (
            {"date": best_day[0], "words": best_day[1]} if best_day else None
        ),
        "top_projects": [
            {"project": p, "words": w} for p, w in top_projects
        ],
        "current_streak": _streak(all_days),
        "longest_streak": _longest_streak(all_days),
        "goal_words": _goal(),
    }
    render_record(data, json_out=json_out, title=f"📊 Writing stats · last {days}d")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `update` is the SQL-natural synonym for `edit`; both work.
app.command(name="update", help="Alias for `edit`")(edit)

# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
