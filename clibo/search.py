"""``clibo search`` — one query across every text-bearing clibo table.

This is the second integrating command (after ``clibo today``): if you've
written something down somewhere in clibo, this finds it. It searches notes,
journal entries, tasks, bookmarks, contacts, meetings, achievements, recipes,
worklog entries, network connections, gift ideas, expenses and the wishlist.
"""

from __future__ import annotations

from sqlalchemy import or_
from sqlmodel import select

from clibo.clis.bookmark import Bookmark
from clibo.clis.brag import Achievement
from clibo.clis.crm import Contact
from clibo.clis.expense import Expense
from clibo.clis.gifts import Gift
from clibo.clis.journal import JournalEntry
from clibo.clis.meetings import Meeting
from clibo.clis.network import Connection
from clibo.clis.notes import Note
from clibo.clis.recipes import Recipe
from clibo.clis.todo import Task
from clibo.clis.wishlist import WishlistItem
from clibo.clis.worklog import WorkLogEntry
from clibo.core.db import session


def _snippet_journal(entry: JournalEntry) -> str:
    body = " ".join((entry.body or "").split())
    return body[:80] + ("…" if len(body) > 80 else "")


def _snippet_contact(contact: Contact) -> str:
    return contact.name + (f" · {contact.company}" if contact.company else "")


def _snippet_gift(gift: Gift) -> str:
    return f"{gift.idea} (for {gift.recipient})"


def _snippet_bookmark(bookmark: Bookmark) -> str:
    return bookmark.title or bookmark.url


#: ``(label, model, [columns to search], snippet_fn)`` for every source.
SOURCES: list[tuple] = [
    ("notes", Note, [Note.title, Note.body, Note.tags], lambda n: n.title),
    ("journal", JournalEntry, [JournalEntry.body, JournalEntry.tags], _snippet_journal),
    ("todo", Task, [Task.title, Task.note, Task.tags], lambda t: t.title),
    ("bookmark", Bookmark,
     [Bookmark.title, Bookmark.url, Bookmark.tags, Bookmark.note], _snippet_bookmark),
    ("crm", Contact,
     [Contact.name, Contact.company, Contact.email, Contact.tags, Contact.notes],
     _snippet_contact),
    ("network", Connection,
     [Connection.name, Connection.company, Connection.met_where,
      Connection.context, Connection.notes],
     lambda c: c.name + (f" · {c.met_where}" if c.met_where else "")),
    ("meetings", Meeting,
     [Meeting.title, Meeting.attendees, Meeting.notes], lambda m: m.title),
    ("brag", Achievement,
     [Achievement.title, Achievement.description, Achievement.impact, Achievement.tags],
     lambda a: a.title),
    ("recipes", Recipe,
     [Recipe.name, Recipe.ingredients, Recipe.instructions, Recipe.tags], lambda r: r.name),
    ("worklog", WorkLogEntry,
     [WorkLogEntry.summary, WorkLogEntry.project], lambda w: w.summary),
    ("gifts", Gift, [Gift.recipient, Gift.idea, Gift.occasion, Gift.notes], _snippet_gift),
    ("expense", Expense,
     [Expense.description, Expense.category, Expense.note], lambda e: e.description),
    ("wishlist", WishlistItem,
     [WishlistItem.name, WishlistItem.category, WishlistItem.note], lambda w: w.name),
]


def search_all(query: str) -> list[dict]:
    """Run a case-insensitive ``LIKE`` query against every source.

    Returns a flat list of ``{"source", "id", "snippet"}`` results, in source
    order so the human renderer can group them naturally.
    """
    if not query:
        return []
    pattern = f"%{query}%"
    out: list[dict] = []
    with session() as db:
        for label, model, columns, snippet_fn in SOURCES:
            rows = db.exec(
                select(model).where(or_(*[col.ilike(pattern) for col in columns]))
            ).all()
            for row in rows:
                out.append({"source": label, "id": row.id, "snippet": snippet_fn(row)})
    return out
