# Prize Strategy — Every Prize We Can Win

Team: Terminal
Hackathon: Flip the Switch (Nov 4–7, 2026)

---

## Prize Overview

The hackathon has $10,000+ in total prizes across multiple tracks. We can enter ALL of them simultaneously. Here's every prize and exactly how we win it.

---

## Track 01 — Best Business Workflow ($2,000 cash)

**Our entry:** ParityCourt (see `docs/PARITYCOURT.md` for full details)

**What judges look for:**
- Use of Switch (30%) — Is Switch central? Would the project stop working without it?
- Technical execution (25%) — Does it run? Can someone clone the repo and reproduce it?
- Creativity and impact (25%) — Fresh idea that solves a problem real teams have?
- Presentation (20%) — Do the demo video and README make clear how Switch is used?

**How we win it:**
- Two physical machines, two AI vendors, one custom agent — impossible without Switch
- `just demo` one-command setup with 25+ pytest tests
- Universal pain point ("works on my machine") elevated with Switch Trust security scan
- 80–150 second video with a clear courtroom narrative and a killer closing line

---

## Code with Wispr ($500 cash)

**What it is:** A side prize for the best project built by voice using Wispr Flow.

**How to enter:**
1. Install Wispr Flow (hackathon gives 1 month Pro free via a link on the event page)
2. Use voice dictation throughout the entire build — prompts to Claude Code / Codex / Kiro, room instructions, README, blog post, commit messages, Mattermost chat
3. Screenshot your Wispr Flow Insights tab (shows total words dictated, time saved, apps used)
4. Attach the screenshot when you submit

**How we win it:**
- Every team member installs Wispr on Day 1
- Use voice for every prompt to coding agents — the bigger the word count across multiple apps, the stronger the submission
- You can still type. The prize goes to the project that used voice most effectively, not someone who never touched a keyboard.
- Include a 5-second picture-in-picture clip of Wispr dictation in the demo video — judges see it in action

**Effort required:** Near zero. You're doing the work anyway — you're just talking instead of typing.

---

## Best Blog (AirPods 5)

**What it is:** The best blog post about building with Switch. Top 5 posts each win a prize; #1 gets AirPods 5.

**How to enter:** Publish a blog post on Dev.to, Hashnode, Medium, or your own site. Link it in your submission.

**What judges look for:** "Clarity, accuracy, and how much it helps a first-time Switch user."

**Our angle:** "Build a Custom Switch Agent in 250 Lines"

This is a first-timer tutorial using our Bailiff as the example. It walks a reader from zero to a working custom agent on the Switch Agent Protocol (SSE/HTTP). The structure:

1. **Why build a custom agent** — Switch ships built-in providers for Claude Code, Codex, etc. But sometimes you need an agent that does something specific — orchestration, guardrails, loop prevention.
2. **The Agent Protocol explained** — SSE events down (messages from the room), HTTP POST actions up (send messages, post attachments).
3. **Building the Bailiff step by step** — connecting to the SSE stream, parsing events, sending responses, adding the loop breaker, integrating Switch Trust CLI.
4. **Testing it** — how we wrote 25+ pytest tests for the state machine.
5. **Running it in a room** — hand-writing the template YAML, connecting to Mattermost, watching it work.

This post works because:
- There's no existing reference custom agent tutorial in the Switch docs
- It directly helps first-time Switch users (the judging criterion)
- It comes naturally from building ParityCourt — we're writing the Bailiff anyway
- The 250-line hook makes it feel approachable

**Effort required:** ~3 hours of writing on Day 3. Most content comes directly from the code we already wrote.

---

## #HowISwitch (Logitech mechanical keyboard — top 5 posts)

**What it is:** Share your build on social media with the hashtag #HowISwitch. Top 5 posts each win a Logitech keyboard.

**How to enter:** Post on X (Twitter) and/or LinkedIn with #HowISwitch, tagging @switchagents_ai, @WeMakeDevs, and @DevToolsAcademy.

**Our approach:**
- Cut a 60-second highlight reel from the demo video
- Post it with a short punchy caption:

  > "We built ParityCourt — a cross-machine debugging courtroom where Claude Code on Mac and a second agent on the failing machine investigate bugs together through Switch. Two machines, three agents, one verdict. #HowISwitch @switchagents_ai @WeMakeDevs @DevToolsAcademy"

