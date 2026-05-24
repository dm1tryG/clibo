"""🚀 challenge — time-boxed challenges with daily check-ins (30-day, 100-day, …).

Distinct from `habit`: a habit is open-ended ("drink water every day forever";
streaks count up indefinitely). A challenge has a target duration, a clear
end date, and a binary outcome at the end — *completed* or *failed*. Think
"30 days of no sugar", "100 days of code", "Dry January".

The killer view is ``challenge status`` — for each active challenge:
how many days down, how many to go, today's check-in status, and the
miss budget remaining (if any).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, console, fail, ok, render_record, render_rows

NAME = "challenge"
HELP = "🚀 Time-boxed challenges with daily check-ins"
EMOJI = "🚀"

STATUSES = ["active", "completed", "failed", "abandoned"]


class Challenge(SQLModel, table=True):
    """One challenge — a target span with daily check-ins."""

    __tablename__ = "challenge_entry"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = None
    start_date: date
    target_days: int
    miss_budget: int = 0     # how many missed days are still ok (default 0 = strict)
    status: str = "active"   # active / completed / failed / abandoned
    finished_at: date | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class ChallengeCheckin(SQLModel, table=True):
    """One daily check-in for a challenge."""

    __tablename__ = "challenge_checkin"

    id: int | None = Field(default=None, primary_key=True)
    challenge_id: int = Field(index=True)
    check_date: date = Field(index=True)
    success: bool = True     # False = missed it that day
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo challenge`` (bare) runs the ``status`` summary."""
    if ctx.invoked_subcommand is None:
        # Pass real `None` so ctx.invoke doesn't forward the Typer
        # ArgumentInfo sentinel as a literal into the DB query.
        ctx.invoke(status, challenge_id=None, json_out=False)


def _end_date(c: Challenge) -> date:
    return c.start_date + timedelta(days=c.target_days - 1)


def _checkins(db, challenge_id: int) -> list[ChallengeCheckin]:
    return list(
        db.exec(
            select(ChallengeCheckin)
            .where(ChallengeCheckin.challenge_id == challenge_id)
            .order_by(ChallengeCheckin.check_date)
        ).all()
    )


def _progress(c: Challenge, checkins: list[ChallengeCheckin]) -> dict:
    """Compute days down, days to go, hits, misses, today's status."""
    today = date.today()
    end = _end_date(c)
    days_elapsed = min((today - c.start_date).days + 1, c.target_days)
    days_elapsed = max(days_elapsed, 0)
    by_date = {ci.check_date: ci for ci in checkins}
    hits = sum(1 for ci in checkins if ci.success)
    misses = sum(1 for ci in checkins if not ci.success)
    today_ci = by_date.get(today)
    if today < c.start_date:
        today_status = "not-yet-started"
    elif today > end:
        today_status = "after-end"
    elif today_ci is None:
        today_status = "pending"
    elif today_ci.success:
        today_status = "done"
    else:
        today_status = "missed"
    return {
        "days_elapsed": days_elapsed,
        "days_remaining": max(c.target_days - days_elapsed, 0),
        "end_date": end,
        "hits": hits,
        "misses": misses,
        "today_status": today_status,
        "miss_budget_remaining": max(c.miss_budget - misses, 0),
    }


def _row(c: Challenge, checkins: list[ChallengeCheckin] | None = None) -> dict:
    if checkins is None:
        checkins = []
    p = _progress(c, checkins)
    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "start_date": c.start_date,
        "target_days": c.target_days,
        "end_date": p["end_date"],
        "status": c.status,
        "days_elapsed": p["days_elapsed"],
        "days_remaining": p["days_remaining"],
        "hits": p["hits"],
        "misses": p["misses"],
        "today_status": p["today_status"],
        "miss_budget": c.miss_budget,
        "miss_budget_remaining": p["miss_budget_remaining"],
        "finished_at": c.finished_at,
    }


def _auto_finalize(c: Challenge, checkins: list[ChallengeCheckin]) -> None:
    """Move active challenges to completed/failed when conditions are met.

    Called whenever we look at a challenge; cheap and idempotent.
    """
    if c.status != "active":
        return
    today = date.today()
    misses = sum(1 for ci in checkins if not ci.success)
    if misses > c.miss_budget:
        c.status = "failed"
        c.finished_at = today
        return
    if today > _end_date(c):
        c.status = "completed"
        c.finished_at = _end_date(c)


@app.command()
def start(
    name: str = typer.Argument(..., help="What the challenge is, e.g. 'no sugar'"),
    days: int = typer.Option(30, "--days", "-d",
                              help="Target duration in days"),
    on: str = typer.Option("today", "--start",
                            help="Start date (default: today)"),
    miss_budget: int = typer.Option(0, "--miss-budget", "-m",
                                     help="How many days you can miss and still "
                                          "complete (default 0 = strict)"),
    description: str = typer.Option(None, "--description", "-D",
                                     help="Optional one-liner about the challenge"),
    json_out: JsonOpt = False,
) -> None:
    """🚀 Start a new time-boxed challenge."""
    if days <= 0:
        fail("Days must be positive", json_out=json_out)
    if miss_budget < 0:
        fail("Miss budget cannot be negative", json_out=json_out)
    start_dt = parse_date(on)
    challenge = Challenge(
        name=name, target_days=days, start_date=start_dt,
        miss_budget=miss_budget, description=description,
    )
    with session() as db:
        db.add(challenge)
        db.flush()
        db.refresh(challenge)
        data = _row(challenge, [])
    ok(f"Started {EMOJI} {days}-day challenge: '{name}' "
       f"(through {data['end_date']:%a %d %b})",
       json_out=json_out, data=data)


