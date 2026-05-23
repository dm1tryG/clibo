"""Tests for the 👥 crm tool."""

from __future__ import annotations


def test_add_contact(cli):
    data = cli.json("crm", "add", "Anna Petrova", "-c", "Acme", "-e", "anna@acme.com")
    assert data["name"] == "Anna Petrova"
    assert data["company"] == "Acme"
    assert data["status"] == "active"


def test_list_filters_by_status(cli):
    cli.run("crm", "add", "Lead Person", "-s", "lead")
    cli.run("crm", "add", "Customer Person", "-s", "customer")
    leads = cli.json("crm", "list", "-s", "lead")
    assert len(leads) == 1
    assert leads[0]["name"] == "Lead Person"


def test_touch_sets_last_contact(cli):
    contact = cli.json("crm", "add", "Bob")
    assert contact["last_contact"] is None
    touched = cli.json("crm", "touch", str(contact["id"]))
    assert touched["last_contact"] is not None


def test_search_matches_company(cli):
    cli.run("crm", "add", "Person One", "-c", "Globex")
    cli.run("crm", "add", "Person Two", "-c", "Initech")
    results = cli.json("crm", "search", "globex")
    assert len(results) == 1


def test_edit_status(cli):
    contact = cli.json("crm", "add", "Carol", "-s", "lead")
    edited = cli.json("crm", "edit", str(contact["id"]), "-s", "customer")
    assert edited["status"] == "customer"


def test_stats(cli):
    cli.run("crm", "add", "A", "-s", "lead")
    cli.run("crm", "add", "B", "-s", "active")
    stats = cli.json("crm", "stats")
    assert stats["total"] == 2
    assert stats["by_status"]["lead"] == 1


def test_invalid_status_fails(cli):
    result = cli.run("crm", "add", "Bad", "-s", "prospect")
    assert result.exit_code != 0


# ──────────────────────────────────────────────────────────────────────
# Name-based resolution on show/edit/rm/touch (iter 81).
# ──────────────────────────────────────────────────────────────────────


def test_crm_show_by_name(cli):
    cli.run("crm", "add", "Bob", "-c", "Acme")
    data = cli.json("crm", "show", "Bob")
    assert data["name"] == "Bob"


def test_crm_show_by_id_still_works(cli):
    entry = cli.json("crm", "add", "Bob")
    data = cli.json("crm", "show", str(entry["id"]))
    assert data["name"] == "Bob"


def test_crm_edit_by_name(cli):
    """The headline use case: 'Bob got promoted' — edit by name."""
    cli.run("crm", "add", "Bob", "-c", "Acme")
    cli.run("crm", "edit", "Bob", "-c", "Acme Corp")
    data = cli.json("crm", "show", "Bob")
    assert data["company"] == "Acme Corp"


def test_crm_edit_unknown_name_fails(cli):
    cli.run("crm", "add", "Bob")
    result = cli.run("crm", "edit", "Ghost", "-c", "X")
    assert result.exit_code != 0


def test_crm_rm_by_name(cli):
    cli.run("crm", "add", "Bob")
    cli.run("crm", "rm", "Bob")
    listing = cli.json("crm", "list")
    assert not any(c["name"] == "Bob" for c in listing)


def test_crm_touch_by_name(cli):
    cli.run("crm", "add", "Bob")
    cli.run("crm", "touch", "Bob", "-d", "yesterday")
    data = cli.json("crm", "show", "Bob")
    assert data["last_contact"] is not None


def test_crm_name_match_is_substring(cli):
    """Fuzzy: 'Smith' matches 'Bob Smith' too."""
    cli.run("crm", "add", "Bob Smith")
    data = cli.json("crm", "show", "Smith")
    assert data["name"] == "Bob Smith"
