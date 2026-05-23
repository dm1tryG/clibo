"""Rendering layer — the part that makes clibo pleasant for both audiences.

Every command accepts ``--json``. Without it, output is a polished Rich table
or panel for humans. With it, output is clean, parseable JSON on stdout for AI
agents. Tools never print directly; they hand data to the helpers here.
"""

from __future__ import annotations

import json as _json
from collections.abc import Callable
from datetime import date, datetime
from typing import Annotated, Any

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
err_console = Console(stderr=True)

#: Reusable ``--json`` option. Add ``json_out: JsonOpt = False`` to any command.
JsonOpt = Annotated[
    bool,
    typer.Option("--json", help="Output machine-readable JSON (for AI agents)."),
]


def _coerce(value: Any) -> Any:
    """JSON fallback for types ``json`` cannot serialize on its own."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    # Pydantic v2 models — use their own JSON-mode dump (handles nested
    # date/datetime fields too).
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return str(value)


def _emit_json(data: Any) -> None:
    # If the caller hands us a Pydantic model, pre-flatten it so the JSON
    # output shape is identical to what the old dict-based code produced.
    if hasattr(data, "model_dump"):
        data = data.model_dump(mode="json")
    print(_json.dumps(data, default=_coerce, ensure_ascii=False, indent=2))


def _cell(value: Any) -> str:
    """Format a single value for a human-facing table cell."""
    if value is None or value == "":
        return "[dim]—[/dim]"
    if isinstance(value, bool):
        return "[green]✓[/green]" if value else "[dim]·[/dim]"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def render_rows(
    rows: list[dict],
    columns: list,
    *,
    json_out: bool,
    title: str | None = None,
    formatters: dict[str, Callable[[Any, dict], str]] | None = None,
    empty: str = "Nothing here yet.",
) -> None:
    """Render a list of records as a JSON array or a Rich table.

    ``columns`` items are either a ``"key"`` string or a ``("key", "Header")``
    tuple. ``formatters`` maps a column key to ``fn(value, row) -> str`` for
    custom human-facing styling (ignored in JSON mode).
    """
    if json_out:
        _emit_json(rows)
        return
    if not rows:
        console.print(f"  [dim]{empty}[/dim]")
        return
    cols = [
        (c, c.replace("_", " ").title()) if isinstance(c, str) else c for c in columns
    ]
    table = Table(
        box=ROUNDED,
        header_style="bold cyan",
        title=title,
        title_style="bold magenta",
        title_justify="left",
        pad_edge=False,
        expand=False,
    )
    for _, header in cols:
        table.add_column(header)
    fmt = formatters or {}
    for row in rows:
        cells = []
        for key, _ in cols:
            value = row.get(key)
            if key in fmt:
                cells.append(str(fmt[key](value, row)))
            else:
                cells.append(_cell(value))
        table.add_row(*cells)
    console.print(table)


def render_record(
    record: dict, *, json_out: bool, title: str | None = None
) -> None:
    """Render a single record as JSON or a Rich key/value panel."""
    if json_out:
        _emit_json(record)
        return
    table = Table(box=None, show_header=False, pad_edge=False)
    table.add_column(style="bold cyan", justify="right")
    table.add_column()
    for key, value in record.items():
        table.add_row(str(key).replace("_", " ").title(), _cell(value))
    console.print(Panel(table, title=title, border_style="cyan", title_align="left"))


def ok(msg: str, *, json_out: bool, data: Any = None) -> None:
    """Report a successful mutation.

    In JSON mode emits ``data`` (e.g. the created record) or an ``ok`` envelope.
    """
    if json_out:
        _emit_json(data if data is not None else {"ok": True, "message": msg})
    else:
        console.print(f"[green]✓[/green] {msg}")


def fail(msg: str, *, json_out: bool = False, code: int = 1) -> None:
    """Report an error and exit with a non-zero status code."""
    if json_out:
        _emit_json({"ok": False, "error": msg})
    else:
        err_console.print(f"[red]✗[/red] {msg}")
    raise typer.Exit(code)


def bar(value: float, total: float, width: int = 24) -> str:
    """A compact text progress bar, e.g. ``████████░░░░  75%``."""
    if total <= 0:
        return "[dim]" + "░" * width + "[/dim]"
    ratio = max(0.0, min(1.0, value / total))
    filled = round(ratio * width)
    color = "green" if ratio >= 1 else "cyan" if ratio >= 0.5 else "yellow"
    return f"[{color}]{'█' * filled}[/{color}][dim]{'░' * (width - filled)}[/dim]  {ratio * 100:.0f}%"
