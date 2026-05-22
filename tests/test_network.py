"""Tests for the 🌐 network tool."""

from __future__ import annotations


def test_add_connection(cli):
    data = cli.json("network", "add", "Sam Lee", "-w", "PyCon", "-c", "talked about CLIs")
    assert data["name"] == "Sam Lee"
    assert data["met_where"] == "PyCon"


def test_list_recent(cli):
    cli.run("network", "add", "Person A", "-w", "Conference")
    cli.run("network", "add", "Person B", "-w", "Meetup")
    connections = cli.json("network", "list")
    assert len(connections) == 2


def test_search_matches_place(cli):
    cli.run("network", "add", "Alice", "-w", "DevConf")
    cli.run("network", "add", "Bob", "-w", "Local meetup")
    results = cli.json("network", "search", "devconf")
    assert len(results) == 1
    assert results[0]["name"] == "Alice"


def test_stats_top_places(cli):
    cli.run("network", "add", "A", "-w", "PyCon")
    cli.run("network", "add", "B", "-w", "PyCon")
    cli.run("network", "add", "C", "-w", "Meetup")
    stats = cli.json("network", "stats")
    assert stats["total"] == 3
    assert stats["top_places"][0] == {"place": "PyCon", "count": 2}


def test_remove(cli):
    conn = cli.json("network", "add", "Temp")
    removed = cli.json("network", "rm", str(conn["id"]))
    assert removed["deleted"] == conn["id"]
