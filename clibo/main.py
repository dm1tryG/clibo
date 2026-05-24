"""clibo — the root command that ties all 50 tools together.

Run ``clibo`` for the menu, ``clibo <tool> --help`` for any tool, and
``clibo info`` to see the project's progress.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import typer
from rich.box import ROUNDED
from rich.panel import Panel
from rich.table import Table

from clibo import __version__, clis
from clibo.admin import backup_db, export_data, import_data, restore_db
from clibo.catalog import CATALOG, CATEGORIES
from clibo.checkins import collect_checkins
from clibo.core import config
from clibo.core.db import init_db, session
from clibo.core.output import JsonOpt, _emit_json, console, fail, ok
from clibo.core.settings import get_setting, set_setting
from clibo.dashboard import render_today
from clibo.recent import _ago, collect_recent
from clibo.search import search_all
from clibo.tags import collect_items_by_tag, collect_tags
from clibo.weekly import render_week

app = typer.Typer(
    name="clibo",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=True,
    help="📦 [bold]clibo[/bold] — 50+ local-first CLI tools for AI agents & humans.",
)

# Register every built tool as a sub-command: `clibo calorie`, `clibo crm`, ...
for module in clis.ALL:
    app.add_typer(module.app, name=module.NAME, help=module.HELP)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"clibo {__version__}")
        raise typer.Exit()


@app.callback()
def _root(
    _show_version: bool = typer.Option(
        None, "--version", "-V",
        callback=_version_callback, is_eager=True,
        help="Show the clibo version and exit.",
    ),
) -> None:
    """Ensure the local database exists before any command runs."""
    init_db()


@app.command()
def info(json_out: JsonOpt = False) -> None:
    """📦 Show every clibo tool and how many are built."""
    built = {m.NAME for m in clis.ALL}

    if json_out:
        _emit_json(
            {
                "version": __version__,
                "database": str(config.db_path()),
                "built": len(built),
                "planned": len(CATALOG),
                "tools": [
                    {
                        "name": t.name,
                        "emoji": t.emoji,
                        "category": t.category,
                        "summary": t.summary,
                        "built": t.name in built,
                    }
                    for t in CATALOG
                ],
            }
        )
        return

    console.print(
        Panel(
            f"📦 [bold]clibo[/bold] v{__version__}\n"
            f"[dim]{len(CATALOG)} local-first CLI tools for AI agents & humans"
            f"[/dim]\n\n"
            f"[bold green]{len(built)}[/bold green] / {len(CATALOG)} tools built"
            f"   ·   🗄️  [dim]{config.db_path()}[/dim]",
            border_style="cyan",
            box=ROUNDED,
        )
    )
    for category in CATEGORIES:
        table = Table(
            box=ROUNDED,
            header_style="bold cyan",
            title=category,
            title_style="bold magenta",
            title_justify="left",
            pad_edge=False,
        )
        table.add_column(" ", width=3)
        table.add_column("Tool", style="bold")
        table.add_column("What it does")
        for tool in (t for t in CATALOG if t.category == category):
            done = tool.name in built
            mark = "[green]✅[/green]" if done else "[dim]⬜[/dim]"
            name = f"{tool.emoji} {tool.name}"
            table.add_row(
                mark,
                name if done else f"[dim]{name}[/dim]",
                tool.summary if done else f"[dim]{tool.summary}[/dim]",
            )
        console.print(table)
    console.print("\n[dim]Try:[/dim] clibo <tool> --help   ·   add --json for AI agents\n")


@app.command()
def version() -> None:
    """Show the clibo version."""
    console.print(f"clibo {__version__}")


@app.command()
def today(
    on: str = typer.Option(
        None, "--on", "-d",
        help="Snapshot for this date instead of today (any parse_date form)",
    ),
    json_out: JsonOpt = False,
) -> None:
    """📅 Today across every clibo tool: tasks, habits, meals, bills…

    Pass ``--on yesterday`` (or any date string parse_date accepts) to look
    at a past day instead. ``clibo yesterday`` is a thin alias for that.
    """
    from clibo.core.base import parse_date
    target = parse_date(on) if on else None
    render_today(json_out=json_out, on=target)


@app.command()
def yesterday(json_out: JsonOpt = False) -> None:
    """📅 Shortcut for `clibo today --on yesterday`."""
    from datetime import date as _date
    from datetime import timedelta as _td
    render_today(json_out=json_out, on=_date.today() - _td(days=1))


@app.command()
def week(json_out: JsonOpt = False) -> None:
    """🗓️  The last 7 days at a glance: sleep, focus, habits, spending, productivity."""
    render_week(json_out=json_out)


@app.command()
def upcoming(
    days: int = typer.Option(
        7, "--days", "-d",
        help="Look ahead this many days (default 7)",
    ),
    json_out: JsonOpt = False,
) -> None:
    """🔮 What's coming up over the next N days.

    Pulls every date-anchored item — tasks, bills, events, follow-ups,
    birthdays, chores, packages and documents expiring — into a single
    chronological view. Sister to ``clibo today`` (today-only) and
    ``clibo week`` (retrospective).
    """
    from clibo.upcoming import render_upcoming
    if days < 1:
        from clibo.core.output import fail
        fail("--days must be >= 1", json_out=json_out)
    render_upcoming(days=days, json_out=json_out)


# ``clibo agenda`` reads more naturally for "what's on my agenda?"
# Same command under a second name.
app.command(name="agenda", help="Alias for `upcoming`")(upcoming)


@app.command()
def overdue(
    days: int = typer.Option(
        None, "--days", "-d",
        help="Only show items overdue by no more than N days "
             "(default: all overdue, regardless of age)",
    ),
    json_out: JsonOpt = False,
) -> None:
    """⚠ Everything that's already slipped, grouped by kind.

    The retrospective companion to ``clibo upcoming``: pulls every
    past-due item across tasks, bills, follow-ups, chores, document
    expiry and undelivered packages. Most-overdue first.
    """
    from clibo.overdue import render_overdue
    if days is not None and days < 0:
        from clibo.core.output import fail
        fail("--days must be >= 0", json_out=json_out)
    render_overdue(max_days=days, json_out=json_out)


from clibo.monthly import month_command  # noqa: E402

app.command(name="month")(month_command)


@app.command()
def year(
    yr: int = typer.Option(
        None, "--year", "-y",
        help="Calendar year (default: current)",
    ),
    json_out: JsonOpt = False,
) -> None:
    """📅 A calendar-year rollup across every tracker: money, productivity,
    hobbies, health, in one screen.

    Sister to ``today`` (now), ``week`` (last 7 days), ``month`` (calendar
    month). Answers *"how was 2026?"* in a single command — per-tool
    annual breakdowns live on each ``<tool> year`` command.
    """
    from clibo.yearly import render_year
    render_year(year=yr, json_out=json_out)


@app.command()
def compare(
    month_mode: bool = typer.Option(
        False, "--month",
        help="Compare this calendar month vs the previous one "
             "(default: week-over-week)",
    ),
    year: int = typer.Option(
        None, "--year", "-y",
        help="Calendar year for --month (default: current)",
    ),
    month_num: int = typer.Option(
        None, "--month-of", "-m",
        help="Calendar month 1-12 for --month (default: current)",
    ),
    json_out: JsonOpt = False,
) -> None:
    """⚖️ Week-over-week (default) or month-over-month comparison.

    Without flags, compares the current 7 days vs the 7 before. With
    ``--month``, compares the current calendar month vs the previous one
    — pass ``--year`` / ``--month-of`` to look at any past pair.
    """
    if month_mode:
        from clibo.compare import render_compare_months
        render_compare_months(json_out=json_out, year=year, month=month_num)
        return
    from clibo.compare import render_compare
    render_compare(json_out=json_out)


@app.command()
def streaks(json_out: JsonOpt = False) -> None:
    """🔥 Every active streak across the suite, in one view.

    Aggregates habits, gratitude, step-goal, fasting target-hits and
    challenges. Sorted current-desc so the longest live streak is first.
    """
    from clibo.streaks import render_streaks
    render_streaks(json_out=json_out)


@app.command()
def checkin(
    all_trackers: bool = typer.Option(
        False, "--all", "-a",
        help="Show every tracker clibo knows about, not just active ones. "
             "Useful for discovery: 'what can I log?'",
    ),
    json_out: JsonOpt = False,
) -> None:
    """📋 Pending daily check-ins across every actively-tracked tool.

    Surfaces one question per actively-used tracker (≥2 entries in the last
    14 days) that hasn't been logged today, with a copy-pasteable command
    and the last known value. `--json` outputs the same data structured —
    ideal for an AI agent to ask the user one question at a time.

    Pass ``--all`` to also list inactive trackers (under the 2-in-14d
    threshold) so you can discover what other tools are available to log.
    """
    from datetime import date as _date

    from clibo.models import CheckinSummary
    today = _date.today()
    with session() as db:
        checkins = collect_checkins(
            db, today=today, include_inactive=all_trackers,
        )
    pending = [c for c in checkins if not c.logged_today]
    done = [c for c in checkins if c.logged_today]
    summary = CheckinSummary(
        date=today,
        pending_count=len(pending),
        logged_count=len(done),
        pending=pending,
        logged=done,
    )
    if json_out:
        _emit_json(summary)
        return
    if not checkins:
        console.print(
            "\n  📋 [dim]No active trackers detected yet.[/dim]   "
            "[dim](A tracker becomes active after 2+ entries in 14 days.)[/dim]\n"
            "  [dim]Run [cyan]clibo checkin --all[/cyan] to see every "
            "tracker available to log.[/dim]\n"
        )
        return
    if not pending and not all_trackers:
        console.print(
            f"\n  📋 [green]✓ All {len(done)} daily check-ins are in for today.[/green]\n"
        )
        return
    header = (
        "📋 All trackers" if all_trackers else "📋 Today's check-ins"
    )
    console.print(
        f"\n[bold]{header}[/bold]   "
        f"[cyan]{len(done)}[/cyan] done   ·   "
        f"[yellow]{len(pending)}[/yellow] pending\n"
    )
    for ci in pending:
        console.print(f"  {ci.emoji}  [bold]{ci.name}[/bold]")
        console.print(f"      ❓ [dim]{ci.question}[/dim]")
        if ci.last_value is not None:
            ago_part = (f", {ci.last_days_ago}d ago"
                        if ci.last_days_ago else "")
            console.print(
                f"      💡 last [dim]{ci.last_value}{ago_part}[/dim]"
            )
        console.print(f"      ➤  [cyan]{ci.command}[/cyan]\n")
    # In --all mode, also show what's already logged today so the view
    # is exhaustive — answers "what's left to log?" at a glance.
    if all_trackers and done:
        console.print("[bold]✓ Already logged today[/bold]\n")
        for ci in done:
            console.print(
                f"  {ci.emoji}  [green]{ci.name}[/green]  "
                f"[dim]{ci.today_value}[/dim]"
            )
        console.print()


@app.command()
def backup(
    dest: Path = typer.Argument(None, help="Where to write the backup .db file"),
    json_out: JsonOpt = False,
) -> None:
    """💾 Copy the clibo database to a timestamped backup file."""
    try:
        path = backup_db(dest)
    except FileNotFoundError as exc:
        fail(str(exc), json_out=json_out)
    ok(f"Backed up clibo database → {path}", json_out=json_out, data={"path": str(path)})


@app.command()
def restore(
    src: Path = typer.Argument(..., help="Backup file to restore from"),
    json_out: JsonOpt = False,
) -> None:
    """💾 Replace the live clibo database with a backup file."""
    try:
        path = restore_db(src)
    except FileNotFoundError as exc:
        fail(str(exc), json_out=json_out)
    ok(f"Restored clibo database from {src} → {path}",
       json_out=json_out, data={"restored_to": str(path)})


@app.command(name="export")
def export_cmd(
    dest: Path = typer.Argument(
        None, help="JSON file (default) or CSV directory (with --csv)"
    ),
    csv: bool = typer.Option(
        False, "--csv",
        help="Write one CSV per table to a directory — easier for spreadsheets",
    ),
    json_out: JsonOpt = False,
) -> None:
    """📤 Dump every clibo table — one big JSON, or one CSV per table.

    Default writes a single JSON file (great for AI agents reading the whole
    state). `--csv` writes a directory with one CSV per table, which Excel /
    Numbers / Sheets can open directly.
    """
    try:
        if csv:
            from clibo.admin import export_csv
            path, summary = export_csv(dest)
            fmt = "csv"
        else:
            path, summary = export_data(dest)
            fmt = "json"
    except FileNotFoundError as exc:
        fail(str(exc), json_out=json_out)
    data = {
        "path": str(path),
        "format": fmt,
        "tables": summary,
        "rows": sum(summary.values()),
    }
    where = f"directory {path}" if csv else f"file {path}"
    ok(f"Exported {data['rows']} rows across {len(summary)} tables → {where}",
       json_out=json_out, data=data)


@app.command(name="import")
def import_cmd(
    src: Path = typer.Argument(..., help="JSON file produced by `clibo export`"),
    replace: bool = typer.Option(False, "--replace", help="Wipe each table before importing"),
    json_out: JsonOpt = False,
) -> None:
    """📥 Load rows from a `clibo export` JSON file."""
    try:
        summary = import_data(src, replace=replace)
    except FileNotFoundError as exc:
        fail(str(exc), json_out=json_out)
    except ValueError as exc:
        fail(str(exc), json_out=json_out)
    total = sum(summary.values())
    ok(f"Imported {total} rows across {len(summary)} tables from {src}",
       json_out=json_out, data={"source": str(src), "rows": total, "tables": summary})


def _human_size(num: int) -> str:
    """Format a byte count as a short ``42 B`` / ``3.1 KB`` / ``2.4 MB``."""
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024 or unit == "GB":
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} GB"


def _check_pypi_latest(timeout: float = 3.0) -> str | None:
    """Best-effort fetch of clibo's latest version on PyPI.

    Returns ``None`` on any failure — no network, DNS error, PyPI down,
    parse problem. Doctor never fails because of update-check.
    """
    import json as _json
    import urllib.error
    import urllib.request
    try:
        req = urllib.request.Request(
            "https://pypi.org/pypi/clibo/json",
            headers={"User-Agent": f"clibo-doctor/{__version__}"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = _json.load(resp)
        return payload.get("info", {}).get("version")
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
        return None


def _version_tuple(v: str) -> tuple[int, ...]:
    """Parse a dotted version into a comparable tuple. Non-int parts coerce to 0."""
    parts: list[int] = []
    for chunk in v.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _detect_schema_drift(db_path: Path) -> list[dict]:
    """Find model columns that aren't present in the live SQLite tables.

    Returns ``[{"table": str, "missing_columns": [str, ...]}]`` for any
    table where the live schema lags the current SQLModel definition.
    ``_add_missing_columns`` normally heals these at startup, so a hit
    here usually means a NOT-NULL-no-default column that can't be added
    safely — worth flagging to the user.
    """
    from sqlmodel import SQLModel
    drift: list[dict] = []
    if not db_path.exists():
        return drift
    with sqlite3.connect(str(db_path)) as conn:
        existing_tables = {
            name for (name,) in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        for table in SQLModel.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            live_cols = {
                row[1] for row in conn.execute(
                    f'PRAGMA table_info("{table.name}")'
                ).fetchall()
            }
            missing = [c.name for c in table.columns if c.name not in live_cols]
            if missing:
                drift.append({"table": table.name, "missing_columns": missing})
    return drift


def _unconfigured_settings() -> list[dict]:
    """List ``_INIT_SETTINGS`` entries the user hasn't filled in yet."""
    out: list[dict] = []
    for cli_key, (scope, key, _, label) in _INIT_SETTINGS.items():
        if get_setting(scope, key) is None:
            out.append({"setting": cli_key, "label": label})
    return out


