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


# ── writing + books on today (iter 93) ──


def test_today_includes_writing_block(cli):
    data = cli.json("today")
    assert "writing" in data
    # Empty case — no sessions yet
    assert data["writing"]["sessions"] == 0
    assert data["writing"]["total_words"] == 0


def test_today_writing_aggregates_sessions(cli):
    cli.run("writing", "log", "novel", "-w", "1200", "-t", "45")
    cli.run("writing", "log", "blog", "-w", "400")
    data = cli.json("today")
    w = data["writing"]
    assert w["sessions"] == 2
    assert w["total_words"] == 1600
    assert w["reached"] is True  # default goal 500
    assert w["current_streak"] == 1


def test_today_writing_respects_goal(cli):
    cli.run("writing", "goal", "1667")
    cli.run("writing", "log", "novel", "-w", "1200")
    data = cli.json("today")
    assert data["writing"]["goal_words"] == 1667
    assert data["writing"]["reached"] is False


def test_today_includes_books_block(cli):
    data = cli.json("today")
    assert "books" in data
    assert data["books"]["sessions"] == 0
    assert data["books"]["pages"] == 0
    assert data["books"]["books"] == []


def test_today_books_aggregates_sessions(cli):
    cli.run("books", "add", "Atomic Habits", "-p", "320")
    cli.run("books", "read", "Atomic Habits", "30", "-t", "45")
    cli.run("books", "add", "Range", "-p", "260")
    cli.run("books", "read", "Range", "20", "-t", "30")
    data = cli.json("today")
    b = data["books"]
    assert b["sessions"] == 2
    assert b["pages"] == 50
    assert b["minutes"] == 75
    assert sorted(b["books"]) == ["Atomic Habits", "Range"]


# ── symptom block on today (iter 96) ──


def test_today_includes_symptoms_block(cli):
    data = cli.json("today")
    assert "symptoms" in data
    s = data["symptoms"]
    assert s["episodes"] == 0
    assert s["worst_intensity"] == 0
    assert s["worst_name"] is None


def test_today_symptoms_aggregates_episodes(cli):
    cli.run("symptom", "log", "back pain", "-i", "7")
    cli.run("symptom", "log", "migraine", "-i", "9")
    cli.run("symptom", "log", "back pain", "-i", "5", "-d", "yesterday")
    s = cli.json("today")["symptoms"]
    assert s["episodes"] == 2  # today only
    assert s["worst_intensity"] == 9
    assert s["worst_name"] == "migraine"
    assert sorted(s["names"]) == ["back pain", "migraine"]


# ── tasks.done_today on the snapshot (iter 125) ──


def _set_done_at(home_dir, task_id: int, when: date) -> None:
    """Helper: backdate a task's completion to `when`. Tests need this
    because `todo done` always stamps `done_at = today`."""
    import sqlite3
    con = sqlite3.connect(f"{home_dir}/clibo.db")
    con.execute(
        "UPDATE todo_task SET done=1, done_at=? WHERE id=?",
        (when.isoformat(), task_id),
    )
    con.commit()
    con.close()


def test_today_lists_tasks_completed_today(cli, tmp_path):
    """`today.tasks.done_today` shows tasks finished today."""
    cli.run("todo", "add", "Ship it", "-p", "high")
    cli.run("todo", "done", "1")
    data = cli.json("today")
    titles = [t["title"] for t in data["tasks"]["done_today"]]
    assert "Ship it" in titles


def test_yesterday_lists_tasks_completed_yesterday(cli, tmp_path):
    """Answers 'what did I get done yesterday?' — the natural ask."""
    cli.run("todo", "add", "Shipped yesterday", "-p", "high")
    cli.run("todo", "add", "Still pending")
    _set_done_at(str(tmp_path), 1, date.today() - timedelta(days=1))
    data = cli.json("yesterday")
    titles = [t["title"] for t in data["tasks"]["done_today"]]
    assert titles == ["Shipped yesterday"]


def test_today_done_today_excludes_other_days(cli, tmp_path):
    """Tasks completed on different days don't leak into today's view."""
    cli.run("todo", "add", "Done two days ago")
    _set_done_at(str(tmp_path), 1, date.today() - timedelta(days=2))
    data = cli.json("today")
    assert data["tasks"]["done_today"] == []


def test_yesterday_done_today_empty_when_nothing_finished(cli):
    """No completed-yesterday tasks → empty list, not missing key."""
    data = cli.json("yesterday")
    assert data["tasks"]["done_today"] == []


def test_done_today_preserves_priority(cli):
    """The done-today block carries priority through."""
    cli.run("todo", "add", "Critical", "-p", "high")
    cli.run("todo", "done", "1")
    item = cli.json("today")["tasks"]["done_today"][0]
    assert item["priority"] == "high"
    assert item["title"] == "Critical"
