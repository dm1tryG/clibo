"""Tests for the 🥫 pantry tool."""

from __future__ import annotations

from datetime import date, timedelta


def test_add_item(cli):
    data = cli.json("pantry", "add", "olive oil", "-l", "pantry", "-q", "1 bottle")
    assert data["name"] == "olive oil"
    assert data["location"] == "pantry"
    assert data["status"] == "none"


def test_expired_status(cli):
    past = (date.today() - timedelta(days=5)).isoformat()
    data = cli.json("pantry", "add", "old yogurt", "-e", past)
    assert data["status"] == "expired"


def test_fresh_status(cli):
    future = (date.today() + timedelta(days=30)).isoformat()
    data = cli.json("pantry", "add", "canned beans", "-e", future)
    assert data["status"] == "fresh"


def test_expiring_lists_soon_and_expired(cli):
    soon = (date.today() + timedelta(days=2)).isoformat()
    far = (date.today() + timedelta(days=60)).isoformat()
    cli.run("pantry", "add", "milk", "-e", soon)
    cli.run("pantry", "add", "rice", "-e", far)
    expiring = cli.json("pantry", "expiring", "--days", "7")
    assert len(expiring) == 1
    assert expiring[0]["name"] == "milk"


def test_list_filters_by_location(cli):
    cli.run("pantry", "add", "ice cream", "-l", "freezer")
    cli.run("pantry", "add", "flour", "-l", "pantry")
    freezer = cli.json("pantry", "list", "-l", "freezer")
    assert len(freezer) == 1


def test_stats(cli):
    past = (date.today() - timedelta(days=1)).isoformat()
    cli.run("pantry", "add", "expired thing", "-e", past)
    stats = cli.json("pantry", "stats")
    assert stats["total"] == 1
    assert stats["expired"] == 1
