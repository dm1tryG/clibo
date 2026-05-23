"""Small helpers shared across CLIs: date parsing and friendly defaults."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

import typer

_RELATIVE_UNITS = {
    "day": 1, "days": 1,
    "week": 7, "weeks": 7,
    "month": 30, "months": 30,   # approximate, but useful
    "year": 365, "years": 365,
}
_RELATIVE_RE = re.compile(
    r"^(\d+)\s+(day|days|week|weeks|month|months|year|years)\s+(ago|from\s+now)$"
)


def parse_date(value: str | None) -> date:
    """Parse a human-friendly date string into a ``date``.

    Accepts ``today``/``yesterday``/``tomorrow``, ``last week`` / ``next month``,
    ``"N days ago"`` / ``"N weeks from now"`` (also ``days``/``weeks``/``months``/
    ``years``), ISO ``YYYY-MM-DD``, and the common short forms ``DD.MM.YYYY``,
    ``DD.MM`` and ``MM/DD``.
    """
    if value is None or value.strip().lower() in {"today", "now"}:
        return date.today()
    text = value.strip().lower()
    if text == "yesterday":
        return date.today() - timedelta(days=1)
    if text == "tomorrow":
        return date.today() + timedelta(days=1)
    # last week / next month / etc.
    direction = {"last": -1, "next": +1}
    parts = text.split()
    if len(parts) == 2 and parts[0] in direction and parts[1] in _RELATIVE_UNITS:
        return date.today() + timedelta(
            days=direction[parts[0]] * _RELATIVE_UNITS[parts[1]]
        )
    # "N days ago" / "N weeks from now"
    if match := _RELATIVE_RE.match(text):
        amount, unit, direction_str = match.groups()
        sign = -1 if direction_str == "ago" else +1
        return date.today() + timedelta(days=sign * int(amount) * _RELATIVE_UNITS[unit])
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