@app.command()
def doctor(
    check_updates: bool = typer.Option(
        False, "--check-updates",
        help="Also query PyPI for the latest version (opt-in; needs network).",
    ),
    json_out: JsonOpt = False,
) -> None:
    """🩺 Health check — verify the install and inspect the local database.

    Reports:
      • version, Python, tool count
      • database location, size, rows-per-table
      • schema drift (model columns not yet in the DB)
      • settings you haven't configured with ``clibo init``
      • with ``--check-updates``: whether a newer clibo is on PyPI
    """
    db_path = config.db_path()
    db_exists = db_path.exists()
    db_size = db_path.stat().st_size if db_exists else 0
    rows_per_table: dict[str, int] = {}
    if db_exists:
        with sqlite3.connect(str(db_path)) as conn:
            for (name,) in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall():
                if name.startswith("sqlite_"):
                    continue
                rows_per_table[name] = conn.execute(
                    f'SELECT COUNT(*) FROM "{name}"'
                ).fetchone()[0]
    total_rows = sum(rows_per_table.values())
    schema_drift = _detect_schema_drift(db_path)
    unconfigured = _unconfigured_settings()

    latest_version: str | None = None
    update_available = False
    if check_updates:
        latest_version = _check_pypi_latest()
        if latest_version and _version_tuple(latest_version) > _version_tuple(__version__):
            update_available = True

    warnings: list[str] = []
    if not db_exists:
        warnings.append("Database file does not exist yet.")
    if len(clis.ALL) != len(CATALOG):
        warnings.append(
            f"Tool count drift: {len(clis.ALL)} built vs {len(CATALOG)} in catalog."
        )
    for entry in schema_drift:
        cols = ", ".join(entry["missing_columns"])
        warnings.append(f"Schema drift in {entry['table']}: missing {cols}.")
    if update_available:
        warnings.append(
            f"Newer clibo on PyPI: {latest_version} (you have {__version__}). "
            f"Upgrade with: pipx upgrade clibo  ·  pip install -U clibo"
        )

    healthy = not warnings

    data = {
        "version": __version__,
        "python": sys.version.split()[0],
        "tools_built": len(clis.ALL),
        "tools_planned": len(CATALOG),
        "database": str(db_path),
        "database_exists": db_exists,
        "database_size_bytes": db_size,
        "tables": len(rows_per_table),
        "total_rows": total_rows,
        "rows_per_table": rows_per_table,
        "schema_drift": schema_drift,
        "unconfigured_settings": unconfigured,
        "latest_version": latest_version,
        "update_available": update_available,
        "warnings": warnings,
        "healthy": healthy,
    }
    if json_out:
        _emit_json(data)
        return
    status = ("[bold green]✓ healthy[/bold green]" if healthy
              else "[bold yellow]⚠ check warnings below[/bold yellow]")
    version_line = f"  Version       [bold]{__version__}[/bold]"
    if update_available:
        version_line += f"   [yellow](upgrade available: {latest_version})[/yellow]"
    elif latest_version:
        version_line += "   [green](latest)[/green]"
    console.print(
        Panel(
            f"🩺 [bold]clibo doctor[/bold]   {status}\n\n"
            f"{version_line}\n"
            f"  Python        {sys.version.split()[0]}\n"
            f"  Tools built   [bold]{len(clis.ALL)}[/bold] / {len(CATALOG)}\n"
            f"  Database      [dim]{db_path}[/dim]\n"
            f"  DB size       {_human_size(db_size) if db_exists else '[red]missing[/red]'}\n"
            f"  Tables        {len(rows_per_table)}\n"
            f"  Total rows    {total_rows}",
            border_style="cyan", box=ROUNDED,
        )
    )
    if rows_per_table:
        top = sorted(rows_per_table.items(), key=lambda kv: kv[1], reverse=True)
        top = [(n, c) for n, c in top if c > 0][:8]
        if top:
            table = Table(
                box=ROUNDED, header_style="bold cyan",
                title="Tables with data", title_style="bold magenta",
                title_justify="left", pad_edge=False,
            )
            table.add_column("Table")
            table.add_column("Rows", justify="right")
            for name, count in top:
                table.add_row(name, str(count))
            console.print(table)
    if warnings:
        console.print()
        console.print("[bold yellow]⚠ Warnings[/bold yellow]")
        for msg in warnings:
            console.print(f"  • {msg}")
    if unconfigured:
        console.print()
        console.print(
            f"[dim]💡 {len(unconfigured)} setting(s) unconfigured — run "
            f"[bold]clibo init[/bold] to set them: "
            f"{', '.join(u['setting'] for u in unconfigured)}[/dim]"
        )
    console.print()


