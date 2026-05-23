"""Tests for `clibo export --csv` — one CSV per table to a directory."""

from __future__ import annotations

import csv
from pathlib import Path


def test_export_csv_writes_one_file_per_table(cli, tmp_path):
    """Empty DB still produces a CSV per table (header only)."""
    out = tmp_path / "export"
    result = cli.json("export", "--csv", str(out))
    assert result["format"] == "csv"
    assert Path(result["path"]).is_dir()
    csv_files = list(Path(result["path"]).glob("*.csv"))
    # Expect at least the core tables present.
    names = {p.stem for p in csv_files}
    assert "weight_log" in names
    assert "todo_task" in names
    assert "calorie_entry" in names


def test_export_csv_populated(cli, tmp_path):
    """Logged rows show up in the right CSV, with a header."""
    cli.run("weight", "log", "70")
    cli.run("weight", "log", "70.5", "-d", "yesterday")
    out = tmp_path / "export"
    cli.json("export", "--csv", str(out))
    weight_csv = out / "weight_log.csv"
    assert weight_csv.exists()
    with weight_csv.open() as fh:
        rows = list(csv.reader(fh))
    # Header + 2 data rows.
    assert len(rows) == 3
    assert "weight_kg" in rows[0]
    weights = {row[rows[0].index("weight_kg")] for row in rows[1:]}
    assert weights == {"70.0", "70.5"}


def test_export_csv_summary_counts(cli, tmp_path):
    cli.run("weight", "log", "70")
    cli.run("expense", "add", "lunch", "-a", "12")
    out = tmp_path / "export"
    result = cli.json("export", "--csv", str(out))
    assert result["tables"]["weight_log"] == 1
    assert result["tables"]["expense_entry"] == 1
    assert result["rows"] >= 2


def test_export_json_still_works_unchanged(cli, tmp_path):
    """The JSON path is unchanged when --csv isn't passed."""
    cli.run("weight", "log", "70")
    out = tmp_path / "export.json"
    result = cli.json("export", str(out))
    assert result["format"] == "json"
    assert out.exists()
    assert out.read_text().lstrip().startswith("{")  # JSON, not CSV
