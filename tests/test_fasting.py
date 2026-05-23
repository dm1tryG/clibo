"""Tests for the 🕒 fasting tool."""

from __future__ import annotations


def test_start_default_target(cli):
    data = cli.json("fasting", "start")
    assert data["ongoing"] is True
    assert data["target_hours"] == 16.0       # default
    assert data["end_time"] is None


def test_start_custom_target(cli):
    data = cli.json("fasting", "start", "-T", "20")
    assert data["target_hours"] == 20.0


def test_start_rejects_second_concurrent(cli):
    cli.run("fasting", "start")
    result = cli.run("fasting", "start", "-T", "18")
    assert result.exit_code != 0


def test_start_rejects_non_positive_target(cli):
    assert cli.run("fasting", "start", "-T", "0").exit_code != 0
    assert cli.run("fasting", "start", "-T", "-5").exit_code != 0


def test_stop_completes_the_fast(cli):
    cli.run("fasting", "start")
    data = cli.json("fasting", "stop")
    assert data["ongoing"] is False
    assert data["end_time"] is not None


def test_stop_with_no_active_fails(cli):
    result = cli.run("fasting", "stop")
    assert result.exit_code != 0


def test_stop_rejects_pre_start_time(cli):
    cli.run("fasting", "start", "-t", "yesterday 12:00")
    result = cli.run("fasting", "stop", "-t", "yesterday 10:00")
    assert result.exit_code != 0


def test_status_when_not_fasting_no_history(cli):
    data = cli.json("fasting", "status")
    assert data["ongoing"] is False
    assert data["last"] is None


def test_status_when_not_fasting_with_history(cli):
    cli.run("fasting", "start", "-t", "yesterday 08:00")
    cli.run("fasting", "stop", "-t", "yesterday 12:00")
    data = cli.json("fasting", "status")
    assert data["ongoing"] is False
    assert data["last"] is not None
    # 12:00 - 08:00 = 4 hours
    assert data["last"]["duration_hours"] == 4.0


def test_status_when_fasting(cli):
    cli.run("fasting", "start", "-T", "16")
    data = cli.json("fasting", "status")
    assert data["ongoing"] is True
    assert "remaining_hours" in data


def test_target_set_and_get(cli):
    data = cli.json("fasting", "target", "--set", "18")
    assert data["target_hours"] == 18.0
    again = cli.json("fasting", "target")
    assert again["target_hours"] == 18.0
    # Subsequent `start` uses the new default.
    started = cli.json("fasting", "start")
    assert started["target_hours"] == 18.0


def test_target_rejects_non_positive(cli):
    assert cli.run("fasting", "target", "--set", "0").exit_code != 0


def test_list_default_includes_ongoing(cli):
    cli.run("fasting", "start")
    rows = cli.json("fasting", "list")
    assert len(rows) == 1
    assert rows[0]["ongoing"] is True


def test_list_completed_only_hides_ongoing(cli):
    cli.run("fasting", "start", "-t", "yesterday 08:00")
    cli.run("fasting", "stop", "-t", "yesterday 16:00")
    cli.run("fasting", "start")  # second, still ongoing
    rows = cli.json("fasting", "list", "--completed")
    assert all(r["end_time"] is not None for r in rows)
    assert len(rows) == 1


def test_show_then_rm(cli):
    f = cli.json("fasting", "start", "-T", "16")
    fetched = cli.json("fasting", "show", str(f["id"]))
    assert fetched["target_hours"] == 16.0
    cli.run("fasting", "rm", str(f["id"]))
    assert cli.json("fasting", "list") == []


def test_stats_summary(cli):
    # Three completed fasts at varying durations, all backdated so the
    # times can't accidentally land in the future regardless of the
    # wall-clock hour the suite runs at.
    cli.run("fasting", "start", "-t", "3 days ago 08:00")
    cli.run("fasting", "stop", "-t", "3 days ago 20:00")    # 12h
    cli.run("fasting", "start", "-t", "2 days ago 06:00")
    cli.run("fasting", "stop", "-t", "2 days ago 22:00")    # 16h — hits target
    cli.run("fasting", "start", "-t", "yesterday 07:00")
    cli.run("fasting", "stop", "-t", "yesterday 15:00")     # 8h
    data = cli.json("fasting", "stats")
    assert data["completed_fasts"] == 3
    assert data["total_hours_fasted"] == 36.0
    assert data["avg_duration_hours"] == 12.0
    assert data["longest_fast_hours"] == 16.0
    # 1 of 3 hit the default 16h target
    assert data["hits"] == 1
    assert data["target_hit_rate_pct"] == pytest_approx(33.3)


def test_searchable_and_in_recent(cli):
    cli.run("fasting", "start", "-T", "20", "-n", "OMAD experiment")
    hits = cli.json("search", "OMAD")
    assert any(h["source"] == "fasting" for h in hits["results"])
    recent = cli.json("recent")
    assert any(e["source"] == "fasting" for e in recent["events"])


# Small helper since we want fuzzy equality but don't want a hard dep on
# pytest.approx in this file's import block.
def pytest_approx(value, tol=0.5):
    class _:
        def __eq__(self, other):
            return abs(other - value) <= tol
    return _()
