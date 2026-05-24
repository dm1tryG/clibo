"""📄 invoice — freelance invoice generator."""

from __future__ import annotations

from datetime import date, datetime

import typer
from rich.box import ROUNDED
from rich.panel import Panel
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows
from clibo.core.settings import get_setting, set_setting

NAME = "invoice"
HELP = "📄 Freelance invoice generator"
EMOJI = "📄"
STATUSES = ["draft", "sent", "paid"]


class Invoice(SQLModel, table=True):
    """A freelance invoice for one client."""

    __tablename__ = "invoice_invoice"

    id: int | None = Field(default=None, primary_key=True)
    number: str
    client: str
    description: str | None = None
    amount: float
    tax_pct: float = 0.0
    issued: date = Field(default_factory=date.today)
    due: date | None = None
    status: str = "draft"
    paid_date: date | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo invoice`` (bare) lists every invoice."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_invoices, status=None, json_out=json_out)


def _next_number() -> str:
    """Generate the next sequential invoice number (INV-0001, ...)."""
    nxt = int(get_setting(NAME, "counter", "0") or "0") + 1
    set_setting(NAME, "counter", str(nxt))
    return f"INV-{nxt:04d}"


def _total(inv: Invoice) -> float:
    """Invoice total including tax."""
    return round(inv.amount * (1 + inv.tax_pct / 100), 2)


def _row(inv: Invoice) -> dict:
    return {
        "id": inv.id,
        "number": inv.number,
        "client": inv.client,
        "description": inv.description,
        "amount": inv.amount,
        "tax_pct": inv.tax_pct,
        "total": _total(inv),
        "issued": inv.issued,
        "due": inv.due,
        "status": inv.status,
        "paid_date": inv.paid_date,
        "note": inv.note,
    }


