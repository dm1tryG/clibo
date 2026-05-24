"""``clibo overdue`` — what's already slipped, across every tracker.

The retrospective companion to ``clibo upcoming``. Where upcoming
answers *"what's coming up?"*, overdue answers *"what have I missed?"*.

Pulls from tasks (not done, past due), bills (unpaid, past due),
follow-ups (not done, past due), chores (next-due in the past),
documents (already expired), and packages (expected, not received,
overdue).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from sqlmodel import select

from clibo.clis.bills import Bill
from clibo.clis.chores import Chore, _next_due
from clibo.clis.documents import Document
from clibo.clis.followup import FollowUp
from clibo.clis.packages import Package
from clibo.clis.todo import Task
from clibo.core.db import session
from clibo.core.output import _emit_json, console


@dataclass
class OverdueItem:
    """One thing that's slipped past its due date."""

    kind: str               # task / bill / followup / chore /
                            # document / package
    due: date
    days_overdue: int
    title: str
    detail: str | None = None

    def as_dict(self) -> dict:
        return {
            "kind": self.kind,
            "due": self.due.isoformat(),
            "days_overdue": self.days_overdue,
            "title": self.title,
            "detail": self.detail,
        }


@dataclass
class OverdueSnapshot:
    """Everything past its due date."""

    asof: date
    max_days: int | None
    items: list[OverdueItem]

    def as_dict(self) -> dict:
        by_kind: dict[str, list[OverdueItem]] = defaultdict(list)
        for item in self.items:
            by_kind[item.kind].append(item)
        return {
            "asof": self.asof.isoformat(),
            "max_days": self.max_days,
            "total": len(self.items),
            "by_kind": {
                k: [it.as_dict() for it in items] for k, items in by_kind.items()
            },
            # Flat sorted list — most-overdue first, which mirrors
            # how a human triages: deal with the worst slips first.
            "items": [it.as_dict() for it in self.items],
        }


_KIND_EMOJI = {
    "task": "✅",
    "bill": "💸",
    "followup": "🔔",
    "chore": "🧹",
    "document": "📑",
    "package": "📦",
}


def collect_overdue(max_days: int | None = None) -> OverdueSnapshot:
    """Aggregate everything overdue as of today.

    ``max_days`` (optional) limits to items overdue by no more than
    that many days — useful for "what slipped in the last week?".
    """
    today = date.today()
    cutoff = today - timedelta(days=max_days) if max_days is not None else None
    items: list[OverdueItem] = []

    def _within(due: date) -> bool:
        return cutoff is None or due >= cutoff

    with session() as db:
        # ✅ Tasks past due, not done.
        for t in db.exec(
            select(Task)
            .where(Task.done == False)  # noqa: E712
            .where(Task.due.is_not(None))  # type: ignore[union-attr]
            .where(Task.due < today)
        ).all():
            if _within(t.due):
                items.append(OverdueItem(
                    kind="task", due=t.due,
                    days_overdue=(today - t.due).days,
                    title=t.title, detail=t.priority,
                ))
        # 💸 Bills past due, unpaid.
        for b in db.exec(
            select(Bill)
            .where(Bill.paid == False)  # noqa: E712
            .where(Bill.due_date < today)
        ).all():
            if _within(b.due_date):
                items.append(OverdueItem(
                    kind="bill", due=b.due_date,
                    days_overdue=(today - b.due_date).days,
                    title=b.name, detail=f"{b.amount:g}",
                ))
        # 🔔 Follow-ups past due, not done.
        for f in db.exec(
            select(FollowUp)
            .where(FollowUp.done == False)  # noqa: E712
            .where(FollowUp.due_date < today)
        ).all():
            if _within(f.due_date):
                items.append(OverdueItem(
                    kind="followup", due=f.due_date,
                    days_overdue=(today - f.due_date).days,
                    title=f.person, detail=f.reason,
                ))
        # 🧹 Chores whose next-due slot is already in the past.
        for chore in db.exec(select(Chore)).all():
            nxt = _next_due(chore)
            if nxt < today and _within(nxt):
                items.append(OverdueItem(
                    kind="chore", due=nxt,
                    days_overdue=(today - nxt).days,
                    title=chore.name,
                    detail=f"every {chore.frequency_days}d",
                ))
        # 📑 Documents that have already expired.
        for d in db.exec(
            select(Document).where(Document.expires < today)
        ).all():
            if _within(d.expires):
                items.append(OverdueItem(
                    kind="document", due=d.expires,
                    days_overdue=(today - d.expires).days,
                    title=d.name, detail="expired",
                ))
        # 📦 Packages expected but not received.
        for p in db.exec(
            select(Package)
            .where(Package.received_date.is_(None))  # type: ignore[union-attr]
            .where(Package.expected_date.is_not(None))  # type: ignore[union-attr]
            .where(Package.expected_date < today)
        ).all():
            if _within(p.expected_date):
                title = (
                    f"{p.sender} — {p.description}" if p.description else p.sender
                )
                items.append(OverdueItem(
                    kind="package", due=p.expected_date,
                    days_overdue=(today - p.expected_date).days,
                    title=title, detail=p.carrier,
                ))
    # Most-overdue first — that's how a person reads a list of slips.
    items.sort(key=lambda it: (-it.days_overdue, it.kind, it.title))
    return OverdueSnapshot(asof=today, max_days=max_days, items=items)


def render_overdue(max_days: int | None, json_out: bool) -> None:
    """Print everything past its due date."""
    snap = collect_overdue(max_days=max_days)
    if json_out:
        _emit_json(snap.as_dict())
        return

    if max_days is None:
        header = "Overdue"
    else:
        header = f"Overdue · last {max_days} days"
    console.print(f"\n⚠ [bold red]{header}[/bold red]  [dim]as of {snap.asof}[/dim]\n")
    if not snap.items:
        console.print("  [dim green]Nothing's overdue. Solid. ✨[/dim green]\n")
        return

    # Group by kind so the eye can scan to the right pile.
    by_kind: dict[str, list[OverdueItem]] = defaultdict(list)
    for item in snap.items:
        by_kind[item.kind].append(item)
    # Order kinds by total slip-days descending — worst category first.
    kind_order = sorted(
        by_kind,
        key=lambda k: -sum(it.days_overdue for it in by_kind[k]),
    )
    for kind in kind_order:
        emoji = _KIND_EMOJI.get(kind, "•")
        plural = "s" if len(by_kind[kind]) != 1 else ""
        console.print(
            f"[bold]{emoji} {kind}{plural}[/bold]  "
            f"[dim]· {len(by_kind[kind])}[/dim]"
        )
        for item in by_kind[kind]:
            days = item.days_overdue
            ago = "1 day ago" if days == 1 else f"{days} days ago"
            detail = f"  [dim]({item.detail})[/dim]" if item.detail else ""
            console.print(f"  [red]⚠[/red] {item.title}{detail}  [dim]· {ago}[/dim]")
        console.print()
    console.print(f"  [dim]{len(snap.items)} items overdue total[/dim]\n")
