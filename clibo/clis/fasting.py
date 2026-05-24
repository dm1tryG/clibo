"""🕒 fasting — intermittent-fasting session tracker.

A fast is a *time window* — distinct from `calorie` (what you ate),
`water` (hydration during/around it) and `sleep` (sleep is overnight,
fasts can span any hours).

The daily-driver question is "am I still fasting? how much longer to
target?" — answered by `fasting status` with a running clock against
the target window.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, console, fail, ok, render_record, render_rows
from clibo.core.settings import get_setting, set_setting

NAME = "fasting"
HELP = "🕒 Intermittent-fasting tracker"
EMOJI = "🕒"
DEFAULT_TARGET_HOURS = 16.0


class FastSession(SQLModel, table=True):
    """One fasting window — `end_time` is None while the fast is ongoing."""

    __tablename__ = "fast_session"

    id: int | None = Field(default=None, primary_key=True)
    start_time: datetime = Field(index=True)
    end_time: datetime | None = None
    target_hours: float = DEFAULT_TARGET_HOURS
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _bare_default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo fasting`` (bare) shows your fasting status.

    The natural ask *"am I still fasting?"* / *"how long until my
    target?"* maps to bare ``clibo fasting``; otherwise users had
    to remember the ``status`` subcommand. Other subcommands
    (``start``, ``stop``, ``list``, …) are unaffected.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(status, json_out=json_out)


def _default_target() -> float:
    raw = get_setting(NAME, "target_hours", str(DEFAULT_TARGET_HOURS))
    try:
        return float(raw or DEFAULT_TARGET_HOURS)
    except ValueError:
        return DEFAULT_TARGET_HOURS


def _duration_hours(fast: FastSession, *, until: datetime | None = None) -> float:
    """Hours from start to end (or to ``until`` if still ongoing)."""
    end = fast.end_time or until or datetime.now()
    return round((end - fast.start_time).total_seconds() / 3600, 2)


def _row(fast: FastSession) -> dict:
    now = datetime.now()
    ongoing = fast.end_time is None
    duration = _duration_hours(fast, until=now if ongoing else None)
    reached = duration >= fast.target_hours
    return {
        "id": fast.id,
        "start_time": fast.start_time,
        "end_time": fast.end_time,
        "target_hours": fast.target_hours,
        "duration_hours": duration,
        "ongoing": ongoing,
        "reached_target": reached,
        "remaining_hours": (
            round(max(fast.target_hours - duration, 0), 2)
            if ongoing else None
        ),
        "note": fast.note,
    }


def _ongoing_fast(db) -> FastSession | None:
    """Return the most recent fast still in progress, or None."""
    return db.exec(
        select(FastSession).where(FastSession.end_time.is_(None))
        .order_by(FastSession.start_time.desc())
    ).first()


def _parse_when(at: str | None) -> datetime:
    """Parse a date/time string into a datetime.

    Accepts:
    * ``None`` → now.
    * ``HH:MM`` → today at that time.
    * Any phrase ``parse_date`` accepts (``yesterday``, ``3 days ago``,
      ``Mar 12``) → that date at midnight.
    * A date phrase **followed by ``HH:MM``** at the end (e.g.
      ``"yesterday 08:00"``, ``"3 days ago 22:00"``) — the trailing
      ``HH:MM`` token is the time, everything before it is the date.
    """
    import re
    if at is None:
        return datetime.now()
    text = at.strip()
    # Bare HH:MM means today.
    if re.fullmatch(r"\d{1,2}:\d{2}", text):
        day = date.today()
        time_part = text
    else:
        # Look for a trailing HH:MM after at least one space.
        match = re.match(r"^(.*\S)\s+(\d{1,2}:\d{2})$", text)
        if match:
            date_phrase, time_part = match.group(1), match.group(2)
            day = parse_date(date_phrase)
        else:
            day = parse_date(text)
            time_part = "00:00"
    try:
        h, m = time_part.split(":")
        return datetime.combine(day, datetime.min.time()).replace(
            hour=int(h), minute=int(m)
        )
    except (ValueError, AttributeError):
        raise typer.BadParameter(
            f"Time must be HH:MM, '<date> HH:MM', or any date parse_date "
            f"accepts (got {at!r})"
        ) from None


@app.command()
def start(
    target: float = typer.Option(None, "--target", "-T",
                                  help="Target hours for this fast "
                                       "(default: your saved target)"),
    at: str = typer.Option(None, "--at", "-t",
                            help="Start time as HH:MM (default: now)"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🕒 Start a fasting window."""
    target_h = target if target is not None else _default_target()
    if target_h <= 0:
        fail("Target hours must be positive", json_out=json_out)
    start_dt = _parse_when(at)
    if start_dt > datetime.now() + timedelta(minutes=1):
        fail("Start time can't be in the future", json_out=json_out)
    with session() as db:
        if _ongoing_fast(db) is not None:
            fail(
                "A fast is already in progress — stop it first with "
                "`clibo fasting stop`",
                json_out=json_out,
            )
        fast = FastSession(
            start_time=start_dt, target_hours=target_h, note=note,
        )
        db.add(fast)
        db.flush()
        db.refresh(fast)
        data = _row(fast)
    ok(
        f"Started {EMOJI} fast at {start_dt:%H:%M} — target {target_h:g}h "
        f"(ends ~{(start_dt + timedelta(hours=target_h)):%a %H:%M})",
        json_out=json_out, data=data,
    )


