"""☕ caffeine — caffeine intake tracker with residual-at-bedtime estimate.

Distinct from `water` (hydration), `calorie` (food / kcal), `meds` (prescribed
medication). The unique value: caffeine has a ~5-6 hour half-life in adults,
so this tool computes how much will still be in your system at bedtime — the
key number for sleep research. A late afternoon coffee can leave 30-50mg in
you when you're trying to fall asleep.

Drink presets (mg of caffeine) save typing. Override with `-m / --mg` for
anything custom (cold brew, double shots, brewed strength, …).
"""

from __future__ import annotations

import math
from collections import Counter
from datetime import date, datetime, time, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows
from clibo.core.settings import get_setting, set_setting

NAME = "caffeine"
HELP = "☕ Caffeine intake tracker with bedtime-residual estimate"
EMOJI = "☕"

# Approximate caffeine content in mg for common drinks. Sources: USDA, FDA,
# manufacturer disclosures. These are reasonable defaults — agents and users
# can always override with -m / --mg.
PRESETS: dict[str, int] = {
    "espresso": 63,
    "double-espresso": 126,
    "americano": 150,
    "latte": 75,
    "cappuccino": 75,
    "flat-white": 130,
    "coffee": 95,             # 240ml brewed
    "cold-brew": 200,         # 350ml
    "drip": 95,
    "decaf": 5,
    "matcha": 70,
    "green-tea": 30,
    "black-tea": 50,
    "earl-grey": 50,
    "redbull": 80,
    "monster": 160,
    "coca-cola": 34,          # 355ml
    "diet-coke": 46,
    "yerba-mate": 85,
    "chocolate": 12,
}

# Caffeine half-life in adults, in hours. 5.5h is the canonical midpoint.
HALF_LIFE_HOURS = 5.5
DEFAULT_BEDTIME = "23:00"  # 24h "HH:MM"
DEFAULT_DAILY_LIMIT_MG = 400  # FDA recommendation for healthy adults


class CaffeineEntry(SQLModel, table=True):
    """One caffeinated drink — drink name, mg, when consumed."""

    __tablename__ = "caffeine_entry"

    id: int | None = Field(default=None, primary_key=True)
    drink: str
    mg: int
    entry_date: date = Field(default_factory=date.today, index=True)
    consumed_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context) -> None:
    """Default: ``clibo caffeine`` (bare) shows today's intake.

    The natural ask *"how much caffeine have I had today?"* maps to
    bare ``clibo caffeine``; otherwise users had to remember the
    ``today`` subcommand. Other subcommands are unaffected.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(today, json_out=False)


def _bedtime() -> time:
    raw = get_setting(NAME, "bedtime", DEFAULT_BEDTIME) or DEFAULT_BEDTIME
    h, m = raw.split(":")
    return time(int(h), int(m))


def _daily_limit() -> int:
    return int(
        get_setting(NAME, "daily_limit_mg", str(DEFAULT_DAILY_LIMIT_MG))
        or DEFAULT_DAILY_LIMIT_MG
    )


def _row(entry: CaffeineEntry) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "consumed_at": entry.consumed_at,
        "drink": entry.drink,
        "mg": entry.mg,
        "note": entry.note,
    }


def _residual_at(entry: CaffeineEntry, when: datetime) -> float:
    """How much of `entry`'s caffeine is still in the body at `when`."""
    hours_passed = (when - entry.consumed_at).total_seconds() / 3600
    if hours_passed < 0:
        return 0.0
    return entry.mg * (0.5 ** (hours_passed / HALF_LIFE_HOURS))


def _parse_consumed_at(on: str, at: str | None) -> datetime:
    """Combine a date string and an optional HH:MM time into a datetime."""
    day = parse_date(on)
    if at is None:
        # Use now if the date is today, else noon (a defensible default).
        if day == date.today():
            return datetime.now()
        return datetime.combine(day, time(12, 0))
    try:
        h, m = at.split(":")
        return datetime.combine(day, time(int(h), int(m)))
    except (ValueError, AttributeError):
        raise typer.BadParameter(f"Time must be HH:MM (got {at!r})") from None


