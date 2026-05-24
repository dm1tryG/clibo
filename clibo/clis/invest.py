"""📈 invest — investment positions with cost basis and unrealized P/L.

Distinct from `networth` (single value per asset row) — this stores
*transactions* (buys + sells, with shares and price per share), then derives
current positions and computes unrealized P/L against the latest known price
the user has typed in.

The intentional scope limit: no live price feeds — clibo is local-first
and stays so. You update the current price with `price TICKER X` whenever
you want a fresh P/L number.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.clis.expense import get_currency, money
from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "invest"
HELP = "📈 Investment positions — cost basis + unrealized P/L"
EMOJI = "📈"

KINDS = ["stock", "etf", "crypto", "bond", "fund", "other"]
ACTIONS = ["buy", "sell"]


class Transaction(SQLModel, table=True):
    """One buy or sell event."""

    __tablename__ = "invest_transaction"

    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    kind: str = "stock"          # stock / etf / crypto / bond / fund / other
    action: str = "buy"          # buy or sell
    shares: float
    price_per_share: float
    txn_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    note: str | None = None


class LatestPrice(SQLModel, table=True):
    """The last manually-entered current price for a ticker."""

    __tablename__ = "invest_latest_price"

    ticker: str = Field(primary_key=True)
    price: float
    updated_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(txn: Transaction) -> dict:
    return {
        "id": txn.id,
        "ticker": txn.ticker,
        "kind": txn.kind,
        "action": txn.action,
        "shares": txn.shares,
        "price_per_share": txn.price_per_share,
        "total": round(txn.shares * txn.price_per_share, 2),
        "txn_date": txn.txn_date,
        "note": txn.note,
    }


def _position(txns: list[Transaction]) -> dict:
    """Compute the net position from a list of transactions for one ticker.

    Uses average cost basis (the simplest defensible approach for an MVP).
    A more sophisticated FIFO/specific-lot model could come later.
    """
    if not txns:
        return {
            "shares": 0.0, "avg_cost": 0.0, "cost_basis": 0.0,
            "realized_pl": 0.0,
        }
    ticker = txns[0].ticker
    kind = txns[0].kind
    # Sort chronologically so the running average reflects buy order.
    txns_sorted = sorted(txns, key=lambda t: (t.txn_date, t.id or 0))
    shares = 0.0
    cost_basis = 0.0   # sum of (shares × price) for buys, less proportional sells
    realized_pl = 0.0
    for txn in txns_sorted:
        if txn.action == "buy":
            shares += txn.shares
            cost_basis += txn.shares * txn.price_per_share
        else:  # sell
            if shares <= 0:
                # Can't sell what you don't have; record as a realized loss
                # equal to proceeds for safety. In practice the validator
                # below prevents this from happening.
                realized_pl += txn.shares * txn.price_per_share
                continue
            avg_cost = cost_basis / shares
            sold_basis = avg_cost * txn.shares
            realized_pl += txn.shares * txn.price_per_share - sold_basis
            shares -= txn.shares
            cost_basis -= sold_basis
    avg_cost = round(cost_basis / shares, 4) if shares > 0 else 0.0
    return {
        "ticker": ticker,
        "kind": kind,
        "shares": round(shares, 6),
        "avg_cost": avg_cost,
        "cost_basis": round(cost_basis, 2),
        "realized_pl": round(realized_pl, 2),
    }


def _enrich_with_price(db, pos: dict) -> dict:
    """Add `current_price`, `market_value`, `unrealized_pl` if a price is known."""
    latest = db.get(LatestPrice, pos["ticker"])
    if latest is None or pos["shares"] <= 0:
        return {**pos, "current_price": None,
                "market_value": None, "unrealized_pl": None}
    market_value = round(latest.price * pos["shares"], 2)
    unrealized = round(market_value - pos["cost_basis"], 2)
    return {
        **pos,
        "current_price": latest.price,
        "current_price_updated_at": latest.updated_at,
        "market_value": market_value,
        "unrealized_pl": unrealized,
    }


def _validate(action: str, kind: str, shares: float, price: float,
              json_out: bool) -> None:
    if action not in ACTIONS:
        fail(f"Action must be one of: {', '.join(ACTIONS)}", json_out=json_out)
    if kind.lower() not in KINDS:
        fail(f"Kind must be one of: {', '.join(KINDS)}", json_out=json_out)
    if shares <= 0:
        fail("Shares must be positive", json_out=json_out)
    if price < 0:
        fail("Price cannot be negative", json_out=json_out)


@app.command()
def buy(
    ticker: str = typer.Argument(..., help="Ticker symbol, e.g. AAPL"),
    shares: float = typer.Argument(..., help="Number of shares (fractional ok)"),
    price: float = typer.Argument(..., help="Price per share at purchase"),
    kind: str = typer.Option("stock", "--kind", "-k",
                              help=f"One of: {', '.join(KINDS)}"),
    on: str = typer.Option("today", "--date", "-d", help="Trade date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """📈 Log a purchase (buy)."""
    _validate("buy", kind, shares, price, json_out)
    ticker = ticker.upper()
    txn = Transaction(
        ticker=ticker, kind=kind.lower(), action="buy",
        shares=shares, price_per_share=price,
        txn_date=parse_date(on), note=note,
    )
    with session() as db:
        db.add(txn)
        db.flush()
        db.refresh(txn)
        data = _row(txn)
    ok(f"Bought {EMOJI} {shares:g} {ticker} @ {money(price)} "
       f"(total {money(data['total'])})",
       json_out=json_out, data=data)


@app.command()
def sell(
    ticker: str = typer.Argument(..., help="Ticker symbol"),
    shares: float = typer.Argument(..., help="Shares sold"),
    price: float = typer.Argument(..., help="Price per share at sale"),
    on: str = typer.Option("today", "--date", "-d", help="Trade date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """📉 Log a sale — computes realized P/L using average cost basis."""
    _validate("sell", "stock", shares, price, json_out)  # kind irrelevant for sells
    ticker = ticker.upper()
    with session() as db:
        # Check there are enough shares to sell.
        existing = list(
            db.exec(select(Transaction).where(Transaction.ticker == ticker)).all()
        )
        pos = _position(existing)
        if shares > pos["shares"]:
            fail(
                f"Can't sell {shares:g} {ticker}: only {pos['shares']:g} in "
                f"your position",
                json_out=json_out,
            )
        # Reuse the kind from prior buys for consistency in stats.
        kind = pos["kind"] if existing else "stock"
        txn = Transaction(
            ticker=ticker, kind=kind, action="sell",
            shares=shares, price_per_share=price,
            txn_date=parse_date(on), note=note,
        )
        db.add(txn)
        db.flush()
        db.refresh(txn)
        # Compute realized P/L for this sale specifically for the success line.
        per_share_basis = pos["avg_cost"]
        pl = round((price - per_share_basis) * shares, 2)
        data = _row(txn) | {
            "realized_pl_this_sale": pl,
            "remaining_shares": round(pos["shares"] - shares, 6),
        }
    pl_str = (f" · realized P/L {money(pl)}" if per_share_basis else "")
    ok(f"Sold {EMOJI} {shares:g} {ticker} @ {money(price)}{pl_str}",
       json_out=json_out, data=data)


@app.command()
def price(
    ticker: str = typer.Argument(..., help="Ticker symbol"),
    price: float = typer.Argument(..., help="Current market price per share"),
    json_out: JsonOpt = False,
) -> None:
    """💲 Update the current market price for a ticker (drives unrealized P/L)."""
    if price < 0:
        fail("Price cannot be negative", json_out=json_out)
    ticker = ticker.upper()
    now = datetime.now()
    with session() as db:
        existing = db.get(LatestPrice, ticker)
        if existing:
            existing.price = price
            existing.updated_at = now
            db.add(existing)
        else:
            db.add(LatestPrice(ticker=ticker, price=price, updated_at=now))
    ok(f"Price of {ticker} = {money(price)}",
       json_out=json_out,
       data={"ticker": ticker, "price": price, "updated_at": now})


@app.command()
def positions(json_out: JsonOpt = False) -> None:
    """📊 Current holdings (rolled up across all transactions)."""
    with session() as db:
        all_txns = list(db.exec(select(Transaction)).all())
        by_ticker: dict[str, list[Transaction]] = {}
        for txn in all_txns:
            by_ticker.setdefault(txn.ticker, []).append(txn)
        rows = []
        for ticker, txns in sorted(by_ticker.items()):
            pos = _position(txns)
            if pos["shares"] <= 0:
                continue  # fully sold positions don't show in positions
            rows.append(_enrich_with_price(db, pos))
    render_rows(
        rows,
        [("ticker", "Ticker"), ("kind", "Kind"), ("shares", "Shares"),
         ("avg_cost", "Avg cost"), ("cost_basis", "Basis"),
         ("current_price", "Price"), ("market_value", "Value"),
         ("unrealized_pl", "Unrealized")],
        json_out=json_out,
        title=f"{EMOJI} Positions",
        empty=("No positions yet — try: clibo invest buy AAPL 5 200"),
        formatters={
            "avg_cost": lambda v, r: money(v),
            "cost_basis": lambda v, r: money(v),
            "current_price": lambda v, r: money(v) if v is not None else "[dim]—[/dim]",
            "market_value": lambda v, r: money(v) if v is not None else "[dim]—[/dim]",
            "unrealized_pl": lambda v, r: (
                "[dim]—[/dim]" if v is None else
                f"[green]{money(v)}[/green]" if v >= 0 else
                f"[red]{money(v)}[/red]"
            ),
        },
    )


@app.command()
def history(
    ticker: str = typer.Option(None, "--ticker", "-t", help="Filter by ticker"),
    days: int = typer.Option(365, "--days", help="Look back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """📜 Transaction history (newest first)."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        query = select(Transaction).where(Transaction.txn_date >= since)
        if ticker:
            query = query.where(Transaction.ticker == ticker.upper())
        txns = list(
            db.exec(query.order_by(Transaction.txn_date.desc(),
                                   Transaction.id.desc())).all()
        )
    render_rows(
        [_row(t) for t in txns],
        [("id", "ID"), ("txn_date", "Date"), ("action", "Action"),
         ("ticker", "Ticker"), ("shares", "Shares"),
         ("price_per_share", "Price"), ("total", "Total"), ("note", "Note")],
        json_out=json_out,
        title=f"{EMOJI} Transactions — last {days}d",
        empty="No transactions in this window.",
        formatters={
            "price_per_share": lambda v, r: money(v),
            "total": lambda v, r: money(v),
        },
    )


