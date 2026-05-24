"""Tests for the 🃏 flashcards tool."""

from __future__ import annotations

from datetime import date, timedelta


def test_add_card(cli):
    data = cli.json("flashcards", "add", "día", "day", "-d", "spanish")
    assert data["front"] == "día"
    assert data["back"] == "day"
    assert data["deck"] == "spanish"
    assert data["box"] == 0
    assert data["next_review"] == date.today().isoformat()


def test_new_cards_are_due(cli):
    cli.run("flashcards", "add", "casa", "house", "-d", "spanish")
    due = cli.json("flashcards", "due")
    assert len(due) == 1
    assert due[0]["due"] is True


def test_grade_right_advances_box(cli):
    cli.run("flashcards", "add", "uno", "one")
    data = cli.json("flashcards", "grade", "1", "right")
    assert data["box"] == 1
    assert data["correct"] == 1
    assert data["reviews"] == 1
    # next review is interval[1] = 3 days from now
    assert data["next_review"] == (date.today() + timedelta(days=3)).isoformat()


def test_grade_wrong_resets_box(cli):
    cli.run("flashcards", "add", "dos", "two")
    cli.run("flashcards", "grade", "1", "right")
    cli.run("flashcards", "grade", "1", "right")  # now box 2
    data = cli.json("flashcards", "grade", "1", "wrong")
    assert data["box"] == 0
    assert data["correct"] == 2
    assert data["reviews"] == 3


def test_decks_summary(cli):
    cli.run("flashcards", "add", "a", "b", "-d", "spanish")
    cli.run("flashcards", "add", "c", "d", "-d", "spanish")
    cli.run("flashcards", "add", "e", "f", "-d", "french")
    decks = cli.json("flashcards", "decks")
    by = {d["deck"]: d for d in decks}
    assert by["spanish"]["cards"] == 2
    assert by["spanish"]["due"] == 2
    assert by["french"]["cards"] == 1


def test_stats_accuracy(cli):
    cli.run("flashcards", "add", "x", "y")
    cli.run("flashcards", "grade", "1", "right")
    cli.run("flashcards", "grade", "1", "right")
    cli.run("flashcards", "grade", "1", "wrong")
    stats = cli.json("flashcards", "stats")
    assert stats["total_reviews"] == 3
    assert stats["accuracy_pct"] == 66.7


def test_invalid_grade_fails(cli):
    cli.run("flashcards", "add", "x", "y")
    result = cli.run("flashcards", "grade", "1", "maybe")
    assert result.exit_code != 0



# ── bare-command default (iter 106) ──


def test_bare_flashcards_runs_due(cli):
    """`clibo flashcards` (no subcommand) runs `due`."""
    result = cli.run("flashcards")
    assert result.exit_code == 0


def test_flashcards_help_still_works(cli):
    """`clibo flashcards --help` still shows the menu after the bare change."""
    result = cli.run("flashcards", "--help")
    assert result.exit_code == 0
    assert "due" in result.stdout
