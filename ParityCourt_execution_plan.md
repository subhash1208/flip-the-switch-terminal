
# Context

- The test was a positive sign. santha received a message from Mattermost, ran a shell command on Santhan's Mac and reported back. That's the core loop ParityCourt needs.
- Two problems showed up:
  a. No [Allow] button appeared. Auto-approve is still effectively ON. The whole demo depends on these buttons (spec Steps 2 and 7), so this is blocker #1.
  b. santha runs in /Users/santhan/.switch/agents/localhost-64640/santha, which isn't a git repo. It needs to work inside a clone of the project.
- We're one day behind docs/TIMELINE.md. It's Nov 5 and the repo has only docs. We have about 2.5 days, and submission is due Nov 7, 6 PM IST.
- Hardware: only Santhan has a Mac. Switch Console, the local Switch server, the bundled Mattermost and every agent run on the Mac. The Switch server is local, so it's only reachable from the Mac. Subhash, Vatsav and Hashwanth (Windows) write code and tests on Windows, push branches, and Santhan pulls and runs everything.
- Decisions made: chat = bundled Mattermost; Linux "Bob" box = Ubuntu Docker container on the Mac, connected over SSH; second agent = a non-Codex CLI agent (which one is still open, see Phase 0); all 4 people are active.

# Phase 0: Unblock (today, first ~2 hours, everyone in parallel)

Each item has a pass/fail gate. Nobody starts Phase 1 work that depends on a gate that hasn't passed.

```text
┌─────────────┬────────────────────────────────────────────────────────────────────────────────────────────┬──────────────────────────────────────────┐
│     Who     │                                            Task                                            │                   Gate                   │
├─────────────┼────────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────┤
│ Santhan     │ Turn off Auto-approve and Auto mode for santha, both on the agent's settings and in        │ An [Allow] button appears, and nothing   │
│ (Mac)       │ Console Settings. Re-send @santha run git status.                                          │ runs until it's tapped                   │
├─────────────┼────────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────┤
│             │ Clone the repo on the Mac (e.g. ~/parity/flip-the-switch-terminal). Re-register or restart │                                          │
│ Santhan     │  the agent with that folder as its working directory, or tell it the path in its           │ git status from the agent shows the repo │
│             │ instructions. Rename it alice-claude if Console allows.                                    │                                          │
├─────────────┼────────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────┤
│ Santhan +   │ Confirm which CLI agents Switch Console 0.40.1 supports as providers (Console's            │ A second agent appears in Console and    │
│ Hashwanth   │ agent-creation list and the Switch docs). Pick the second vendor for "Bob". Fallback:      │ replies in a room                        │
│             │ Claude Code for both agents.                                                               │                                          │
├─────────────┼────────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────┤
│             │ Ubuntu 24.04 container on the Mac with openssh-server, git, Node ≥ 22.13. Onboard it in    │ The second agent runs inside the         │
│ Vatsav      │ Console as a remote host (Switch docs: "Onboard a remote host"). Can be written on         │ container and uname -a shows Linux       │
│             │ Windows, but must be tested on the Mac.                                                    │                                          │
├─────────────┼────────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────┤
│             │                                                                                            │ Both commands run on a sample file. If   │
│ Hashwanth   │ Install switch-trust-cli (Windows is fine). Confirm scan and eval exist, then record their │ either doesn't exist, tell the team      │
│             │  real CLI flags and output format into docs/SWITCH-TRUST-NOTES.md.                         │ immediately. Step 5 of the demo depends  │
│             │                                                                                            │ on it                                    │
├─────────────┼────────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────┤
│             │ Read the Switch Agent Protocol doc (docs/official/internals/agent-protocol.md in the       │ This file becomes the shared contract    │
│ Subhash     │ switch repo). Write down the exact SSE event and HTTP action shapes in                     │ for the Bailiff and its tests            │
│             │ docs/PROTOCOL-NOTES.md.                                                                    │                                          │
└─────────────┴────────────────────────────────────────────────────────────────────────────────────────────┴──────────────────────────────────────────┘
```

# Phase 1: Build the pieces (rest of Nov 5)

Everyone works on separate files on their own branch (feature/<name>/<desc>, per CONTRIBUTING.md).

