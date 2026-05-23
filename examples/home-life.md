# 🏠 Home & life

Tools covered: `groceries`, `pantry`, `recipes`, `meals`, `chores`, `plants`,
`car`, `home`, `pets`, `travel`, `packages`, `documents`.

## Grocery + pantry

```bash
clibo groceries add chicken
clibo groceries add "olive oil"
clibo groceries done 1                          # got it

clibo pantry add "olive oil" --expires "in 6 months"
clibo pantry expiring                           # what's about to go off
```

## Recipes + meal plan

```bash
clibo recipes add "Chocolate cookies" -i "flour, butter, sugar, chocolate" --steps "..." -t dessert
clibo recipes search "chocolate"

clibo meals plan tomorrow dinner "Chocolate cookies"
clibo meals plan saturday lunch "Quinoa salad"
clibo meals list
```

## Chores

```bash
clibo chores add "Vacuum" -e 7                  # every 7 days
clibo chores add "Take trash out" -e 7 -a "Me"
clibo chores due                                # what's due or overdue
clibo chores done Vacuum
```

## Plants

```bash
clibo plants add "Basil" -w 2                   # water every 2 days
clibo plants thirsty                            # who needs water now
clibo plants water Basil
```

## Car

```bash
clibo car fuel 45 -c 60                         # 45 L for $60 (odometer optional)
clibo car fuel 45.5 -o 52340 -c 68              # with odometer reading
clibo car service "Oil change" -c 80 -o 52500
clibo car stats                                 # spending + economy
```

## Home maintenance

```bash
clibo home add "HVAC filter" -e 90 -c upkeep    # repeats every 90 days
clibo home done 1
```

## Pets

```bash
clibo pets add Whiskers -s cat
clibo pets log Whiskers --kind food
clibo pets log Whiskers --kind vet --cost 120 --summary "annual checkup"
```

## Trips

```bash
clibo travel add "Lisbon trip" -d "in 3 months" --destination Lisbon
clibo travel plan 1 "Book flights" -d "in 2 months"
clibo travel show 1
clibo travel upcoming
```

## Packages

The everyday "where's my Amazon order?" tool.

```bash
clibo packages add "Amazon" -t TBA123 -c amazon -e "in 2 days"
clibo packages pending                          # late packages first
clibo packages pending --late                   # only the late ones
clibo packages received 1                       # mark delivered
clibo packages update 2 -e "in 5 days"          # ETA pushed
```

## Documents that quietly expire

```bash
clibo documents add Passport -e "March 15 2030" -k passport -# AB1234567
clibo documents add "Car insurance" -e "2027-01-01" -k insurance -# POL-9999
clibo documents expiring --days 90              # the warning view
clibo documents expired                         # already past
```

Late packages + expiring documents both surface in `clibo today` so you're
never blindsided.
