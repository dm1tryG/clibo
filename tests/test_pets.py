"""Tests for the 🐾 pets tool."""

from __future__ import annotations


def test_add_pet(cli):
    data = cli.json("pets", "add", "Whiskers", "-s", "cat", "-b", "British Shorthair",
                    "--birth", "2022-04-15")
    assert data["name"] == "Whiskers"
    assert data["species"] == "cat"
    assert data["age_years"] is not None


def test_log_event(cli):
    cli.run("pets", "add", "Rex", "-s", "dog")
    data = cli.json("pets", "log", "Rex", "vet", "Annual checkup", "-c", "120")
    assert data["kind"] == "vet"
    assert data["cost"] == 120.0


def test_show_includes_events(cli):
    cli.run("pets", "add", "Cat")
    cli.run("pets", "log", "Cat", "feeding", "morning meal")
    cli.run("pets", "log", "Cat", "vet", "vaccination")
    detail = cli.json("pets", "show", "Cat")
    assert detail["events_logged"] == 2
    assert len(detail["events"]) == 2
    assert detail["last_vet"] is not None


def test_events_lists_across_pets(cli):
    cli.run("pets", "add", "A")
    cli.run("pets", "add", "B")
    cli.run("pets", "log", "A", "walk", "morning walk")
    cli.run("pets", "log", "B", "feeding", "dinner")
    events = cli.json("pets", "events")
    assert len(events) == 2


def test_stats(cli):
    cli.run("pets", "add", "Pet")
    cli.run("pets", "log", "Pet", "vet", "checkup", "-c", "100")
    cli.run("pets", "log", "Pet", "vet", "shots", "-c", "50")
    stats = cli.json("pets", "stats")
    assert stats["pets"] == 1
    assert stats["events"] == 2
    assert stats["spent"] == 150.0
    assert stats["by_kind"]["vet"] == 2


def test_invalid_kind_fails(cli):
    cli.run("pets", "add", "X")
    result = cli.run("pets", "log", "X", "training", "session")
    assert result.exit_code != 0
