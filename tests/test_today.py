"""Tests for ``clibo today`` and the dashboard collector."""

from __future__ import annotations

from datetime import date, timedelta


def test_today_empty_state(cli):
    data = cli.json("today")
    assert data["tasks"]["pending"] == 0
    assert data["habits"]["total"] == 0
    assert data["events"] == []
    assert data["bills"] == []


def test_today_aggregates_tasks(cli):
    past = (date.today() - timedelta(days=2)).isoformat()
    cli.run("todo", "add", "Overdue thing", "-d", past, "-p", "high")
    cli.run("todo", "add", "Today thing", "-d", "today")
    data = cli.json("today")
    assert data["tasks"]["pending"] == 2
    assert len(data["tasks"]["overdue"]) == 1
    assert data["tasks"]["overdue"][0]["title"] == "Overdue thing"
    assert len(data["tasks"]["due_today"]) == 1


def test_today_includes_water_and_habits(cli):
    cli.run("water", "drink", "500")
    cli.run("habit", "add", "Read")
    cli.run("habit", "check", "Read")
    data = cli.json("today")
    assert data["water"]["total_ml"] == 500
    assert data["habits"]["total"] == 1
    assert data["habits"]["done_today"] == 1


def test_today_bills_and_followups(cli):
    past = (date.today() - timedelta(days=1)).isoformat()
    cli.run("bills", "add", "Internet", "-d", past, "-a", "40")
    cli.run("followup", "add", "Anna", "-d", past)
    data = cli.json("today")
    assert any(b["overdue"] for b in data["bills"])
    assert any(f["overdue"] for f in data["followups"])


def test_today_birthdays(cli):
    today = date.today()
    cli.run("birthdays", "add", "Mom", "-d", f"{today.month:02d}-{today.day:02d}")
    data = cli.json("today")
    assert any(b["person"] == "Mom" for b in data["birthdays"])


def test_today_plants_and_chores(cli):
    cli.run("plants", "add", "Basil", "-w", "1")
    cli.run("chores", "add", "Dishes", "-e", "1")
    data = cli.json("today")
    assert any(p["name"] == "Basil" for p in data["plants_thirsty"])
    assert any(c["name"] == "Dishes" for c in data["chores_due"])


# ──────────────────────────────────────────────────────────────────────
# Post-v1.0 tool integration into `today` (iter 68).
# ──────────────────────────────────────────────────────────────────────


def test_today_includes_mood(cli):
    cli.run("mood", "log", "4", "-e", "calm")
    data = cli.json("today")
    assert data["mood"] is not None
    assert data["mood"]["score"] == 4
    assert data["mood"]["emotion"] == "calm"
    assert data["mood"]["checkins"] == 1


def test_today_mood_none_when_no_checkin(cli):
    data = cli.json("today")
    assert data["mood"] is None


def test_today_includes_steps(cli):
    cli.run("steps", "log", "6500")
    data = cli.json("today")
    assert data["steps"]["total"] == 6500
    assert data["steps"]["goal"] == 10000  # default
    assert data["steps"]["reached"] is False


def test_today_workouts(cli):
    cli.run("workout", "log", "running", "-t", "30", "-c", "350")
    cli.run("workout", "log", "stretching", "-t", "10")
    data = cli.json("today")
    assert data["workouts"]["sessions"] == 2
    assert data["workouts"]["minutes"] == 40
    assert data["workouts"]["kcal"] == 350


def test_today_caffeine(cli):
    cli.run("caffeine", "log", "espresso")  # 63 mg
    cli.run("caffeine", "log", "latte")     # 75 mg
    data = cli.json("today")
    assert data["caffeine"]["drinks"] == 2
    assert data["caffeine"]["mg_today"] == 138
    # residual_at_bedtime is computed; just check the key is present and non-negative
    assert data["caffeine"]["residual_at_bedtime_mg"] >= 0


def test_today_fasting_in_progress(cli):
    cli.run("fasting", "start", "-T", "16")
    data = cli.json("today")
    assert data["fasting"] is not None
    assert data["fasting"]["target_hours"] == 16.0
    assert data["fasting"]["elapsed_hours"] >= 0


def test_today_fasting_none_when_no_active_fast(cli):
    data = cli.json("today")
    assert data["fasting"] is None


def test_today_pending_challenge_checkins(cli):
    cli.run("challenge", "start", "no sugar", "--days", "30")
    cli.run("challenge", "start", "100 days of code", "--days", "100")
    data = cli.json("today")
    pending_names = {c["name"] for c in data["challenges_pending"]}
    assert pending_names == {"no sugar", "100 days of code"}


def test_today_challenge_disappears_after_checkin(cli):
    ch = cli.json("challenge", "start", "no sugar", "--days", "30")
    cli.run("challenge", "check", str(ch["id"]))
    data = cli.json("today")
    assert data["challenges_pending"] == []


def test_today_late_packages(cli):
    from datetime import date as date_
    from datetime import timedelta
    today_str = str(date_.today() - timedelta(days=2))
    cli.run("packages", "add", "LateOne", "-e", today_str)
    cli.run("packages", "add", "OnTime")
    data = cli.json("today")
    assert data["packages"]["pending"] == 2
    late_names = {p["sender"] for p in data["packages"]["late"]}
    assert late_names == {"LateOne"}


def test_today_documents_expiring_within_30_days(cli):
    from datetime import date as date_
    from datetime import timedelta
    today = date_.today()
    cli.run("documents", "add", "Passport",
            "-e", str(today + timedelta(days=15)), "-k", "passport")
    cli.run("documents", "add", "Far",
            "-e", str(today + timedelta(days=200)), "-k", "other")
    data = cli.json("today")
    names = {d["name"] for d in data["documents_expiring"]}
    assert names == {"Passport"}


# ──────────────────────────────────────────────────────────────────────
# `today --on DATE` and `clibo yesterday` (iter 74).
# ──────────────────────────────────────────────────────────────────────


def test_today_on_yesterday_shows_yesterdays_logs(cli):
    from datetime import date as date_
    from datetime import timedelta
    cli.run("mood", "log", "3", "-e", "tired", "-d", "yesterday")
    cli.run("mood", "log", "5", "-e", "great")  # today's entry
    data = cli.json("today", "--on", "yesterday")
    assert data["date"] == str(date_.today() - timedelta(days=1))
    assert data["mood"] is not None
    assert data["mood"]["score"] == 3


def test_today_default_still_targets_today(cli):
    from datetime import date as date_
    data = cli.json("today")
    assert data["date"] == str(date_.today())


def test_today_on_iso_date(cli):
    """ISO date strings work too."""
    from datetime import date as date_
    from datetime import timedelta
    yesterday = date_.today() - timedelta(days=1)
    cli.run("steps", "log", "8500", "-d", "yesterday")
    data = cli.json("today", "--on", str(yesterday))
    assert data["date"] == str(yesterday)
    assert data["steps"]["total"] == 8500


def test_yesterday_command(cli):
    """`clibo yesterday` is the alias for `today --on yesterday`."""
    from datetime import date as date_
    from datetime import timedelta
    cli.run("water", "drink", "500", "-d", "yesterday")
    data = cli.json("yesterday")
    assert data["date"] == str(date_.today() - timedelta(days=1))
    assert data["water"]["total_ml"] == 500
