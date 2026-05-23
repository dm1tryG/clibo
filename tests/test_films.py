"""Tests for the 🎬 films tool."""

from __future__ import annotations


def test_add_movie(cli):
    data = cli.json("films", "add", "Dune", "-y", "2021", "-k", "movie")
    assert data["title"] == "Dune"
    assert data["year"] == 2021
    assert data["kind"] == "movie"
    assert data["status"] == "watchlist"


def test_watched_with_rating(cli):
    cli.run("films", "add", "Dune", "-y", "2021")
    data = cli.json("films", "watched", "Dune", "-r", "5")
    assert data["status"] == "watched"
    assert data["rating"] == 5
    assert data["watched_on"] is not None


def test_rate_changes_rating(cli):
    cli.run("films", "add", "Mid", "-s", "watched")
    data = cli.json("films", "rate", "Mid", "3")
    assert data["rating"] == 3


def test_list_filters(cli):
    cli.run("films", "add", "Movie A", "-k", "movie")
    cli.run("films", "add", "Show B", "-k", "show")
    movies = cli.json("films", "list", "-k", "movie")
    assert len(movies) == 1
    assert movies[0]["title"] == "Movie A"


def test_stats_top_rated(cli):
    cli.run("films", "add", "Great", "-s", "watched", "-r", "5")
    cli.run("films", "add", "Good", "-s", "watched", "-r", "4")
    cli.run("films", "add", "Meh", "-s", "watched", "-r", "2")
    stats = cli.json("films", "stats")
    assert stats["watched"] == 3
    assert stats["top_rated"][0] == {"title": "Great", "rating": 5}


def test_invalid_kind_fails(cli):
    result = cli.run("films", "add", "Bad", "-k", "documentary")
    assert result.exit_code != 0
