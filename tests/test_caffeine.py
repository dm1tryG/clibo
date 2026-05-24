"""Tests for the ☕ caffeine tool."""

from __future__ import annotations

from datetime import date, timedelta

import pytest


def test_log_uses_preset_mg(cli):
    data = cli.json("caffeine", "log", "espresso")
    assert data["drink"] == "espresso"
    assert data["mg"] == 63


def test_log_with_explicit_mg_overrides_preset(cli):
    data = cli.json("caffeine", "log", "coffee", "-m", "120")
    assert data["mg"] == 120


def test_log_with_explicit_mg_for_unknown_drink(cli):
    data = cli.json("caffeine", "log", "yerba-mate-strong", "-m", "150")
    assert data["mg"] == 150


def test_log_unknown_drink_without_mg_fails(cli):
    result = cli.run("caffeine", "log", "moonjuice")
    assert result.exit_code != 0
    assert "preset" in result.output.lower() or "mg" in result.output.lower()


def test_log_negative_mg_rejected(cli):
    result = cli.run("caffeine", "log", "coffee", "-m", "-50")
    assert result.exit_code != 0


def test_log_drink_normalizes_case_and_spaces(cli):
    data = cli.json("caffeine", "log", "  ESPRESSO  ")
    assert data["drink"] == "espresso"
    assert data["mg"] == 63


def test_log_with_explicit_time(cli):
    data = cli.json("caffeine", "log", "coffee", "-t", "09:30")
    assert data["consumed_at"].endswith("09:30:00")


def test_log_rejects_bad_time_format(cli):
    result = cli.run("caffeine", "log", "coffee", "-t", "9am")
    assert result.exit_code != 0


def test_add_alias_works(cli):
    log_help = cli.run("caffeine", "log", "--help")
    add_help = cli.run("caffeine", "add", "--help")
    assert log_help.exit_code == 0 and "Usage:" in log_help.output
    assert add_help.exit_code == 0 and "Usage:" in add_help.output
    cli.run("caffeine", "add", "matcha")
    today = cli.json("caffeine", "today")
    assert today["drinks"] == 1


def test_today_sums_mg(cli):
    cli.run("caffeine", "log", "espresso")          # 63
    cli.run("caffeine", "log", "latte")             # 75
    cli.run("caffeine", "log", "coffee", "-m", "100")
    today = cli.json("caffeine", "today")
    assert today["drinks"] == 3
    assert today["total_mg"] == 63 + 75 + 100


def test_today_over_limit_flag(cli):
    cli.run("caffeine", "log", "cold-brew")  # 200
    cli.run("caffeine", "log", "cold-brew")  # 200
    cli.run("caffeine", "log", "monster")    # 160
    today = cli.json("caffeine", "today")
    assert today["total_mg"] == 560
    assert today["over_limit"] is True


def test_today_residual_is_present_in_json(cli):
    cli.run("caffeine", "log", "coffee")
    today = cli.json("caffeine", "today")
    # residual should be a non-negative number (could be ~0 if bedtime is
    # many hours away but still defined)
    assert "residual_at_bedtime_mg" in today
    assert today["residual_at_bedtime_mg"] >= 0


def test_residual_decays_with_time(cli):
    """A morning coffee leaves less residual than a late-evening one."""
    morning = cli.json(
        "caffeine", "log", "coffee", "-t", "08:00",
        "-d", str(date.today() - timedelta(days=0)),
    )
    morning_resid = morning["residual_at_bedtime_mg"]
    cli.run("caffeine", "rm", str(morning["id"]))
    evening = cli.json("caffeine", "log", "coffee", "-t", "20:00")
    evening_resid = evening["residual_at_bedtime_mg"]
    assert evening_resid > morning_resid


def test_cutoff_lists_each_preset(cli):
    rows = cli.json("caffeine", "cutoff")
    drinks = {r["drink"] for r in rows}
    # Spot-check a handful of known presets are listed.
    assert {"espresso", "coffee", "matcha", "redbull"} <= drinks


