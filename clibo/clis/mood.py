"""🙂 mood — daily mood & emotion journal."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, console, fail, ok, render_record, render_rows

NAME = "mood"
HELP = "🙂 Daily mood & emotion journal"
EMOJI = "🙂"
MOOD_FACES = {1: "😞", 2: "🙁", 3: "😐", 4: "🙂", 5: "😄"}
MOOD_LABELS = {1: "awful", 2: "low", 3: "okay", 4: "good", 5: "great"}


class MoodLog(SQLModel, table=True):
    """One mood check-in: a 1–5 score with optional emotion tag and note."""

    __tablename__ = "mood_log"

    id: int | None = Field(default=None, primary_key=True)
    score: int
    emotion: str | None = None
    note: str | None = None
    entry_date: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _row(entry: MoodLog) -> dict:
    return {
        "id": entry.id,
        "entry_date": entry.entry_date,
        "score": entry.score,
        "face": MOOD_FACES.get(entry.score, "?"),
        "label": MOOD_LABELS.get(entry.score, "?"),
        "emotion": entry.emotion,
        "note": entry.note,
    }


@app.command()
def log(
    score: int = typer.Argument(..., help="How you feel, 1 (awful) – 5 (great)"),
    emotion: str = typer.Option(None, "--emotion", "-e", help="Emotion word, e.g. 'calm'"),
    note: str = typer.Option(None, "--note", "-n", help="What's on your mind"),
    on: str = typer.Option("today", "--date", "-d", help="Date"),
    json_out: JsonOpt = False,
) -> None:
    """🙂 Log how you're feeling right now."""
    if score not in MOOD_FACES:
        fail("Score must be 1–5", json_out=json_out)
    entry = MoodLog(
        score=score,
        emotion=emotion.lower() if emotion else None,
        note=note,
        entry_date=parse_date(on),
    )
    with session() as db:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        data = _row(entry)
    ok(
        f"Logged mood {MOOD_FACES[score]} {MOOD_LABELS[score]}"
        + (f" — {emotion}" if emotion else ""),
        json_out=json_out,
        data=data,
    )


# `add` is a friendlier alias for `log` (predictable verbs across tools).
app.command(name="add", help="Alias for `log`")(log)


@app.command()
def today(json_out: JsonOpt = False) -> None:
    """🙂 Show today's mood check-ins."""
    day = date.today()
    with session() as db:
        entries = list(
            db.exec(
                select(MoodLog)
                .where(MoodLog.entry_date == day)
                .order_by(MoodLog.created_at)
            ).all()
        )
    rows = [_row(e) for e in entries]
    if json_out:
        avg = round(sum(r["score"] for r in rows) / len(rows), 1) if rows else None
        render_record({"date": day, "checkins": rows, "avg_score": avg}, json_out=True)
        return
    render_rows(
        rows,
        [("face", " "), ("score", "Score"), ("emotion", "Emotion"), ("note", "Note")],
        json_out=False,
        title=f"🙂 Mood · {day:%a %d %b}",
        empty="No mood logged today — try: clibo mood log 4 -e calm",
    )
    if rows:
        avg = sum(r["score"] for r in rows) / len(rows)
        console.print(f"  Average today: [bold]{avg:.1f}/5[/bold]  {MOOD_FACES[round(avg)]}")


@app.command(name="list")
def list_entries(
    days: int = typer.Option(14, "--days", help="Look back this many days"),
    json_out: JsonOpt = False,
) -> None:
    """🙂 List recent mood check-ins."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(
            db.exec(
                select(MoodLog)
                .where(MoodLog.entry_date >= since)
                .order_by(MoodLog.entry_date.desc(), MoodLog.id.desc())
            ).all()
        )
    render_rows(
        [_row(e) for e in entries],
        [("id", "ID"), ("entry_date", "Date"), ("face", " "),
         ("score", "Score"), ("emotion", "Emotion"), ("note", "Note")],
        json_out=json_out,
        title="🙂 Mood journal",
        empty="No mood entries yet.",
    )


@app.command()
def rm(entry_id: int = typer.Argument(..., help="Entry ID"), json_out: JsonOpt = False) -> None:
    """🙂 Delete a mood check-in."""
    with session() as db:
        entry = db.get(MoodLog, entry_id)
        if not entry:
            fail(f"No mood entry #{entry_id}", json_out=json_out)
        db.delete(entry)
    ok(f"Deleted mood entry #{entry_id}", json_out=json_out, data={"deleted": entry_id})


@app.command()
def stats(
    days: int = typer.Option(30, "--days", help="Window size in days"),
    json_out: JsonOpt = False,
) -> None:
    """📊 Mood stats and distribution over the last N days."""
    since = date.today() - timedelta(days=days - 1)
    with session() as db:
        entries = list(db.exec(select(MoodLog).where(MoodLog.entry_date >= since)).all())
    if not entries:
        fail("No mood logged in this window", json_out=json_out)
    scores = [e.score for e in entries]
    distribution = {MOOD_FACES[s]: sum(1 for x in scores if x == s) for s in MOOD_FACES}
    emotions: dict[str, int] = {}
    for entry in entries:
        if entry.emotion:
            emotions[entry.emotion] = emotions.get(entry.emotion, 0) + 1
    top = sorted(emotions.items(), key=lambda kv: kv[1], reverse=True)[:3]
    data = {
        "window_days": days,
        "checkins": len(entries),
        "days_logged": len({e.entry_date for e in entries}),
        "avg_score": round(sum(scores) / len(scores), 1),
        "best_score": max(scores),
        "worst_score": min(scores),
        "distribution": distribution,
        "top_emotions": [{"emotion": name, "count": count} for name, count in top],
    }
    render_record(data, json_out=json_out, title=f"📊 Mood stats · last {days}d")
