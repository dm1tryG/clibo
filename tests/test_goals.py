"""Tests for the 🎯 goals tool."""

from __future__ import annotations


def test_add_goal(cli):
    data = cli.json("goals", "add", "Learn Spanish", "-D", "Reach B1 level")
    assert data["name"] == "Learn Spanish"
    assert data["progress_pct"] == 0.0


def test_milestones_drive_progress(cli):
    cli.run("goals", "add", "Ship app")
    cli.run("goals", "milestone", "Ship app", "Design")
    m2 = cli.json("goals", "milestone", "Ship app", "Build")
    checked = cli.json("goals", "check", str(m2["id"]))
    assert checked["milestones_total"] == 2
    assert checked["milestones_done"] == 1
    assert checked["progress_pct"] == 50.0


def test_uncheck_milestone(cli):
    cli.run("goals", "add", "Goal")
    ms = cli.json("goals", "milestone", "Goal", "Step")
    cli.run("goals", "check", str(ms["id"]))
    data = cli.json("goals", "uncheck", str(ms["id"]))
    assert data["milestones_done"] == 0


def test_complete_goal(cli):
    cli.run("goals", "add", "Quick win")
    data = cli.json("goals", "complete", "Quick win")
    assert data["done"] is True
    assert cli.json("goals", "list") == []


def test_show_lists_milestones(cli):
    cli.run("goals", "add", "Big goal")
    cli.run("goals", "milestone", "Big goal", "First step")
    detail = cli.json("goals", "show", "Big goal")
    assert len(detail["milestones"]) == 1


def test_stats(cli):
    cli.run("goals", "add", "A")
    cli.run("goals", "add", "B")
    cli.run("goals", "complete", "A")
    stats = cli.json("goals", "stats")
    assert stats["total_goals"] == 2
    assert stats["achieved"] == 1


def test_milestone_unknown_goal_fails(cli):
    result = cli.run("goals", "milestone", "Ghost", "Step")
    assert result.exit_code != 0


def test_deadline_accepts_d_shortcut(cli):
    """`goals add -d` is the natural shorthand; was missing before."""
    data = cli.json("goals", "add", "Run a marathon", "-d", "in 6 months")
    assert data["name"] == "Run a marathon"
    assert data["deadline"] is not None


# ── bare-command default (iter 125) ──


def test_bare_goals_lists_active(cli):
    """`clibo goals` (no subcommand) lists active goals — iter-110 convention."""
    cli.run("goals", "add", "Read 30 books")
    cli.run("goals", "add", "Run 1000km")
    result = cli.run("goals")
    assert result.exit_code == 0
    assert "Read 30 books" in result.output
    assert "Run 1000km" in result.output


def test_bare_goals_empty_state(cli):
    """No goals → graceful empty state, not a crash."""
    result = cli.run("goals")
    assert result.exit_code == 0
    assert "No goals yet" in result.output


# ── is_behind_schedule + `goals list --at-risk` ──


def test_goal_without_deadline_is_never_behind(cli):
    """No deadline → no time pressure → not behind."""
    cli.run("goals", "add", "Open-ended")
    rows = cli.json("goals", "list")
    g = next(r for r in rows if r["name"] == "Open-ended")
    assert g["days_remaining"] is None
    assert g["is_behind_schedule"] is False


def test_goal_overdue_is_behind(cli):
    """Past-deadline goals that aren't done are at-risk by definition."""
    cli.run("goals", "add", "Overdue thing", "-d", "10 days ago")
    rows = cli.json("goals", "list")
    g = next(r for r in rows if r["name"] == "Overdue thing")
    assert g["days_remaining"] == -10
    assert g["is_behind_schedule"] is True


def test_goal_pacing_slower_than_calendar_is_behind(cli, tmp_path):
    """Calendar elapsed faster than milestone progress → behind."""
    cli.run("goals", "add", "Marathon", "-d", "in 30 days")
    cli.run("goals", "milestone", "Marathon", "Step 1")
    cli.run("goals", "milestone", "Marathon", "Step 2")
    # Backdate created so calendar progress is meaningful.
    import sqlite3
    con = sqlite3.connect(f"{tmp_path}/clibo.db")
    con.execute("UPDATE goals_goal SET created_at='2026-03-01 12:00:00' WHERE id=1")
    con.commit()
    con.close()
    rows = cli.json("goals", "list")
    g = rows[0]
    assert g["is_behind_schedule"] is True


def test_goal_done_is_never_behind(cli):
    """Completed goals can't be at risk — they're already shipped."""
    cli.run("goals", "add", "Shipped", "-d", "in 30 days")
    cli.run("goals", "complete", "Shipped")
    # Completed goals are filtered by default; pass --all to see them.
    rows = cli.json("goals", "list", "--all")
    g = next(r for r in rows if r["name"] == "Shipped")
    assert g["done"] is True
    assert g["is_behind_schedule"] is False


def test_at_risk_filter_excludes_on_track(cli, tmp_path):
    """`--at-risk` hides goals without a deadline + goals on pace."""
    cli.run("goals", "add", "On track", "-d", "in 30 days")
    cli.run("goals", "add", "Overdue", "-d", "5 days ago")
    cli.run("goals", "add", "Open-ended")
    rows = cli.json("goals", "list", "--at-risk")
    names = {r["name"] for r in rows}
    assert names == {"Overdue"}


def test_at_risk_empty_when_nothing_slipping(cli):
    """All goals on pace → empty at-risk view, friendly message."""
    cli.run("goals", "add", "Open one")
    result = cli.run("goals", "list", "--at-risk")
    assert result.exit_code == 0
    assert "No goals at risk" in result.output


def test_at_risk_pacing_slack(cli, tmp_path):
    """5-point slack means barely-behind isn't flagged."""
    cli.run("goals", "add", "Marathon", "-d", "in 100 days")
    cli.run("goals", "milestone", "Marathon", "M1")
    cli.run("goals", "milestone", "Marathon", "M2")
    cli.run("goals", "milestone", "Marathon", "M3")
    cli.run("goals", "milestone", "Marathon", "M4")
    cli.run("goals", "check", "1")   # 25% done
    # Backdate so 22 of 122 days elapsed → ~18% calendar, 25% progress.
    import sqlite3
    con = sqlite3.connect(f"{tmp_path}/clibo.db")
    con.execute("UPDATE goals_goal SET created_at='2026-05-02 12:00:00' WHERE id=1")
    con.commit()
    con.close()
    rows = cli.json("goals", "list")
    g = rows[0]
    assert g["is_behind_schedule"] is False  # ahead of pace
