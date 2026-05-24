"""``clibo streaks`` — every active streak across the suite, in one view.

Streaks live in many tools (habits, gratitude, fasting, daily-step-goal,
challenges). This view aggregates them so the user can see the full
motivational picture at a glance: which streaks are alive, how long
they've been running, and which longest-ever marks are set.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlmodel import select

from clibo.clis.challenge import Challenge, ChallengeCheckin
from clibo.clis.fasting import FastSession, _duration_hours
from clibo.clis.gratitude import GratitudeEntry
from clibo.clis.habit import Habit, HabitCheck, _longest_streak, _streak
from clibo.clis.meditate import MeditationSession
from clibo.clis.mileage import MileageEntry
from clibo.clis.steps import StepEntry
from clibo.clis.steps import _streak as _steps_streak
from clibo.clis.stretches import StretchSession
from clibo.clis.workout import Workout
from clibo.core.db import session
from clibo.core.output import _emit_json, console
from clibo.core.settings import get_setting


@dataclass(frozen=True)
class StreakRow:
    """One streak row in the aggregated view."""

    source: str          # habit / gratitude / fasting / steps / challenge
    emoji: str
    name: str            # e.g. habit name, "Daily gratitude", "Step goal"
    current: int
    longest: int
    note: str | None = None    # extra context — e.g. "day 5 / 30" for a challenge


def _longest_consecutive(dates: set[date]) -> int:
    """Helper: longest run of consecutive days in a set of dates."""
    if not dates:
        return 0
    ordered = sorted(dates)
    longest = run = 1
    for i in range(1, len(ordered)):
        run = run + 1 if (ordered[i] - ordered[i - 1]).days == 1 else 1
        longest = max(longest, run)
    return longest


def collect_streaks() -> list[StreakRow]:
    """Collect every active streak from every source. Sorted current-desc."""
    rows: list[StreakRow] = []
    today = date.today()
    with session() as db:
        # 🔥 Habits — one row per active habit.
        habits = list(
            db.exec(select(Habit).where(Habit.active == True)).all()  # noqa: E712
        )
        for habit in habits:
            check_dates = {
                c.check_date for c in db.exec(
                    select(HabitCheck).where(HabitCheck.habit_id == habit.id)
                ).all()
            }
            current = _streak(check_dates)
            longest = _longest_streak(check_dates)
            if current or longest:
                rows.append(StreakRow(
                    source="habit", emoji="🔥",
                    name=habit.name,
                    current=current, longest=longest,
                    note=(f"target {habit.target_per_week}/wk"
                          if habit.target_per_week != 7 else None),
                ))

        # 🙏 Gratitude — single global streak (any entry on a day counts).
        gratitude_dates = {
            g.entry_date for g in db.exec(select(GratitudeEntry)).all()
        }
        if gratitude_dates:
            g_current = _streak(gratitude_dates)
            g_longest = _longest_consecutive(gratitude_dates)
            if g_current or g_longest:
                rows.append(StreakRow(
                    source="gratitude", emoji="🙏",
                    name="Daily gratitude",
                    current=g_current, longest=g_longest,
                ))

        # 👟 Steps — consecutive days hitting the daily goal.
        steps_goal = int(get_setting("steps", "daily_goal", "10000") or 10000)
        step_entries = list(db.exec(select(StepEntry)).all())
        if step_entries:
            totals: dict[date, int] = {}
            for s in step_entries:
                totals[s.entry_date] = totals.get(s.entry_date, 0) + s.count
            current = _steps_streak(totals, steps_goal)
            # Longest goal-hit streak in history.
            goal_days = {d for d, n in totals.items() if n >= steps_goal}
            longest = _longest_consecutive(goal_days)
            if current or longest:
                rows.append(StreakRow(
                    source="steps", emoji="👟",
                    name="Step goal",
                    current=current, longest=longest,
                    note=f"goal {steps_goal:,}/day",
                ))

        # 🏋️ Workout — consecutive days with any workout logged.
        workout_dates = {
            w.entry_date for w in db.exec(select(Workout)).all()
        }
        if workout_dates:
            w_current = _streak(workout_dates)
            w_longest = _longest_consecutive(workout_dates)
            if w_current or w_longest:
                rows.append(StreakRow(
                    source="workout", emoji="🏋️",
                    name="Workout days",
                    current=w_current, longest=w_longest,
                ))

        # 🏃 Mileage — consecutive days with any distance entry.
        mileage_dates = {
            m.entry_date for m in db.exec(select(MileageEntry)).all()
        }
        if mileage_dates:
            m_current = _streak(mileage_dates)
            m_longest = _longest_consecutive(mileage_dates)
            if m_current or m_longest:
                rows.append(StreakRow(
                    source="mileage", emoji="🏃",
                    name="Mileage days",
                    current=m_current, longest=m_longest,
                ))

        # 🧘 Meditate — consecutive days with any meditation session.
        meditate_dates = {
            e.entry_date for e in db.exec(select(MeditationSession)).all()
        }
        if meditate_dates:
            me_current = _streak(meditate_dates)
            me_longest = _longest_consecutive(meditate_dates)
            if me_current or me_longest:
                rows.append(StreakRow(
                    source="meditate", emoji="🧘",
                    name="Meditation",
                    current=me_current, longest=me_longest,
                ))

        # 🧎 Stretches — consecutive days with any stretching session.
        stretch_dates = {
            e.entry_date for e in db.exec(select(StretchSession)).all()
        }
        if stretch_dates:
            s_current = _streak(stretch_dates)
            s_longest = _longest_consecutive(stretch_dates)
            if s_current or s_longest:
                rows.append(StreakRow(
                    source="stretches", emoji="🧎",
                    name="Stretching",
                    current=s_current, longest=s_longest,
                ))

        # 🕒 Fasting — consecutive completed fasts (each ≥ target) by start date.
        fasts = list(
            db.exec(
                select(FastSession).where(FastSession.end_time.is_not(None))
                .order_by(FastSession.start_time)
            ).all()
        )
        if fasts:
            hit_dates = {
                f.start_time.date()
                for f in fasts if _duration_hours(f) >= f.target_hours
            }
            f_current: int = 0
            cursor = today
            while cursor in hit_dates:
                f_current += 1
                cursor -= timedelta(days=1)
            f_longest = _longest_consecutive(hit_dates)
            if f_current or f_longest:
                rows.append(StreakRow(
                    source="fasting", emoji="🕒",
                    name="Fasting target-hit",
                    current=f_current, longest=f_longest,
                ))

        # 🚀 Challenges — per active challenge, count consecutive check-ins
        # ending today (no misses) as the current streak. Longest is the
        # longest consecutive-success run in the challenge's history.
        active = list(
            db.exec(select(Challenge).where(Challenge.status == "active")).all()
        )
        for ch in active:
            check_dates = {
                c.check_date for c in db.exec(
                    select(ChallengeCheckin)
                    .where(ChallengeCheckin.challenge_id == ch.id)
                    .where(ChallengeCheckin.success == True)  # noqa: E712
                ).all()
            }
            current = _streak(check_dates)
            longest = _longest_consecutive(check_dates)
            if current or longest:
                day_n = (today - ch.start_date).days + 1
                rows.append(StreakRow(
                    source="challenge", emoji="🚀",
                    name=ch.name,
                    current=current, longest=longest,
                    note=f"day {day_n}/{ch.target_days}",
                ))

    rows.sort(key=lambda r: (-r.current, -r.longest))
    return rows


def render_streaks(json_out: bool) -> None:
    """Render the global streaks view to stdout."""
    rows = collect_streaks()
    if json_out:
        _emit_json({
            "count": len(rows),
            "streaks": [
                {
                    "source": r.source, "emoji": r.emoji, "name": r.name,
                    "current": r.current, "longest": r.longest, "note": r.note,
                }
                for r in rows
            ],
        })
        return
    if not rows:
        console.print(
            "\n🔥 [dim]No streaks yet — start a habit, log gratitude, hit your "
            "step goal, complete a fast, or check in on a challenge.[/dim]\n"
        )
        return
    console.print(f"\n🔥 [bold]Streaks[/bold]   "
                   f"[dim]{len(rows)} active[/dim]\n")
    for r in rows:
        cur = (f"[bold red]{r.current}[/bold red]" if r.current >= 7
               else f"[bold]{r.current}[/bold]" if r.current > 0
               else "[dim]0[/dim]")
        best = (f"  [dim]best {r.longest}[/dim]" if r.longest > r.current
                else "  [dim]·[/dim]")
        note = f"   [dim]({r.note})[/dim]" if r.note else ""
        console.print(
            f"  {r.emoji}  {r.name:<26} {cur:>3} {best}{note}"
        )
    console.print()
