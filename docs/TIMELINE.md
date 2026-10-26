# Development Timeline & Work Split

Team: Terminal
Hackathon: Flip the Switch (Nov 4–7, 2026)

---

## Team Members

| Name | Role | Machine | Primary Tools |
|------|------|---------|---------------|
| **Subhash** | Team Lead | Windows | Claude Code, Kiro, Copilot |
| **Santhan** | Developer | **macOS** | Claude Code, Kiro, Copilot |
| **Vatsav** | Developer | Windows | Claude Code, Kiro, Copilot |
| **Hashwanth** | Developer | Windows | Claude Code, Kiro, Copilot |

**Important:** Santhan is on macOS. This is critical because ParityCourt needs a Mac host for `@alice-claude`. Santhan's machine IS Alice's machine in the demo.

---

## Work Assignment Overview

| Person | Primary Responsibility | Secondary |
|--------|----------------------|-----------|
| **Subhash** | Bailiff agent (Python, SSE/HTTP protocol) + overall integration | Demo video script + submission |
| **Santhan** | Mac-side setup (`@alice-claude` + Switch Console) + sample app | Blog post |
| **Vatsav** | Linux SSH container setup (`@bob-codex`) + Docker/infra | Room template YAML + `just demo` bootstrapper |
| **Hashwanth** | pytest suite (25+ tests for Bailiff) + Switch Trust CLI integration | README + #HowISwitch social post |

Everyone installs and uses **Wispr Flow** from Day 1 for all prompts.

---

## Phase 0: Before Nov 4 (Now → Nov 3)

**Rules reminder: Write ZERO project code before Nov 4.** Environment setup and Track 03 PRs are allowed.

### Everyone (parallel)

