"""Admin helpers — back up, restore and export the local database.

Uses plain :mod:`sqlite3` for export so the JSON dump doesn't depend on any
particular set of SQLModel tables being importable.
"""

from __future__ import annotations

import json as _json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from clibo.core import config
from clibo.core.db import init_db, reset_engine


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def default_backup_path() -> Path:
    """The default destination for ``clibo backup`` if none is given."""
    return config.clibo_home() / "backups" / f"clibo-{_stamp()}.db"


def default_export_path() -> Path:
    return config.clibo_home() / f"clibo-export-{_stamp()}.json"


def backup_db(dest: Path | None = None) -> Path:
    """Copy the live database file to ``dest`` (or a timestamped default)."""
    init_db()
    src = config.db_path()
    if not src.exists():
        raise FileNotFoundError(f"Database not found at {src}")
    target = Path(dest).expanduser() if dest else default_backup_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)
    return target


def restore_db(src: Path) -> Path:
    """Replace the live database with ``src``. Closes any cached engine first."""
    source = Path(src).expanduser()
    if not source.exists():
        raise FileNotFoundError(f"Backup file not found at {source}")
    reset_engine()
    target = config.db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def export_data(dest: Path | None = None) -> tuple[Path, dict]:
    """Dump every clibo table as JSON.

    Returns ``(path, summary)`` where ``summary`` maps each table name to its
    row count.
    """
    init_db()
    src = config.db_path()
    conn = sqlite3.connect(str(src))
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cursor.fetchall() if not r[0].startswith("sqlite_")]
        data: dict[str, list[dict]] = {}
        summary: dict[str, int] = {}
        for name in tables:
            rows = [dict(row) for row in cursor.execute(f'SELECT * FROM "{name}"').fetchall()]
            data[name] = rows
            summary[name] = len(rows)
    finally:
        conn.close()
    target = Path(dest).expanduser() if dest else default_export_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as fh:
        _json.dump(
            {"version": 1, "exported_at": datetime.now().isoformat(), "tables": data},
            fh,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    return target, summary
