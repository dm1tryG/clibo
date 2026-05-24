"""🎯 goals — goals & OKRs with milestones."""

from __future__ import annotations

from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import humanize_delta, parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, bar, fail, ok, render_record, render_rows

NAME = "goals"
HELP = "🎯 Goals & OKRs with milestones"
EMOJI = "🎯"


class Goal(SQLModel, table=True):
    """A goal or objective, optionally broken into milestones."""

    __tablename__ = "goals_goal"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = None
    deadline: date | None = None
    done: bool = False
    done_at: date | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class Milestone(SQLModel, table=True):
    """A checkpoint on the way to a goal."""

    __tablename__ = "goals_milestone"

    id: int | None = Field(default=None, primary_key=True)
    goal_id: int = Field(index=True)
    name: str
    done: bool = False
    done_at: date | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=True, help=HELP)


def _resolve(db, ident: str) -> Goal | None:
    """Look up a goal by numeric ID or by (case-insensitive) name."""
    if ident.isdigit():
        goal = db.get(Goal, int(ident))
        if goal:
            return goal
    return db.exec(select(Goal).where(Goal.name.ilike(ident))).first()


def _row(db, goal: Goal) -> dict:
    milestones = db.exec(select(Milestone).where(Milestone.goal_id == goal.id)).all()
    total = len(milestones)
    done = sum(1 for m in milestones if m.done)
    if total:
        progress = round(done / total * 100, 1)
    else:
        progress = 100.0 if goal.done else 0.0
    return {
        "id": goal.id,
        "name": goal.name,
        "description": goal.description,
        "deadline": goal.deadline,
        "deadline_in": humanize_delta(goal.deadline) if goal.deadline else None,
        "done": goal.done,
        "milestones_total": total,
        "milestones_done": done,
        "progress_pct": progress,
        "note": goal.note,
    }


