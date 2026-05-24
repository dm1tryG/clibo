"""Tests for the 🪴 plants tool."""

from __future__ import annotations


def test_add_plant(cli):
    data = cli.json("plants", "add", "Monstera", "-w", "7", "-l", "living room")
    assert data["name"] == "Monstera"
    assert data["water_every_days"] == 7
    assert data["location"] == "living room"


def test_new_plant_needs_water(cli):
    data = cli.json("plants", "add", "Cactus", "-w", "14")
    assert data["status"] == "water today"


def test_water_pushes_next(cli):
    cli.run("plants", "add", "Fern", "-w", "3")
    watered = cli.json("plants", "water", "Fern")
    assert watered["status"] == "ok"
    assert watered["last_watered"] is not None


def test_thirsty_lists_unwatered(cli):
    cli.run("plants", "add", "Thirsty one", "-w", "5")
    happy = cli.json("plants", "add", "Happy one", "-w", "5")
    cli.run("plants", "water", str(happy["id"]))
    thirsty = cli.json("plants", "thirsty")
    assert len(thirsty) == 1
    assert thirsty[0]["name"] == "Thirsty one"


def test_stats(cli):
    cli.run("plants", "add", "P", "-w", "7")
    stats = cli.json("plants", "stats")
    assert stats["total"] == 1
    assert stats["water_today"] == 1


def test_invalid_frequency_fails(cli):
    result = cli.run("plants", "add", "Bad", "-w", "0")
    assert result.exit_code != 0


# ── edit by name + plant edit command (iter 82) ──


def test_plants_edit_by_name(cli):
    cli.run("plants", "add", "Basil", "-w", "2", "-l", "living room")
    cli.run("plants", "edit", "Basil", "-l", "kitchen")
    data = cli.json("plants", "list")
    basil = next(p for p in data if p["name"] == "Basil")
    assert basil["location"] == "kitchen"


def test_plants_rm_by_name(cli):
    cli.run("plants", "add", "Basil", "-w", "2")
    cli.run("plants", "rm", "Basil")
    data = cli.json("plants", "list")
    assert not any(p["name"] == "Basil" for p in data)


def test_plants_edit_rejects_zero_frequency(cli):
    cli.run("plants", "add", "Basil", "-w", "2")
    result = cli.run("plants", "edit", "Basil", "-w", "0")
    assert result.exit_code != 0



# ── bare-command default (iter 107) ──


def test_bare_plants_runs_thirsty(cli):
    """`clibo plants` (no subcommand) runs `thirsty`."""
    result = cli.run("plants")
    assert result.exit_code == 0


def test_plants_help_still_works(cli):
    """`clibo plants --help` still shows the menu after the bare change."""
    result = cli.run("plants", "--help")
    assert result.exit_code == 0
    assert "thirsty" in result.stdout
