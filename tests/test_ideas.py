"""Tests for the 💡 ideas tool."""

from __future__ import annotations


def test_capture_idea(cli):
    data = cli.json("ideas", "add", "build a plugin marketplace", "-t", "clibo,community")
    assert data["title"] == "build a plugin marketplace"
    assert data["status"] == "raw"
    assert data["tags"] == "clibo,community"


def test_move_through_lifecycle(cli):
    idea = cli.json("ideas", "add", "Pomodoro variant", "-D", "60/15 instead of 25/5")
    cli.run("ideas", "move", str(idea["id"]), "exploring")
    cli.run("ideas", "move", str(idea["id"]), "validated")
    shipped = cli.json("ideas", "move", str(idea["id"]), "shipped")
    assert shipped["status"] == "shipped"


def test_open_filter(cli):
    cli.run("ideas", "add", "Active 1", "-s", "raw")
    cli.run("ideas", "add", "Active 2", "-s", "exploring")
    cli.run("ideas", "add", "Done", "-s", "shipped")
    cli.run("ideas", "add", "Killed", "-s", "abandoned")
    open_ideas = cli.json("ideas", "list", "--open")
    titles = {i["title"] for i in open_ideas}
    assert titles == {"Active 1", "Active 2"}


def test_search_finds_in_description(cli):
    cli.run("ideas", "add", "X", "-D", "marketplace for plugins")
    cli.run("ideas", "add", "Y", "-D", "unrelated thing")
    results = cli.json("ideas", "search", "marketplace")
    assert len(results) == 1
    assert results[0]["title"] == "X"


def test_pipeline_counts(cli):
    cli.run("ideas", "add", "A", "-s", "raw")
    cli.run("ideas", "add", "B", "-s", "raw")
    cli.run("ideas", "add", "C", "-s", "shipped")
    pipe = cli.json("ideas", "pipeline")
    assert pipe["by_status"]["raw"] == 2
    assert pipe["by_status"]["shipped"] == 1
    assert pipe["total"] == 3


def test_invalid_status_fails(cli):
    result = cli.run("ideas", "add", "Bad", "-s", "incubating")
    assert result.exit_code != 0


# ── ideas stale: surface open ideas that have grown cold ──


def _backdate_idea(home_dir, title: str, days_ago: int) -> None:
    """Helper: walk an idea's updated_at back N days."""
    import sqlite3
    from datetime import datetime, timedelta
    when = (datetime.now() - timedelta(days=days_ago)).isoformat(" ", "seconds")
    con = sqlite3.connect(f"{home_dir}/clibo.db")
    con.execute(
        "UPDATE ideas_idea SET updated_at=? WHERE title=?",
        (when, title),
    )
    con.commit()
    con.close()


def test_ideas_stale_picks_old_open_ideas(cli, tmp_path):
    cli.run("ideas", "add", "Fresh idea", "-s", "raw")
    cli.run("ideas", "add", "Stale raw", "-s", "raw")
    _backdate_idea(str(tmp_path), "Stale raw", days_ago=60)
    rows = cli.json("ideas", "stale")
    titles = [r["title"] for r in rows]
    assert "Stale raw" in titles
    assert "Fresh idea" not in titles
    stale = next(r for r in rows if r["title"] == "Stale raw")
    assert stale["days_since_update"] >= 59


def test_ideas_stale_excludes_shipped_and_abandoned(cli, tmp_path):
    """Only open-status ideas (raw / exploring / validated) count."""
    cli.run("ideas", "add", "Shipped one", "-s", "shipped")
    cli.run("ideas", "add", "Abandoned one", "-s", "abandoned")
    cli.run("ideas", "add", "Open one", "-s", "raw")
    for t in ("Shipped one", "Abandoned one", "Open one"):
        _backdate_idea(str(tmp_path), t, days_ago=60)
    rows = cli.json("ideas", "stale")
    titles = {r["title"] for r in rows}
    assert titles == {"Open one"}


def test_ideas_stale_threshold_filters(cli, tmp_path):
    """`--days 90` only flags ideas older than 90 days."""
    cli.run("ideas", "add", "60d old", "-s", "raw")
    cli.run("ideas", "add", "100d old", "-s", "raw")
    _backdate_idea(str(tmp_path), "60d old", days_ago=60)
    _backdate_idea(str(tmp_path), "100d old", days_ago=100)
    rows = cli.json("ideas", "stale", "--days", "90")
    titles = [r["title"] for r in rows]
    assert titles == ["100d old"]


def test_ideas_stale_negative_days_fails(cli):
    result = cli.run("ideas", "stale", "--days", "-1")
    assert result.exit_code != 0


def test_ideas_stale_empty_when_all_fresh(cli):
    """Empty list when nothing's stale — graceful empty state."""
    cli.run("ideas", "add", "Fresh", "-s", "raw")
    rows = cli.json("ideas", "stale")
    assert rows == []


def test_ideas_stale_sorted_oldest_first(cli, tmp_path):
    """Oldest-touch first so triage starts with the most-neglected."""
    cli.run("ideas", "add", "Older", "-s", "raw")
    cli.run("ideas", "add", "Newer", "-s", "raw")
    _backdate_idea(str(tmp_path), "Older", days_ago=90)
    _backdate_idea(str(tmp_path), "Newer", days_ago=45)
    rows = cli.json("ideas", "stale")
    assert [r["title"] for r in rows] == ["Older", "Newer"]