#: ``cli flag → (settings scope, settings key, validator, label)`` for ``clibo init``.
_INIT_SETTINGS = {
    "currency": ("money", "currency", lambda v: bool(v), "Currency"),
    "height_cm": ("weight", "height_cm", lambda v: v > 0, "Height cm"),
    "calorie_goal": ("calorie", "daily_kcal", lambda v: v > 0, "Calorie goal (kcal/day)"),
    "water_goal_ml": ("water", "daily_ml", lambda v: v > 0, "Water goal (ml/day)"),
    "focus_goal_min": ("focus", "daily_min", lambda v: v > 0, "Focus goal (min/day)"),
    "sleep_goal_hours": ("sleep", "goal_hours", lambda v: v > 0, "Sleep goal (hours/night)"),
    "meditate_goal_min": ("meditate", "daily_min", lambda v: v > 0, "Meditation goal (min/day)"),
}


@app.command(name="init")
def init_cmd(
    currency: str = typer.Option(None, "--currency", "-c", help="Money currency code, e.g. USD/EUR"),
    height_cm: float = typer.Option(None, "--height-cm", help="Body height in cm (enables BMI)"),
    calorie_goal: int = typer.Option(None, "--calorie-goal", help="Daily calorie target"),
    water_goal_ml: int = typer.Option(None, "--water-goal-ml", help="Daily water target (ml)"),
    focus_goal_min: int = typer.Option(None, "--focus-goal-min", help="Daily focus target (min)"),
    sleep_goal_hours: float = typer.Option(None, "--sleep-goal-hours", help="Nightly sleep target (hours)"),
    meditate_goal_min: int = typer.Option(None, "--meditate-goal-min", help="Daily meditation target (min)"),
    json_out: JsonOpt = False,
) -> None:
    """🚀 Set common goals in one command — currency, height, daily targets."""
    values = {
        "currency": currency.upper() if currency is not None else None,
        "height_cm": height_cm,
        "calorie_goal": calorie_goal,
        "water_goal_ml": water_goal_ml,
        "focus_goal_min": focus_goal_min,
        "sleep_goal_hours": sleep_goal_hours,
        "meditate_goal_min": meditate_goal_min,
    }
    updated: dict[str, object] = {}
    for flag, value in values.items():
        if value is None:
            continue
        scope, key, valid, label = _INIT_SETTINGS[flag]
        if not valid(value):
            fail(f"{label} must be positive", json_out=json_out)
        set_setting(scope, key, str(value))
        updated[flag] = value
    current = {
        flag: get_setting(scope, key)
        for flag, (scope, key, _, _) in _INIT_SETTINGS.items()
    }
    if json_out:
        _emit_json({"updated": updated, "current": current})
        return
    if updated:
        console.print(f"\n[green]✓[/green] Updated [bold]{len(updated)}[/bold] setting(s)\n")
    else:
        console.print("\n  [dim]No flags given — showing current defaults.[/dim]\n")
    table = Table(
        box=ROUNDED, header_style="bold cyan",
        title="🚀 clibo defaults", title_style="bold magenta",
        title_justify="left", pad_edge=False,
    )
    table.add_column("Setting", style="bold")
    table.add_column("Value")
    for flag, (_, _, _, label) in _INIT_SETTINGS.items():
        value = current[flag]
        cell = "[dim]—[/dim]" if value is None else str(value)
        if flag in updated:
            cell = f"[green]{cell}[/green]"
        table.add_row(label, cell)
    console.print(table)
    console.print()


