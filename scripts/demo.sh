#!/usr/bin/env bash
# scripts/demo.sh — a short, self-contained tour of clibo.
#
# Sets CLIBO_HOME to a throwaway temp dir, populates sample data across
# many tools, then runs the showcase commands. Great for recording an
# asciinema demo or for the README walkthrough.
#
# Usage:   ./scripts/demo.sh
# With venv: CLIBO=./.venv/bin/clibo ./scripts/demo.sh
set -euo pipefail

clibo=${CLIBO:-clibo}
export CLIBO_HOME
CLIBO_HOME=$(mktemp -d)
trap 'rm -rf "$CLIBO_HOME"' EXIT

run() {
    echo
    echo "$ $*"
    "$@"
}

quiet() {
    "$@" >/dev/null
}

# ── seed: health
quiet $clibo calorie goal --set 2000
quiet $clibo calorie log "oatmeal with berries" -k 320 -p 12 -c 48 -f 6 -m breakfast
quiet $clibo calorie log "black coffee" -k 5 -m breakfast
quiet $clibo calorie log "chicken salad" -k 520 -p 38 -c 22 -f 24 -m lunch
quiet $clibo water drink 750
quiet $clibo focus goal --set 90
quiet $clibo focus log 45 -t "writing"
quiet $clibo habit add "Read 10 pages"
quiet $clibo habit check "Read 10 pages"
quiet $clibo habit add "Exercise"

# ── seed: money / CRM
quiet $clibo expense currency --set USD
quiet $clibo leads add "Acme renewal" -v 12000 -c "Acme Inc" -s proposal
quiet $clibo leads add "Globex pilot" -v 4000 -c "Globex" -s qualified
quiet $clibo leads add "Initech contract" -v 8000 -c "Initech" -s won
quiet $clibo crm add "Anna Petrova" -c "Acme Inc" -e anna@acme.com -s customer

# ── seed: productivity / home
quiet $clibo todo add "Ship clibo v1" -p high -d today
quiet $clibo todo add "Reply to Acme" -p med
quiet $clibo bills add "Electricity" -d 2026-05-22 -a 65
quiet $clibo events add "Team standup" -d today -t 10:00 -l Zoom
quiet $clibo plants add "Basil" -w 1 -l kitchen
quiet $clibo notes add "Acme contract notes" -b "Discussed annual renewal terms"

# ── showcase commands
run $clibo today
run $clibo calorie today
run $clibo leads pipeline
run $clibo search acme
run $clibo info
