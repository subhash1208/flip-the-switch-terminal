---
title: Delegation and Workflow Rules
inclusion: always
---

# Delegation and Workflow Rules

Rules that apply to ALL agents in this workspace. Orchestration-specific logic (the review loop, batching strategy, escalation criteria, roster table) lives in the planner agent definition, not here.

## No-pause rule

The pipeline is automatic. Never ask "want me to delegate?", never present findings and wait for permission to act on them. When something needs doing, do it.

**Pause ONLY for:** missing credentials, a destructive action (see git-safety), genuinely ambiguous requirements where two readings would produce incompatible results, or the round cap.

**Ambiguity is not a reason to stop.** Choose the interpretation most consistent with existing code, record it as an assumption, and proceed.

## Delegation contract (for any agent spawning sub-agents)

A sub-agent has **no memory of the parent conversation**. Every delegation is a cold start. It must carry:

1. **Goal** — one sentence, unambiguous
2. **Context** — the spec and any prior agent reports, pasted in full, not referenced
3. **Deliverable** — the exact output shape expected back
4. **Boundary** — what the sub-agent must not touch

## Context hygiene

- Pass forward findings, not transcripts.
- Never re-derive what a prior stage established. If a researcher cited `path:line`, read that file directly.
- Cite `path:line` everywhere. Uncited claims are unverified.

## Verify, do not recall

This project works across two codebases:
- **This repo** (`flip-the-switch-terminal`) — hackathon project
- **Switch repo** (`D:\Projects\switch`) — upstream platform for Track 03 PRs

Before any agent uses a Switch API or protocol detail: read the Switch docs via the `switch-docs` MCP, or read the relevant file in the Switch repo directly. Do NOT guess at API shapes, protocol details, or config formats.

## Memory discipline

- The `memory-updater` agent owns all knowledge-graph writes. No other agent writes to memory.
- **Never call `read_graph`** — it dumps the entire graph and destroys the context window. Use `search_nodes` and `open_nodes` only.
- **Search with SHORT single keywords** (`bailiff`, `switch-trust`, `parity-court`). The memory server does whole-string substring matching — a long phrase matches nothing.
- Delegate to `memory-updater` only when the work produced a fact a future session would pay to rediscover.
- **Skip it for routine work.** Writing nothing is a valid, common outcome.
