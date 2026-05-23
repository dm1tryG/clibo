"""Tests for ``clibo doctor``."""

from __future__ import annotations

from clibo import __version__


def test_doctor_reports_install(cli):
    data = cli.json("doctor")
    assert data["version"] == __version__
    assert data["tools_built"] >= 50
    assert data["tools_built"] == data["tools_planned"]
    assert data["healthy"] is True
    assert data["database_exists"] is True


def test_doctor_counts_rows(cli):
    cli.run("todo", "add", "task one")
    cli.run("todo", "add", "task two")
    cli.run("water", "drink", "500")
    data = cli.json("doctor")
    assert data["rows_per_table"].get("todo_task") == 2
    assert data["rows_per_table"].get("water_log") == 1
    assert data["total_rows"] >= 3


def test_doctor_python_version(cli):
    data = cli.json("doctor")
    parts = data["python"].split(".")
    assert int(parts[0]) >= 3


# ── new fields: warnings + schema-drift + unconfigured + update-check (iter 89) ──


def test_doctor_exposes_warnings_field(cli):
    """`warnings` is always present (empty when healthy)."""
    data = cli.json("doctor")
    assert "warnings" in data
    assert data["warnings"] == []
    assert data["healthy"] is True


def test_doctor_lists_unconfigured_settings(cli):
    """Fresh sandbox: every `clibo init` knob is unconfigured."""
    data = cli.json("doctor")
    settings = [u["setting"] for u in data["unconfigured_settings"]]
    assert "currency" in settings
    assert "height_cm" in settings


def test_doctor_unconfigured_shrinks_after_init(cli):
    cli.run("init", "--currency", "EUR")
    data = cli.json("doctor")
    settings = [u["setting"] for u in data["unconfigured_settings"]]
    assert "currency" not in settings
    assert "height_cm" in settings  # still missing


def test_doctor_schema_drift_empty_in_normal_install(cli):
    """A fresh init has no drift — the migration helper just ran."""
    data = cli.json("doctor")
    assert data["schema_drift"] == []


def test_doctor_detects_schema_drift(tmp_path):
    """Unit test for `_detect_schema_drift` — give it a DB where a real
    model's table is missing some columns, and it should report the gap.

    We test the helper directly because the CLI subprocess has its own
    SQLModel.metadata, so we can't inject a synthetic table through it.
    """
    import sqlite3

    import clibo.clis.films  # noqa: F401  ensure Film is registered
    from clibo.main import _detect_schema_drift
    db_path = tmp_path / "drift.db"
    con = sqlite3.connect(str(db_path))
    # Films model declares ~12 columns; we only create 2.
    con.execute("CREATE TABLE films_film (id INTEGER PRIMARY KEY, title TEXT)")
    con.commit()
    con.close()
    drift = _detect_schema_drift(db_path)
    films = next((d for d in drift if d["table"] == "films_film"), None)
    assert films is not None
    # `season` and `episode` were added in iter 87 — both should be flagged.
    assert "season" in films["missing_columns"]
    assert "episode" in films["missing_columns"]


def test_doctor_update_check_skipped_by_default(cli):
    """Without --check-updates, no network call and latest_version is None."""
    data = cli.json("doctor")
    assert data["latest_version"] is None
    assert data["update_available"] is False


def test_doctor_update_check_with_stub(cli, monkeypatch):
    """With --check-updates and a newer PyPI version, surface the upgrade."""
    from clibo import main as cli_main
    monkeypatch.setattr(cli_main, "_check_pypi_latest", lambda *a, **kw: "99.0.0")
    data = cli.json("doctor", "--check-updates")
    assert data["latest_version"] == "99.0.0"
    assert data["update_available"] is True
    assert any("99.0.0" in w for w in data["warnings"])
    assert data["healthy"] is False


def test_doctor_update_check_pypi_unreachable(cli, monkeypatch):
    """When PyPI is unreachable, update-check fails silently — still healthy."""
    from clibo import main as cli_main
    monkeypatch.setattr(cli_main, "_check_pypi_latest", lambda *a, **kw: None)
    data = cli.json("doctor", "--check-updates")
    assert data["latest_version"] is None
    assert data["update_available"] is False
    assert data["healthy"] is True


def test_version_tuple_compares_correctly():
    """Sanity check on the version-comparison helper."""
    from clibo.main import _version_tuple
    assert _version_tuple("1.9.0") < _version_tuple("1.10.0")
    assert _version_tuple("2.0.0") > _version_tuple("1.99.99")
    assert _version_tuple("1.9.0") == _version_tuple("1.9.0")
    # Pre-releases / suffixes: non-int chunks treated as 0
    assert _version_tuple("1.9.0a1") == (1, 9, 1)
