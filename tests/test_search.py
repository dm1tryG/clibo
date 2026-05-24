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


# ── search indexes 7 more entity tools (iter 114) ──


def test_search_finds_events_by_title(cli):
    """The original failing probe: 'dentist'."""
    cli.run("events", "add", "Dentist appointment",
            "-d", "2026-02-15", "-c", "health")
    res = cli.json("search", "dentist")
    assert any(r["source"] == "events" for r in res["results"])


def test_search_finds_events_by_location(cli):
    cli.run("events", "add", "Lunch", "-d", "today",
            "-l", "Blue Bottle Coffee")
    res = cli.json("search", "Blue Bottle")
    assert any(r["source"] == "events" for r in res["results"])


def test_search_finds_birthdays_by_person(cli):
    cli.run("birthdays", "add", "Mom", "-d", "03-15")
    res = cli.json("search", "Mom")
    assert any(r["source"] == "birthdays" for r in res["results"])


def test_search_finds_goals_by_name(cli):
    cli.run("goals", "add", "Read 30 books")
    res = cli.json("search", "books")
    assert any(r["source"] == "goals" for r in res["results"])


def test_search_finds_goals_by_description(cli):
    cli.run("goals", "add", "Health", "-D", "improve cardiovascular fitness")
    res = cli.json("search", "cardiovascular")
    assert any(r["source"] == "goals" for r in res["results"])


def test_search_finds_jobs_by_company(cli):
    cli.run("jobs", "add", "Stripe", "Software Engineer")
    res = cli.json("search", "Stripe")
    assert any(r["source"] == "jobs" for r in res["results"])


def test_search_finds_jobs_by_role(cli):
    cli.run("jobs", "add", "Acme", "Senior Product Manager")
    res = cli.json("search", "Product Manager")
    assert any(r["source"] == "jobs" for r in res["results"])


def test_search_finds_leads_by_name(cli):
    cli.run("leads", "add", "BigCorp deal", "-v", "50000")
    res = cli.json("search", "BigCorp")
    assert any(r["source"] == "leads" for r in res["results"])


def test_search_finds_travel_by_destination(cli):
    cli.run("travel", "add", "Summer trip", "-d", "Berlin")
    res = cli.json("search", "Berlin")
    assert any(r["source"] == "travel" for r in res["results"])


def test_search_finds_pets_by_name(cli):
    cli.run("pets", "add", "Whiskers", "-s", "cat")
    res = cli.json("search", "Whiskers")
    assert any(r["source"] == "pets" for r in res["results"])


def test_search_finds_pets_by_breed(cli):
    cli.run("pets", "add", "Rex", "-s", "dog", "-b", "Golden Retriever")
    res = cli.json("search", "Golden")
    assert any(r["source"] == "pets" for r in res["results"])


# ── search indexes 9 more finance + home tools (iter 115) ──


def test_search_finds_bills_by_name(cli):
    cli.run("bills", "add", "Electricity", "-d", "2026-06-01", "-a", "80")
    res = cli.json("search", "Electricity")
    assert any(r["source"] == "bills" for r in res["results"])


def test_search_finds_subs_by_name(cli):
    cli.run("subs", "add", "Netflix", "-a", "16")
    res = cli.json("search", "Netflix")
    assert any(r["source"] == "subs" for r in res["results"])


def test_search_finds_savings_by_name(cli):
    cli.run("savings", "add", "Vacation fund", "-t", "5000")
    res = cli.json("search", "Vacation")
    assert any(r["source"] == "savings" for r in res["results"])


def test_search_finds_debt_by_name(cli):
    cli.run("debt", "add", "Car loan", "-a", "12000", "-c", "Toyota Finance")
    res = cli.json("search", "Toyota")
    assert any(r["source"] == "debt" for r in res["results"])


def test_search_finds_invoice_by_client(cli):
    cli.run("invoice", "add", "Acme Corp", "-a", "5000",
            "--desc", "Q2 retainer")
    res = cli.json("search", "Acme")
    assert any(r["source"] == "invoice" for r in res["results"])


def test_search_finds_clients_by_company(cli):
    cli.run("clients", "add", "BigCorp", "-c", "BigCorp Inc")
    res = cli.json("search", "BigCorp")
    assert any(r["source"] == "clients" for r in res["results"])


def test_search_finds_clients_by_email(cli):
    cli.run("clients", "add", "Alice", "-e", "alice@bigcorp.com")
    res = cli.json("search", "alice@bigcorp.com")
    assert any(r["source"] == "clients" for r in res["results"])


def test_search_finds_home_by_title(cli):
    cli.run("home", "add", "Painted bedroom", "-k", "improvement",
            "-l", "master bedroom")
    res = cli.json("search", "bedroom")
    assert any(r["source"] == "home" for r in res["results"])


def test_search_finds_home_by_note(cli):
    cli.run("home", "add", "Painted", "-k", "improvement",
            "--note", "used Behr Marquee paint")
    res = cli.json("search", "Behr")
    assert any(r["source"] == "home" for r in res["results"])


def test_search_finds_plants_by_name(cli):
    cli.run("plants", "add", "Monstera", "-s", "Monstera deliciosa")
    res = cli.json("search", "Monstera")
    assert any(r["source"] == "plants" for r in res["results"])


def test_search_finds_plants_by_location(cli):
    cli.run("plants", "add", "Basil", "-l", "kitchen window")
    res = cli.json("search", "kitchen")
    assert any(r["source"] == "plants" for r in res["results"])


def test_search_finds_chores_by_name(cli):
    cli.run("chores", "add", "Vacuum")
    res = cli.json("search", "Vacuum")
    assert any(r["source"] == "chores" for r in res["results"])


def test_search_finds_chores_by_assignee(cli):
    cli.run("chores", "add", "Dishes", "-a", "Sarah")
    res = cli.json("search", "Sarah")
    assert any(r["source"] == "chores" for r in res["results"])
