"""📦 packages — shipment & parcel tracker.

The daily-driver view is ``packages pending`` — what's still on its way.
Records the tracking number, carrier, sender, expected vs received dates,
and a status that progresses from `ordered` → `in_transit` → `delivered`
(or branches to `lost` / `returned`).

Distinct from `bills` (recurring money out), `events` (one-off dates with
no logistical state), `wishlist` (things you want to buy, not things in
transit). The schema is shaped specifically for the "where's my order?"
question.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import humanize_delta, parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "packages"
HELP = "📦 Shipment & parcel tracker"
EMOJI = "📦"

CARRIERS = [
    "usps", "ups", "fedex", "dhl", "amazon", "royal-mail",
    "deutsche-post", "la-poste", "other",
]
STATUSES = ["ordered", "in_transit", "delivered", "lost", "returned"]


class Package(SQLModel, table=True):
    """One shipment in flight, delivered, or otherwise resolved."""

    __tablename__ = "package_entry"

    id: int | None = Field(default=None, primary_key=True)
    sender: str                                 # e.g. "Amazon", "Best Buy"
    description: str | None = None              # what's inside
    tracking_number: str | None = None
    carrier: str | None = None                  # free text, suggested set above
    ordered_date: date = Field(default_factory=date.today)
    expected_date: date | None = None
    received_date: date | None = None
    status: str = "ordered"                     # ordered / in_transit / delivered / lost / returned
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(pkg: Package) -> dict:
    today = date.today()
    days_outstanding: int | None
    days_outstanding = None
    if pkg.status not in ("delivered", "lost", "returned"):
        days_outstanding = (today - pkg.ordered_date).days
    is_late = (
        pkg.expected_date is not None
        and pkg.received_date is None
        and pkg.status not in ("delivered", "lost", "returned")
        and pkg.expected_date < today
    )
    return {
        "id": pkg.id,
        "sender": pkg.sender,
        "description": pkg.description,
        "tracking_number": pkg.tracking_number,
        "carrier": pkg.carrier,
        "ordered_date": pkg.ordered_date,
        "expected_date": pkg.expected_date,
        "expected_in": (
            humanize_delta(pkg.expected_date) if pkg.expected_date else None
        ),
        "received_date": pkg.received_date,
        "status": pkg.status,
        "days_outstanding": days_outstanding,
        "is_late": is_late,
        "note": pkg.note,
    }


@app.command()
def add(
    sender: str = typer.Argument(..., help="Sender / retailer (e.g. 'Amazon')"),
    tracking: str = typer.Option(None, "--tracking", "-t",
                                  help="Tracking number"),
    carrier: str = typer.Option(None, "--carrier", "-c",
                                 help=f"Carrier (free text; suggested: "
                                      f"{', '.join(CARRIERS)})"),
    description: str = typer.Option(None, "--desc", "-D",
                                     help="What's inside (e.g. 'Mechanical keyboard')"),
    ordered: str = typer.Option("today", "--ordered",
                                 help="Date the order was placed"),
    expected: str = typer.Option(None, "--expected", "-e",
                                  help="Expected delivery date"),
    status: str = typer.Option("ordered", "--status", "-s",
                                help=f"Initial status, one of: "
                                     f"{', '.join(STATUSES)}"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """📦 Register a new package / order."""
    status_lc = status.lower()
    if status_lc not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}",
             json_out=json_out)
    pkg = Package(
        sender=sender.strip(),
        tracking_number=tracking,
        carrier=carrier.lower().strip() if carrier else None,
        description=description,
        ordered_date=parse_date(ordered),
        expected_date=parse_date(expected) if expected else None,
        status=status_lc,
        note=note,
    )
    with session() as db:
        db.add(pkg)
        db.flush()
        db.refresh(pkg)
        data = _row(pkg)
    when = f" — expected {data['expected_in']}" if pkg.expected_date else ""
    ok(f"Added {EMOJI} package from {sender}{when}",
       json_out=json_out, data=data)


# `log` is a friendlier alias for `add` — agents naturally say "log a package".
app.command(name="log", help="Alias for `add`")(add)


@app.command()
def update(
    pkg_id: int = typer.Argument(..., help="Package ID"),
    status: str = typer.Option(None, "--status", "-s",
                                help=f"New status: {', '.join(STATUSES)}"),
    expected: str = typer.Option(None, "--expected", "-e",
                                  help="Updated expected delivery"),
    tracking: str = typer.Option(None, "--tracking", "-t",
                                  help="Updated tracking number"),
    carrier: str = typer.Option(None, "--carrier", "-c", help="Updated carrier"),
    note: str = typer.Option(None, "--note", "-n", help="Replace note"),
    json_out: JsonOpt = False,
) -> None:
    """📦 Update a package's status, ETA, tracking number or note."""
    with session() as db:
        pkg = db.get(Package, pkg_id)
        if not pkg:
            fail(f"No package #{pkg_id}", json_out=json_out)
        if status is not None:
            if status.lower() not in STATUSES:
                fail(f"Status must be one of: {', '.join(STATUSES)}",
                     json_out=json_out)
            pkg.status = status.lower()
        if expected is not None:
            pkg.expected_date = parse_date(expected)
        if tracking is not None:
            pkg.tracking_number = tracking
        if carrier is not None:
            pkg.carrier = carrier.lower().strip()
        if note is not None:
            pkg.note = note
        db.add(pkg)
        db.flush()
        db.refresh(pkg)
        data = _row(pkg)
    ok(f"Updated package #{pkg_id}", json_out=json_out, data=data)


