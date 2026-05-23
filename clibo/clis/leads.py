"""🧲 leads — sales pipeline & deals."""

from __future__ import annotations

from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, console, fail, ok, render_record, render_rows

NAME = "leads"
HELP = "🧲 Sales pipeline & deals"
EMOJI = "🧲"

STAGES = ["new", "contacted", "qualified", "proposal", "won", "lost"]
OPEN_STAGES = ["new", "contacted", "qualified", "proposal"]


class Lead(SQLModel, table=True):
    """A sales deal moving through the pipeline."""

    __tablename__ = "leads_lead"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    contact: str | None = None
    value: float = 0.0
    stage: str = "new"
    expected_close: date | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(lead: Lead) -> dict:
    return {
        "id": lead.id,
        "name": lead.name,
        "contact": lead.contact,
        "value": lead.value,
        "stage": lead.stage,
        "expected_close": lead.expected_close,
        "notes": lead.notes,
    }


def _stage_cell(stage: str) -> str:
    return {
        "new": "[white]new[/white]",
        "contacted": "[cyan]contacted[/cyan]",
        "qualified": "[blue]qualified[/blue]",
        "proposal": "[yellow]proposal[/yellow]",
        "won": "[green]✓ won[/green]",
        "lost": "[red]✗ lost[/red]",
    }.get(stage, stage)


