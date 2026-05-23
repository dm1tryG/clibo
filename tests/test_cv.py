"""Tests for the 📜 cv tool."""

from __future__ import annotations


def test_add_job(cli):
    data = cli.json(
        "cv", "add", "Senior Engineer",
        "-o", "Acme", "-k", "job",
        "--start", "2024-01", "--end", "2026-04",
        "-l", "Remote",
    )
    assert data["title"] == "Senior Engineer"
    assert data["org"] == "Acme"
    assert data["kind"] == "job"
    assert data["start_date"] == "2024-01-01"
    assert data["end_date"] == "2026-04-01"
    assert data["current"] is False


def test_current_entry_has_no_end(cli):
    data = cli.json("cv", "add", "Founder", "-o", "Self", "--start", "2025-06")
    assert data["current"] is True
    assert data["end_date"] is None


def test_end_closes_an_entry(cli):
    entry = cli.json("cv", "add", "Engineer", "-o", "X", "--start", "2023-01")
    ended = cli.json("cv", "end", str(entry["id"]), "--on", "2024-06")
    assert ended["end_date"] == "2024-06-01"
    assert ended["current"] is False


def test_achieve_appends_bullets(cli):
    entry = cli.json("cv", "add", "Engineer", "-o", "Y")
    cli.run("cv", "achieve", str(entry["id"]), "Shipped the API")
    data = cli.json("cv", "achieve", str(entry["id"]), "Cut latency 40%")
    assert "Shipped the API" in data["achievements"]
    assert "Cut latency 40%" in data["achievements"]


def test_current_filter(cli):
    cli.run("cv", "add", "Past role", "--start", "2020-01", "--end", "2022-01")
    cli.run("cv", "add", "Current role", "--start", "2024-01")
    rows = cli.json("cv", "current")
    assert len(rows) == 1
    assert rows[0]["title"] == "Current role"


def test_list_filters_by_kind(cli):
    cli.run("cv", "add", "Engineer", "-k", "job")
    cli.run("cv", "add", "BSc CS", "-k", "education")
    education = cli.json("cv", "list", "-k", "education")
    assert len(education) == 1


def test_stats_approx_years(cli):
    cli.run("cv", "add", "Job 1", "-k", "job", "--start", "2020-01", "--end", "2022-01")
    cli.run("cv", "add", "Job 2", "-k", "job", "--start", "2022-02", "--end", "2024-02")
    stats = cli.json("cv", "stats")
    # ~24 + ~24 = ~48 months ≈ 4 years
    assert 3.9 <= stats["approx_job_years"] <= 4.1


def test_invalid_kind_fails(cli):
    result = cli.run("cv", "add", "Bad", "-k", "thing")
    assert result.exit_code != 0


def test_end_before_start_fails(cli):
    cli.run("cv", "add", "X", "--start", "2024-01")
    result = cli.run("cv", "end", "1", "--on", "2023-01")
    assert result.exit_code != 0


# ── name resolution (iter 84) ──


def test_cv_show_by_title(cli):
    cli.run("cv", "add", "Staff Engineer", "-o", "Acme", "-k", "job",
            "--start", "2020-01")
    data = cli.json("cv", "show", "Staff")
    assert "Staff" in data["title"]


def test_cv_end_by_title(cli):
    cli.run("cv", "add", "Staff Engineer", "-o", "Acme", "-k", "job",
            "--start", "2020-01")
    cli.run("cv", "end", "Staff", "--on", "2024-06")
    data = cli.json("cv", "show", "Staff")
    assert data["end_date"] is not None


def test_cv_achieve_by_title(cli):
    cli.run("cv", "add", "Staff Engineer", "-o", "Acme", "-k", "job",
            "--start", "2020-01")
    cli.run("cv", "achieve", "Staff", "Led the migration to event-driven arch")
    data = cli.json("cv", "show", "Staff")
    assert "migration" in (data.get("achievements") or "")
