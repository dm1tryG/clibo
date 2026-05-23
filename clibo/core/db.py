"""Database engine and sessions, shared by all 50 CLIs.

A single SQLite file holds every tool's tables; each model namespaces its table
name (``calorie_entry``, ``crm_contact``, ...) so the tools never collide.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import inspect
from sqlalchemy.dialects import sqlite as sqlite_dialect
from sqlmodel import Session, SQLModel, create_engine

from clibo.core import config

_engine = None


def get_engine():
    """Return the process-wide SQLAlchemy engine, creating it lazily."""
    global _engine
    if _engine is None:
        config.ensure_home()
        _engine = create_engine(
            f"sqlite:///{config.db_path()}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
    return _engine


def reset_engine() -> None:
    """Drop the cached engine — used by tests to switch databases."""
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None


def init_db() -> None:
    """Create any missing tables for every registered model, then add any
    columns the model now declares but the existing table is missing.

    Importing the cli package registers all SQLModel tables; ``create_all`` is
    idempotent so creating new tables is safe to call before every command.
    The follow-up :func:`_add_missing_columns` handles forward-compatible
    schema evolution — when a model gains a nullable column, existing
    databases pick it up via ``ALTER TABLE ADD COLUMN`` rather than crashing
    on SELECT.
    """
    from clibo import clis  # noqa: F401  (imports register the models)
    from clibo.core import settings  # noqa: F401

    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    _add_missing_columns(engine)


def _add_missing_columns(engine) -> None:
    """For every model table that already exists, add any columns the model
    declares but the database is missing. Only nullable / defaulted columns
    can be added this way — SQLite refuses ``ALTER ADD COLUMN`` for a NOT
    NULL column without a server-side default, which is the right behaviour
    (it'd corrupt existing rows). We surface that as a noisy skip.
    """
    inspector = inspect(engine)
    dialect = sqlite_dialect.dialect()
    with engine.begin() as conn:
        for table in SQLModel.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue  # create_all just made it; nothing to migrate
            existing = {col["name"] for col in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                if not column.nullable and column.default is None and column.server_default is None:
                    # Can't safely add a NOT NULL column without a default.
                    continue
                type_sql = column.type.compile(dialect=dialect)
                nullable = "" if column.nullable else " NOT NULL"
                conn.exec_driver_sql(
                    f'ALTER TABLE "{table.name}" ADD COLUMN '
                    f'"{column.name}" {type_sql}{nullable}'
                )


@contextmanager
def session() -> Iterator[Session]:
    """Context-managed session that commits on success.

    ``expire_on_commit=False`` keeps loaded attributes readable after the
    session closes, so commands can safely render objects they just fetched.
    """
    db = Session(get_engine(), expire_on_commit=False)
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
