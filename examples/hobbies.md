# 🎨 Hobbies & culture

Tools covered: `books`, `films`, `quotes`, `gratitude`, `lessons`,
`flashcards`, `dreams`, `dashboard`.

## Reading

```bash
clibo books add "Atomic Habits" -a "James Clear" -p 320
clibo books start "Atomic Habits"           # mark as currently reading
clibo books log "Atomic Habits" 30          # +30 pages read
clibo books finish "Atomic Habits" -r 5     # finished with rating
clibo books list --status reading
clibo books stats                            # pages read, finished count
```

## Films / TV

```bash
clibo films add "Severance" -k show -s watching
clibo films add "Dune Part Two" -k movie -s watchlist
clibo films watched 1 -r 5                   # mark seen with rating
clibo films list --status watchlist
```

## Quotes (commonplace book)

```bash
clibo quotes add "Stay hungry, stay foolish" -a "Steve Jobs"
clibo quotes add "What you do today is what matters most" -a "Buddha" -t motivation
clibo quotes search "stay"
clibo quotes random                          # pull a random one
```

## Lessons learned

```bash
clibo lessons add "Ship small batches" -c engineering -d "Smaller PRs = fewer bugs"
clibo lessons search "ship"
clibo lessons list -c engineering
```

## Daily gratitude

```bash
clibo gratitude add "coffee, the puppy, finished chapter"
clibo gratitude today                        # what you wrote, current streak
clibo gratitude stats                        # longest streak ever
clibo gratitude edit last -t "coffee, the puppy, finished chapter, sunshine"  # fix
```

## Dreams

A dream journal distinct from `journal` — has vividness, lucid flag, and
comma-separated symbols you can search for recurring themes.

```bash
clibo dreams add "flying over the city" -v 5 --lucid -s flying,city,wind
clibo dreams symbols                         # frequency table — recurring themes
clibo dreams stats                           # lucid rate, avg vividness
```

## Flashcards (spaced repetition)

```bash
clibo flashcards add Spanish "manzana" "apple"
clibo flashcards add Spanish "perro" "dog"
clibo flashcards drill Spanish               # review session, Leitner-style
clibo flashcards stats
```

## Customisable dashboard

```bash
clibo dashboard                              # the default set of widgets
clibo dashboard add weight                   # add a weight widget
clibo dashboard add steps_today
clibo dashboard list                         # current widget set
clibo dashboard rm weight                    # remove
```

## Cross-tool

```bash
clibo search "Atomic"                        # finds books, ideas, quotes, ...
clibo recent -n 20                           # latest activity across hobbies
```
