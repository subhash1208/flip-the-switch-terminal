# Contributing — Team Terminal

Rules for working on this repo. Everyone follows these. No exceptions.

---

## Branching

**Never push directly to `main`.** Ever.

1. Create a feature branch for every piece of work:
   ```
   git checkout main
   git pull
   git checkout -b feature/<your-name>/<short-description>
   ```
   Examples:
   - `feature/subhash/bailiff-agent`
   - `feature/santhan/sample-app`
   - `feature/vatsav/docker-setup`
   - `feature/hashwanth/pytest-suite`

2. Push your branch:
   ```
   git push -u origin feature/<your-name>/<short-description>
   ```

3. Open a Pull Request on GitHub when your work is ready for review.

4. At least **one other team member** must review and approve before merging.

5. Merge via GitHub PR — do not merge locally with `git merge`.

---

## Branch Naming

Format: `feature/<your-name>/<short-description>`

| Good | Bad |
|------|-----|
| `feature/santhan/sample-app-bugs` | `my-branch` |
| `feature/vatsav/docker-compose` | `fix` |
| `feature/hashwanth/switch-trust-tests` | `test123` |
| `feature/subhash/bailiff-loop-breaker` | `stuff` |

For bug fixes during the build: `fix/<your-name>/<what-broke>`

Example: `fix/vatsav/ssh-bridge-ip`

---

## Commits

- Write clear commit messages. Say what changed and why.
- Keep commits focused — one logical change per commit.
- Don't commit generated files, node_modules, __pycache__, .env, or secrets.

Good:
```
Add Bailiff SSE event parser with loop breaker (6-turn cap)
```

Bad:
```
updates
```
```
fixed stuff
```

---

## Pull Requests

1. **Title:** Short and clear. Under 70 characters.
   - Good: `Add sample app with 3 planted bugs`
   - Bad: `santhan's changes`

2. **Description:** Briefly explain:
   - What this PR does
   - How to test it
   - Anything the reviewer should know

3. **Keep PRs small.** One feature or fix per PR. Don't pile 5 unrelated changes into one PR.

4. **Link to the work:** If your PR corresponds to a task in `docs/TIMELINE.md`, mention it.

5. **Review turnaround:** When someone requests your review, respond within 2 hours during build days (Nov 4–7). Don't block your teammates.

---

## Code Review

When reviewing someone's PR:

- **Test it.** Pull the branch and run it if possible.
- **Be specific.** "This might break if the SSH container isn't running" is useful. "Looks good" without checking is not.
- **Approve or request changes.** Don't leave a PR hanging.
- **Be respectful.** We're on the same team under time pressure.

---

## What NOT to Commit

These must never end up in the repo:

- `.env` files with real API keys or passwords
- Wispr Flow credentials
- Switch Console auth tokens
- Personal SSH keys
- Employer code, data, or tools
- node_modules/
- __pycache__/
- Large binary files (videos, images over 5MB)

The `.gitignore` handles most of this, but double-check before staging with `git diff --staged`.

---

## Daily Workflow (Nov 4–7)

1. **Start of day:** Pull latest main.
   ```
   git checkout main
   git pull
   ```

2. **Create your branch** for the day's task (or continue on an existing one).

3. **Push often.** Don't sit on uncommitted code for hours. Push at least every 2 hours so others can see progress.

4. **Open PR when ready.** Ping the team in chat for review.

5. **After merge:** Delete your branch and pull main again before starting the next task.
   ```
   git checkout main
   git pull
   git branch -d feature/<your-name>/<old-branch>
   ```

---

## Conflict Resolution

If you get a merge conflict:

1. Pull latest main into your branch:
   ```
   git checkout your-branch
   git pull origin main
   ```
2. Resolve conflicts in your editor.
3. Test that everything still works.
4. Commit the resolution and push.

If the conflict is complex, message the team before force-resolving anything. **Never use `git push --force` or `git reset --hard` without team agreement.**

---

## Folder Ownership

Each person primarily owns certain folders. This reduces merge conflicts:

| Person | Primary Folders |
|--------|----------------|
| **Subhash** | `bailiff/`, `docs/` |
| **Santhan** | `sample-app/`, blog post file |
| **Vatsav** | `deploy/`, `justfile`, `README.md` |
| **Hashwanth** | `tests/`, `templates/` |

If you need to edit a file in someone else's folder, coordinate with them first or mention it in your PR description.

---

## Hotfix Process (Something Is Broken and Blocking Everyone)

If something is broken on main and blocking the team:

1. Create a `fix/<your-name>/<what>` branch.
2. Fix it.
3. Open a PR and ping the team with **"HOTFIX — blocking"** in the chat.
4. One person reviews ASAP and merges.

---

## Tools

Everyone should have:

- Git (configured with your personal GitHub account)
- Claude Code, Kiro, and/or Copilot
- Wispr Flow (active from Day 1)
- Docker Desktop (Vatsav primarily, but everyone should have it)
- Python 3.10+ (for Bailiff and tests)
- Node.js 22.13+ (for the sample app)
- Switch Console 0.40.1

---

## Questions?

If anything in this guide is unclear, ask in the team chat. Don't guess. We have 4 days and zero room for miscommunication.
