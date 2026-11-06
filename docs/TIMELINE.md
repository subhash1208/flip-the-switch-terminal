# Timeline and Work Split

Team: Terminal (Subhash, Santhan, Vatsav, Hashwanth)
Hackathon: Flip the Switch (Nov 4–7, 2026). Official deadline: Nov 7, 11:59 PM IST.

This file tracks status, owners, and what is left. The idea and the 8-step flow live in [`docs/PARITYCOURT.md`](PARITYCOURT.md). The earlier Nov 4–7 schedule was written before that idea was revised, and it has been replaced by this file.

## Status

**As of Nov 7, 2026, 01:30 IST (about 22 hours to the deadline).** The offline core is built and verified on Subhash's Windows PC: the `bailiff/` package, 572 passing pytest tests (about 94% branch coverage), strict mypy and ruff clean, and `python -m bailiff.demo --offline`, which replays 4 of 4 steps on canned fixtures (labelled SIMULATED). Live mode is merged to main and has run once against Switch 0.31.0 with scripted Alice and Bob. The Docker judge path passes (`python scripts/judge.py`, 8 of 8) and CI is 8 jobs, all green. Real Claude Code agents in the room (in progress) and the demo video are not done.

| Name | Role | Machine |
|------|------|---------|
| **Subhash** | Team lead; Bailiff, integration, submission. Boss: merges PRs and decides when the repo goes public. | Windows |
| **Santhan** | Developer; Mac host for Alice and the recording | macOS |
| **Vatsav** | Developer; Docker and the judge path | Windows |
| **Hashwanth** | Developer; docs review and the social post | Windows |

Owner "Subhash" means Subhash with his AI coding agents, unless noted.

---

## Status by item

Owner is Subhash with his AI coding agents unless noted.

### Done

| Item | Notes |
|------|-------|
| `bailiff/` Python package | Allow-listed probes, secret redaction, fingerprint and diff, ablation planner and classifier, receipt build/validate/replay, WebSocket transport with pong-and-cursor, reconnect and `taken_over` handling, Bailiff agent loop, scripted alice and bob agents, in-process fake room |
| Tests and checks | 572 pytest tests pass, about 94% branch coverage; mypy strict and ruff clean |
| Live mode (`python -m bailiff.demo --live`) | Merged to main. Registers pc-live-bailiff, pc-live-alice and pc-live-bob, runs one case over real WebSockets against Switch 0.31.0. Alice and Bob are scripted agents on canned fixtures (scripted-machine live transport). Transcript: `docs/evidence/transcript.txt` |
| Judge path in Docker | `python scripts/judge.py` 8 of 8 with Docker; container check 5 of 5 |
| CI workflow | 8 jobs, all green |
| Offline demo | `python -m bailiff.demo --offline` runs the whole story on canned fixtures (labelled SIMULATED), writes `receipt.json`, and replays 4 of 4 steps |
| Sample app | `sample-app/export-service`: Node 18.20.8 fails with `scopes.toSorted is not a function`; Node 22 passes. The TZ and NODE_OPTIONS decoys are harmless. |
| Research | About 80 rival repos scanned; Switch docs gotchas; blog research |
| Idea | ParityCourt revised and approved after two Opus 5.5 reviews. See `docs/PARITYCOURT.md`. |

### Written, not yet run

| Item | Notes |
|------|-------|
| `README.md` | Draft. Final pass pending. |

### In progress

| Item | Owner | Notes |
|------|-------|-------|
| Open PR against `main` (docs sweep on `docs/stale-sweep`) | Subhash | Boss merges |

### Not started

| Item | Owner | Notes |
|------|-------|-------|
| Install WSL2 and Docker Desktop on Subhash's PC, on the D: drive | Subhash; Boss supervises the admin install | Plan step 2 |
| Real Claude Code Alice and Bob in the room | Subhash | In progress. Not claimed done. |
| Judge command and `JUDGES.md` | Subhash | |
| Privacy (PII) masking | Subhash | Planned. See `docs/PARITYCOURT.md`, Privacy. |
| Property-based tests on redact and parsers | Subhash | |
| Mutation tests on pure modules (cosmic-ray, 1 h box) | Subhash | |
| Ponytail lean-code review (45 min) | Subhash | |
| Final README | Subhash; Hashwanth proofreads | Video link added after recording |
| Demo video, 80–150 s | Santhan records on his Mac; Subhash narrates | Recording slot: Nov 7, 10:00–12:00 IST |
| Optional blog post | Unassigned | Only if time remains |
| #HowISwitch post | Hashwanth | Draft text |
| Repo made public | Boss | Target no later than Nov 7, 18:00 IST. Private until then. |

---

## Plan: Nov 6, 17:00 IST to Nov 7, 20:00 IST

Times are planned estimates, not commitments. The only fixed slot is the recording. Steps keep the approved order. If behind, drop from the bottom: the blog first, then the mutation tests and the ponytail review.

