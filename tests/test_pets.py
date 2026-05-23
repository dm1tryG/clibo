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


# ── log SUMMARY optional + edit + rm by name (iter 83) ──


def test_log_summary_optional_defaults_to_kind(cli):
    """`pets log Whiskers vet` (no summary) defaults summary to the kind."""
    cli.run("pets", "add", "Whiskers", "-s", "cat")
    data = cli.json("pets", "log", "Whiskers", "vet")
    assert data["summary"] == "vet"


def test_log_summary_when_given_is_kept(cli):
    cli.run("pets", "add", "Whiskers")
    data = cli.json("pets", "log", "Whiskers", "vet", "annual checkup")
    assert data["summary"] == "annual checkup"


def test_edit_pet_by_name(cli):
    cli.run("pets", "add", "Whiskers", "-s", "cat")
    cli.run("pets", "edit", "Whiskers", "--breed", "Persian", "-n", "loud meower")
    data = cli.json("pets", "show", "Whiskers")
    assert data["breed"] == "Persian"
    assert data["notes"] == "loud meower"


def test_edit_pet_rename(cli):
    cli.run("pets", "add", "Old Name")
    cli.run("pets", "edit", "Old Name", "--name", "Whiskers")
    data = cli.json("pets", "show", "Whiskers")
    assert data["name"] == "Whiskers"


def test_edit_pet_unknown_fails(cli):
    result = cli.run("pets", "edit", "Ghost", "-s", "ghost")
    assert result.exit_code != 0


def test_rm_pet_by_name(cli):
    cli.run("pets", "add", "Whiskers")
    cli.run("pets", "rm", "Whiskers")
    result = cli.run("pets", "show", "Whiskers")
    assert result.exit_code != 0


def test_pet_name_fuzzy_match(cli):
    """`Whisk` finds `Whiskers`."""
    cli.run("pets", "add", "Whiskers")
    data = cli.json("pets", "show", "Whisk")
    assert data["name"] == "Whiskers"
