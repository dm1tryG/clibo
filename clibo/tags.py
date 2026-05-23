"""``clibo tags`` — discover every tag used across clibo, with counts.

Tags live in eight different tables (one per tag-bearing tool). The collector
queries them with plain SQLite so it works even when individual tool modules
change their schema, normalises everything to lowercase, and groups by source.
"""

from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict

from clibo.core import config
from clibo.core.db import init_db

#: ``(source label, table name)`` for every tag-bearing model.
#: ``network`` and ``gifts`` keep free-text notes but don't expose a tag
#: column — they're intentionally omitted.
TAG_SOURCES: list[tuple[str, str]] = [
    ("notes", "notes_note"),
    ("todo", "todo_task"),
    ("bookmark", "bookmark_bookmark"),
    ("crm", "crm_contact"),
    ("brag", "brag_achievement"),
    ("recipes", "recipes_recipe"),
    ("journal", "journal_entry"),
    # ── beyond the original 50 ────────────────────────────────────────
    ("ideas", "ideas_idea"),
    ("quotes", "quotes_quote"),
    ("lessons", "lessons_lesson"),
    ("cv", "cv_entry"),
]


def _split(value: str | None) -> list[str]:
    """Split a comma-joined tags string into a clean list of lowercase tags."""
    if not value:
        return []
    return [tag.strip().lower() for tag in value.split(",") if tag.strip()]


def collect_tags() -> list[dict]:
    """Aggregate every tag across all tag-bearing tables.

    Returns one record per tag, sorted by count descending:
    ``{"tag": "work", "count": 8, "by_source": {"notes": 3, "todo": 5}}``.
    """
    init_db()
    totals: Counter[str] = Counter()
    by_source: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    conn = sqlite3.connect(str(config.db_path()))
    try:
        for source, table in TAG_SOURCES:
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            if not exists:
                continue
            # Defensive: only query if the table actually has a `tags` column.
            columns = {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}
            if "tags" not in columns:
                continue
            for (raw,) in conn.execute(
                f'SELECT tags FROM "{table}" WHERE tags IS NOT NULL'
            ).fetchall():
                for tag in _split(raw):
                    totals[tag] += 1
                    by_source[tag][source] += 1
    finally:
        conn.close()
    return [
        {"tag": tag, "count": count, "by_source": dict(by_source[tag])}
        for tag, count in totals.most_common()
    ]
