"""🃏 flashcards — spaced-repetition cards (Leitner-style)."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "flashcards"
HELP = "🃏 Spaced-repetition flashcards (Leitner-style)"
EMOJI = "🃏"

#: Box → days until next review.  Box 0 is fresh / just-wrong.
INTERVALS = [1, 3, 7, 14, 30]
MAX_BOX = len(INTERVALS) - 1


class Flashcard(SQLModel, table=True):
    """One card with front/back and a Leitner box."""

    __tablename__ = "flashcards_card"

    id: int | None = Field(default=None, primary_key=True)
    front: str
    back: str
    deck: str = "default"
    box: int = 0
    next_review: date = Field(default_factory=date.today, index=True)
    reviews: int = 0
    correct: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo flashcards`` (bare) runs the ``due`` summary."""
    if ctx.invoked_subcommand is None:
        # Pass real defaults so ctx.invoke doesn't forward Typer's
        # OptionInfo sentinels as literals into the DB query.
        ctx.invoke(due, deck=None, limit=20, json_out=json_out)


def _row(card: Flashcard) -> dict:
    return {
        "id": card.id,
        "deck": card.deck,
        "front": card.front,
        "back": card.back,
        "box": card.box,
        "next_review": card.next_review,
        "due": card.next_review <= date.today(),
        "reviews": card.reviews,
        "correct": card.correct,
        "accuracy_pct": (
            round(card.correct / card.reviews * 100, 1) if card.reviews else None
        ),
    }


@app.command()
def add(
    front: str = typer.Argument(..., help="Front of the card (prompt)"),
    back: str = typer.Argument(..., help="Back of the card (answer)"),
    deck: str = typer.Option("default", "--deck", "-d", help="Deck to add to"),
    json_out: JsonOpt = False,
) -> None:
    """🃏 Add a card."""
    card = Flashcard(front=front, back=back, deck=deck)
    with session() as db:
        db.add(card)
        db.flush()
        db.refresh(card)
        data = _row(card)
    ok(f"Added {EMOJI} '{front}' → '{back}' [{deck}]", json_out=json_out, data=data)


@app.command()
def due(
    deck: str = typer.Option(None, "--deck", "-d", help="Filter by deck"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max cards to show"),
    json_out: JsonOpt = False,
) -> None:
    """🃏 Show cards due for review today."""
    with session() as db:
        query = select(Flashcard).where(Flashcard.next_review <= date.today())
        if deck:
            query = query.where(Flashcard.deck == deck)
        cards = list(db.exec(query.order_by(Flashcard.next_review, Flashcard.id)).all())
    rows = [_row(c) for c in cards[:limit]]
    render_rows(
        rows,
        [("id", "ID"), ("deck", "Deck"), ("front", "Front"),
         ("box", "Box"), ("next_review", "Was Due")],
        json_out=json_out,
        title=f"🃏 Due today  [dim]({len(cards)} cards)[/dim]",
        empty="Nothing due — you're all caught up! ✨",
    )


@app.command()
def grade(
    card_id: int = typer.Argument(..., help="Card ID"),
    result: str = typer.Argument(..., help="right / wrong"),
    json_out: JsonOpt = False,
) -> None:
    """🃏 Record a review: ``right`` advances the card; ``wrong`` resets to box 0."""
    result = result.lower()
    if result not in {"right", "wrong"}:
        fail("Result must be 'right' or 'wrong'", json_out=json_out)
    with session() as db:
        card = db.get(Flashcard, card_id)
        if not card:
            fail(f"No card #{card_id}", json_out=json_out)
        card.reviews += 1
        if result == "right":
            card.correct += 1
            card.box = min(card.box + 1, MAX_BOX)
        else:
            card.box = 0
        card.next_review = date.today() + timedelta(days=INTERVALS[card.box])
        db.add(card)
        db.flush()
        data = _row(card)
    next_in = (card.next_review - date.today()).days
    ok(f"Graded {result} — box {card.box}, next review in {next_in}d",
       json_out=json_out, data=data)


@app.command(name="list")
def list_cards(
    deck: str = typer.Option(None, "--deck", "-d", help="Filter by deck"),
    json_out: JsonOpt = False,
) -> None:
    """🃏 List all cards."""
    with session() as db:
        query = select(Flashcard)
        if deck:
            query = query.where(Flashcard.deck == deck)
        cards = list(db.exec(query.order_by(Flashcard.deck, Flashcard.id)).all())
    render_rows(
        [_row(c) for c in cards],
        [("id", "ID"), ("deck", "Deck"), ("front", "Front"), ("back", "Back"),
         ("box", "Box"), ("next_review", "Next"), ("accuracy_pct", "Acc")],
        json_out=json_out,
        title="🃏 Flashcards",
        empty="No cards yet — try: clibo flashcards add 'día' 'day' -d spanish",
    )


@app.command()
def decks(json_out: JsonOpt = False) -> None:
    """🃏 List decks with card counts and due counts."""
    today = date.today()
    with session() as db:
        cards = list(db.exec(select(Flashcard)).all())
    by_deck: dict[str, dict] = {}
    for card in cards:
        bucket = by_deck.setdefault(card.deck, {"total": 0, "due": 0})
        bucket["total"] += 1
        if card.next_review <= today:
            bucket["due"] += 1
    rows = [
        {"deck": d, "cards": info["total"], "due": info["due"]}
        for d, info in sorted(by_deck.items())
    ]
    render_rows(
        rows,
        [("deck", "Deck"), ("cards", "Cards"), ("due", "Due")],
        json_out=json_out,
        title="🃏 Decks",
        empty="No decks yet.",
    )


@app.command()
def rm(card_id: int = typer.Argument(..., help="Card ID"), json_out: JsonOpt = False) -> None:
    """🃏 Delete a card."""
    with session() as db:
        card = db.get(Flashcard, card_id)
        if not card:
            fail(f"No card #{card_id}", json_out=json_out)
        db.delete(card)
    ok(f"Deleted card #{card_id}", json_out=json_out, data={"deleted": card_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Flashcard stats — mastery distribution and accuracy."""
    with session() as db:
        cards = list(db.exec(select(Flashcard)).all())
    if not cards:
        fail("No cards yet", json_out=json_out)
    today = date.today()
    by_box = {b: sum(1 for c in cards if c.box == b) for b in range(MAX_BOX + 1)}
    reviews = sum(c.reviews for c in cards)
    correct = sum(c.correct for c in cards)
    data = {
        "total_cards": len(cards),
        "due_today": sum(1 for c in cards if c.next_review <= today),
        "decks": len({c.deck for c in cards}),
        "by_box": by_box,
        "total_reviews": reviews,
        "accuracy_pct": round(correct / reviews * 100, 1) if reviews else None,
        "mastered_box_4": by_box[MAX_BOX],
    }
    render_record(data, json_out=json_out, title="📊 Flashcard stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