@app.command()
def stop(
    at: str = typer.Option(None, "--at", "-t",
                            help="Stop time as HH:MM (default: now)"),
    note: str = typer.Option(None, "--note", "-n",
                              help="Optional note to append"),
    json_out: JsonOpt = False,
) -> None:
    """⏹ End the currently-ongoing fast."""
    end_dt = _parse_when(at)
    with session() as db:
        fast = _ongoing_fast(db)
        if fast is None:
            fail("No fast in progress — start one with `clibo fasting start`",
                 json_out=json_out)
        if end_dt < fast.start_time:
            fail(
                f"Stop time {end_dt} is before start {fast.start_time}",
                json_out=json_out,
            )
        if end_dt > datetime.now() + timedelta(minutes=1):
            fail("Stop time can't be in the future", json_out=json_out)
        fast.end_time = end_dt
        if note is not None:
            fast.note = note
        db.add(fast)
        db.flush()
        db.refresh(fast)
        data = _row(fast)
    flair = "  ✓ target reached" if data["reached_target"] else ""
    ok(f"Ended {EMOJI} fast — {data['duration_hours']:g}h "
       f"(target {fast.target_hours:g}h){flair}",
       json_out=json_out, data=data)


@app.command()
def status(json_out: JsonOpt = False) -> None:
    """🕒 Are you fasting right now? How much longer until target?"""
    with session() as db:
        fast = _ongoing_fast(db)
        if fast is None:
            # Show the most recent completed fast instead.
            last = db.exec(
                select(FastSession).where(FastSession.end_time.is_not(None))
                .order_by(FastSession.end_time.desc())
            ).first()
        else:
            last = None
    if fast:
        data = _row(fast)
        if json_out:
            render_record(data, json_out=True)
            return
        elapsed = data["duration_hours"]
        target = data["target_hours"]
        remaining = data["remaining_hours"]
        console.print(f"\n{EMOJI} [bold]Fasting in progress[/bold]\n")
        console.print(f"  started   {fast.start_time:%a %H:%M}")
        console.print(f"  target    {target:g}h "
                       f"(ends ~{(fast.start_time + timedelta(hours=target)):%a %H:%M})\n")
        console.print(f"  {bar(elapsed, target)}")
        console.print(
            f"  [bold cyan]{elapsed:g}h[/bold cyan] elapsed   ·   "
            + (f"[green]{remaining:g}h to target[/green]"
               if remaining > 0 else "[green]✓ target reached![/green]")
        )
        console.print()
        return
    if last is None:
        if json_out:
            render_record({"ongoing": False, "last": None}, json_out=True)
            return
        console.print(f"\n{EMOJI} [dim]No fasts logged yet.[/dim]\n")
        return
    data = {"ongoing": False, "last": _row(last)}
    if json_out:
        render_record(data, json_out=True)
        return
    last_row = data["last"]
    console.print(f"\n{EMOJI} [dim]Not currently fasting.[/dim]\n")
    console.print(
        f"  Last fast: [bold]{last_row['duration_hours']:g}h[/bold] "
        f"(target {last_row['target_hours']:g}h, "
        f"ended {last.end_time:%a %H:%M})\n"
    )


