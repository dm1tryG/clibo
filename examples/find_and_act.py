#!/usr/bin/env python3
"""A small agent pattern: search across clibo, then act on a match.

The agent question this answers: "Find every mention of <topic> across the
user's clibo data, and offer to schedule a follow-up."

Usage:  python examples/find_and_act.py acme
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, timedelta


def clibo(*args: str) -> dict | list:
    out = subprocess.run(
        ["clibo", *args, "--json"], capture_output=True, check=True, text=True
    )
    return json.loads(out.stdout)


def main(query: str) -> int:
    hits = clibo("search", query)
    if hits["count"] == 0:
        print(f"No matches for {query!r}.")
        return 0

    print(f"🔍 {hits['count']} matches for {query!r}:\n")
    for hit in hits["results"]:
        print(f"  · [{hit['source']:>8}] #{hit['id']}  {hit['snippet']}")

    # A common agent move: if any of the matches are CRM contacts, suggest a
    # follow-up reminder for one of them next week.
    crm_hits = [h for h in hits["results"] if h["source"] == "crm"]
    if not crm_hits:
        return 0

    print()
    contact = crm_hits[0]
    due = (date.today() + timedelta(days=7)).isoformat()
    print(f"💡 You could add a follow-up reminder for {contact['snippet']}:")
    print(f"   clibo followup add \"{contact['snippet'].split(' · ')[0]}\" -d {due}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python examples/find_and_act.py <search-query>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
