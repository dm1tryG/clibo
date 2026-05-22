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


def import_data(src: Path, *, replace: bool = False) -> dict[str, int]:
    """Insert rows from a ``clibo export`` JSON file into the live database.

    With ``replace=True`` each table is emptied first; otherwise existing rows
    are kept and any primary-key collisions are silently skipped (so the same
    file can be re-imported safely).

    Returns a ``{table_name: inserted_rows}`` summary.
    """
    init_db()
    source = Path(src).expanduser()
    if not source.exists():
        raise FileNotFoundError(f"Import file not found at {source}")
    with source.open(encoding="utf-8") as fh:
        payload = _json.load(fh)
    if isinstance(payload, dict) and isinstance(payload.get("tables"), dict):
        tables = payload["tables"]
    elif (
        isinstance(payload, dict)
        and payload
        and all(isinstance(v, list) for v in payload.values())
    ):
        # Allow a bare ``{table_name: [rows]}`` dump (no envelope).
        tables = payload
    else:
        raise ValueError("Import file is not a clibo export — expected a 'tables' map")

    reset_engine()
    inserted: dict[str, int] = {}
    db_path = config.db_path()
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        for table_name, rows in tables.items():
            if not isinstance(rows, list):
                continue
            exists = cursor.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            ).fetchone()
            if not exists:
                continue  # an extra table from a different clibo version
            if replace:
                cursor.execute(f'DELETE FROM "{table_name}"')
            inserted.setdefault(table_name, 0)
            for row in rows:
                if not isinstance(row, dict) or not row:
                    continue
                cols = list(row.keys())
                placeholders = ", ".join("?" for _ in cols)
                col_list = ", ".join(f'"{c}"' for c in cols)
                cursor.execute(
                    f'INSERT OR IGNORE INTO "{table_name}" ({col_list}) VALUES ({placeholders})',
                    [row[c] for c in cols],
                )
                if cursor.rowcount > 0:
                    inserted[table_name] += 1
        conn.commit()
    finally:
        conn.close()
    return inserted


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
