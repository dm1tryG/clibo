"""Every bare-default command (e.g. ``clibo expense``) must also accept ``--json``.

This was broken across 42 tools — the ``@app.callback()`` accepted only
``ctx`` and ignored ``--json``, so agent flows like ``clibo expense --json``
failed with "No such option '--json'". This file pins the contract.
"""

from __future__ import annotations

import json

# All tools that have a bare-default callback (alphabetised).
# `dashboard` is excluded — its bare form already takes no flags.
BARE_DEFAULT_TOOLS = [
    "bills", "birthdays", "budget", "caffeine", "calorie", "challenge",
    "chores", "documents", "donations", "dreams", "events", "expense",
    "fasting", "flashcards", "focus", "followup", "goals", "gratitude",
    "habit", "income", "jobs", "journal", "leads", "meals", "meds",
    "mileage", "mood", "networth", "packages", "plants", "sleep",
    "split", "steps", "stretches", "subs", "symptom", "time", "vitals",
    "water", "worklog", "workout", "writing",
]


def test_every_bare_default_accepts_json(cli):
    """`clibo <tool> --json` on the bare command must return valid JSON.

    A single test loops over every tool because the contract is uniform;
    pinning each individually would be 42 near-identical tests. Any
    failure here points at one specific tool — see the assertion text.
    """
    failures = []
    for tool in BARE_DEFAULT_TOOLS:
        result = cli.run(tool, "--json")
        # Exit code can be non-zero for empty-state errors (e.g. sleep
        # with no logs), but the output must still be valid JSON —
        # that's the contract agents rely on.
        try:
            json.loads(result.output)
        except json.JSONDecodeError as exc:
            failures.append(
                f"{tool}: not valid JSON (exit={result.exit_code}, {exc})"
            )
    assert not failures, (
        "Bare-default tools should emit JSON on --json:\n  "
        + "\n  ".join(failures)
    )


def test_bare_default_human_view_still_works(cli):
    """Sanity: passing no flag still produces the human view (not JSON)."""
    result = cli.run("expense")
    assert result.exit_code == 0
    # Rich tables / Rich-rendered headers contain non-ASCII or
    # markdown-like markers; the output is decidedly not JSON.
    assert not result.output.lstrip().startswith("{")
