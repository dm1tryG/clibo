"""Small helpers shared across CLIs: date parsing and friendly defaults."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import typer


def parse_date(value: str | None) -> date:
    """Parse a human-friendly date string into a ``date``.

    Accepts ``today``/``yesterday``/``tomorrow``, ISO ``YYYY-MM-DD``, and the
    common short forms ``DD.MM.YYYY``, ``DD.MM`` and ``MM/DD``.
    """
    if value is None or value.strip().lower() in {"today", "now"}:
        return date.today()
    text = value.strip().lower()
    if text == "yesterday":
        return date.today() - timedelta(days=1)
    if text == "tomorrow":
        return date.today() + timedelta(days=1)
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d.%m", "%m/%d"):
        try:
            parsed = datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
        if fmt in ("%d.%m", "%m/%d"):
            parsed = parsed.replace(year=date.today().year)
        return parsed
    raise typer.BadParameter(f"Unrecognized date: {value!r}")


def day_bounds(d: date) -> tuple[datetime, datetime]:
    """Return the ``[start, end)`` datetimes covering a calendar day."""
    start = datetime.combine(d, datetime.min.time())
    return start, start + timedelta(days=1)


def humanize_delta(d: date) -> str:
    """Render a date relative to today: ``today``, ``in 3d``, ``5d ago``."""
    days = (d - date.today()).days
    if days == 0:
        return "today"
    if days == 1:
        return "tomorrow"
    if days == -1:
        return "yesterday"
    return f"in {days}d" if days > 0 else f"{-days}d ago"
