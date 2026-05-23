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


# ── show progress: season/episode pointer (iter 87) ──


def test_add_show_with_progress(cli):
    """`films add 'Show' -k show -S 6 -E 5` records the pointer
    and auto-bumps status to watching."""
    data = cli.json("films", "add", "Better Call Saul",
                    "-k", "show", "-S", "6", "-E", "5")
    assert data["season"] == 6
    assert data["episode"] == 5
    assert data["progress"] == "S06E05"
    assert data["status"] == "watching"


def test_progress_sets_absolute_pointer(cli):
    cli.run("films", "add", "Show A", "-k", "show")
    data = cli.json("films", "progress", "Show A", "-S", "3", "-E", "7")
    assert data["season"] == 3
    assert data["episode"] == 7
    assert data["progress"] == "S03E07"
    assert data["status"] == "watching"


def test_progress_bump_increments_episode(cli):
    cli.run("films", "add", "Show B", "-k", "show", "-S", "1", "-E", "1")
    data = cli.json("films", "progress", "Show B", "--bump")
    assert data["episode"] == 2
    data = cli.json("films", "progress", "Show B", "--bump")
    assert data["episode"] == 3


def test_progress_bump_with_no_prior_season_defaults_to_s1(cli):
    cli.run("films", "add", "Show C", "-k", "show")
    data = cli.json("films", "progress", "Show C", "--bump")
    assert data["season"] == 1
    assert data["episode"] == 1


def test_progress_episode_only_keeps_season(cli):
    cli.run("films", "add", "Show D", "-k", "show", "-S", "2", "-E", "3")
    data = cli.json("films", "progress", "Show D", "-E", "9")
    assert data["season"] == 2
    assert data["episode"] == 9


def test_progress_on_movie_fails(cli):
    cli.run("films", "add", "Dune", "-k", "movie")
    result = cli.run("films", "progress", "Dune", "-S", "1", "-E", "1")
    assert result.exit_code != 0


def test_progress_no_args_fails(cli):
    cli.run("films", "add", "Show E", "-k", "show")
    result = cli.run("films", "progress", "Show E")
    assert result.exit_code != 0


def test_progress_rejects_zero(cli):
    cli.run("films", "add", "Show F", "-k", "show")
    result = cli.run("films", "progress", "Show F", "-E", "0")
    assert result.exit_code != 0


def test_add_progress_on_movie_rejected(cli):
    """Can't set season/episode on a movie."""
    result = cli.run("films", "add", "Bad Movie", "-k", "movie", "-S", "1")
    assert result.exit_code != 0


# ── new show + edit + rm-by-name (iter 87) ──


def test_show_displays_film(cli):
    cli.run("films", "add", "Dune", "-y", "2021", "-k", "movie")
    data = cli.json("films", "show", "Dune")
    assert data["title"] == "Dune"
    assert data["year"] == 2021


def test_edit_by_title(cli):
    cli.run("films", "add", "Old Title", "-k", "movie")
    edited = cli.json("films", "edit", "Old Title", "-t", "New Title")
    assert edited["title"] == "New Title"


def test_edit_status_to_watched_sets_date(cli):
    cli.run("films", "add", "Movie X", "-k", "movie")
    edited = cli.json("films", "edit", "Movie X", "-s", "watched")
    assert edited["status"] == "watched"
    assert edited["watched_on"] is not None


def test_rm_by_title(cli):
    cli.run("films", "add", "Doomed", "-k", "movie")
    cli.json("films", "rm", "Doomed")
    listing = cli.json("films", "list")
    assert not any(f["title"] == "Doomed" for f in listing)


def test_resolve_exact_match_wins_over_substring(cli):
    """'Dune' should pick Dune (exact), not 'Dune: Part Two' (substring)."""
    cli.run("films", "add", "Dune: Part Two", "-y", "2024", "-k", "movie")
    cli.run("films", "add", "Dune", "-y", "2021", "-k", "movie")
    data = cli.json("films", "show", "Dune")
    assert data["title"] == "Dune"
