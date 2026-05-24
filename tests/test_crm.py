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


# ── crm dormant — surface contacts overdue for a check-in (iter 124) ──


def test_dormant_lists_stale_contacts(cli):
    """`crm dormant` finds contacts not touched in >90d (default)."""
    cli.run("crm", "add", "Recent Pal")
    cli.run("crm", "add", "Old Friend")
    cli.run("crm", "touch", "Recent Pal", "-d", "today")
    cli.run("crm", "touch", "Old Friend", "-d", "2025-01-01")
    rows = cli.json("crm", "dormant")
    names = [r["name"] for r in rows]
    assert "Old Friend" in names
    assert "Recent Pal" not in names


def test_dormant_includes_never_contacted_by_default(cli):
    """Never-touched contacts are dormant too — they need outreach."""
    cli.run("crm", "add", "Never Met")
    rows = cli.json("crm", "dormant")
    assert any(r["name"] == "Never Met" for r in rows)


def test_dormant_skip_never_flag(cli):
    """--skip-never excludes never-touched contacts."""
    cli.run("crm", "add", "Never Met")
    cli.run("crm", "add", "Old Friend")
    cli.run("crm", "touch", "Old Friend", "-d", "2025-01-01")
    rows = cli.json("crm", "dormant", "--skip-never")
    names = {r["name"] for r in rows}
    assert "Old Friend" in names
    assert "Never Met" not in names


def test_dormant_custom_days(cli):
    """--days 7 surfaces shorter-staleness contacts."""
    cli.run("crm", "add", "Two Weeks Ago")
    cli.run("crm", "touch", "Two Weeks Ago", "-d", "14 days ago")
    rows = cli.json("crm", "dormant", "--days", "7")
    assert any(r["name"] == "Two Weeks Ago" for r in rows)
    rows_30 = cli.json("crm", "dormant", "--days", "30")
    assert not any(r["name"] == "Two Weeks Ago" for r in rows_30)


def test_dormant_skips_non_active_contacts(cli):
    """Cold/inactive contacts shouldn't show up — they're already paused."""
    cli.run("crm", "add", "Cold Person")
    cli.run("crm", "edit", "Cold Person", "--status", "cold")
    rows = cli.json("crm", "dormant")
    assert not any(r["name"] == "Cold Person" for r in rows)


def test_dormant_sorts_never_first(cli):
    """Never-touched listed first, then oldest-touched."""
    cli.run("crm", "add", "Stale One")
    cli.run("crm", "touch", "Stale One", "-d", "2025-01-01")
    cli.run("crm", "add", "Never Met")
    rows = cli.json("crm", "dormant")
    assert rows[0]["name"] == "Never Met"
    assert rows[0]["last_contact_ago"] == "never"


def test_dormant_negative_days_fails(cli):
    result = cli.run("crm", "dormant", "--days", "-1")
    assert result.exit_code != 0
