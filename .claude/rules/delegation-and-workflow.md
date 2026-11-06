# Delegation and Workflow Rules

How to decompose work, delegate to sub-agents, and drive tasks to completion.

## Foreground only

Always spawn subagents in the foreground (`run_in_background` unset or false). Wait for each result before the next step.

## No-pause rule

The pipeline is automatic. Never ask "want me to delegate?", never present findings and wait for permission to act on them. When something needs doing, do it.

**Git actions are never automatic.** Commit, push, and branch creation always need the user's explicit go-ahead, per `git-safety.md`. Doing the work, running gates, and fixing findings stay automatic.

**Pause ONLY for:** missing credentials, a destructive action (see git-safety), genuinely ambiguous requirements where two readings would produce incompatible results, or the round cap.

**Ambiguity is not a reason to stop.** Choose the interpretation most consistent with existing code, record it as an assumption, and proceed. A documented assumption the human can correct beats a blocked pipeline.

## Delegation contract

A sub-agent has **no memory of the parent conversation**. Every delegation is a cold start. It must carry:

1. **Goal** — one sentence, unambiguous
2. **Context** — the spec and any prior agent reports, pasted in full, not referenced
3. **Deliverable** — the exact output shape expected back
4. **Boundary** — what the sub-agent must not touch

A delegation missing any of these produces a sub-agent that guesses. Guessing is the primary failure mode of multi-agent systems.

## Batching — stages are not todo items

**Group cohesive work into a SINGLE stage and review ONCE at the end.** Eight related edits must not become eight separate delegations — that multiplies turnaround for zero quality gain.

Split into separate stages ONLY when:
- Tasks are genuinely independent and parallelizing them buys speed (different files, no shared state)
- A task is risky enough to warrant isolated review

A todo item is what the human sees. A stage is how the work runs. They are decoupled — a 10-item todo list is frequently one stage.

## Parallel vs sequential

Fan out in a single batch when tasks share no data dependency:
- Multiple researchers answering different questions — always parallel, one question each
- Independent work touching disjoint files — parallel
- Code work and doc work on the same feature — parallel

Run sequentially when one task's output is the next one's input. Do not artificially serialize independent work — it's the largest source of wasted time.

**One question per researcher.** Two questions in one prompt produces two shallow answers instead of one deep one.

**Shared contract → define it before fanning out.** Parallel workers touching disjoint files can still share a type, a data shape, or a config value. Define that contract explicitly before delegating, and paste it into every parallel delegation. Two workers inferring the same contract independently is the classic parallel integration bug.

**Every parallel delegation must name what its siblings own.** Positive scope alone does not prevent overlap. State the negative scope explicitly: "Do NOT investigate X — that is task B's area."

## Context hygiene

- Pass forward findings, not transcripts. A researcher's 250-word report goes to the next stage; its tool calls do not.
- Never re-derive what a prior stage established. If a researcher cited `path:line`, the next stage reads that file directly — it does not re-search for it.
- Cite `path:line` everywhere. Uncited claims are unverified.

## Verify, do not recall

Before any agent uses, reviews, or plans around a Switch API or protocol detail: read the Switch docs via the `switch-docs` MCP, or read the relevant file in the `sandbox-quantum/switch` repo directly. Do NOT guess at API shapes, protocol details, or config formats.

A confident answer built on a stale assumption is worse than "I don't know" — it costs a full round to discover.

## Memory discipline

- The `memory-updater` agent owns all knowledge-graph writes. No other agent writes to memory.
- **Never call `read_graph`** — it dumps the entire graph and destroys the context window. Use `search_nodes` and `open_nodes` only.
- **Search with SHORT single keywords** (`bailiff`, `switch-trust`, `parity-court`). The memory server does whole-string substring matching — a long phrase matches nothing.
- Delegate to `memory-updater` only when the work produced a fact a future session would pay to rediscover: a root cause, an architectural decision, a non-obvious constraint, a correction to something the graph gets wrong.
- **Skip it for routine work.** A config tweak, a small fix, a doc update following an existing pattern — these produce no durable fact. Writing nothing is a valid, common outcome.

## Escalate to the human when

- A sub-agent reports scope creep beyond the spec's blast radius
- An architectural choice has no clear precedent in the codebase
- Anything destructive is required (deleting files, force push, schema change)
- Genuinely ambiguous requirements where two readings would produce incompatible architectures
- The same approach has failed twice — step back and rethink rather than retry

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| One stage per todo item | 8 delegations for 8 related edits — pure overhead |
| Asking permission mid-loop | Turns an automatic pipeline into a manual one |
| Recalling a Switch API instead of reading the docs | Confidently wrong code, costs a full round |
| Skipping memory-updater on a genuinely durable fact | The next session rediscovers it at full price |
| Running memory-updater on routine work | Fills the graph with noise that crowds out real facts |
| Re-spawning a failed stage with unchanged instructions | Same input, same failure. Narrow it, re-aim it, re-route it, or escalate. |
| Trusting a sub-agent's summary without artifacts | A stage that went wrong and one that went right arrive looking identical |
