# Handoff for Subhash: non-coding work for the ParityCourt submission

Status as of Nov 6, 2026, 23:35 IST. Official deadline: Nov 7, 2026, 11:59 PM IST. Target: public repo by 18:00 IST (you decide).

**Warning:** the status table in `docs/TIMELINE.md` is stale. It is dated Nov 6, 17:15 IST and reports 132 tests and "4 of 4". Do not use it as status. Task 5 fixes it.

## 1. Read this first

You can start without asking Santhan anything. You need to make one decision:

- **Decide:** host Switch and the Bailiff on one cloud VM, so Hashwanth can join from his own laptop? Yes or no. (to be verified: the VM needs a public address and TLS.)

You also need one answer from Hashwanth (Task 6). Do not edit code under `bailiff/` or `tests/`. Start with Task 1.

## 2. The idea

ParityCourt is cross-machine bug forensics. "Works on my machine" becomes evidence. Two machines each run their own agent in one Switch room, and a custom arbiter, the Bailiff, runs the case. The core is cause isolation: the Bailiff compares both environments, then changes one variable on the failing machine to find the cause. Each owner approves probes on their own machine, and `receipt.json` lets `replay` re-run the result.

Lead with cause isolation. Receipts and replay are crowded (splitbrain, Flipside/gateplus, switch-notary, Countersign). Nobody else does environment drift.

The demo culprit is the Node major version: `scopes.toSorted is not a function` on Node 18, a pass on Node 22. The `TZ` and `NODE_OPTIONS` decoys are harmless.

Track 01, Best Business Workflow. Judging: Use of Switch 30%, Technical execution 25%, Creativity 25%, Presentation 20%.

## 3. Decided and open

**Decided on Nov 6:**

- Pull requests go to `main` only. You merge. Nobody pushes to `main`. This overrides the `feature/subhash` PR rule in `docs/TIMELINE.md` and `CONTRIBUTING.md`.
- The recorded demo uses a real Bob. Alice is Santhan's Claude Code on his Mac, through Switch Console. Bob is a second Claude Code agent owned by Hashwanth, ideally on WSL2 Ubuntu with Node 18 installed through nvm. (to be verified: Switch Console runs on WSL2.)
- The scripted Bob stays as the fallback and as the keyless judge path.
- Kiro and Copilot cannot be Switch room agents. Switch Console runs only Claude Code, Codex, Antigravity, Cursor and OpenCode. Use Kiro and Copilot to write docs and code only.
- The Bailiff is a separate Python process, started with `python -m bailiff.agent`. It is not a Console agent. It can run on any machine with outbound access to the Switch server.

**Open:** cloud VM hosting (section 1); Hashwanth's availability (Task 6); owner of the Wispr Flow screenshot (not assigned); owner of the optional blog post (not assigned).

## 4. Coding status (read only)

- The offline core is done. 558 pytest tests pass on Santhan's Mac. ruff, mypy strict and bandit are clean. `scripts/judge.py` passes 8 of 8, including the Docker check.
- The offline demo replays 5 of 5 steps. The filesystem-case difference (APFS vs ext2/ext3) is real but is not the cause.
- Live mode works against a real Switch 0.31.0 server on Santhan's Mac, but only with a temporary workaround.
- **Known defect:** Switch puts an opaque Matrix id in `payload.sender` and the agent name in `payload.sender_name`. The Bailiff compares the wrong one, so the live case stalls. A fix and an independent review are in progress.
- Santhan's work is not pushed. You cannot see the live code until he commits, pushes, and gives the go-ahead.
- GitHub CI jobs `actionlint` and `security` failed on the first run and do not reproduce locally. Real logs are needed (`gh auth login` is pending).
- Mutation tests are not run.

## 5. Your tasks

Work in this order. Each task has acceptance criteria.

**Task 1. README final pass (`README.md`).**

- Keep "How Switch is used" as the first section. Add how to connect agents, set up the channel, and run it.
- Fix line 16. It says Bob is Codex on Ubuntu over SSH. Rewrite it to match section 3.
- Change "4/4" on line 81 to "5/5".
- Remove or update the live-mode lines (84, 96, 216) only after Santhan confirms live mode passes.
- Label every unverified claim `(to be verified)`. Add the demo video link at the top after recording.

Acceptance: no "Codex on Ubuntu"; no "4/4"; live-mode lines unchanged until Santhan confirms.

