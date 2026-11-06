# ParityCourt

**Cross-machine bug forensics with receipts.**

"Works on my machine" is now evidence: each machine's own agent testifies, and each owner signs for their own machine.

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

ParityCourt turns the ping-pong into a case file. One Switch room holds each case. An agent on each real machine gathers evidence. A neutral arbiter, `@bailiff`, keeps the case file as a room document. Humans do two things only: approve probes on their own machine, and attest to results on their own machine.

1. Each machine agent fingerprints its own machine and proposes probes. Only that machine's owner can approve them.
2. The Bailiff compares the two environments and runs one ablation to isolate the cause.
3. The verdict is a **reproduction receipt**. `receipt.json` lists each ablation step (variable, value, outcome, pinned). A `replay` command re-runs every step and prints the same outcomes.
4. The fix is verified on the failing machine, by re-running the failing test there.
5. Each owner attests to the result on their own machine.

Approval-gate tools record that a human said yes. ParityCourt's output is a receipt anyone can re-run, with each owner's attestation attached to their own machine's part of it.

The courtroom names are garnish. The substance is the receipt.

**Delete Switch and these agents can't see each other's machines.**

---

## The Three Agents

The recorded run and the judge path differ in who runs each agent. In the recorded video run, Alice is real Claude Code on a Mac (Santhan's), and Bob is the scripted agent in a `node:18` Linux container on the same Mac. The judge path is fully scripted and keyless: Alice and Bob are both scripted containers, and no model key is needed.

### Agent 1: `@alice-claude` (Role: `baseline-counsel`)

- **What it is:** Claude Code on Alice's machine: her macOS host in the recorded run. In the judge path, Alice is the scripted agent in a container, with no model key. Either way, it connects to Switch under its own connection id.
- **What it does:** Fingerprints its machine (OS, Node version, filesystem case behaviour, `git config core.ignorecase`, lockfile hashes). Writes the code fix. Optionally pushes the fix branch.
- **Who controls it:** Only Alice can approve probes on her machine. Switch refuses commands from anyone else (see Step 5).

### Agent 2: `@bob-codex` (Role: `forensic-prosecutor`)

- **What it is:** The scripted Bob agent on Bob's failing machine. In the recorded run, that is a `node:18` Linux container on Santhan's Mac. In the judge path, it is the Bob container (`node:18-bookworm-slim`, Debian bookworm). It connects to Switch over SSH through the remote-host controller, under its own connection id.
- **What it does:** Fingerprints the Linux environment. Runs the one ablation on the failing machine. Re-runs the failing test there after Alice's fix lands.
- **Who controls it:** Only Bob can approve probes on his machine.

### Agent 3: `@bailiff` (Role: `court-arbiter`)

- **What it is:** A small Python agent (target: about 250 lines) built directly on the Switch Agent Protocol. Events come in over a WebSocket; actions go out over HTTP.
- **What it does:**
  - Opens and closes cases, and keeps the case file as a room document
  - Subscribes with `filter=all`, so it sees every room message, not only mentions
  - Redacts secret-looking values from env dumps with a simple regex before anything is posted
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

Bob reports: "@bailiff Open Case #101: The `export-service` auth middleware passes on Alice's Mac but throws a 500 `AuthVerifierError` on my Ubuntu 24.04 staging box."

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
| C — Node Major Version (judge path) | `node:22-bookworm-slim` | `node:18-bookworm-slim` | **Culprit** |

This table shows the judge-path bug. In the recorded real-Mac run, row C is filesystem case (APFS vs ext4) and that is the culprit there; see The Sample App.

### Step 4 — One Ablation on the Failing Machine

The Bailiff asks `@bob-codex` to change one variable on the failing box. On the judge path, that variable is the Node major: Bob's agent runs the failing test under Node 22 instead of Node 18. In the recorded real-Mac run, it is how the import resolves the file name: Bob's agent adds a symlink named `SqlAuthGuard.ts` that points at `sqlAuthGuard.ts`, then starts the app again.

- Ablation (judge path): failing test run under Node 22 → passes (outcome: pass)
- Ablation (recorded run): one case-matching symlink for the import → App boots (outcome: pass)

Root cause (judge path): `toSorted()` is not a function on Node 18, so the auth path throws. Root cause (recorded run): the import `from './security/SqlAuthGuard'` resolves on a case-insensitive filesystem but not on a case-sensitive one, where the file is `security/sqlAuthGuard.ts`.

The env diff rules out the decoys. If time allows, one ablation each clears them too. Every step goes into the receipt.

### Step 5 — Failed Bypass: Bob Tries to Approve Alice's Probes

This is the security beat, and the demo shows it on purpose. Switch enforces owner-only approval, and ParityCourt's code is not in the path. Approval answers pass the same addressing gate as commands to an agent. A `[Allow]` press is mapped to the clicker's Switch identity and sent as that person. Verified in code; not yet live-tested.

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

`@alice-claude` writes the fix: the import is corrected to match the file on disk. It may also add a check that blocks case-mismatched imports. Both changes go on branch `fix/case-101-import`.

`@bob-codex` re-runs the failing test on Bob's machine. The fix counts as verified only when the test passes where it failed, not on Alice's Mac.

Opening the PR is optional. Auto-push is a stretch item, not part of the must-have slice.

### Step 7 — Owner Attestation

- `@alice-claude` asks Alice to attest to the Mac-side evidence and the fix. Alice taps `[Allow]`.
- `@bob-codex` asks Bob to attest to the Linux-side evidence and the passing re-run. Bob taps `[Allow]`.

Each owner signs for the result on their own machine. Neither can attest for the other. Attestation records who said yes; it is not a cryptographic signature (see Honest Limits).

### Step 8 — Verdict and Replay

The Bailiff posts the verdict to the room and saves `receipt.json`:

> **VERDICT #101** (recorded real-Mac run; the judge-path verdict names the Node major instead): Culprit: import filename case mismatch (`SqlAuthGuard` vs `sqlAuthGuard.ts`). One ablation shows the cause. The fix is verified on the failing machine. Both owners attested on their own machines.

Each receipt step records the variable, its value, the outcome, and what was pinned (commit, Node version, mount type). The `replay` command re-runs every step and prints the same outcomes. That is the proof anyone can repeat.

*Delete Switch, and these agents can't see each other's machines.*

---

## The Sample App (Planted Bugs)

A small Node.js `export-service` with auth middleware. Its git history is real: an earlier commit renamed `SqlAuthGuard.ts` to `sqlAuthGuard.ts` by case alone. A case-insensitive filesystem accepts that rename silently, so the slip is realistic. That history drives the recorded real-Mac run, not the judge path.

The app has one culprit per path and two decoys.

### Judge-path culprit (primary): Node-version-dependent API

- The auth path calls `Array.prototype.toSorted()`. The method landed in Node 20 (UNVERIFIED: not yet confirmed against the Node changelog; confirm by running).
- Alice's container (`node:22-bookworm-slim`) runs it, and the test passes.
- Bob's container (`node:18-bookworm-slim`) throws a TypeError, so the auth path fails and the test goes red (UNVERIFIED until run).
- Deterministic: both images are pinned by digest in `docker-compose.yml` (UNVERIFIED until that file exists) and stay on glibc. No privileges and no host-specific behaviour.

### Recorded real-Mac run: case-only import mismatch

- The file on disk is `security/sqlAuthGuard.ts`; the import is `from './security/SqlAuthGuard'`.
- On a case-insensitive filesystem (APFS on a real Mac) the import resolves and the app boots. On a case-sensitive one (ext4 on Bob's box) it fails.
- This bug is not in the planned recording, and no real-Mac replay of it is recorded yet (unverified). The judge containers do not reproduce it (see How Judges Reproduce It).

### Fallback (UNVERIFIED): privileged case-insensitive mount

- Would let the judge path reproduce the case bug. Usable only if tested on Linux, macOS and WSL2 Docker Desktop.
- Feasibility is UNVERIFIED: ext4 casefold needs kernel support plus a loop mount, the Docker Desktop VM kernel is unknown, and sources conflict on VirtioFS case behaviour.
- Until it is tested, the judge path uses the Node-version culprit.

### Decoy 1: Timezone/Locale
- Alice's container has `TZ=Asia/Kolkata`; Bob's has `TZ=UTC`
- Looks suspicious, but doesn't cause the failure
- Agents investigate and rule it out

### Decoy 2: Stale Shell Flag
- Bob's container sets `NODE_OPTIONS=--openssl-legacy-provider`
- Also suspicious, also harmless to this bug. The flag should be valid on Node 18 and 22 (UNVERIFIED until run).
- Agents investigate and rule it out

The decoys make the diagnosis non-trivial. The receipt makes the answer checkable.

---

## The Custom Bailiff Agent

The Bailiff is a small Python agent (target: about 250 lines) built on the Switch Agent Protocol:

- **Inbound:** a WebSocket from Switch (`/agents/{agent_id}/connection/ws`), subscribed with `filter=all`. SSE is the deprecated fallback for older clients; do not build on it.
- **Outbound:** HTTP POST actions back to Switch
- **Case file:** a room document, appended to as the case moves. The Bailiff creates the case-file room document itself, since only the creating agent may edit a room document.
- **Secret redactor:** a simple regex on env dumps before posting, with Switch's guardrail as the second layer
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
2. **A deterministic difference:** the Node major version (primary; see The Sample App). The difference lives in the containers, so the judge's host OS doesn't change the result.
3. **One command:** `just demo` bootstraps both containers and the Switch stack. (Planned entry point.)
4. **Chat platform:** the Mattermost that Switch bundles.
5. **Room template:** hand-written v2 YAML. Switch Console's "Capture as template" strips agent instructions and permissions, so we write it ourselves.
6. **Auto-approve OFF:** every probe waits for its owner.
7. **Recorded run:** a recording of the full run and `replay`, for the video and for anyone who can't run Docker.

**The honest story:** The bug is a Node-version-dependent API. The case-only import (macOS APFS vs Linux ext4) is a real-world analogue. The judge containers do not reproduce it, and it is not the culprit in the planned recording.

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

Images are pinned by digest in `docker-compose.yml` (digests to be filled in when the compose file exists; UNVERIFIED until then). This document doesn't assert version numbers for Switch or Switch Trust; check them against the running stack.

---

## Honest Limits

For the README:

- **Approval identity is the participant's name, not a signed identity.** An attestation records who said yes. It is not a cryptographic signature.
- **Probes are allow-listed.** Agents run only the commands on the approved list. They never read `.env` files.
- **Real vs simulated.** Built and tested offline: the receipt and the replay. Not yet run against a real Switch server: the Switch rooms, agent connections, and owner-scoped addressing (live mode is planned). Simulated in the judge path: both sides are Node containers (Node 22 and Node 18), not a Mac or an Ubuntu box. The case-only import is not part of the planned recording, and the judge containers do not reproduce it. The recording shows the full run (planned, not yet recorded).
- **Switch has no built-in loop breaker or dual sign-off.** Any turn cap or two-owner rule is Bailiff code, and the turn cap is optional.
- **Secret redaction is best effort.** It combines Switch's guardrail with a regex. It is not a guarantee against every secret format.
- **Verification covers one test.** The fix is verified by re-running the failing test on the failing machine. That is not proof the fix is correct beyond that test.
- **Owner-only approval is verified in code, not yet live-tested.** See Risks.
- **Custom agents apparently cannot raise Switch approval cards (unverified).** Those cards belong to Console-run agents such as Claude Code. The scripted agents' owner gate is a targeted message to the owner plus an addressed reply, enforced by Switch's addressing policy. Real approval cards appear only in the recorded run, where Alice is real Claude Code. See Risks.

---

## Privacy

The Bailiff masks personal data as well as secrets. Masking happens before anything is posted to the room, or written to the case file or `receipt.json`. Each masked value is replaced with a typed placeholder, for example `[redacted:email]`.

| Data | Status |
|------|--------|
| Secrets in env dumps (regex; best effort, see Honest Limits) | Done |
| Emails, usernames, hostnames, IP addresses, home directory paths, phone numbers | Planned, not yet built |
| Card numbers, matched only when they pass the Luhn check | Planned, not yet built |

Masking is pattern-based, not name detection. Under the planned design, a person's name in free text is not masked unless it matches a pattern. (Planned, not yet built.)

---

## Quality

| Check | Status |
|-------|--------|
| ruff | Done: clean |
| mypy, strict | Done: clean |
| pytest, 132 tests | Done: all pass (on Subhash's PC) |
| Coverage gate at 90% | Planned, not yet built. Current coverage (unverified). |
| hypothesis property tests (redact, parsers) | Planned, not yet built |
| Mutation tests on pure modules (cosmic-ray, 1 h box) | Planned, not yet built |
| bandit, pip-audit, gitleaks | Planned, not yet built |
| CI workflow running the checks above, plus a Node test job, a Docker judge-path job, actionlint, pre-commit, and Dependabot | Planned, not yet built |

Once the CI workflow exists, it is the authority for what runs.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Switch Console | Desktop app (version not asserted here) |
| Switch Core | Self-hosted via Docker (version not asserted here) |
| Switch Trust CLI | Optional bonus only: `scan` (OpenGrep code analysis) and `eval` (scores a running HTTP agent 0–100%; needs an LLM key). Not in the main plot. |
| Chat Platform | Mattermost (bundled with Switch) |
| Agent 1 | Claude Code on Alice's macOS host (recorded run); scripted agent in a container, no model key (judge path) |
| Agent 2 | Scripted Bob agent (judge path: `node:18-bookworm-slim` container; recorded run: `node:18` Linux container on Santhan's Mac) |
| Agent 3 (Bailiff) | Custom Python, WebSocket/HTTP protocol |
| Sample App | Node.js `export-service` with auth middleware |
| Tests | pytest for the Bailiff: 132 tests pass (on Subhash's PC). CI and coverage gate planned. |
| Room Template | Hand-written v2 YAML |
| Setup | `just demo` (planned) |

---

## Why This Wins

| Rubric (weight) | How ParityCourt scores |
|-----------------|----------------------|
| **Use of Switch (30%)** | One room per case, one connection id per machine agent, owner-scoped addressing, room documents as the case file, two AI vendors on two machines. Remove Switch and nothing works. |
| **Technical Execution (25%)** | One-command `just demo` (planned), a two-container judge path with a deterministic bug, a re-runnable receipt with `replay`, pytest coverage for the Bailiff (target). |
| **Creativity & Impact (25%)** | "Works on my machine" becomes evidence: a receipt anyone can replay, with each owner attesting for their own machine. |
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

1. **Owner-only approval: verified in code, needs one live test.** Switch's addressing gate covers approval answers as well as commands (Switch core `session_activity/service.py:483-485`, refusal at `:599-603`). A `[Allow]` press is mapped to the clicker's identity (`collaboration_core.py:1886-1907`, `bridge_answers.py:187-210`). Run the Step 5 demo before the demo depends on it. If it fails, the Bailiff pre-check is enforced by our code, never by Switch. Finding (Nov 6, unverified end to end): custom Python agents apparently cannot raise Switch approval cards, which belong to Console-run agents such as Claude Code. For the scripted agents, the gate is a targeted message to the owner plus an addressed reply, enforced by Switch's addressing policy. Real approval cards appear only in the recorded run, where Alice is real Claude Code.
2. **The judge path reproduces a Node-version bug, not the case bug.** The primary bug is `toSorted()` (UNVERIFIED until run). The case-only import is the recorded real-Mac run. Reproducing it in the judge path needs the privileged vfat mount, which is untested on Linux, macOS and WSL2 Docker Desktop. If that mount fails, the judge path keeps the Node bug.
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

---

## Key Links

- [Hackathon Page](https://www.wemakedevs.org/hackathons/switch)
- [DevTools Academy Page](https://www.devtoolsacademy.com/hackathons/flip-the-switch)
- [Switch GitHub](https://github.com/sandbox-quantum/switch)
- [Switch Trust CLI](https://github.com/sandbox-quantum/switch-trust-cli)
- [Switch Agent Protocol](https://github.com/sandbox-quantum/switch/blob/main/docs/official/internals/agent-protocol.md)
- [Remote Host Setup](https://github.com/sandbox-quantum/switch/blob/main/docs/official/deploy/host-remotely.md)
- [Wispr Flow](https://wisprflow.ai)