def _todays_residual_at_bedtime() -> tuple[float, datetime]:
    """Total residual caffeine in mg at tonight's bedtime."""
    bedtime = _bedtime()
    now = datetime.now()
    bedtime_dt = datetime.combine(now.date(), bedtime)
    if bedtime_dt < now:
        bedtime_dt += timedelta(days=1)
    with session() as db:
        # Pull entries from the last 48h — anything older is negligible.
        cutoff_dt = now - timedelta(hours=48)
        entries = list(
            db.exec(
                select(CaffeineEntry).where(CaffeineEntry.consumed_at >= cutoff_dt)
            ).all()
        )
    return (
        round(sum(_residual_at(e, bedtime_dt) for e in entries), 1),
        bedtime_dt,
    )


@app.command()
def log(
    drink: str = typer.Argument(...,
                                help=f"Drink name. Presets with default mg: "
                                     f"{', '.join(sorted(PRESETS))}"),
    mg: int = typer.Option(None, "--mg", "-m",
                            help="Caffeine in mg (overrides the preset)"),
    at: str = typer.Option(None, "--at", "-t",
                            help="Time of day as HH:MM (default: now)"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """☕ Log a caffeinated drink."""
    drink_key = drink.lower().strip().replace(" ", "-")
    resolved_mg: int | None = mg
    if resolved_mg is None:
        resolved_mg = PRESETS.get(drink_key)
    if resolved_mg is None:
        fail(
            f"No preset for {drink!r} — pass `-m / --mg` with the caffeine "
            f"content in milligrams. Known presets: "
            f"{', '.join(sorted(PRESETS))}",
            json_out=json_out,
        )
    if resolved_mg <= 0:
        fail("Caffeine mg must be positive", json_out=json_out)
    consumed_at = _parse_consumed_at(on, at)
    entry = CaffeineEntry(
        drink=drink_key,
        mg=resolved_mg,
        entry_date=consumed_at.date(),
        note=note,
        consumed_at=consumed_at,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    # Show today's running total + the headline number: residual at bedtime.
    residual, bedtime_dt = _todays_residual_at_bedtime()
    ok(
        f"Logged {EMOJI} {drink_key} ({resolved_mg} mg) at "
        f"{consumed_at:%H:%M} — {residual:g} mg residual at "
        f"{bedtime_dt:%H:%M}",
        json_out=json_out,
        data={**data, "residual_at_bedtime_mg": residual,
              "bedtime": bedtime_dt.isoformat()},
    )


# `add` is a friendlier alias for `log` (predictable verbs across tools).
app.command(name="add", help="Alias for `log`")(log)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """☕ Today's caffeine total and bedtime-residual estimate."""
    day = date.today()
    limit = _daily_limit()
    with session() as db:
        entries = list(
            db.exec(
                select(CaffeineEntry).where(CaffeineEntry.entry_date == day)
                .order_by(CaffeineEntry.consumed_at)
            ).all()
        )
    total = sum(e.mg for e in entries)
    residual, bedtime_dt = _todays_residual_at_bedtime()
    if json_out:
        render_record(
            {
                "date": day,
                "drinks": len(entries),
                "total_mg": total,
                "daily_limit_mg": limit,
                "over_limit": total > limit,
                "residual_at_bedtime_mg": residual,
                "bedtime": bedtime_dt.isoformat(),
                "entries": [_row(e) for e in entries],
            },
            json_out=True,
        )
        return
    if not entries:
        console.print(f"\n{EMOJI} [dim]No caffeine logged today.[/dim]\n")
        return
    console.print(f"\n{EMOJI} [bold]Caffeine today[/bold] · {day:%a %d %b}\n")
    for entry in entries:
        console.print(
            f"  • {entry.consumed_at:%H:%M}   "
            f"[cyan]{entry.drink}[/cyan] — "
            f"[bold]{entry.mg}[/bold] mg"
        )
    over = " [red](over daily limit!)[/red]" if total > limit else ""
    bedtime_colour = "yellow" if residual > 10 else "green"
    console.print(
        f"\n  [bold]{total}[/bold] mg total today (limit {limit}){over}"
    )
    console.print(
        f"  By {bedtime_dt:%H:%M} bedtime: "
        f"[{bedtime_colour}]{residual:g} mg[/{bedtime_colour}] still in system"
    )
    if residual > 10:
        console.print(
            "  [dim](sleep researchers recommend < 10 mg residual)[/dim]\n"
        )
    else:
        console.print()


@app.command()
def cutoff(json_out: JsonOpt = False) -> None:
    """🕘 Latest time today you can have one of each preset and still hit
    the under-10 mg residual target at bedtime."""
    bedtime = _bedtime()
    now = datetime.now()
    bedtime_dt = datetime.combine(now.date(), bedtime)
    if bedtime_dt < now:
        bedtime_dt += timedelta(days=1)
    rows = []
    for drink, mg in sorted(PRESETS.items(), key=lambda kv: -kv[1]):
        # Solve mg * 0.5^(hours/half_life) = 10 for hours →
        # hours = half_life * log2(mg / 10).
        if mg <= 10:
            latest = bedtime_dt  # already at or below the 10 mg target
        else:
            hours = HALF_LIFE_HOURS * math.log2(mg / 10)
            latest = bedtime_dt - timedelta(hours=hours)
        rows.append({
            "drink": drink,
            "mg": mg,
            "latest_safe_time": latest.strftime("%H:%M"),
            "safe_now": latest >= now,
        })
    render_rows(
        rows,
        [("drink", "Drink"), ("mg", "mg"),
         ("latest_safe_time", "Latest by"), ("safe_now", "OK now?")],
        json_out=json_out,
        title=f"🕘 Caffeine cutoff for {bedtime_dt:%H:%M} bedtime "
              f"(< 10 mg target)",
    )


@app.command(name="list")
def list_entries(
    days: int = typer.Option(7, "--days", help="Look back this many days"),
    drink: str = typer.Option(None, "--drink", help="Filter by drink"),
    json_out: JsonOpt = False,
) -> None:
    """☕ List recent caffeine entries."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(CaffeineEntry).where(CaffeineEntry.entry_date >= since)
        if drink:
            query = query.where(CaffeineEntry.drink == drink.lower().strip())
        entries = list(
            db.exec(query.order_by(CaffeineEntry.consumed_at.desc())).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("consumed_at", "When"),
         ("drink", "Drink"), ("mg", "mg"), ("note", "Note")],
        json_out=json_out,
        title=f"{EMOJI} Caffeine — last {days}d",
        empty="No entries yet — try: clibo caffeine log coffee",
    )


@app.command()
def show(entry_id: int = typer.Argument(..., help="Entry ID"),
         json_out: JsonOpt = False) -> None:
    """☕ Show one caffeine entry."""
    with session() as db:
        entry = db.get(CaffeineEntry, entry_id)
        if not entry:
            fail(f"No caffeine entry #{entry_id}", json_out=json_out)
        data = _row(entry)
    render_record(data, json_out=json_out,
                  title=f"{EMOJI} Caffeine entry #{entry_id}")


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Entry ID"),
       json_out: JsonOpt = False) -> None:
    """☕ Delete a caffeine entry."""
    with session() as db:
        entry = db.get(CaffeineEntry, entry_id)
        if not entry:
            fail(f"No caffeine entry #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted caffeine entry #{entry_id}",
       json_out=json_out, data={"deleted": entry_id})


@app.command()
def edit(
    target: str = typer.Argument(..., help="Entry ID or 'last' for the most recent"),
    drink: str = typer.Option(None, "--drink", help="New drink name"),
    mg: int = typer.Option(None, "--mg", "-m", help="New mg of caffeine"),
    at: str = typer.Option(None, "--at", "-t", help="New consumed time HH:MM"),
    on: str = typer.Option(None, "--date", "-d", help="New date"),
    note: str = typer.Option(None, "--note", "-n", help="New note"),
    json_out: JsonOpt = False,
) -> None:
    """☕ Edit an existing caffeine entry."""
    from clibo.core.base import resolve_id
    with session() as db:
        entry = resolve_id(target, CaffeineEntry, db)
        if not entry:
            fail(f"No caffeine entry matching {target!r}", json_out=json_out)
        if drink is not None:
            entry.drink = drink.lower().strip().replace(" ", "-")
        if mg is not None:
            if mg <= 0:
                fail("mg must be positive", json_out=json_out)
            entry.mg = mg
        # Re-build consumed_at if either date or time is being changed.
        if at is not None or on is not None:
            day = parse_date(on) if on is not None else entry.entry_date
            if at is not None:
                consumed_at = _parse_consumed_at(str(day), at)
            else:
                consumed_at = datetime.combine(day, entry.consumed_at.time())
            entry.consumed_at = consumed_at
            entry.entry_date = consumed_at.date()
        if note is not None:
            entry.note = note
        db.add(entry)
        db.flush()
        data = _row(entry)
    ok(f"Updated caffeine entry #{entry.id} — {entry.drink} ({entry.mg} mg)",
       json_out=json_out, data=data)


@app.command(name="bedtime")
def bedtime_cmd(
    set_time: str = typer.Option(None, "--set",
                                  help="Set bedtime as HH:MM (24-hour)"),
    json_out: JsonOpt = False,
) -> None:
    """🌙 Show or set your bedtime (used by residual-caffeine calculations)."""
    if set_time is not None:
        try:
            h, m = set_time.split(":")
            time(int(h), int(m))
        except ValueError:
            fail("Bedtime must be HH:MM (24-hour)", json_out=json_out)
        set_setting(NAME, "bedtime", set_time)
        ok(f"Bedtime set to {set_time}", json_out=json_out,
           data={"bedtime": set_time})
        return
    render_record({"bedtime": _bedtime().strftime("%H:%M")},
                  json_out=json_out, title="🌙 Bedtime")


@app.command()
def stats(
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Caffeine stats — daily avg, by drink, over-limit days."""
    since = date.today() - timedelta(days=days - 1)
    limit = _daily_limit()
    with session() as db:
        entries = list(
            db.exec(
                select(CaffeineEntry).where(CaffeineEntry.entry_date >= since)
            ).all()
        )
    if not entries:
        fail("No caffeine in this window", json_out=json_out)
    per_day: dict[date, int] = {}
    for entry in entries:
        per_day[entry.entry_date] = per_day.get(entry.entry_date, 0) + entry.mg
    drinks = Counter(e.drink for e in entries)
    total_mg = sum(e.mg for e in entries)
    days_logged = len(per_day)
    over_limit_days = sum(1 for mg in per_day.values() if mg > limit)
    biggest_day, biggest_mg = max(per_day.items(), key=lambda kv: kv[1])
    from clibo.core.sparkline import sparkline_days
    data = {
        "window_days": days,
        "entries": len(entries),
        "days_logged": days_logged,
        "total_mg": total_mg,
        "avg_mg_per_day": round(total_mg / days_logged) if days_logged else 0,
        "daily_limit_mg": limit,
        "over_limit_days": over_limit_days,
        "biggest_day": {"date": biggest_day, "mg": biggest_mg},
        "by_drink_count": dict(drinks),
        "chart": sparkline_days(
            {d: float(v) for d, v in per_day.items()}, since, date.today()
        ),
    }
    render_record(data, json_out=json_out,
                  title=f"📊 Caffeine · last {days}d")