**Task 2. Demo storyboard and narration (new file: `docs/DEMO-STORYBOARD.md`, proposed name).**

Length: 80 to 150 seconds. Beats, in order:

1. The case opens.
2. A real approval card appears from Alice's Claude Code.
3. A refused non-owner action: Bob presses Allow on Alice's probe, and Switch refuses. (to be verified: live test.)
4. The culprit is isolated: the Node major version. The filesystem-case difference is shown as real but not causal.
5. `replay` prints the same outcomes.
6. Closing line: "Delete Switch, and these agents can't see each other's machines." (`docs/PARITYCOURT.md:418`)

Optional 10-second bonus: the case-only import works on APFS and fails on Linux.

Recording: Nov 7, 10:00 to 12:00 IST, on Santhan's Mac. Fallback: the offline demo, which must show SIMULATED on screen.

Acceptance: one line of narration per beat; read aloud within 80 to 150 seconds.

**Task 3. Proofread `JUDGES.md`.**

Acceptance: every command matches `README.md` Quick start, and every Docker step says it needs Docker.

**Task 4. Submission package.**

- Make the repo public by 18:00 IST. Acceptance: a clean clone works without login.
- Link the demo video at the top of the README. Acceptance: the link plays.
- Attach the Wispr Flow Insights screenshot to the submission.
- Star `sandbox-quantum/switch`.
- Submit ParityCourt to Track 01 before 11:59 PM IST.
- Hashwanth posts #HowISwitch, tagging the accounts listed in `docs/PARITYCOURT.md` (line 382).
- Optional blog, lowest priority. Outline: framing, numbered list of what it does, what went wrong, what it does not do.

**Task 5. Fix stale docs (after Task 1).**

Search the repo for each string below. Fix every hit, or label it `(to be verified)`:

- `feature/subhash` in `docs/TIMELINE.md` and `CONTRIBUTING.md`: change the PR target to `main`.
- Test counts: `132` (TIMELINE), `445` (README and PARITYCOURT), `558` (latest measured). Use one figure.
- `4 of 4` and `4/4` in TIMELINE and README.
- `Codex` in README, `docs/PARITYCOURT.md` and `docs/PRIZES.md` (line 90). Match section 3.
- Rewrite the `docs/TIMELINE.md` status table.

Acceptance: each search returns no stale hit.

**Task 6. Ask Hashwanth about Bob.**

Ask three questions in team chat:

1. Can you be online Nov 7 from 09:00 to 12:00 IST?
2. Can Switch Console run in WSL2 Ubuntu on your PC, with Node 18 through nvm?
3. Is Claude Code logged in on your machine?

Acceptance: a yes or no to each. Do not share login details.

## 6. Rules and honesty

- The offline demo is SIMULATED. Say so on screen.
- Custom Python agents cannot raise Switch approval cards. Only Claude Code and Codex agents get real cards. The scripted agents' owner gate is a targeted message plus an addressed reply. (to be verified.)
- Approval identity is a participant name, not a signed identity.
- Never use the `anyone` addressing policy on a ParityCourt agent.
- Privacy masking is regex and checksum only. Names in free text are not masked.
- No secrets in commits, chat or docs. This includes API keys, registration keys and login details.
- Stage files by explicit path. Never run `git add .` or `git add -A`. Never use `--no-verify`.
- Commit and push only after Santhan says so. Do not commit `.claude/agents/*.md` or `switch-hackathon-knowledge-graph.jsonl` unless he says so.

## 7. Commands and file map

Copy commands from `README.md` Quick start, which is their source. Do not copy them elsewhere.

- `python -m pip install -e .`: install.
- `python scripts/judge.py`: the one-command check (8 checks). The Docker check is skipped without Docker.
- `python -m bailiff.demo --offline`: offline demo, SIMULATED.
- `just judge-check`: judge-path check. Needs Docker.
- `python -m bailiff.replay receipt.json --docker`: replay. Needs Docker.

Files:

- `docs/PARITYCOURT.md`: the idea, the 8-step flow, risks.
- `docs/TIMELINE.md`: work split. Status table is stale.
- `JUDGES.md`: judge instructions.
- `CONTRIBUTING.md`: branch and commit rules.
- `bailiff/`, `tests/`: code. Do not edit.
- `docs/evidence/`: live evidence (`receipt.json`, `transcript.txt`) after Santhan pushes.
