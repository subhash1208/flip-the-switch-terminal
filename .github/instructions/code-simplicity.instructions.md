---
applyTo: "**"
---

# Simple by Default

**The simplest implementation that is correct and complete wins.**

This is a hackathon project. Every line of code must earn its place. Overengineering is the enemy of shipping in 4 days.

## Structure has to earn its place

| Don't | Until |
|-------|-------|
| Extract a helper | There is a second call site |
| Add a parameter or options object | A caller actually passes something other than the default |
| Introduce an abstraction layer | Two concrete implementations exist and genuinely differ |
| Add a dependency | The standard library and what's already installed can't do it |
| Write a comment | The code cannot be made to say it itself |

## Patterns that keep it small

- **Return early.** Guard clauses beat nested if/else.
- **One source of truth.** Config values, constants, and shared types live in one place.
- **Derive, don't store.** A second variable that is a function of the first is two values waiting to disagree.
- **Already-installed before new.** Check what's in `requirements.txt` or `package.json` before adding a dependency.

## What "simple" never means

Simplicity governs the code you write, never the cases it must handle:

- **Error handling.** The Bailiff must handle SSE disconnects, malformed events, and agent timeouts gracefully.
- **Cleanup.** SSE connections and HTTP sessions must be closed properly.
- **Security.** Switch Trust guardrails and secret redaction are not optional complexity.
- **Tests.** The 25+ pytest tests are not overhead — they're what makes judges take the project seriously.

## Deliver in verifiable steps

Work in the smallest increments that each leave the project runnable. An interrupted session should cost one step, not a day's work. A large change that has never been tested is not progress.
