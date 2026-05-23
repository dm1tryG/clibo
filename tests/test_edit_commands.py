"""Tests for the new `edit ID|last` pattern across daily trackers.

The user pain point this addresses:
> "Edit my last weight entry — typo, was 71.5 not 75"

`edit` now exists on weight, mood, sleep, caffeine, steps, gratitude.
Each accepts either a numeric entry ID or the keyword ``last`` (the
most recently inserted row), with field-level optional flags.
"""

from __future__ import annotations


# ──────────────────────────────────────────────────────────────────────
# ⚖️ weight
# ──────────────────────────────────────────────────────────────────────


def test_weight_edit_last_fixes_typo(cli):
    """The headline use case: typo'd weight, fix it with `edit last`."""
    cli.run("weight", "log", "75")     # typo
    cli.run("weight", "edit", "last", "-w", "71.5")
    rows = cli.json("weight", "list")
    assert rows[0]["weight_kg"] == 71.5


def test_weight_edit_by_id(cli):
    entry = cli.json("weight", "log", "75")
    cli.run("weight", "edit", str(entry["id"]), "-w", "71.5")
    rows = cli.json("weight", "list")
    assert rows[0]["weight_kg"] == 71.5


def test_weight_edit_rejects_non_positive(cli):
    cli.run("weight", "log", "70")
    result = cli.run("weight", "edit", "last", "-w", "0")
    assert result.exit_code != 0


def test_weight_edit_unknown_id_fails(cli):
    result = cli.run("weight", "edit", "999", "-w", "70")
    assert result.exit_code != 0


def test_weight_edit_last_with_no_entries_fails(cli):
    result = cli.run("weight", "edit", "last", "-w", "70")
    assert result.exit_code != 0


def test_weight_edit_bad_target_fails(cli):
    cli.run("weight", "log", "70")
    result = cli.run("weight", "edit", "garbage", "-w", "71")
    assert result.exit_code != 0


# ──────────────────────────────────────────────────────────────────────
# 🙂 mood
# ──────────────────────────────────────────────────────────────────────


def test_mood_edit_last(cli):
    cli.run("mood", "log", "3", "-e", "tired")
    cli.run("mood", "edit", "last", "-s", "4", "-e", "calm")
    today = cli.json("mood", "today")
    assert today["checkins"][0]["score"] == 4
    assert today["checkins"][0]["emotion"] == "calm"


def test_mood_edit_rejects_bad_score(cli):
    cli.run("mood", "log", "3")
    result = cli.run("mood", "edit", "last", "-s", "9")
    assert result.exit_code != 0


# ──────────────────────────────────────────────────────────────────────
# 😴 sleep
# ──────────────────────────────────────────────────────────────────────


def test_sleep_edit_last(cli):
    cli.run("sleep", "log", "7")
    cli.run("sleep", "edit", "last", "-H", "7.5", "-q", "5")
    rows = cli.json("sleep", "list")
    assert rows[0]["hours"] == 7.5
    assert rows[0]["quality"] == 5


def test_sleep_edit_rejects_zero_hours(cli):
    cli.run("sleep", "log", "7")
    result = cli.run("sleep", "edit", "last", "-H", "0")
    assert result.exit_code != 0


# ──────────────────────────────────────────────────────────────────────
# ☕ caffeine
# ──────────────────────────────────────────────────────────────────────


def test_caffeine_edit_mg(cli):
    cli.run("caffeine", "log", "coffee")
    cli.run("caffeine", "edit", "last", "-m", "150")
    today = cli.json("caffeine", "today")
    assert today["entries"][0]["mg"] == 150


def test_caffeine_edit_drink_normalizes(cli):
    cli.run("caffeine", "log", "coffee")
    cli.run("caffeine", "edit", "last", "--drink", "Cold Brew")
    today = cli.json("caffeine", "today")
    assert today["entries"][0]["drink"] == "cold-brew"


# ──────────────────────────────────────────────────────────────────────
# 👟 steps
# ──────────────────────────────────────────────────────────────────────


def test_steps_edit_count(cli):
    cli.run("steps", "log", "8500")
    cli.run("steps", "edit", "last", "-c", "9000")
    today = cli.json("steps", "today")
    assert today["total"] == 9000


def test_steps_edit_rejects_non_positive_count(cli):
    cli.run("steps", "log", "8500")
    result = cli.run("steps", "edit", "last", "-c", "0")
    assert result.exit_code != 0


# ──────────────────────────────────────────────────────────────────────
# 🙏 gratitude
# ──────────────────────────────────────────────────────────────────────


def test_gratitude_edit_text(cli):
    cli.run("gratitude", "add", "coffe")  # typo
    cli.run("gratitude", "edit", "last", "-t", "coffee, dog, sunshine")
    today = cli.json("gratitude", "today")
    assert today["entries"][0]["text"] == "coffee, dog, sunshine"


def test_gratitude_edit_rejects_empty_text(cli):
    cli.run("gratitude", "add", "x")
    result = cli.run("gratitude", "edit", "last", "-t", "   ")
    assert result.exit_code != 0
