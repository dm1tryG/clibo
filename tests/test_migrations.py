"""Tests for the forward-compatible column-addition migration helper.

When a model gains a new nullable column, existing databases should pick
it up via ``ALTER TABLE ADD COLUMN`` on the next ``init_db()`` call —
otherwise SELECTs would crash because SQLAlchemy generates an explicit
column list that includes the new column.
"""

from __future__ import annotations

from sqlalchemy import Column, Integer, inspect
from sqlmodel import SQLModel

from clibo.core import db
from clibo.core.db import _add_missing_columns


def _columns(engine, table_name: str) -> set[str]:
    return {col["name"] for col in inspect(engine).get_columns(table_name)}


def test_add_missing_columns_adds_a_new_nullable_column(monkeypatch, tmp_path):
    monkeypatch.setenv("CLIBO_HOME", str(tmp_path))
    db.reset_engine()
    db.init_db()
    engine = db.get_engine()
    assert "kcal_burned" in _columns(engine, "workout_entry")

    # Simulate a database that pre-dates the column: drop it manually,
    # then re-run the helper and confirm it gets added back.
    with engine.begin() as conn:
        # SQLite ALTER TABLE DROP COLUMN is available from 3.35; if not,
        # rebuild the table without it.
        conn.exec_driver_sql(
            "CREATE TABLE workout_entry_old AS "
            "SELECT id, exercise, sets, reps, weight_kg, duration_min, "
            "entry_date, created_at, note FROM workout_entry"
        )
        conn.exec_driver_sql("DROP TABLE workout_entry")
        conn.exec_driver_sql(
            "ALTER TABLE workout_entry_old RENAME TO workout_entry"
        )
    assert "kcal_burned" not in _columns(engine, "workout_entry")

    # Re-running the helper should restore the missing column.
    _add_missing_columns(engine)
    assert "kcal_burned" in _columns(engine, "workout_entry")


def test_add_missing_columns_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setenv("CLIBO_HOME", str(tmp_path))
    db.reset_engine()
    db.init_db()
    engine = db.get_engine()
    before = _columns(engine, "workout_entry")
    _add_missing_columns(engine)
    _add_missing_columns(engine)
    after = _columns(engine, "workout_entry")
    assert before == after  # no duplicate columns added


def test_add_missing_columns_skips_unknown_tables(monkeypatch, tmp_path):
    """An entry in the model metadata that doesn't exist as a table yet
    is skipped, not crashed on — `create_all` will create it next call."""
    monkeypatch.setenv("CLIBO_HOME", str(tmp_path))
    db.reset_engine()
    db.init_db()
    engine = db.get_engine()

    # Register a brand-new table in metadata without creating it.
    from sqlalchemy import Table
    if "test_migration_synth" not in SQLModel.metadata.tables:
        Table(
            "test_migration_synth", SQLModel.metadata,
            Column("id", Integer, primary_key=True),
            Column("new_col", Integer, nullable=True),
        )
    try:
        # Should not raise: the inspector reports it doesn't exist, we skip it.
        _add_missing_columns(engine)
    finally:
        SQLModel.metadata.remove(SQLModel.metadata.tables["test_migration_synth"])
