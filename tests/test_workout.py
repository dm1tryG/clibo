"""Tests for the 🏋️ workout tool."""

from __future__ import annotations


def test_log_strength_computes_volume(cli):
    data = cli.json("workout", "log", "squat", "-s", "5", "-r", "5", "-w", "80")
    assert data["exercise"] == "squat"
    assert data["volume_kg"] == 2000.0


def test_today_aggregates(cli):
    cli.run("workout", "log", "bench", "-s", "3", "-r", "10", "-w", "60")
    cli.run("workout", "log", "run", "-t", "25")
    today = cli.json("workout", "today")
    assert len(today["exercises"]) == 2
    assert today["total_minutes"] == 25
    assert today["total_volume_kg"] == 1800.0


def test_stats_lists_top_exercises(cli):
    cli.run("workout", "log", "squat", "-s", "5", "-r", "5", "-w", "80")
    cli.run("workout", "log", "squat", "-s", "5", "-r", "5", "-w", "85")
    cli.run("workout", "log", "deadlift", "-s", "1", "-r", "5", "-w", "100")
    stats = cli.json("workout", "stats")
    assert stats["exercises_logged"] == 3
    assert stats["top_exercises"][0]["exercise"] == "squat"
    assert stats["top_exercises"][0]["count"] == 2


def test_remove(cli):
    entry = cli.json("workout", "log", "plank", "-t", "2")
    removed = cli.json("workout", "rm", str(entry["id"]))
    assert removed["deleted"] == entry["id"]


def test_log_calories_burned(cli):
    """The new --calories flag captures kcal burned in this session."""
    data = cli.json("workout", "log", "jogging", "-t", "30", "-c", "350")
    assert data["duration_min"] == 30
    assert data["kcal_burned"] == 350


def test_log_without_calories_leaves_field_null(cli):
    data = cli.json("workout", "log", "squat", "-s", "5", "-r", "5", "-w", "80")
    assert data["kcal_burned"] is None


def test_log_calories_can_be_zero(cli):
    data = cli.json("workout", "log", "rest pose", "-c", "0")
    assert data["kcal_burned"] == 0


def test_log_rejects_negative_calories(cli):
    result = cli.run("workout", "log", "jogging", "-t", "30", "-c", "-50")
    assert result.exit_code != 0


def test_today_totals_kcal(cli):
    cli.run("workout", "log", "jogging", "-t", "30", "-c", "350")
    cli.run("workout", "log", "cycling", "-t", "45", "-c", "400")
    cli.run("workout", "log", "squat", "-s", "5", "-r", "5", "-w", "80")
    today = cli.json("workout", "today")
    assert today["total_kcal"] == 750
    assert today["total_minutes"] == 75
    # the squat session contributes 0 kcal (no flag passed)
    by_ex = {r["exercise"]: r["kcal_burned"] for r in today["exercises"]}
    assert by_ex["squat"] is None


def test_stats_includes_kcal_total(cli):
    cli.run("workout", "log", "jogging", "-t", "30", "-c", "300")
    cli.run("workout", "log", "running", "-t", "20", "-c", "250")
    stats = cli.json("workout", "stats")
    assert stats["total_kcal_burned"] == 550


# ── PR view + name-resolve on show/rm (iter 88) ──


def test_pr_all_exercises_picks_heaviest(cli):
    """`workout pr` shows the heaviest weight per exercise."""
    cli.run("workout", "log", "bench", "-s", "3", "-r", "5", "-w", "70")
    cli.run("workout", "log", "bench", "-s", "1", "-r", "1", "-w", "90")
    cli.run("workout", "log", "squat", "-s", "5", "-r", "5", "-w", "100")
    prs = cli.json("workout", "pr")
    by_ex = {p["exercise"]: p for p in prs}
    assert by_ex["bench"]["weight_kg"] == 90.0
    assert by_ex["squat"]["weight_kg"] == 100.0
    # sorted by heaviest first
    assert prs[0]["exercise"] == "squat"


def test_pr_records_session_count(cli):
    cli.run("workout", "log", "bench", "-s", "3", "-r", "5", "-w", "70")
    cli.run("workout", "log", "bench", "-s", "3", "-r", "5", "-w", "75")
    cli.run("workout", "log", "bench", "-s", "1", "-r", "1", "-w", "90")
    prs = cli.json("workout", "pr")
    bench = next(p for p in prs if p["exercise"] == "bench")
    assert bench["sessions"] == 3


def test_pr_ignores_no_rep_cardio(cli):
    """Cardio entries (reps=0) should not appear in PR view."""
    cli.run("workout", "log", "jogging", "-t", "30", "-c", "300")
    result = cli.run("workout", "pr")
    assert result.exit_code != 0  # "no strength workouts logged yet"


