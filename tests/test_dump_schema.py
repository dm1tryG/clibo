"""Smoke test for ``scripts/dump_schema.py``.

Ensures the schema-dump script keeps working as new tools/tables are added.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_dump_schema_runs(tmp_path, monkeypatch):
    """The script writes a SCHEMA.md that mentions all known table prefixes."""
    monkeypatch.setenv("CLIBO_HOME", str(tmp_path))
    monkeypatch.chdir(REPO)
    # Run via a sub-process so it exercises the script's main() end-to-end.
    result = subprocess.run(
        [sys.executable, "scripts/dump_schema.py"],
        capture_output=True, text=True, check=False,
        cwd=str(REPO),
    )
    assert result.returncode == 0, result.stderr
    written = REPO / "docs" / "SCHEMA.md"
    assert written.exists()
    text = written.read_text(encoding="utf-8")
    # A handful of representative tables across categories must show up.
    for table in ("clibo_setting", "calorie_entry", "expense_entry",
                  "todo_task", "crm_contact", "groceries_item"):
        assert f"`{table}`" in text
    # The header should reflect a real, non-zero table count.
    assert "_0 tables in total._" not in text
