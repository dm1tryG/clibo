"""Tests for the ❤️ donations tool."""

from __future__ import annotations

from datetime import date


def test_log_basic(cli):
    data = cli.json("donations", "log", "Red Cross", "-a", "50")
    assert data["recipient"] == "Red Cross"
    assert data["amount"] == 50.0
    assert data["tax_deductible"] is True   # default


def test_log_non_deductible(cli):
    data = cli.json(
        "donations", "log", "GoFundMe Alice",
        "-a", "200", "--no-deductible",
    )
    assert data["tax_deductible"] is False


def test_log_with_receipt(cli):
    data = cli.json(
        "donations", "log", "MSF",
        "-a", "100", "-r", "RC-2026-0042",
    )
    assert data["receipt"] == "RC-2026-0042"


def test_log_rejects_zero_and_negative(cli):
    assert cli.run("donations", "log", "Org", "-a", "0").exit_code != 0
    assert cli.run("donations", "log", "Org", "-a", "-5").exit_code != 0


def test_add_alias_works(cli):
    log_help = cli.run("donations", "log", "--help")
    add_help = cli.run("donations", "add", "--help")
    assert log_help.exit_code == 0 and "Usage:" in log_help.output
    assert add_help.exit_code == 0 and "Usage:" in add_help.output
    cli.run("donations", "add", "Red Cross", "-a", "10")
    rows = cli.json("donations", "list")
    assert len(rows) == 1


def test_year_summary(cli):
    yr = date.today().year
    cli.run("donations", "log", "Red Cross", "-a", "50",
            "-d", f"{yr}-03-15")
    cli.run("donations", "log", "Red Cross", "-a", "100",
            "-d", f"{yr}-06-20")
    cli.run("donations", "log", "MSF", "-a", "75",
            "-d", f"{yr}-09-10")
    cli.run("donations", "log", "Political PAC", "-a", "25",
            "-d", f"{yr}-11-01", "--no-deductible")
    data = cli.json("donations", "year")
    assert data["year"] == yr
    assert data["count"] == 4
    assert data["total"] == 250.0
    assert data["deductible_total"] == 225.0
    assert data["non_deductible_total"] == 25.0
    assert data["recipients"] == 3
    # Recipients sorted by amount descending: Red Cross (150), MSF (75), PAC (25)
    by_r = [r["recipient"] for r in data["by_recipient"]]
    assert by_r[0] == "Red Cross"


def test_year_for_specific_year_excludes_others(cli):
    cli.run("donations", "log", "X", "-a", "100", "-d", "2024-06-01")
    cli.run("donations", "log", "Y", "-a", "200", "-d", "2025-06-01")
    data_2024 = cli.json("donations", "year", "-y", "2024")
    assert data_2024["total"] == 100.0
    data_2025 = cli.json("donations", "year", "-y", "2025")
    assert data_2025["total"] == 200.0


def test_list_filters_by_recipient(cli):
    cli.run("donations", "log", "Red Cross", "-a", "50")
    cli.run("donations", "log", "MSF", "-a", "75")
    only_rc = cli.json("donations", "list", "-R", "Red Cross")
    assert {r["recipient"] for r in only_rc} == {"Red Cross"}


def test_list_filters_by_year(cli):
    cli.run("donations", "log", "X", "-a", "100", "-d", "2024-06-01")
    cli.run("donations", "log", "Y", "-a", "200", "-d", "2025-06-01")
    only_2024 = cli.json("donations", "list", "-y", "2024")
    assert {r["recipient"] for r in only_2024} == {"X"}


def test_top_aggregates_by_recipient(cli):
    cli.run("donations", "log", "Red Cross", "-a", "50")
    cli.run("donations", "log", "Red Cross", "-a", "100")
    cli.run("donations", "log", "Red Cross", "-a", "25")
    cli.run("donations", "log", "MSF", "-a", "200")
    top = cli.json("donations", "top")
    by = {r["recipient"]: r for r in top}
    assert by["MSF"]["total"] == 200.0
    assert by["MSF"]["gifts"] == 1
    assert by["Red Cross"]["total"] == 175.0
    assert by["Red Cross"]["gifts"] == 3


def test_show(cli):
    entry = cli.json("donations", "log", "Red Cross", "-a", "50",
                      "-r", "RC-001")
    fetched = cli.json("donations", "show", str(entry["id"]))
    assert fetched["receipt"] == "RC-001"


def test_rm(cli):
    entry = cli.json("donations", "log", "X", "-a", "10")
    cli.run("donations", "rm", str(entry["id"]))
    assert cli.json("donations", "list") == []


def test_stats(cli):
    cli.run("donations", "log", "Red Cross", "-a", "50",
            "-d", "2024-06-01")
    cli.run("donations", "log", "Red Cross", "-a", "100",
            "-d", "2025-06-01")
    cli.run("donations", "log", "MSF", "-a", "25",
            "-d", "2025-09-01", "--no-deductible")
    data = cli.json("donations", "stats")
    assert data["lifetime_count"] == 3
    assert data["lifetime_total"] == 175.0
    assert data["lifetime_deductible_total"] == 150.0
    assert data["recipients"] == 2
    assert data["top_recipient"]["recipient"] == "Red Cross"
    assert data["top_recipient"]["total"] == 150.0
    assert data["by_year"] == {"2024": 50.0, "2025": 125.0}


def test_searchable_and_in_recent(cli):
    cli.run("donations", "log", "Médecins Sans Frontières",
            "-a", "100", "-r", "MSF-2026-77",
            "-n", "annual giving campaign")
    by_recipient = cli.json("search", "Médecins")
    assert any(h["source"] == "donations" for h in by_recipient["results"])
    by_receipt = cli.json("search", "MSF-2026")
    assert any(h["source"] == "donations" for h in by_receipt["results"])
    by_note = cli.json("search", "campaign")
    assert any(h["source"] == "donations" for h in by_note["results"])
    recent = cli.json("recent")
    assert any(e["source"] == "donations" for e in recent["events"])


# ── name-resolution on show/edit/rm (iter 85) ──


def test_donations_show_by_recipient_name(cli):
    cli.run("donations", "log", "Red Cross", "-a", "50")
    data = cli.json("donations", "show", "Red Cross")
    assert data["recipient"] == "Red Cross"


def test_donations_rm_by_recipient_name(cli):
    cli.run("donations", "log", "Red Cross", "-a", "50")
    cli.json("donations", "rm", "Red Cross")
    listing = cli.json("donations", "list")
    assert not any(e["recipient"] == "Red Cross" for e in listing)


def test_donations_edit_amount_by_name(cli):
    cli.run("donations", "log", "MSF", "-a", "100")
    edited = cli.json("donations", "edit", "MSF", "-a", "150")
    assert edited["amount"] == 150.0


def test_donations_edit_flips_deductible(cli):
    cli.run("donations", "log", "GoFundMe Friend", "-a", "50")
    edited = cli.json("donations", "edit", "GoFundMe", "--no-deductible")
    assert edited["tax_deductible"] is False


def test_donations_resolves_most_recent_when_multiple(cli):
    """Repeat giving — name lookup prefers the latest gift."""
    cli.run("donations", "log", "Red Cross", "-a", "25")
    latest = cli.json("donations", "log", "Red Cross", "-a", "75")
    data = cli.json("donations", "show", "Red Cross")
    assert data["id"] == latest["id"]
    assert data["amount"] == 75.0


def test_donations_unknown_recipient_fails(cli):
    result = cli.run("donations", "show", "ghost")
    assert result.exit_code != 0
