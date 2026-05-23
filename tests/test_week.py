"""Tests for ``clibo week`` and its collector."""

from __future__ import annotations

from datetime import date, timedelta


def test_week_empty(cli):
    data = cli.json("week")
    assert data["days"] == 7
    assert data["sleep"]["nights_logged"] == 0
    assert data["expenses"]["entries"] == 0
    assert data["tasks"]["completed"] == 0


def test_week_sleep_and_focus(cli):
    cli.run("sleep", "log", "7", "-q", "4", "-d", "yesterday")
    cli.run("sleep", "log", "8", "-q", "5", "-d", "today")
    cli.run("focus", "log", "25", "-t", "writing")
    cli.run("focus", "log", "40", "-t", "review")
    data = cli.json("week")
    assert data["sleep"]["nights_logged"] == 2
    assert data["sleep"]["avg_hours"] == 7.5
    assert data["focus"]["sessions"] == 2
    assert data["focus"]["total_minutes"] == 65


def test_week_habits_track_target(cli):
    cli.run("habit", "add", "Stretch", "-t", "3")
    cli.run("habit", "check", "Stretch", "-d", "today")
    cli.run("habit", "check", "Stretch", "-d", "yesterday")
    cli.run("habit", "check", "Stretch", "-d", "2 days ago" if False else (date.today() - timedelta(days=2)).isoformat())
    data = cli.json("week")
    assert data["habits"]["tracked"] == 1
    habit = data["habits"]["items"][0]
    assert habit["done"] == 3
    assert habit["hit_target"] is True


def test_week_expenses_top_category(cli):
    cli.run("expense", "add", "lunch", "-a", "12", "-c", "food")
    cli.run("expense", "add", "dinner", "-a", "20", "-c", "food")
    cli.run("expense", "add", "bus", "-a", "3", "-c", "transport")
    data = cli.json("week")
    assert data["expenses"]["entries"] == 3
    assert data["expenses"]["total"] == 35.0
    assert data["expenses"]["top_category"]["category"] == "food"
    assert data["expenses"]["top_category"]["amount"] == 32.0


def test_week_tasks_completed_counted(cli):
    cli.run("todo", "add", "Done thing")
    task = cli.json("todo", "list")[0]
    cli.run("todo", "done", str(task["id"]))
    cli.run("todo", "add", "Still pending")
    data = cli.json("week")
    assert data["tasks"]["completed"] == 1


def test_week_water_goal_reached(cli):
    cli.run("water", "goal", "--set", "2000")
    cli.run("water", "drink", "2500")
    data = cli.json("week")
    assert data["water"]["days_logged"] == 1
    assert data["water"]["days_goal_reached"] == 1


# ──────────────────────────────────────────────────────────────────────
# Post-v1.0 tools surfaced in `week` (iter 69).
# ──────────────────────────────────────────────────────────────────────


def test_week_steps_aggregates(cli):
    cli.run("steps", "log", "6500")
    cli.run("steps", "log", "11000", "-d", "yesterday")
    data = cli.json("week")
    assert data["steps"]["days_logged"] == 2
    assert data["steps"]["total"] == 17500
    assert data["steps"]["days_goal_reached"] == 1  # only yesterday hit 10k


def test_week_workouts_aggregates(cli):
    cli.run("workout", "log", "running", "-t", "30", "-c", "350")
    cli.run("workout", "log", "stretching", "-t", "15")
    data = cli.json("week")
    assert data["workouts"]["sessions"] == 2
    assert data["workouts"]["total_minutes"] == 45
    assert data["workouts"]["total_kcal_burned"] == 350


def test_week_caffeine_aggregates(cli):
    cli.run("caffeine", "log", "espresso")  # 63
    cli.run("caffeine", "log", "coffee")    # 95
    data = cli.json("week")
    assert data["caffeine"]["drinks"] == 2
    assert data["caffeine"]["total_mg"] == 158


def test_week_fasting_aggregates(cli):
    cli.run("fasting", "start", "-T", "16", "-t", "3 days ago 08:00")
    cli.run("fasting", "stop", "-t", "3 days ago 22:00")     # 14h
    cli.run("fasting", "start", "-T", "16", "-t", "yesterday 06:00")
    cli.run("fasting", "stop", "-t", "yesterday 22:00")      # 16h hit
    data = cli.json("week")
    assert data["fasting"]["completed"] == 2
    assert data["fasting"]["total_hours"] == 30.0
    assert data["fasting"]["longest_hours"] == 16.0
    assert data["fasting"]["target_hits"] == 1


