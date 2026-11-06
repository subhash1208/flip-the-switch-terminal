# Flip the Switch submission kit: ParityCourt

**Status: DRAFT, written 2026-11-07 for Subhash. Not submitted.**

Track 01, Best Business Workflow. Judging: Use of Switch 30%, Technical execution 25%, Creativity and impact 25%, Presentation 20%.

Paste-ready text is in fenced blocks. Items the verified facts do not settle are listed under "Still to confirm" at the end. Resolve or delete them before pasting.

---

## 0. Submission requirements

From `docs/PRIZES.md`:

- **Track 01 entry:** ParityCourt. Judged on the four criteria above.
- **Demo video:** target 80–150 seconds (`docs/PARITYCOURT.md`, rule 10; `docs/STORYBOARD.md` plans 100–140 seconds). `docs/PRIZES.md` says "2:30 video", which is the 150-second upper bound. Include a 5-second picture-in-picture clip of Wispr dictation. The accepted video host is in "Still to confirm".
- **Code with Wispr (side prize):** install Wispr Flow, dictate the build, screenshot the Insights tab (words dictated, time saved, apps used), and attach the screenshot at submission.
- **Best Blog (optional):** publish on Dev.to, Hashnode, Medium or your own site, and link it in the submission.
- **#HowISwitch (optional):** post on X and/or LinkedIn with `#HowISwitch`, tagging `@switchagents_ai`, `@WeMakeDevs` and `@DevToolsAcademy`.

Not stated in `docs/PRIZES.md`, so they are in "Still to confirm" at the end:

- Whether a public repo and a README that explains how Switch is used are required.
- Whether starring `sandbox-quantum/switch` is required. It appears only in `docs/TIMELINE.md`.
- The submission form and its fields.

---

## 1. Name and tagline

Project name: **ParityCourt**

```text
ParityCourt: each machine's agent testifies in one Switch room, and a referee isolates the cause.
```

---

## 2. Short description (form, 300 words max)

```text
ParityCourt settles "works on my machine" with evidence. A bug case runs in one Switch room with three participants: @alice-claude on Alice's machine, Bob's agent on the failing machine, and @bailiff, a custom Python referee that runs the case.

Switch is the foundation, not a thin wrapper. The room is the case file, and the Bailiff creates the room document, because only the agent that creates a room document may edit it. Each agent has its own connection id and receives room events over a WebSocket; it answers through Switch's HTTP API. Each owner approves probes on their own machine. Delete Switch and the agents cannot see each other's machines or share a case file.

What we built is the Bailiff, a deterministic referee, not an LLM:
- It runs only allow-listed probes, such as uname -a, node -v and env.
- It masks secrets and personal data before anything reaches the room or the receipt.
- It runs one-variable ablation: it changes one variable on the failing machine at a time and re-runs the failing test.
- It writes receipt.json, which records every step with its image, environment, command and outcome. replay re-runs those steps in Docker.

The sample case is a Node version bug. scopes.toSorted is not a function on Node 18 and passes on Node 22. The TZ and NODE_OPTIONS differences are decoys in this sample.

The offline demo runs the full flow on canned output, with no keys and no Docker. The live Switch path ran against a real Switch 0.31.0 server. The recorded run uses scripted Alice and Bob.
```

---

## 3. What is real vs scripted

What is real: the Bailiff's WebSocket and HTTP transport to a self-hosted Switch 0.31.0 server (`python -m bailiff.agent`), merged to main as PR #9 (commit 31d7c57). It ran against a real Switch 0.31.0 server; the transcript is `docs/evidence/transcript.txt`. Also real: the redaction, fingerprint diff, ablation planner, receipt writer and replay code, and the Node 18 vs Node 22 failure in the sample app.

What is scripted: the offline demo (`python -m bailiff.demo --offline`) runs an in-memory room with canned agent output, and it must say SIMULATED on screen. In the recorded live run (`docs/evidence/transcript.txt`), Alice and Bob are scripted: every approval reads `auto-approved (scripted agent, no human)`.

Bob's handle is `@bob-codex`, a handle only. A real Bob would run Claude Code, which is in progress. Until then, the fallback is the scripted Bob container on Node 18. Real Claude Code Alice and Bob are not claimed anywhere in this kit.

