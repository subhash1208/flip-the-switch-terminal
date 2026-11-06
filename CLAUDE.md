# flip-the-switch-terminal (ParityCourt)

Hackathon project (Flip the Switch, Nov 2026). Team Terminal. Python 3.11+.
Overview: see `README.md`.

## Layout
- `bailiff/`: the court-arbiter agent (Python)
- `sample-app/`, `tests/`, `scripts/`, `deploy/`, `docs/`

## Working rules
- Rules live in `.claude/rules/`. They load automatically.
- Agents live in `.claude/agents/`. The `planner` is the default agent for this repo.
- Read memory first: `open_nodes` on `user-preferences` and the relevant area (`bailiff`, `switch-trust`, `parity-court`). Use short keywords; never `read_graph`.
- Never commit, push, or branch without the user's explicit go-ahead (`.claude/rules/git-safety.md`).
- Never delete or reset without permission.
- Run all agents in the foreground. Never set `run_in_background` on the Agent tool, and do not use background agents.

## Switch platform
- Switch source repo: `<switch-repo>` (local clone path; set it on each machine). When it is not present, use the `switch-docs` MCP.
- Do not recall Switch API details from memory. Read the source or the docs first.

## Verify
- Python: `just check`, `just typecheck`, `just test`, or plain `python -m pytest` if `just` is missing.
