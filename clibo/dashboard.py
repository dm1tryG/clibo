"""``clibo today`` — a one-screen dashboard pulling from every tool.

This is the integrating view that makes 50 separate trackers feel like one
app: tasks due, habits to keep, today's meals and events, bills coming up,
people to follow up with, plants needing water, calories logged, and so on.

It only imports models from other CLI modules (never their Typer apps), so
it stays a pure read-only consumer of each tool's data.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlmodel import select

from clibo.checkins import collect_checkins
from clibo.clis.bills import Bill
from clibo.clis.birthdays import Occasion
from clibo.clis.books import Book, BookSession
from clibo.clis.caffeine import (
    CaffeineEntry,
    _bedtime,
    _residual_at,
)
from clibo.clis.calorie import CalorieEntry
from clibo.clis.challenge import (
    Challenge,
    ChallengeCheckin,
    _auto_finalize,
    _checkins,
    _end_date,
)
from clibo.clis.chores import Chore
from clibo.clis.documents import Document
from clibo.clis.events import Event
from clibo.clis.fasting import FastSession, _duration_hours
from clibo.clis.focus import FocusSession
from clibo.clis.followup import FollowUp
from clibo.clis.habit import Habit, HabitCheck
from clibo.clis.meals import MealPlan
from clibo.clis.mood import MoodLog
from clibo.clis.packages import Package
from clibo.clis.plants import Plant
from clibo.clis.steps import StepEntry
from clibo.clis.symptom import Symptom
from clibo.clis.todo import Task
from clibo.clis.water import WaterLog
from clibo.clis.workout import Workout
from clibo.clis.writing import WritingSession
from clibo.core.db import session
from clibo.core.output import _emit_json, bar, console
from clibo.core.settings import get_setting
from clibo.models import (
    BillDue,
    BirthdayToday,
    BooksToday,
    CaffeineToday,
    ChallengePending,
    DocumentExpiring,
    EventToday,
    FastingProgress,
    FollowupDue,
    GoalProgress,
    HabitItem,
    HabitsBlock,
    LatePackage,
    MealToday,
    MoodToday,
    NamedItem,
    PackagesBlock,
    SymptomToday,
    TasksBlock,
    TaskSummary,
    TodaySnapshot,
    WorkoutsToday,
    WritingToday,
)


def _streak_from_days(days: set[date], today: date) -> int:
    """Consecutive-day streak ending at ``today`` (or yesterday if today empty)."""
    if not days:
        return 0
    cursor = today
    if cursor not in days:
        cursor -= timedelta(days=1)
    if cursor not in days:
        return 0
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def collect_today(on: date | None = None) -> TodaySnapshot:
    """Gather a snapshot of everything actionable on ``on`` (default: today).

    Passing a past date renders a retrospective day-view — useful for
    "how did yesterday go?" or auditing a past day from JSON via an agent.
    Forward-looking data (pending tasks, late packages, expiring documents,
    upcoming bills) is always relative to the requested date.
    """
    today = on or date.today()
    soon = today + timedelta(days=2)
    week = today + timedelta(days=7)
    with session() as db:
        # 📋 Tasks
        tasks = list(db.exec(select(Task).where(Task.done == False)).all())  # noqa: E712
        overdue = [t for t in tasks if t.due and t.due < today]
        due_today = [t for t in tasks if t.due == today]
        # Tasks completed on the snapshot's date — answers "what did I
        # get done?". Especially valuable for `clibo yesterday`.
        done_today_tasks = list(
            db.exec(
                select(Task)
                .where(Task.done == True)  # noqa: E712
                .where(Task.done_at == today)
                .order_by(Task.id.desc())
            ).all()
        )
        # 🔥 Habits
        habits = list(
            db.exec(select(Habit).where(Habit.active == True)).all()  # noqa: E712
        )
        checked = {
            c.habit_id
            for c in db.exec(select(HabitCheck).where(HabitCheck.check_date == today)).all()
        }
        # 💧 Water
        water_total = sum(
            w.amount_ml
            for w in db.exec(select(WaterLog).where(WaterLog.entry_date == today)).all()
        )
        water_goal = int(get_setting("water", "daily_ml", "2000") or 2000)
        # 🍎 Calories
        kcal_total = sum(
            c.kcal
            for c in db.exec(select(CalorieEntry).where(CalorieEntry.entry_date == today)).all()
        )
        kcal_goal = int(get_setting("calorie", "daily_kcal", "0") or 0)
        # 🍅 Focus
        focus_total = sum(
            f.minutes
            for f in db.exec(
                select(FocusSession).where(FocusSession.entry_date == today)
            ).all()
        )
        focus_goal = int(get_setting("focus", "daily_min", "100") or 100)
        # 📅 Events today
        events = list(db.exec(select(Event).where(Event.event_date == today)).all())
        # 🍽️ Meals today
        meals = list(db.exec(select(MealPlan).where(MealPlan.plan_date == today)).all())
        # 🧾 Bills due
        bills = list(
            db.exec(
                select(Bill).where(Bill.paid == False, Bill.due_date <= week)  # noqa: E712
            ).all()
        )
        # 🔔 Follow-ups
        followups = list(
            db.exec(
                select(FollowUp).where(
                    FollowUp.done == False, FollowUp.due_date <= soon  # noqa: E712
                )
            ).all()
        )
        # 🪴 Plants
        plants = list(db.exec(select(Plant)).all())
        thirsty = [
            p for p in plants
            if (p.last_watered + timedelta(days=p.water_every_days) if p.last_watered else today)
            <= today
        ]
        # 🧹 Chores
        chores = list(db.exec(select(Chore)).all())
        chores_due = [
            c for c in chores
            if (c.last_done + timedelta(days=c.frequency_days) if c.last_done else today)
            <= today
        ]
        # 🎂 Birthdays today
        occasions = list(db.exec(select(Occasion)).all())
        bdays = [o for o in occasions if o.month == today.month and o.day == today.day]

        # 🙂 Mood — today's latest score + emotions
        mood_today = list(
            db.exec(
                select(MoodLog).where(MoodLog.entry_date == today)
                .order_by(MoodLog.created_at.desc())
            ).all()
        )

        # 👟 Steps — today's total vs goal
        step_today_total = sum(
            s.count
            for s in db.exec(select(StepEntry).where(StepEntry.entry_date == today)).all()
        )
        steps_goal = int(get_setting("steps", "daily_goal", "10000") or 10000)

        # 🏋️ Workout — today's session count + total kcal
        workouts_today = list(
            db.exec(select(Workout).where(Workout.entry_date == today)).all()
        )

        # ☕ Caffeine — today's mg + residual at bedtime
        caffeine_today = list(
            db.exec(
                select(CaffeineEntry).where(CaffeineEntry.entry_date == today)
            ).all()
        )
        caffeine_mg = sum(c.mg for c in caffeine_today)
        bedtime = _bedtime()
        bedtime_dt = datetime.combine(today, bedtime)
        if bedtime_dt < datetime.now():
            bedtime_dt += timedelta(days=1)
        # Pull last 48h of entries for the bedtime-residual calc.
        recent_caffeine = list(
            db.exec(
                select(CaffeineEntry).where(
                    CaffeineEntry.consumed_at >= datetime.now() - timedelta(hours=48)
                )
            ).all()
        )
        caffeine_residual = round(
            sum(_residual_at(e, bedtime_dt) for e in recent_caffeine), 1
        )

        # 🕒 Fasting — running clock if a fast is open
        ongoing_fast = db.exec(
            select(FastSession).where(FastSession.end_time.is_(None))
            .order_by(FastSession.start_time.desc())
        ).first()
        fasting_model: FastingProgress | None = None
        if ongoing_fast is not None:
            elapsed = _duration_hours(ongoing_fast, until=datetime.now())
            fasting_model = FastingProgress(
                started=ongoing_fast.start_time,
                target_hours=ongoing_fast.target_hours,
                elapsed_hours=elapsed,
                remaining_hours=round(
                    max(ongoing_fast.target_hours - elapsed, 0), 2
                ),
                reached=elapsed >= ongoing_fast.target_hours,
            )

        # 🚀 Challenges — active + still need today's check-in
        active_challenges = list(
            db.exec(select(Challenge).where(Challenge.status == "active")).all()
        )
        pending_checkin_challenges = []
        for ch in active_challenges:
            # Skip challenges outside their window.
            if today < ch.start_date or today > _end_date(ch):
                continue
            existing = db.exec(
                select(ChallengeCheckin)
                .where(ChallengeCheckin.challenge_id == ch.id)
                .where(ChallengeCheckin.check_date == today)
            ).first()
            if existing is None:
                # Need check-in.
                cs = _checkins(db, ch.id)
                _auto_finalize(ch, cs)
                if ch.status == "active":
                    pending_checkin_challenges.append(ChallengePending(
                        id=ch.id, name=ch.name,
                        day=(today - ch.start_date).days + 1,
                        target_days=ch.target_days,
                    ))

        # 📦 Packages — pending count + late count
        packages_pending = list(
            db.exec(
                select(Package).where(
                    Package.status.in_(["ordered", "in_transit"])
                )
            ).all()
        )
        packages_late = [
            p for p in packages_pending
            if p.expected_date is not None and p.expected_date < today
        ]

        # 📑 Documents — expiring within 30 days
        soon_30 = today + timedelta(days=30)
        documents_expiring = list(
            db.exec(
                select(Document)
                .where(Document.expires >= today)
                .where(Document.expires <= soon_30)
                .order_by(Document.expires)
            ).all()
        )

        # ✍️ Writing — today's words across all projects, goal & streak
        writing_today_rows = list(
            db.exec(
                select(WritingSession).where(WritingSession.entry_date == today)
            ).all()
        )
        writing_words = sum(s.words for s in writing_today_rows)
        writing_goal = int(get_setting("writing", "daily_words", "500") or 500)
        writing_days = {
            s.entry_date for s in db.exec(select(WritingSession)).all()
        }
        writing_streak = _streak_from_days(writing_days, today)

        # 📖 Books — today's reading sessions (pages + minutes + book titles)
        book_sessions_today = list(
            db.exec(
                select(BookSession).where(BookSession.entry_date == today)
            ).all()
        )
        book_titles = {b.id: b.title for b in db.exec(select(Book)).all()}
        books_today_titles = sorted({
            book_titles.get(s.book_id, "?") for s in book_sessions_today
        })

        # 🤒 Symptoms — today's flare-ups
        symptoms_today = list(
            db.exec(
                select(Symptom).where(Symptom.entry_date == today)
            ).all()
        )
        worst_sym = (
            max(symptoms_today, key=lambda s: s.intensity)
            if symptoms_today else None
        )
        symptom_names_today = sorted({s.name for s in symptoms_today})

        # 📊 Daily check-ins — every actively-used tracker with today's status
        daily_checkins = collect_checkins(db, today=today)

    # Latest mood for the headline row
    latest_mood = mood_today[0] if mood_today else None

    return TodaySnapshot(
        date=today,
        tasks=TasksBlock(
            pending=len(tasks),
            overdue=[TaskSummary(title=t.title, priority=t.priority) for t in overdue],
            due_today=[TaskSummary(title=t.title, priority=t.priority) for t in due_today],
            done_today=[
                TaskSummary(title=t.title, priority=t.priority)
                for t in done_today_tasks
            ],
        ),
        habits=HabitsBlock(
            total=len(habits),
            done_today=sum(1 for h in habits if h.id in checked),
            items=[HabitItem(name=h.name, done=h.id in checked) for h in habits],
        ),
        water=GoalProgress(total_ml=water_total, goal_ml=water_goal),
        calories=GoalProgress(total_kcal=kcal_total, goal_kcal=kcal_goal),
        focus=GoalProgress(total_minutes=focus_total, goal_minutes=focus_goal),
        events=[EventToday(time=e.event_time, title=e.title) for e in events],
        meals=[MealToday(meal=m.meal_type, dish=m.dish) for m in meals],
        bills=[
            BillDue(name=b.name, due=b.due_date, overdue=b.due_date < today)
            for b in bills
        ],
        followups=[
            FollowupDue(person=f.person, due=f.due_date, overdue=f.due_date < today)
            for f in followups
        ],
        plants_thirsty=[
            NamedItem(name=p.name, location=p.location) for p in thirsty
        ],
        chores_due=[
            NamedItem(name=c.name, assignee=c.assignee) for c in chores_due
        ],
        birthdays=[BirthdayToday(person=o.person, kind=o.kind) for o in bdays],
        mood=(
            MoodToday(
                score=latest_mood.score,
                emotion=latest_mood.emotion,
                checkins=len(mood_today),
            ) if latest_mood else None
        ),
        steps=GoalProgress(
            total=step_today_total, goal=steps_goal,
            reached=step_today_total >= steps_goal,
        ),
        workouts=WorkoutsToday(
            sessions=len(workouts_today),
            kcal=sum(w.kcal_burned or 0 for w in workouts_today),
            minutes=sum(w.duration_min for w in workouts_today),
        ),
        caffeine=CaffeineToday(
            mg_today=caffeine_mg,
            residual_at_bedtime_mg=caffeine_residual,
            drinks=len(caffeine_today),
        ),
        fasting=fasting_model,
        challenges_pending=pending_checkin_challenges,
        packages=PackagesBlock(
            pending=len(packages_pending),
            late=[
                LatePackage(id=p.id, sender=p.sender, expected_date=p.expected_date)
                for p in packages_late
            ],
        ),
        documents_expiring=[
            DocumentExpiring(
                name=d.name, kind=d.kind, expires=d.expires,
                days_until=(d.expires - today).days,
            )
            for d in documents_expiring
        ],
        writing=WritingToday(
            total_words=writing_words,
            goal_words=writing_goal,
            reached=writing_words >= writing_goal,
            sessions=len(writing_today_rows),
            current_streak=writing_streak,
        ),
        books=BooksToday(
            pages=sum(s.pages for s in book_sessions_today),
            minutes=sum(s.duration_min for s in book_sessions_today),
            sessions=len(book_sessions_today),
            books=books_today_titles,
        ),
        symptoms=SymptomToday(
            episodes=len(symptoms_today),
            worst_intensity=worst_sym.intensity if worst_sym else 0,
            worst_name=worst_sym.name if worst_sym else None,
            names=symptom_names_today,
        ),
        checkins=daily_checkins,
    )


def _section(title: str, items: list, render_item) -> None:
    if not items:
        return
    console.print(f"\n[bold]{title}[/bold]")
    for item in items:
        console.print(f"  {render_item(item)}")


def render_today(json_out: bool, on: date | None = None) -> None:
    """Render the dashboard to stdout — for ``on`` if given, else today."""
    data: TodaySnapshot = collect_today(on=on)
    if json_out:
        _emit_json(data)
        return

    # Header reads "Today" only when it really is today; otherwise show
    # the date so the user knows they're looking at a past day.
    if data.date == date.today():
        header = "Today"
    elif data.date == date.today() - timedelta(days=1):
        header = "Yesterday"
    else:
        header = data.date.strftime("%A")
    console.print(f"\n📅 [bold]{header}[/bold] · {data.date:%A %d %B %Y}\n")

    # 🎂 Birthdays first — easy to miss
    if data.birthdays:
        console.print("[bold]🎂 Today[/bold]")
        for b in data.birthdays:
            console.print(f"  🎉 {b.kind.title()}: [bold]{b.person}[/bold]")
        console.print()

    # ✅ Tasks
    if data.tasks.overdue or data.tasks.due_today:
        console.print("[bold]✅ Tasks[/bold]")
        for t in data.tasks.overdue:
            console.print(f"  [red]⚠ overdue[/red]  {t.title}  [dim]({t.priority})[/dim]")
        for t in data.tasks.due_today:
            console.print(f"  [yellow]● today[/yellow]    {t.title}  [dim]({t.priority})[/dim]")
        console.print()

    # 🏁 Completed-on-this-day — most valuable on `clibo yesterday`,
    # where the natural ask is "what did I get done?".
    if data.tasks.done_today:
        verb = "Done yesterday" if header == "Yesterday" else (
            "Done today" if header == "Today" else f"Done on {data.date:%b %d}"
        )
        console.print(f"[bold]🏁 {verb}[/bold]  [green]{len(data.tasks.done_today)}[/green]")
        for t in data.tasks.done_today:
            console.print(f"  [green]✓[/green]  {t.title}  [dim]({t.priority})[/dim]")
        console.print()

    # 🔥 Habits
    if data.habits.total:
        console.print(
            f"[bold]🔥 Habits[/bold]  [cyan]{data.habits.done_today}[/cyan]/"
            f"{data.habits.total} done"
        )
        for item in data.habits.items:
            mark = "[green]✓[/green]" if item.done else "[dim]○[/dim]"
            console.print(f"  {mark} {item.name}")
        console.print()

    # 💧🍎🍅👟 Daily metrics
    metric_lines: list[str] = []
    if data.water.goal_ml:
        metric_lines.append(
            f"💧 Water    {bar(data.water.total_ml, data.water.goal_ml, width=18)}  "
            f"[bold]{data.water.total_ml}[/bold]/{data.water.goal_ml} ml"
        )
    if data.calories.goal_kcal:
        metric_lines.append(
            f"🍎 Calories {bar(data.calories.total_kcal, data.calories.goal_kcal, width=18)}  "
            f"[bold]{data.calories.total_kcal}[/bold]/{data.calories.goal_kcal} kcal"
        )
    if data.focus.total_minutes or data.focus.goal_minutes:
        metric_lines.append(
            f"🍅 Focus    {bar(data.focus.total_minutes, data.focus.goal_minutes, width=18)}  "
            f"[bold]{data.focus.total_minutes}[/bold]/{data.focus.goal_minutes} min"
        )
    if data.steps.total or data.steps.goal:
        metric_lines.append(
            f"👟 Steps    {bar(data.steps.total, data.steps.goal, width=18)}  "
            f"[bold]{data.steps.total:,}[/bold]/{data.steps.goal:,}"
        )
    if metric_lines:
        for line in metric_lines:
            console.print(f"  {line}")
        console.print()

    # 🕒 Fasting — running clock if a fast is open
    if data.fasting is not None:
        f = data.fasting
        colour = "green" if f.reached else "yellow"
        trailing = (
            "[green]✓ target reached[/green]" if f.reached
            else f"[{colour}]{f.remaining_hours:g}h to target[/{colour}]"
        )
        console.print(
            f"  🕒 [bold]Fasting[/bold]   "
            f"{bar(f.elapsed_hours, f.target_hours, width=18)}  "
            f"[bold cyan]{f.elapsed_hours:g}h[/bold cyan]/"
            f"{f.target_hours:g}h   ·   {trailing}\n"
        )

    # 🙂☕🏋️ Lightweight one-liners for trackers with activity today
    today_lines: list[str] = []
    if data.mood is not None:
        m = data.mood
        emotion = f" — {m.emotion}" if m.emotion else ""
        today_lines.append(
            f"🙂 Mood     {m.score}/5{emotion}"
            + (f"   [dim]({m.checkins} check-ins today)[/dim]"
               if m.checkins > 1 else "")
        )
    caf = data.caffeine
    if caf.drinks:
        residual_colour = "yellow" if caf.residual_at_bedtime_mg > 10 else "green"
        today_lines.append(
            f"☕ Caffeine {caf.mg_today} mg total   ·   "
            f"[{residual_colour}]{caf.residual_at_bedtime_mg:g} mg residual at bedtime"
            f"[/{residual_colour}]"
        )
    wo = data.workouts
    if wo.sessions:
        kcal_part = f"   ·   🔥 {wo.kcal} kcal" if wo.kcal else ""
        min_part = f"   ·   ⏱ {wo.minutes} min" if wo.minutes else ""
        today_lines.append(
            f"🏋️ Workouts {wo.sessions} session{'s' if wo.sessions != 1 else ''}"
            f"{min_part}{kcal_part}"
        )
    wr = data.writing
    if wr.sessions:
        streak_part = (f"   ·   🔥 {wr.current_streak}-day streak"
                       if wr.current_streak > 1 else "")
        goal_marker = " 🎉" if wr.reached else ""
        today_lines.append(
            f"✍️ Writing  {wr.total_words}/{wr.goal_words} w{goal_marker}"
            f"   ·   {wr.sessions} session{'s' if wr.sessions != 1 else ''}"
            f"{streak_part}"
        )
    bk = data.books
    if bk.sessions:
        title_part = ""
        if bk.books:
            shown = bk.books[:2]
            more = f" + {len(bk.books) - 2} more" if len(bk.books) > 2 else ""
            title_part = f"   ·   [dim]{', '.join(shown)}{more}[/dim]"
        min_part = f"   ·   ⏱ {bk.minutes} min" if bk.minutes else ""
        today_lines.append(
            f"📖 Reading  {bk.pages}p"
            f"   ·   {bk.sessions} session{'s' if bk.sessions != 1 else ''}"
            f"{min_part}{title_part}"
        )
    sym = data.symptoms
    if sym.episodes:
        # Colour-code by worst intensity in line with the standard 1-10 scale.
        colour = (
            "green" if sym.worst_intensity <= 3
            else "yellow" if sym.worst_intensity <= 6
            else "red" if sym.worst_intensity <= 9
            else "bold red"
        )
        names_part = ""
        if sym.names:
            shown = sym.names[:2]
            more = f" + {len(sym.names) - 2} more" if len(sym.names) > 2 else ""
            names_part = f"   ·   [dim]{', '.join(shown)}{more}[/dim]"
        today_lines.append(
            f"🤒 Symptoms {sym.episodes} episode{'s' if sym.episodes != 1 else ''}"
            f"   ·   worst [{colour}]{sym.worst_intensity}/10[/{colour}]"
            f" ({sym.worst_name}){names_part}"
        )
    if today_lines:
        for line in today_lines:
            console.print(f"  {line}")
        console.print()

    # 📊 Daily check-ins — every active tracker, with today's status
    if data.checkins:
        done = sum(1 for c in data.checkins if c.logged_today)
        console.print(
            f"[bold]📊 Daily check-ins[/bold]   "
            f"[cyan]{done}[/cyan]/{len(data.checkins)} logged"
        )
        for ci in data.checkins:
            label = f"{ci.emoji} {ci.name}"
            if ci.logged_today:
                console.print(
                    f"  [green]✓[/green]  {label:<14}  [bold]{ci.today_value}[/bold]"
                )
            else:
                ago = (f"{ci.last_days_ago}d ago"
                       if ci.last_days_ago is not None else "")
                last = (f"   [dim]last {ci.last_value}"
                        + (f", {ago}" if ago else "") + "[/dim]"
                        if ci.last_value else "")
                console.print(
                    f"  [dim]○[/dim]  {label:<14}  [dim]not logged today[/dim]"
                    f"{last}"
                )
        console.print()

    # 🚀 Challenges that still need today's check-in
    if data.challenges_pending:
        console.print("[bold]🚀 Challenges — check-in pending[/bold]")
        for ch in data.challenges_pending:
            console.print(
                f"  · [bold]{ch.name}[/bold]    "
                f"day {ch.day}/{ch.target_days}    "
                f"[dim]clibo challenge check {ch.id}[/dim]"
            )
        console.print()

    # 📦 Packages — surface late ones; otherwise just a count
    if data.packages.late:
        console.print("[bold]📦 Late packages[/bold]")
        for p in data.packages.late:
            console.print(
                f"  [red]⚠[/red]  {p.sender}   "
                f"[dim]expected {p.expected_date}[/dim]"
            )
        console.print()
    elif data.packages.pending:
        console.print(
            f"  📦 [dim]{data.packages.pending} package"
            f"{'s' if data.packages.pending != 1 else ''} on the way"
            f"[/dim]\n"
        )

    # 📑 Documents expiring soon (≤30 days)
    if data.documents_expiring:
        console.print("[bold]📑 Documents expiring soon[/bold]")
        for d in data.documents_expiring:
            colour = "red" if d.days_until <= 7 else "yellow"
            console.print(
                f"  [{colour}]·[/{colour}]  {d.kind}: {d.name}   "
                f"[dim]expires {d.expires} (in {d.days_until}d)[/dim]"
            )
        console.print()

    # 📅 Events
    _section(
        "📅 Events",
        data.events,
        lambda e: f"[cyan]{e.time or 'all day'}[/cyan]  {e.title}",
    )
    # 🍽️ Meals
    _section(
        "🍽️ Meals",
        data.meals,
        lambda m: f"[cyan]{m.meal:<10}[/cyan] {m.dish}",
    )
    # 🧾 Bills
    _section(
        "🧾 Bills due",
        data.bills,
        lambda b: (f"[red]⚠ overdue[/red]  {b.name}  [dim]({b.due})[/dim]"
                   if b.overdue
                   else f"[yellow]⏰[/yellow]  {b.name}  [dim]({b.due})[/dim]"),
    )
    # 🔔 Follow-ups
    _section(
        "🔔 Follow-ups",
        data.followups,
        lambda f: (f"[red]⚠[/red] {f.person}  [dim]({f.due})[/dim]"
                   if f.overdue
                   else f"[yellow]⏰[/yellow] {f.person}  [dim]({f.due})[/dim]"),
    )
    # 🪴 Plants & 🧹 chores
    _section(
        "🪴 Plants needing water",
        data.plants_thirsty,
        lambda p: f"{p.name}" + (f"  [dim]({p.location})[/dim]" if p.location else ""),
    )
    _section(
        "🧹 Chores due",
        data.chores_due,
        lambda c: f"{c.name}" + (f"  [dim]({c.assignee})[/dim]" if c.assignee else ""),
    )

    # Empty-state cheer
    has_anything = any([
        data.birthdays, data.tasks.overdue, data.tasks.due_today,
        data.tasks.done_today,
        data.habits.total, metric_lines, data.events, data.meals,
        data.bills, data.followups, data.plants_thirsty, data.chores_due,
        data.fasting, today_lines, data.challenges_pending,
        data.packages.late, data.packages.pending,
        data.documents_expiring, data.checkins,
    ])
    if not has_anything:
        console.print("  [dim]Nothing on the radar today — enjoy! ✨[/dim]\n")
    else:
        console.print()
