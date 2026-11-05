---
name: review
description: "Runs a bug-hunt review of the current uncommitted changes via the reviewer custom agent, which returns VERDICT GREEN or RED with findings ranked by severity. Use when the user invokes /review or asks for a code review. Read-only."
argument-hint: "[files, branch, or area to review]"
disable-model-invocation: true
---

# Bug-hunt review via the reviewer agent

1. Collect the changes: `git --no-pager status` and `git --no-pager diff`. Scope them to any
   files or area the user named after `/review`.
2. Delegate to the `reviewer` custom agent with the `task` tool and `mode: "sync"`. Pass the
   diff and ask for logic errors, edge cases, security issues, resource leaks, and violations of
   existing conventions. Tell it to report only confident findings and to end with `VERDICT: GREEN`
   or `VERDICT: RED`.
3. Relay the findings verbatim. If the verdict is RED, ask whether to hand them to the
   `implementer` agent.