- Post on BOTH X and LinkedIn for maximum reach
- Each team member can reshare from their own accounts

**Effort required:** 30 minutes to cut the clip and write the caption. Do this on Day 3 or Day 4.

---

## Track 03 — Best Core Contribution ($100 × 20 PRs)

**What it is:** The top 20 pull requests to Switch's open-source core each win $100. You can have up to 5 PRs open at once.

**Key rule:** You can start TODAY. Track 03 doesn't require waiting until Nov 4. But your PR must be open by Nov 7, 11:59 PM IST.

**How to get assigned:**
1. Browse [hackathon-labelled issues](https://github.com/sandbox-quantum/switch/issues?q=is%3Aissue+state%3Aopen+label%3Ahackathon)
2. Comment on the issue, tag @petr-sandbox, and say in 1-2 lines how you plan to solve it
3. Wait until you're assigned, then start
4. Read `CONTRIBUTING.md` first — it covers dev setup and the one-time CLA

**Best issues for our team:**

| Issue | What it is | Effort | Good for |
|-------|-----------|--------|----------|
| #801 | Deliver mid-turn messages to a running agent | Medium — Python core work in switch-core | Someone comfortable with Python internals |
| #779 | Add Kiro CLI as an agent provider | Medium — TypeScript/Console work | Someone who uses Kiro daily |
| #780 | Add Goose as an agent provider | Medium — similar pattern to #779 | Anyone with a Goose account |
| #808 | Five-minute quickstart for new contributors | Low — documentation | Anyone; our blog post partially covers this |
| #806 | Prettify the agent controller CLI output | Low-Medium — formatting work | Quick win |

**Assignment rule conflict:** The website says you must be assigned before PRing. But the maintainer said on Oct 22 (#808 comment) that anyone can attempt any issue. Play it safe — comment first, wait for assignment, then start.

**Effort required:** Each PR is independent work. 4-8 hours per issue depending on complexity. Start these NOW, before Nov 4.

---

## Swag (Random Draw — 20 winners)

**What it is:** 20 project submissions picked at random get swag shipped to them.

**How to enter:** Submit a project. That's it. We're entered automatically.

---

## Certificate (Every submission)

**What it is:** Every project gets a certificate, win or not. Winning projects are showcased across Switch, WeMakeDevs, and DevTools Academy channels.

---

## Total Prize Potential

If everything lands:

| Prize | Value |
|-------|-------|
| Track 01 — Best Business Workflow | $2,000 |
| Code with Wispr | $500 |
| Best Blog | AirPods 5 (~$250 value) |
| #HowISwitch (top 5) | Logitech keyboard (~$100 value) |
| Track 03 — Core PRs (up to 5 per person × 4 people) | Up to $2,000 |
| Swag random draw | Swag |
| Certificate | Certificate |
| **Maximum total** | **~$4,850+ in prizes** |

---

## Optional: Track 02 — Best Personal/Creative Workflow ($2,000 cash)

If ParityCourt is solid by end of Day 2 and we have time, we can submit a second project to Track 02: **LaunchForge Studio** (a multi-creator indie product launch room).

This reuses the same Mac + Linux SSH + custom Python agent infrastructure from ParityCourt, just swaps the sample app from a broken auth service to a live hot-reloading product launch page.

**Decision point:** End of Day 2. If ParityCourt works end-to-end, one person spends 4 hours adapting it for Track 02. If not, skip it — one polished entry beats two rough ones.

---

## Priority Order

1. **ParityCourt (Track 01)** — This is the main event. Everything else orbits around it.
2. **Wispr** — Zero extra effort. Just talk instead of type from Day 1.
3. **Blog post** — Write on Day 3. Content comes from the Bailiff code we already wrote.
4. **#HowISwitch** — 30 minutes on Day 3/4 to cut a clip and post it.
5. **Track 03 PRs** — Start before Nov 4. Independent work that doesn't block ParityCourt.
6. **Track 02** — Only if time allows after ParityCourt is done.
