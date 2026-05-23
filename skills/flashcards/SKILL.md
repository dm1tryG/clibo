---
name: clibo-flashcards
description: Spaced-repetition flashcards with the `clibo flashcards` CLI. Use when the user wants to memorise term/definition pairs — language vocab, formulas, names. Leitner-style boxes (1/3/7/14/30 day intervals). Maps "Spanish: día = day" to `clibo flashcards add "día" "day" -d spanish`.
---

# 🃏 clibo flashcards

Spaced-repetition flashcards, Leitner-style. Each card lives in a box
0–4; **right** answer → next box (longer interval); **wrong** → back to
box 0. Intervals: 1, 3, 7, 14, 30 days.

## Commands

| Command | What it does |
|---|---|
| `clibo flashcards add FRONT BACK -d DECK` | Add a card |
| `clibo flashcards due [-d DECK]` | Cards due for review today |
| `clibo flashcards grade ID right\|wrong` | Record a review result |
| `clibo flashcards list [-d DECK]` | All cards |
| `clibo flashcards decks` | Card counts and due counts per deck |
| `clibo flashcards rm ID` | Delete a card |
| `clibo flashcards stats` | Box distribution and accuracy |

## Agent flow

The standard review loop looks like:

```bash
# 1. find what's due
clibo flashcards due --json
# 2. for each card, show the front, prompt the user, then:
clibo flashcards grade <id> right    # or wrong
```

| User says | Command |
|---|---|
| "Spanish vocab: día = day" | `clibo flashcards add "día" "day" -d spanish` |
| "Let's review my Spanish" | `clibo flashcards due -d spanish` |
| "Got that one right" (after a review) | `clibo flashcards grade <id> right` |
| "What decks do I have?" | `clibo flashcards decks` |

```bash
clibo flashcards stats --json
# -> { "total_cards", "due_today", "by_box": {0: 5, 1: 3, …},
#      "total_reviews", "accuracy_pct", "mastered_box_4" }
```
