"""Pydantic models for the integration views.

`today`, `week`, `month` and `checkin` used to pass around plain dicts
constructed in collect_*() and consumed in render_*() via `data["foo"]`
accesses. That worked but had no type safety and no schema documentation.

These Pydantic v2 models give every field a typed contract. Both producers
and consumers use attribute access (`snapshot.tasks.overdue`) instead of
dict subscription, and `_emit_json` serializes them with the same JSON shape
as before so external consumers (tests, agents) keep working unchanged.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class _BaseSnapshot(BaseModel):
    """Allow the unusual types we pass through (`datetime`, `date`) without
    fuss — Pydantic v2 handles both natively as long as we don't reject them."""

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ──────────────────────────────────────────────────────────────────────
# `today` view
# ──────────────────────────────────────────────────────────────────────


class TaskSummary(_BaseSnapshot):
    title: str
    priority: str


class TasksBlock(_BaseSnapshot):
    pending: int
    overdue: list[TaskSummary]
    due_today: list[TaskSummary]
    # Tasks completed on the snapshot's date — most useful on `yesterday`,
    # where the natural question is "what did I get done?".
    done_today: list[TaskSummary] = []


class HabitItem(_BaseSnapshot):
    name: str
    done: bool
    # The current streak as of yesterday — useful for "you'll break a
    # 5-day streak if you don't check in today" surfacing. Zero means
    # no active streak (so no urgency).
    current_streak: int = 0


class HabitsBlock(_BaseSnapshot):
    total: int
    done_today: int
    items: list[HabitItem]


class GoalProgress(_BaseSnapshot):
    """A simple metric with a daily target — water, calories, focus."""

    total_ml: int | None = None
    goal_ml: int | None = None
    total_kcal: int | None = None
    goal_kcal: int | None = None
    total_minutes: int | None = None
    goal_minutes: int | None = None
    total: int | None = None
    goal: int | None = None
    reached: bool | None = None


class EventToday(_BaseSnapshot):
    time: str | None
    title: str


class MealToday(_BaseSnapshot):
    meal: str
    dish: str


class BillDue(_BaseSnapshot):
    name: str
    due: date
    overdue: bool


class FollowupDue(_BaseSnapshot):
    person: str
    due: date
    overdue: bool


class NamedItem(_BaseSnapshot):
    name: str
    location: str | None = None
    assignee: str | None = None


class BirthdayToday(_BaseSnapshot):
    person: str
    kind: str


class MoodToday(_BaseSnapshot):
    score: int
    emotion: str | None
    checkins: int


class WorkoutsToday(_BaseSnapshot):
    sessions: int
    kcal: int
    minutes: int


class CaffeineToday(_BaseSnapshot):
    mg_today: int
    residual_at_bedtime_mg: float
    drinks: int


class FastingProgress(_BaseSnapshot):
    started: datetime
    target_hours: float
    elapsed_hours: float
    remaining_hours: float
    reached: bool


class ChallengePending(_BaseSnapshot):
    id: int
    name: str
    day: int
    target_days: int


class LatePackage(_BaseSnapshot):
    id: int
    sender: str
    expected_date: date | None


class PackagesBlock(_BaseSnapshot):
    pending: int
    late: list[LatePackage]


class DocumentExpiring(_BaseSnapshot):
    name: str
    kind: str
    expires: date
    days_until: int


class WritingToday(_BaseSnapshot):
    """Words written today across all projects, with goal & streak."""

    total_words: int
    goal_words: int
    reached: bool
    sessions: int
    current_streak: int


class SymptomToday(_BaseSnapshot):
    """Symptom events today — count, worst score, distinct conditions."""

    episodes: int
    worst_intensity: int
    worst_name: str | None
    names: list[str]


class BooksToday(_BaseSnapshot):
    """Reading sessions today — pages, minutes, and which book(s)."""

    pages: int
    minutes: int
    sessions: int
    books: list[str]


class CheckinStatus(_BaseSnapshot):
    name: str
    emoji: str
    logged_today: bool
    today_value: str | None
    last_value: str | None
    last_days_ago: int | None
    question: str
    command: str


