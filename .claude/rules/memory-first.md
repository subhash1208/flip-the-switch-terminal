---
title: Read Memory Before Non-Trivial Work
inclusion: always
---

# Check memory before you start, not after you're stuck

A durable fact the team already paid to discover — a root cause, an architectural decision, a non-obvious Switch constraint, a correction to something the docs get wrong — lives in the knowledge graph. Rediscovering it from scratch costs a full round. Reading it costs one search.

**Before beginning any non-trivial task, query memory first.** Non-trivial means: implementing or changing code, debugging, planning an approach, or answering a question about how something in this project works or was decided. Skip the lookup only for trivial one-offs (a typo fix, a formatting pass, a direct file read the user pointed you at).

## How to read — reuse the existing discipline

The retrieval rules already live in `delegation-and-workflow.md` under "Memory discipline." They bind here too. The essentials:

- **Never call `read_graph`.** It dumps the entire graph and destroys the context window. Use `search_nodes` and `open_nodes` only.
- **Search with SHORT single keywords** — `bailiff`, `switch-trust`, `parity-court`, `ablation`, `template`. The memory server does whole-string substring matching, so a long natural-language phrase matches nothing and produces a false "the graph is empty" result. If a search comes back empty, retry with a shorter keyword before concluding the fact isn't stored.
- **One broad search, then one batched `open_nodes`** — not a search per question. `open_nodes` takes an array; pass every name you want in a single call.

## Always load user preferences first

Every new session, before anything else, load the `user-preferences` node: `open_nodes(["user-preferences"])`. It carries standing, owner-set interaction rules that apply to every session. As of now those are: **the assistant is named Hex and refers to itself as Hex**, and **the user is addressed as Boss**. Honor them for the whole session. This load is mandatory and is not a "non-trivial task" judgment call — it happens on every session regardless of what the work is.

## The loop

1. Load `user-preferences` (above) — always, first.
2. Pull the one or two keywords that name what you're about to touch.
3. `search_nodes` on the broadest one; skim the returned entities and relations.
4. `open_nodes` (batched) on anything that looks relevant.
5. Proceed, now grounded in what the team already knows.

If the search genuinely returns nothing after a short-keyword retry, say so and proceed — an empty graph on a fresh topic is normal, not a blocker.

## What this is not

- **Not a write instruction.** Only the `memory-updater` agent writes to memory. Reading first does not change that.
- **Not a reason to pause.** Reading memory is part of starting work, not a checkpoint to ask permission at. Do it and continue.