@app.command()
def received(
    pkg_id: int = typer.Argument(..., help="Package ID"),
    on: str = typer.Option("today", "--date", "-d", help="Delivery date"),
    json_out: JsonOpt = False,
) -> None:
    """✅ Mark a package as delivered."""
    with session() as db:
        pkg = db.get(Package, pkg_id)
        if not pkg:
            fail(f"No package #{pkg_id}", json_out=json_out)
        pkg.status = "delivered"
        pkg.received_date = parse_date(on)
        db.add(pkg)
        db.flush()
        db.refresh(pkg)
        data = _row(pkg)
    ok(f"Received {EMOJI} package #{pkg_id} from {pkg.sender}",
       json_out=json_out, data=data)


@app.command()
def pending(
    show_late_only: bool = typer.Option(False, "--late",
                                         help="Only show late packages"),
    json_out: JsonOpt = False,
) -> None:
    """📦 Packages not yet delivered — the daily-driver view."""
    today = date.today()
    with session() as db:
        query = select(Package).where(
            Package.status.in_(["ordered", "in_transit"])
        )
        pkgs = list(db.exec(query).all())
    rows = [_row(p) for p in pkgs]
    if show_late_only:
        rows = [r for r in rows if r["is_late"]]
    # sort: late first, then by expected date ascending (None last),
    # then by ordered date.
    rows.sort(key=lambda r: (
        not r["is_late"],
        r["expected_date"] or date.max,
        r["ordered_date"],
    ))
    render_rows(
        rows,
        [("id", "ID"), ("sender", "From"), ("description", "Item"),
         ("carrier", "Carrier"), ("expected_in", "Expected"),
         ("is_late", "Late?"), ("tracking_number", "Tracking")],
        json_out=json_out,
        title="📦 Pending packages" + (" · late only" if show_late_only else ""),
        empty="[green]No packages on the way.[/green]",
        formatters={
            "is_late": lambda v, r: "[red]⚠[/red]" if v else "[dim]·[/dim]",
        },
    )
    if not json_out and not rows:
        return
    _ = today  # kept for future formatting hooks


@app.command(name="list")
def list_packages(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    carrier: str = typer.Option(None, "--carrier", "-c", help="Filter by carrier"),
    show_all: bool = typer.Option(False, "--all", "-a",
                                   help="Include delivered/returned/lost"),
    json_out: JsonOpt = False,
) -> None:
    """📦 List packages (active by default; `--all` to include resolved)."""
    with session() as db:
        query = select(Package)
        if status:
            if status.lower() not in STATUSES:
                fail(f"Status must be one of: {', '.join(STATUSES)}",
                     json_out=json_out)
            query = query.where(Package.status == status.lower())
        elif not show_all:
            query = query.where(
                Package.status.in_(["ordered", "in_transit"])
            )
        if carrier:
            query = query.where(Package.carrier == carrier.lower().strip())
        pkgs = list(
            db.exec(query.order_by(Package.ordered_date.desc())).all()
        )
    render_rows(
        [_row(p) for p in pkgs],
        [("id", "ID"), ("sender", "From"), ("description", "Item"),
         ("carrier", "Carrier"), ("ordered_date", "Ordered"),
         ("expected_date", "Expected"), ("status", "Status")],
        json_out=json_out,
        title="📦 Packages",
        empty="No packages yet — try: clibo packages add 'Amazon' -t TRACKING -e 'in 3 days'",
    )


@app.command()
def show(
    pkg_id: int = typer.Argument(..., help="Package ID"),
    json_out: JsonOpt = False,
) -> None:
    """📦 Show one package in full detail."""
    with session() as db:
        pkg = db.get(Package, pkg_id)
        if not pkg:
            fail(f"No package #{pkg_id}", json_out=json_out)
        data = _row(pkg)
    render_record(data, json_out=json_out, title=f"{EMOJI} Package #{pkg_id}")


@app.command()
def rm(
    pkg_id: int = typer.Argument(..., help="Package ID"),
    json_out: JsonOpt = False,
) -> None:
    """📦 Delete a package entry."""
    with session() as db:
        pkg = db.get(Package, pkg_id)
        if not pkg:
            fail(f"No package #{pkg_id}", json_out=json_out)
        db.delete(pkg)
    ok(f"Deleted package #{pkg_id}",
       json_out=json_out, data={"deleted": pkg_id})


@app.command()
def stats(
    days: int = typer.Option(90, "--days", help="Window for delivery times"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Package stats — by status, by carrier, on-time vs late."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        pkgs = list(db.exec(select(Package)).all())
    if not pkgs:
        fail("No packages yet", json_out=json_out)
    by_status = dict(Counter(p.status for p in pkgs))
    by_carrier = dict(Counter(p.carrier for p in pkgs if p.carrier))
    delivered_in_window = [
        p for p in pkgs
        if p.status == "delivered"
        and p.received_date is not None
        and p.received_date >= since
    ]
    avg_delivery_days: float | None = None
    if delivered_in_window:
        deltas = [
            (p.received_date - p.ordered_date).days
            for p in delivered_in_window
        ]
        avg_delivery_days = round(sum(deltas) / len(deltas), 1)
    on_time = sum(
        1 for p in delivered_in_window
        if p.expected_date is None or p.received_date <= p.expected_date
    )
    late_arrivals = len(delivered_in_window) - on_time
    data = {
        "total": len(pkgs),
        "by_status": by_status,
        "by_carrier": by_carrier,
        "delivered_in_window": len(delivered_in_window),
        "avg_delivery_days": avg_delivery_days,
        "on_time": on_time,
        "late_arrivals": late_arrivals,
        "currently_pending": sum(
            1 for p in pkgs if p.status in ("ordered", "in_transit")
        ),
    }
    render_record(data, json_out=json_out, title="📊 Package stats")
