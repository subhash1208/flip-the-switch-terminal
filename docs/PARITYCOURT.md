# ParityCourt

**Cross-machine bug forensics with receipts.**

"Works on my machine" is now evidence: each machine's own agent testifies, and each machine's owner approves its probes and attests to that machine's side.

Hackathon: [Flip the Switch](https://www.wemakedevs.org/hackathons/switch) (Nov 4–7, 2026)
Track: 01 — Best Business Workflow ($2,000)
Team: Terminal

---

## The Problem We're Solving

An app works on Alice's Mac. The same app crashes on Bob's Linux staging box. Nobody can figure out why.

Today this means hours of back-and-forth on Slack:
- "What's your Node version?" ... waits 20 minutes ...
- "Can you run `printenv | grep PATH`?" ... waits 30 more ...
- "Try deleting node_modules and reinstalling" ... waits an hour ...

The person with the working machine can't see the failing machine. The person with the failing machine doesn't know what to look for. Meanwhile the feature branch is blocked and the PR is stuck.

**The real cost isn't the bug. It's the human ping-pong.** Agents on each machine gather the evidence directly. Humans approve which probes may run and attest to what they saw.

---

## What ParityCourt Does

ParityCourt turns the ping-pong into a case file. One Switch room holds each case. An agent on each real machine gathers evidence. A neutral arbiter, `@bailiff`, keeps the case file as a room document. Humans do only two things: approve probes on their own machine, and the machine owner attests to that machine's side.

1. Each machine agent fingerprints its own machine and proposes probes. Only that machine's owner can approve them.
2. The Bailiff compares the two environments and runs one ablation to isolate the cause.
3. The verdict is a **reproduction receipt**. `receipt.json` lists each ablation step (variable, value, outcome, pinned). A `replay` command re-runs every step and prints the same outcomes.
4. The fix is verified on the failing machine by re-running the failing test there.
5. The machine owner attests to that machine's side.

Approval-gate tools record that a human said yes. ParityCourt's output is a receipt anyone can re-run, with each owner's attestation attached to that machine's part of it.

The courtroom names are garnish. The substance is the receipt.

**Delete Switch, and these agents can't see each other's machines.**

---

## The Three Agents

The recorded run and the judge path differ in who runs each agent. In the planned recording, Alice is real Claude Code on a Mac (Santhan's), and Bob is the scripted agent in a `node:18` Linux container on the same Mac. A real Claude Code Alice has run once; a real Claude Code Bob is in progress and is not claimed. The judge path is fully scripted and keyless: Alice and Bob are both scripted containers, and no model key is needed. The Bailiff is the arbiter in both. `@alice-claude` and `@bob-codex` are handles only: the names the code and Switch use for each connection. They do not say which tool runs the agent.

### Agent 1: `@alice-claude` (Role: `baseline-counsel`)

- **What it is:** In the recorded run, Alice is a scripted agent. A real Claude Code Alice ran on a Mac in a later live run, not in the recorded transcript. In the judge path, Alice is the scripted agent in a container, with no model key. In all cases, it connects to Switch under its own connection id.
- **What it does:** Fingerprints its machine (OS, Node version, filesystem case behaviour, `git config core.ignorecase`, lockfile hashes). Writes the code fix. Optionally pushes the fix branch.
- **Who controls it:** Only Alice can approve probes on her machine. Switch refuses commands from anyone else (see Step 5).

### Agent 2: `@bob-codex` (Role: `forensic-prosecutor`)

- **What it is:** The scripted Bob agent on Bob's failing machine. In the recorded run, that is a `node:18` Linux container on Santhan's Mac. In the judge path, it is the Bob container (`node:18-bookworm-slim`, Debian bookworm). It is planned to connect to Switch through the remote-host controller, under its own connection id. SSH is not yet set up.
- **What it does:** Fingerprints the Linux environment. Runs the one ablation on the failing machine. Re-runs the failing test there after Alice's fix lands.
- **Who controls it:** Only Bob can approve probes on his machine.

### Agent 3: `@bailiff` (Role: `court-arbiter`)

- **What it is:** A small Python agent (target: about 250 lines) built directly on the Switch Agent Protocol. Events come in over a WebSocket; actions go out over HTTP.
- **What it does:**
  - Opens and closes cases, and keeps the case file as a room document
  - Subscribes with `filter=all`, so it sees every room message, not only mentions
  - Masks secrets and personal data (regex and checksum) before anything is posted
  - Writes `receipt.json` and provides the `replay` command
  - Optionally caps agent-to-agent turns at 6. Switch has no built-in loop breaker, so this is Bailiff code.
- **Who controls it:** Orchestrates the case. It holds no approval power of its own; only owners approve.

---

## Why Switch Is Essential (The 30% Rubric Answer)

Switch puts agents on **different physical machines**, from **different AI vendors**, into one room. Each machine's agent answers only its owner, and the owner approves what that agent may run.

What Switch carries, concretely:
- **One room per case.** The room's documents are the case file.
- **One connection id per machine agent.** Reusing an id is a takeover, not a second connection. The displaced connection receives `taken_over`, which is final, so two agents can't share one id.
- **The Bailiff uses `filter=all`.** A connection with `filter=addressed` never receives `command` events, and it drops messages that don't mention it.
- **A new agent answers only its owner.** Until its addressing policy is set, a newly registered agent admits its owner and the owner's other agents. Anyone else gets a refusal, not an answer.
- **Owner-only approval is enforced by Switch, not by message text.** Switch's addressing gate covers approval answers as well as commands. A Mattermost button press is mapped to the clicker's Switch identity and checked there. A non-owner's command to `@alice-claude` is demoted to unaddressed chatter, and Switch posts a canned refusal. This is verified in code and not yet live-tested; see Step 5 and Risks. Writing "only Alice may approve" in a message enforces nothing.
- **Registration is one call per agent.** Register once with `POST /agents`, authenticated by a registration key. The response returns the agent's own API key, once. Do not use `POST /agents/register-known`: Switch's docs say it registers only the agent types Switch Console runs.

Without Switch:
- Alice's agent cannot see Bob's filesystem
- There's no shared room to hold the case file
- There's no owner-scoped gate on each machine's probes
- Nothing stops one person's agent from being commanded by another person

Switch is the architecture, not a wrapper.

---

## The 8-Step Flow

Here's what a ParityCourt trial looks like, step by step:

### Step 1 — Opening the Case

Bob reports: "@bailiff Open Case #101: The `export-service` auth middleware passes on Alice's Mac but throws a 500 `AuthVerifierError` on my Linux staging container."

The Bailiff creates the room document **Case #101 Evidence Ledger** and summons both agents by role.

### Step 2 — Fingerprinting and Owner-Approved Probes

Each agent proposes probes from an allow-list:
- `@alice-claude`: `uname -a`, `node -v`, `git config core.ignorecase`, `diskutil info /` (macOS host only)
- `@bob-codex`: `uname -a`, `node -v`, `env`, `stat -f -c %T .`

Auto-approve is OFF, so every probe waits for its machine's owner. Alice approves Mac probes. Bob approves Linux probes. Each `[Allow]` press is checked by Switch against the clicker's identity. That is verified in code and not yet live-tested; see Step 5 and Risks.

### Step 3 — Redaction and Environment Diff

Both agents return their fingerprints. Secret-looking values are redacted before they reach room history: Switch's own Trust guardrail shows them as `[redacted]`, and the Bailiff's regex catches what remains in env dumps. Illustrative output:

```
DATABASE_PASSWORD=[redacted]
```

The Bailiff posts the clean env diff to Room Documents as `env-diff-case-101` and isolates three suspects:

| Suspect | Alice (works) | Bob (fails) | Verdict |
|---------|---------------|-------------|---------|
| A — Timezone/Locale | `TZ=Asia/Kolkata` | `TZ=UTC` | Decoy |
| B — Stale Shell Flag | Not set | `NODE_OPTIONS=--openssl-legacy-provider` | Decoy |
| C — Node Major Version | Node 22 (`node:22-bookworm-slim` in the judge path; scripted Alice in the recorded run) | Node 18 (`node:18-bookworm-slim` in the judge path; `node:18` container in the recorded run) | **Culprit** |

The same culprit appears in both runs: Node 18 fails, Node 22 passes. Decoys A and B are planted in both runs. The case-only import is a separate, optional bonus clip; see The Sample App.

### Step 4 — One Ablation on the Failing Machine

The Bailiff asks `@bob-codex` to change one variable on the failing box: the Node major. Bob's agent runs the failing test under Node 22 instead of Node 18. This step is the same in the recorded run and the judge path.

- Ablation: failing test run under Node 22 → passes (outcome: pass)

Root cause: `toSorted()` is not a function on Node 18, so the auth path throws.

The env diff rules out the decoys. If time allows, one ablation each clears them too. Every step goes into the receipt.

### Step 5 — Failed Bypass: Bob Tries to Approve Alice's Probes

This is the security beat, and the demo shows it on purpose. Switch enforces owner-only approval, and ParityCourt's code is not in the path. Approval answers pass the same addressing gate as commands to an agent. An `[Allow]` press is mapped to the clicker's Switch identity and sent as that person. Verified in code; not yet live-tested.

Demo steps:

1. Alice's agent, on the default addressing policy (never `anyone`), raises an approval card in a Mattermost-bridged room.
2. Bob presses `[Allow]`, then separately types "yes" in the card's thread.
3. Expected: Bob's press shows "Your answer to <handle> did not land, because you may not address this agent, so you may not answer it." Switch logs a NOT_AUTHORIZED refusal. The card stays open. The typed "yes" falls back to the card thread, where everyone can see it.
4. ParityCourt's code must not call the answer endpoint in this run, so the rejection cannot come from us.

The control lives in Switch's addressing policy, not in the message, so it holds even if the message says "Alice approved." Caveats, all verified in code and none live-tested:

- The default policy admits the owner and the owner's other agents. It is not strictly owner-only.
- An `anyone` policy admits everyone. Never set it on a ParityCourt agent.
- Any agent Alice owns can approve on her behalf. Check who owns `@bailiff` before the demo.

If the live test fails, the fallback is a Bailiff pre-check that refuses answers from non-owners. It is enforced by our code and is never claimed as Switch enforcement.

### Step 6 — Fix and Verification on the Failing Machine

`@alice-claude` writes the fix: the auth path no longer calls `toSorted()`, or the project pins a Node version that provides it. The change goes on branch `fix/node-101-tosorted`.

`@bob-codex` re-runs the failing test on Bob's machine. The fix counts as verified only when the test passes where it failed, not on Alice's Mac.

Opening the PR is optional. Auto-push is a stretch item, not part of the must-have slice.

### Step 7 — Owner Attestation

- `@alice-claude` asks Alice to attest to the Mac-side evidence and the fix. Alice taps `[Allow]`.
- `@bob-codex` asks Bob to attest to the Linux-side evidence and the passing re-run. Bob taps `[Allow]`.

Each machine's owner attests to that machine's side. Neither can attest for the other. Attestation records who said yes; it is not a cryptographic signature (see Honest Limits).

### Step 8 — Verdict and Replay

The Bailiff posts the verdict to the room and saves `receipt.json`:

> **VERDICT #101**: Culprit: Node major version (`toSorted()` throws on Node 18; Node 22 passes). The decoys (`TZ`, `NODE_OPTIONS`) are ruled out. One ablation shows the cause. The fix is verified on the failing machine. Both machine owners attested to their machine's side.

Each receipt step records the variable, its value, the outcome, and what was pinned (commit, Node version, mount type). The `replay` command re-runs every step and prints the same outcomes. That is the proof anyone can repeat.

*Delete Switch, and these agents can't see each other's machines.*

---

## The Sample App (Planted Bugs)

A small Node.js `export-service` with auth middleware. It has one culprit and two decoys, and the same culprit drives both the recorded run and the judge path.

The git history is real: an earlier commit renamed `SqlAuthGuard.ts` to `sqlAuthGuard.ts` by case alone. A case-insensitive filesystem accepts that rename silently. That history drives only the optional case-only bonus clip, not the main story.

### Culprit: Node-version-dependent API

- The auth path calls `Array.prototype.toSorted()`. The method landed in Node 20 (UNVERIFIED: not yet confirmed against the Node changelog; confirm by running).
- Alice's side runs it on Node 22 (a scripted Alice in the recorded run; a real Claude Code Alice ran on a Mac in a later live run, not in the recorded transcript; `node:22-bookworm-slim` container in the judge path), and the test passes.
- Bob's container (`node:18-bookworm-slim` in the judge path; `node:18` container in the recorded run) throws a TypeError, so the auth path fails and the test goes red (verified: container check 5 of 5).
- Deterministic: both images are meant to be pinned by digest in `deploy/docker-compose.yml` `(to be verified)` and stay on glibc. No privileges and no host-specific behaviour.

### Optional bonus clip: case-only import mismatch (10 seconds, same Mac)

- The file on disk is `security/sqlAuthGuard.ts`; the import is `from './security/SqlAuthGuard'`.
- `node sample-app/export-service/case-demo/consumer.js` works on a case-insensitive filesystem (APFS on the Mac). The same file fails with `MODULE_NOT_FOUND` inside the Linux container (case-sensitive ext4).
- This is an analogue, not the culprit, and not part of the main story. It is unverified until recorded. The judge containers do not reproduce it (see How Judges Reproduce It).

### Fallback (UNVERIFIED): privileged case-insensitive mount

- Would let the judge path reproduce the optional case-only analogue. Not needed for the main story. Usable only if tested on Linux, macOS and WSL2 Docker Desktop.
- Feasibility is UNVERIFIED: ext4 casefold needs kernel support plus a loop mount, the Docker Desktop VM kernel is unknown, and sources conflict on VirtioFS case behaviour.
- Until it is tested, the judge path uses the Node-version culprit.

### Decoy 1: Timezone/Locale
- Alice's container has `TZ=Asia/Kolkata`; Bob's has `TZ=UTC`
- Looks suspicious, but doesn't cause the failure
- Agents investigate and rule it out

### Decoy 2: Stale Shell Flag
- Bob's container sets `NODE_OPTIONS=--openssl-legacy-provider`
- Also suspicious, but not the cause of this bug. The flag should be valid on Node 18 and 22 (UNVERIFIED until run).
- Agents investigate and rule it out

The decoys make the diagnosis non-trivial. The receipt makes the answer checkable.

---

## The Custom Bailiff Agent

The Bailiff is a small Python agent (target: about 250 lines) built on the Switch Agent Protocol:

- **Inbound:** a WebSocket from Switch (`/agents/{agent_id}/connection/ws`), subscribed with `filter=all`. SSE is the deprecated fallback for older clients; do not build on it.
- **Outbound:** HTTP POST actions back to Switch
- **Case file:** a room document, appended to as the case moves. The Bailiff creates the case-file room document itself, since only the creating agent may edit a room document.
- **Secret redactor:** regex and checksum masking of secrets and personal data before posting, with Switch's guardrail as the second layer
- **Receipt:** writes `receipt.json` and provides `replay`
- **State machine:** OPEN → FINGERPRINTING → ABLATION → FIX → VERIFY → ATTESTATION → VERDICT

**Must-have slice:** fingerprint, env diff with redaction, one ablation, owner approvals, receipt + replay, verification on the failing machine.
**Optional, cut first:** the 6-turn loop breaker and auto-push of the PR.
**Not in the plot:** `switch-trust` scan and eval. They appear only as an optional bonus (see Tech Stack).

This matters because:
1. It shows the Switch protocol at the wire level (WebSocket + HTTP)
2. Switch has no built-in loop breaker and no dual sign-off, so any guard the Bailiff ships is its own code
3. It's the blog post: "Build a Custom Switch Agent in 250 Lines" (optional side entry)

---

## How Judges Reproduce It

Judges need Docker. Nothing else: no model key, no Mac, no Linux box, no Slack workspace, no accounts. The judge path is fully scripted and keyless.

1. **Two containers:** an Alice container and a Bob container, built from the pinned Node images in the sketch below (Debian bookworm, not Ubuntu 24.04). Each has its own Switch connection id. Bob's connects through the remote-host controller; the sketch does not set up SSH yet.
2. **A deterministic difference:** the Node major version (see The Sample App). The difference lives in the containers, so the judge's host OS doesn't change the result.
3. **One command:** `python scripts/judge.py` runs the offline checks, and its Docker check runs when Docker is on PATH (run with Docker: 8 of 8 checks; container check 5 of 5). Bootstrapping both containers and the Switch stack from one command is planned.
4. **Chat platform:** the Mattermost that Switch bundles.
5. **Room template:** hand-written v2 YAML. Switch Console's "Capture as template" strips agent instructions and permissions, so we write it ourselves.
6. **Auto-approve OFF:** every probe waits for its owner.
7. **Recorded run:** a recording of the full run and `replay`, for the video and for anyone who can't run Docker.

**The honest story:** The bug is a Node-version-dependent API, in the recorded run and the judge path alike. The case-only import (macOS APFS vs Linux ext4) is a real-world analogue, shown only as an optional 10-second bonus clip on the same Mac. The judge containers do not reproduce it.

Compose sketch (images to be pinned by digest before the demo; `test.js` is the failing test, so confirm it exists in `export-service`):

```yaml
services:
  alice:
    image: node:22-bookworm-slim@sha256:<pin>
    environment:
      TZ: Asia/Kolkata
    working_dir: /app
    volumes:
      - ./export-service:/app:ro
    command: node test.js

  bob:
    image: node:18-bookworm-slim@sha256:<pin>
    environment:
      TZ: UTC
      NODE_OPTIONS: --openssl-legacy-provider
    working_dir: /app
    volumes:
      - ./export-service:/app:ro
    command: node test.js
```

The compose file is `deploy/docker-compose.yml`. Digest pinning in it is `(to be verified)`. This document doesn't assert version numbers for Switch or Switch Trust; check them against the running stack.

---

## Honest Limits

For the README:

- **Approval identity is the participant's name, not a signed identity.** An attestation records who said yes. It is not a cryptographic signature.
- **Probes are allow-listed.** Agents run only the commands on the approved list. They never read `.env` files.
- **Real vs simulated.** Built and tested offline: the receipt, the replay, the redactor and the in-memory room. Live mode is merged to main and has run once against a real Switch 0.31.0 server with scripted Alice and Bob ([`docs/evidence/transcript.txt`](evidence/transcript.txt)). Owner-scoped addressing live test: `(to be verified)`. Simulated in the judge path: both sides are Node containers (Node 22 and Node 18), not a Mac or an Ubuntu box. The planned recording uses real Claude Code for Alice on the Mac and a Node 18 container for Bob; a real Claude Code Alice has run once, and a real Claude Code Bob is in progress and not claimed. The case-only import is an optional bonus clip that the judge containers do not reproduce. The 80–150 second recording is planned, not yet recorded.
- **Switch has no built-in loop breaker or dual sign-off.** Any turn cap or two-owner rule is Bailiff code, and the turn cap is optional.
- **Masking is regex and checksum, for secrets and personal data.** It is not a guarantee against every format, and whether Switch's guardrail masks real agent replies is unverified. The masking limits are listed under Privacy in the README.
- **Masked suspects are not ablated.** A suspect whose value contains a placeholder gets verdict `unknown` (`not ablated: value masked`).
- **No ablation, no verdict.** If nothing could be ablated, the receipt is INCONCLUSIVE.
- **Verification covers one test.** The fix is verified by re-running the failing test on the failing machine. That is not proof the fix is correct beyond that test.
- **Owner-only approval is verified in code, not yet live-tested.** See Risks.
- **Custom agents apparently cannot raise Switch approval cards (unverified).** Those cards belong to Console-run agents such as Claude Code. The scripted agents' owner gate is a targeted message to the owner plus an addressed reply, enforced by Switch's addressing policy. A real Claude Code Alice has run once, with Auto mode on; real Claude Code Bob has not run. Approval cards were not observed with Auto mode on. They also cannot be posted for Alice in a Mattermost room (no Mattermost bot exists for her), so approval cards were not demonstrated. See Risks.

---

## Privacy

The Bailiff masks personal data as well as secrets. Masking happens before anything is posted to the room, or written to the case file or `receipt.json`. Each masked value is replaced with a typed placeholder, for example `[redacted:email]`.

| Data | Status |
|------|--------|
| Secrets (secret-named keys, tokens, Bearer, AWS/GitHub keys, JWTs, URL credentials, auth headers, password flags) become `[redacted]` | Built, offline, tested |
| Personal data becomes typed placeholders: `[redacted:email]`, `[redacted:ip]`, `[redacted:mac]`, `[redacted:card]` (Luhn-valid only), `[redacted:ssn]`, `[redacted:phone]` (E.164 only), `[redacted:id]`, `[redacted:user]`, `[redacted:host]` | Built, offline, tested |
| Receipt `privacy` block: placeholder counts and one masked example | Built |
| Names and street addresses in free text, non-Latin scripts, base64-embedded PII | Not masked (known limit) |

Masking is pattern-based and checksum-based, not name detection. A person's name in free text is not masked unless it matches a pattern. The full masking limits are listed under Privacy in the README.

The masking code is `bailiff/redact.py`: deterministic, linear-time, idempotent, never raises, with input capped at 64 KB per message.

---

## Quality

| Check | Status |
|-------|--------|
| ruff (lint and format) | Done: clean |
| mypy, strict, over `bailiff/` | Done: clean |
| pytest | Done: 603 tests pass |
| Branch coverage | Done: 95 percent measured. The 90 percent gate is in the CI config; CI is green (8 jobs) |
| hypothesis property tests (redact, PII masking) | Done: `tests/test_redact_properties.py`, `tests/test_pii_properties.py` |
| Mutation tests on pure modules | Planned |
| Ponytail review | Planned |
| bandit, pip-audit, gitleaks | Configured in CI; CI is green (8 jobs) |
| CI workflow (lint and types, tests with the 90% gate, Node job, Docker judge path, actionlint, `ci-ok`), plus Dependabot and pre-commit | Defined in `.github/workflows/ci.yml`; 8 jobs, all green |

`.github/workflows/ci.yml` is the authority for what CI runs. It has run on GitHub: 8 jobs, all green.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Switch Console | Desktop app (version not asserted here) |
| Switch Core | Self-hosted via Docker (version not asserted here) |
| Switch Trust CLI | Optional bonus only: `scan` (OpenGrep code analysis) and `eval` (scores a running HTTP agent 0–100%; needs an LLM key). Not in the main plot. |
| Chat Platform | Mattermost (bundled with Switch) |
| Agent 1 | Scripted Alice in the recorded run; Claude Code on a Mac in a later live run (not in the recorded transcript); scripted agent in a container, no model key (judge path) |
| Agent 2 | Scripted Bob agent (judge path: `node:18-bookworm-slim` container; recorded run: `node:18` Linux container on Santhan's Mac) |
| Agent 3 (Bailiff) | Custom Python, WebSocket/HTTP protocol |
| Sample App | Node.js `export-service` with auth middleware |
| Tests | pytest with hypothesis property tests for the Bailiff. Counts in Quality. CI green (8 jobs). |
| Room Template | Hand-written v2 YAML |
| Setup | `python -m pip install -e .`, then `python scripts/judge.py`. `just demo` runs the offline demo. |

---

## Why This Wins

| Rubric (weight) | How ParityCourt scores |
|-----------------|----------------------|
| **Use of Switch (30%)** | One room per case, one connection id per machine agent, owner-scoped addressing, room documents as the case file, two AI vendors on two machines. Remove Switch and nothing works. |
| **Technical Execution (25%)** | One-command `python scripts/judge.py` (8 of 8 checks with Docker; container check 5 of 5), a two-container judge path with a deterministic bug, a re-runnable receipt with `replay`, pytest and property tests for the Bailiff (built; see Quality). |
| **Creativity & Impact (25%)** | "Works on my machine" becomes evidence: a receipt anyone can replay, with each machine's owner attesting to that machine's side. |
| **Presentation (20%)** | The failed bypass (Bob's command rejected), the owner attestations, `replay` printing the same outcomes, the closing line. |

---

## Prize Stacking

ParityCourt is the Track 01 submission. Side entries only if they're cheap:

| Prize | How we get it |
|-------|--------------|
| **Track 01 ($2,000)** | ParityCourt submission |
| **Code with Wispr ($500)** | Dictate prompts, room instructions, README, and blog post via Wispr Flow. Submit Insights screenshot. |
| **Best Blog (AirPods 5)** | First-time-user quickstart: "Build a Custom Switch Agent in 250 Lines," using the Bailiff as the example |
| **#HowISwitch (Logitech keyboard)** | 60-second highlight clip on X and LinkedIn, tag @switchagents_ai @WeMakeDevs @DevToolsAcademy |
| **Swag (random draw)** | Every submission is entered automatically |
| **Certificate** | Every submission gets one |

---

## Risks

1. **Owner-only approval: verified in code, needs one live test.** Switch's addressing gate covers approval answers as well as commands (Switch core `session_activity/service.py:483-485`, refusal at `:599-603`). An `[Allow]` press is mapped to the clicker's identity (`collaboration_core.py:1886-1907`, `bridge_answers.py:187-210`). Run the Step 5 demo before the demo depends on it. If it fails, the Bailiff pre-check is enforced by our code, never by Switch. Finding (Nov 6, unverified end to end): custom Python agents apparently cannot raise Switch approval cards, which belong to Console-run agents such as Claude Code. For the scripted agents, the gate is a targeted message to the owner plus an addressed reply, enforced by Switch's addressing policy. Real approval cards are expected only once real Claude Code agents join the room (in progress).
2. **The main story is a Node-version bug in both the judge path and the recorded run.** The culprit is `toSorted()` (verified: container check 5 of 5). The case-only import is an optional 10-second bonus clip on the Mac. Reproducing it in the judge path needs the privileged case-insensitive mount, which is untested on Linux, macOS and WSL2 Docker Desktop. If that mount fails, nothing in the main story is lost.
3. **Addressing policy and the ping TTL catch new agents out.**
   - A newly registered agent answers only its owner until an addressing policy is set. Test with a second agent before the demo.
   - Each connection must answer app-level pings within 6 seconds, or Switch evicts it (`heartbeat_lapsed`). The reply is a `pong` carrying the cursor: `{"type":"pong","cursor":N}`. Answer pings before processing events. After a lapse, reopen and resume from your cursor.
   - Reopening a live connection id is a takeover. Give each agent its own id, and never reconnect after `taken_over`.
   - `filter=addressed` drops non-mentions. The Bailiff uses `filter=all`.

---

## Important Rules and Gotchas

1. **No project code before Nov 4.** The Switch setup and workflow must be built during Nov 4–7. Your git history must start on Nov 4. Environment setup is OK before that.

2. **Auto-approve and Auto-mode must be OFF** in Switch Console, otherwise the approval buttons never render in chat.

3. **Console's "Capture as template" strips agent instructions and permissions.** Hand-write the v2 room template YAML.

4. **Register agents with `POST /agents`, not `POST /agents/register-known`.** The latter registers only the agent types Switch Console runs.

5. **Task delegation is not ready in Switch.** Use `@-mentions` by role to direct messages to specific agents.

6. **docs.switchagents.ai may be down (503).** The same docs exist in the repo at `docs/official/`.

7. **Switch Trust is an optional bonus, not the main plot.** Don't let it displace the must-have slice.

8. **Repo public by ~6 PM IST on Nov 7** (target; Boss decides). The official deadline is 11:59 PM IST on Nov 7. Submit before then to avoid server issues.

9. **The demo video closing line is:** "Delete Switch, and these agents can't see each other's machines."

10. **Demo video length: 80–150 seconds.** Judges favour short videos. The case-only bonus clip is optional and does not count toward the main story.

---

## Key Links

- [Hackathon Page](https://www.wemakedevs.org/hackathons/switch)
- [DevTools Academy Page](https://www.devtoolsacademy.com/hackathons/flip-the-switch)
- [Switch GitHub](https://github.com/sandbox-quantum/switch)
- [Switch Trust CLI](https://github.com/sandbox-quantum/switch-trust-cli)
- [Switch Agent Protocol](https://github.com/sandbox-quantum/switch/blob/main/docs/official/internals/agent-protocol.md)
- [Remote Host Setup](https://github.com/sandbox-quantum/switch/blob/main/docs/official/deploy/host-remotely.md)
- [Wispr Flow](https://wisprflow.ai)
