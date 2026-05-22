"""Tests for the 👨‍🍳 recipes tool."""

from __future__ import annotations


def test_add_recipe(cli):
    data = cli.json("recipes", "add", "Pasta", "-i", "pasta, tomato", "-s", "2", "-p", "20")
    assert data["name"] == "Pasta"
    assert data["servings"] == 2
    assert data["prep_minutes"] == 20


def test_search_matches_ingredients(cli):
    cli.run("recipes", "add", "Omelette", "-i", "eggs, cheese")
    cli.run("recipes", "add", "Salad", "-i", "lettuce, tomato")
    results = cli.json("recipes", "search", "cheese")
    assert len(results) == 1
    assert results[0]["name"] == "Omelette"


def test_random_picks_a_recipe(cli):
    cli.run("recipes", "add", "Only Recipe")
    chosen = cli.json("recipes", "random")
    assert chosen["name"] == "Only Recipe"


def test_edit_recipe(cli):
    recipe = cli.json("recipes", "add", "Soup")
    edited = cli.json("recipes", "edit", str(recipe["id"]), "-s", "4")
    assert edited["servings"] == 4


def test_stats(cli):
    cli.run("recipes", "add", "A", "-c", "dinner", "-p", "30")
    cli.run("recipes", "add", "B", "-c", "dessert", "-p", "10")
    stats = cli.json("recipes", "stats")
    assert stats["total"] == 2
    assert stats["avg_prep_minutes"] == 20.0


def test_random_without_recipes_fails(cli):
    result = cli.run("recipes", "random")
    assert result.exit_code != 0
