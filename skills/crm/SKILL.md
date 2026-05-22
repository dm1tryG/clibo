---
name: clibo-crm
description: Manage contacts with the `clibo crm` CLI. Use when the user wants to add a contact, look someone up, record that they were in touch, or review their contacts.
---

# 👥 clibo crm

Contacts CRM. Local SQLite. Every command accepts `--json`.

## Commands

| Command | What it does |
|---|---|
| `clibo crm add NAME` | Add a contact (`-c` company, `-e` email, `-p` phone) |
| `clibo crm list` | List contacts (`-s` status, `-t` tag) |
| `clibo crm show ID` | One contact in detail |
| `clibo crm edit ID` | Edit a contact |
| `clibo crm touch ID` | Record that you contacted them |
| `clibo crm search QUERY` | Search name / company / email / tags |
| `clibo crm rm ID` | Delete a contact |
| `clibo crm stats` | Counts by status |

Status is `lead`, `active`, `customer` or `cold` (default `active`).

## Examples

```bash
clibo crm add "Anna Petrova" -c "Acme Inc" -e anna@acme.com -s customer
clibo crm touch 1
clibo crm search acme
clibo crm list -s lead
```

## For agents

```bash
clibo crm list --json
# -> [ { "id", "name", "company", "email", "phone", "status",
#        "tags", "last_contact", "last_contact_ago" } ]
```