| Time (IST) | Step | Owner | Gate or done when |
|------------|------|-------|-------------------|
| Nov 6, 17:00–18:00 | 1. Review, commit, push to `feature/subhash`, open PR | Subhash | PR open; Boss merges |
| Nov 6, 18:00–20:00 (est.) | 2. Install WSL2 and Docker Desktop on the D: drive | Subhash; Boss supervises the admin install | Docker runs on Subhash's PC |
| Nov 6, 20:00–02:00 (est.) | 3. Live mode against a self-hosted Switch (about 6 h) | Subhash | Go/no-go at hour 2 (about 22:00). Go = one full case runs over the real WebSocket. No-go fallback: not yet decided; Boss decides. |
| Nov 7, 02:00–05:00 (est.) | 4. Judge command, `JUDGES.md`, CI | Subhash; Vatsav runs the judge path | Judge path runs from one command |
| Nov 7, 05:00–08:00 (est.) | 5. Privacy (PII) masking | Subhash | Masking tests pass |
| Nov 7, 08:00–09:30 (est.) | 6. Property tests on redact and parsers | Subhash | Tests pass |
| Nov 7, 09:30–10:00 | Recording setup: Mac charged, Claude Code logged in, Docker and Switch running | Santhan | Santhan checklist below |
| Nov 7, 10:00–12:00 | 8. Demo video recorded on Santhan's Mac | Santhan records; Subhash narrates | Recording exists |
| Nov 7, 12:00–13:30 (est.) | 7. Final README; add the video link | Subhash; Hashwanth proofreads | README links the video |
| Nov 7, 13:30–14:30 (est.) | 9a. Mutation tests (cosmic-ray, 1 h box) | Subhash | Run complete |
| Nov 7, 14:30–15:15 (est.) | 9b. Ponytail lean-code review (45 min) | Subhash | Review complete |
| Nov 7, 15:15–18:00 | Video cut and upload (not in the approved plan; owner to confirm); Wispr screenshot; 10. Optional blog, only if time remains | Subhash; owners to confirm | Video playable from the README |
| By Nov 7, 18:00 | Repo public (target) | Boss | Repo clones without login |
| Nov 7, 18:00–20:00 | Final review and submission | Subhash, all | ParityCourt submitted to Track 01 |

---

## Per-person checklists

### Santhan (macOS)

You need a real Claude Code login on the Mac. The repo is private, so you need collaborator access first.

- [ ] Install Docker Desktop and Switch Console.
- [ ] `git clone` the repo, then `git checkout main`.
- [ ] Run `python -m bailiff.demo --offline` and send the full output to Subhash. Use the Python version in `pyproject.toml`.
- [ ] Confirm Claude Code is logged in on the Mac. In the recording, this is Alice.
- [ ] Block Nov 7, 10:00–12:00 IST for the recording. Bring the Mac charged.

### Vatsav (Windows, Docker)

- [ ] `git pull` on `main`.
- [ ] Install Docker Desktop (WSL2 backend, as on Subhash's PC).
- [ ] Run `python scripts/check_judge_path.py`, or run `docker compose -f deploy/docker-compose.yml run --rm bob` and then `docker compose -f deploy/docker-compose.yml run --rm alice`. Send the full output to Subhash.
- [ ] Expected, unverified until run: the Bob container (Node 18) fails with `scopes.toSorted is not a function`, and the Alice container (Node 22) passes. Report what actually happens.
- [ ] Report whether the pinned image digests pull on your machine, and any architecture-specific digest problem (the multi-arch digest question).

### Hashwanth (Windows)

- [ ] Proofread `README.md` and `docs/PARITYCOURT.md` for clarity and typos.
- [ ] Fix typos in a PR to `main`, committed from your own account.
- [ ] Draft the #HowISwitch post text. The tags are listed in `docs/PARITYCOURT.md`, Prize Stacking.

## How to help (if you are idle)

- Review an open PR against `main`. Comment; do not merge.
- Test the README from a clean clone, on a machine that has not run this project before. Note every step that fails.
- Rehearse the demo walkthrough with a timer. Target 80–150 s. Beats: the approval card, a refused non-owner action, the culprit isolated, the replay.

## Rules

- Never push to `main`. Open PRs against `main`.
- Boss (Subhash) merges PRs.
- No secrets in the repo, in commits, or in chat. That includes API keys, tokens, and Claude Code login details.
- Branch and commit policy: see `CONTRIBUTING.md`.

---

## Submission checklist

- [ ] Repo public by Nov 7, 18:00 IST (target; Boss decides). Official deadline: Nov 7, 11:59 PM IST.
- [ ] Verify the public repo clones without login.
- [ ] Short demo video (80–150 s), linked from the README.
- [ ] README with a "How Switch is used" section.
- [ ] Wispr Flow scorecard screenshot. Owner: not yet assigned (Boss to confirm).
- [ ] Optional blog post, only if time remains.
- [ ] Star the Switch repo (`sandbox-quantum/switch`).
- [ ] Submit ParityCourt to Track 01.

No slide deck. The official submission is a public repo, a short demo video, and a README.

Links (hackathon page, Switch repo, Switch Trust CLI, docs) are in the Key Links section of [`docs/PARITYCOURT.md`](PARITYCOURT.md).