Tick a box only if the demo video shows that agent real. The transcript shows scripted agents, so leave both unticked for it:

[ ] real Alice  [ ] real Bob

---

## 4. How to reproduce in 3 commands

Source: the Quick start in `README.md`. Needs Python 3.11 or later.

```text
python -m pip install -e .
python scripts/judge.py
python -m bailiff.demo --offline
```

- Command 2 runs 8 checks and ends in `JUDGE RESULT`. It exits 1 if any check FAILs. Check 8 runs the Docker judge path and SKIPs when Docker is not on PATH.
- Command 3 is the offline demo. It is SIMULATED and writes `receipt.json` to the current directory.

---

## 5. Stats

- **579 tests**, from `python -m pytest -q --cov=bailiff --cov-branch` (572 on main, plus 7 new preflight tests).
- **94% branch coverage**, against a CI gate of 90%.
- **8 CI jobs, all green** on main, run 42278458185: security scans; lint, types and tests on Python 3.11 and 3.12; node 22 expect-pass; node 18 expect-fail; live judge path (Docker); actionlint; ci-ok.
- **`scripts/judge.py`: 8/8 with Docker.** Without Docker: 7 PASS and 1 SKIP (check 8).
- **Docker container check: 5/5**, run locally and in CI.

---

## 6. Honest limits

From the "Honest limits" section of `README.md`, and the privacy limits. For scaling limits, see "Scaling and limits" in README.md.

- The offline demo is SIMULATED: an in-memory room, scripted agents and canned output.
- Live mode ran against a real Switch 0.31.0 server, but the recorded machine agents are scripted. Real Claude Code Alice and Bob are in progress. See section 3.
- The first GitHub CI run failed `actionlint` and `security` (per `docs/HANDOFF-SUBHASH.md`). Run 42278458185 on main is green.
- Approval identity is the participant's name, not a signed identity. An attestation records who said yes. It is not a cryptographic signature.
- The Bailiff does not refuse an approval from someone who is not the probe owner. Owner-refusal is not implemented.
- Custom Python agents cannot raise Switch approval cards (unverified). Real approval cards appear only for Claude Code and Codex agents. The scripted agents' owner gate is a targeted message plus an addressed reply.
- Switch has no loop breaker or dual sign-off. The turn cap is Bailiff code and is optional.
- Probes are allow-listed. Agents never read `.env` files.
- The judge path reproduces a Node version bug, not the filesystem case bug (`SqlAuthGuard` vs `sqlAuthGuard`). The case bug is real on case-sensitive filesystems but is not the cause.
- Only one test is verified. A passing re-run of the failing test is not proof that the fix is correct beyond that test.
- No ablation, no verdict. If nothing could be ablated, the receipt is INCONCLUSIVE. A suspect whose value is masked is not ablated.
- Privacy masking is regex and checksum only. It is not a security review. It does not mask:
  - names or street addresses in free text, non-Latin scripts, or base64-embedded personal data;
  - bare national phone numbers (only `+` E.164 is masked);
  - `user@host:path` SSH remotes, or dash-style hostnames such as `ip-10-0-1-5`;
  - PEM bodies on later lines, YAML block scalars, unquoted numeric JSON secrets, `docker login -p X`, or `mysql -pX`.
- Whether Switch's own guardrail masks real agent replies is unverified.

---

## 7. Optional extras

### #HowISwitch post (optional, 280 characters max)

```text
We built ParityCourt: one Switch room, an agent on each machine, and a referee that isolates a cross-machine bug one variable at a time and writes a replayable receipt.json. #HowISwitch @switchagents_ai @WeMakeDevs @DevToolsAcademy
```

Post only after the demo video link works. The recorded live run uses scripted agents, and the offline run is SIMULATED.

### Blog outline (OPTIONAL, lowest priority)

Owner not assigned (see "Still to confirm"). Publish only if time remains.

- **Framing:** "works on my machine" is an evidence problem, and a referee agent in a Switch room is one answer to it.
- **What it does:** the numbered flow. Fingerprint both machines, produce a masked environment diff, run one-variable ablation, and replay `receipt.json`.
- **Building a custom Switch agent:** WebSocket in, HTTP out, one `POST /agents` registration per agent. The Bailiff is the worked example.
- **What went wrong:** the wrong sender field, and the filesystem case difference that looks like the cause but is not.
- **What it does not do:** the limits in section 6, and the offline demo is simulated.