@app.command()
def recent(
    limit: int = typer.Option(20, "--limit", "-n", help="How many entries to show"),
    tool: str = typer.Option(
        None, "--tool", "-t",
        help="Filter to one source (e.g. workout, expense). "
             "Answers 'when did I last do X?'",
    ),
    json_out: JsonOpt = False,
) -> None:
    """📜 A chronological feed of your most recent actions across every tool."""
    from clibo.recent import known_sources
    if tool and tool.lower() not in known_sources():
        from clibo.core.output import fail
        valid = ", ".join(known_sources())
        fail(
            f"Unknown source {tool!r}. Try one of: {valid}",
            json_out=json_out,
        )
    rows = collect_recent(limit=limit, tool=tool)
    if json_out:
        _emit_json({
            "count": len(rows),
            "tool": tool.lower() if tool else None,
            "events": [
                {**row, "ago": _ago(row["created_at"])} for row in rows
            ],
        })
        return
    if not rows:
        empty = (
            f"\n  [dim]No recent {tool} activity.[/dim]\n"
            if tool
            else "\n  [dim]Nothing logged yet — try `clibo today` to get started.[/dim]\n"
        )
        console.print(empty)
        return
    title = (
        f"📜 [bold]Recent {tool}[/bold]  [dim](last {len(rows)})[/dim]"
        if tool else
        f"📜 [bold]Recent activity[/bold]  [dim](last {len(rows)})[/dim]"
    )
    console.print(f"\n{title}\n")
    for row in rows:
        when = f"[dim]{_ago(row['created_at']):>10}[/dim]"
        console.print(
            f"  {when}  {row['emoji']} [cyan]{row['source']:<10}[/cyan] {row['summary']}"
        )
    console.print()


