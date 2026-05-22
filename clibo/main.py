"""clibo — the root command that ties all 50 tools together.

Run ``clibo`` for the menu, ``clibo <tool> --help`` for any tool, and
``clibo info`` to see the project's progress.
"""

from __future__ import annotations

import typer
from rich.box import ROUNDED
from rich.panel import Panel
from rich.table import Table

from clibo import __version__, clis
from clibo.catalog import CATALOG, CATEGORIES
from clibo.core import config
from clibo.core.db import init_db
from clibo.core.output import JsonOpt, _emit_json, console

app = typer.Typer(
    name="clibo",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=True,
    help="📦 [bold]clibo[/bold] — 50 local-first CLI tools for AI agents & humans.",
)

# Register every built tool as a sub-command: `clibo calorie`, `clibo crm`, ...
for module in clis.ALL:
    app.add_typer(module.app, name=module.NAME, help=module.HELP)


@app.callback()
def _root() -> None:
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
            f"[dim]50 local-first CLI tools for AI agents & humans[/dim]\n\n"
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


def main() -> None:
    """Console-script entry point declared in pyproject.toml."""
    app()


if __name__ == "__main__":
    main()
