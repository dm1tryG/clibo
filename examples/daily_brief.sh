#!/usr/bin/env bash
# A bash version of examples/daily_brief.py — same idea, uses jq.
#
# Usage:  bash examples/daily_brief.sh
set -euo pipefail

today=$(clibo today --json)
week=$(clibo week --json)

date=$(jq -r .date <<<"$today")
echo "# 📅 Daily brief · $date"
echo

# Tasks
overdue=$(jq -r '.tasks.overdue[] | "- ⚠ **overdue** — \(.title) _(\(.priority))_"' <<<"$today")
today_tasks=$(jq -r '.tasks.due_today[] | "- 🟡 due today — \(.title) _(\(.priority))_"' <<<"$today")
if [ -n "$overdue$today_tasks" ]; then
    echo "## ✅ Tasks"
    [ -n "$overdue" ] && echo "$overdue"
    [ -n "$today_tasks" ] && echo "$today_tasks"
    echo
fi

# Daily metrics
water_goal=$(jq -r '.water.goal_ml // 0' <<<"$today")
if [ "$water_goal" -gt 0 ]; then
    water_total=$(jq -r '.water.total_ml' <<<"$today")
    pct=$(( water_total * 100 / water_goal ))
    echo "## 📊 Today"
    echo "- 💧 Water: ${water_total} / ${water_goal} ml (${pct}%)"
fi

# Weekly trend
nights=$(jq -r '.sleep.nights_logged' <<<"$week")
if [ "$nights" -gt 0 ]; then
    avg=$(jq -r '.sleep.avg_hours' <<<"$week")
    focus=$(jq -r '.focus.total_minutes' <<<"$week")
    spent=$(jq -r '.expenses.total' <<<"$week")
    currency=$(jq -r '.expenses.currency' <<<"$week")
    start=$(jq -r '.start' <<<"$week")
    end=$(jq -r '.end' <<<"$week")
    echo
    echo "## 🗓️ This week ($start → $end)"
    echo "- 😴 Sleep: **${avg}h** avg over $nights nights"
    echo "- 🍅 Focus: **${focus} min** total"
    echo "- 💸 Spent: **${spent} ${currency}**"
fi