@app.command()
def add(
    name: str = typer.Argument(..., help="Goal name"),
    description: str = typer.Option(None, "--desc", "-D", help="What the goal means"),
    deadline: str = typer.Option(None, "--deadline", "-d", help="Target date"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """🎯 Create a goal."""
    goal = Goal(
        name=name, description=description,
        deadline=parse_date(deadline) if deadline else None, note=note,
    )
    with session() as db:
        db.add(goal)
        db.flush()
        db.refresh(goal)
        data = _row(db, goal)
    ok(f"Created {EMOJI} goal '{name}'", json_out=json_out, data=data)


@app.command()
def milestone(
    goal: str = typer.Argument(..., help="Goal name or ID"),
    name: str = typer.Argument(..., help="Milestone name"),
    json_out: JsonOpt = False,
) -> None:
    """🎯 Add a milestone to a goal."""
    with session() as db:
        target = _resolve(db, goal)
        if not target:
            fail(f"No goal matching {goal!r}", json_out=json_out)
        ms = Milestone(goal_id=target.id, name=name)
        db.add(ms)
        db.flush()
        db.refresh(ms)
        data = {"id": ms.id, "goal": target.name, "name": ms.name, "done": False}
    ok(f"Added milestone to '{target.name}': {name}", json_out=json_out, data=data)


@app.command(name="list")
def list_goals(
    show_all: bool = typer.Option(False, "--all", help="Include completed goals"),
    json_out: JsonOpt = False,
) -> None:
    """🎯 List goals with milestone progress."""
    with session() as db:
        query = select(Goal)
        if not show_all:
            query = query.where(Goal.done == False)  # noqa: E712
        goals = list(db.exec(query.order_by(Goal.name)).all())
        rows = [_row(db, g) for g in goals]
    render_rows(
        rows,
        [("id", "ID"), ("name", "Goal"), ("milestones_done", "Milestones"),
         ("progress_pct", "Progress"), ("deadline", "Deadline"), ("deadline_in", "When")],
        json_out=json_out,
        title="🎯 Goals",
        formatters={
            "milestones_done": lambda v, r: f"{v}/{r['milestones_total']}",
            "progress_pct": lambda v, r: bar(v, 100),
        },
        empty="No goals yet — try: clibo goals add 'Learn Spanish'",
    )


@app.command()
def show(
    goal: str = typer.Argument(..., help="Goal name or ID"),
    json_out: JsonOpt = False,
) -> None:
    """🎯 Show a goal with its milestones."""
    with session() as db:
        target = _resolve(db, goal)
        if not target:
            fail(f"No goal matching {goal!r}", json_out=json_out)
        data = _row(db, target)
        milestones = [
            {"id": m.id, "name": m.name, "done": m.done, "done_at": m.done_at}
            for m in db.exec(
                select(Milestone).where(Milestone.goal_id == target.id).order_by(Milestone.id)
            ).all()
        ]
    if json_out:
        render_record(data | {"milestones": milestones}, json_out=True)
        return
    render_record(data, json_out=False, title=f"🎯 {target.name}")
    render_rows(
        milestones,
        [("id", "ID"), ("done", "✓"), ("name", "Milestone"), ("done_at", "Done")],
        json_out=False,
        title="Milestones",
        empty="No milestones — add one with: clibo goals milestone <goal> '<step>'",
    )


@app.command()
def check(milestone_id: int = typer.Argument(..., help="Milestone ID"), json_out: JsonOpt = False) -> None:
    """🎯 Mark a milestone as done."""
    with session() as db:
        ms = db.get(Milestone, milestone_id)
        if not ms:
            fail(f"No milestone #{milestone_id}", json_out=json_out)
        ms.done = True
        ms.done_at = date.today()
        db.add(ms)
        db.flush()
        data = _row(db, db.get(Goal, ms.goal_id))
    ok(f"Milestone done {EMOJI}: {ms.name}", json_out=json_out, data=data)


@app.command()
def uncheck(milestone_id: int = typer.Argument(..., help="Milestone ID"), json_out: JsonOpt = False) -> None:
    """🎯 Mark a milestone as not done."""
    with session() as db:
        ms = db.get(Milestone, milestone_id)
        if not ms:
            fail(f"No milestone #{milestone_id}", json_out=json_out)
        ms.done = False
        ms.done_at = None
        db.add(ms)
        db.flush()
        data = _row(db, db.get(Goal, ms.goal_id))
    ok(f"Reopened milestone: {ms.name}", json_out=json_out, data=data)


@app.command()
def complete(
    goal: str = typer.Argument(..., help="Goal name or ID"),
    json_out: JsonOpt = False,
) -> None:
    """🏆 Mark a whole goal as achieved."""
    with session() as db:
        target = _resolve(db, goal)
        if not target:
            fail(f"No goal matching {goal!r}", json_out=json_out)
        target.done = True
        target.done_at = date.today()
        db.add(target)
        db.flush()
        data = _row(db, target)
    ok(f"Goal achieved {EMOJI} '{target.name}' 🎉", json_out=json_out, data=data)


@app.command()
def rm(goal_id: int = typer.Argument(..., help="Goal ID"), json_out: JsonOpt = False) -> None:
    """🎯 Delete a goal and its milestones."""
    with session() as db:
        goal = db.get(Goal, goal_id)
        if not goal:
            fail(f"No goal #{goal_id}", json_out=json_out)
        for ms in db.exec(select(Milestone).where(Milestone.goal_id == goal_id)).all():
            db.delete(ms)
        db.delete(goal)
    ok(f"Deleted goal #{goal_id}", json_out=json_out, data={"deleted": goal_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Goal stats."""
    with session() as db:
        goals = list(db.exec(select(Goal)).all())
        milestones = list(db.exec(select(Milestone)).all())
    data = {
        "total_goals": len(goals),
        "achieved": sum(1 for g in goals if g.done),
        "in_progress": sum(1 for g in goals if not g.done),
        "total_milestones": len(milestones),
        "milestones_done": sum(1 for m in milestones if m.done),
    }
    render_record(data, json_out=json_out, title="📊 Goal stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
