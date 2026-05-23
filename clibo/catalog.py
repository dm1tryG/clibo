"""The catalog of all 50 clibo tools.

This is the single source of truth for what clibo aims to be. ``clibo info``
reads it to show progress; the build loop reads PLAN.md (generated from this)
to decide what to build next. Tools are listed in build order.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    """One planned CLI: its command name, emoji, category and one-liner."""

    name: str
    emoji: str
    category: str
    summary: str


CATALOG: list[Tool] = [
    # ── 🏃 Health & Wellness ──────────────────────────────────────────────
    Tool("calorie", "🍎", "Health & Wellness", "Food & calorie tracker with macros"),
    Tool("water", "💧", "Health & Wellness", "Daily water intake tracker"),
    Tool("weight", "⚖️", "Health & Wellness", "Body-weight log with BMI & trend"),
    Tool("workout", "🏋️", "Health & Wellness", "Exercise & gym session log"),
    Tool("sleep", "😴", "Health & Wellness", "Sleep duration & quality tracker"),
    Tool("mood", "🙂", "Health & Wellness", "Daily mood & emotion journal"),
    Tool("meds", "💊", "Health & Wellness", "Medication log & dosage reminders"),
    Tool("period", "🌸", "Health & Wellness", "Menstrual cycle tracker & predictions"),
    Tool("meditate", "🧘", "Health & Wellness", "Meditation & mindfulness sessions"),
    Tool("vitals", "❤️", "Health & Wellness", "Blood pressure, pulse & glucose log"),
    # ── 💰 Money & Finance ────────────────────────────────────────────────
    Tool("expense", "💸", "Money & Finance", "Personal expense tracker"),
    Tool("budget", "📊", "Money & Finance", "Monthly budgets by category"),
    Tool("subs", "🔁", "Money & Finance", "Recurring subscriptions tracker"),
    Tool("bills", "🧾", "Money & Finance", "Bills & due-date reminders"),
    Tool("savings", "🐷", "Money & Finance", "Savings goals with progress"),
    Tool("debt", "📉", "Money & Finance", "Debt & loan payoff tracker"),
    Tool("networth", "💰", "Money & Finance", "Assets, liabilities & net worth"),
    Tool("invoice", "📄", "Money & Finance", "Freelance invoice generator"),
    Tool("split", "🤝", "Money & Finance", "Split shared expenses with people"),
    Tool("wishlist", "⭐", "Money & Finance", "Things-to-buy wishlist with prices"),
    Tool("income", "💵", "Money & Finance", "Income tracker — counterpart to expense"),
    # ── ✅ Productivity & Work ────────────────────────────────────────────
    Tool("todo", "✅", "Productivity & Work", "Task & to-do manager"),
    Tool("notes", "📝", "Productivity & Work", "Quick searchable notes"),
    Tool("habit", "🔥", "Productivity & Work", "Habit tracker with streaks"),
    Tool("focus", "🍅", "Productivity & Work", "Pomodoro & focus sessions"),
    Tool("time", "⏱️", "Productivity & Work", "Time tracking by project"),
    Tool("journal", "📔", "Productivity & Work", "Daily journal & diary"),
    Tool("goals", "🎯", "Productivity & Work", "Goals & OKRs with milestones"),
    Tool("events", "📅", "Productivity & Work", "Events & reminders calendar"),
    Tool("worklog", "🗒️", "Productivity & Work", "Work log & standup notes"),
    Tool("bookmark", "🔖", "Productivity & Work", "Bookmarks & link saver"),
    Tool("ideas", "💡", "Productivity & Work", "Idea capture with lifecycle (raw → shipped)"),
    # ── 🤝 CRM & Relationships ────────────────────────────────────────────
    Tool("crm", "👥", "CRM & Relationships", "Contacts CRM"),
    Tool("leads", "🧲", "CRM & Relationships", "Sales pipeline & deals"),
    Tool("followup", "🔔", "CRM & Relationships", "Follow-up reminders for people"),
    Tool("meetings", "🗓️", "CRM & Relationships", "Meeting notes & action items"),
    Tool("jobs", "💼", "CRM & Relationships", "Job application tracker"),
    Tool("clients", "🧑‍💼", "CRM & Relationships", "Freelance client manager"),
    Tool("birthdays", "🎂", "CRM & Relationships", "Birthday & anniversary reminders"),
    Tool("network", "🌐", "CRM & Relationships", "Networking & people-you-met log"),
    Tool("gifts", "🎁", "CRM & Relationships", "Gift ideas & giving tracker"),
    Tool("brag", "🏆", "CRM & Relationships", "Achievement log for reviews"),
    Tool("cv", "📜", "CRM & Relationships", "Career history — jobs, education, projects, certs"),
    # ── 🏠 Home & Life ───────────────────────────────────────────────────
    Tool("groceries", "🛒", "Home & Life", "Grocery & shopping list"),
    Tool("pantry", "🥫", "Home & Life", "Food inventory with expiry dates"),
    Tool("recipes", "👨‍🍳", "Home & Life", "Personal recipe book"),
    Tool("meals", "🍽️", "Home & Life", "Weekly meal planner"),
    Tool("chores", "🧹", "Home & Life", "Household chores rotation"),
    Tool("plants", "🪴", "Home & Life", "Plant care & watering schedule"),
    Tool("car", "🚗", "Home & Life", "Car maintenance & fuel log"),
    Tool("home", "🏠", "Home & Life", "Home maintenance & repairs"),
    Tool("pets", "🐾", "Home & Life", "Pet care, feeding & vet log"),
    Tool("travel", "✈️", "Home & Life", "Trip planner & itinerary"),
    # ── 🎨 Hobbies & Culture ────────────────────────────────────────────
    Tool("books", "📚", "Hobbies & Culture", "Reading log with progress & ratings"),
    Tool("films", "🎬", "Hobbies & Culture", "Movie & show watchlist with ratings"),
    Tool("mileage", "🏃", "Hobbies & Culture", "Running/cycling/walking distance log"),
    Tool("gratitude", "🙏", "Hobbies & Culture", "Daily gratitude practice with streaks"),
    Tool("quotes", "💬", "Hobbies & Culture", "A commonplace book of quotes worth keeping"),
    Tool("flashcards", "🃏", "Hobbies & Culture", "Spaced-repetition flashcards (Leitner-style)"),
    Tool("lessons", "📓", "Hobbies & Culture", "Lessons learned — context + takeaway"),
    Tool("dashboard", "🎛️", "Hobbies & Culture", "Customizable widget dashboard"),
]

CATEGORIES: list[str] = list(dict.fromkeys(t.category for t in CATALOG))


def by_name(name: str) -> Tool | None:
    """Look up a tool definition by its command name."""
    return next((t for t in CATALOG if t.name == name), None)
