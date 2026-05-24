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


# ── direct IOU verbs: owe / lent (iter 86) ──


def test_owe_records_iou(cli):
    """`split owe Anna 50` — I owe Anna $50."""
    data = cli.json("split", "owe", "Anna", "50")
    assert data["amount"] == 50.0
    assert data["paid_by"] == "Anna"
    assert data["participants"] == ["me"]
    assert data["per_person"] == 50.0


def test_owe_flows_into_balances(cli):
    cli.run("split", "owe", "Anna", "50")
    balances = {r["person"]: r["balance"] for r in cli.json("split", "balances")}
    assert balances["Anna"] == 50.0
    assert balances["me"] == -50.0


def test_lent_records_reverse_iou(cli):
    """`split lent Bob 20` — Bob owes me $20."""
    data = cli.json("split", "lent", "Bob", "20")
    assert data["amount"] == 20.0
    assert data["paid_by"] == "me"
    assert data["participants"] == ["Bob"]


def test_lent_flows_into_balances(cli):
    cli.run("split", "lent", "Bob", "20")
    balances = {r["person"]: r["balance"] for r in cli.json("split", "balances")}
    assert balances["Bob"] == -20.0
    assert balances["me"] == 20.0


def test_owe_and_lent_combine_correctly(cli):
    """A combination should produce the right net balance."""
    cli.run("split", "owe", "Anna", "50")
    cli.run("split", "lent", "Bob", "20")
    balances = {r["person"]: r["balance"] for r in cli.json("split", "balances")}
    assert balances["Anna"] == 50.0
    assert balances["Bob"] == -20.0
    assert balances["me"] == -30.0  # net: owe Anna 50, lent Bob 20 → -30


def test_owe_custom_me_name(cli):
    """`--me` switches the ledger identity."""
    data = cli.json("split", "owe", "Anna", "50", "--me", "Dmitrii")
    assert data["participants"] == ["Dmitrii"]
    balances = {r["person"]: r["balance"] for r in cli.json("split", "balances")}
    assert balances["Dmitrii"] == -50.0


def test_owe_settles_through_settle(cli):
    """An IOU recorded via `owe` can be cleared via `settle`."""
    cli.run("split", "owe", "Anna", "50")
    cli.run("split", "settle", "me", "Anna", "50")
    balances = {r["person"]: r["balance"] for r in cli.json("split", "balances")}
    assert balances["Anna"] == 0.0
    assert balances["me"] == 0.0


def test_owe_negative_amount_fails(cli):
    result = cli.run("split", "owe", "Anna", "-5")
    assert result.exit_code != 0


def test_lent_negative_amount_fails(cli):
    result = cli.run("split", "lent", "Bob", "-5")
    assert result.exit_code != 0


def test_owe_default_description(cli):
    """Description defaults to a descriptive 'IOU: …' string."""
    data = cli.json("split", "owe", "Anna", "50")
    assert "owes" in data["description"]
    assert "Anna" in data["description"]



# ── bare-command default (iter 107) ──


def test_bare_split_runs_balances(cli):
    """`clibo split` (no subcommand) runs `balances`."""
    result = cli.run("split")
    assert result.exit_code == 0


def test_split_help_still_works(cli):
    """`clibo split --help` still shows the menu after the bare change."""
    result = cli.run("split", "--help")
    assert result.exit_code == 0
    assert "balances" in result.stdout