class TodaySnapshot(_BaseSnapshot):
    date: date
    tasks: TasksBlock
    habits: HabitsBlock
    water: GoalProgress
    calories: GoalProgress
    focus: GoalProgress
    steps: GoalProgress
    events: list[EventToday]
    meals: list[MealToday]
    bills: list[BillDue]
    followups: list[FollowupDue]
    plants_thirsty: list[NamedItem]
    chores_due: list[NamedItem]
    birthdays: list[BirthdayToday]
    mood: MoodToday | None
    workouts: WorkoutsToday
    caffeine: CaffeineToday
    fasting: FastingProgress | None
    challenges_pending: list[ChallengePending]
    packages: PackagesBlock
    documents_expiring: list[DocumentExpiring]
    writing: WritingToday
    books: BooksToday
    symptoms: SymptomToday
    checkins: list[CheckinStatus]


# ──────────────────────────────────────────────────────────────────────
# `week` view
# ──────────────────────────────────────────────────────────────────────


class SleepWeek(_BaseSnapshot):
    nights_logged: int
    avg_hours: float | None
    avg_quality: float | None


class CalorieWeek(_BaseSnapshot):
    days_logged: int
    total_kcal: int
    avg_kcal_per_logged_day: float | None
    goal_kcal: int | None


class WaterWeek(_BaseSnapshot):
    days_logged: int
    total_ml: int
    goal_ml: int
    days_goal_reached: int


class FocusWeek(_BaseSnapshot):
    sessions: int
    total_minutes: int
    days_focused: int
    goal_minutes_per_day: int


class MoodWeek(_BaseSnapshot):
    checkins: int
    avg_score: float | None


class CategoryTotal(_BaseSnapshot):
    category: str
    amount: float


class ExpensesWeek(_BaseSnapshot):
    entries: int
    total: float
    avg_per_day: float
    top_category: CategoryTotal | None
    currency: str


class HabitWeekRow(_BaseSnapshot):
    name: str
    done: int
    target_per_week: int
    hit_target: bool


class HabitsWeek(_BaseSnapshot):
    tracked: int
    items: list[HabitWeekRow]
    hit_target: int


class JournalWeek(_BaseSnapshot):
    entries: int
    days_journaled: int


class WorklogWeek(_BaseSnapshot):
    entries: int
    by_kind: dict[str, int]


class TasksWeek(_BaseSnapshot):
    completed: int


class StepsWeek(_BaseSnapshot):
    days_logged: int
    total: int
    avg_per_logged_day: int
    goal: int
    days_goal_reached: int


class WorkoutWeek(_BaseSnapshot):
    sessions: int
    days_active: int
    total_minutes: int
    total_kcal_burned: int


class CaffeineWeek(_BaseSnapshot):
    drinks: int
    days_logged: int
    total_mg: int
    avg_mg_per_logged_day: float
    over_limit_days: int


class FastingWeek(_BaseSnapshot):
    completed: int
    total_hours: float
    avg_hours: float
    longest_hours: float
    target_hits: int


class TimedActivityWeek(_BaseSnapshot):
    sessions: int
    days: int
    total_minutes: int


class MileageWeek(_BaseSnapshot):
    sessions: int
    total_km: float
    by_activity: dict[str, float]


class GratitudeWeek(_BaseSnapshot):
    entries: int
    days_logged: int


class DonationsWeek(_BaseSnapshot):
    entries: int
    total: float
    deductible_total: float
    recipients: int


class WritingWeek(_BaseSnapshot):
    sessions: int
    total_words: int
    total_minutes: int
    days_written: int
    avg_words_per_active_day: float
    top_projects: list[CategoryTotal]


class BooksWeek(_BaseSnapshot):
    sessions: int
    pages: int
    minutes: int
    days_read: int
    books: list[str]


class SymptomWeek(_BaseSnapshot):
    episodes: int
    days_affected: int
    avg_intensity: float | None
    worst_intensity: int
    worst_name: str | None
    top_symptoms: list[CategoryTotal]   # name → episode count


class WeekSnapshot(_BaseSnapshot):
    start: date
    end: date
    days: int
    sleep: SleepWeek
    calories: CalorieWeek
    water: WaterWeek
    focus: FocusWeek
    mood: MoodWeek
    expenses: ExpensesWeek
    habits: HabitsWeek
    journal: JournalWeek
    worklog: WorklogWeek
    tasks: TasksWeek
    steps: StepsWeek
    workouts: WorkoutWeek
    caffeine: CaffeineWeek
    fasting: FastingWeek
    meditate: TimedActivityWeek
    stretches: TimedActivityWeek
    mileage: MileageWeek
    gratitude: GratitudeWeek
    donations: DonationsWeek
    writing: WritingWeek
    books: BooksWeek
    symptoms: SymptomWeek


