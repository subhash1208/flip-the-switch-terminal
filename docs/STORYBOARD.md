# ParityCourt demo video: storyboard and narration

## 1. Purpose and pitch

This storyboard is the shot list and spoken script for the ParityCourt demo video (target 100 to 140 seconds) for Flip the Switch, Track 01 Best Business Workflow. It follows one bug case from start to finish: two machine agents and the Bailiff, a deterministic arbiter, share one Switch room. Every command and output line below is taken from `bailiff/demo.py`, `bailiff/replay.py`, `scripts/judge.py`, `bailiff/scripted/runner.py` and `docs/evidence/transcript.txt` (the committed scripted run, 5 ablations). Plan B's 6-ablation shot 8 and the 6/6 replay line in shot 11 follow the live run's room log, which is not committed. Plan A uses real Claude Code and Codex agents, and may only be claimed where the recording shows them. Plan B is the scripted live run: a real Switch server and real WebSockets, with scripted machines and the Plan B caption on screen.

**Pitch (one sentence):** The agents investigate; the court doesn't guess - same evidence, same verdict, replayable by anyone without an API key.

## 2. Shot table

Narration counts are whitespace tokens. Each line is at most 25 words. The "Plan A vs Plan B" column lists only where the two plans differ.

| # | Time | On screen | Narration | Caption | Plan A vs Plan B (only where different) |
|---|---|---|---|---|---|
| 0 | 0:00-0:06 | Title card: ParityCourt, Flip the Switch, Track 01 Best Business Workflow | ParityCourt, for Flip the Switch, Track 01: Best Business Workflow. | Works on my machine is now evidence. | Plan B: the Plan B caption (section 3) appears here and stays on screen for the whole cut. |
| 1 | 0:06-0:14 | Bob's terminal: `node test.js` prints `TypeError: [].toSorted is not a function` and `    at test.js:3:12` | Same repo, same test. It passes on one machine and throws on the other. Works on my machine. | Works on my machine. | Plan A: Bob's real shell. Plan B: canned fixture output, same text. |
| 2 | 0:14-0:22 | Alice's terminal on the Mac: `node -v`, then `node test.js` prints `suite: 4 passed` | Minutes of chat later, we have opinions, not evidence. ParityCourt turns the bug into a receipt. | Opinions, not evidence. | Plan A: show whatever `node -v` prints on the Mac; do not pre-fill it. Plan B: fixture prints `v22.11.0`. |
| 3 | 0:22-0:30 | Switch Console: one room with three participants, `@alice-claude`, `@bob-codex`, `@bailiff` | One Switch room, three participants: Alice's agent, Bob's agent, and the Bailiff. | One Switch room. Three participants. | Plan B: participants are `pc-live-alice`, `pc-live-bob`, `pc-live-bailiff`. Show the first line of `python -m bailiff.demo --live`: `LIVE: running against a real Switch server at <base> (not simulated)`. |
| 3b | 0:30-0:38 | Same room: message list and the Bailiff's participant card | Switch hosts the room, the messages and the approval cards. The Bailiff is deterministic code with no approval power. | Switch: room, messages, approval cards. | None. |
| 4 | 0:38-0:47 | Bob's message in the room: `!open case export-service 500 AuthVerifierError on Ubuntu, passes on the Mac`. The Bailiff's reply, then the case file document appears in the room | Bob opens the case with one line. The Bailiff creates the case file, and only the Bailiff can edit it. | `!open case export-service 500 AuthVerifierError on Ubuntu, passes on the Mac` | None. |
| 5 | 0:47-0:56 | Probe requests: Alice's `node -v` and Bob's `uname -a`, each with an approval card in the Console | Each machine proposes allow-listed probes. Its owner approves each one before it runs. Auto-approve is off. | Probes: allow-listed. Approval: Switch's card. | Plan A: real approval cards from the real agents; the machine owner presses Allow; confirm auto-approve is off before recording. Plan B narration: "Each machine proposes allow-listed probes. Scripted agents auto-approve them here, so no human approved anything." Plan B screen shows the line `APPROVAL: auto-approved (scripted agent, no human)`. |
| 6 | 0:56-1:05 | Bob's `env` probe result in the room, with masked values: `DATABASE_PASSWORD=[redacted]`, `EMAIL=[redacted:email]`, `HOSTNAME=[redacted:host]` | Secrets and personal data are masked before they reach the room. Raw values stay in memory. | Masked before the room sees it. | Plan A: show what the real `env` prints, masked the same way. Plan B: fixture `env` output. |
| 7 | 1:05-1:15 | The case file document: the env diff with TZ and NODE_OPTIONS marked as decoys set aside, and the Node version listed as a suspect | The diff finds several differences. Timezone and the Node flag are set aside as decoys, and the court still tests them. | Decoys set aside (TZ, NODE_OPTIONS): tested next. | Plan A: values are whatever the machines reported; do not read a timezone value aloud. Plan B: `Europe/London` against `UTC`; `--max-old-space-size=4096` against `--max-old-space-size=2048`; `v22.11.0` against `v18.20.4`. |
| 7b | 1:15-1:19 | Same case file, suspect list, every verdict still `unknown` | Each suspect is tested, not argued. | Tested, not argued. | None. |
| 8 | 1:19-1:30 | Bob's six ablation runs, in order, each with exit code and outcome: (1) `node test.js` with `TZ` set to Alice's value, exit 1, fail; (2) `/opt/node22/bin/node test.js`, prints `suite: 4 passed`, exit 0, pass; (3) `node test.js` with Alice's `NODE_OPTIONS`, exit 1, fail; (4), (5) and (6) no-op runs on the filesystem, OS and lockfile suspects, each with an empty env, exit 1, fail | One ablation: change one variable on Bob's machine, run the failing test, record the result. Only the Node major version flips the result. | 6 runs on Bob. Only Node 22 passes. | Plan A: the Node 22 run uses the Node 22 binary in the Bob container. Plan B: same order and outcomes as the live run's room log, which is not the committed transcript. |
| 9 | 1:30-1:40 | Case file verdict block, exact receipt field: `culprit: {"variable": "node", "evidence_step": "ablation-2"}` | Culprit: the Node major version. toSorted throws on Node 18 and passes on Node 22. | Culprit: Node major version. Decoys ruled out. | Plan B: values from the live run's receipt. Recapture if `docs/evidence/receipt.json` is not saved (see section 3). |
| 9b | 1:40-1:47 | Verification line: `fix re-run on bob: {"branch": null, "verified_on": "bob", "outcome": "pass"}` | The verification re-runs the failing test on Bob's machine, under Node 22, and it passes. | Verified on Bob's machine: pass. | Plan A and Plan B: the `branch` is `null`. Do not show a branch, a PR, or a "fix shipped" caption; this build does not create one. |
| 10 | 1:47-1:57 | Attestation cards for `attest` on each machine, then the case file attestations block | The machine owner attests to that machine's side. The receipt records who said yes; it is not a cryptographic signature. | Attestation recorded. Not a signature. | Plan A: real cards; the owner presses Allow on that machine's side. Plan B narration: "Attestations here are scripted and auto-approved, so this run shows the mechanics, not a human sign-off." Plan B screen shows `APPROVAL: auto-approved (scripted agent, no human)`. |
| 11 | 1:57-2:06 | Terminal in the repo root, Docker running: `python -m bailiff.replay receipt.json --docker`, then the replay lines (see section 4) | Anyone can replay the receipt. Each step re-runs in Docker, and every outcome must match the original. | Replay: same outcomes. Docker. | Plan B: the last line of `python -m bailiff.demo --live` is `replay: 6/6 steps matched (fixture replay, not Docker)`. Plan B narration: "Anyone can replay the receipt. In this run the replay uses the fixture, not Docker, and every outcome must match." Plan B caption: "Fixture replay, not Docker." |
| 12 | 2:06-2:15 | Closing card: the replay output stays on the left, the pitch line on top | The agents investigate; the court doesn't guess - same evidence, same verdict, replayable by anyone without an API key. | The agents investigate; the court doesn't guess - same evidence, same verdict, replayable by anyone without an API key. | None. Hold the card for about 8 seconds. |

