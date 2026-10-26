# ParityCourt

**Two Machines. Three Agents. Zero Trust Gaps. One Verdict.**

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

The person with the working machine can't see the failing machine. The person with the failing machine doesn't know what to look for. Meanwhile the feature branch is blocked, the PR is stuck, and if it's near a release, everyone's stressed.

**The real cost isn't the bug. It's the human ping-pong.** What takes an afternoon of relay collapses to minutes when agents on each machine can talk directly and humans just approve the actions.

---

## What ParityCourt Does

ParityCourt turns cross-environment debugging into a structured courtroom trial. Three agents in a Switch room investigate the bug together — one on each machine, plus a custom arbiter that controls the process.

When a bug only appears on one machine, the Bailiff opens a case, summons both machine agents, and runs a forensic investigation. Each agent fingerprints its own machine, the Bailiff compares the environments, isolates the root cause through one-variable-at-a-time ablation, scans for security vulnerabilities using Switch Trust CLI, and enforces dual human sign-off before the fix ships.

**Delete Switch and these agents can't see each other's machines.**

---

## The Three Agents

### Agent 1: `@alice-claude` (Role: `baseline-counsel`)

- **What it is:** Claude Code running on Alice's macOS machine via Switch Console
- **What it does:** Fingerprints the Mac environment (OS, Node version, filesystem type, env vars, lockfile hashes). When the root cause is found, it writes the code fix, adds a pre-commit hook to prevent recurrence, and pushes the PR branch.
- **Who controls it:** Only Alice can tap the `[Allow]` button for probes on her machine.

### Agent 2: `@bob-codex` (Role: `forensic-prosecutor`)

- **What it is:** Codex running on Bob's Ubuntu 24.04 box, connected to Switch over SSH using the remote-host controller
- **What it does:** Fingerprints the Linux environment. Runs the one-variable-at-a-time ablation loop to isolate the root cause. Pulls and verifies the fix on Linux after Alice's agent writes it.
- **Who controls it:** Only Bob can tap the `[Allow]` button for probes on his machine.

### Agent 3: `@bailiff` (Role: `court-arbiter`)

- **What it is:** A custom ~250-line Python agent built directly on the Switch Agent Protocol (SSE events down, HTTP actions up)
- **What it does:**
  - Opens and closes cases
  - Enforces a 6-turn loop breaker (prevents agents from messaging each other forever)
  - Runs `switch-trust scan` to redact leaked secrets (API keys, passwords) from env dumps before posting to the room
  - Runs `switch-trust eval` to check for security vulnerabilities in the fixed code
  - Writes the final Verdict Document to the room's shared context
- **Who controls it:** Responds to both humans; orchestrates the entire trial

---

## Why Switch Is Essential (The 30% Rubric Answer)

Switch is the only platform that puts agents running on **different physical machines**, from **different AI vendors**, into a single conversation room where **humans approve every action with chat buttons**.

Without Switch:
- Alice's agent (Claude Code on Mac) cannot see Bob's Linux filesystem
- Bob's agent (Codex on Linux) cannot see Alice's working baseline
- There's no shared room to post environment diffs into
- There's no approval mechanism for humans to gate agent actions
- There's no way for the Bailiff to orchestrate turn-taking between agents

No other tool — not Slack, not a shared terminal, not a webhook — can replicate this. Switch is the architecture, not a wrapper.

---

## The 8-Step Flow

Here's exactly what happens in a ParityCourt trial, step by step:

### Step 1 — Opening the Case

Bob reports: "@bailiff Open Case #101: The `export-service` auth middleware passes all tests on Alice's Mac but throws a 500 `AuthVerifierError` on my Ubuntu 24.04 staging box."

The Bailiff creates a Room Document called **Case #101 Evidence Ledger**, sets the turn counter to 0/6, and summons both agents by role.

### Step 2 — Cross-Machine Fingerprinting

Both agents request permission to inspect their machines:
- `@alice-claude` asks to run: `uname -a`, `node -v`, `git config core.ignorecase`, `cat .env`, `diskutil info /`
- `@bob-codex` asks to run: `uname -a`, `node -v`, `env`, `stat -f -c %T .`

