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

#: ``(source label, table name, label column)`` for every tag-bearing model.
#: The label column is what we surface in `clibo tagged <tag>` listings —
#: typically the row's title or name. Free-text columns like `journal.body`
#: are truncated by the consumer.
#: ``network`` and ``gifts`` keep free-text notes but don't expose a tag
#: column — they're intentionally omitted.
TAG_SOURCES: list[tuple[str, str, str]] = [
    ("notes", "notes_note", "title"),
    ("todo", "todo_task", "title"),
    ("bookmark", "bookmark_bookmark", "title"),
    ("crm", "crm_contact", "name"),
    ("brag", "brag_achievement", "title"),
    ("recipes", "recipes_recipe", "name"),
    ("journal", "journal_entry", "body"),
    # ── beyond the original 50 ────────────────────────────────────────
    ("ideas", "ideas_idea", "title"),
    ("quotes", "quotes_quote", "text"),
    ("lessons", "lessons_lesson", "takeaway"),
    ("cv", "cv_entry", "title"),
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
        for source, table, _label in TAG_SOURCES:
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


def _truncate(text: str | None, n: int = 80) -> str:
    """Shorten free-text labels for one-line display."""
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def collect_items_by_tag(tag: str) -> list[dict]:
    """Every item across every source that carries the given tag.

    Returns rows sorted newest-first (by ``created_at`` where available).
    Each row: ``{"source", "id", "label", "tags", "created_at"}``.
    Match is case-insensitive on the normalised tag list (whitespace
    stripped, lowercase) — same as `collect_tags`.
    """
    init_db()
    needle = tag.strip().lower()
    out: list[dict] = []
    conn = sqlite3.connect(str(config.db_path()))
    conn.row_factory = sqlite3.Row
    try:
        for source, table, label_col in TAG_SOURCES:
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            if not exists:
                continue
            columns = {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}
            if "tags" not in columns or label_col not in columns:
                continue
            time_col = "created_at" if "created_at" in columns else None
            select_cols = ["id", "tags", f'"{label_col}" AS _label']
            if time_col:
                select_cols.append(f'"{time_col}" AS _created_at')
            order = f' ORDER BY "{time_col}" DESC' if time_col else ""
            rows = conn.execute(
                f'SELECT {", ".join(select_cols)} FROM "{table}" '
                f"WHERE tags IS NOT NULL{order}"
            ).fetchall()
            for row in rows:
                if needle in _split(row["tags"]):
                    out.append({
                        "source": source,
                        "id": row["id"],
                        "label": _truncate(row["_label"]),
                        "tags": _split(row["tags"]),
                        "created_at": row["_created_at"] if time_col else None,
                    })
    finally:
        conn.close()
    # Sort across sources: newest first when created_at is available,
    # then by source/id as a stable fallback.
    out.sort(
        key=lambda r: (r["created_at"] or "", r["source"], r["id"]),
        reverse=True,
    )
    return out