def test_week_meditate_aggregates(cli):
    cli.run("meditate", "log", "10")
    cli.run("meditate", "log", "15", "-d", "yesterday")
    data = cli.json("week")
    assert data["meditate"]["sessions"] == 2
    assert data["meditate"]["days"] == 2
    assert data["meditate"]["total_minutes"] == 25


def test_week_stretches_aggregates(cli):
    cli.run("stretches", "log", "hips", "-m", "10")
    cli.run("stretches", "log", "back", "-m", "5", "-d", "yesterday")
    data = cli.json("week")
    assert data["stretches"]["sessions"] == 2
    assert data["stretches"]["total_minutes"] == 15


def test_week_mileage_aggregates(cli):
    cli.run("mileage", "log", "5", "-a", "run")
    cli.run("mileage", "log", "10", "-a", "cycle", "-d", "yesterday")
    data = cli.json("week")
    assert data["mileage"]["sessions"] == 2
    assert data["mileage"]["total_km"] == 15.0
    assert data["mileage"]["by_activity"]["run"] == 5.0
    assert data["mileage"]["by_activity"]["cycle"] == 10.0


def test_week_gratitude_aggregates(cli):
    cli.run("gratitude", "add", "coffee")
    cli.run("gratitude", "add", "sunshine", "-d", "yesterday")
    data = cli.json("week")
    assert data["gratitude"]["entries"] == 2
    assert data["gratitude"]["days_logged"] == 2


def test_week_donations_aggregates(cli):
    cli.run("donations", "log", "Red Cross", "-a", "50")
    cli.run("donations", "log", "PAC", "-a", "100", "--no-deductible")
    data = cli.json("week")
    assert data["donations"]["entries"] == 2
    assert data["donations"]["total"] == 150.0
    assert data["donations"]["deductible_total"] == 50.0
    assert data["donations"]["recipients"] == 2


# ── writing + books on week (iter 93) ──


def test_week_includes_writing_block(cli):
    data = cli.json("week")
    assert "writing" in data
    assert data["writing"]["sessions"] == 0


def test_week_writing_aggregates_across_days(cli):
    cli.run("writing", "log", "novel", "-w", "1200", "-t", "45")
    cli.run("writing", "log", "novel", "-w", "1000", "-d", "yesterday")
    cli.run("writing", "log", "blog", "-w", "400", "-d", "yesterday")
    data = cli.json("week")
    w = data["writing"]
    assert w["sessions"] == 3
    assert w["total_words"] == 2600
    assert w["days_written"] == 2
    top = {p["category"]: p["amount"] for p in w["top_projects"]}
    assert top["novel"] == 2200
    assert top["blog"] == 400


def test_week_includes_books_block(cli):
    data = cli.json("week")
    assert "books" in data
    assert data["books"]["sessions"] == 0
    assert data["books"]["books"] == []


def test_week_books_aggregates_sessions(cli):
    cli.run("books", "add", "Atomic Habits", "-p", "320")
    cli.run("books", "read", "Atomic Habits", "30", "-t", "45")
    cli.run("books", "read", "Atomic Habits", "25", "-d", "yesterday")
    data = cli.json("week")
    b = data["books"]
    assert b["sessions"] == 2
    assert b["pages"] == 55
    assert b["days_read"] == 2
    assert b["books"] == ["Atomic Habits"]


# ── symptom block on week (iter 96) ──


def test_week_includes_symptoms_block(cli):
    data = cli.json("week")
    assert "symptoms" in data
    s = data["symptoms"]
    assert s["episodes"] == 0
    assert s["worst_name"] is None


def test_week_symptoms_aggregates_across_days(cli):
    cli.run("symptom", "log", "back pain", "-i", "7")
    cli.run("symptom", "log", "back pain", "-i", "5", "-d", "yesterday")
    cli.run("symptom", "log", "migraine", "-i", "9", "-d", "2 days ago")
    s = cli.json("week")["symptoms"]
    assert s["episodes"] == 3
    assert s["days_affected"] == 3
    assert s["avg_intensity"] == 7.0
    assert s["worst_intensity"] == 9
    assert s["worst_name"] == "migraine"
    top = {row["category"]: row["amount"] for row in s["top_symptoms"]}
    assert top["back pain"] == 2
    assert top["migraine"] == 1
