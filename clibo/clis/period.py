"""🌸 period — menstrual cycle tracker & predictions."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "period"
HELP = "🌸 Menstrual cycle tracker & predictions"
EMOJI = "🌸"
FLOWS = ["light", "medium", "heavy"]
DEFAULT_CYCLE_DAYS = 28
LUTEAL_PHASE_DAYS = 14


class PeriodLog(SQLModel, table=True):
    """One menstrual period — its start, optional end, flow and notes."""

    __tablename__ = "period_log"

    id: int | None = Field(default=None, primary_key=True)
    start_date: date = Field(index=True)
    end_date: date | None = None
    flow: str | None = None
    symptoms: str | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _length(entry: PeriodLog) -> int | None:
    """Period length in days, if it has an end date."""
    if entry.end_date is None:
        return None
    return (entry.end_date - entry.start_date).days + 1


def _row(entry: PeriodLog) -> dict:
    return {
        "id": entry.id,
        "start_date": entry.start_date,
        "end_date": entry.end_date,
        "length_days": _length(entry),
        "flow": entry.flow,
        "symptoms": entry.symptoms,
        "note": entry.note,
    }


def _all_starts(db) -> list[date]:
    """All period start dates, oldest first."""
    return [
        e.start_date
        for e in db.exec(select(PeriodLog).order_by(PeriodLog.start_date)).all()
    ]


def _avg_cycle(starts: list[date]) -> tuple[int, int]:
    """Return (average cycle length in days, number of cycles observed)."""
    gaps = [(starts[i + 1] - starts[i]).days for i in range(len(starts) - 1)]
    if not gaps:
        return DEFAULT_CYCLE_DAYS, 0
    return round(sum(gaps) / len(gaps)), len(gaps)


@app.command()
def start(
    on: str = typer.Option("today", "--date", "-d", help="Period start date"),
    flow: str = typer.Option(None, "--flow", "-f", help="light / medium / heavy"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🌸 Log the start of a period."""
    if flow and flow.lower() not in FLOWS:
        fail(f"Flow must be one of: {', '.join(FLOWS)}", json_out=json_out)
    entry = PeriodLog(
        start_date=parse_date(on),
        flow=flow.lower() if flow else None,
        note=note,
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    ok(f"Period started {EMOJI} {entry.start_date}", json_out=json_out, data=data)


@app.command()
def end(
    on: str = typer.Option("today", "--date", "-d", help="Period end date"),
    json_out: JsonOpt = False,
) -> None:
    """🌸 Set the end date of your most recent period."""
    end_date = parse_date(on)
    with session() as db:
        entry = db.exec(
            select(PeriodLog).order_by(PeriodLog.start_date.desc())
        ).first()
        if not entry:
            fail("No period logged yet — start one with: clibo period start",
                 json_out=json_out)
        if end_date < entry.start_date:
            fail("End date cannot be before the start date", json_out=json_out)
        entry.end_date = end_date
        db.add(entry)
        db.flush()
        data = _row(entry)
    ok(f"Period ended {EMOJI} {end_date} ({data['length_days']} days)",
       json_out=json_out, data=data)


@app.command()
def log(
    start_date: str = typer.Option(..., "--start", "-s", help="Start date"),
    end_date: str = typer.Option(..., "--end", "-e", help="End date"),
    flow: str = typer.Option(None, "--flow", "-f", help="light / medium / heavy"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🌸 Log a complete past period with start and end dates."""
    if flow and flow.lower() not in FLOWS:
        fail(f"Flow must be one of: {', '.join(FLOWS)}", json_out=json_out)
    sd, ed = parse_date(start_date), parse_date(end_date)
    if ed < sd:
        fail("End date cannot be before the start date", json_out=json_out)
    entry = PeriodLog(start_date=sd, end_date=ed, flow=flow.lower() if flow else None, note=note)
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    ok(f"Logged period {EMOJI} {sd} → {ed} ({data['length_days']} days)",
       json_out=json_out, data=data)


# `add` is a friendlier alias for `log` (predictable verbs across tools).
app.command(name="add", help="Alias for `log`")(log)


@app.command(name="list")
def list_entries(
    limit: int = typer.Option(12, "--limit", help="How many recent periods to show"),
    json_out: JsonOpt = False,
) -> None:
    """🌸 List recent periods."""
    with session() as db:
        entries = list(
            db.exec(
                select(PeriodLog).order_by(PeriodLog.start_date.desc()).limit(limit)
            ).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("start_date", "Start"), ("end_date", "End"),
         ("length_days", "Days"), ("flow", "Flow"), ("note", "Note")],
        json_out=json_out,
        title="🌸 Period history",
        empty="No periods logged yet — start one with: clibo period start",
    )


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Entry ID"), json_out: JsonOpt = False) -> None:
    """🌸 Delete a period entry."""
    with session() as db:
        entry = db.get(PeriodLog, entry_id)
        if not entry:
            fail(f"No period entry #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted period entry #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def predict(json_out: JsonOpt = False) -> None:
    """🔮 Predict your next period and fertile window."""
    with session() as db:
        starts = _all_starts(db)
    if not starts:
        fail("No periods logged yet — start one with: clibo period start",
             json_out=json_out)
    avg_cycle, cycles = _avg_cycle(starts)
    last_start = starts[-1]
    next_start = last_start + timedelta(days=avg_cycle)
    ovulation = next_start - timedelta(days=LUTEAL_PHASE_DAYS)
    data = {
        "last_start": last_start,
        "avg_cycle_days": avg_cycle,
        "cycles_observed": cycles,
        "next_predicted_start": next_start,
        "days_until_next": (next_start - date.today()).days,
        "estimated_ovulation": ovulation,
        "fertile_window_start": ovulation - timedelta(days=4),
        "fertile_window_end": ovulation + timedelta(days=1),
        "estimate_basis": "logged history" if cycles else f"default {DEFAULT_CYCLE_DAYS}-day cycle",
    }
    render_record(data, json_out=json_out, title="🔮 Period prediction")


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Cycle and period-length statistics."""
    with session() as db:
        entries = list(db.exec(select(PeriodLog).order_by(PeriodLog.start_date)).all())
    if not entries:
        fail("No periods logged yet", json_out=json_out)
    starts = [e.start_date for e in entries]
    gaps = [(starts[i + 1] - starts[i]).days for i in range(len(starts) - 1)]
    lengths = [length for e in entries if (length := _length(e)) is not None]
    data = {
        "periods_logged": len(entries),
        "avg_cycle_days": round(sum(gaps) / len(gaps), 1) if gaps else None,
        "shortest_cycle_days": min(gaps) if gaps else None,
        "longest_cycle_days": max(gaps) if gaps else None,
        "avg_period_length_days": round(sum(lengths) / len(lengths), 1) if lengths else None,
    }
    render_record(data, json_out=json_out, title="📊 Period stats")
