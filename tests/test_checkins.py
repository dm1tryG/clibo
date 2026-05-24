"""Tests for the daily check-in detection + `clibo checkin` command."""

from __future__ import annotations


def _seed_active_weight(cli, days_ago_list=(1, 2, 3)):
    """Log a few prior weight entries so the tracker registers as active."""
    for d in days_ago_list:
        cli.run("weight", "log", str(70 + d), "-d", f"{d} days ago")


def test_inactive_tracker_is_not_surfaced(cli):
    """A tracker with < 2 entries in 14 days does NOT show up."""
    cli.run("weight", "log", "70")  # only one entry
    data = cli.json("today")
    weight_in = [c for c in data["checkins"] if c["name"] == "Weight"]
    assert weight_in == []


def test_active_tracker_appears_pending(cli):
    """≥ 2 entries in 14 days → tracker is active; today not logged → pending."""
    _seed_active_weight(cli)
    data = cli.json("today")
    weight = next(c for c in data["checkins"] if c["name"] == "Weight")
    assert weight["logged_today"] is False
    assert weight["last_value"] is not None
    assert weight["last_days_ago"] == 1


def test_active_tracker_appears_logged(cli):
    """If today is logged, the tracker shows up with today_value set."""
    _seed_active_weight(cli)
    cli.run("weight", "log", "70.5")  # today
    data = cli.json("today")
    weight = next(c for c in data["checkins"] if c["name"] == "Weight")
    assert weight["logged_today"] is True
    assert weight["today_value"] == "70.5 kg"


def test_multiple_trackers_surface(cli):
    """Mood + sleep + steps + gratitude all seed-able as active in parallel."""
    for d in (1, 2, 3):
        cli.run("weight", "log", "70", "-d", f"{d} days ago")
        cli.run("mood", "log", "4", "-d", f"{d} days ago")
        cli.run("sleep", "log", "7", "-d", f"{d} days ago")
        cli.run("steps", "log", "8000", "-d", f"{d} days ago")
        cli.run("gratitude", "add", "x", "-d", f"{d} days ago")
    data = cli.json("today")
    names = {c["name"] for c in data["checkins"]}
    assert names == {"Weight", "Mood", "Sleep", "Steps", "Gratitude"}


def test_checkin_command_json(cli):
    """`clibo checkin --json` returns pending + logged splits."""
    _seed_active_weight(cli)
    for d in (1, 2):
        cli.run("mood", "log", "4", "-d", f"{d} days ago")
    cli.run("mood", "log", "5")  # logged today
    data = cli.json("checkin")
    assert data["logged_count"] == 1
    assert data["pending_count"] == 1
    assert data["logged"][0]["name"] == "Mood"
    assert data["pending"][0]["name"] == "Weight"


def test_checkin_command_pending_includes_question_and_command(cli):
    _seed_active_weight(cli)
    data = cli.json("checkin")
    weight = data["pending"][0]
    assert weight["question"] == "What's your weight today?"
    assert weight["command"].startswith("clibo weight log")


def test_checkin_command_all_done(cli):
    """When every active tracker has a today entry, the human-readable view
    says everything's in. JSON returns empty pending."""
    _seed_active_weight(cli)
    cli.run("weight", "log", "70.5")  # today
    data = cli.json("checkin")
    assert data["pending_count"] == 0
    assert data["logged_count"] == 1


def test_checkin_command_no_active_trackers(cli):
    """A fresh clibo with no recent activity returns an empty checkins list."""
    data = cli.json("checkin")
    assert data["pending_count"] == 0
    assert data["logged_count"] == 0
    assert data["pending"] == []


# ── new trackers: writing + symptom (iter 97) ──


def test_writing_active_tracker_surfaces(cli):
    cli.run("writing", "log", "novel", "-w", "500")
    cli.run("writing", "log", "novel", "-w", "800", "-d", "yesterday")
    data = cli.json("checkin")
    names = [c["name"] for c in data["logged"] + data["pending"]]
    assert "Writing" in names


