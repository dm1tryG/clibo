"""Tests for the ✍️ writing tool."""

from __future__ import annotations


def test_add_writing_session(cli):
    data = cli.json("writing", "log", "novel", "-w", "1200", "-t", "45")
    assert data["project"] == "novel"
    assert data["words"] == 1200
    assert data["duration_min"] == 45
    assert data["wpm"] == 26.7
    assert data["total_today"] == 1200
    assert data["current_streak"] == 1


def test_add_alias_works(cli):
    data = cli.json("writing", "add", "blog", "-w", "300")
    assert data["project"] == "blog"
    assert data["words"] == 300


def test_default_project(cli):
    """Project defaults to 'main' when omitted."""
    data = cli.json("writing", "log", "-w", "500")
    assert data["project"] == "main"


def test_words_negative_fails(cli):
    result = cli.run("writing", "log", "novel", "-w", "-5")
    assert result.exit_code != 0


def test_duration_negative_fails(cli):
    result = cli.run("writing", "log", "novel", "-w", "100", "-t", "-1")
    assert result.exit_code != 0


def test_wpm_only_when_duration_set(cli):
    data = cli.json("writing", "log", "novel", "-w", "500")
    assert data["wpm"] is None
    data2 = cli.json("writing", "log", "novel", "-w", "500", "-t", "10")
    assert data2["wpm"] == 50.0


def test_today_aggregates_by_project(cli):
    cli.run("writing", "log", "novel", "-w", "1200")
    cli.run("writing", "log", "blog", "-w", "400")
    cli.run("writing", "log", "novel", "-w", "300")
    today = cli.json("writing", "today")
    assert today["total_words"] == 1900
    assert today["sessions"] == 3
    by_proj = {r["project"]: r["words"] for r in today["by_project"]}
    assert by_proj["novel"] == 1500
    assert by_proj["blog"] == 400


def test_today_goal_progress(cli):
    cli.run("writing", "log", "novel", "-w", "600")  # over default goal of 500
    today = cli.json("writing", "today")
    assert today["goal_words"] == 500
    assert today["reached"] is True


def test_goal_set_and_persist(cli):
    cli.json("writing", "goal", "1667")
    today = cli.json("writing", "today")
    assert today["goal_words"] == 1667


def test_goal_show_default(cli):
    data = cli.json("writing", "goal")
    assert data["daily_words"] == 500


def test_goal_rejects_non_positive(cli):
    result = cli.run("writing", "goal", "0")
    assert result.exit_code != 0
    result = cli.run("writing", "goal", "-100")
    assert result.exit_code != 0


def test_streak_counts_consecutive_days(cli):
    cli.run("writing", "log", "novel", "-w", "500")
    cli.run("writing", "log", "novel", "-w", "500", "-d", "yesterday")
    cli.run("writing", "log", "novel", "-w", "500", "-d", "2 days ago")
    data = cli.json("writing", "streak")
    assert data["current_streak"] == 3
    assert data["longest_streak"] == 3
    assert data["days_written"] == 3


def test_streak_breaks_with_gap(cli):
    cli.run("writing", "log", "novel", "-w", "500")
    cli.run("writing", "log", "novel", "-w", "500", "-d", "3 days ago")
    data = cli.json("writing", "streak")
    assert data["current_streak"] == 1
    assert data["longest_streak"] == 1


def test_list_filters_by_project(cli):
    cli.run("writing", "log", "novel", "-w", "1000")
    cli.run("writing", "log", "blog", "-w", "300")
    novel_only = cli.json("writing", "list", "-p", "novel")
    assert all(e["project"] == "novel" for e in novel_only)
    assert len(novel_only) == 1


def test_show_by_project_name_picks_most_recent(cli):
    cli.run("writing", "log", "novel", "-w", "1000")
    latest = cli.json("writing", "log", "novel", "-w", "1500")
    data = cli.json("writing", "show", "novel")
    assert data["id"] == latest["id"]
    assert data["words"] == 1500


def test_edit_by_project(cli):
    cli.run("writing", "log", "novel", "-w", "1000")
    edited = cli.json("writing", "edit", "novel", "-w", "1100")
    assert edited["words"] == 1100


