---
applyTo: "**"
---

# Git Safety

**Standing instruction: never commit, push, or create branches without explicit permission from the user.**

## Rules

1. **Never run `git commit` without the user saying to commit.** Propose the commit message and list the files to stage. Wait for approval.
2. **Never run `git push` without the user saying to push.** Confirm the branch and remote first.
3. **Never commit to `main` directly.** All work goes on feature branches per `CONTRIBUTING.md`.
4. **Never use `git push --force`, `git reset --hard`, `git clean -f`, or `git branch -D`** without explicit permission and an explanation of what will be lost.
5. **Never run `git add .` or `git add -A`.** Stage specific files by name.
6. **Never amend a pushed commit** without permission. Prefer a new commit.
7. **Never skip pre-commit hooks** (`--no-verify`) unless the user explicitly asks.

## Before every commit

Ask the user:
- "Ready to commit? Here's what I'd stage: [list files]. Proposed message: [message]. OK?"

## What you CAN do without asking

- `git status`, `git diff`, `git log` — read-only operations are always fine
- `git stash` — non-destructive, reversible
- Creating a file or editing a file — that's your job

## What requires permission

- Any `git commit`
- Any `git push`
- Any `git branch` creation
- Any destructive git operation
- Any changes to `.gitignore`