@app.command()
def add(
    client: str = typer.Argument(..., help="Client name"),
    amount: float = typer.Option(..., "--amount", "-a", help="Invoice subtotal"),
    description: str = typer.Option(None, "--desc", "-D", help="What the invoice is for"),
    tax: float = typer.Option(0, "--tax", help="Tax percentage"),
    due: str = typer.Option(None, "--due", help="Due date"),
    issued: str = typer.Option("today", "--issued", help="Issue date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """📄 Create a new invoice (draft)."""
    if amount <= 0:
        fail("Amount must be positive", json_out=json_out)
    if tax < 0:
        fail("Tax cannot be negative", json_out=json_out)
    number = _next_number()
    inv = Invoice(
        number=number, client=client, description=description, amount=amount,
        tax_pct=tax, issued=parse_date(issued),
        due=parse_date(due) if due else None, note=note,
    )
    with session() as db:
        db.add(inv)
        db.flush()
        db.refresh(inv)
        data = _row(inv)
    ok(f"Created {EMOJI} {number} for {client} — {money(data['total'])}",
       json_out=json_out, data=data)


@app.command(name="list")
def list_invoices(
    status: str = typer.Option(None, "--status", "-s", help=f"Filter: {', '.join(STATUSES)}"),
    json_out: JsonOpt = False,
) -> None:
    """📄 List invoices."""
    if status and status.lower() not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    with session() as db:
        query = select(Invoice)
        if status:
            query = query.where(Invoice.status == status.lower())
        invoices = list(db.exec(query.order_by(Invoice.issued.desc(), Invoice.id.desc())).all())
    render_rows(
        [_row(i) for i in invoices],
        [("number", "Number"), ("client", "Client"), ("total", "Total"),
         ("issued", "Issued"), ("due", "Due"), ("status", "Status")],
        json_out=json_out,
        title="📄 Invoices",
        formatters={
            "total": lambda v, r: money(v),
            "status": lambda v, r: {
                "draft": "[dim]draft[/dim]",
                "sent": "[cyan]sent[/cyan]",
                "paid": "[green]✓ paid[/green]",
            }.get(v, v),
        },
        empty="No invoices yet — try: clibo invoice add 'Acme Inc' -a 1200",
    )


@app.command()
def show(invoice_id: int = typer.Argument(..., help="Invoice ID"), json_out: JsonOpt = False) -> None:
    """📄 Show one invoice."""
    with session() as db:
        inv = db.get(Invoice, invoice_id)
        if not inv:
            fail(f"No invoice #{invoice_id}", json_out=json_out)
        data = _row(inv)
    render_record(data, json_out=json_out, title=f"📄 {data['number']}")


@app.command()
def render(invoice_id: int = typer.Argument(..., help="Invoice ID"), json_out: JsonOpt = False) -> None:
    """🧾 Render a formatted invoice document."""
    with session() as db:
        inv = db.get(Invoice, invoice_id)
        if not inv:
            fail(f"No invoice #{invoice_id}", json_out=json_out)
        data = _row(inv)
    if json_out:
        render_record(data, json_out=True)
        return
    tax_line = (f"\n  Tax ({inv.tax_pct:g}%)         {money(data['total'] - inv.amount):>14}"
                if inv.tax_pct else "")
    body = (
        f"[bold cyan]INVOICE {inv.number}[/bold cyan]\n\n"
        f"  Billed to     [bold]{inv.client}[/bold]\n"
        f"  Issued        {inv.issued}\n"
        f"  Due           {inv.due or '—'}\n"
        f"  Status        {inv.status}\n\n"
        f"  [dim]{inv.description or 'Services rendered'}[/dim]\n\n"
        f"  Subtotal          {money(inv.amount):>14}"
        f"{tax_line}\n"
        f"  [bold]Total             {money(data['total']):>14}[/bold]"
    )
    console.print(Panel(body, border_style="cyan", box=ROUNDED, title="🧾 clibo invoice",
                        title_align="left", padding=(1, 2)))


@app.command()
def send(invoice_id: int = typer.Argument(..., help="Invoice ID"), json_out: JsonOpt = False) -> None:
    """📤 Mark an invoice as sent."""
    with session() as db:
        inv = db.get(Invoice, invoice_id)
        if not inv:
            fail(f"No invoice #{invoice_id}", json_out=json_out)
        inv.status = "sent"
        db.add(inv)
        db.flush()
        data = _row(inv)
    ok(f"Marked {inv.number} as sent", json_out=json_out, data=data)


@app.command()
def pay(
    invoice_id: int = typer.Argument(..., help="Invoice ID"),
    on: str = typer.Option("today", "--date", "-d", help="Date paid"),
    json_out: JsonOpt = False,
) -> None:
    """💵 Mark an invoice as paid."""
    with session() as db:
        inv = db.get(Invoice, invoice_id)
        if not inv:
            fail(f"No invoice #{invoice_id}", json_out=json_out)
        inv.status = "paid"
        inv.paid_date = parse_date(on)
        db.add(inv)
        db.flush()
        data = _row(inv)
    ok(f"Marked {inv.number} as paid 🎉", json_out=json_out, data=data)


@app.command()
def rm(invoice_id: int = typer.Argument(..., help="Invoice ID"), json_out: JsonOpt = False) -> None:
    """📄 Delete an invoice."""
    with session() as db:
        inv = db.get(Invoice, invoice_id)
        if not inv:
            fail(f"No invoice #{invoice_id}", json_out=json_out)
        db.delete(inv)
    ok(f"Deleted invoice #{invoice_id}", json_out=json_out, data={"deleted": invoice_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Invoice stats — billed, paid and outstanding."""
    with session() as db:
        invoices = list(db.exec(select(Invoice)).all())
    paid = [i for i in invoices if i.status == "paid"]
    outstanding = [i for i in invoices if i.status != "paid"]
    data = {
        "invoices": len(invoices),
        "total_billed": round(sum(_total(i) for i in invoices), 2),
        "total_paid": round(sum(_total(i) for i in paid), 2),
        "total_outstanding": round(sum(_total(i) for i in outstanding), 2),
        "paid_count": len(paid),
        "outstanding_count": len(outstanding),
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Invoice stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