def test_edit_rejects_negative_words(cli):
    cli.run("writing", "log", "novel", "-w", "500")
    result = cli.run("writing", "edit", "novel", "-w", "-5")
    assert result.exit_code != 0


def test_rm_by_project(cli):
    cli.run("writing", "log", "doomed", "-w", "100")
    cli.json("writing", "rm", "doomed")
    listing = cli.json("writing", "list")
    assert not any(e["project"] == "doomed" for e in listing)


def test_unknown_project_fails(cli):
    result = cli.run("writing", "show", "ghost")
    assert result.exit_code != 0


def test_stats_top_projects_and_best_day(cli):
    cli.run("writing", "log", "novel", "-w", "1500")
    cli.run("writing", "log", "blog", "-w", "400")
    cli.run("writing", "log", "novel", "-w", "1000", "-d", "yesterday")
    data = cli.json("writing", "stats", "--days", "7")
    assert data["total_words"] == 2900
    assert data["top_projects"][0]["project"] == "novel"
    assert data["top_projects"][0]["words"] == 2500
    assert data["best_day"]["words"] == 1900


def test_stats_avg_wpm(cli):
    cli.run("writing", "log", "novel", "-w", "1000", "-t", "20")  # 50 wpm
    cli.run("writing", "log", "novel", "-w", "500", "-t", "10")   # 50 wpm
    data = cli.json("writing", "stats")
    assert data["avg_wpm"] == 50.0



# ── bare-command default (iter 106) ──


def test_bare_writing_runs_today(cli):
    """`clibo writing` (no subcommand) runs `today`."""
    result = cli.run("writing")
    assert result.exit_code == 0


def test_writing_help_still_works(cli):
    """`clibo writing --help` still shows the menu after the bare change."""
    result = cli.run("writing", "--help")
    assert result.exit_code == 0
    assert "today" in result.stdout


# ── writing year: annual rollup ──


def test_writing_year_aggregates_total_and_sessions(cli):
    cli.run("writing", "log", "novel", "-w", "500")
    cli.run("writing", "log", "novel", "-w", "1200")
    cli.run("writing", "log", "blog", "-w", "400")
    data = cli.json("writing", "year")
    assert data["total_words"] == 2100
    assert data["sessions"] == 3
    assert data["days_written"] == 1
    # Two projects, sorted by words desc.
    assert data["by_project"][0] == {"project": "novel", "words": 1700}
    assert data["by_project"][1] == {"project": "blog", "words": 400}


def test_writing_year_biggest_session_picks_max(cli):
    cli.run("writing", "log", "novel", "-w", "500")
    cli.run("writing", "log", "novel", "-w", "1200")
    big = cli.json("writing", "year")["biggest_session"]
    assert big["words"] == 1200
    assert big["project"] == "novel"


def test_writing_year_by_month_has_12_slots(cli):
    cli.run("writing", "log", "novel", "-w", "1000")
    data = cli.json("writing", "year")
    assert len(data["by_month"]) == 12
    assert {m["month"] for m in data["by_month"]} == set(range(1, 13))


def test_writing_year_project_filter_is_fuzzy(cli):
    cli.run("writing", "log", "main-novel", "-w", "1000")
    cli.run("writing", "log", "blog", "-w", "400")
    data = cli.json("writing", "year", "--project", "novel")
    assert data["total_words"] == 1000
    assert data["sessions"] == 1
    assert data["project"] == "novel"


def test_writing_year_empty_state_is_safe(cli):
    """No sessions → zero totals, biggest_session is null, no crash."""
    data = cli.json("writing", "year")
    assert data["total_words"] == 0
    assert data["sessions"] == 0
    assert data["biggest_session"] is None
    assert data["biggest_month"] is None


def test_writing_year_specific_year_argument(cli):
    """--year Y restricts to that calendar year."""
    cli.run("writing", "log", "novel", "-w", "500")
    data = cli.json("writing", "year", "--year", "1999")
    assert data["year"] == 1999
    assert data["total_words"] == 0
