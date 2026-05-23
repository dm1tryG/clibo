"""🙏 gratitude — daily gratitude practice with streaks."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "gratitude"
HELP = "🙏 Daily gratitude practice with streaks"
EMOJI = "🙏"


class GratitudeEntry(SQLModel, table=True):
    """One thing you're grateful for, dated."""

    __tablename__ = "gratitude_entry"

    id: int | None = Field(default=None, primary_key=True)
    text: str
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _streak(days: set[date]) -> int:
    """Current run of consecutive days with at least one gratitude entry."""
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


def _row(entry: GratitudeEntry) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "text": entry.text,
    }


@app.command()
def add(
    text: str = typer.Argument(..., help="What you're grateful for"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    json_out: JsonOpt = False,
) -> None:
    """🙏 Log one thing you're grateful for."""
    entry = GratitudeEntry(text=text, entry_date=parse_date(on))
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        days = {e.entry_date for e in db.exec(select(GratitudeEntry)).all()}
        data = _row(entry) | {"current_streak": _streak(days)}
    streak = data["current_streak"]
    flair = f" — 🔥 {streak}-day streak" if streak > 1 else ""
    ok(f"Logged {EMOJI} {text}{flair}", json_out=json_out, data=data)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """🙏 Today's gratitude entries."""
    today_date = date.today()
    with session() as db:
        entries = list(
            db.exec(
                select(GratitudeEntry)
                .where(GratitudeEntry.entry_date == today_date)
                .order_by(GratitudeEntry.created_at)
            ).all()
        )
        days = {e.entry_date for e in db.exec(select(GratitudeEntry)).all()}
    streak = _streak(days)
    if json_out:
        render_record(
            {
                "date": today_date,
                "entries": [_row(e) for e in entries],
                "current_streak": streak,
            },
            json_out=True,
        )
        return
    flame = "🔥" * min(streak, 7) if streak else "[dim]—[/dim]"
    console.print(
        f"\n🙏 [bold]Today[/bold] · {today_date:%a %d %b}   "
        f"streak [cyan]{streak}[/cyan]  {flame}\n"
    )
    if not entries:
        console.print(
            "  [dim]Nothing yet. Even one small thing counts — "
            "clibo gratitude add '…'[/dim]\n"
        )
        return
    for entry in entries:
        console.print(f"  · {entry.text}")
    console.print()


@app.command(name="list")
def list_entries(
    days: int = typer.Option(14, "--days", help="Look back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """🙏 Recent gratitude entries."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(
                select(GratitudeEntry)
                .where(GratitudeEntry.entry_date >= since)
                .order_by(GratitudeEntry.entry_date.desc(), GratitudeEntry.id.desc())
            ).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("text", "Grateful for")],
        json_out=json_out,
        title="🙏 Gratitude log",
        empty="Nothing logged yet — try: clibo gratitude add 'sunshine'",
    )


@app.command()
def streak(json_out: JsonOpt = False) -> None:
    """🔥 Show the current and longest gratitude streaks."""
    with session() as db:
        days = {e.entry_date for e in db.exec(select(GratitudeEntry)).all()}
    current = _streak(days)
    longest = _longest_streak(days)
    if json_out:
        render_record(
            {"current_streak": current, "longest_streak": longest,
             "days_practiced": len(days)},
            json_out=True,
        )
        return
    flame = "🔥" * min(current, 10) if current else "[dim]—[/dim]"
    console.print(
        f"\n  🙏 Gratitude streak: [bold cyan]{current}[/bold cyan] days  "
        f"{flame}   [dim](longest ever: {longest})[/dim]\n"
    )


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Entry ID"), json_out: JsonOpt = False) -> None:
    """🙏 Delete a gratitude entry."""
    with session() as db:
        entry = db.get(GratitudeEntry, entry_id)
        if not entry:
            fail(f"No gratitude entry #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted gratitude entry #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def stats(
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Gratitude stats — entries, days practised, streak."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(select(GratitudeEntry).where(GratitudeEntry.entry_date >= since)).all()
        )
        all_days = {e.entry_date for e in db.exec(select(GratitudeEntry)).all()}
    days_in_window = {e.entry_date for e in entries}
    data = {
        "window_days": days,
        "entries": len(entries),
        "days_practised": len(days_in_window),
        "current_streak": _streak(all_days),
        "longest_streak": _longest_streak(all_days),
        "avg_per_day": (
            round(len(entries) / len(days_in_window), 1) if days_in_window else 0.0
        ),
    }
    render_record(data, json_out=json_out, title=f"📊 Gratitude stats · last {days}d")