Cut length is about 2:15. Plan A narration is 263 words, about 105 seconds at 2.5 words per second. Plan B narration is 261 words, about 104 seconds. The rest of the time is on-screen beats: approval clicks, the diff and the ablation runs.

## 3. Plan B caption

If the run is scripted (Plan B), the video must show this caption on screen from shot 0 to shot 12 as a lower-third, not only once:

> Machines in this run are scripted agents; transport, Bailiff and receipt are real.

It is shown from the title card (shot 0) to the closing card (shot 12). The machine approvals in Plan B read `APPROVAL: auto-approved (scripted agent, no human)`, and the on-screen text must not suggest a human pressed Allow.

**Mixed run caption (real Alice, scripted Bob).** If the recording uses `--alice-agent` so that Alice is a real Claude Code agent and Bob is scripted, show this lower-third instead of the Plan B caption. Plan B stays as written for an all-scripted run:

> Alice is a real Claude Code agent. Bob and the fixture replay are scripted. Alice's attestation reads UNVERIFIED or DECLINED; the Bailiff does not check that string.

If `docs/evidence/receipt.json` is not saved by the live run, the receipt shots (9 and 11) must be recaptured on recording day. Only `docs/evidence/transcript.txt` exists in the repository today.

## 4. Closing shot

The closing shot is the replay of `receipt.json` followed by the pitch line.