def test_writing_today_value_shows_words_and_project(cli):
    cli.run("writing", "log", "novel", "-w", "1200")
    cli.run("writing", "log", "blog", "-w", "300", "-d", "yesterday")
    data = cli.json("checkin")
    writing = next(
        c for c in data["logged"] + data["pending"] if c["name"] == "Writing"
    )
    assert "1200w" in writing["today_value"]
    assert "novel" in writing["today_value"]


def test_symptom_active_tracker_surfaces(cli):
    cli.run("symptom", "log", "back pain", "-i", "7")
    cli.run("symptom", "log", "back pain", "-i", "5", "-d", "yesterday")
    data = cli.json("checkin")
    names = [c["name"] for c in data["logged"] + data["pending"]]
    assert "Symptom" in names


def test_symptom_today_value_includes_intensity_and_location(cli):
    cli.run("symptom", "log", "back pain", "-i", "7", "-l", "lumbar")
    cli.run("symptom", "log", "back pain", "-i", "5", "-d", "yesterday")
    data = cli.json("checkin")
    sym = next(
        c for c in data["logged"] + data["pending"] if c["name"] == "Symptom"
    )
    assert "back pain" in sym["today_value"]
    assert "7/10" in sym["today_value"]
    assert "lumbar" in sym["today_value"]


def test_single_writing_entry_is_not_active(cli):
    """A single entry shouldn't pollute the check-in list."""
    cli.run("writing", "log", "novel", "-w", "500")
    data = cli.json("checkin")
    names = [c["name"] for c in data["logged"] + data["pending"]]
    assert "Writing" not in names


# ── --all flag for discovery (iter 129) ──


def test_checkin_all_lists_every_tracker_when_empty(cli):
    """`checkin --all` on a fresh install surfaces all 14 trackers."""
    data = cli.json("checkin", "--all")
    names = {c["name"] for c in data["pending"] + data["logged"]}
    expected = {
        "Weight", "Sleep", "Mood", "Steps", "Workout", "Caffeine",
        "Meditate", "Stretches", "Mileage", "Journal", "Gratitude",
        "Writing", "Symptom", "Fasting",
    }
    assert expected <= names
    assert data["pending_count"] == len(expected)
    assert data["logged_count"] == 0


def test_checkin_all_marks_logged_today_correctly(cli):
    """If a tracker has today's entry, --all moves it to `logged`."""
    cli.run("weight", "log", "70")
    data = cli.json("checkin", "--all")
    logged_names = {c["name"] for c in data["logged"]}
    pending_names = {c["name"] for c in data["pending"]}
    assert "Weight" in logged_names
    assert "Weight" not in pending_names


def test_checkin_all_carries_old_last_value(cli):
    """Inactive trackers still surface their last-ever entry's value."""
    cli.run("weight", "log", "70", "-d", "2025-01-01")
    data = cli.json("checkin", "--all")
    weight_row = next(c for c in data["pending"] + data["logged"]
                      if c["name"] == "Weight")
    assert weight_row["last_value"] == "70 kg"
    assert weight_row["last_days_ago"] is not None
    assert weight_row["last_days_ago"] > 0


def test_checkin_without_all_still_filters_to_active(cli):
    """`--all` is opt-in; default behaviour unchanged."""
    cli.run("weight", "log", "70")
    data = cli.json("checkin")
    names = {c["name"] for c in data["pending"] + data["logged"]}
    # Only an actively-tracked thing makes it in; nothing else leaks.
    assert names <= {"Weight"}


def test_checkin_empty_state_hint_mentions_all_flag(cli):
    """The empty-state message should point users at `--all`."""
    result = cli.run("checkin")
    assert result.exit_code == 0
    assert "--all" in result.output


def test_checkin_all_human_view_runs(cli):
    """Rich render works in --all mode without crashing."""
    result = cli.run("checkin", "--all")
    assert result.exit_code == 0
    assert "All trackers" in result.output