@app.command(name="list")
def list_fasts(
    days: int = typer.Option(30, "--days", help="Look back this many days"),
    completed_only: bool = typer.Option(False, "--completed",
                                         help="Hide the in-progress fast"),
    json_out: JsonOpt = False,
) -> None:
    """🕒 Recent fasting sessions, newest first."""
    since = datetime.now() - timedelta(days=days)
    with session() as db:
        query = select(FastSession).where(FastSession.start_time >= since)
        if completed_only:
            query = query.where(FastSession.end_time.is_not(None))
        fasts = list(
            db.exec(query.order_by(FastSession.start_time.desc())).all()
        )
    render_rows(
        [_row(f) for f in fasts],
        [("id", "ID"), ("start_time", "Started"),
         ("end_time", "Ended"), ("duration_hours", "Hours"),
         ("target_hours", "Target"), ("reached_target", "✓?")],
        json_out=json_out,
        title=f"{EMOJI} Fasts — last {days}d",
        empty="No fasts yet — try: clibo fasting start --target 16",
        formatters={
            "duration_hours": lambda v, r: f"{v:g}h",
            "target_hours": lambda v, r: f"{v:g}h",
            "end_time": lambda v, r: (f"{v:%a %H:%M}" if v else "[dim]ongoing[/dim]"),
            "reached_target": lambda v, r: (
                "[green]✓[/green]" if v else "[dim]·[/dim]"
            ),
        },
    )


@app.command()
def show(
    fast_id: int = typer.Argument(..., help="Fast ID"),
    json_out: JsonOpt = False,
) -> None:
    """🕒 Show one fast."""
    with session() as db:
        fast = db.get(FastSession, fast_id)
        if not fast:
            fail(f"No fast #{fast_id}", json_out=json_out)
        data = _row(fast)
    render_record(data, json_out=json_out, title=f"{EMOJI} Fast #{fast_id}")


@app.command()
def rm(
    fast_id: int = typer.Argument(..., help="Fast ID"),
    json_out: JsonOpt = False,
) -> None:
    """🕒 Delete a fast."""
    with session() as db:
        fast = db.get(FastSession, fast_id)
        if not fast:
            fail(f"No fast #{fast_id}", json_out=json_out)
        db.delete(fast)
    ok(f"Deleted fast #{fast_id}",
       json_out=json_out, data={"deleted": fast_id})


@app.command()
def target(
    set_hours: float = typer.Option(None, "--set",
                                     help="Set your default target hours"),
    json_out: JsonOpt = False,
) -> None:
    """🎯 Show or set your default fasting target."""
    if set_hours is not None:
        if set_hours <= 0:
            fail("Target hours must be positive", json_out=json_out)
        set_setting(NAME, "target_hours", str(set_hours))
        ok(f"Default fasting target set to {set_hours:g}h",
           json_out=json_out, data={"target_hours": set_hours})
        return
    render_record({"target_hours": _default_target()},
                  json_out=json_out, title="🎯 Default fasting target")


@app.command()
def stats(
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Fasting stats — count, avg duration, longest, hit rate."""
    since = datetime.now() - timedelta(days=days)
    with session() as db:
        fasts = list(
            db.exec(
                select(FastSession)
                .where(FastSession.start_time >= since)
                .where(FastSession.end_time.is_not(None))
            ).all()
        )
    if not fasts:
        fail("No completed fasts in this window", json_out=json_out)
    durations = [_duration_hours(f) for f in fasts]
    targets = [f.target_hours for f in fasts]
    hits = sum(1 for d, t in zip(durations, targets, strict=True) if d >= t)
    longest = max(fasts, key=lambda f: _duration_hours(f))
    longest_h = _duration_hours(longest)
    data = {
        "window_days": days,
        "completed_fasts": len(fasts),
        "total_hours_fasted": round(sum(durations), 1),
        "avg_duration_hours": round(sum(durations) / len(durations), 2),
        "longest_fast_hours": longest_h,
        "longest_fast_id": longest.id,
        "target_hit_rate_pct": round(100 * hits / len(fasts), 1),
        "hits": hits,
        "default_target_hours": _default_target(),
    }
    render_record(data, json_out=json_out, title=f"📊 Fasting · last {days}d")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
