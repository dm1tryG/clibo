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
_IN_RE = re.compile(
    r"^in\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)$"
)

_WEEKDAYS = [
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
]
# Allow common 3-letter abbreviations too.
_WEEKDAY_ABBR = {
    "mon": 0, "tue": 1, "tues": 1, "wed": 2, "thu": 3, "thur": 3, "thurs": 3,
    "fri": 4, "sat": 5, "sun": 6,
}

# English month names + common abbreviations. Locale-independent on purpose —
# `strptime("%B")` is locale-sensitive and would break on non-English systems.
_MONTHS = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sept": 9, "sep": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}
_MONTH_DAY_RE = re.compile(r"^([a-z]+)\.?\s+(\d{1,2})(?:\s+(\d{4}))?$")
_DAY_MONTH_RE = re.compile(r"^(\d{1,2})\s+([a-z]+)\.?(?:\s+(\d{4}))?$")


def _weekday_index(word: str) -> int | None:
    """Return 0-6 for Monday-Sunday, or None if `word` isn't a weekday name."""
    if word in _WEEKDAYS:
        return _WEEKDAYS.index(word)
    return _WEEKDAY_ABBR.get(word)


def _weekday_to_date(target_idx: int, modifier: str | None) -> date:
    """Resolve a weekday name to a date.

    ``modifier`` is one of ``None`` / ``"this"`` / ``"next"`` / ``"last"``.
    Bare ``"monday"`` and ``"next monday"`` both mean the next coming Monday
    (today if it's already Monday → 7 days later, since "monday" alone
    naturally refers to the upcoming one). ``"this monday"`` allows today.
    """
    today = date.today()
    today_idx = today.weekday()
    if modifier == "last":
        delta = -((today_idx - target_idx) % 7)
        if delta == 0:
            delta = -7
        return today + timedelta(days=delta)
    delta = (target_idx - today_idx) % 7
    if modifier == "this":
        # "this <weekday>": today if it matches, otherwise the next occurrence.
        return today + timedelta(days=delta)
    # Bare or "next": always future, skip today.
    if delta == 0:
        delta = 7
    return today + timedelta(days=delta)


def _parse_month_name_date(text: str) -> date | None:
    """Parse ``"March 12"`` / ``"12 march 1985"`` / ``"Mar 12"`` etc.

    Returns ``None`` if the text doesn't match any month-name form.
    Year defaults to the current year when omitted.
    """
    for regex, month_first in ((_MONTH_DAY_RE, True), (_DAY_MONTH_RE, False)):
        if match := regex.match(text):
            if month_first:
                month_name, day_str, year_str = match.groups()
            else:
                day_str, month_name, year_str = match.groups()
            month_num = _MONTHS.get(month_name)
            if month_num is None:
                continue
            try:
                return date(
                    int(year_str) if year_str else date.today().year,
                    month_num,
                    int(day_str),
                )
            except ValueError:
                return None
    return None


def parse_date(value: str | None) -> date:
    """Parse a human-friendly date string into a ``date``.

    Accepts (case-insensitive):

    * ``today`` / ``yesterday`` / ``tomorrow`` / ``now``
    * ``last week`` / ``next month`` (any of day/week/month/year)
    * ``"N days ago"`` / ``"N weeks from now"`` / ``"in N days"``
    * Weekday names: ``"monday"`` (next coming Monday), ``"next tuesday"``,
      ``"this friday"``, ``"last wednesday"``. Common 3-letter forms work too
      (``mon``, ``tue``, ``wed``, ``thu``, ``fri``, ``sat``, ``sun``).
    * Month-name forms: ``"march 12"``, ``"12 March"``, ``"Mar 12 1985"``.
      Year defaults to the current year.
    * ISO ``YYYY-MM-DD`` and the short forms ``DD.MM.YYYY``, ``DD.MM``, ``MM/DD``.
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
    # Weekday alone, or with this/next/last.
    if len(parts) == 1 and (idx := _weekday_index(parts[0])) is not None:
        return _weekday_to_date(idx, modifier=None)
    if (
        len(parts) == 2
        and parts[0] in {"this", "next", "last"}
        and (idx := _weekday_index(parts[1])) is not None
    ):
        return _weekday_to_date(idx, modifier=parts[0])
    # "N days ago" / "N weeks from now"
    if match := _RELATIVE_RE.match(text):
        amount, unit, direction_str = match.groups()
        sign = -1 if direction_str == "ago" else +1
        return date.today() + timedelta(days=sign * int(amount) * _RELATIVE_UNITS[unit])
    # "in N days/weeks/months/years"
    if match := _IN_RE.match(text):
        amount, unit = match.groups()
        return date.today() + timedelta(days=int(amount) * _RELATIVE_UNITS[unit])
    # Month-name forms.
    if (md := _parse_month_name_date(text)) is not None:
        return md
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
