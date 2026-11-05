---
name: remember
description: "Saves a durable fact to the knowledge graph by delegating to the memory-updater agent. Use when the user invokes /remember or asks to store a fact, decision, or root cause."
---

# Save a fact via the memory-updater agent

Delegate to the `memory-updater` custom agent with the `task` tool and `mode: "sync"`. Pass the
text the user typed after `/remember` verbatim as "What to save".

The memory-updater decides whether the fact is durable. If it is not, it skips it and says why.
Do not write to the knowledge graph yourself.