def test_bedtime_set_and_get(cli):
    data = cli.json("caffeine", "bedtime", "--set", "22:30")
    assert data["bedtime"] == "22:30"
    again = cli.json("caffeine", "bedtime")
    assert again["bedtime"] == "22:30"


def test_bedtime_rejects_bad_format(cli):
    result = cli.run("caffeine", "bedtime", "--set", "10pm")
    assert result.exit_code != 0


def test_list_filters_by_drink(cli):
    cli.run("caffeine", "log", "espresso")
    cli.run("caffeine", "log", "matcha")
    only_matcha = cli.json("caffeine", "list", "--drink", "matcha")
    assert len(only_matcha) == 1
    assert only_matcha[0]["drink"] == "matcha"


def test_stats(cli):
    cli.run("caffeine", "log", "espresso", "-d", "today")
    cli.run("caffeine", "log", "coffee", "-d", "today")
    cli.run("caffeine", "log", "latte", "-d", "yesterday")
    data = cli.json("caffeine", "stats", "--days", "7")
    assert data["entries"] == 3
    assert data["days_logged"] == 2
    assert data["total_mg"] == 63 + 95 + 75
    assert data["by_drink_count"] == {
        "espresso": 1, "coffee": 1, "latte": 1,
    }


def test_rm(cli):
    entry = cli.json("caffeine", "log", "espresso")
    cli.run("caffeine", "rm", str(entry["id"]))
    today = cli.json("caffeine", "today")
    assert today["drinks"] == 0


def test_searchable_and_in_recent(cli):
    cli.run("caffeine", "log", "matcha", "-n", "ceremonial grade")
    hits = cli.json("search", "ceremonial")
    assert any(h["source"] == "caffeine" for h in hits["results"])
    recent = cli.json("recent")
    assert any(e["source"] == "caffeine" for e in recent["events"])


def test_residual_decay_math():
    """Sanity-check the half-life math directly."""
    from datetime import datetime

    from clibo.clis.caffeine import HALF_LIFE_HOURS, CaffeineEntry, _residual_at
    entry = CaffeineEntry(
        drink="coffee", mg=100,
        consumed_at=datetime(2026, 5, 23, 12, 0),
        entry_date=date(2026, 5, 23),
    )
    # After one half-life, residual should be ~50% of mg.
    later = datetime(2026, 5, 23, 12, 0) + timedelta(hours=HALF_LIFE_HOURS)
    assert _residual_at(entry, later) == pytest.approx(50, rel=0.01)
    # Two half-lives → 25%.
    later2 = datetime(2026, 5, 23, 12, 0) + timedelta(hours=2 * HALF_LIFE_HOURS)
    assert _residual_at(entry, later2) == pytest.approx(25, rel=0.01)


# ── bare-command default (iter 104) ──


def test_bare_caffeine_runs_today(cli):
    """`clibo caffeine` (no subcommand) shows today's intake."""
    cli.run("caffeine", "log", "coffee", "-m", "200")
    result = cli.run("caffeine")
    assert result.exit_code == 0
    assert "Caffeine" in result.stdout or "caffeine" in result.stdout
    assert "200" in result.stdout


def test_caffeine_help_still_works(cli):
    """`clibo caffeine --help` still shows the menu."""
    result = cli.run("caffeine", "--help")
    assert result.exit_code == 0
    assert "log" in result.stdout
    assert "today" in result.stdout


# ── caffeine today: remaining_mg + pct_of_limit ──


def test_caffeine_today_under_limit(cli):
    cli.run("caffeine", "log", "Espresso", "-m", "75")
    data = cli.json("caffeine", "today")
    assert data["total_mg"] == 75
    assert data["daily_limit_mg"] == 400
    assert data["over_limit"] is False
    assert data["remaining_mg"] == 325
    assert data["pct_of_limit"] == 18.8


def test_caffeine_today_over_limit(cli):
    cli.run("caffeine", "log", "Coffee", "-m", "500")
    data = cli.json("caffeine", "today")
    assert data["over_limit"] is True
    assert data["remaining_mg"] == -100
    assert data["pct_of_limit"] == 125.0
