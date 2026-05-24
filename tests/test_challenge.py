"""Tests for the 🚀 challenge tool."""

from __future__ import annotations

from datetime import date, timedelta


def test_start_basic(cli):
    data = cli.json("challenge", "start", "no sugar", "--days", "30")
    assert data["name"] == "no sugar"
    assert data["target_days"] == 30
    assert data["status"] == "active"
    assert data["days_elapsed"] == 1
    assert data["days_remaining"] == 29
    assert data["miss_budget"] == 0


def test_start_with_miss_budget(cli):
    data = cli.json(
        "challenge", "start", "100 days of code",
        "--days", "100", "-m", "5",
        "-D", "ship code every day",
    )
    assert data["miss_budget"] == 5
    assert data["description"] == "ship code every day"


def test_start_rejects_zero_or_negative_days(cli):
    assert cli.run("challenge", "start", "x", "--days", "0").exit_code != 0
    assert cli.run("challenge", "start", "x", "--days", "-3").exit_code != 0


def test_start_rejects_negative_miss_budget(cli):
    result = cli.run("challenge", "start", "x", "--days", "10", "-m", "-1")
    assert result.exit_code != 0


def test_check_success(cli):
    started = cli.json("challenge", "start", "no sugar", "--days", "30")
    data = cli.json("challenge", "check", str(started["id"]))
    assert data["hits"] == 1
    assert data["misses"] == 0
    assert data["today_status"] == "done"


def test_check_missed(cli):
    started = cli.json("challenge", "start", "no sugar", "--days", "30",
                        "-m", "1")
    data = cli.json("challenge", "check", str(started["id"]), "--missed")
    assert data["hits"] == 0
    assert data["misses"] == 1
    assert data["today_status"] == "missed"
    assert data["status"] == "active"  # miss budget covers it


def test_check_idempotent_overwrites(cli):
    """Checking in twice for the same day overwrites, not duplicates."""
    started = cli.json("challenge", "start", "x", "--days", "10")
    cli.run("challenge", "check", str(started["id"]))           # success
    cli.run("challenge", "check", str(started["id"]), "--missed")  # then missed
    data = cli.json("challenge", "show", str(started["id"]))
    assert len(data["checkins"]) == 1
    assert data["checkins"][0]["success"] is False


def test_miss_budget_exceeded_fails_challenge(cli):
    started = cli.json("challenge", "start", "strict", "--days", "10",
                        "-m", "0")
    cli.run("challenge", "check", str(started["id"]), "--missed")
    data = cli.json("challenge", "status", str(started["id"]))
    one = data["challenges"][0]
    assert one["status"] == "failed"


def test_miss_within_budget_keeps_challenge_active(cli):
    started = cli.json("challenge", "start", "lenient", "--days", "30",
                        "-m", "3")
    cli.run("challenge", "check", str(started["id"]), "--missed",
            "-d", "today")
    data = cli.json("challenge", "status", str(started["id"]))
    one = data["challenges"][0]
    assert one["status"] == "active"
    assert one["miss_budget_remaining"] == 2


def test_check_outside_window_fails(cli):
    started = cli.json("challenge", "start", "x", "--days", "10",
                        "--start", str(date.today()))
    result = cli.run(
        "challenge", "check", str(started["id"]),
        "-d", str(date.today() + timedelta(days=99)),
    )
    assert result.exit_code != 0


def test_check_already_finished_fails(cli):
    started = cli.json("challenge", "start", "strict", "--days", "5",
                        "-m", "0")
    cli.run("challenge", "check", str(started["id"]), "--missed")
    # Now it's failed; a second check-in attempt should be rejected.
    result = cli.run("challenge", "check", str(started["id"]))
    assert result.exit_code != 0


def test_today_lists_pending(cli):
    a = cli.json("challenge", "start", "A", "--days", "10")
    cli.json("challenge", "start", "B", "--days", "10")
    cli.run("challenge", "check", str(a["id"]))   # only A checked
    pending = cli.json("challenge", "today")
    names = {r["name"] for r in pending["pending"]}
    assert names == {"B"}


def test_list_defaults_to_active_only(cli):
    a = cli.json("challenge", "start", "Active", "--days", "30")
    cli.run("challenge", "abandon", str(a["id"]))
    cli.json("challenge", "start", "Other", "--days", "30")
    active_only = cli.json("challenge", "list")
    assert {r["name"] for r in active_only} == {"Other"}
    all_ = cli.json("challenge", "list", "--all")
    assert {r["name"] for r in all_} == {"Active", "Other"}


def test_abandon(cli):
    started = cli.json("challenge", "start", "x", "--days", "10")
    data = cli.json("challenge", "abandon", str(started["id"]))
    assert data["status"] == "abandoned"


def test_abandon_only_active(cli):
    started = cli.json("challenge", "start", "x", "--days", "10")
    cli.run("challenge", "abandon", str(started["id"]))
    result = cli.run("challenge", "abandon", str(started["id"]))
    assert result.exit_code != 0


def test_show_includes_checkins(cli):
    started = cli.json("challenge", "start", "x", "--days", "10")
    cli.run("challenge", "check", str(started["id"]))
    data = cli.json("challenge", "show", str(started["id"]))
    assert len(data["checkins"]) == 1
    assert data["checkins"][0]["success"] is True


def test_rm_cascades_checkins(cli):
    started = cli.json("challenge", "start", "x", "--days", "10")
    cli.run("challenge", "check", str(started["id"]))
    cli.run("challenge", "rm", str(started["id"]))
    # Listing should be empty; show should fail.
    assert cli.json("challenge", "list", "--all") == []
    assert cli.run("challenge", "show", str(started["id"])).exit_code != 0


def test_stats(cli):
    cli.run("challenge", "start", "Active", "--days", "30")
    # one that immediately fails
    failed = cli.json("challenge", "start", "Fail", "--days", "10", "-m", "0")
    cli.run("challenge", "check", str(failed["id"]), "--missed")
    # one abandoned
    aban = cli.json("challenge", "start", "Aban", "--days", "10")
    cli.run("challenge", "abandon", str(aban["id"]))
    data = cli.json("challenge", "stats")
    assert data["total"] == 3
    assert data["active"] == 1
    assert data["failed"] == 1
    assert data["abandoned"] == 1
    # Completion rate counts completed / (completed+failed) = 0/1 = 0.0
    assert data["completion_rate_pct"] == 0.0


def test_searchable_and_in_recent(cli):
    cli.run("challenge", "start", "Atomic Habits Challenge",
            "--days", "30", "-D", "build the habit")
    hits = cli.json("search", "Atomic")
    assert any(h["source"] == "challenge" for h in hits["results"])
    recent = cli.json("recent")
    assert any(e["source"] == "challenge" for e in recent["events"])



# ── bare-command default (iter 106) ──


def test_bare_challenge_runs_status(cli):
    """`clibo challenge` (no subcommand) runs `status`."""
    result = cli.run("challenge")
    assert result.exit_code == 0


def test_challenge_help_still_works(cli):
    """`clibo challenge --help` still shows the menu after the bare change."""
    result = cli.run("challenge", "--help")
    assert result.exit_code == 0
    assert "status" in result.stdout
