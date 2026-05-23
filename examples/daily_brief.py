#!/usr/bin/env python3
"""A small daily brief built on top of `clibo today` and `clibo week`.

The point isn't the formatting — it's the pattern: ``clibo <cmd> --json`` is
the contract, so any Python (or Node, or shell) program can build on it
without learning clibo's internals.

Run:  python examples/daily_brief.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date


def clibo(*args: str) -> dict:
    """Call ``clibo <args> --json`` and return the parsed result.

    Errors from the CLI surface as a CalledProcessError because we pass
    ``check=True``; the stderr message ends up on this script's stderr.
    """
    result = subprocess.run(
        ["clibo", *args, "--json"],
        capture_output=True,
        check=True,
        text=True,
    )
    return json.loads(result.stdout)


def render_brief() -> str:
    today = clibo("today")
    week = clibo("week")

    lines: list[str] = []
    lines.append(f"# 📅 Daily brief · {today['date']}\n")

    # Tasks
    overdue = today["tasks"]["overdue"]
    due_today = today["tasks"]["due_today"]
    if overdue or due_today:
        lines.append("## ✅ Tasks")
        for task in overdue:
            lines.append(f"- ⚠ **overdue** — {task['title']} _({task['priority']})_")
        for task in due_today:
            lines.append(f"- 🟡 due today — {task['title']} _({task['priority']})_")
        lines.append("")

    # Habits
    if today["habits"]["total"]:
        h = today["habits"]
        lines.append(f"## 🔥 Habits  {h['done_today']} / {h['total']} done")
        for item in h["items"]:
            mark = "✅" if item["done"] else "⬜"
            lines.append(f"- {mark} {item['name']}")
        lines.append("")

    # Daily metrics — only show what has a goal set
    metrics: list[str] = []
    if today["water"]["goal_ml"]:
        w = today["water"]
        pct = round(w["total_ml"] / w["goal_ml"] * 100)
        metrics.append(f"- 💧 Water: {w['total_ml']} / {w['goal_ml']} ml ({pct}%)")
    if today["calories"]["goal_kcal"]:
        c = today["calories"]
        pct = round(c["total_kcal"] / c["goal_kcal"] * 100)
        metrics.append(f"- 🍎 Calories: {c['total_kcal']} / {c['goal_kcal']} kcal ({pct}%)")
    if today["focus"]["goal_minutes"]:
        f = today["focus"]
        pct = round(f["total_minutes"] / f["goal_minutes"] * 100)
        metrics.append(f"- 🍅 Focus: {f['total_minutes']} / {f['goal_minutes']} min ({pct}%)")
    if metrics:
        lines.append("## 📊 Today")
        lines.extend(metrics)
        lines.append("")

    # Weekly trend
    s = week["sleep"]
    if s["nights_logged"]:
        lines.append(
            f"## 🗓️ This week ({week['start']} → {week['end']})\n"
            f"- 😴 Sleep: **{s['avg_hours']}h** avg over {s['nights_logged']} nights\n"
            f"- 🍅 Focus: **{week['focus']['total_minutes']} min** total across "
            f"{week['focus']['sessions']} sessions\n"
            f"- 💸 Spent: **{week['expenses']['total']} {week['expenses']['currency']}**"
        )

    if not lines or lines[-1] == "":
        return "_Nothing to brief today — enjoy the quiet._\n"
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    try:
        print(render_brief(), end="")
    except subprocess.CalledProcessError as exc:
        print(f"clibo failed: {exc.stderr.strip()}", file=sys.stderr)
        sys.exit(exc.returncode)
