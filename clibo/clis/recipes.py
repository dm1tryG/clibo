"""👨‍🍳 recipes — personal recipe book."""

from __future__ import annotations

import random
from datetime import datetime

import typer
from sqlalchemy import or_
from sqlmodel import Field, SQLModel, select

from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "recipes"
HELP = "👨‍🍳 Personal recipe book"
EMOJI = "👨‍🍳"


class Recipe(SQLModel, table=True):
    """A saved recipe."""

    __tablename__ = "recipes_recipe"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    ingredients: str | None = None
    instructions: str | None = None
    servings: int | None = None
    prep_minutes: int | None = None
    category: str = "other"
    tags: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(recipe: Recipe) -> dict:
    return {
        "id": recipe.id,
        "name": recipe.name,
        "ingredients": recipe.ingredients,
        "instructions": recipe.instructions,
        "servings": recipe.servings,
        "prep_minutes": recipe.prep_minutes,
        "category": recipe.category,
        "tags": recipe.tags,
    }


@app.command()
def add(
    name: str = typer.Argument(..., help="Recipe name"),
    ingredients: str = typer.Option(None, "--ingredients", "-i", help="Ingredients"),
    instructions: str = typer.Option(None, "--instructions", "-I", help="How to cook it"),
    servings: int = typer.Option(None, "--servings", "-s", help="Number of servings"),
    prep: int = typer.Option(None, "--prep", "-p", help="Prep time in minutes"),
    category: str = typer.Option("other", "--category", "-c", help="Category"),
    tag: str = typer.Option(None, "--tag", "-t", help="Comma-separated tags"),
    json_out: JsonOpt = False,
) -> None:
    """👨‍🍳 Save a recipe."""
    recipe = Recipe(
        name=name, ingredients=ingredients, instructions=instructions,
        servings=servings, prep_minutes=prep, category=category.lower(), tags=tag,
    )
    with session() as db:
        db.add(recipe)
        db.flush()
        db.refresh(recipe)
        data = _row(recipe)
    ok(f"Saved {EMOJI} recipe '{name}'", json_out=json_out, data=data)


