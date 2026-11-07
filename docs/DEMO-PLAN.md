# ParityCourt demo video: handoff plan

Written 2026-11-07, about 10:45 PM IST, for a teammate who did not take part in the session. Read this file top to bottom once before touching anything. It covers what to record, what to generate, how to assemble the cut, and what must not be said.

**Canonical homes (do not restate elsewhere):** judging weights, track and submission rules, and the form are in `docs/SUBMISSION.md`. The demo-length rule is in `docs/PARITYCOURT.md` (rule 10) and `docs/SUBMISSION.md` (line 16). The durable definition of what is scripted and what is real is in `docs/SUBMISSION.md` (the "What is scripted" paragraph). The README video link lives in `README.md`. This file owns only tonight's cut: the script, the shot list, the asset specs and the handoff.

## 1. Brief and pitch

ParityCourt is a court-arbiter for "works on my machine" bugs. Two machines run the same failing test. The agents on each side propose allow-listed probes. A deterministic Python referee (the Bailiff) ablates one variable at a time on the failing machine, names the culprit from exit codes and outcomes, writes a receipt, and lets anyone replay that receipt. The whole case runs in one Switch room.

The video must show one real case end to end in about 2 minutes 10 seconds. It needs one real AI agent and one real person working together in the room, with Switch at the centre.

**Pitch line (use verbatim, on the closing card):**

> The agents investigate; the court doesn't guess - same evidence, same verdict, replayable by anyone without an API key.

### What is real and what is scripted

| Element | Status in this cut |
|---|---|
| Alice | **Real.** A Claude Code agent on the team's Mac, run by Switch Console. The `LIVE:` line says so. |
| Switch | **Real.** Switch 0.31.0 server, real WebSockets, real room. |
| Room | **Real.** Mattermost room `paritycourt-live-<hex>`, shown in Console's Chat tab. |
| Bailiff | **Real.** Deterministic code. It has no approval power and does not use a model. |
| Receipt | **Real.** Written by the run. |
| Human | **Real, minimal.** The `user` account posts one real message in the room. |
| Bob | **Scripted.** A fixture reporting `v18.20.4`. Its approvals read `APPROVAL: auto-approved (scripted agent, no human)`. |
| Fix re-run on Bob | **Scripted** (fixture). |
| Replay | **Scripted in effect.** It is the fixture replay, not Docker. |
| Hashwanth's laptop | Onboarded as a remote host. **Bob did not run on it.** Never imply it did. |

Alice's messages display under the name `admin` in the room, because she has no Mattermost bot account. Narration calls her Alice. Do not claim the `admin` name is her identity.

## 2. Roles and timeline to 11:20 PM IST

Times are IST on Nov 7. The deadline is 11:59 PM IST (see `docs/SUBMISSION.md`). Tonight's internal targets are below.

| Time | Who | Work |
|---|---|---|
| 10:45 to 10:55 | Teammate | Generate the motion cards (section 6) and the voice (section 7). Do not wait for the live run. |
| 10:45 to 10:55 | Santhan | Pre-flight (section 5). Confirm Alice is responsive. |
| 10:55 to 11:08 | Santhan | Live run and screen recordings (section 5). Post the one `user` message. Save the terminal log and the receipt. |
| 11:08 | Santhan | Hand over the raw files (checklist below). |
| 11:08 to 11:18 | Teammate | Assemble (section 8). Run the QA checklist (section 10). |
| By 11:20 | Teammate | Deliver the MP4 to Santhan. If late, deliver the fallback cut (section 10). |
| 11:20 to 11:30 | Santhan | Upload to Google Drive with "Anyone with the link". Test in a private window. Add the link to the README, merge, fill the form. Target submit 11:30 PM. |

Timeline risk: about 35 minutes is very little for this. If the live run is not clean by 11:10, stop recording and ship the fallback (section 10).

### Santhan delivers to the teammate

- Screen recordings as `.mov` files, one per shot in section 5, named by shot number.
- The terminal log of the live run (text), including the `LIVE:` lines and the final `replay:` line.
- The receipt file the run wrote. The storyboard says `docs/evidence/receipt.json` is not in the repo today; the path the live run writes to is unverified, so locate it on the Mac.
- A written note of the exact attestation line on screen. It must read `UNVERIFIED: ...` or a decline by Alice (section 4, shot 11). If it does not, see the gate below.
- Confirmation that the `user` message was posted, and its text.

### Teammate delivers to Santhan

- One MP4 file (`demo.mp4`), 1080p, H.264, yuv420p, with AAC audio.
- The narration audio file and the cue table used to build it.
- The motion-card HTML files, so the cards can be re-rendered if a line changes.

**Gate: the attestation take.** If the receipt line reads `APPROVAL: approved by human via Console permission card`, and no human clicked a card, that take is not usable. Re-record it. The narration line at 1:47 depends on Alice declining to claim a human approval. Do not edit the receipt line.

## 3. Script (timed)

This is the one narration script for this cut. It supersedes the storyboard's 261-word script for this video (see section 11). Each line starts at its cue time. The lower-third (section 6) runs for the whole cut.

