"""Tests for the 📄 invoice tool."""

from __future__ import annotations


def test_add_assigns_number(cli):
    first = cli.json("invoice", "add", "Acme Inc", "-a", "1200")
    assert first["number"] == "INV-0001"
    second = cli.json("invoice", "add", "Globex", "-a", "800")
    assert second["number"] == "INV-0002"


def test_tax_included_in_total(cli):
    data = cli.json("invoice", "add", "Client", "-a", "1000", "--tax", "20")
    assert data["amount"] == 1000.0
    assert data["total"] == 1200.0


def test_send_and_pay_flow(cli):
    inv = cli.json("invoice", "add", "Client", "-a", "500")
    assert inv["status"] == "draft"
    sent = cli.json("invoice", "send", str(inv["id"]))
    assert sent["status"] == "sent"
    paid = cli.json("invoice", "pay", str(inv["id"]))
    assert paid["status"] == "paid"
    assert paid["paid_date"] is not None


def test_stats_split_paid_outstanding(cli):
    a = cli.json("invoice", "add", "A", "-a", "1000")
    cli.json("invoice", "add", "B", "-a", "500")
    cli.run("invoice", "pay", str(a["id"]))
    stats = cli.json("invoice", "stats")
    assert stats["total_billed"] == 1500.0
    assert stats["total_paid"] == 1000.0
    assert stats["total_outstanding"] == 500.0


def test_render_returns_invoice(cli):
    inv = cli.json("invoice", "add", "Render Co", "-a", "300")
    rendered = cli.json("invoice", "render", str(inv["id"]))
    assert rendered["client"] == "Render Co"


def test_negative_amount_fails(cli):
    result = cli.run("invoice", "add", "Bad", "-a", "-100")
    assert result.exit_code != 0