@app.command(name="list")
def list_recipes(
    category: str = typer.Option(None, "--category", "-c", help="Filter by category"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    json_out: JsonOpt = False,
) -> None:
    """👨‍🍳 List recipes."""
    with session() as db:
        query = select(Recipe)
        if category:
            query = query.where(Recipe.category == category.lower())
        if tag:
            query = query.where(Recipe.tags.ilike(f"%{tag}%"))
        recipes = list(db.exec(query.order_by(Recipe.name)).all())
    render_rows(
        [_row(r) for r in recipes],
        [("id", "ID"), ("name", "Recipe"), ("category", "Category"),
         ("servings", "Servings"), ("prep_minutes", "Prep·min"), ("tags", "Tags")],
        json_out=json_out,
        title="👨‍🍳 Recipes",
        empty="No recipes yet — try: clibo recipes add 'Pasta' -i 'pasta, tomato'",
    )


@app.command()
def show(recipe_id: int = typer.Argument(..., help="Recipe ID"), json_out: JsonOpt = False) -> None:
    """👨‍🍳 Show a full recipe."""
    with session() as db:
        recipe = db.get(Recipe, recipe_id)
        if not recipe:
            fail(f"No recipe #{recipe_id}", json_out=json_out)
        data = _row(recipe)
    if json_out:
        render_record(data, json_out=True)
        return
    render_record(
        {"id": recipe.id, "name": recipe.name, "category": recipe.category,
         "servings": recipe.servings, "prep_minutes": recipe.prep_minutes, "tags": recipe.tags},
        json_out=False,
        title=f"👨‍🍳 {recipe.name}",
    )
    if recipe.ingredients:
        console.print("[bold cyan]Ingredients[/bold cyan]")
        console.print(f"  {recipe.ingredients}\n")
    if recipe.instructions:
        console.print("[bold cyan]Instructions[/bold cyan]")
        console.print(f"  {recipe.instructions}\n")


@app.command()
def search(
    query: str = typer.Argument(..., help="Text to search for"),
    json_out: JsonOpt = False,
) -> None:
    """🔍 Search recipes by name, ingredients or tags."""
    pattern = f"%{query}%"
    with session() as db:
        recipes = list(
            db.exec(
                select(Recipe).where(
                    or_(
                        Recipe.name.ilike(pattern),
                        Recipe.ingredients.ilike(pattern),
                        Recipe.tags.ilike(pattern),
                    )
                ).order_by(Recipe.name)
            ).all()
        )
    render_rows(
        [_row(r) for r in recipes],
        [("id", "ID"), ("name", "Recipe"), ("category", "Category"), ("tags", "Tags")],
        json_out=json_out,
        title=f"🔍 Recipes matching '{query}'",
        empty=f"No recipes match '{query}'.",
    )


@app.command()
def edit(
    recipe_id: int = typer.Argument(..., help="Recipe ID"),
    name: str = typer.Option(None, "--name", help="New name"),
    ingredients: str = typer.Option(None, "--ingredients", "-i"),
    instructions: str = typer.Option(None, "--instructions", "-I"),
    servings: int = typer.Option(None, "--servings", "-s"),
    prep: int = typer.Option(None, "--prep", "-p"),
    json_out: JsonOpt = False,
) -> None:
    """👨‍🍳 Edit a recipe."""
    with session() as db:
        recipe = db.get(Recipe, recipe_id)
        if not recipe:
            fail(f"No recipe #{recipe_id}", json_out=json_out)
        for field, value in {"name": name, "ingredients": ingredients,
                             "instructions": instructions, "servings": servings,
                             "prep_minutes": prep}.items():
            if value is not None:
                setattr(recipe, field, value)
        db.add(recipe)
        db.flush()
        data = _row(recipe)
    ok(f"Updated recipe #{recipe_id}", json_out=json_out, data=data)


@app.command()
def rm(recipe_id: int = typer.Argument(..., help="Recipe ID"), json_out: JsonOpt = False) -> None:
    """👨‍🍳 Delete a recipe."""
    with session() as db:
        recipe = db.get(Recipe, recipe_id)
        if not recipe:
            fail(f"No recipe #{recipe_id}", json_out=json_out)
        db.delete(recipe)
    ok(f"Deleted recipe #{recipe_id}", json_out=json_out, data={"deleted": recipe_id})


@app.command(name="random")
def pick(json_out: JsonOpt = False) -> None:
    """🎲 Pick a random recipe — for when you can't decide what to cook."""
    with session() as db:
        recipes = list(db.exec(select(Recipe)).all())
    if not recipes:
        fail("No recipes yet — add one first", json_out=json_out)
    chosen = random.choice(recipes)
    data = _row(chosen)
    if json_out:
        render_record(data, json_out=True)
        return
    console.print(f"\n🎲 Tonight, why not cook:  [bold green]{chosen.name}[/bold green]")
    if chosen.prep_minutes:
        console.print(f"   [dim]~{chosen.prep_minutes} min prep[/dim]")
    console.print(f"   [dim]clibo recipes show {chosen.id}[/dim]\n")


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Recipe-book stats."""
    with session() as db:
        recipes = list(db.exec(select(Recipe)).all())
    by_category: dict[str, int] = {}
    for recipe in recipes:
        by_category[recipe.category] = by_category.get(recipe.category, 0) + 1
    preps = [r.prep_minutes for r in recipes if r.prep_minutes]
    data = {
        "total": len(recipes),
        "by_category": by_category,
        "avg_prep_minutes": round(sum(preps) / len(preps), 1) if preps else None,
    }
    render_record(data, json_out=json_out, title="📊 Recipe stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `update` is the SQL-natural synonym for `edit`; both work.
app.command(name="update", help="Alias for `edit`")(edit)

# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