**Each probe shows an `[Allow]` button that only that machine's owner can tap.** Alice approves Mac probes. Bob approves Linux probes. Auto-approve is OFF so judges see both buttons fire live.

### Step 3 — Secret Redaction and Environment Diff

Both agents return raw fingerprints. Before posting the diff, the Bailiff's embedded Switch Trust guardrail intercepts Bob's raw `env` output:

> 🛡️ **SWITCH TRUST GUARDRAIL:** Redacted `STRIPE_LIVE_SECRET=sk_live_99a...` and `DATABASE_PASSWORD` from @bob-codex's environment probe before writing to shared room history.

The Bailiff posts the clean **env-diff-case-101.md** to Room Documents, isolating 3 suspect differences:

| Suspect | Mac | Linux | Verdict |
|---------|-----|-------|---------|
| A — Timezone/Locale | `TZ=Asia/Kolkata` (`en_IN.UTF-8`) | `TZ=UTC` (`C.UTF-8`) | Decoy |
| B — Stale Shell Flag | Not set | `NODE_OPTIONS=--openssl-legacy-provider` | Decoy |
| C — Filesystem Case | APFS (case-insensitive) | ext4 (case-sensitive) | **Culprit** |

### Step 4 — One-Variable Ablation on Linux

The Bailiff tells `@bob-codex` to toggle one suspect at a time on the Linux box:

- Ablation 1: Set `TZ=Asia/Kolkata` → Still fails ❌ (Decoy 1 cleared)
- Ablation 2: Unset `NODE_OPTIONS` → Still fails ❌ (Decoy 2 cleared)
- Ablation 3: Symlink `SqlAuthGuard.ts` → `sqlAuthGuard.ts` → App boots ✅

Root cause isolated: the import `from './security/SqlAuthGuard'` resolves on case-insensitive macOS but fails on case-sensitive Linux ext4.

### Step 5 — The Twist: Switch Trust Security Scan

Now that the import is loading on Linux, the Bailiff automatically runs `switch-trust scan` and `switch-trust eval` against `security/sqlAuthGuard.ts`:

> 🛑 **SWITCH TRUST SECURITY HOLD (Scan: 85% | Eval: 68% — BLOCKED)**
>
> Finding [OWASP ASI-01 / Prompt-to-SQL Injection]: The sanitizer in `sqlAuthGuard.ts` can be bypassed using Unicode full-width homoglyphs (`ＳＥＬＥＣＴ * ＦＲＯＭ customers`). Furthermore, because the import was failing silently into a fallback stub on staging, staging was running with zero SQL sanitization.
>
> Order to @alice-claude: (1) Fix the case-sensitive import + set `git config core.ignorecase false`, AND (2) Add `String.prototype.normalize('NFKC')` + parameterized query binding inside `sqlAuthGuard.ts`.

This is the demo's climax. What started as a "works on my machine" typo turned into a production-breaking security vulnerability.

### Step 6 — Cross-Vendor Fix and Verification

`@alice-claude` (Claude Code on Mac) writes both fixes:
- Case-sensitivity fix: corrects the import path + adds a pre-commit hook blocking case-mismatched imports
- Security fix: adds NFKC Unicode normalization + parameterized query binding

Pushes branch `fix/case-101-parity-and-asi01`.

`@bob-codex` (Codex on Linux) pulls the branch, runs `npm test` (18/18 passing), and the Bailiff re-runs `switch-trust eval`:

> 🟢 **SWITCH TRUST PASSED (Scan: 99% | Eval: 97% | 0 ASI findings | Linux + Mac 100% Parity)**

### Step 7 — Dual Human Sign-Off

- `@alice-claude` requests permission from Alice to open & merge PR #42. Alice taps `[Allow]`.
- `@bailiff` requests sign-off from Bob to close Case #101. Bob taps `[Allow]`.

Two humans, two machines, explicit consent on both sides.

### Step 8 — Verdict and ROI Telemetry

The Bailiff writes the permanent Verdict Document to the room's shared context:

> ⚖️ **VERDICT #101 ENTERED:** Root cause: APFS vs. ext4 case-sensitivity masking an unnormalized OWASP ASI-01 Unicode SQL injection flaw. Fixed on Mac, verified on Linux, guarded by Switch Trust.
>
> 📊 **Switch ROI Telemetry:** 2 machines · 3 agents · 3 ablation runs · 2 secrets redacted · Session cost: $0.17 (Est. 6 hrs cross-team debugging + 1 Sev-1 breach prevented)
>
> *Delete Switch, and these agents can't see each other's machines.*

---

## The Sample App (Planted Bugs)

We build a small Node.js `export-service` with auth middleware. It contains 3 planted issues — 2 decoys and 1 real culprit with a hidden security flaw:

### Bug 1 — Decoy: Timezone/Locale
- Mac has `TZ=Asia/Kolkata`, Linux has `TZ=UTC`
- Looks suspicious but doesn't cause the crash
- Agents investigate and rule it out

### Bug 2 — Decoy: Stale Shell Flag
- Linux `.bashrc` has `NODE_OPTIONS=--openssl-legacy-provider`
- Again suspicious but not the cause
- Agents investigate and rule it out

### Bug 3 — The Real Culprit: Case-Sensitive Import + Unicode SQL Injection
- File on disk: `security/sqlAuthGuard.ts`
- Import in code: `from './security/SqlAuthGuard'`
- On macOS (APFS, case-insensitive): resolves fine, app works
- On Linux (ext4, case-sensitive): import fails, falls back to a stub with zero SQL sanitization
- Hidden inside the now-loading file: the sanitizer doesn't normalize Unicode, allowing homoglyph SQL injection (`ＳＥＬＥＣＴ * ＦＲＯＭ customers`)
- This means staging has been running with no SQL protection at all

The decoys make the diagnosis non-trivial. The security twist makes the stakes real.

---

## The Custom Bailiff Agent

The Bailiff is ~250 lines of Python built directly on the Switch Agent Protocol:

- **Inbound:** Server-Sent Events (SSE) stream from Switch
- **Outbound:** HTTP POST actions back to Switch
- **Loop breaker:** Caps agent-to-agent turns at 6 to prevent infinite messaging loops
- **Secret redactor:** Pipes env dumps through `switch-trust scan` before posting to the room
- **Security gate:** Runs `switch-trust eval` on code changes before allowing PRs
- **State machine:** Tracks case lifecycle (OPEN → FINGERPRINTING → ABLATION → SECURITY_SCAN → FIX → VERIFY → VERDICT)

This matters because:
1. Switch has no built-in timer/trigger system — the Bailiff fills that gap
2. Switch has no loop prevention — the Bailiff enforces turn limits
3. There's no reference custom agent in the Switch repo — the Bailiff IS that reference
4. It proves deep understanding of the Switch protocol at the wire level (SSE + HTTP)
5. It's the blog post: "Build a Custom Switch Agent in 250 Lines"

---

## How Judges Reproduce It

Judges don't need a Mac and a Linux box. Everything runs on one machine:

