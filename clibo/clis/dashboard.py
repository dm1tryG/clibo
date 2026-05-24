"""🎛️ dashboard — customizable widget dashboard.

Different from `clibo today` (which is a fixed 12-section snapshot):
this is *your* dashboard — pick any subset of the registered widgets,
order matters, save it once. Defaults to the most common widgets so
``clibo dashboard`` does something useful out of the box.
"""

from __future__ import annotations

from datetime import date

import typer
from sqlmodel import select  # noqa: F401  (widgets import models that need it)

from clibo.core.db import session
from clibo.core.output import JsonOpt, _emit_json, console, fail, ok, render_rows
from clibo.core.settings import get_setting, set_setting
from clibo.widgets import DEFAULT_WIDGETS, WIDGETS

NAME = "dashboard"
HELP = "🎛️  Customizable widget dashboard (different from `clibo today`)"
EMOJI = "🎛️"


app = typer.Typer(no_args_is_help=False, invoke_without_command=True, help=HELP)


def _active_widgets() -> list[str]:
    raw = get_setting(NAME, "widgets")
    if raw is None:
        return list(DEFAULT_WIDGETS)
    return [w for w in (s.strip() for s in raw.split(",")) if w]


def _save(widgets: list[str]) -> None:
    set_setting(NAME, "widgets", ",".join(widgets))


def _render_human(active: list[str]) -> None:
    today = date.today()
    console.print(
        f"\n🎛️  [bold]Dashboard[/bold]  ·  {today:%A %d %b %Y}   "
        f"[dim]({len(active)} widget{'s' if len(active) != 1 else ''})[/dim]\n"
    )
    if not active:
        console.print("  [dim]No widgets enabled — add one with: "
                      "clibo dashboard add tasks[/dim]\n")
        return
    rendered_any = False
    with session() as db:
        for name in active:
            entry = WIDGETS.get(name)
            if not entry:
                console.print(f"  [dim](unknown widget: {name})[/dim]")
                continue
            _, fn = entry
            block = fn(db)
            lines = block.get("lines", [])
            if not lines:
                continue
            console.print(f"[bold]{block['title']}[/bold]")
            for line in lines:
                console.print(f"  {line}")
            console.print()
            rendered_any = True
    if not rendered_any:
        console.print("  [dim]Nothing to show right now — enable more widgets or log "
                      "some data.[/dim]\n")


@app.callback()
def _root(ctx: typer.Context, json_out: JsonOpt = False) -> None:
    """🎛️ Render the dashboard (default), or run a sub-command to configure it."""
    if ctx.invoked_subcommand is not None:
        return
    active = _active_widgets()
    if json_out:
        out = {"date": date.today(), "widgets": []}
        with session() as db:
            for name in active:
                entry = WIDGETS.get(name)
                if not entry:
                    continue
                _, fn = entry
                block = fn(db)
                out["widgets"].append({
                    "name": name,
                    "title": block["title"],
                    "data": block.get("data"),
                })
        _emit_json(out)
        return
    _render_human(active)


@app.command(name="list")
def list_widgets(json_out: JsonOpt = False) -> None:
    """🎛️ List every widget — installed or available — with descriptions."""
    active = set(_active_widgets())
    rows = [
        {"name": name, "description": desc, "active": name in active}
        for name, (desc, _) in WIDGETS.items()
    ]
    render_rows(
        rows,
        [("name", "Widget"), ("active", "On"), ("description", "What it shows")],
        json_out=json_out,
        title="🎛️ Widgets",
        formatters={"active": lambda v, r: "[green]✓[/green]" if v else "[dim]·[/dim]"},
        empty="(no widgets registered)",
    )


@app.command()
def add(
    name: str = typer.Argument(..., help="Widget name (see `clibo dashboard list`)"),
    json_out: JsonOpt = False,
) -> None:
    """🎛️ Enable a widget on the dashboard."""
    name = name.lower()
    if name not in WIDGETS:
        fail(f"No widget named {name!r}. See `clibo dashboard list`.", json_out=json_out)
    active = _active_widgets()
    if name in active:
        ok(f"'{name}' is already on the dashboard", json_out=json_out,
           data={"widgets": active})
        return
    active.append(name)
    _save(active)
    ok(f"Added widget '{name}'", json_out=json_out, data={"widgets": active})


@app.command()
def remove(
    name: str = typer.Argument(..., help="Widget to remove"),
    json_out: JsonOpt = False,
) -> None:
    """🎛️ Remove a widget from the dashboard."""
    name = name.lower()
    active = _active_widgets()
    if name not in active:
        fail(f"'{name}' is not currently on the dashboard", json_out=json_out)
    active = [w for w in active if w != name]
    _save(active)
    ok(f"Removed widget '{name}'", json_out=json_out, data={"widgets": active})


@app.command()
def reset(json_out: JsonOpt = False) -> None:
    """🎛️ Reset the dashboard to the default widget set."""
    _save(list(DEFAULT_WIDGETS))
    ok(f"Reset to defaults: {', '.join(DEFAULT_WIDGETS)}",
       json_out=json_out, data={"widgets": list(DEFAULT_WIDGETS)})


@app.command()
def clear(json_out: JsonOpt = False) -> None:
    """🎛️ Remove every widget — dashboard becomes blank."""
    _save([])
    ok("Dashboard cleared — no widgets enabled.", json_out=json_out, data={"widgets": []})


# `rm` is the universal short verb across clibo; aliased to local `remove`.
app.command(name="rm", help="Alias for `remove`")(remove)
