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