| # | Start | On screen (title or caption) | Narration (exact) | Source |
|---|---|---|---|---|
| 1 | 0:00 | Title card. Headline: "A test passes on one machine and fails on another. Every team knows this argument." | A test passes on one machine and fails on another. Every team knows this argument. | AI card (title) |
| 2 | 0:08 | Split card: "Same repo, same test." / "'Works on my machine' is an opinion." / "ParityCourt turns it into evidence." | Same repo, same test. 'Works on my machine' is an opinion. ParityCourt turns it into evidence. | AI card (split) |
| 3 | 0:20 | Console Chat tab, the room with its participants visible. | Everything happens in one Switch room: Alice, a real Claude Code agent on the team's Mac; Bob, scripted in this run; and the Bailiff, which is deterministic code. | Screen recording, shot A |
| 4 | 0:35 | Terminal: the first `LIVE:` lines of the run. | This is a real Switch server, not a simulation. | Screen recording, shot B |
| 5 | 0:42 | Chat: Bob's open-case line, then the case-file document. Briefly, the `user` message. | Bob opens a case with one line. The Bailiff creates the case file. | Screen recording, shot C |
| 6 | 0:52 | Chat: Alice's probes and results (for example `node -v`, `node test.js`). **Sped up 1.5x, labelled.** | The Bailiff only asks for allow-listed commands. Alice's Claude Code runs them on the team's Mac and replies in strict JSON. | Screen recording, shot D, sped up |
| 7 | 1:07 | Bob's `env` probe in the room, with masked values. | Secrets and personal data are masked before they reach the room. | Screen recording, shot E |
| 8 | 1:15 | Suspect list: tz, node, node_options, fs_case, os, lock_sha. | Six differences. Nobody argues about them. Each one gets tested. | AI card (suspects), or terminal crop if the run prints the list |
| 9 | 1:25 | Six-run table, one row per ablation, outcome column. | Change one variable on Bob, rerun the failing test. Only Node 22 flips the result. | AI card (six-run table), values from the run log |
| 10 | 1:37 | Culprit line from the receipt, verbatim. | Culprit: the Node version. toSorted is not a function on Node 18. | Screen recording, shot F, with the AI verdict card behind |
| 11 | 1:47 | Receipt, including the attestation line (`UNVERIFIED: ...` or Alice's decline). | The receipt records every step. Alice declined to claim a human approval, because nobody gave one. | Screen recording, shot G (gate, section 2) |
| 12 | 1:57 | Replay output: `replay: 6/6 steps matched (fixture replay, not Docker)`. Caption "Fixture replay, not Docker." | And the case can be replayed. Here, that's against the fixture, not Docker. | Screen recording, shot H |
| 13 | 2:03 | Closing card, pitch line, disclosure footer. Hold to about 2:10. | The agents investigate; the court doesn't guess. | AI card (closing) |

**Word count of the narration: 186 words** (whitespace tokens, counting "the team's" as two words and "allow-listed" as one). **Estimated speech length: about 68 to 75 seconds** at the speaking rates in section 7. That leaves about 55 seconds of on-screen beats across a 130-second cut. This is a count of the script as given, not the "about 230 words" in the brief. Do not pad the script to reach 230 words; the cut is already inside the 80 to 150 second rule.

Caption and claim rules that apply to every line are in section 9. Line 9 is the one most likely to be over-claimed; read section 9 before recording it.

## 4. Choreography per shot

Times match the script table. Durations run from one cue to the next. The lower-third is on every frame, so it is not repeated below.

**Shot 1 (0:00 to 0:08), title card.** The kicker "ParityCourt · Flip the Switch · Track 01: Best Business Workflow" fades in first. The headline then reveals word by word. No camera motion. Audio: narration line 1 only. Hold for 2 seconds after the headline.

**Shot 2 (0:08 to 0:20), split card.** Left column "Same repo, same test." fades in. Then "'Works on my machine'" fades in, followed by a strikethrough drawn across the word "opinion". Right column "ParityCourt turns it into evidence." slides in from the right. Audio: narration line 2.

**Shot 3 (0:20 to 0:35), Console room.** Screen recording of the Chat tab, the room visible with its participants. No camera motion; the full frame is kept. Caption at the lower edge: "One Switch room. Three participants." Note: Alice's messages show as `admin` in the room (section 1). Do not caption the name.

**Shot 4 (0:35 to 0:42), terminal.** Screen recording of the first `LIVE:` lines. Hold on the line `LIVE: running against a real Switch server at http://127.0.0.1:64640 (not simulated)`. The port varies by run, so keep the line as recorded. Caption: "Real Switch server. Not simulated." Audio: narration line 4.

**Shot 5 (0:42 to 0:52), Chat.** Bob's open-case line, `!open case export-service 500 AuthVerifierError on Ubuntu, passes on the Mac`, is the line from the storyboard. Check it against the live run before use. If the live line says Ubuntu, that is the fixture's text: do not add it to the captions or to any claim about the machine. Then the case-file document appears. The `user` message appears briefly in the room during this segment. Caption: "Bob: scripted fixture." Audio: narration line 5.

**Shot 6 (0:52 to 1:07), Chat, sped up.** Alice's probe results. Speed 1.5x on video only (`setpts=PTS/1.5`, proposed here, not from a skill). Burn a small label in the top-right corner: "sped up 1.5x". Narration runs over the sped-up footage. Caption: "Probes: allow-listed commands only." Audio: narration line 6.

**Shot 7 (1:07 to 1:15), `env` probe.** Bob's `env` result in the room. Hold on `DATABASE_PASSWORD=[redacted]`. Caption: "Masked before the room sees it. Regex and checksum rules." Audio: narration line 7.

**Shot 8 (1:15 to 1:25), suspects.** AI suspects card: six rows, one per suspect, each row fades in with a 120 ms stagger. Caption: "Tested, not argued." Audio: narration line 8.

**Shot 9 (1:25 to 1:37), six runs.** AI six-run card. Rows appear in run order, 1 to 6. Each row shows the run number, the suspect, the exit code and the outcome, filled from the run log. Only run 2 shows PASS (in the accent colour); the others show FAIL in muted grey. Audio: narration line 9.

**Shot 10 (1:37 to 1:47), culprit.** Screen recording of the receipt's culprit line, cropped to the line. Behind it, the AI verdict card's sentence fades in: "Culprit: the Node major version. Decoys ruled out." Caption: "Culprit: Node major version." Audio: narration line 10.

**Shot 11 (1:47 to 1:57), receipt and attestation.** Screen recording of the receipt, then the attestation line. Hold on the attestation line for about 3 seconds. Caption: "Attestation recorded. Not a signature." Audio: narration line 11. This is the gate in section 2.

**Shot 12 (1:57 to 2:03), replay.** Screen recording of the replay line, `replay: 6/6 steps matched (fixture replay, not Docker)`. Caption: "Fixture replay, not Docker." Audio: narration line 12.

**Shot 13 (2:03 to about 2:10), closing.** AI closing card. Pitch line in the centre (section 1). The disclosure footer reads: "Narration is AI-generated. Motion cards are AI-generated. Screen recordings show a real run." Hold for about 7 seconds. Fade to black over the last 0.5 seconds. Audio: narration line 13.

**Transitions.** Use one transition throughout: a 0.5-second cross-fade, which is the default in the video pipeline's cut logic (`.claude/skills/video-production/references/pipeline.md`, "Cards and fades"). Do not use other transitions.

## 5. Screen recording shot list (Santhan)

### Pre-flight (before recording)

1. Check no stale run is alive: `pgrep -fl "bailiff.demo" | grep -v pgrep`. It must print nothing.
2. Send `hello` to Alice in her New Chat, so the session is warm.
3. Set Auto mode on. Set Bypass off.
4. Load the environment with the run's environment file **before** you start recording, off camera. Do not echo or display the file's contents. Clear the Terminal scrollback (Cmd+K, verify on the Mac) so no secret is visible.
5. Run the command: `python -m bailiff.demo --live --alice-agent alice-claude --chat-user user`. Confirm the exact flags against the `bailiff/demo.py` argument parser before recording, because this command was given to the teammate from the brief and not checked against the parser here.
6. If Alice gets stuck, send `!interrupt @alice-claude` in the room, then re-run the shot.

### Recording setup

- Record with Cmd+Shift+5. Choose "Record Selected Portion" for one window at a time, or "Record Entire Screen" for the Console and Terminal side by side. Turn on "Show Mouse Pointer" in the options (verify this menu item on the Mac; it is standard macOS but unverified here).
- Set the Terminal and the Console to the same window size, ideally a 16:9 frame. Record at native resolution and scale to 1920 by 1080 in the assembly step.
- Turn on Focus (Do Not Disturb) before recording, to hide notifications. Hide the Dock and desktop icons.
- Cursor: move slowly. Pause one second before each click so the edit can cut on it.
- Zoom: this cut has no zoom. Record the full window at a size that stays readable without one.

### Privacy: decide before recording

- **Hostname and disk UUID.** `uname -a` prints the hostname, and `diskutil` prints the disk UUID. Do not run either on screen. The decision is: avoid, do not blur. If a path or hostname ends up on screen anyway (for example Alice's `uname`, or `/Users/<name>` in a prompt), the teammate covers it in assembly with a solid box (section 8, step 6). If the box cannot be placed cleanly, re-record the shot.
- Do not show a `.env` file, a shell `export` line, or your own `env` output.
- Do not show the room's real personal data. The room shows masked values only.
- Hide the browser's bookmarks bar and tabs that are not part of the Console.

### Shot order and what to do

| Shot | Window | Action | Length | Notes |
|---|---|---|---|---|
| A | Console, Chat tab | Show the room and its participants. Scroll slightly, no clicks. | about 15 s | Feeds script line 3. |
| B | Terminal | Start the run. Let the first `LIVE:` lines print. Hold. | about 7 s | Feeds line 4. |
| C | Chat | Bob's open-case line. Post the `user` message, one line, then show it. | about 9 s | The `user` message is real. Post one short, honest line of your choice. It must not claim any approval. |
| D | Chat | Alice's probe results and her reply. | 15 to 20 s (sped up to about 10 to 14 s in edit) | Feeds line 6. |
| E | Chat | Bob's `env` result. | about 8 s | Feeds line 7. |
| F | Terminal | Scroll to the culprit line. | about 6 s | Feeds line 10. |
| G | Terminal or receipt viewer | Show the receipt and the attestation line. | about 10 s | This is the gate in section 2. |
| H | Terminal | Show the replay line. | about 6 s | Feeds line 12. |

Total recorded footage should be about 90 seconds, which the edit trims. Record each shot twice if time allows, and use the cleaner take.

## 6. AI-generated assets

### Which skill fits

| Asset | Skill | Fit | Fallback |
|---|---|---|---|
| Motion cards: title, split, architecture, suspects, six-run table, verdict, closing | `.claude/skills/html-slides/SKILL.md` | **Fits, with a limit.** It generates single-file HTML slides with viewport fitting (`100vh`/`100dvh`), CSS entrance animations (`.reveal`), and optional GSAP. It does not export MP4. | Open each HTML file full-screen at 1920 by 1080 and screen-record it with Cmd+Shift+5, or use Playwright's screenshot and recording APIs (not covered by any skill here; unverified). |
| Style and palette | `.claude/skills/slide-design/SKILL.md` | Use for the rules: one entrance animation, at most three colours, one heading font and one body font, no AI-slop styling. Its presets file (`references/style-presets.md`) is not used for this cut. | Use the palette below. |
| Lower-third overlay (transparent PNG over video) | None fits. html-slides has no transparent-background export. | **Not covered.** | Render the lower-third as an HTML element on a transparent page and capture it as a PNG, or type it into the video with the editor. Unverified. |
| Voiceover | `.claude/skills/video-production/` (ElevenLabs path, `gen-voice.mjs`) | Partly fits. The skill expects a project scaffold with `narration.mjs` and `scenario.mjs`. | macOS `say` (section 7). |
| Screen recordings | None. | **Not covered.** The video-production recorder (`recorder.mjs`) drives a web app with Playwright; it does not capture a terminal or the Switch Console. | Cmd+Shift+5 (section 5). |
| Assembly and sync | `.claude/skills/video-production/` (`build.mjs`) | **Does not fit.** `build.mjs` aligns voice to the recorder's clap and beat marker, which only the Playwright recorder emits. Screen recordings have neither. | Manual assembly by timestamp (section 8). |

Skill behaviour in this table is taken from the skill files. None of it has been run for this video. Treat every "fits" as unverified until the teammate tests one card.

### Palette and type (for all cards)

- Background: near-black, `#12151A`.
- Text: off-white, `#F2F2F2`. Secondary text: `#9AA3AE`.
- One accent: amber, `#F5A524`. Used for the culprit, the PASS result, and the underline on the strikethrough.
- Fonts: IBM Plex Sans for headlines and body; IBM Plex Mono for every command, path and JSON line. Load from Google Fonts. If offline, fall back to `system-ui` and `ui-monospace`.
- Headline size: at least three times the body size (rule from the html-slides skill).
- Canvas: 1920 by 1080, 16:9.

### Motion (for all cards)

- One entrance animation: `.reveal`, opacity 0 to 1 and translateY 20 px to 0, 200 ms with `cubic-bezier(0.16, 1, 0.3, 1)` (the skill's `--ease-out-expo`). Stagger elements by 120 ms. The skill's "Technical" guidance is 150 to 200 ms with no bounce.
- Respect `prefers-reduced-motion`: if set, show elements at once.
- No scrolling inside a card.

### Lower-third (every frame)

- Text, exact: **Alice is a real Claude Code agent. Bob and the fixture replay are scripted.**
- Layout: bottom-left, a dark band at 70% opacity, IBM Plex Sans, 36 px, off-white. Full width of the text, with 24 px padding.
- Motion: fades in once at 0:00 and stays until the closing card fades. No animation after that.

### Card specifications

Each card gives: exact text, layout, motion, and a prompt to paste into Claude.

**Card 1: Title (0:00, 8 s).** Kicker (mono, accent): "ParityCourt · Flip the Switch · Track 01: Best Business Workflow". Headline (large, centred): "A test passes on one machine and fails on another. Every team knows this argument." Motion: kicker, then headline reveal word by word, 60 ms per word.

> Using the html-slides skill, make one single-file HTML slide, 1920 by 1080, dark background #12151A, IBM Plex Sans. Show a small mono kicker in amber: "ParityCourt · Flip the Switch · Track 01: Best Business Workflow". Under it, a large centred headline in off-white: "A test passes on one machine and fails on another. Every team knows this argument." Use one entrance animation (opacity and translateY 20px, 200ms, cubic-bezier(0.16, 1, 0.3, 1)). Reveal the kicker first, then the headline word by word at 60ms per word. Respect prefers-reduced-motion. No scrolling. No other colours. Output the HTML only.

**Card 2: Split (0:08, 12 s).** Left column, heading "Same repo, same test." Right column, a line "'Works on my machine' is an opinion." then a line "ParityCourt turns it into evidence." The word "opinion" gets a strikethrough in amber. Motion: left column first, then the right, then the strikethrough draws left to right over 400 ms.

> Using the html-slides skill, make one single-file HTML slide, 1920 by 1080, background #12151A, IBM Plex Sans. Split into two columns with a thin vertical divider. Left column, large off-white text: "Same repo, same test." Right column: "'Works on my machine' is an opinion." then below it, in amber: "ParityCourt turns it into evidence." Draw a strikethrough in amber across the word "opinion" after the right column appears. Use one entrance animation (opacity and translateY 20px, 200ms). Order: left column, right column, strikethrough. Respect prefers-reduced-motion. No scrolling. Output the HTML only.

**Card 3: Architecture, how it works (about 15 s; optional inset during shot 3 if time allows).** Five boxes: a "Switch room" box at the centre, largest, with three smaller boxes around it: "Alice: real Claude Code agent (team's Mac)", "Bob: scripted fixture", and "Bailiff: deterministic code, allow-listed commands, no approval power". Below, a single line of arrows: "case file → probes → suspects → ablations → verdict → receipt → replay". Motion: boxes appear in order (Switch room, then Alice, Bob, Bailiff), then the arrow line draws left to right. Do not use the phrase "owner-only" or any claim about Switch enforcing approvals.

> Using the html-slides skill, make one single-file HTML slide, 1920 by 1080, background #12151A, IBM Plex Sans and IBM Plex Mono. Centre a large box labelled "Switch room". Around it, three smaller boxes: "Alice: real Claude Code agent (team's Mac)", "Bob: scripted fixture", "Bailiff: deterministic code, allow-listed commands, no approval power". Under the diagram, one mono line: "case file → probes → suspects → ablations → verdict → receipt → replay". Accent amber only on the Switch room border. Entrance: boxes in order (Switch room, Alice, Bob, Bailiff), then the arrow line draws left to right. Respect prefers-reduced-motion. No scrolling. Do not write any claim about approvals being enforced. Output the HTML only.

**Card 4: Suspects (1:15, 10 s).** Heading "Six differences. Each one gets tested." Six rows, each a mono label: tz, node, node_options, fs_case, os, lock_sha. Caption on the card: "Tested, not argued." Motion: rows appear 120 ms apart. Labels must match the names the run prints. If the run prints the list, use a terminal crop instead and drop this card.

> Using the html-slides skill, make one single-file HTML slide, 1920 by 1080, background #12151A, IBM Plex Sans and IBM Plex Mono. Heading in off-white: "Six differences. Each one gets tested." Below it, six rows, each one a mono label, in this order: tz, node, node_options, fs_case, os, lock_sha. A small grey line under the list: "Tested, not argued." Entrance: each row reveals 120ms after the previous. Respect prefers-reduced-motion. No scrolling. Output the HTML only.

**Card 5: Six-run table (1:25, 12 s).** Heading "Change one variable. Rerun the failing test." Table with columns: Run, Variable changed, Exit code, Outcome. Six rows. **Fill every cell from the run log of the live run. Do not write values from the storyboard.** The brief states that only run 2 (`/opt/node22/bin/node test.js`, Node 22) passes, and that runs 4 to 6 are no-op runs. Show PASS in amber for run 2 and FAIL in muted grey for the others. Motion: rows in run order, 150 ms apart.

> Using the html-slides skill, make one single-file HTML slide, 1920 by 1080, background #12151A, IBM Plex Sans and IBM Plex Mono. Heading in off-white: "Change one variable. Rerun the failing test." Below, a table with columns Run, Variable changed, Exit code, Outcome, and six rows. Fill the rows from the attached run log only (I will paste the log): do not invent values. Show the outcome PASS in amber bold and FAIL in muted grey. Reveal rows in run order, 150ms apart. Respect prefers-reduced-motion. No scrolling. Output the HTML only.

**Card 6: Verdict (1:37, behind the culprit crop, 8 s).** Text, exact: **"Culprit: the Node major version. Decoys ruled out."** The literal receipt line is not on this card; it comes from the screen recording (section 3, line 10). Motion: sentence fades in over the recording, with a 40% dark scrim behind it.

> Using the html-slides skill, make one single-file HTML slide, 1920 by 1080, with a transparent background and a 40% black scrim across the full frame. One centred sentence in off-white, IBM Plex Sans, large: "Culprit: the Node major version. Decoys ruled out." Entrance: one fade and translateY 20px, 200ms. Respect prefers-reduced-motion. Output the HTML only.

**Card 7: Closing (2:03 to about 2:10).** Pitch line, centred, large: "The agents investigate; the court doesn't guess - same evidence, same verdict, replayable by anyone without an API key." Footer, small, grey: "Narration is AI-generated. Motion cards are AI-generated. Screen recordings show a real run." Motion: pitch line fades in, footer fades in 600 ms later. No exit animation; the cross-fade to black does the exit.

> Using the html-slides skill, make one single-file HTML slide, 1920 by 1080, background #12151A, IBM Plex Sans. Centred, large, off-white: "The agents investigate; the court doesn't guess - same evidence, same verdict, replayable by anyone without an API key." Bottom, small, grey #9AA3AE: "Narration is AI-generated. Motion cards are AI-generated. Screen recordings show a real run." Entrance: the main line first, then the footer 600ms later, one fade and translateY 20px, 200ms. Respect prefers-reduced-motion. Output the HTML only.

**Card 8: Lower-third (whole cut).** See the lower-third spec above. Render it as a transparent PNG, or type it in the editor, because html-slides does not export transparent overlays (section 6 table).

> Make one lower-third as a 1920 by 1080 transparent HTML page. Bottom-left, a dark band, background rgba(18,21,26,0.7), 24px padding, IBM Plex Sans 36px, off-white, containing exactly this text: "Alice is a real Claude Code agent. Bob and the fixture replay are scripted." Nothing else on the page. Output the HTML only.

## 7. Voiceover

### Which voice tool

- **ElevenLabs, if a key exists** on the teammate's side. Use the video-production skill's voice script (`gen-voice.mjs`, then `trim-voice.mjs`). The skill's pipeline reference says the key goes into a gitignored env file in the project, and that the key must be revoked after use if it was pasted in plain text. Never write the key into this file, into any card, or into chat. The skill's voice script reads lines from a `narration.mjs` project file, so partial use needs the scaffold. Whether `gen-voice.mjs` runs on one line set without the scaffold is **unverified**; read the template header first.
- **Otherwise, macOS `say`**: `say -v Samantha -r 165 -f narration.txt -o voice.aiff`. This produces one file, so every line's timing is unknown. Use the per-line method below.

### Per-line method (recommended for either tool)

Generate each line as its own audio file, then place each file at its cue time. This keeps the narration in sync with the cut without any beat marker.

Example for line 1 (macOS): `say -v Samantha -r 165 -o line-01.aiff "A test passes on one machine and fails on another. Every team knows this argument."`

Measure each file's duration with ffprobe. If a line runs past its next cue, shorten the on-screen hold, not the narration. Never speed up the voice.

### narration.txt (speak this file, one line per block, nothing else)

Keep labels and timings out of this file. Anything in it is read aloud.

```
A test passes on one machine and fails on another. Every team knows this argument.

Same repo, same test. 'Works on my machine' is an opinion. ParityCourt turns it into evidence.

Everything happens in one Switch room: Alice, a real Claude Code agent on the team's Mac; Bob, scripted in this run; and the Bailiff, which is deterministic code.

This is a real Switch server, not a simulation.

Bob opens a case with one line. The Bailiff creates the case file.

The Bailiff only asks for allow-listed commands. Alice's Claude Code runs them on the team's Mac and replies in strict JSON.

Secrets and personal data are masked before they reach the room.

Six differences. Nobody argues about them. Each one gets tested.

Change one variable on Bob, rerun the failing test. Only Node 22 flips the result.

Culprit: the Node version. toSorted is not a function on Node 18.

The receipt records every step. Alice declined to claim a human approval, because nobody gave one.

And the case can be replayed. Here, that's against the fixture, not Docker.

The agents investigate; the court doesn't guess.
```

### Tone

- Calm and plain, like a colleague showing a result. No hype, no exclamation marks.
- Check the pronunciation of "toSorted" on the first take. If it sounds wrong, respell it in `narration.txt` only (for example "to sorted"), never on screen.
- Pace: one breath between lines. Do not read the captions.
- Narration is spoken over the sped-up chat shot. It stays at normal speed.

### Disclosure

The closing card's footer must read: "Narration is AI-generated." It also reads that motion cards are AI-generated and that screen recordings show a real run (section 6, card 7).

### Music

No music. The pipeline's music step costs ElevenLabs credits and needs explicit consent (`.claude/skills/video-production/SKILL.md`, Safety). This cut does not use it.

## 8. Assembly

### Install

1. Check for ffmpeg on the teammate's machine: `ffmpeg -version`. It is not installed on Santhan's Mac.
2. If missing: `brew install ffmpeg` (Homebrew required). Then check the filters the steps below use: `loudnorm`, `adelay`, `amix`, `overlay`, `drawbox`, `setpts`. The skill's pre-flight notes that some ffmpeg builds lack `subtitles` and `drawtext` (libass or freetype); plan to overlay PNGs instead of relying on them. Filter availability: unverified until checked on the teammate's build.

### Steps

1. **Convert recordings to MP4.** For each `.mov`: `ffmpeg -i demo.mov -c:v libx264 -crf 23 -pix_fmt yuv420p -c:a aac demo.mp4`. Check the output size with `ffprobe`. Scale to 1920 by 1080 in the same step if the source differs.
2. **Render the cards.** Open each HTML card at 1920 by 1080 full-screen and record it (Cmd+Shift+5, or the alternative in section 6). Trim each to its on-screen length.
3. **Cut the timeline by construction.** Each video segment starts at its cue time from the script table and runs until the next cue. Trim each segment to exactly that duration (`-t`). Sync then comes from the timeline, not from a clap or a marker.
4. **Cross-fade** between segments with a 0.5-second fade (default in the pipeline).
5. **Place the voice.** Each per-line audio file is delayed to its cue (`adelay=<ms>|<ms>`), then mixed with `amix normalize=0`. Cue times in milliseconds: 0, 8000, 20000, 35000, 42000, 52000, 67000, 75000, 85000, 97000, 107000, 117000, 123000.
6. **Cover privacy items** if any appear on screen. Use a `drawbox` filter over the area, in solid black, for the segment only. Verify that the box covers the item in a frame at its start and at its end.
7. **Speed up shot 6** with `setpts=PTS/1.5` on the video only. Overlay the label "sped up 1.5x" for that segment.
8. **Lower-third.** Overlay the transparent lower-third PNG over the whole cut, or type it in the editor.
9. **Loudness.** Apply `loudnorm I=-16:TP=-1.5:LRA=11` to the mixed audio (the values the skill's build uses). Confirm with `volumedetect`: about -16 dB during a line, and near silence after the last line.
10. **Subtitles (optional).** If time allows, write an SRT file from the cue table and deliver it as a sidecar. Burn-in is not required and depends on the ffmpeg build.
11. **Export** `demo.mp4`: H.264, yuv420p, AAC, 1920 by 1080.

The video-production skill's `build.mjs` cannot do steps 3 to 5, because it needs the Playwright recorder's clap and beat marker (section 6). The manual steps above replace it. This is untested.

## 9. Do-not-say list

These bind the narration, the captions, the cards and the description. The storyboard's section 5 holds the general rules. This list adapts them to this mixed run.

- Do not say Bob is real, or that Bob is a Claude Code or Codex agent. Bob is a scripted fixture.
- Do not say Bob ran on Linux or Ubuntu, or on any real machine. The fixture reports `v18.20.4`. Do not caption a host or OS for Bob.
- Do not say Hashwanth's laptop ran Bob, or that a remote host ran any probe. It was onboarded, nothing more.
- Do not say a human approved anything. No approval cards appear in this cut, and no narration says a probe was approved by a person. Do not show `APPROVAL: approved by human via Console permission card` on screen.
- Do not say "each owner signs on their own machine", "each owner attests on their own machine", or "each owner approves on their own machine". Say "the machine owner approves each probe" or "the machine owner attests to that machine's side", and only if the recording shows it.
- Do not call the attestation a signature, tamper-proof, or cryptographic. It records a name.
- Do not say "the Bailiff checks the approval string". It does not.
- Do not say "Switch enforces owner-only approval". Switch's addressing gate is verified in code only, with a live test pending.
- Do not say "verified in Docker", "5/5", or "the judge path passes". The replay on screen is the fixture, not Docker.
- Do not say a fix is shipped, a branch was created, or a PR was opened. This build does not do any of those.
- Do not say `toSorted` arrived in Node 20, or make any claim about Node 20. Say "`toSorted` is not a function on Node 18". Node 22 is the version that passes.
- Do not say masking removes all personal data. Masking is regex and checksum only.
- Do not say the Bailiff uses a model to decide the verdict. It is deterministic code.
- Do not say the system scales to any number of cases or machines. Say one case per Switch room.
- Do not state Alice's timezone, Alice's OS, or any machine value that is not on screen.
- Do not present the case-only import (an optional analogue) as the cause or as part of this video.
- Do not say `python -m bailiff.demo --live` is "not built yet". It is built.
- Do not caption Alice's messages with a name other than the one on screen. Her messages show as `admin`.

## 10. QA checklist, fallback and cut order

### QA checklist (run before delivery)

- [ ] `ffprobe` reports a duration between 80 and 150 seconds (repo rule). Target about 130 seconds.
- [ ] Resolution 1920 by 1080, H.264, yuv420p, AAC audio.
- [ ] The lower-third is visible on every frame: check frames at the start, middle and end.
- [ ] The narration is in sync: pick three lines (for example 0:52, 1:37, 2:03), and check the audio starts with the matching shot. Extract a frame at each cue time.
- [ ] The culprit line reads exactly `culprit: {"variable": "node", "evidence_step": "ablation-2"}`. The replay line reads exactly `replay: 6/6 steps matched (fixture replay, not Docker)`. Check against the run log, character for character.
- [ ] The `LIVE:` lines are on screen: `LIVE: running against a real Switch server at ... (not simulated)` and `LIVE: Alice is @alice-claude, a real agent (not scripted)`.
- [ ] Alice's `node test.js` shows `export-service: all checks passed` if it is on screen, and Bob's failure shows `TypeError: [].toSorted is not a function` if it is on screen. Check each against the log.
- [ ] Alice's version on screen matches what she printed on the run. Do not write a version into a caption.
- [ ] The attestation take shows `UNVERIFIED: ...` or Alice's decline, not a human approval. If not, re-record (section 2).
- [ ] No hostname, disk UUID, personal email, `.env` content or secret is visible in any frame. Check frames at the beginning and end of each recording segment.
- [ ] Captions and narration pass section 9. Search the script and the cards for "approved", "signs", "Docker", "shipped", "branch", "PR", "Node 20", "signature" and "scales". Any hit must be correct and sourced, or removed.
- [ ] The closing card's footer contains "Narration is AI-generated."
- [ ] Uploaded to Google Drive with "Anyone with the link". Opened in a private window. The link plays.
- [ ] Link added to the README by Santhan. (See `README.md`; the video link placeholder is there.)

### Open items to decide before the cut

- **Wispr picture-in-picture.** `docs/SUBMISSION.md` (line 16) and `docs/PRIZES.md` (line 46) ask for a 5-second Wispr dictation clip in the video. This brief does not include it. Decide tonight whether it is in. If yes, Santhan records it and it is placed at a free beat; that beat is not in the script table above.
- **Closing line.** `docs/PARITYCOURT.md` (rule 9) names a different closing line: "Delete Switch, and these agents can't see each other's machines." This plan uses the brief's pitch line. Confirm with Santhan which one closes the video; change only card 7 and the narration's last line if it switches.

### Fallback if time runs out

Ship in this order, and stop at the first step that is done and acceptable:

1. **Full cut** (sections 3 to 8).
2. **Recording plus narration plus lower-third only.** Drop every AI card. Use the first frame of the Console recording as the title. End on the replay recording with the closing line as a plain text overlay (or a black frame with the pitch line typed in the editor). Keep the lower-third and the disclosure. The disclosure must still appear in the video.
3. **Recording plus lower-third only.** Only if voice is not ready. Captions carry the narration; the lower-third stays. Do not ship without the disclosure and the lower-third.

Never ship a cut without the lower-third. The attestation gate and the do-not-say list stay in force for every fallback.

### Cut order (to stay under 150 seconds while keeping the pass conditions)

If the cut runs long, drop in this order. The pass conditions are: one real agent, one human message, Switch in the room, the culprit, the verification line, the replay line, and the lower-third.

1. Drop the Wispr clip, if it was added.
2. Drop card 3 (architecture).
3. Shorten shot 3 (Console room) to 6 seconds.
4. Drop the subtitles.
5. Shorten the closing hold from about 7 seconds to 5 seconds (keep the pitch line on screen for at least 5).

Do not cut shots 4 (real Switch server), 10 (culprit), 11 (attestation gate) or 12 (replay). They carry the pass conditions.

## 11. Known conflicts and unverified items

### Conflicts with other files (not fixed here)

These files were not edited, because this task allowed only one file. Each one still says something that this cut contradicts. Flag them for whoever owns them.

- `docs/STORYBOARD.md` (sections 2 to 4) has a 261-word Plan B narration, approval-card shots (5 and 10), and participant names `pc-live-*` and `@bob-codex`. This cut uses the 186-word script in section 3, has no approval cards (per the brief), and does not name Bob's handle. The storyboard's Plan B wording must not be used for this cut.
- `docs/SUBMISSION.md` (line 148) and `docs/TIMELINE.md` (lines 65 and 85) say "Subhash narrates". This plan uses AI narration. Those files will be wrong once this video is final.
- `JUDGES.md` (lines 55 and 75) says the live transcript has "scripted Alice and Bob". The brief now says Alice is a real Claude Code agent in this run. The transcript at `docs/evidence/transcript.txt` is the scripted run, so both statements are true of different runs. The text should say so.
- `docs/PARITYCOURT.md` (rule 9) gives a closing line that differs from this plan's (section 10).

### Unverified

- Skill behaviour: none of the video-production or html-slides steps has been run for this video. The "fits" in section 6 come from reading the files.
- Timing: the script's per-line durations are estimated from word counts (about 2.5 to 2.75 words per second). Not rehearsed. Measure after `say` or ElevenLabs.
- Live run length and the exact receipt path. Locate the receipt on the Mac before recording.
- Exact text of the attestation line (`UNVERIFIED: ...`). Read it from the recording.
- The six-run table values. The brief states only that run 2 passes and runs 4 to 6 are no-ops. Fill every value from the run log.
- The suspects list as printed by the run (section 4, shot 8). Check the labels against the log.
- The macOS "Show Mouse Pointer" option and Focus setting in Cmd+Shift+5. Standard macOS, not checked on this Mac.
- `drawbox`, `loudnorm`, `adelay` and `setpts` availability on the teammate's ffmpeg build.
- Whether the ElevenLabs path works without the video-production project scaffold.
- The `say -v Samantha` voice is installed on the teammate's Mac. `say` is macOS-only.
- Google Fonts load during HTML card rendering, if the render machine is offline.