@app.command()
def check(
    challenge_id: int = typer.Argument(..., help="Challenge ID"),
    missed: bool = typer.Option(False, "--missed", "--fail", "-x",
                                 help="Mark today as a miss (broke the rule)"),
    on: str = typer.Option("today", "--date", "-d", help="Date for the check-in"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """✅ Check in for today (default success; pass --missed if you broke the rule)."""
    check_date = parse_date(on)
    with session() as db:
        c = db.get(Challenge, challenge_id)
        if not c:
            fail(f"No challenge #{challenge_id}", json_out=json_out)
        if c.status != "active":
            fail(f"Challenge #{challenge_id} is {c.status}, not active",
                 json_out=json_out)
        if check_date < c.start_date or check_date > _end_date(c):
            fail(
                f"{check_date} is outside the challenge window "
                f"({c.start_date} → {_end_date(c)})",
                json_out=json_out,
            )
        # Idempotent: replace any existing check-in for this date.
        existing = db.exec(
            select(ChallengeCheckin)
            .where(ChallengeCheckin.challenge_id == challenge_id)
            .where(ChallengeCheckin.check_date == check_date)
        ).first()
        if existing:
            existing.success = not missed
            if note is not None:
                existing.note = note
            db.add(existing)
        else:
            db.add(ChallengeCheckin(
                challenge_id=challenge_id, check_date=check_date,
                success=not missed, note=note,
            ))
        db.flush()
        checkins = _checkins(db, challenge_id)
        _auto_finalize(c, checkins)
        db.add(c)
        db.flush()
        db.refresh(c)
        data = _row(c, checkins)
    flair = ""
    if data["status"] == "completed":
        flair = "  🎉 challenge completed!"
    elif data["status"] == "failed":
        flair = "  💥 challenge failed (miss budget exhausted)"
    verb = "Missed" if missed else "Checked in for"
    ok(f"{verb} day {data['days_elapsed']} of {c.target_days} on '{c.name}'{flair}",
       json_out=json_out, data=data)


@app.command()
def status(
    challenge_id: int = typer.Argument(None, help="Optional: focus on one challenge"),
    json_out: JsonOpt = False,
) -> None:
    """🚀 Show progress on active challenges (or one specific challenge)."""
    with session() as db:
        if challenge_id is not None:
            c = db.get(Challenge, challenge_id)
            if not c:
                fail(f"No challenge #{challenge_id}", json_out=json_out)
            challenges = [c]
        else:
            challenges = list(
                db.exec(
                    select(Challenge).where(Challenge.status == "active")
                    .order_by(Challenge.start_date)
                ).all()
            )
        rows = []
        for ch in challenges:
            cs = _checkins(db, ch.id)
            _auto_finalize(ch, cs)
            db.add(ch)
            rows.append(_row(ch, cs))
        db.flush()
    if json_out:
        render_record({"count": len(rows), "challenges": rows}, json_out=True)
        return
    if not rows:
        console.print(f"\n{EMOJI} [dim]No active challenges.[/dim]\n")
        return
    console.print(f"\n{EMOJI} [bold]Active challenges[/bold]\n")
    for r in rows:
        emoji_status = {
            "done": "[green]✓[/green]",
            "missed": "[red]✗[/red]",
            "pending": "[yellow]·[/yellow]",
            "not-yet-started": "[dim]→[/dim]",
            "after-end": "[dim]end[/dim]",
        }.get(r["today_status"], "·")
        console.print(
            f"  {emoji_status}  [bold]{r['name']}[/bold]    "
            f"day {r['days_elapsed']}/{r['target_days']}    "
            f"{bar(r['days_elapsed'], r['target_days'])}"
        )
        sub_parts = []
        if r["misses"]:
            sub_parts.append(f"{r['misses']} miss{'es' if r['misses'] != 1 else ''}")
        if r["miss_budget"]:
            sub_parts.append(f"{r['miss_budget_remaining']} of {r['miss_budget']} miss-budget left")
        if r["days_remaining"]:
            sub_parts.append(f"{r['days_remaining']}d to go")
        if sub_parts:
            console.print(f"     [dim]{' · '.join(sub_parts)}[/dim]")
    console.print()


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """🚀 Active challenges that still need today's check-in."""
    today_date = date.today()
    with session() as db:
        active = list(
            db.exec(select(Challenge).where(Challenge.status == "active")).all()
        )
        pending = []
        for ch in active:
            if today_date < ch.start_date or today_date > _end_date(ch):
                continue
            existing = db.exec(
                select(ChallengeCheckin)
                .where(ChallengeCheckin.challenge_id == ch.id)
                .where(ChallengeCheckin.check_date == today_date)
            ).first()
            if existing is None:
                pending.append(_row(ch, _checkins(db, ch.id)))
    if json_out:
        render_record(
            {"date": today_date, "pending": pending, "count": len(pending)},
            json_out=True,
        )
        return
    if not pending:
        console.print(f"\n{EMOJI} [green]All challenge check-ins are in for today.[/green]\n")
        return
    console.print(f"\n{EMOJI} [bold]Pending challenge check-ins[/bold]\n")
    for r in pending:
        console.print(
            f"  ·  [bold]{r['name']}[/bold]    "
            f"day {r['days_elapsed']}/{r['target_days']}    "
            f"[dim]clibo challenge check {r['id']}[/dim]"
        )
    console.print()


@app.command(name="list")
def list_all(
    show_all: bool = typer.Option(False, "--all", "-a",
                                   help="Include finished, failed and abandoned"),
    json_out: JsonOpt = False,
) -> None:
    """🚀 List challenges (active by default; --all includes the rest)."""
    with session() as db:
        query = select(Challenge)
        if not show_all:
            query = query.where(Challenge.status == "active")
        challenges = list(db.exec(query.order_by(Challenge.start_date.desc())).all())
        rows = []
        for ch in challenges:
            cs = _checkins(db, ch.id)
            _auto_finalize(ch, cs)
            rows.append(_row(ch, cs))
        db.flush()
    render_rows(
        rows,
        [("id", "ID"), ("name", "Name"), ("target_days", "Days"),
         ("days_elapsed", "Done"), ("hits", "✓"), ("misses", "✗"),
         ("status", "Status"), ("end_date", "Ends")],
        json_out=json_out,
        title=f"{EMOJI} Challenges",
        empty="No challenges yet — try: clibo challenge start 'no sugar' -d 30",
    )


@app.command()
def show(
    challenge_id: int = typer.Argument(..., help="Challenge ID"),
    json_out: JsonOpt = False,
) -> None:
    """🚀 Show one challenge with its full check-in history."""
    with session() as db:
        c = db.get(Challenge, challenge_id)
        if not c:
            fail(f"No challenge #{challenge_id}", json_out=json_out)
        checkins = _checkins(db, challenge_id)
        _auto_finalize(c, checkins)
        db.add(c)
        db.flush()
        db.refresh(c)
        data = _row(c, checkins)
        data["checkins"] = [
            {"date": ci.check_date, "success": ci.success, "note": ci.note}
            for ci in checkins
        ]
    render_record(data, json_out=json_out, title=f"{EMOJI} {c.name}")


@app.command()
def abandon(
    challenge_id: int = typer.Argument(..., help="Challenge ID"),
    json_out: JsonOpt = False,
) -> None:
    """🏳️ Abandon an active challenge (you'll see it in `list --all`)."""
    with session() as db:
        c = db.get(Challenge, challenge_id)
        if not c:
            fail(f"No challenge #{challenge_id}", json_out=json_out)
        if c.status != "active":
            fail(f"Challenge #{challenge_id} is {c.status}, not active",
                 json_out=json_out)
        c.status = "abandoned"
        c.finished_at = date.today()
        db.add(c)
        db.flush()
        db.refresh(c)
        data = _row(c, _checkins(db, challenge_id))
    ok(f"Abandoned '{c.name}'", json_out=json_out, data=data)


@app.command()
def rm(
    challenge_id: int = typer.Argument(..., help="Challenge ID"),
    json_out: JsonOpt = False,
) -> None:
    """🚀 Delete a challenge (and its check-ins)."""
    with session() as db:
        c = db.get(Challenge, challenge_id)
        if not c:
            fail(f"No challenge #{challenge_id}", json_out=json_out)
        # Cascade-delete check-ins manually (no FK constraint defined).
        for ci in _checkins(db, challenge_id):
            db.delete(ci)
        db.delete(c)
    ok(f"Deleted challenge #{challenge_id}",
       json_out=json_out, data={"deleted": challenge_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Overall: total challenges started, completed, current count."""
    with session() as db:
        challenges = list(db.exec(select(Challenge)).all())
        # Make sure auto-finalization runs before counting.
        for ch in challenges:
            _auto_finalize(ch, _checkins(db, ch.id))
            db.add(ch)
        db.flush()
        challenges = list(db.exec(select(Challenge)).all())
    if not challenges:
        fail("No challenges yet", json_out=json_out)
    by_status: dict[str, int] = {}
    for ch in challenges:
        by_status[ch.status] = by_status.get(ch.status, 0) + 1
    completed = by_status.get("completed", 0)
    failed = by_status.get("failed", 0)
    finalised = completed + failed
    data = {
        "total": len(challenges),
        "active": by_status.get("active", 0),
        "completed": completed,
        "failed": failed,
        "abandoned": by_status.get("abandoned", 0),
        "completion_rate_pct": round(100 * completed / finalised, 1)
            if finalised else None,
        "by_status": by_status,
    }
    render_record(data, json_out=json_out, title=f"{EMOJI} Challenge stats")
