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
from clibo.clis.books import Book
from clibo.clis.brag import Achievement
from clibo.clis.caffeine import CaffeineEntry
from clibo.clis.challenge import Challenge
from clibo.clis.crm import Contact
from clibo.clis.cv import CvEntry
from clibo.clis.documents import Document
from clibo.clis.donations import Donation
from clibo.clis.dreams import Dream
from clibo.clis.expense import Expense
from clibo.clis.fasting import FastSession
from clibo.clis.films import Film
from clibo.clis.gifts import Gift
from clibo.clis.gratitude import GratitudeEntry
from clibo.clis.ideas import Idea
from clibo.clis.income import IncomeEntry
from clibo.clis.invest import Transaction as InvestTransaction
from clibo.clis.journal import JournalEntry
from clibo.clis.lessons import Lesson
from clibo.clis.meetings import Meeting
from clibo.clis.network import Connection
from clibo.clis.notes import Note
from clibo.clis.packages import Package
from clibo.clis.quotes import Quote
from clibo.clis.recipes import Recipe
from clibo.clis.steps import StepEntry
from clibo.clis.stretches import StretchSession
from clibo.clis.tip import TipEntry
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
    # ── beyond the original 50 ─────────────────────────────────────────────
    ("books", Book, [Book.title, Book.author, Book.note], lambda b: b.title),
    ("films", Film, [Film.title, Film.note], lambda f: f.title),
    ("income", IncomeEntry,
     [IncomeEntry.source, IncomeEntry.category, IncomeEntry.note],
     lambda i: f"{i.source} ({i.category})"),
    ("ideas", Idea,
     [Idea.title, Idea.description, Idea.tags],
     lambda i: f"[{i.status}] {i.title}"),
    ("quotes", Quote,
     [Quote.text, Quote.author, Quote.source, Quote.tags],
     lambda q: (q.text[:60] + ("…" if len(q.text) > 60 else ""))
                + (f" — {q.author}" if q.author else "")),
    ("lessons", Lesson,
     [Lesson.takeaway, Lesson.context, Lesson.tags],
     lambda ls: ls.takeaway),
    ("cv", CvEntry,
     [CvEntry.title, CvEntry.org, CvEntry.description,
      CvEntry.achievements, CvEntry.tags],
     lambda c: f"{c.title}" + (f" @ {c.org}" if c.org else "")),
    ("dreams", Dream,
     [Dream.summary, Dream.description, Dream.symbols],
     lambda d: d.summary),
    ("gratitude", GratitudeEntry,
     [GratitudeEntry.text], lambda g: g.text),
    ("stretches", StretchSession,
     [StretchSession.area, StretchSession.poses, StretchSession.note],
     lambda s: f"{s.area} · {s.duration_min} min"
                + (f" ({s.poses})" if s.poses else "")),
    ("tip", TipEntry, [TipEntry.venue, TipEntry.note],
     lambda t: f"{t.tip_amount:.2f} ({t.tip_percent:g}%)"
                + (f" @ {t.venue}" if t.venue else "")),
    ("steps", StepEntry, [StepEntry.source, StepEntry.note],
     lambda s: f"{s.count:,} steps"
                + (f" ({s.source})" if s.source else "")),
    ("caffeine", CaffeineEntry,
     [CaffeineEntry.drink, CaffeineEntry.note],
     lambda c: f"{c.drink} ({c.mg} mg)"),
    ("documents", Document,
     [Document.name, Document.kind, Document.number, Document.note],
     lambda d: f"{d.kind}: {d.name} (expires {d.expires})"),
    ("challenge", Challenge,
     [Challenge.name, Challenge.description],
     lambda c: f"{c.status} {c.target_days}-day: {c.name}"),
    ("donations", Donation,
     [Donation.recipient, Donation.receipt, Donation.note],
     lambda d: f"{d.amount:.2f} to {d.recipient}"),
    ("invest", InvestTransaction,
     [InvestTransaction.ticker, InvestTransaction.note],
     lambda t: f"{t.action} {t.shares:g} {t.ticker} @ {t.price_per_share:.2f}"),
    ("packages", Package,
     [Package.sender, Package.description, Package.tracking_number,
      Package.carrier, Package.note],
     lambda p: f"[{p.status}] {p.sender}"
                + (f" — {p.description}" if p.description else "")),
    ("fasting", FastSession, [FastSession.note],
     lambda f: f"{f.target_hours:g}h target"
                + (f" — {f.note}" if f.note else "")),
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