```text
┌───────────┬─────────────────────────────────────────────────────────────────┬────────────────────────────────────┬──────────────────────────────────┐
│    Who    │                             Builds                              │               Where                │            Done when             │
├───────────┼─────────────────────────────────────────────────────────────────┼────────────────────────────────────┼──────────────────────────────────┤
│ Santhan   │ sample-app/ (Node export-service) with the 3 planted bugs from  │ Mac                                │ npm test passes on the Mac and   │
│           │ the spec                                                        │                                    │ fails in the Linux container     │
├───────────┼─────────────────────────────────────────────────────────────────┼────────────────────────────────────┼──────────────────────────────────┤
│ Subhash   │ bailiff/: SSE client, HTTP actions, state machine, 6-turn loop  │ Windows (develops against recorded │ Opens a case and summons both    │
│           │ breaker                                                         │  SSE fixtures), runs on the Mac    │ agents in a real room            │
├───────────┼─────────────────────────────────────────────────────────────────┼────────────────────────────────────┼──────────────────────────────────┤
│ Hashwanth │ tests/ (pytest, using fixtures from PROTOCOL-NOTES.md) +        │ Windows                            │ First 10 tests pass; redaction   │
│           │ bailiff/trust.py wrapper around switch-trust scan/eval          │                                    │ works on a fake env dump         │
├───────────┼─────────────────────────────────────────────────────────────────┼────────────────────────────────────┼──────────────────────────────────┤
│           │ deploy/docker-compose.yml, deploy/ssh-setup.sh, justfile        │                                    │ just linux-up brings up the      │
│ Vatsav    │ skeleton                                                        │ Windows → tested on the Mac        │ container that Console connects  │
│           │                                                                 │                                    │ to                               │
└───────────┴─────────────────────────────────────────────────────────────────┴────────────────────────────────────┴──────────────────────────────────┘
```

# Shared contract (decide before splitting up):
- Event and action shapes come from PROTOCOL-NOTES.md.
- The Bailiff reads its Switch server URL and credentials from env vars.
- Agent handles: @alice-claude, @bob-<vendor>, @bailiff.

# Phase 2: Integrate on the Mac (Nov 6)

Integration happens on Santhan's Mac. The Windows teammates follow along over a screen share and push fixes to their branches.

Build the demo in rungs. Each rung is a complete, demoable flow. Record a backup video the moment a rung works.

1. Rung 1 (must have): Step 1 open case → Step 2 fingerprints with [Allow] buttons → Step 3 Trust redaction + env diff → Step 8 verdict.
2. Rung 2: + Step 4 one-variable ablation in the Linux container.
3. Rung 3: + Step 5 Trust security hold → Step 6 fix on the Mac and verification on Linux → Step 7 dual sign-off.

Same day: the pytest suite reaches 25+ tests, and the hand-written room template goes in templates/parity-court.template.yaml.

# Phase 3: Package and submit (Nov 6 night → Nov 7, 6 PM IST)

- just demo tested from a clean clone on the Mac.
- README with GIF, architecture, quickstart and test badge.
- 2:30 video (product working within the first 25 seconds; closing line from the spec).
- Blog post, #HowISwitch clip, Wispr screenshots.
- Submit by 6 PM IST.

# Ideas that improve our chances

- Make the human gate visible: both [Allow] buttons on screen, a red Trust BLOCK, then a green PASS. That covers the 30% "Use of Switch" score, so protect these moments above everything else.
- Real wire-level Bailiff + tests = Technical Execution (25%). Keep the Bailiff small (~250 lines), as the blog promises.
- Optional extra: Telegram already works. A 5-second "the trial also runs from your phone" shot shows the same room on two platforms.
- Cut, don't slip: if it's Nov 6 evening and Rung 3 isn't solid, ship Rung 2 with a polished video.

# Verification

- Phase 0: each gate in the table, shown on the Mac (screenshots in the team chat).
- Code: pytest passes on Windows (Bailiff + Trust wrapper); npm test passes on the Mac and fails in the container.
- End to end: on the Mac, just demo → post "Open Case #101" in Mattermost → watch every rung's steps complete, with the [Allow] buttons appearing and Trust redacting and then blocking.
- Final: from a fresh clone, run just demo again before recording.
