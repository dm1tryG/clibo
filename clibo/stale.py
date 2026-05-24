"""``clibo stale`` — everything you've been neglecting, across every tracker.

Three tools store "last activity" timestamps that previous iterations
exposed individually: `crm dormant`, `ideas stale`, `books stale`.
This module pulls all three into a single view — the same lens as
``clibo overdue`` (past-due items) but on the orthogonal "haven't
touched it recently" axis.

Each per-tool command keeps its own default threshold (CRM=90d
since that's a slower social cadence; ideas=30d; books=14d) — this
aggregator uses a single uniform threshold across all three so the
question "what have I been neglecting in the last month?" has one
answer instead of three.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlmodel import select

from clibo.clis.books import Book, BookSession
from clibo.clis.crm import Contact
from clibo.clis.ideas import OPEN_STATUSES as IDEA_OPEN_STATUSES
from clibo.clis.ideas import Idea
from clibo.core.db import session
from clibo.core.output import _emit_json, console


@dataclass
class StaleItem:
    """One thing that's gone quiet."""

    source: str          # crm / ideas / books
    id: int
    title: str           # contact name / idea title / book title
    days_since: int      # days since the last touch
    detail: str | None = None    # status / company / author

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "id": self.id,
            "title": self.title,
            "days_since": self.days_since,
            "detail": self.detail,
        }


@dataclass
class StaleSnapshot:
    """Everything neglected past the threshold."""

    asof: date
    days: int
    items: list[StaleItem]

    def as_dict(self) -> dict:
        by_source: dict[str, list[StaleItem]] = defaultdict(list)
        for item in self.items:
            by_source[item.source].append(item)
        return {
            "asof": self.asof.isoformat(),
            "days": self.days,
            "total": len(self.items),
            "by_source": {
                k: [it.as_dict() for it in items] for k, items in by_source.items()
            },
            # Flat list, sorted most-stale first.
            "items": [it.as_dict() for it in self.items],
        }


_KIND_EMOJI = {
    "crm": "👥",
    "ideas": "💡",
    "books": "📚",
}


def collect_stale(days: int = 30) -> StaleSnapshot:
    """Aggregate every neglected item across the supported sources."""
    today = date.today()
    cutoff_date = today - timedelta(days=days)
    cutoff_dt = datetime.combine(cutoff_date, datetime.min.time())
    items: list[StaleItem] = []
    with session() as db:
        # 👥 CRM — active contacts not touched in `days`, plus
        # never-contacted active contacts (count from contact creation).
        for c in db.exec(
            select(Contact).where(Contact.status == "active")
        ).all():
            if c.last_contact is None:
                # Use created_at as the anchor — same logic as `crm dormant`
                # except we apply the unified threshold here.
                anchor = c.created_at.date()
                if anchor <= cutoff_date:
                    items.append(StaleItem(
                        source="crm", id=c.id, title=c.name,
                        days_since=(today - anchor).days,
                        detail=c.company,
                    ))
            elif c.last_contact <= cutoff_date:
                items.append(StaleItem(
                    source="crm", id=c.id, title=c.name,
                    days_since=(today - c.last_contact).days,
                    detail=c.company,
                ))

        # 💡 Ideas — open-status only, updated_at older than threshold.
        for idea in db.exec(
            select(Idea)
            .where(Idea.status.in_(IDEA_OPEN_STATUSES))
            .where(Idea.updated_at <= cutoff_dt)
        ).all():
            items.append(StaleItem(
                source="ideas", id=idea.id, title=idea.title,
                days_since=(today - idea.updated_at.date()).days,
                detail=idea.status,
            ))

        # 📚 Books — reading-status, last session older than threshold
        # (or no session at all, anchored on `started`).
        reading = list(
            db.exec(select(Book).where(Book.status == "reading")).all()
        )
        sessions_all = list(db.exec(select(BookSession)).all())
        last_session: dict[int, date] = {}
        for s in sessions_all:
            prev = last_session.get(s.book_id)
            if prev is None or s.entry_date > prev:
                last_session[s.book_id] = s.entry_date
        for b in reading:
            last = last_session.get(b.id)
            anchor = last or b.started
            if anchor is None:
                # Reading-status without started or session — anchor on
                # created. The book is at risk of being forgotten.
                continue
            if anchor <= cutoff_date:
                items.append(StaleItem(
                    source="books", id=b.id, title=b.title,
                    days_since=(today - anchor).days,
                    detail=b.author,
                ))
    # Sort most-stale first; secondary by source/id for stability.
    items.sort(key=lambda it: (-it.days_since, it.source, it.id))
    return StaleSnapshot(asof=today, days=days, items=items)


def render_stale(days: int, json_out: bool) -> None:
    """Print the cross-tool stale view."""
    snap = collect_stale(days=days)
    if json_out:
        _emit_json(snap.as_dict())
        return

    console.print(
        f"\n🌫️  [bold]Stale[/bold]   "
        f"[dim]>{days}d since last touch  ·  as of {snap.asof}[/dim]\n"
    )
    if not snap.items:
        console.print(
            "  [dim green]Nothing's gone stale. Everything's been "
            "touched recently. ✨[/dim green]\n"
        )
        return

    # Group by source so the eye scans to the right pile.
    by_source: dict[str, list[StaleItem]] = defaultdict(list)
    for item in snap.items:
        by_source[item.source].append(item)
    # Order: source with the most stale items first.
    order = sorted(by_source, key=lambda s: -len(by_source[s]))
    for src in order:
        emoji = _KIND_EMOJI.get(src, "•")
        plural = "s" if len(by_source[src]) != 1 else ""
        console.print(
            f"[bold]{emoji} {src}{plural}[/bold]  "
            f"[dim]· {len(by_source[src])}[/dim]"
        )
        for item in by_source[src]:
            detail = f"  [dim]({item.detail})[/dim]" if item.detail else ""
            console.print(
                f"  [yellow]·[/yellow] {item.title}{detail}  "
                f"[dim]· {item.days_since}d[/dim]"
            )
        console.print()
    console.print(f"  [dim]{len(snap.items)} stale items total[/dim]\n")
