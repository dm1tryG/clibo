"""``clibo recent`` — a chronological activity feed across every tool.

Where ``today`` groups by category and ``week`` aggregates, this just shows
what you've actually done lately, newest first. Reads every table that has
a ``created_at`` column with plain SQLite — no SQLModel imports, so the
feed survives any schema tweak as long as ``id`` and ``created_at`` still
exist.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Callable

from clibo.core import config
from clibo.core.db import init_db

#: Tables whose timestamp column isn't ``created_at`` (overrides for ``recent``).
TIME_COLUMN_OVERRIDES = {"habit_check": "check_date"}


#: ``(label, emoji, table, columns to fetch, format(row) -> str)`` for every
#: activity stream. ``id`` and the table's timestamp column are always pulled.
SOURCES: list[tuple[str, str, str, list[str], Callable[[sqlite3.Row], str]]] = [
    ("calorie", "🍎", "calorie_entry", ["food", "kcal"],
     lambda r: f"{r['food']} ({r['kcal']} kcal)"),
    ("water", "💧", "water_log", ["amount_ml"],
     lambda r: f"drank {r['amount_ml']} ml"),
    ("weight", "⚖️", "weight_log", ["weight_kg"],
     lambda r: f"weighed {r['weight_kg']:g} kg"),
    ("workout", "🏋️", "workout_entry", ["exercise", "sets", "reps", "weight_kg", "duration_min"],
     lambda r: (
         f"{r['exercise']} — "
         + (f"{r['sets']}×{r['reps']} @ {r['weight_kg']:g}kg"
            if r["sets"] else f"{r['duration_min']} min")
     )),
    ("sleep", "😴", "sleep_log", ["hours", "quality"],
     lambda r: f"slept {r['hours']:g}h (quality {r['quality']}/5)"),
    ("mood", "🙂", "mood_log", ["score", "emotion"],
     lambda r: f"mood {r['score']}/5"
                + (f" ({r['emotion']})" if r["emotion"] else "")),
    ("meds", "💊", "meds_dose", ["med_id"],
     lambda r: f"took medication #{r['med_id']}"),
    ("meditate", "🧘", "meditate_session", ["minutes", "kind"],
     lambda r: f"{r['minutes']} min {r['kind']}"),
    ("vitals", "❤️", "vitals_reading", ["kind", "value", "value2", "unit"],
     lambda r: (
         f"{r['kind']} {r['value']:g}"
         + (f"/{r['value2']:g}" if r["value2"] is not None else "")
         + f" {r['unit']}"
     )),
    ("expense", "💸", "expense_entry", ["description", "amount", "category"],
     lambda r: f"spent {r['amount']:g} on {r['description']} ({r['category']})"),
    ("bills", "🧾", "bills_bill", ["name", "amount", "paid"],
     lambda r: ("paid " if r["paid"] else "added bill ") + r["name"]),
    ("savings", "🐷", "savings_deposit", ["amount", "goal_id"],
     lambda r: f"deposited {r['amount']:g} to goal #{r['goal_id']}"),
    ("debt", "📉", "debt_payment", ["amount", "debt_id"],
     lambda r: f"paid {r['amount']:g} on debt #{r['debt_id']}"),
    ("invoice", "📄", "invoice_invoice", ["number", "client", "amount"],
     lambda r: f"created {r['number']} for {r['client']}"),
    ("todo", "✅", "todo_task", ["title", "done"],
     lambda r: ("completed " if r["done"] else "added task ") + r["title"]),
    ("notes", "📝", "notes_note", ["title"],
     lambda r: f"noted: {r['title']}"),
    ("habit", "🔥", "habit_check", ["habit_id"],
     lambda r: f"checked habit #{r['habit_id']}"),
    ("focus", "🍅", "focus_session", ["minutes", "task"],
     lambda r: f"focused {r['minutes']} min"
                + (f" on {r['task']}" if r["task"] else "")),
    ("time", "⏱️", "time_entry", ["minutes", "project"],
     lambda r: f"logged {r['minutes']} min on {r['project']}"),
    ("journal", "📔", "journal_entry", ["body"],
     lambda r: " ".join((r["body"] or "").split())[:60]),
    ("goals", "🎯", "goals_goal", ["name"],
     lambda r: f"set goal: {r['name']}"),
    ("events", "📅", "events_event", ["title", "event_date"],
     lambda r: f"scheduled '{r['title']}' for {r['event_date']}"),
    ("worklog", "🗒️", "worklog_entry", ["summary", "kind"],
     lambda r: f"[{r['kind']}] {r['summary']}"),
    ("bookmark", "🔖", "bookmark_bookmark", ["title", "url"],
     lambda r: f"saved {r['title'] or r['url']}"),
    ("crm", "👥", "crm_contact", ["name"],
     lambda r: f"added contact: {r['name']}"),
    ("leads", "🧲", "leads_lead", ["name", "stage"],
     lambda r: f"deal '{r['name']}' → {r['stage']}"),
    ("followup", "🔔", "followup_followup", ["person"],
     lambda r: f"follow up with {r['person']}"),
    ("meetings", "🗓️", "meetings_meeting", ["title"],
     lambda r: f"meeting: {r['title']}"),
    ("jobs", "💼", "jobs_application", ["company", "role"],
     lambda r: f"applied to {r['role']} @ {r['company']}"),
    ("clients", "🧑‍💼", "clients_hours", ["client_id", "hours"],
     lambda r: f"{r['hours']:g}h for client #{r['client_id']}"),
    ("birthdays", "🎂", "birthdays_occasion", ["person", "kind"],
     lambda r: f"saved {r['kind']}: {r['person']}"),
    ("network", "🌐", "network_connection", ["name", "met_where"],
     lambda r: f"met {r['name']}"
                + (f" @ {r['met_where']}" if r["met_where"] else "")),
    ("gifts", "🎁", "gifts_gift", ["recipient", "idea", "status"],
     lambda r: f"gift for {r['recipient']}: {r['idea']} ({r['status']})"),
    ("brag", "🏆", "brag_achievement", ["title"],
     lambda r: f"win: {r['title']}"),
    ("groceries", "🛒", "groceries_item", ["name", "bought"],
     lambda r: ("bought " if r["bought"] else "added ") + r["name"]),
    ("pantry", "🥫", "pantry_item", ["name", "location"],
     lambda r: f"pantry: {r['name']}"
                + (f" ({r['location']})" if r["location"] else "")),
    ("recipes", "👨‍🍳", "recipes_recipe", ["name"],
     lambda r: f"recipe: {r['name']}"),
    ("meals", "🍽️", "meals_plan", ["meal_type", "dish", "plan_date"],
     lambda r: f"planned {r['meal_type']} on {r['plan_date']}: {r['dish']}"),
    ("chores", "🧹", "chores_chore", ["name"],
     lambda r: f"chore: {r['name']}"),
    ("plants", "🪴", "plants_plant", ["name"],
     lambda r: f"plant: {r['name']}"),
    ("car", "🚗", "car_entry", ["kind", "service", "volume"],
     lambda r: (
         f"car {r['kind']}"
         + (f" — {r['service']}" if r["service"] else "")
         + (f" — {r['volume']:g}L" if r["volume"] else "")
     )),
    ("home", "🏠", "home_entry", ["title", "kind"],
     lambda r: f"home {r['kind']}: {r['title']}"),
    ("pets", "🐾", "pets_event", ["kind", "summary"],
     lambda r: f"pet {r['kind']}: {r['summary']}"),
    ("travel", "✈️", "travel_trip", ["name", "destination"],
     lambda r: f"trip: {r['name']}"
                + (f" → {r['destination']}" if r["destination"] else "")),
]


def _ago(when: datetime) -> str:
    """A short, relative-time label: ``2h ago`` / ``3d ago`` / ``yesterday``."""
    now = datetime.now()
    delta = now - when
    seconds = int(delta.total_seconds())
    if seconds < 0:
        return when.strftime("%Y-%m-%d %H:%M")
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    days = seconds // 86400
    if days == 1:
        return "yesterday"
    return f"{days}d ago"


def collect_recent(limit: int = 20) -> list[dict]:
    """Pull the most-recent ``limit`` events across all activity sources."""
    init_db()
    db_path = config.db_path()
    out: list[dict] = []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        for source, emoji, table, cols, fmt in SOURCES:
            table_exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            if not table_exists:
                continue
            schema = {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}
            time_col = TIME_COLUMN_OVERRIDES.get(table, "created_at")
            if time_col not in schema:
                continue
            available = [c for c in cols if c in schema]
            select_cols = ", ".join(
                f'"{c}"' for c in (["id", time_col] + available)
            )
            rows = conn.execute(
                f'SELECT {select_cols} FROM "{table}" '
                f'ORDER BY "{time_col}" DESC LIMIT ?',
                (limit,),
            ).fetchall()
            for row in rows:
                try:
                    when = datetime.fromisoformat(row[time_col])
                except (TypeError, ValueError):
                    continue
                try:
                    summary = fmt(row)
                except (KeyError, TypeError):
                    continue
                out.append({
                    "source": source,
                    "emoji": emoji,
                    "id": row["id"],
                    "created_at": when,
                    "summary": summary,
                })
    finally:
        conn.close()
    out.sort(key=lambda r: r["created_at"], reverse=True)
    return out[:limit]
