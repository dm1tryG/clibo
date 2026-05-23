"""Tiny ASCII sparklines for inline trends in ``stats`` commands.

A sparkline is a one-line, no-axes mini-chart that fits inside a normal
text row. Unicode block-elements ``▁▂▃▄▅▆▇█`` give 8 brightness levels,
which is enough to show a trend at a glance.

Two flavours:

* :func:`sparkline` — a sequence of values, rendered one block per value.
* :func:`sparkline_days` — a date→value map over a contiguous range,
  with gap days rendered as ``·`` so the time progression stays honest.

Both return an empty string for empty input so callers can `if line:` cheaply.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta

_BLOCKS = "▁▂▃▄▅▆▇█"
_GAP = "·"


def _to_block(value: float, mn: float, mx: float) -> str:
    span = mx - mn
    if span <= 0:
        return _BLOCKS[3]
    idx = int((value - mn) / span * (len(_BLOCKS) - 1) + 0.5)
    return _BLOCKS[max(0, min(idx, len(_BLOCKS) - 1))]


def sparkline(values: Iterable[float | None]) -> str:
    """Render a sparkline from a flat list of values.

    ``None`` values render as ``·`` so a list with missing samples stays
    readable. The min/max are computed over the non-None values; a
    constant series renders as a flat mid-level.
    """
    items = list(values)
    present = [v for v in items if v is not None]
    if not present:
        return ""
    mn, mx = min(present), max(present)
    return "".join(_GAP if v is None else _to_block(v, mn, mx) for v in items)


def sparkline_days(
    by_date: dict[date, float], start: date, end: date
) -> str:
    """Render a sparkline over the contiguous day range ``start..end``.

    Days missing from ``by_date`` render as ``·``. Useful for daily metrics
    where a missing day is itself meaningful (no entry vs. zero entry).
    """
    if start > end or not by_date:
        return ""
    series: list[float | None] = []
    d = start
    while d <= end:
        series.append(by_date.get(d))
        d += timedelta(days=1)
    return sparkline(series)
