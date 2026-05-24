"""Tests for the 🙂 mood tool."""

from __future__ import annotations


def test_log_records_mood(cli):
    data = cli.json("mood", "log", "4", "-e", "Calm")
    assert data["score"] == 4
    assert data["label"] == "good"
    assert data["emotion"] == "calm"


def test_today_averages(cli):
    cli.run("mood", "log", "2")
    cli.run("mood", "log", "4")
    today = cli.json("mood", "today")
    assert len(today["checkins"]) == 2
    assert today["avg_score"] == 3.0


def test_stats_distribution_and_emotions(cli):
    cli.run("mood", "log", "5", "-e", "happy")
    cli.run("mood", "log", "5", "-e", "happy")
    cli.run("mood", "log", "3", "-e", "tired")
    stats = cli.json("mood", "stats")
    assert stats["checkins"] == 3
    assert stats["best_score"] == 5
    assert stats["top_emotions"][0] == {"emotion": "happy", "count": 2}


def test_remove(cli):
    entry = cli.json("mood", "log", "3")
    removed = cli.json("mood", "rm", str(entry["id"]))
    assert removed["deleted"] == entry["id"]


def test_invalid_score_fails(cli):
    result = cli.run("mood", "log", "7")
    assert result.exit_code != 0


def test_multiple_emotions_via_repeated_flag(cli):
    """`-e anxious -e excited` keeps both, in order, deduplicated."""
    data = cli.json("mood", "log", "3", "-e", "anxious", "-e", "excited")
    assert data["emotion"] == "anxious,excited"


def test_multiple_emotions_via_comma(cli):
    """`-e \"anxious,excited\"` is the equivalent comma-separated form."""
    data = cli.json("mood", "log", "3", "-e", "anxious, excited")
    assert data["emotion"] == "anxious,excited"


def test_emotions_are_deduplicated_and_lowercased(cli):
    """Repeated emotions collapse; case is normalised."""
    data = cli.json("mood", "log", "3", "-e", "Calm", "-e", "calm",
                    "-e", "FOCUSED")
    assert data["emotion"] == "calm,focused"


def test_no_emotion_stays_null(cli):
    data = cli.json("mood", "log", "4")
    assert data["emotion"] is None


# ── bare-command default (iter 105) ──


def test_bare_mood_runs_today(cli):
    """`clibo mood` (no subcommand) runs `today`."""
    result = cli.run("mood")
    assert result.exit_code == 0
    # No assertion on output content — that varies by tool.
    # Equivalence check: bare exits cleanly just like the explicit subcommand would.


def test_mood_help_still_works(cli):
    """`clibo mood --help` still shows the menu after the bare change."""
    result = cli.run("mood", "--help")
    assert result.exit_code == 0
    assert "today" in result.stdout