@app.command()
def tags(json_out: JsonOpt = False) -> None:
    """🏷️  List every tag used across clibo, with counts and sources."""
    rows = collect_tags()
    if json_out:
        _emit_json({"count": len(rows), "tags": rows})
        return
    if not rows:
        console.print(
            "\n  [dim]No tags yet — add tags with `-t/--tag` in notes, "
            "todo, bookmark, crm, network, brag, recipes or journal.[/dim]\n"
        )
        return
    table = Table(
        box=ROUNDED, header_style="bold cyan",
        title=f"🏷️  Tags  [dim]({len(rows)})[/dim]",
        title_style="bold magenta", title_justify="left", pad_edge=False,
    )
    table.add_column("Tag", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Sources")
    for row in rows:
        sources = ", ".join(
            f"{src} ({n})" for src, n in sorted(row["by_source"].items())
        )
        table.add_row(row["tag"], str(row["count"]), sources)
    console.print(table)
    console.print()


@app.command()
def tagged(
    tag: str = typer.Argument(..., help="Tag to look up (case-insensitive)"),
    json_out: JsonOpt = False,
) -> None:
    """🏷️  Show every item tagged ``TAG`` across every tool.

    The natural drill-down from ``clibo tags`` — that command tells you
    *which* tags exist; this one tells you *what* carries one. Answers
    *"show me everything tagged #urgent"* in one shot, across notes,
    todo, bookmark, crm, brag, recipes, journal, ideas, quotes,
    lessons and cv.
    """
    rows = collect_items_by_tag(tag)
    if json_out:
        _emit_json({"tag": tag.strip().lower(), "count": len(rows), "items": rows})
        return
    if not rows:
        console.print(
            f"\n  [dim]Nothing tagged [cyan]{tag}[/cyan]. "
            f"Run [cyan]clibo tags[/cyan] to see which tags exist.[/dim]\n"
        )
        return
    table = Table(
        box=ROUNDED, header_style="bold cyan",
        title=f"🏷️  Tagged [cyan]#{tag.strip().lower()}[/cyan]  "
              f"[dim]({len(rows)} items)[/dim]",
        title_style="bold magenta", title_justify="left", pad_edge=False,
    )
    table.add_column("Source", style="cyan")
    table.add_column("ID", justify="right")
    table.add_column("Label")
    for row in rows:
        table.add_row(row["source"], str(row["id"]), row["label"])
    console.print(table)
    console.print()


@app.command(name="search")
def search_cmd(
    query: str = typer.Argument(..., help="Text to search for across every tool"),
    json_out: JsonOpt = False,
) -> None:
    """🔍 Search every text-bearing clibo table at once."""
    results = search_all(query)
    if json_out:
        _emit_json({"query": query, "count": len(results), "results": results})
        return
    if not results:
        console.print(f"\n  [dim]No matches for {query!r}.[/dim]\n")
        return
    grouped: dict[str, list[dict]] = {}
    for hit in results:
        grouped.setdefault(hit["source"], []).append(hit)
    console.print(f"\n🔍 [bold]{len(results)}[/bold] matches for [cyan]{query!r}[/cyan]\n")
    for source, hits in grouped.items():
        table = Table(
            box=ROUNDED, header_style="bold cyan",
            title=f"{source}  [dim]({len(hits)})[/dim]",
            title_style="bold magenta", title_justify="left", pad_edge=False,
        )
        table.add_column("ID", width=5)
        table.add_column("Match")
        for hit in hits:
            table.add_row(str(hit["id"]), hit["snippet"] or "[dim]—[/dim]")
        console.print(table)
    console.print()


def main() -> None:
    """Console-script entry point declared in pyproject.toml."""
    app()


if __name__ == "__main__":
    main()