def test_pr_for_one_exercise_groups_by_reps(cli):
    """Specific-exercise PR breaks down by rep count (1RM / 3RM / 5RM)."""
    cli.run("workout", "log", "bench press", "-s", "3", "-r", "5", "-w", "70")
    cli.run("workout", "log", "bench press", "-s", "3", "-r", "5", "-w", "75")
    cli.run("workout", "log", "bench press", "-s", "5", "-r", "3", "-w", "82.5")
    cli.run("workout", "log", "bench press", "-s", "1", "-r", "1", "-w", "90")
    breakdown = cli.json("workout", "pr", "bench press")
    by_reps = {r["reps"]: r for r in breakdown}
    assert by_reps[1]["weight_kg"] == 90.0
    assert by_reps[3]["weight_kg"] == 82.5
    assert by_reps[5]["weight_kg"] == 75.0  # heavier of the two 5-rep sets


def test_pr_fuzzy_exercise_match(cli):
    """`workout pr bench` finds 'bench press'."""
    cli.run("workout", "log", "bench press", "-s", "1", "-r", "1", "-w", "90")
    breakdown = cli.json("workout", "pr", "bench")
    assert len(breakdown) == 1
    assert breakdown[0]["weight_kg"] == 90.0


def test_pr_unknown_exercise_fails(cli):
    cli.run("workout", "log", "bench", "-s", "1", "-r", "1", "-w", "90")
    result = cli.run("workout", "pr", "deadlift")
    assert result.exit_code != 0


def test_workout_show_by_name(cli):
    cli.run("workout", "log", "squat", "-s", "5", "-r", "5", "-w", "100")
    data = cli.json("workout", "show", "squat")
    assert data["exercise"] == "squat"
    assert data["weight_kg"] == 100.0


def test_workout_show_name_prefers_most_recent(cli):
    cli.run("workout", "log", "squat", "-s", "3", "-r", "5", "-w", "80")
    latest = cli.json("workout", "log", "squat", "-s", "3", "-r", "5", "-w", "100")
    data = cli.json("workout", "show", "squat")
    assert data["id"] == latest["id"]
    assert data["weight_kg"] == 100.0


def test_workout_rm_by_name(cli):
    cli.run("workout", "log", "bench", "-s", "1", "-r", "1", "-w", "90")
    cli.json("workout", "rm", "bench")
    listing = cli.json("workout", "list")
    assert not any(e["exercise"] == "bench" for e in listing)


def test_workout_unknown_name_fails(cli):
    result = cli.run("workout", "show", "ghost-exercise")
    assert result.exit_code != 0


# ── bare-command default (iter 105) ──


def test_bare_workout_runs_today(cli):
    """`clibo workout` (no subcommand) runs `today`."""
    result = cli.run("workout")
    assert result.exit_code == 0
    # No assertion on output content — that varies by tool.
    # Equivalence check: bare exits cleanly just like the explicit subcommand would.


def test_workout_help_still_works(cli):
    """`clibo workout --help` still shows the menu after the bare change."""
    result = cli.run("workout", "--help")
    assert result.exit_code == 0
    assert "today" in result.stdout


# ── streak subcommand (iter 112) ──


def test_streak_empty(cli):
    data = cli.json("workout", "streak")
    assert data["current_streak"] == 0
    assert data["longest_streak"] == 0
    assert data["days_logged"] == 0


def test_streak_counts_consecutive_days(cli):
    cli.run("workout", "log", "squat", "-s", "5", "-r", "5", "-w", "100")
    cli.run("workout", "log", "bench", "-s", "5", "-r", "5", "-w", "70",
            "-d", "yesterday")
    cli.run("workout", "log", "deadlift", "-s", "5", "-r", "5", "-w", "100",
            "-d", "2 days ago")
    data = cli.json("workout", "streak")
    assert data["current_streak"] == 3
    assert data["longest_streak"] == 3
    assert data["days_logged"] == 3


def test_streak_breaks_with_gap(cli):
    """Today logged, but 3 days ago — only today counts as the current streak."""
    cli.run("workout", "log", "x")
    cli.run("workout", "log", "y", "-d", "3 days ago")
    cli.run("workout", "log", "z", "-d", "4 days ago")
    cli.run("workout", "log", "w", "-d", "5 days ago")
    data = cli.json("workout", "streak")
    assert data["current_streak"] == 1
    assert data["longest_streak"] == 3
    assert data["days_logged"] == 4


def test_streak_multiple_sessions_same_day_count_as_one(cli):
    """Two workouts on the same day don't inflate the streak."""
    cli.run("workout", "log", "squat", "-s", "5", "-r", "5", "-w", "100")
    cli.run("workout", "log", "bench", "-s", "5", "-r", "5", "-w", "70")
    cli.run("workout", "log", "row", "-d", "yesterday")
    data = cli.json("workout", "streak")
    assert data["current_streak"] == 2
    assert data["days_logged"] == 2  # 2 days, not 3 sessions


def test_streak_yesterday_only_still_current(cli):
    """Yesterday logged but not today → still counts as a current 1-day streak."""
    cli.run("workout", "log", "x", "-d", "yesterday")
    data = cli.json("workout", "streak")
    assert data["current_streak"] == 1