1. **The "second machine"** is an Ubuntu 24.04 Docker container with SSH access, connected to Switch via the remote-host controller
2. **One command:** `just demo` bootstraps everything
3. **Chat platform:** Uses the Mattermost that Switch bundles — no Slack workspace needed
4. **Room template:** Hand-written v2 YAML (Switch Console's "Capture as template" strips agent instructions, so we write it ourselves)
5. **Version pinned:** Switch Console 0.40.1 / switch-core 0.31.0 / switch-agent-controller 0.31.0-rc.6
6. **Auto-approve OFF:** So the `[Allow]` buttons appear on every probe

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Switch Console | v0.40.1 (desktop app) |
| Switch Core | v0.31.0 (self-hosted via Docker) |
| Switch Trust CLI | v1.7.2 (`switch-trust scan` + `switch-trust eval`) |
| Chat Platform | Mattermost (bundled with Switch) |
| Agent 1 | Claude Code (macOS host) |
| Agent 2 | Codex (Ubuntu 24.04 SSH container) |
| Agent 3 (Bailiff) | Custom Python (~250 lines, SSE/HTTP protocol) |
| Sample App | Node.js `export-service` with auth middleware |
| Tests | pytest (25+ unit tests for Bailiff) |
| Room Template | Hand-written v2 YAML |
| Setup | `just demo` one-command bootstrapper |

---

## Why This Wins

| Rubric (weight) | How ParityCourt scores |
|-----------------|----------------------|
| **Use of Switch (30%)** | Two physical machines (Mac + Linux SSH), two AI vendors (Claude + Codex), one custom SSE/HTTP agent, per-owner approval buttons, Switch Trust scan/eval. Remove Switch and nothing works. |
| **Technical Execution (25%)** | One-command `just demo` setup, 25+ pytest tests, hand-written v2 room template, clean two-environment architecture reproducible on one laptop via Docker. |
| **Creativity & Impact (25%)** | Universal pain point ("works on my machine") elevated to a security story (Unicode homoglyph SQL injection found by Switch Trust). Every developer has lived this. |
| **Presentation (20%)** | 8-step courtroom narrative designed for a 2:30 video. Visual moments: two `[Allow]` buttons, red Trust BLOCK → self-heal → green PASS, side-by-side Mac vs Linux terminal, closing line. |

---

## Prize Stacking

ParityCourt is the Track 01 submission. We stack everything else on top:

| Prize | How we get it |
|-------|--------------|
| **Track 01 ($2,000)** | ParityCourt submission |
| **Code with Wispr ($500)** | Dictate all prompts, room instructions, README, and blog post via Wispr Flow from Day 1. Submit Insights screenshot. |
| **Best Blog (AirPods 5)** | "Build a Custom Switch Agent in 250 Lines" — a first-timer tutorial using the Bailiff as the example |
| **#HowISwitch (Logitech keyboard)** | 60-second highlight clip on X and LinkedIn, tag @switchagents_ai @WeMakeDevs @DevToolsAcademy |
| **Track 03 ($100 each)** | 1-3 core PRs on hackathon-labelled issues (start before Nov 4 — this is allowed) |
| **Swag (random draw)** | Every submission is entered automatically |
| **Certificate** | Every submission gets one |

---

## Important Rules and Gotchas

1. **No project code before Nov 4.** The Switch setup and workflow must be built during Nov 4–7. Your git history must start on Nov 4. Environment setup and Track 03 PRs are OK before that.

2. **Auto-approve and Auto-mode must be OFF** in Switch Console, otherwise the approval buttons never render in chat.

3. **Console's "Capture as template" strips agent instructions and permissions.** Hand-write the v2 room template YAML.

4. **Task-delegation APIs have been removed from Switch.** Use `@-mentions` by role to direct messages to specific agents.

5. **docs.switchagents.ai may be down (503).** The same docs exist in the repo at `docs/official/`.

6. **Switch Trust CLI is brand new (launched Oct 19, 2026).** Most competitors won't know it exists. This is our differentiator.

7. **Submit by ~6 PM IST on Nov 7** — 5+ hours before the 11:59 PM deadline to avoid server issues.

8. **The demo video closing line is:** "Delete Switch, and these agents can't see each other's machines."

---

## Key Links

- [Hackathon Page](https://www.wemakedevs.org/hackathons/switch)
- [DevTools Academy Page](https://www.devtoolsacademy.com/hackathons/flip-the-switch)
- [Switch GitHub](https://github.com/sandbox-quantum/switch)
- [Switch Trust CLI](https://github.com/sandbox-quantum/switch-trust-cli)
- [Switch Agent Protocol](https://github.com/sandbox-quantum/switch/blob/main/docs/official/internals/agent-protocol.md)
- [Remote Host Setup](https://github.com/sandbox-quantum/switch/blob/main/docs/official/deploy/host-remotely.md)
- [Hackathon Issues (Track 03)](https://github.com/sandbox-quantum/switch/issues?q=is%3Aissue+state%3Aopen+label%3Ahackathon)
- [Wispr Flow](https://wisprflow.ai)