@app.command()
def show(
    ticker: str = typer.Argument(..., help="Ticker symbol"),
    json_out: JsonOpt = False,
) -> None:
    """📈 Show one ticker — current position + every transaction."""
    ticker = ticker.upper()
    with session() as db:
        txns = list(
            db.exec(select(Transaction).where(Transaction.ticker == ticker)).all()
        )
        if not txns:
            fail(f"No transactions for {ticker}", json_out=json_out)
        pos = _enrich_with_price(db, _position(txns))
    data = {
        **pos,
        "transactions": [_row(t) for t in
                         sorted(txns, key=lambda t: t.txn_date, reverse=True)],
    }
    render_record(data, json_out=json_out, title=f"{EMOJI} {ticker}")


@app.command()
def rm(
    txn_id: int = typer.Argument(..., help="Transaction ID"),
    json_out: JsonOpt = False,
) -> None:
    """📈 Delete a transaction (use carefully — corrects bookkeeping)."""
    with session() as db:
        txn = db.get(Transaction, txn_id)
        if not txn:
            fail(f"No transaction #{txn_id}", json_out=json_out)
        db.delete(txn)
    ok(f"Deleted transaction #{txn_id}",
       json_out=json_out, data={"deleted": txn_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Portfolio stats — invested, market value, realized + unrealized P/L."""
    with session() as db:
        all_txns = list(db.exec(select(Transaction)).all())
        if not all_txns:
            fail("No transactions yet", json_out=json_out)
        by_ticker: dict[str, list[Transaction]] = {}
        for txn in all_txns:
            by_ticker.setdefault(txn.ticker, []).append(txn)
        positions = [
            _enrich_with_price(db, _position(txns))
            for txns in by_ticker.values()
        ]
    active = [p for p in positions if p["shares"] > 0]
    total_basis = round(sum(p["cost_basis"] for p in active), 2)
    realized = round(sum(p["realized_pl"] for p in positions), 2)
    priced = [p for p in active if p["current_price"] is not None]
    market_value = (round(sum(p["market_value"] for p in priced), 2)
                    if priced else None)
    unrealized = (round(sum(p["unrealized_pl"] for p in priced), 2)
                  if priced else None)
    by_kind: dict[str, float] = {}
    for p in active:
        by_kind[p["kind"]] = round(
            by_kind.get(p["kind"], 0) + p["cost_basis"], 2
        )
    data = {
        "active_positions": len(active),
        "total_invested_basis": total_basis,
        "realized_pl_lifetime": realized,
        "positions_with_current_price": len(priced),
        "market_value": market_value,
        "unrealized_pl": unrealized,
        "by_kind_basis": by_kind,
        "currency": get_currency(),
    }
    render_record(data, json_out=json_out, title="📊 Portfolio")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)
