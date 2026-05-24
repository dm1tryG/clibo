"""💼 jobs — job application tracker."""

from __future__ import annotations

from datetime import date, datetime

import typer
from sqlmodel import Field, SQLModel, select

from clibo.core.base import parse_date
from clibo.core.db import session
from clibo.core.output import JsonOpt, fail, ok, render_record, render_rows

NAME = "jobs"
HELP = "💼 Job application tracker"
EMOJI = "💼"
STATUSES = ["wishlist", "applied", "interviewing", "offer", "rejected", "accepted"]


class JobApplication(SQLModel, table=True):
    """A job application moving through the hiring process."""

    __tablename__ = "jobs_application"

    id: int | None = Field(default=None, primary_key=True)
    company: str
    role: str
    status: str = "applied"
    applied_date: date = Field(default_factory=date.today)
    salary: str | None = None
    location: str | None = None
    url: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


app = typer.Typer(no_args_is_help=False, help=HELP, invoke_without_command=True)


@app.callback()
def _default(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """Default: ``clibo jobs`` (bare) runs the ``pipeline`` summary."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(pipeline, json_out=json_out)


def _resolve(db, ident: str) -> JobApplication | None:
    """Look up an application by numeric ID or by company (case-insensitive)."""
    if ident.isdigit():
        job = db.get(JobApplication, int(ident))
        if job:
            return job
    return db.exec(
        select(JobApplication).where(JobApplication.company.ilike(f"%{ident}%"))
    ).first()


def _row(job: JobApplication) -> dict:
    return {
        "id": job.id,
        "company": job.company,
        "role": job.role,
        "status": job.status,
        "applied_date": job.applied_date,
        "salary": job.salary,
        "location": job.location,
        "url": job.url,
        "notes": job.notes,
    }


def _status_cell(status: str) -> str:
    return {
        "wishlist": "[dim]wishlist[/dim]",
        "applied": "[cyan]applied[/cyan]",
        "interviewing": "[yellow]interviewing[/yellow]",
        "offer": "[bold green]offer[/bold green]",
        "rejected": "[red]rejected[/red]",
        "accepted": "[bold green]✓ accepted[/bold green]",
    }.get(status, status)


@app.command()
def add(
    company: str = typer.Argument(..., help="Company name"),
    role: str = typer.Argument(..., help="Job title"),
    status: str = typer.Option("applied", "--status", "-s", help="Application status"),
    salary: str = typer.Option(None, "--salary", help="Salary or range"),
    location: str = typer.Option(None, "--location", "-l", help="Location"),
    url: str = typer.Option(None, "--url", "-u", help="Job posting URL"),
    applied: str = typer.Option("today", "--applied", help="Date applied"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    json_out: JsonOpt = False,
) -> None:
    """💼 Track a new job application."""
    status = status.lower()
    if status not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    job = JobApplication(
        company=company, role=role, status=status, salary=salary,
        location=location, url=url, applied_date=parse_date(applied), notes=note,
    )
    with session() as db:
        db.add(job)
        db.flush()
        db.refresh(job)
        data = _row(job)
    ok(f"Added {EMOJI} {role} @ {company} ({status})", json_out=json_out, data=data)


@app.command(name="list")
def list_jobs(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    json_out: JsonOpt = False,
) -> None:
    """💼 List job applications."""
    if status and status.lower() not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    with session() as db:
        query = select(JobApplication)
        if status:
            query = query.where(JobApplication.status == status.lower())
        jobs = list(db.exec(query.order_by(JobApplication.applied_date.desc())).all())
    render_rows(
        [_row(j) for j in jobs],
        [("id", "ID"), ("company", "Company"), ("role", "Role"),
         ("status", "Status"), ("applied_date", "Applied"), ("location", "Location")],
        json_out=json_out,
        title="💼 Job applications",
        formatters={"status": lambda v, r: _status_cell(v)},
        empty="No applications yet — try: clibo jobs add 'Acme' 'Engineer'",
    )


@app.command()
def show(
    job: str = typer.Argument(..., help="Application ID or company name"),
    json_out: JsonOpt = False,
) -> None:
    """💼 Show one job application. Accepts a numeric ID or a company name."""
    with session() as db:
        target = _resolve(db, job)
        if not target:
            fail(f"No application matching {job!r}", json_out=json_out)
        data = _row(target) | {"created_at": target.created_at}
    render_record(data, json_out=json_out,
                  title=f"💼 {data['role']} @ {data['company']}")


@app.command()
def move(
    job: str = typer.Argument(..., help="Application ID or company name"),
    status: str = typer.Argument(..., help=f"New status: {', '.join(STATUSES)}"),
    json_out: JsonOpt = False,
) -> None:
    """💼 Update an application's status."""
    status = status.lower()
    if status not in STATUSES:
        fail(f"Status must be one of: {', '.join(STATUSES)}", json_out=json_out)
    with session() as db:
        target = _resolve(db, job)
        if not target:
            fail(f"No application matching {job!r}", json_out=json_out)
        target.status = status
        db.add(target)
        db.flush()
        data = _row(target)
    flair = " 🎉" if status in ("offer", "accepted") else ""
    ok(f"Moved {target.role} @ {target.company} to {status}{flair}",
       json_out=json_out, data=data)


@app.command()
def edit(
    job: str = typer.Argument(..., help="Application ID or company name"),
    role: str = typer.Option(None, "--role", help="New role"),
    salary: str = typer.Option(None, "--salary", help="New salary"),
    location: str = typer.Option(None, "--location", "-l"),
    url: str = typer.Option(None, "--url", "-u"),
    note: str = typer.Option(None, "--note", "-n"),
    json_out: JsonOpt = False,
) -> None:
    """💼 Edit a job application."""
    with session() as db:
        target = _resolve(db, job)
        if not target:
            fail(f"No application matching {job!r}", json_out=json_out)
        for field, value in {"role": role, "salary": salary, "location": location,
                             "url": url, "notes": note}.items():
            if value is not None:
                setattr(target, field, value)
        db.add(target)
        db.flush()
        data = _row(target)
    ok(f"Updated application #{target.id}", json_out=json_out, data=data)


@app.command()
def rm(
    job: str = typer.Argument(..., help="Application ID or company name"),
    json_out: JsonOpt = False,
) -> None:
    """💼 Delete a job application."""
    with session() as db:
        target = _resolve(db, job)
        if not target:
            fail(f"No application matching {job!r}", json_out=json_out)
        jid = target.id
        db.delete(target)
    ok(f"Deleted application #{jid}", json_out=json_out, data={"deleted": jid})


@app.command()
def pipeline(json_out: JsonOpt = False) -> None:
    """📊 Application counts by status."""
    with session() as db:
        jobs = list(db.exec(select(JobApplication)).all())
    by_status = {s: sum(1 for j in jobs if j.status == s) for s in STATUSES}
    if json_out:
        render_record({"by_status": by_status, "total": len(jobs)}, json_out=True)
        return
    render_rows(
        [{"status": s, "count": by_status[s]} for s in STATUSES],
        [("status", "Status"), ("count", "Applications")],
        json_out=False,
        title="📊 Application pipeline",
        formatters={"status": lambda v, r: _status_cell(v)},
        empty="No applications yet.",
    )


@app.command()
def stats(json_out: JsonOpt = False) -> None:
    """📊 Job-search stats."""
    with session() as db:
        jobs = list(db.exec(select(JobApplication)).all())
    active = [j for j in jobs if j.status in ("applied", "interviewing", "offer")]
    positive = [j for j in jobs if j.status in ("offer", "accepted", "interviewing")]
    data = {
        "total": len(jobs),
        "active": len(active),
        "interviewing": sum(1 for j in jobs if j.status == "interviewing"),
        "offers": sum(1 for j in jobs if j.status in ("offer", "accepted")),
        "response_rate_pct": round(len(positive) / len(jobs) * 100, 1) if jobs else 0.0,
    }
    render_record(data, json_out=json_out, title="📊 Job-search stats")

# `delete` is an English-natural synonym for `rm`; both work.
app.command(name="delete", help="Alias for `rm`")(rm)


# `update` is the SQL-natural synonym for `edit`; both work.
app.command(name="update", help="Alias for `edit`")(edit)

# `remove` is the English-long-form synonym for `rm`/`delete`; all three work.
app.command(name="remove", help="Alias for `rm`")(rm)
