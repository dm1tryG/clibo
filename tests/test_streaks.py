"""Tests for `clibo streaks` — global view of every active streak."""

from __future__ import annotations


def test_streaks_empty(cli):
    data = cli.json("streaks")
    assert data["count"] == 0
    assert data["streaks"] == []


def test_streaks_includes_habit(cli):
    cli.run("habit", "add", "Read")
    cli.run("habit", "check", "Read")
    data = cli.json("streaks")
    sources = {row["source"] for row in data["streaks"]}
    assert "habit" in sources
    read = next(r for r in data["streaks"] if r["name"] == "Read")
    assert read["current"] == 1
    assert read["longest"] == 1


def test_streaks_includes_gratitude(cli):
    for d in (0, 1, 2):
        cli.run("gratitude", "add", f"thing-{d}", "-d", f"{d} days ago")
    data = cli.json("streaks")
    grat = next(r for r in data["streaks"] if r["source"] == "gratitude")
    assert grat["current"] == 3


def test_streaks_steps_goal_streak(cli):
    cli.run("steps", "goal", "--set", "5000")
    for d in (0, 1, 2):
        cli.run("steps", "log", "6000", "-d", f"{d} days ago")
    data = cli.json("streaks")
    steps = next(r for r in data["streaks"] if r["source"] == "steps")
    assert steps["current"] == 3


def test_streaks_sorted_by_current_desc(cli):
    """Streaks are listed strongest-first."""
    cli.run("habit", "add", "Short")
    cli.run("habit", "check", "Short")
    cli.run("habit", "add", "Long")
    for d in (0, 1, 2, 3, 4):
        cli.run("habit", "check", "Long", "-d", f"{d} days ago")
    data = cli.json("streaks")
    # The first habit row should be "Long" (5-day) before "Short" (1-day).
    habit_rows = [r for r in data["streaks"] if r["source"] == "habit"]
    assert habit_rows[0]["name"] == "Long"
    assert habit_rows[0]["current"] == 5
    assert habit_rows[1]["name"] == "Short"


def test_streaks_includes_active_challenge(cli):
    started = cli.json("challenge", "start", "no sugar", "--days", "30")
    cli.run("challenge", "check", str(started["id"]))
    data = cli.json("streaks")
    chal = next(r for r in data["streaks"] if r["source"] == "challenge")
    assert chal["name"] == "no sugar"
    assert chal["current"] == 1


def test_streaks_ignores_finished_challenges(cli):
    started = cli.json("challenge", "start", "x", "--days", "10")
    cli.run("challenge", "check", str(started["id"]))
    cli.run("challenge", "abandon", str(started["id"]))
    data = cli.json("streaks")
    challenges = [r for r in data["streaks"] if r["source"] == "challenge"]
    assert challenges == []


def test_streaks_steps_no_streak_when_below_goal(cli):
    cli.run("steps", "goal", "--set", "10000")
    cli.run("steps", "log", "5000")  # below goal
    data = cli.json("streaks")
    steps = [r for r in data["streaks"] if r["source"] == "steps"]
    assert steps == []  # no streak surfaced


# ── workout added to the streaks aggregator (iter 112) ──


def test_streaks_includes_workout(cli):
    """`clibo streaks` now surfaces workout streak alongside habits/gratitude."""
    cli.run("workout", "log", "squat", "-s", "5", "-r", "5", "-w", "100")
    cli.run("workout", "log", "bench", "-d", "yesterday")
    data = cli.json("streaks")
    sources = [s["source"] for s in data["streaks"]]
    assert "workout" in sources
    workout_row = next(s for s in data["streaks"] if s["source"] == "workout")
    assert workout_row["current"] == 2
    assert workout_row["name"] == "Workout days"


# ── mileage / meditate / stretches added to the aggregator (iter 113) ──


def test_streaks_includes_mileage(cli):
    cli.run("mileage", "log", "5")
    cli.run("mileage", "log", "3", "-d", "yesterday")
    data = cli.json("streaks")
    sources = [s["source"] for s in data["streaks"]]
    assert "mileage" in sources


def test_streaks_includes_meditate(cli):
    cli.run("meditate", "log", "15")
    cli.run("meditate", "log", "10", "-d", "yesterday")
    data = cli.json("streaks")
    sources = [s["source"] for s in data["streaks"]]
    assert "meditate" in sources


def test_streaks_includes_stretches(cli):
    cli.run("stretches", "log", "hamstrings", "-m", "10")
    cli.run("stretches", "log", "hips", "-m", "15", "-d", "yesterday")
    data = cli.json("streaks")
    sources = [s["source"] for s in data["streaks"]]
    assert "stretches" in sources


# ── streaks --at-risk + done_today field ──


def test_streaks_done_today_true_when_logged(cli):
    """A habit checked today has done_today=True in the aggregated view."""
    cli.run("habit", "add", "Read")
    cli.run("habit", "check", "Read", "-d", "yesterday")
    cli.run("habit", "check", "Read")
    data = cli.json("streaks")
    row = next(s for s in data["streaks"] if s["name"] == "Read")
    assert row["done_today"] is True
    assert row["current"] == 2


def test_streaks_done_today_false_when_streak_through_yesterday(cli):
    """Streaked through yesterday but not today → done_today is False."""
    cli.run("habit", "add", "Read")
    cli.run("habit", "check", "Read", "-d", "2 days ago")
    cli.run("habit", "check", "Read", "-d", "yesterday")
    data = cli.json("streaks")
    row = next(s for s in data["streaks"] if s["name"] == "Read")
    assert row["done_today"] is False
    assert row["current"] == 2  # still active, just at-risk


def test_streaks_at_risk_filter_excludes_done_today(cli):
    """`streaks --at-risk` hides streaks already continued today."""
    cli.run("habit", "add", "Read")
    cli.run("habit", "add", "Exercise")
    cli.run("habit", "check", "Read", "-d", "yesterday")
    cli.run("habit", "check", "Read")        # streaked today (safe)
    cli.run("habit", "check", "Exercise", "-d", "yesterday")  # not yet today
    data = cli.json("streaks", "--at-risk")
    names = {s["name"] for s in data["streaks"]}
    assert "Read" not in names           # done today, hidden
    assert "Exercise" in names           # at risk, shown
    assert data["at_risk_filter"] is True


def test_streaks_at_risk_filter_excludes_inactive(cli):
    """current==0 streaks (no longer alive) aren't 'at risk' — already lost."""
    cli.run("habit", "add", "Lapsed")
    cli.run("habit", "check", "Lapsed", "-d", "5 days ago")
    cli.run("habit", "check", "Lapsed", "-d", "4 days ago")
    # Gap of multiple days — current streak is 0.
    data = cli.json("streaks", "--at-risk")
    assert all(s["current"] > 0 for s in data["streaks"])


def test_streaks_at_risk_empty_when_everything_done(cli):
    """All streaks continued today → empty at-risk view, friendly message."""
    cli.run("habit", "add", "Read")
    cli.run("habit", "check", "Read")
    data = cli.json("streaks", "--at-risk")
    assert data["count"] == 0
    result = cli.run("streaks", "--at-risk")
    assert result.exit_code == 0
    assert "No streaks at risk" in result.output


def test_streaks_human_view_marks_done_today(cli):
    """Human view shows ✓ done today on continued streaks."""
    cli.run("habit", "add", "Read")
    cli.run("habit", "check", "Read", "-d", "yesterday")
    cli.run("habit", "check", "Read")
    result = cli.run("streaks")
    assert "done today" in result.output
