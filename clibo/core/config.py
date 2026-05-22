"""Configuration: where clibo keeps its data.

Everything lives in a single local SQLite database so that installing clibo is
trivial and backing it up is a one-file copy. Locations can be overridden with
environment variables, which is also how the test-suite isolates itself.

    CLIBO_HOME   directory for clibo data        (default: ~/.clibo)
    CLIBO_DB     full path to the SQLite file    (default: $CLIBO_HOME/clibo.db)
"""

from __future__ import annotations

import os
from pathlib import Path


def clibo_home() -> Path:
    """Directory holding clibo's data (created on demand)."""
    override = os.environ.get("CLIBO_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".clibo"


def db_path() -> Path:
    """Absolute path to the SQLite database file."""
    override = os.environ.get("CLIBO_DB")
    if override:
        return Path(override).expanduser()
    return clibo_home() / "clibo.db"


def ensure_home() -> Path:
    """Make sure the data directory exists and return it."""
    home = clibo_home()
    home.mkdir(parents=True, exist_ok=True)
    return home
