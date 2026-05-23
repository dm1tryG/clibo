# 🤝 Relationships & career

Tools covered: `crm`, `network`, `followup`, `meetings`, `birthdays`, `gifts`,
`brag`, `cv`, `jobs`, `leads`, `clients`.

## Personal CRM

```bash
clibo crm add Anna -c Acme --role "Head of Design"
clibo crm note Anna "Allergic to peanuts"     # append context
clibo crm list
clibo crm show Anna
```

## Networking log (people you met)

```bash
clibo network add Sarah -c "Stripe" -p PyCon -x "interested in CRDTs"
clibo network search "PyCon"
clibo network stats
```

## Follow-ups

```bash
clibo followup add Anna --due "in 2 weeks" --reason "introduce Bob"
clibo followup due                           # overdue + due-soon
clibo followup done 1
```

## Meeting notes

```bash
clibo meetings add "Project Phoenix sync" -a "Anna,Bob" --notes "Key decision: rewrite in Rust"
clibo meetings list --days 7
```

## Birthdays + anniversaries

```bash
clibo birthdays add Dad -d "March 12"             # month-name forms work
clibo birthdays add Mom -d "1965-04-15"           # full ISO too
clibo birthdays upcoming --days 30
clibo birthdays today
```

## Gifts

```bash
clibo gifts add Anna --idea "Book on type design" --occasion birthday
clibo gifts log Anna --idea "Bookstore voucher" --given $(date +%F)
```

## Career

```bash
clibo brag add "Shipped auth refactor under budget" -i "Saved 2 weeks vs estimate"
clibo brag stats                                   # great review prep

clibo cv add "Staff Engineer" -o "Acme" -s 2023-06 -k job
clibo cv achieve "Staff Engineer" "Led migration to event-driven architecture"

clibo jobs add Stripe "Senior Engineer" -s applied
clibo jobs update 1 -s interview
clibo jobs list --active
```

## Freelance

```bash
clibo clients add "Acme Corp" -r 150               # 150/hr
clibo clients log Acme 4 -n "API integration work"
clibo invoice add "Acme Corp" -a 1200 -d "in 14 days"
clibo invoice pay 1                                # mark received
clibo leads add "BigCorp" -e "alice@bigcorp.com"   # sales pipeline
```

## Cross-tool questions

```bash
clibo search "Acme"                                # across crm, jobs, invoice, ...
clibo network stats
clibo followup stats
```
