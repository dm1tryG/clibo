# 🧩 clibo skills

Each clibo tool ships a **micro-skill** here — a short `SKILL.md` describing
what the tool does and exactly how to call it. They are designed to be dropped
straight into an AI agent's skill set (the YAML frontmatter is compatible with
Claude Code Skills).

```
skills/
├── calorie/SKILL.md
├── water/SKILL.md
├── weight/SKILL.md
└── workout/SKILL.md   ... one per tool, growing toward 50
```

## Using a skill with an agent

Point the agent at `skills/<tool>/SKILL.md`. Every skill follows the same
shape: a command table, copy-paste examples, and a "For agents" section that
documents the `--json` output contract.

## The contract every tool keeps

- Every command accepts `--json` → clean JSON on stdout.
- Mutations (`log`, `add`, `edit`) return the affected record as JSON.
- Deletes return `{"deleted": ID}`.
- Errors go to stderr with a non-zero exit code.
- Data is stored locally in `~/.clibo/clibo.db` — no network, no accounts.
