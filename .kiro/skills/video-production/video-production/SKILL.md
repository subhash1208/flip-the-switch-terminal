---
name: video-production
description: Use when producing a tutorial/demo video of a web app - recording browser walkthroughs with a visible cursor, synchronized ElevenLabs voice-over, burned-in subtitles, background music, or when the /video command is invoked, or when debugging desynchronized audio/video, drifting captures, or silent TTS gaps in such a pipeline.
---

# Tutorial video production (Playwright + ffmpeg + ElevenLabs)

## Overview

A 4-script pipeline (templates in `templates/`, copied into `<project>/demo-video/`):

| Script | Role |
|---|---|
| `gen-voice.mjs` | ElevenLabs voice **one-shot per video** (continuous intonation) via `/with-timestamps`, split per line. Without a key: estimated manifest (65 ms/char) |
| `trim-voice.mjs` | Cuts TTS silences (head/tail + internal pauses > 0.4 s) - eleven_v3 inserts up to 1.4 s between word groups |
| `recorder.mjs` | Playwright capture: visible animated cursor, badge, realistic typing, beats paced by voice-clip durations. `FAST=1` = quick rehearsal |
| `build.mjs` | Editing: xfade, burned-in PNG subtitles, voice aligned to measured video time, music, loudnorm, MP4 + SRT |

Order: `gen-voice → trim-voice → FAST=1 recorder (repeat until zero errors) → recorder → build`.
The project-specific work lives in `scenario.mjs` + `narration.mjs` + `video.config.mjs` - never modify the 4 pipeline scripts.

## Voice/image sync - the critical part

Two non-negotiable mechanisms (already in the templates, do not bypass):

1. **Clap + beat marker.** Playwright capture starts late AND drops frames on every navigation (up to 2.7 s of cumulative drift measured). The script clock does NOT match video time. The recorder shows a black clap (detected via `blackdetect`) and an 8×8 px dot alternating black/gray on every line; `build.mjs` scans the dot frame-by-frame to align every audio clip to **measured** video time, then erases it (`delogo`).
2. **Fractional cues.** In `scenario.mjs`, every action fires via `api.cueFrac(f)` where `f` = key-word position in the text ÷ text length (e.g. "then click Filter" at index 61 of a 78-char line → `cueFrac(0.78)`). Never hard-code millisecond delays: they break as soon as the voice changes. The voice announces, the action follows.

## Narration rules

- One explicit audience per video (admin ≠ end user): "you", their vocabulary.
- Quote the EXACT button/menu labels - check them in the view code before generating the voice (regeneration costs credits).
- One line = one idea + one on-screen action. Short sentences, precise and friendly tone.

## Safety - non-negotiable

- Local environment only: local database, external APIs cut (flag off + key emptied + URL pointed at a dead port), mail in log mode, **demo password** (it gets filmed).
- ElevenLabs key in `.elevenlabs.env` (gitignored). Remind the user to revoke it after use if it was shared in plain text.
- The ElevenLabs Music API costs credits: `music.generate: true` only with the user's explicit consent.

## Common pitfalls

| Symptom | Cause / fix |
|---|---|
| Voice out of sync with image | Aligned on script clock instead of markers - check build.mjs `marks` logs |
| `subtitles`/`drawtext` filter not found | Minimal ffmpeg build (no libass) - templates use PNG overlay; pre-flight checks filters |
| Click opens a native file picker (hangs) | Never click a dropzone: use `page.setInputFiles()` directly |
| `confirm()`/`alert()` freeze the capture | `page.on('dialog', accept)` is already in the recorder; do not remove it |
| `silencedetect`/`blackdetect` return nothing in Node | ffmpeg logs to **stderr**: use `spawnSync` and read `res.stderr`, not `execFileSync` |
| eleven_v3 returns 400 | Supports neither `previous_text`/`next_text` nor `style`/`use_speaker_boost`; `stability` ∈ {0.0, 0.5, 1.0} |
| Native `<select>` shows nothing on click | OS menu is not captured: use `api.select()` (hover + `selectOption`) |
| Element "hidden" although visible on screen | Multiple matches, one hidden: narrow the selector or use `:visible` |
| Voice feels slow | Run `trim-voice.mjs` (TTS silences); do NOT regenerate the voice |

Detailed architecture, full scenario API and the QA procedure: [references/pipeline.md](references/pipeline.md).
