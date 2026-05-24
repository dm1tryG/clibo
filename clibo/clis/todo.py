"""✅ todo — task & to-do manager."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import humanize_delta, parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "todo"
HELP = "✅ Task & to-do manager"
EMOJI = "✅"

#: priority name -> sort rank (higher = more urgent)
PRIORITIES: dict[str, int] = {"low": 0, "med": 1, "high": 2}


class Task(SQLModel, table=True):
    """A single to-do task."""

    __tablename__ = "todo_task"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    priority: str = "med"
    due: date | None = None
    done: bool = False
    done_at: date | None = None
    project: str | None = None
    tags: str | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo todo`` (bare) lists pending tasks.

    Same as ``clibo todo list`` — every optional filter passed at its
    declared default so Typer's ArgumentInfo sentinel doesn't leak in.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(
            list_tasks,
            show_all=False, project=None, tag=None,
            due=None, overdue=False, due_within=None,
            json_out=json_out,
        )


def _row(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "priority": task.priority,
        "due": task.due,
        "due_in": humanize_delta(task.due) if task.due else None,
        "overdue": bool(task.due and not task.done and task.due < date.today()),
        "done": task.done,
        "done_at": task.done_at,
        "project": task.project,
        "tags": task.tags,
        "note": task.note,
    }


def _priority_cell(value: str) -> str:
    return {
        "high": "[red]● high[/red]",
        "med": "[yellow]● med[/yellow]",
        "low": "[dim]● low[/dim]",
    }.get(value, value)


@app.command()
def add(
    title: str = typer.Argument(..., help="What needs doing"),
    priority: str = typer.Option("med", "--priority", "-p", help="low / med / high"),
    due: str = typer.Option(None, "--due", "-d", help="Due date"),
    project: str = typer.Option(None, "--project", "-P", help="Project this belongs to"),
    tag: str = typer.Option(None, "--tag", "-t", help="Comma-separated tags"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """✅ Add a task."""
    priority = priority.lower()
    if priority not in PRIORITIES:
        fail(f"Priority must be one of: {', '.join(PRIORITIES)}", json_out=json_out)
    task = Task(
        title=title, priority=priority,
        due=parse_date(due) if due else None,
        project=project, tags=tag, note=note,
    )
    with session() as db:
        db.add(task)
        db.flush()
        db.refresh(task)
        data = _row(task)
    ok(f"Added {EMOJI} task #{task.id}: {title}", json_out=json_out, data=data)


@app.command(name="list")
def list_tasks(
    show_all: bool = typer.Option(False, "--all", help="Include completed tasks"),
    project: str = typer.Option(None, "--project", "-P", help="Filter by project"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    due: str = typer.Option(
        None, "--due", "-d",
        help="Only tasks due on this date "
             "(accepts 'today' / 'tomorrow' / 'yesterday' / YYYY-MM-DD)",
    ),
    overdue: bool = typer.Option(
        False, "--overdue",
        help="Only show pending tasks whose due date is in the past",
    ),
    due_within: int = typer.Option(
        None, "--due-within",
        help="Only pending tasks due in the next N days "
             "(includes overdue and today)",
    ),
    json_out: JsonOpt = False,
) -> None:
    """✅ List tasks (pending first, by priority then due date).

    Date filters answer common asks: ``--due today``,
    ``--due tomorrow``, ``--overdue``, ``--due-within 7``. These
    combine with ``--project`` / ``--tag``; ``--due`` takes
    precedence over ``--due-within`` when both are passed.
    """
    if due_within is not None and due_within < 0:
        fail("--due-within must be ≥ 0", json_out=json_out)
    target_due: date | None = None
    if due:
        try:
            target_due = parse_date(due)
        except Exception:
            fail(f"Could not parse date {due!r}", json_out=json_out)
    today = date.today()
    with session() as db:
        query = select(Task)
        if not show_all:
            query = query.where(Task.done == False)  # noqa: E712
        if project:
            query = query.where(Task.project == project)
        if tag:
            query = query.where(Task.tags.ilike(f"%{tag}%"))
        # Date filters — `--due` is exact-match and wins over `--due-within`.
        if target_due is not None:
            query = query.where(Task.due == target_due)
        elif overdue:
            query = query.where(Task.due != None)  # noqa: E711
            query = query.where(Task.due < today)
        elif due_within is not None:
            horizon = today + timedelta(days=due_within)
            query = query.where(Task.due != None)  # noqa: E711
            query = query.where(Task.due <= horizon)
        tasks = list(db.exec(query).all())
    tasks.sort(key=lambda t: (
        t.done,
        -PRIORITIES.get(t.priority, 1),
        t.due or date.max,
        t.id,
    ))
    render_rows(
        [_row(t) for t in tasks],
        [("id", "ID"), ("done", "✓"), ("title", "Task"), ("priority", "Priority"),
         ("due", "Due"), ("due_in", "When"), ("project", "Project")],
        json_out=json_out,
        title="✅ Tasks",
        formatters={
            "priority": lambda v, r: _priority_cell(v),
            "due_in": lambda v, r: (f"[red]{v}[/red]" if r["overdue"] else (v or "[dim]—[/dim]")),
        },
        empty="No tasks — add one with: clibo todo add 'Buy milk' -p high",
    )


@app.command()
def done(task_id: int = typer.Argument(..., help="Task ID"), json_out: JsonOpt = False) -> None:
    """✅ Mark a task as done."""
    with session() as db:
        task = db.get(Task, task_id)
        if not task:
            fail(f"No task #{task_id}", json_out=json_out)
        task.done = True
        task.done_at = date.today()
        db.add(task)
        db.flush()
        data = _row(task)
    ok(f"Completed {EMOJI} task #{task_id}: {task.title}", json_out=json_out, data=data)


# `complete` is the formal-prose verb — agents say "mark this task as complete";
# `done` is the short form. Both work.
app.command(name="complete", help="Alias for `done`")(done)


@app.command()
def snooze(
    task_id: int = typer.Argument(..., help="Task ID"),
    days: int = typer.Option(
        1, "--days", "-d",
        help="Days to push the due date forward (default 1)",
    ),
    json_out: JsonOpt = False,
) -> None:
    """⏰ Push a task's due date forward by N days.

    *"Snooze this for 2 days"* → ``clibo todo snooze 1 -d 2``. If the
    task has no due date yet, the new due is set to ``today + N``.
    Existing due dates roll forward from their current value, so a
    task already due tomorrow snoozed by 2 lands the day after that.
    """
    if days < 1:
        fail("--days must be >= 1", json_out=json_out)
    with session() as db:
        task = db.get(Task, task_id)
        if not task:
            fail(f"No task #{task_id}", json_out=json_out)
        # Roll forward from existing due if any; otherwise anchor on today.
        anchor = task.due or date.today()
        task.due = anchor + timedelta(days=days)
        db.add(task)
        db.flush()
        data = _row(task)
    ok(
        f"Snoozed {EMOJI} task #{task_id} → {task.due}",
        json_out=json_out, data=data,
    )


@app.command()
def undone(task_id: int = typer.Argument(..., help="Task ID"), json_out: JsonOpt = False) -> None:
    """✅ Mark a task as not done again."""
    with session() as db:
        task = db.get(Task, task_id)
        if not task:
            fail(f"No task #{task_id}", json_out=json_out)
        task.done = False
        task.done_at = None
        db.add(task)
        db.flush()
        data = _row(task)
    ok(f"Reopened task #{task_id}", json_out=json_out, data=data)


@app.command()
def edit(
    task_id: int = typer.Argument(..., help="Task ID"),
    title: str = typer.Option(None, "--title", help="New title"),
    priority: str = typer.Option(None, "--priority", "-p", help="low / med / high"),
    due: str = typer.Option(None, "--due", "-d", help="New due date"),
    project: str = typer.Option(None, "--project", "-P"),
    tag: str = typer.Option(None, "--tag", "-t"),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """✅ Edit a task."""
    if priority and priority.lower() not in PRIORITIES:
        fail(f"Priority must be one of: {', '.join(PRIORITIES)}", json_out=json_out)
    with session() as db:
        task = db.get(Task, task_id)
        if not task:
            fail(f"No task #{task_id}", json_out=json_out)
        if title is not None:
            task.title = title
        if priority is not None:
            task.priority = priority.lower()
        if due is not None:
            task.due = parse_date(due)
        if project is not None:
            task.project = project
        if tag is not None:
            task.tags = tag
        if note is not None:
            task.note = note
        db.add(task)
        db.flush()
        data = _row(task)
    ok(f"Updated task #{task_id}", json_out=json_out, data=data)


@app.command()
def show(task_id: int = typer.Argument(..., help="Task ID"), json_out: JsonOpt = False) -> None:
    """✅ Show one task in detail."""
    with session() as db:
        task = db.get(Task, task_id)
        if not task:
            fail(f"No task #{task_id}", json_out=json_out)
        data = _row(task) | {"created_at": task.created_at}
    render_record(data, json_out=json_out, title=f"✅ Task #{task_id}")


@app.command()
def rm(task_id: int = typer.Argument(..., help="Task ID"), json_out: JsonOpt = False) -> None:
    """✅ Delete a task."""
    with session() as db:
        task = db.get(Task, task_id)
        if not task:
            fail(f"No task #{task_id}", json_out=json_out)
        db.delete(task)
    ok(f"Deleted task #{task_id}", json_out=json_out, data={"deleted": task_id})


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Task stats — pending, done, overdue, oldest pending, backlog age."""
    with session() as db:
        tasks = list(db.exec(select(Task)).all())
    today = date.today()
    pending = [t for t in tasks if not t.done]
    overdue = [t for t in pending if t.due and t.due < today]
    by_priority = {p: sum(1 for t in pending if t.priority == p) for p in PRIORITIES}

    # Oldest pending — *"what's been sitting on my list longest?"*.
    # Picks by created_at; ties broken by id ascending.
    oldest = min(pending, key=lambda t: (t.created_at, t.id)) if pending else None
    most_overdue = (
        max(overdue, key=lambda t: (today - t.due).days) if overdue else None
    )
    avg_age_days = (
        round(sum((today - t.created_at.date()).days for t in pending) / len(pending), 1)
        if pending else 0.0
    )

    data = {
        "total": len(tasks),
        "pending": len(pending),
        "done": sum(1 for t in tasks if t.done),
        "overdue": len(overdue),
        "pending_by_priority": by_priority,
        "avg_backlog_age_days": avg_age_days,
        "oldest_pending": (
            {
                "id": oldest.id,
                "title": oldest.title,
                "priority": oldest.priority,
                "created_at": oldest.created_at,
                "age_days": (today - oldest.created_at.date()).days,
            }
            if oldest else None
        ),
        "most_overdue": (
            {
                "id": most_overdue.id,
                "title": most_overdue.title,
                "priority": most_overdue.priority,
                "due": most_overdue.due,
                "days_overdue": (today - most_overdue.due).days,
            }
            if most_overdue else None
        ),
    }
    render_record(data, json_out=json_out, title="📊 Todo stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `update` is the SQL-natural synonym for `edit`; both work.
app.command(name="update", help="Alias for `edit`")(edit)

# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
