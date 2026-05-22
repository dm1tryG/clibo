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
