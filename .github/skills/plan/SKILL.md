---
name: plan
description: "Hands a task to the planner custom agent for structured planning and delegation before any code is written. Use when the user invokes /plan, or asks for a plan, breakdown, or approach. Not for trivial one-file edits."
---

# Plan a task via the planner agent

Delegate to the `planner` custom agent with the `task` tool and `mode: "sync"`.

Pass the text the user typed after `/plan` to the planner verbatim. If it is empty, ask what
should be planned before delegating.

Do not plan or implement the task yourself. Relay the planner's plan and progress without
editorialising.
