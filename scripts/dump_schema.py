#!/usr/bin/env python3
"""Regenerate ``docs/SCHEMA.md`` from SQLModel metadata.

Why: clibo's 40+ tables are defined in 50 separate cli modules. There's no
single place a contributor (or an AI agent writing analytics) can see them
all. This script walks ``SQLModel.metadata`` and produces a human-readable
Markdown reference, grouped by tool category and table name.

Usage:  python scripts/dump_schema.py
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from sqlmodel import SQLModel  # noqa: E402

from clibo.catalog import CATALOG  # noqa: E402
from clibo.core.db import init_db  # noqa: E402


def _table_category(table_name: str) -> str:
    """Map a table prefix to a catalog category, or 'Core' for shared ones."""
    prefix = table_name.split("_", 1)[0]
    for tool in CATALOG:
        if tool.name == prefix:
            return tool.category
    return "Core"


def render() -> str:
    init_db()

    by_category: dict[str, list[str]] = defaultdict(list)
    for name in sorted(SQLModel.metadata.tables):
        by_category[_table_category(name)].append(name)

    categories = ["Core"] + [t.category for t in CATALOG if t.category not in {"Core"}]
    # Deduplicate while preserving order.
    seen: set[str] = set()
    ordered = [c for c in categories if not (c in seen or seen.add(c))]

    lines: list[str] = []
    lines.append("# clibo schema")
    lines.append("")
    lines.append(
        "Auto-generated reference for every SQLite table clibo writes to. "
        "Regenerate with `python scripts/dump_schema.py`."
    )
    lines.append("")
    lines.append(f"_{len(SQLModel.metadata.tables)} tables in total._")
    lines.append("")
    lines.append("## Contents")
    lines.append("")
    for category in ordered:
        if not by_category.get(category):
            continue
        anchor = category.lower().replace(" & ", "--").replace(" ", "-")
        lines.append(f"- [{category}](#{anchor})")
    lines.append("")

    for category in ordered:
        tables = by_category.get(category, [])
        if not tables:
            continue
        lines.append(f"## {category}")
        lines.append("")
        for name in tables:
            table = SQLModel.metadata.tables[name]
            lines.append(f"### `{name}`")
            lines.append("")
            lines.append("| Column | Type | Notes |")
            lines.append("|---|---|---|")
            for column in table.columns:
                notes: list[str] = []
                if column.primary_key:
                    notes.append("PK")
                if not column.nullable:
                    notes.append("NOT NULL")
                if column.index:
                    notes.append("indexed")
                if column.default is not None or column.server_default is not None:
                    notes.append("default")
                if column.foreign_keys:
                    fk = next(iter(column.foreign_keys))
                    notes.append(f"FK → `{fk.target_fullname}`")
                lines.append(
                    f"| `{column.name}` | `{column.type}` | {', '.join(notes) or '—'} |"
                )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    out = REPO / "docs" / "SCHEMA.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(), encoding="utf-8")
    print(f"Wrote {out.relative_to(REPO)} ({len(SQLModel.metadata.tables)} tables).")


if __name__ == "__main__":
    main()
