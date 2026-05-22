"""Database engine and sessions, shared by all 50 CLIs.

A single SQLite file holds every tool's tables; each model namespaces its table
name (``calorie_entry``, ``crm_contact``, ...) so the tools never collide.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

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
    """Create any missing tables for every registered model.

    Importing the cli package registers all SQLModel tables; ``create_all`` is
    idempotent so this is safe to call before every command.
    """
    from clibo import clis  # noqa: F401  (imports register the models)
    from clibo.core import settings  # noqa: F401

    SQLModel.metadata.create_all(get_engine())


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
