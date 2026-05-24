"""``clibo upcoming`` — what's on the radar over the next N days.

Sister command to ``clibo today`` (today only) and ``clibo week``
(retrospective last 7 days). Where today is *what's actionable now*
and week is *how the last 7 went*, upcoming is *what's coming up*
across every date-anchored tracker.

Pulls from tasks, bills, events, follow-ups, birthdays, chores,
packages and document expiry — grouped by date so you can scan the
week ahead at a glance.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from sqlmodel import select

from clibo.clis.bills import Bill
from clibo.clis.birthdays import Occasion, _next_occurrence
from clibo.clis.chores import Chore, _next_due
from clibo.clis.documents import Document
from clibo.clis.events import Event
from clibo.clis.followup import FollowUp
from clibo.clis.packages import Package
from clibo.clis.todo import Task
from clibo.core.db import session
from clibo.core.output import _emit_json, console


@dataclass
class UpcomingItem:
    """One thing happening on a future date."""

    kind: str               # task / bill / event / followup / birthday /
                            # chore / package / document
    date: date
    title: str
    detail: str | None = None   # e.g. priority, amount, kind-of-occasion

    def as_dict(self) -> dict:
        return {
            "kind": self.kind,
            "date": self.date.isoformat(),
            "title": self.title,
            "detail": self.detail,
        }


@dataclass
class UpcomingSnapshot:
    """The next-N-days view."""

    days: int
    start: date
    end: date
    items: list[UpcomingItem]

    def as_dict(self) -> dict:
        # Group by date for the JSON shape — agents typically want
        # "what's on each day", not a flat sorted list.
        by_date: dict[date, list[UpcomingItem]] = defaultdict(list)
        for item in self.items:
            by_date[item.date].append(item)
        return {
            "days": self.days,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "total": len(self.items),
            "by_date": [
                {
                    "date": d.isoformat(),
                    "items": [it.as_dict() for it in by_date[d]],
                }
                for d in sorted(by_date)
            ],
            # Flat sorted list too — easier to scan, "what's the
            # very next thing on my plate?".
            "items": [it.as_dict() for it in self.items],
        }


# Emoji for each kind — used in the human render.
_KIND_EMOJI = {
    "task": "✅",
    "bill": "💸",
    "event": "📅",
    "followup": "🔔",
    "birthday": "🎂",
    "chore": "🧹",
    "package": "📦",
    "document": "📑",
}


def collect_upcoming(days: int = 7) -> UpcomingSnapshot:
    """Aggregate everything date-anchored over the next ``days`` days."""
    today = date.today()
    end = today + timedelta(days=days)
    items: list[UpcomingItem] = []
    with session() as db:
        # ✅ Tasks with a due date in the window, not done.
        tasks = list(
            db.exec(
                select(Task)
                .where(Task.done == False)  # noqa: E712
                .where(Task.due.is_not(None))  # type: ignore[union-attr]
                .where(Task.due >= today)
                .where(Task.due <= end)
            ).all()
        )
        for t in tasks:
            items.append(UpcomingItem(
                kind="task", date=t.due, title=t.title,
                detail=t.priority,
            ))
        # 💸 Unpaid bills due in the window.
        bills = list(
            db.exec(
                select(Bill)
                .where(Bill.paid == False)  # noqa: E712
                .where(Bill.due_date >= today)
                .where(Bill.due_date <= end)
            ).all()
        )
        for b in bills:
            items.append(UpcomingItem(
                kind="bill", date=b.due_date, title=b.name,
                detail=f"{b.amount:g}",
            ))
        # 📅 Events in the window.
        events = list(
            db.exec(
                select(Event)
                .where(Event.event_date >= today)
                .where(Event.event_date <= end)
            ).all()
        )
        for e in events:
            items.append(UpcomingItem(
                kind="event", date=e.event_date, title=e.title,
                detail=e.event_time,
            ))
        # 🔔 Follow-ups due in the window.
        followups = list(
            db.exec(
                select(FollowUp)
                .where(FollowUp.done == False)  # noqa: E712
                .where(FollowUp.due_date >= today)
                .where(FollowUp.due_date <= end)
            ).all()
        )
        for f in followups:
            items.append(UpcomingItem(
                kind="followup", date=f.due_date, title=f.person,
                detail=f.reason,
            ))
        # 🎂 Birthdays / occasions whose next occurrence is in the window.
        for occ in db.exec(select(Occasion)).all():
            nxt = _next_occurrence(occ.month, occ.day)
            if today <= nxt <= end:
                items.append(UpcomingItem(
                    kind="birthday", date=nxt, title=occ.person,
                    detail=occ.kind,
                ))
        # 🧹 Chores whose next due falls in the window.
        for chore in db.exec(select(Chore)).all():
            nxt = _next_due(chore)
            if today <= nxt <= end:
                items.append(UpcomingItem(
                    kind="chore", date=nxt, title=chore.name,
                    detail=f"every {chore.frequency_days}d",
                ))
        # 📦 Packages expected in the window (not yet received).
        packages = list(
            db.exec(
                select(Package)
                .where(Package.received_date.is_(None))  # type: ignore[union-attr]
                .where(Package.expected_date.is_not(None))  # type: ignore[union-attr]
                .where(Package.expected_date >= today)
                .where(Package.expected_date <= end)
            ).all()
        )
        for p in packages:
            title = (
                f"{p.sender} — {p.description}" if p.description else p.sender
            )
            items.append(UpcomingItem(
                kind="package", date=p.expected_date, title=title,
                detail=p.carrier,
            ))
        # 📑 Documents expiring in the window.
        docs = list(
            db.exec(
                select(Document)
                .where(Document.expires >= today)
                .where(Document.expires <= end)
            ).all()
        )
        for d in docs:
            items.append(UpcomingItem(
                kind="document", date=d.expires, title=d.name,
                detail="expires",
            ))
    # Sort: by date, then by kind for stability.
    items.sort(key=lambda it: (it.date, it.kind, it.title))
    return UpcomingSnapshot(days=days, start=today, end=end, items=items)


def render_upcoming(days: int, json_out: bool) -> None:
    """Print the next-N-days view to stdout."""
    snap = collect_upcoming(days=days)
    if json_out:
        _emit_json(snap.as_dict())
        return

    if days == 7:
        header = "This week"
    elif days == 14:
        header = "Next two weeks"
    elif days == 30:
        header = "Next 30 days"
    else:
        header = f"Next {days} days"
    console.print(
        f"\n🔮 [bold]{header}[/bold]  "
        f"[dim]{snap.start:%a %d %b} → {snap.end:%a %d %b}[/dim]\n"
    )
    if not snap.items:
        console.print(
            f"  [dim]Nothing on the radar for the next {days} day"
            f"{'s' if days != 1 else ''}. ✨[/dim]\n"
        )
        return

    # Group by date for the human view.
    by_date: dict[date, list[UpcomingItem]] = defaultdict(list)
    for item in snap.items:
        by_date[item.date].append(item)
    today = date.today()
    for d in sorted(by_date):
        if d == today:
            label = "Today"
        elif d == today + timedelta(days=1):
            label = "Tomorrow"
        else:
            label = d.strftime("%A %d %b")
        console.print(f"[bold]{label}[/bold]  [dim]· {d}[/dim]")
        for item in by_date[d]:
            emoji = _KIND_EMOJI.get(item.kind, "•")
            detail = f"  [dim]({item.detail})[/dim]" if item.detail else ""
            console.print(f"  {emoji} {item.title}{detail}")
        console.print()
    console.print(f"  [dim]{len(snap.items)} items total[/dim]\n")