# ──────────────────────────────────────────────────────────────────────
# `month` view
# ──────────────────────────────────────────────────────────────────────


class IncomeMonth(_BaseSnapshot):
    total: float
    entries: int
    by_category: dict[str, float]


class ExpenseMonth(_BaseSnapshot):
    total: float
    entries: int
    by_category: dict[str, float]
    top_category: tuple[str, float] | None


class DonationsMonth(_BaseSnapshot):
    total: float
    entries: int
    deductible_total: float


class BillsMonth(_BaseSnapshot):
    paid: int
    unpaid: int
    paid_total: float
    unpaid_total: float


class InvestMonth(_BaseSnapshot):
    transactions: int
    buys_total: float
    sells_total: float


class MoneyMonth(_BaseSnapshot):
    income: IncomeMonth
    expenses: ExpenseMonth
    donations: DonationsMonth
    bills: BillsMonth
    subs_monthly_total: float
    invest: InvestMonth
    net_cash_flow: float
    currency: str


class CalorieMonth(_BaseSnapshot):
    days_logged: int
    total_kcal: int
    avg_per_day: float | None
    goal_kcal: int | None


class StepsMonth(_BaseSnapshot):
    days_logged: int
    total: int
    avg_per_logged_day: int
    goal: int
    days_goal_reached: int


class FastingMonth(_BaseSnapshot):
    completed: int
    total_hours: float
    longest_hours: float
    target_hits: int


class CaffeineMonth(_BaseSnapshot):
    drinks: int
    days_logged: int
    total_mg: int
    over_limit_days: int


class MileageMonth(_BaseSnapshot):
    sessions: int
    total_km: float


class FocusMonth(_BaseSnapshot):
    sessions: int
    total_minutes: int
    days: int


class WritingMonth(_BaseSnapshot):
    """Aggregated writing for the calendar month."""

    sessions: int
    total_words: int
    total_minutes: int
    days_written: int
    avg_words_per_active_day: float
    top_projects: list[CategoryTotal]


class ProductivityMonth(_BaseSnapshot):
    focus: FocusMonth
    habit_checks: int
    journal_entries: int
    journal_days: int
    gratitude_entries: int
    gratitude_days: int
    tasks_completed: int
    writing: WritingMonth


class BookFinished(_BaseSnapshot):
    title: str
    author: str | None
    rating: int | None


class FilmWatched(_BaseSnapshot):
    title: str
    rating: int | None
    kind: str


class ReadingMonth(_BaseSnapshot):
    """Reading sessions across all books for the month."""

    sessions: int
    pages: int
    minutes: int
    days_read: int
    books: list[str]


class HobbiesMonth(_BaseSnapshot):
    books_finished: list[BookFinished]
    films_watched: list[FilmWatched]
    reading: ReadingMonth


class SymptomMonth(_BaseSnapshot):
    """Aggregate of symptom episodes across a calendar month."""

    episodes: int
    days_affected: int
    avg_intensity: float | None
    worst_intensity: int
    worst_name: str | None
    top_symptoms: list[CategoryTotal]   # name → episode count


class MonthSnapshot(_BaseSnapshot):
    year: int
    month: int
    month_name: str
    start: date
    end: date
    days: int
    money: MoneyMonth
    sleep: SleepWeek
    calories: CalorieMonth
    water: WaterWeek
    steps: StepsMonth
    workouts: WorkoutWeek
    caffeine: CaffeineMonth
    fasting: FastingMonth
    meditate: TimedActivityWeek
    stretches: TimedActivityWeek
    mileage: MileageMonth
    mood: MoodWeek
    productivity: ProductivityMonth
    hobbies: HobbiesMonth
    symptoms: SymptomMonth


# ──────────────────────────────────────────────────────────────────────
# `checkin` view
# ──────────────────────────────────────────────────────────────────────


class CheckinSummary(_BaseSnapshot):
    date: date
    pending_count: int
    logged_count: int
    pending: list[CheckinStatus]
    logged: list[CheckinStatus]


# Type alias for any of the snapshot models — useful for `_emit_json`.
Snapshot = TodaySnapshot | WeekSnapshot | MonthSnapshot | CheckinSummary

# Keep `Any` imported via the module's namespace so callers that need
# arbitrary-shape extras (e.g. checkin record's optional extras) still
# get them.
_ = Any
