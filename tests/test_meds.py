"""Tests for the 💊 meds tool."""

from __future__ import annotations


def test_add_medication(cli):
    data = cli.json("meds", "add", "Vitamin D", "-d", "1000IU", "-t", "1")
    assert data["name"] == "Vitamin D"
    assert data["dosage"] == "1000IU"
    assert data["times_per_day"] == 1


def test_take_by_name_and_id(cli):
    med = cli.json("meds", "add", "Aspirin", "-t", "2")
    by_name = cli.json("meds", "take", "Aspirin")
    assert by_name["taken_today"] == 1
    by_id = cli.json("meds", "take", str(med["id"]))
    assert by_id["taken_today"] == 2


def test_today_tracks_progress(cli):
    cli.run("meds", "add", "Iron", "-t", "2")
    cli.run("meds", "take", "Iron")
    today = cli.json("meds", "today")
    med = today["medications"][0]
    assert med["taken"] == 1
    assert med["remaining"] == 1
    assert med["done"] is False


def test_stop_hides_from_list(cli):
    med = cli.json("meds", "add", "Temp")
    cli.run("meds", "stop", str(med["id"]))
    assert cli.json("meds", "list") == []
    assert len(cli.json("meds", "list", "--all")) == 1


def test_adherence_stats(cli):
    cli.run("meds", "add", "Daily", "-t", "1")
    cli.run("meds", "take", "Daily")
    stats = cli.json("meds", "stats", "--days", "1")
    assert stats["doses_taken"] == 1
    assert stats["doses_expected"] == 1
    assert stats["adherence_pct"] == 100


def test_take_unknown_with_strict_fails(cli):
    """`--strict` keeps the old fail-on-unknown behaviour."""
    result = cli.run("meds", "take", "Nonexistent", "--strict")
    assert result.exit_code != 0


# ── auto-create + name-resolve on edit/stop/rm (iter 101) ──


def test_take_auto_creates_unknown_med(cli):
    """`meds take Vitamin D` works even when Vitamin D isn't registered yet."""
    data = cli.json("meds", "take", "Vitamin D")
    assert data["medication"] == "Vitamin D"
    assert data["auto_created"] is True
    assert data["taken_today"] == 1


def test_take_second_dose_uses_existing_med(cli):
    """A second `take` of the same med doesn't create a duplicate."""
    cli.run("meds", "take", "Vitamin D")
    data = cli.json("meds", "take", "Vitamin D")
    assert data["auto_created"] is False
    assert data["taken_today"] == 2
    # Only one Medication row should exist
    listing = cli.json("meds", "list", "--all")
    assert sum(1 for m in listing if m["name"] == "Vitamin D") == 1


def test_take_auto_create_default_one_per_day(cli):
    data = cli.json("meds", "take", "Aspirin")
    assert data["times_per_day"] == 1


def test_take_strict_still_fails_for_unknown(cli):
    result = cli.run("meds", "take", "Ghost", "--strict")
    assert result.exit_code != 0


def test_take_strict_unknown_id_fails(cli):
    """Numeric IDs that don't exist always fail, even without --strict.

    We don't want a fat-fingered `meds take 99` to create medication
    named '99' silently.
    """
    result = cli.run("meds", "take", "99999")
    assert result.exit_code != 0


def test_edit_by_name(cli):
    cli.run("meds", "add", "Vitamin D")
    edited = cli.json("meds", "edit", "Vitamin D",
                      "-d", "1000 IU", "-t", "2")
    assert edited["dosage"] == "1000 IU"
    assert edited["times_per_day"] == 2


def test_edit_can_rename(cli):
    cli.run("meds", "add", "Old Name")
    edited = cli.json("meds", "edit", "Old Name", "--name", "New Name")
    assert edited["name"] == "New Name"


def test_edit_rejects_invalid_times_per_day(cli):
    cli.run("meds", "add", "X")
    result = cli.run("meds", "edit", "X", "-t", "0")
    assert result.exit_code != 0


def test_edit_unknown_fails(cli):
    result = cli.run("meds", "edit", "Ghost")
    assert result.exit_code != 0


def test_stop_by_name(cli):
    cli.run("meds", "add", "Vitamin D")
    data = cli.json("meds", "stop", "Vitamin D")
    assert data["active"] is False


def test_rm_by_name(cli):
    cli.run("meds", "add", "Doomed")
    cli.json("meds", "rm", "Doomed")
    listing = cli.json("meds", "list", "--all")
    assert not any(m["name"] == "Doomed" for m in listing)


def test_rm_cascades_doses(cli):
    """Deleting a med also deletes its dose history."""
    cli.run("meds", "add", "Cascading", "-t", "1")
    cli.run("meds", "take", "Cascading")
    cli.json("meds", "rm", "Cascading")
    # If we re-add and check stats, no historical doses should bleed through.
    cli.run("meds", "add", "Cascading", "-t", "1")
    stats = cli.json("meds", "stats", "--days", "1")
    assert stats["doses_taken"] == 0