---

## 8. Submission-day checklist (IST, Nov 7)

Times are from the spec and `docs/TIMELINE.md`. Hard deadline: Nov 7, 11:59 PM IST.

- [ ] **10:00–12:00 IST:** record the demo video (80–150 seconds) on Santhan's Mac. Subhash narrates. Fallback: the offline demo, labelled SIMULATED on screen. Tick the fill-in line in section 3 to match the recording.
- [ ] **Before 14:00 IST:** re-run the stats on the freeze commit: `python -m pytest -q --cov=bailiff --cov-branch`, `python scripts/judge.py`, and `just judge-check` with Docker. If a number changed, update section 5 with the verbatim output. Owner: Subhash.
- [ ] **14:00 IST: CODE FREEZE.** No code changes after this time. `docs/TIMELINE.md` plans mutation tests (13:30–14:30) and the lean-code review (14:30–15:15), which cross this line. Finish them before 14:00 or drop them.
- [ ] **17:00 IST: DOCS FREEZE.** `README.md`, `docs/PARITYCOURT.md` and `JUDGES.md` are final. Search each file for `(to be verified)`, and keep only the claims that are true. Owner: Subhash. Hashwanth proofreads.
- [ ] **Before 18:00 IST: DECISION for Subhash (not decided here).** Publish these, or remove them from the public tree:
  - `docs/PRIZES.md` (internal prize strategy);
  - `docs/TIMELINE.md` (per-person owners and checklists);
  - `docs/HANDOFF-SUBHASH.md` (internal team tasks);
  - `switch-hackathon-knowledge-graph.jsonl` (memory graph with personal preferences). The owner committed it on purpose on 2026-10-27. Removing it reverses that decision and needs an explicit call;
  - any other internal file under `docs/` (not reviewed for this kit).

  Decision and reason: ______
- [ ] **Video:** uploaded to the accepted host, linked at the top of `README.md`, and the link plays in a logged-out browser. Host: see "Still to confirm".
- [ ] **Wispr Flow Insights screenshot** taken (words dictated, time saved, apps used) and saved for attaching at submission. Owner: see "Still to confirm".
- [ ] **Star `sandbox-quantum/switch`** from the account that submits. Required or not: see "Still to confirm".
- [ ] **18:00 IST: repo made public.** Owner: Subhash decides. Then check that a clean `git clone` of the public URL works without login.
- [ ] **Before 20:00 IST: no-secrets check.** The `gitleaks` job in CI is green on the submission commit. Only if that job is absent, run `git grep -nIE "AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----"` and expect no output. Caveat: `git grep` scans tracked files only, not git history.
- [ ] **#HowISwitch post** on X and/or LinkedIn, with the three tags, published after the video link works. Owner: Hashwanth. Availability: see "Still to confirm".
- [ ] **Optional blog** published, with its link ready for the form. Only if time remains.
- [ ] **Before 20:00 IST:** form fields filled: name, tagline, description, Track 01, video link, repo link, Wispr screenshot, and blog and #HowISwitch links if the form asks. Fields and attachments: see "Still to confirm".
- [ ] **20:00 IST: SUBMIT** the form.
- [ ] **23:59 IST, Nov 7: HARD DEADLINE.** Do not rely on it.
- [ ] Before pasting from this file, delete this checklist and the "Still to confirm" list.

---

## Still to confirm

Not settled by the verified facts. Check each one on the hackathon page (https://www.wemakedevs.org/hackathons/switch) or with the named owner.

1. Accepted video host and upload rules.
2. Whether a public repo and a README that explains Switch use are required.
3. Whether starring `sandbox-quantum/switch` is required.
4. The submission form fields and required attachments.
5. Owner of the Wispr Flow Insights screenshot (not assigned in `docs/HANDOFF-SUBHASH.md`).
6. Hashwanth's availability for the #HowISwitch post (`docs/HANDOFF-SUBHASH.md` Task 6 is open).
7. Owner of the optional blog (not assigned in `docs/HANDOFF-SUBHASH.md`).
8. Whether the earlier sender-field defect that stalled the live case is closed on main. The verified facts do not say.
