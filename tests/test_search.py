"""Tests for the 🔍 global search command."""

from __future__ import annotations


def test_search_finds_notes(cli):
    cli.run("notes", "add", "Idea", "-b", "Build a CLI toolbox with rainbow output")
    cli.run("notes", "add", "Other", "-b", "unrelated text")
    result = cli.json("search", "rainbow")
    assert result["count"] == 1
    assert result["results"][0]["source"] == "notes"


def test_search_spans_multiple_tools(cli):
    cli.run("notes", "add", "Acme research")
    cli.run("crm", "add", "Anna", "-c", "Acme")
    cli.run("todo", "add", "Email Acme about contract")
    cli.run("bookmark", "add", "https://acme.example.com", "-t", "Acme docs")
    result = cli.json("search", "acme")
    sources = {hit["source"] for hit in result["results"]}
    assert sources >= {"notes", "todo", "crm", "bookmark"}
    assert result["count"] >= 4


def test_search_includes_recipes_and_brag(cli):
    cli.run("recipes", "add", "Pasta", "-i", "spaghetti, tomatoes, basil")
    cli.run("brag", "add", "Shipped basil parser", "-i", "Cut parse time")
    result = cli.json("search", "basil")
    sources = {hit["source"] for hit in result["results"]}
    assert "recipes" in sources
    assert "brag" in sources


def test_search_no_matches(cli):
    cli.run("notes", "add", "Existing")
    result = cli.json("search", "nothing-matches-this")
    assert result["count"] == 0
    assert result["results"] == []


def test_search_each_result_has_snippet(cli):
    cli.run("journal", "write", "A productive day building widgets")
    result = cli.json("search", "widgets")
    assert all(hit["snippet"] for hit in result["results"])


def test_search_covers_beyond_50_tools(cli):
    """The 12 tools added after v1.0 must also be searchable."""
    cli.run("books", "add", "Atomic Habits", "-a", "James Clear")
    cli.run("films", "add", "Atomic Blonde")
    cli.run("ideas", "add", "atomic widget refactor")
    cli.run("quotes", "add", "atomic wisdom", "-a", "Sage")
    cli.run("lessons", "add", "keep changes atomic")
    cli.run("cv", "add", "Atomic team lead", "-o", "X")
    cli.run("dreams", "add", "atomic explosion dream")
    cli.run("gratitude", "add", "atomic clarity")
    cli.run("income", "add", "Atomic Corp salary", "-a", "1000")
    result = cli.json("search", "atomic")
    sources = {hit["source"] for hit in result["results"]}
    assert {"books", "films", "ideas", "quotes", "lessons", "cv",
            "dreams", "gratitude", "income"} <= sources


# ── search covers writing + book-sessions + symptom (iter 97) ──


def test_search_finds_writing_session_note(cli):
    cli.run("writing", "log", "novel", "-w", "500",
            "--note", "draft of chapter 3")
    res = cli.json("search", "chapter")
    sources = [r["source"] for r in res["results"]]
    assert "writing" in sources


def test_search_finds_writing_by_project(cli):
    cli.run("writing", "log", "memoir", "-w", "500")
    res = cli.json("search", "memoir")
    assert any(r["source"] == "writing" for r in res["results"])


def test_search_finds_book_session_by_note(cli):
    """`books read --note "..."` text should be findable."""
    cli.run("books", "add", "Atomic Habits", "-p", "320")
    cli.run("books", "read", "Atomic Habits", "30",
            "--note", "great chapter on identity")
    res = cli.json("search", "identity")
    sources = [r["source"] for r in res["results"]]
    assert "reading" in sources


def test_search_finds_symptom_by_name(cli):
    cli.run("symptom", "log", "migraine", "-i", "8")
    res = cli.json("search", "migraine")
    assert any(r["source"] == "symptom" for r in res["results"])


def test_search_finds_symptom_by_location(cli):
    cli.run("symptom", "log", "back pain", "-i", "7", "-l", "lumbar")
    res = cli.json("search", "lumbar")
    assert any(r["source"] == "symptom" for r in res["results"])


def test_search_finds_symptom_by_triggers(cli):
    cli.run("symptom", "log", "headache", "-i", "5",
            "--triggers", "poor sleep, bright light")
    res = cli.json("search", "bright")
    assert any(r["source"] == "symptom" for r in res["results"])
