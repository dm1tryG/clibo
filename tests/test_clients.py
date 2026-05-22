"""Tests for the 🧑‍💼 clients tool."""

from __future__ import annotations


def test_add_client(cli):
    data = cli.json("clients", "add", "Acme Inc", "-r", "80", "-e", "hi@acme.com")
    assert data["name"] == "Acme Inc"
    assert data["hourly_rate"] == 80.0
    assert data["status"] == "active"


def test_log_hours_and_earnings(cli):
    cli.run("clients", "add", "Globex", "-r", "100")
    cli.run("clients", "log", "Globex", "3")
    data = cli.json("clients", "log", "Globex", "2")
    assert data["hours_logged"] == 5.0
    assert data["earnings"] == 500.0


def test_show_lists_hours(cli):
    cli.run("clients", "add", "Initech", "-r", "50")
    cli.run("clients", "log", "Initech", "4", "-D", "Built the report")
    detail = cli.json("clients", "show", "Initech")
    assert len(detail["hours_log"]) == 1
    assert detail["hours_log"][0]["hours"] == 4.0


def test_edit_rate(cli):
    client = cli.json("clients", "add", "Client", "-r", "60")
    edited = cli.json("clients", "edit", str(client["id"]), "-r", "90")
    assert edited["hourly_rate"] == 90.0


def test_stats_total_earnings(cli):
    cli.run("clients", "add", "A", "-r", "100")
    cli.run("clients", "log", "A", "10")
    stats = cli.json("clients", "stats")
    assert stats["total_hours"] == 10.0
    assert stats["total_earnings"] == 1000.0


def test_log_unknown_client_fails(cli):
    result = cli.run("clients", "log", "Ghost", "5")
    assert result.exit_code != 0