**Plan A, real Docker replay.** Command: `python -m bailiff.replay receipt.json --docker`. The format below is what `bailiff/replay.py` prints (lines 89 to 92), and the outcomes are those of the offline receipt, which is the same five-step run. The Docker output has not been captured yet, so replace these lines with the real output on recording day:

```
ablation-1: ok (exit 1, outcome fail)
ablation-2: ok (exit 0, outcome pass)
ablation-3: ok (exit 1, outcome fail)
ablation-4: ok (exit 1, outcome fail)
ablation-5: ok (exit 1, outcome fail)
5/5 steps matched
```

If any line reads `MISMATCH`, record again. Do not edit the output and do not cut the line.

**Plan B, fixture replay.** The last line of `python -m bailiff.demo --live` reads `replay: 6/6 steps matched (fixture replay, not Docker)`. Caption it "Fixture replay, not Docker."

**Pitch line on screen.** The approved framing line, shown over the replay output for about 8 seconds: "The agents investigate; the court doesn't guess - same evidence, same verdict, replayable by anyone without an API key."

## 5. Do not say

- Do not say "each owner signs on their own machine", "each owner signs for their own machine", or "each owner attests on their own machine". Say "the machine owner approves each probe" or "the machine owner attests to that machine's side". Alice and Bob may share one Mac and one Console user in the recording.
- Do not say Alice or Bob is a real Claude Code or Codex agent in any Plan B cut.
- Do not show or narrate a refusal of Bob's Allow press in this cut. No owner pre-check exists in `bailiff/` yet, and the Switch addressing gate is verified in code only, with a live test pending. If a refusal is ever shown, caption the Bailiff's own check as ParityCourt refusing, and never attribute Switch's addressing gate to ParityCourt.
- Do not say "Switch enforces owner-only approval" as a verified fact. Say "Switch's addressing gate; verified in code, live test pending."
- Do not say "verified in Docker", "5/5 in the container", or "the judge path passes" until the real output is on screen.
- Do not say a fix is shipped, a branch was created, or a PR was opened. This build does not do any of those.
- Do not call the attestation a signature, tamper-proof, or cryptographic. It records a name.
- Do not say masking removes all personal data or guarantees privacy. Masking is regex and checksum only.
- Do not say the Bailiff uses a model to decide the verdict. The Bailiff is deterministic code; only the machine agents are LLM-driven.
- Do not say `toSorted` arrived in Node 20. That is not verified. Say "`toSorted` is not a function on Node 18".
- Do not present the case-only import as the cause. It is an optional analogue and is not in this video.
- Do not say the system scales to any number of cases or machines. Say one case per Switch room, with cost linear in the number of differing variables.
- Do not state Alice's timezone or any machine value before the recording shows it.
- Do not say `python -m bailiff.demo --live` is "not built yet". It is built; the README line is stale.

## 6. Judge Q&A cheat sheet

1. **Why a deterministic referee?** The Bailiff is plain Python with a fixed allow-list, one variable per ablation, and verdicts taken from exit codes and outcomes. The two machine agents can argue; the court reads the same evidence the same way every time, and the receipt replays.
2. **Scalability?** One case per Switch room. Ablation runs scale linearly with the number of differing, unmasked variables, and every run is on the failing machine. Replay needs no API key. Point to the README "Honest limits" section for limits; there is no "Scaling and limits" heading yet.
3. **Privacy and masking limits?** Masking is regex and checksum, not a security review. It does not catch names, street addresses, bare national phone numbers, SSH remotes, PEM bodies or YAML block scalars. A suspect whose value is masked gets verdict `unknown` and is not ablated.
4. **What is Switch and what is ParityCourt?** Switch: the room, the WebSocket and HTTP transport, agent identities, approval cards and the addressing gate (verified in code, live test pending). ParityCourt: the Bailiff, redaction, the fingerprint diff, the ablation plan, the case file, and the receipt and replay. Any owner pre-check is ParityCourt's own rule, not Switch's, and it is not built yet.
5. **What is scripted?** In Plan B, Alice and Bob are scripted fixtures auto-approved by scripted agents. The Switch server, the WebSockets, the Bailiff and the receipt are real. The offline demo runs in an in-memory room and prints SIMULATED. In Plan A, the machines are real only where the recording shows real Claude Code or Codex.
6. **How do I reproduce it in three commands?** `python -m pip install -e .`, then `python scripts/judge.py` (keyless, 8 checks, ends with `JUDGE RESULT: PASS`), then `python -m bailiff.replay receipt.json --docker`. The last command needs Docker and a `receipt.json` from `python -m bailiff.demo --offline`.

## Narration word count

- **Plan A:** 263 words, 16 lines, longest line 23 words, about 105 seconds at 2.5 words per second.
- **Plan B:** 261 words, 16 lines, longest line 23 words, about 104 seconds at 2.5 words per second.
- Counted as whitespace-separated tokens. The pitch line counts 19 tokens including the standalone dash.
