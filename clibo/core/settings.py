"""A tiny key/value store shared by every CLI.

Tools use it for small bits of per-user configuration — a daily calorie goal,
your height for BMI, a water target — without each one needing its own table.
Values are stored as strings under a ``scope`` (usually the tool name).
"""

from __future__ import annotations

from sqlmodel import Field, SQLModel, select

from clibo.core.db import session


class Setting(SQLModel, table=True):
    """One configuration value, addressed by ``(scope, key)``."""

    __tablename__ = "clibo_setting"

    id: int | None = Field(default=None, primary_key=True)
    scope: str = Field(index=True)
    key: str = Field(index=True)
    value: str


def get_setting(scope: str, key: str, default: str | None = None) -> str | None:
    """Read a value, returning ``default`` when it has never been set."""
    with session() as db:
        row = db.exec(
            select(Setting).where(Setting.scope == scope, Setting.key == key)
        ).first()
        return row.value if row else default


def set_setting(scope: str, key: str, value: str) -> None:
    """Create or update a value."""
    with session() as db:
        row = db.exec(
            select(Setting).where(Setting.scope == scope, Setting.key == key)
        ).first()
        if row:
            row.value = value
        else:
            row = Setting(scope=scope, key=key, value=value)
        db.add(row)