- [ ] Install Wispr Flow (use the hackathon's 1-month Pro free link)
- [ ] Practice dictating prompts to your coding agent via Wispr
- [ ] Install and pin **Switch Console 0.40.1** from [releases](https://github.com/sandbox-quantum/switch/releases)
- [ ] Read the [10-minute quickstart](https://www.wemakedevs.org/hackathons/switch/resources)
- [ ] Read `docs/PARITYCOURT.md` in this repo — understand the full 8-step flow
- [ ] Join the [WeMakeDevs Discord](https://discord.gg/wemakedevs) for hackathon support

### Subhash (Team Lead)

- [ ] Read the [Switch Agent Protocol docs](https://github.com/sandbox-quantum/switch/blob/main/docs/official/internals/agent-protocol.md) — understand SSE events and HTTP actions
- [ ] Sketch the Bailiff state machine on paper: OPEN → FINGERPRINT → ABLATION → SECURITY_SCAN → FIX → VERIFY → VERDICT
- [ ] Read `switch-trust-cli` README and understand `scan` and `eval` commands
- [ ] Optionally start a Track 03 PR (issue #801 — deliver mid-turn messages — Python core work)

### Santhan (macOS)

- [ ] Do the Switch quickstart in a throwaway room on your Mac — get Claude Code connected as an agent
- [ ] Verify Switch Console 0.40.1 runs correctly on your macOS
- [ ] Confirm you can create a room, add an agent, and see approval buttons (with Auto-approve OFF)
- [ ] Optionally start a Track 03 PR (issue #779 — add Kiro CLI as agent provider)

### Vatsav

- [ ] Spin up an Ubuntu 24.04 Docker container with `openssh-server`, `git`, `Node >= 22.13`
- [ ] Test SSH connectivity from Switch Console to the container using a non-localhost bridge IP
- [ ] Follow [host-remotely.md](https://github.com/sandbox-quantum/switch/blob/main/docs/official/deploy/host-remotely.md) to connect a remote agent
- [ ] Optionally start a Track 03 PR (issue #780 — add Goose as agent provider)

### Hashwanth

- [ ] Install `switch-trust-cli` (`pip install switch-trust-cli`) and verify `switch-trust scan` works locally
- [ ] Read the [Switch Trust CLI repo](https://github.com/sandbox-quantum/switch-trust-cli) — understand scan vs eval
- [ ] Read the `triage-pair.template.yaml` from the [resources page](https://www.wemakedevs.org/hackathons/switch/resources) — understand what we need to differentiate from
- [ ] Optionally start a Track 03 PR (issue #806 — prettify agent controller CLI output)

### Nov 2 — Kickoff Live Stream (3:30 PM UK time)

Everyone attends. Ask these questions in chat:
1. Can one team submit to both Track 01 AND Track 02?
2. Confirm Track 03 PR assignment rules
3. Any updates to judging criteria or prizes?

---

## Phase 1: Day 1 — Wednesday, Nov 4

**Goal by end of day:** All three agents connected in one Switch room. The Bailiff can open a case and summon agents. Fingerprinting works on both machines.

### Morning (4 hours)

| Person | Task | Output |
|--------|------|--------|
| **Subhash** | Initialize the git repo (first commit after 12:01 AM IST). Start building the Bailiff agent — SSE connection to Switch, event parser, HTTP action sender, case lifecycle state machine. | `bailiff/agent.py` — connects to Switch, parses events, sends messages |
| **Santhan** | Build the sample `export-service` Node.js app with the 3 planted bugs: (1) timezone decoy, (2) stale NODE_OPTIONS decoy, (3) case-sensitive import `SqlAuthGuard` vs `sqlAuthGuard.ts` with the Unicode homoglyph SQL injection inside. | `sample-app/` — a working Node.js app that passes tests on Mac, fails on Linux |
| **Vatsav** | Set up the Docker infrastructure: `docker-compose.yml` with Ubuntu 24.04 SSH container + Switch's bundled Mattermost. Configure SSH keys and bridge networking so Switch Console can reach the container. | `deploy/docker-compose.yml` + `deploy/ssh-setup.sh` |
| **Hashwanth** | Write the v2 room template YAML by hand: define all 3 agent roles (`baseline-counsel`, `forensic-prosecutor`, `court-arbiter`), addressing rules (`owner-agents` for machine agents, `anyone` for bailiff), and permission gates. | `templates/parity-court.template.yaml` |

### Afternoon (4 hours)

| Person | Task | Output |
|--------|------|--------|
| **Subhash** | Add the 6-turn loop breaker to the Bailiff. Implement the fingerprinting orchestration (Bailiff tells each agent what to inspect, collects results). | Bailiff can orchestrate Steps 1-2 of the flow |
| **Santhan** | Connect `@alice-claude` (Claude Code on Mac) to the Switch room via Switch Console. Verify it can receive messages from the Bailiff and respond. Disable Auto-approve and Auto-mode. | `@alice-claude` responds to fingerprint requests with real Mac env data |
| **Vatsav** | Connect `@bob-codex` (Codex on Linux container) to Switch via SSH remote-host controller. Clone the sample app into the container. Verify it crashes on Linux. | `@bob-codex` responds to fingerprint requests with real Linux env data |
| **Hashwanth** | Start writing pytest tests for the Bailiff: SSE event parser tests, loop-breaker counter tests, state machine transition tests. | `tests/test_bailiff.py` — first 10 tests passing |

### End of Day 1 Checkpoint

- [ ] All 3 agents visible in the Switch room on Mattermost
- [ ] Bailiff can open a case and summon agents by role
- [ ] Both machine agents respond to fingerprint requests
- [ ] Human approval buttons appear (Auto-approve is OFF)
- [ ] Sample app works on Mac, crashes on Linux
- [ ] First 10 pytest tests passing

---

## Phase 1: Day 2 — Thursday, Nov 5

**Goal by end of day:** The full 8-step flow works end-to-end. Switch Trust integration is live. All tests pass.

### Morning (4 hours)

| Person | Task | Output |
|--------|------|--------|
| **Subhash** | Implement the environment diff logic in the Bailiff — compare both fingerprints, identify suspects, post the diff table as a Room Document attachment. Implement the ablation orchestration (tell Bob's agent to toggle one variable at a time). | Steps 3-4 of the flow working |
| **Santhan** | Implement Alice's agent behavior for Step 6: when the Bailiff orders a fix, `@alice-claude` writes the code fix (import path correction + NFKC normalization + pre-commit hook), commits, and pushes a branch. | `@alice-claude` can write and push the fix on command |
| **Vatsav** | Implement Bob's agent behavior for Step 4 (ablation — toggle env vars one at a time, re-run the app, report pass/fail) and Step 6 (pull the fix branch, run `npm test`, report results). | `@bob-codex` can run ablation and verify fixes |
| **Hashwanth** | Integrate `switch-trust-cli` into the Bailiff: (1) secret redaction — pipe env dumps through `switch-trust scan` before posting, (2) security gate — run `switch-trust eval` on the fixed code before allowing PR. | Bailiff's Step 3 redacts secrets, Step 5 catches the Unicode homoglyph |

### Afternoon (4 hours)

| Person | Task | Output |
|--------|------|--------|
| **Subhash** | Wire together the full 8-step flow end-to-end. Run through the entire courtroom trial from Step 1 to Step 8. Debug any handoff issues between agents. | Full flow works start to finish |
| **Santhan** | Implement the dual human sign-off (Step 7): Alice approves the PR merge, Bob approves case closure. Both via chat buttons. | Step 7 approval buttons work |
| **Vatsav** | Build the `just demo` one-command bootstrapper: starts Docker containers, sets up SSH, launches Switch + Mattermost, seeds the room with the template, prints instructions. | `justfile` with `just demo` command — judges run this one command |
| **Hashwanth** | Complete the pytest suite: add tests for secret redaction, Switch Trust scan/eval integration, ablation state tracking, verdict document generation. Target: 25+ tests. | `tests/` — 25+ tests, all passing |

### End of Day 2 Checkpoint

- [ ] Full 8-step flow works end-to-end on Mattermost
- [ ] Switch Trust redacts secrets in Step 3
- [ ] Switch Trust blocks the PR in Step 5 (Unicode homoglyph detection)
- [ ] Both human approval button pairs work (Step 2 + Step 7)
- [ ] `just demo` bootstraps everything from scratch
- [ ] 25+ pytest tests passing
- [ ] Verdict document posts correctly with ROI telemetry

**DECISION POINT:** If the flow is solid, one person (Vatsav) can spend Day 3 morning adapting it for Track 02 (LaunchForge Studio). If not, everyone stays on ParityCourt polish.

---

## Phase 1: Day 3 — Friday, Nov 6

**Goal by end of day:** Demo video recorded. README complete. Blog post drafted. Social posts ready.

### Morning (4 hours)

| Person | Task | Output |
|--------|------|--------|
| **Subhash** | Test a clean install: delete everything, run `just demo`, verify the full flow works in under 3 minutes. Fix any issues. Write the demo video script — exactly what happens at each timestamp (2:30 total). | Clean install verified. Video script finalized. |
| **Santhan** | Draft the blog post: "Build a Custom Switch Agent in 250 Lines." Use the Bailiff code as the example. Structure: why → protocol explained → step-by-step build → testing → running in a room. | Blog post draft (~1500 words) |
| **Vatsav** | Write the README.md: hero GIF at top, one-paragraph pitch, architecture diagram (text-based), "How Switch Is Used" section, `just demo` quickstart, `pytest: 28 passed` badge, limitations section. | `README.md` complete |
| **Hashwanth** | Run the full flow one more time and record raw screen footage. Capture: both terminals (Mac + Linux), Mattermost chat with approval buttons, Switch Trust block/pass moments, the verdict card. | Raw recording footage (~10 minutes of material) |

### Afternoon (4 hours)

| Person | Task | Output |
|--------|------|--------|
| **Subhash** | Edit the demo video: cut to 2:30, add any text overlays if needed, include 5-second Wispr picture-in-picture, ensure the product is working within the first 25 seconds, closing line at the end. | `demo-video.mp4` — 2:30, 1080p |
| **Santhan** | Review and polish the blog post. Test all code snippets in the post. Publish on Dev.to or Hashnode. | Blog post live with URL |
| **Vatsav** | Polish the README. Add the demo video link/GIF. Verify all links work. Do a final `just demo` clean install test. | README finalized |
| **Hashwanth** | Cut the 60-second #HowISwitch highlight clip from the demo footage. Write the social media caption. Prepare the Wispr Insights screenshots from everyone's machines. | Social post draft + Wispr screenshots collected |

### End of Day 3 Checkpoint

- [ ] Demo video (2:30) recorded, edited, and ready
- [ ] README complete with GIF, architecture, quickstart, and test badge
- [ ] Blog post published and URL saved
- [ ] #HowISwitch clip and caption ready to post
- [ ] Wispr Insights screenshots collected from all 4 team members
- [ ] Clean install works from scratch via `just demo`

---

## Phase 1: Day 4 — Saturday, Nov 7

**Goal: Submit everything by 6 PM IST.** Five hours before the 11:59 PM deadline.

### Morning (3 hours)

| Person | Task | Output |
|--------|------|--------|
| **Subhash** | Final review of all submission materials. Verify demo video plays correctly. Verify repo is public and cloneable. Do one last `just demo` dry run. | Everything verified |
| **Santhan** | Post the #HowISwitch clip on X and LinkedIn. Tag @switchagents_ai, @WeMakeDevs, @DevToolsAcademy. Share from personal account too. | Social posts live |
| **Vatsav** | Verify all Track 03 PRs are open and linked to their issues with `Closes #number`. Check that CLA is signed. | Track 03 PRs confirmed |
| **Hashwanth** | Compile the Wispr Insights screenshots into one image/document. Final proofread of README and blog post for typos. | Wispr proof ready |

### Afternoon — Submit by 6 PM IST

| Person | Task |
|--------|------|
| **Subhash** | Submit ParityCourt to Track 01. Attach: repo link, demo video, Wispr scorecard, blog post URL. |
| **Everyone** | Review the submission together before Subhash hits submit. |
| **Subhash** | If Track 02 (LaunchForge Studio) was built, submit it separately. |

---

## Parallel Work Streams (Visual Overview)

```
           Day 1              Day 2              Day 3              Day 4
         ─────────          ─────────          ─────────          ─────────

Subhash  [Bailiff agent   ] [Full flow wiring ] [Video script +  ] [Final review   ]
         [SSE/HTTP + loop  ] [end-to-end debug ] [video editing   ] [Submit by 6 PM ]
         [breaker          ] [                 ] [                ] [               ]

Santhan  [Sample app with  ] [Alice fix logic + ] [Blog post draft ] [Social posts   ]
(macOS)  [planted bugs     ] [dual sign-off     ] [+ publish       ] [               ]
         [+ Console setup  ] [approval buttons  ] [                ] [               ]

Vatsav   [Docker + SSH     ] [`just demo`      ] [README.md       ] [Track 03 PR    ]
         [Linux container  ] [bootstrapper     ] [+ clean install ] [verification   ]
         [setup            ] [                 ] [test            ] [               ]

Hashwanth[Room template    ] [pytest suite 25+ ] [Screen recording] [Wispr proofs + ]
         [YAML + first     ] [+ Switch Trust   ] [+ social clip   ] [final proofread]
         [10 tests         ] [integration      ] [cut             ] [               ]
```

---

## Why This Split Works

**Subhash (Team Lead, Windows):** Owns the Bailiff — the core piece that ties everything together. As team lead, he has the full picture of how all pieces connect. The Bailiff runs as a standalone Python process, so it doesn't need macOS or Linux — it connects to Switch over the network.

**Santhan (macOS):** The ONLY person on Mac. This is essential — ParityCourt needs a real macOS host for `@alice-claude`. Santhan builds the sample app (needs to verify it works on Mac) and runs Claude Code on Mac for the demo. Also writes the blog post because he'll have the deepest hands-on experience with the Switch Console + Agent workflow.

**Vatsav (Windows):** Owns all infrastructure — Docker, SSH, networking, the `just demo` bootstrapper. The Linux container runs inside Docker on his Windows machine. He's the person who makes sure judges can reproduce everything with one command. Also writes the README because he knows the setup process inside out.

**Hashwanth (Windows):** Owns quality and security — pytest tests + Switch Trust CLI integration. These are both independent, parallelizable workstreams that don't depend on the Mac. He also handles the screen recording and social media content because he'll be watching the full flow run (to write tests for it) and will naturally capture the best moments.

---

## Communication During the Build

- **Primary channel:** WhatsApp/Discord group chat for quick updates
- **Code sharing:** This GitHub repo (`feature/subhash` branch) — push frequently
- **Daily standups:** Brief 10-minute call at the start of each day
- **End-of-day checkpoint:** Everyone confirms their checklist items are done
- **Blockers:** If you're stuck for more than 30 minutes, post in the group immediately. Don't sit on it.

---

## Critical Rules (Everyone Must Know)

1. **No project code before Nov 4, 12:01 AM IST.** Git log must start clean on Nov 4. Environment setup before Nov 4 is OK.
2. **Auto-approve and Auto-mode must be OFF** in Switch Console for the demo. Otherwise approval buttons don't appear.
3. **Hand-write the room template YAML.** Console's "Capture as template" strips agent instructions.
4. **Task-delegation APIs are removed.** Use @-mentions by role to direct messages.
5. **docs.switchagents.ai may return 503.** Use the repo docs at `docs/official/` instead.
6. **Submit by 6 PM IST on Nov 7** — not 11:59 PM. Avoid last-minute server issues.
7. **Wispr Flow stays ON the entire time.** Every dictated prompt counts toward the $500 prize.
8. **Everyone uses personal hardware and accounts only.** No employer tools, code, or data.

---

## Key Links (Bookmark These)

| Resource | URL |
|----------|-----|
| Hackathon Page | https://www.wemakedevs.org/hackathons/switch |
| Hackathon Resources | https://www.wemakedevs.org/hackathons/switch/resources |
| Switch GitHub | https://github.com/sandbox-quantum/switch |
| Switch Releases | https://github.com/sandbox-quantum/switch/releases |
| Switch Trust CLI | https://github.com/sandbox-quantum/switch-trust-cli |
| Agent Protocol | https://github.com/sandbox-quantum/switch/blob/main/docs/official/internals/agent-protocol.md |
| Remote Host Setup | https://github.com/sandbox-quantum/switch/blob/main/docs/official/deploy/host-remotely.md |
| Room Template Docs | https://github.com/sandbox-quantum/switch/blob/main/docs/TEMPLATES.md |
| Hackathon Issues | https://github.com/sandbox-quantum/switch/issues?q=is%3Aissue+state%3Aopen+label%3Ahackathon |
| CONTRIBUTING.md | https://github.com/sandbox-quantum/switch/blob/main/CONTRIBUTING.md |
| Wispr Flow | https://wisprflow.ai |
| WeMakeDevs Discord | https://discord.gg/wemakedevs |
| Our Repo | https://github.com/subhash1208/flip-the-switch-terminal |
| ParityCourt Idea Doc | `docs/PARITYCOURT.md` in this repo |
| Prize Strategy | `docs/PRIZES.md` in this repo |
