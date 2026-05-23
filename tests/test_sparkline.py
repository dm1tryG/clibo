"""Tests for the ASCII sparkline helpers + integration into `stats` views."""

from __future__ import annotations

from datetime import date, timedelta

from clibo.core.sparkline import sparkline, sparkline_days


def test_sparkline_empty():
    assert sparkline([]) == ""


def test_sparkline_all_none():
    assert sparkline([None, None, None]) == ""


def test_sparkline_constant_series():
    """A flat series renders as a single mid-level block, repeated."""
    out = sparkline([5, 5, 5, 5])
    assert len(out) == 4
    assert out == "▄" * 4


def test_sparkline_monotonic_rise():
    """A rising series should produce strictly-monotone block indices."""
    out = sparkline([1, 2, 3, 4, 5, 6, 7, 8])
    blocks = "▁▂▃▄▅▆▇█"
    assert out == blocks


def test_sparkline_none_gap_renders_as_dot():
    out = sparkline([1, None, 5, None, 10])
    assert out[1] == "·"
    assert out[3] == "·"
    # Non-None positions render real blocks.
    assert out[0] in "▁▂▃▄▅▆▇█"
    assert out[2] in "▁▂▃▄▅▆▇█"
    assert out[4] in "▁▂▃▄▅▆▇█"


def test_sparkline_days_gap_filled():
    """Missing days in a date range render as ·."""
    today = date(2026, 5, 23)
    by_date = {
        today - timedelta(days=4): 1.0,
        today - timedelta(days=2): 5.0,
        today: 10.0,
    }
    out = sparkline_days(by_date, today - timedelta(days=4), today)
    # Five days; positions 0/2/4 have data, 1/3 are gaps.
    assert len(out) == 5
    assert out[1] == "·"
    assert out[3] == "·"


def test_sparkline_days_empty_dict():
    today = date(2026, 5, 23)
    assert sparkline_days({}, today - timedelta(days=6), today) == ""


# Integration: every stats command now exposes a 'chart' field.


def test_weight_stats_chart(cli):
    cli.run("weight", "log", "75", "-d", "5 days ago")
    cli.run("weight", "log", "74", "-d", "3 days ago")
    cli.run("weight", "log", "73.5", "-d", "yesterday")
    data = cli.json("weight", "stats", "--days", "7")
    assert data["chart"]
    # 3 measurements → 3 chars in the sparkline.
    assert len(data["chart"]) == 3


def test_sleep_stats_chart(cli):
    cli.run("sleep", "log", "7", "-d", "5 days ago")
    cli.run("sleep", "log", "8", "-d", "yesterday")
    data = cli.json("sleep", "stats", "--days", "7")
    assert "chart" in data


def test_steps_stats_chart(cli):
    cli.run("steps", "log", "8000", "-d", "yesterday")
    cli.run("steps", "log", "9000", "-d", "today")
    data = cli.json("steps", "stats", "--days", "7")
    assert "chart" in data


def test_mood_stats_chart(cli):
    cli.run("mood", "log", "3", "-d", "yesterday")
    cli.run("mood", "log", "5", "-d", "today")
    data = cli.json("mood", "stats", "--days", "7")
    assert "chart" in data


def test_caffeine_stats_chart(cli):
    cli.run("caffeine", "log", "coffee", "-d", "yesterday")
    cli.run("caffeine", "log", "latte", "-d", "today")
    data = cli.json("caffeine", "stats", "--days", "7")
    assert "chart" in data


def test_expense_stats_chart(cli):
    cli.run("expense", "add", "lunch", "-a", "12", "-d", "yesterday")
    cli.run("expense", "add", "dinner", "-a", "30", "-d", "today")
    data = cli.json("expense", "stats", "--days", "7")
    assert "chart" in data
