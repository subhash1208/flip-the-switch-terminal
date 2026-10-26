---
description: Produce a polished tutorial video of this project's web app (browser recording, synced voice-over, burned-in subtitles, full editing)
argument-hint: [journeys to film, e.g. "admin" or "onboarding + checkout"]
---

Produce one or more tutorial videos of this project's application by following the `video-production` skill pipeline from this plugin. User request: "$ARGUMENTS" (if empty: propose a breakdown of the main user journeys).

First read the SKILL.md of the `video-production` skill (video-maker plugin) and keep its rules in mind throughout. Then run this workflow:

## 1. Brief (a single round of questions)

Explore the project (stack, routes/screens, how to run the app locally). Then propose a plan: number of videos, journeys covered by each, target audience of each video. Ask the essential questions in ONE batch: ElevenLabs voice-over (API key + voice ID) or subtitles only? Background music (generate via API = paid credits, provide an MP3, or none)? Language of narration/subtitles/cards? Title-card branding (product name, accent color)?

## 2. Safe environment

NEVER record against production. Set up a local environment: local config (local database, external services disabled or pointed at dead ports, DEMO passwords - they will be filmed), realistic demo data (dedicated seeder), local server running. Verify every page of the journey with curl before recording.

## 3. Pipeline installation

Copy the skill templates into `<project>/demo-video/`:
```bash
cp -R "${CLAUDE_PLUGIN_ROOT}/skills/video-production/templates/" demo-video/
cd demo-video && npm install && npx playwright install chromium
```
Rename the `*.example.mjs` files (config, narration, scenario) and adapt `video.config.mjs`. If voice is enabled: write the key into `demo-video/.elevenlabs.env` (and add that file to .gitignore).

## 4. Scenario and narration

Analyze the views/screens to collect the EXACT selectors and the real button labels. Write `narration.mjs` (short lines, exact labels, addressed to the audience) then `scenario.mjs` (actions cued on the spoken words via `cueFrac` - the voice announces, the action follows). Follow the API and sync rules from SKILL.md.

## 5. Production

```bash
node gen-voice.mjs        # one-shot voice + per-line split (or estimated manifest without a key)
node trim-voice.mjs       # compress TTS silences
FAST=1 node recorder.mjs  # rehearsal: validates every selector in ~1 min
node recorder.mjs         # real recording, paced by the voice
node build.mjs            # editing: MP4 + SRT per video
```
Fix selectors until the FAST rehearsal passes end-to-end before any real recording.

## 6. Quality check, then delivery

Before delivering, verify on evidence: extract frames at the timestamps of spoken actions (at the START and the END of each video) and confirm the screen matches the subtitle; measure audio levels (voice present, music discreet, clean silence at the end). Deliver the MP4s + SRTs, and remind the user to revoke/rotate any API key that was shared in plain text.
