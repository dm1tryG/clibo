"""Tests for the 🤝 split tool."""

from __future__ import annotations


def test_add_splits_equally(cli):
    data = cli.json("split", "add", "Dinner", "-a", "60", "-b", "Alice", "-w", "Alice,Bob,Carol")
    assert data["amount"] == 60.0
    assert data["per_person"] == 20.0
    assert set(data["participants"]) == {"Alice", "Bob", "Carol"}


def test_balances_after_one_expense(cli):
    cli.run("split", "add", "Taxi", "-a", "30", "-b", "Alice", "-w", "Alice,Bob,Carol")
    balances = {r["person"]: r["balance"] for r in cli.json("split", "balances")}
    assert balances["Alice"] == 20.0
    assert balances["Bob"] == -10.0
    assert balances["Carol"] == -10.0


def test_settle_clears_balance(cli):
    cli.run("split", "add", "Lunch", "-a", "20", "-b", "Alice", "-w", "Alice,Bob")
    cli.run("split", "settle", "Bob", "Alice", "10")
    balances = {r["person"]: r["balance"] for r in cli.json("split", "balances")}
    assert balances["Alice"] == 0.0
    assert balances["Bob"] == 0.0


def test_who_suggests_payments(cli):
    cli.run("split", "add", "Trip", "-a", "90", "-b", "Alice", "-w", "Alice,Bob,Carol")
    txns = cli.json("split", "who")["transactions"]
    assert len(txns) == 2
    assert all(t["to"] == "Alice" for t in txns)
    assert sum(t["amount"] for t in txns) == 60.0


def test_negative_amount_fails(cli):
    result = cli.run("split", "add", "Bad", "-a", "-5", "-b", "Alice", "-w", "Alice,Bob")
    assert result.exit_code != 0