@app.command()
def add(
    name: str = typer.Argument(..., help="Deal name"),
    value: float = typer.Option(0, "--value", "-v", help="Deal value"),
    contact: str = typer.Option(None, "--contact", "-c", help="Person or company"),
    stage: str = typer.Option("new", "--stage", "-s", help="Pipeline stage"),
    expected_close: str = typer.Option(None, "--close", help="Expected close date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🧲 Add a deal to the pipeline."""
    stage = stage.lower()
    if stage not in STAGES:
        fail(f"Stage must be one of: {', '.join(STAGES)}", json_out=json_out)
    if value < 0:
        fail("Value cannot be negative", json_out=json_out)
    lead = Lead(
        name=name, value=value, contact=contact, stage=stage,
        expected_close=parse_date(expected_close) if expected_close else None, notes=note,
    )
    with session() as db:
        db.add(lead)
        db.flush()
        db.refresh(lead)
        data = _row(lead)
    ok(f"Added {EMOJI} deal '{name}' — {money(value)} ({stage})", json_out=json_out, data=data)


@app.command(name="list")
def list_leads(
    stage: str = typer.Option(None, "--stage", "-s", help="Filter by stage"),
    json_out: JsonOpt = False,
) -> None:
    """🧲 List deals."""
    if stage and stage.lower() not in STAGES:
        fail(f"Stage must be one of: {', '.join(STAGES)}", json_out=json_out)
    with session() as db:
        query = select(Lead)
        if stage:
            query = query.where(Lead.stage == stage.lower())
        leads = list(db.exec(query.order_by(Lead.value.desc())).all())
    render_rows(
        [_row(deal) for deal in leads],
        [("id", "ID"), ("name", "Deal"), ("contact", "Contact"),
         ("value", "Value"), ("stage", "Stage"), ("expected_close", "Close")],
        json_out=json_out,
        title="🧲 Deals",
        formatters={
            "value": lambda v, r: money(v),
            "stage": lambda v, r: _stage_cell(v),
        },
        empty="No deals yet — try: clibo leads add 'Acme contract' -v 5000",
    )


def _resolve_lead(db, ident: str) -> Lead | None:
    from clibo.core.base import lookup_by_id_or_name
    return lookup_by_id_or_name(db, Lead, ident, Lead.name)


@app.command()
def show(
    lead: str = typer.Argument(..., help="Deal ID or name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🧲 Show one deal. Accepts a numeric ID or a name."""
    with session() as db:
        target = _resolve_lead(db, lead)
        if not target:
            fail(f"No deal matching {lead!r}", json_out=json_out)
        data = _row(target) | {"created_at": target.created_at}
    render_record(data, json_out=json_out, title=f"🧲 {data['name']}")


@app.command()
def move(
    lead: str = typer.Argument(..., help="Deal ID or name (fuzzy)"),
    stage: str = typer.Argument(..., help=f"New stage: {', '.join(STAGES)}"),
    json_out: JsonOpt = False,
) -> None:
    """🧲 Move a deal to a new pipeline stage."""
    stage = stage.lower()
    if stage not in STAGES:
        fail(f"Stage must be one of: {', '.join(STAGES)}", json_out=json_out)
    with session() as db:
        target = _resolve_lead(db, lead)
        if not target:
            fail(f"No deal matching {lead!r}", json_out=json_out)
        target.stage = stage
        db.add(target)
        db.flush()
        data = _row(target)
    flair = " 🎉" if stage == "won" else ""
    ok(f"Moved '{target.name}' to {stage}{flair}", json_out=json_out, data=data)


@app.command()
def edit(
    lead: str = typer.Argument(..., help="Deal ID or name (fuzzy)"),
    name: str = typer.Option(None, "--name", help="New name"),
    value: float = typer.Option(None, "--value", "-v", help="New value"),
    contact: str = typer.Option(None, "--contact", "-c"),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """🧲 Edit a deal. Accepts a numeric ID or a name."""
    with session() as db:
        target = _resolve_lead(db, lead)
        if not target:
            fail(f"No deal matching {lead!r}", json_out=json_out)
        if name is not None:
            target.name = name
        if value is not None:
            target.value = value
        if contact is not None:
            target.contact = contact
        if note is not None:
            target.notes = note
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Updated deal #{target.id}", json_out=json_out, data=data)


@app.command()
def rm(
    lead: str = typer.Argument(..., help="Deal ID or name (fuzzy)"),
    json_out: JsonOpt = False,
) -> None:
    """🧲 Delete a deal."""
    with session() as db:
        target = _resolve_lead(db, lead)
        if not target:
            fail(f"No deal matching {lead!r}", json_out=json_out)
        lid = target.id
        db.delete(target)
    ok(f"Deleted deal #{lid}", json_out=json_out, data={"deleted": lid})


@app.command()
def pipeline(json_out: JsonOpt = False) -> None:
    """📊 The pipeline: open deals grouped by stage."""
    with session() as db:
        leads = list(db.exec(select(Lead)).all())
    by_stage = {
        s: {"deals": sum(1 for x in leads if x.stage == s),
            "value": round(sum(x.value for x in leads if x.stage == s), 2)}
        for s in OPEN_STAGES
    }
    open_value = round(sum(g["value"] for g in by_stage.values()), 2)
    rows = [{"stage": s, **by_stage[s]} for s in OPEN_STAGES]
    if json_out:
        render_record(
            {"by_stage": rows, "open_value": open_value, "currency": get_currency()},
            json_out=True,
        )
        return
    render_rows(
        rows,
        [("stage", "Stage"), ("deals", "Deals"), ("value", "Value")],
        json_out=False,
        title="📊 Pipeline",
        formatters={
            "stage": lambda v, r: _stage_cell(v),
            "value": lambda v, r: f"{money(v)}  {bar(v, open_value or 1, width=16)}",
        },
        empty="No open deals.",
    )
    console.print(f"  💰 [bold]Open pipeline value:[/bold] {money(open_value)}")


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Pipeline stats — values and win rate."""
    with session() as db:
        leads = list(db.exec(select(Lead)).all())
    won = [d for d in leads if d.stage == "won"]
    lost = [d for d in leads if d.stage == "lost"]
    open_deals = [d for d in leads if d.stage in OPEN_STAGES]
    closed = len(won) + len(lost)
    data = {
        "total_deals": len(leads),
        "open_deals": len(open_deals),
        "open_value": round(sum(d.value for d in open_deals), 2),
        "won_deals": len(won),
        "won_value": round(sum(d.value for d in won), 2),
        "lost_deals": len(lost),
        "win_rate_pct": round(len(won) / closed * 100, 1) if closed else 0.0,
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Pipeline stats")
