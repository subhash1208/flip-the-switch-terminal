# Video pipeline reference

## File layout (in `<project>/demo-video/`)

```
demo-video/
├── video.config.mjs      # project config (baseUrl, prepare, voice, music, subtitles)
├── narration.mjs         # lines per video: { videoKey: [{id, text}] }
├── scenario.mjs          # VIDEOS = [{key, badge, intro, outro, run(api)}]
├── recorder.mjs          # ❄ pipeline (do not edit)
├── gen-voice.mjs         # ❄ pipeline
├── trim-voice.mjs        # ❄ pipeline
├── build.mjs             # ❄ pipeline
├── lib/overlay.js        # ❄ cursor + ripple + badge + beat-marker dot
├── cards/card.html       # ❄ animated title card (title/subtitle/kicker via query string)
├── .elevenlabs.env       # secrets (gitignore it!)
├── voice/                # full-*.mp3, clips, manifest.json, music.mp3
└── out/                  # raw webm, timeline.json, tuto-*.mp4, tuto-*.srt
```

## Scenario API (`run(api)`)

| Method | Usage |
|---|---|
| `api.beat(id, fn)` | Plays line `id`; `fn` holds the actions. Duration = max(voice duration + 300 ms, action duration). Automatically triggers the sync clap on the first beat and the marker on every beat |
| `api.cueFrac(f)` | Waits until the current beat's voice reaches fraction `f` (0–0.97). `f` = key-word index ÷ text length |
| `api.goto(url)` | `networkidle` navigation; relative URLs resolved against `config.baseUrl`; re-applies the badge |
| `api.click(sel, {ax, ay, dur})` | Eased glide + realistic click (down 60 ms up). `ax/ay`: anchor point 0–1 inside the element |
| `api.hover(sel, {dur})` | Glide to the element (automatic smooth scroll if off-screen) |
| `api.type(sel, text, {clear})` | Click then type (24 ms/char; `clear` empties the field) |
| `api.select(sel, value)` | Native `<select>` without opening the OS menu |
| `api.scrollTo(y)` / `api.scrollIntoView(sel)` | Eased scrolling |
| `api.wait(ms)` / `api.setBadge(txt)` / `api.page` | Misc; `page` = raw Playwright Page |

Selectors: prefer `id`/`name`; `:visible` when multiple matches; `button:has-text("…")` for labels. Always verify selectors in the view code, then validate with `FAST=1 node recorder.mjs` before any real recording.

## Synchronization internals

1. **Clap**: `startSync()` shows 420 ms of black after the first load; `build.mjs` detects it (`blackdetect d=0.2 pix_th=0.10`, 0.25–1.2 s range before 15 s) and trims the video at its end → shared time zero.
2. **Beat-marker dot**: 8×8 px, `right:2px;bottom:2px`, alternates `#000`/`#808080` on each beat (persists across navigations via `sessionStorage`). `build.mjs` extracts it as 1-px gray rawvideo at 30 fps (same `trim+fps` pipeline as the edit) and detects transitions to the expected color (black for even beats). Falls back to the script clock with a warning if the count mismatches.
3. **Audio**: each voice clip is `adelay`-ed to its beat's measured time, `amix normalize=0`, `loudnorm I=-16:TP=-1.5:LRA=11`. Music: `volume≈0.075`, fade in 1.5 s / out 2.8 s, mixed AFTER the voice loudnorm.
4. **Subtitles**: PNGs rendered by Chromium (semi-transparent rounded box), `overlay enable='between(t,start,end)'`, same timings as the voice; end = next beat start − 0.12 s.

## Cards and fades

Segments per video: `intro card → main → outro card`, `xfade` cross-fades (default 0.5 s). Segment k offset = Σ previous durations − k×fade. Intro ~3.2 s, outro ~2.8 s.

## Voice

- **One-shot per video**: all lines joined with `\n\n` in a single `/v1/text-to-speech/{voice}/with-timestamps` call → continuous intonation. Per-line split uses `alignment.character_start_times_seconds` (cut at start − 0.1 s / end + 0.35 s capped at next start − 0.03 s).
- **Cache**: md5 hash (voiceId|model|full text) per video in `manifest._meta` - editing one line only regenerates its video.
- **trim-voice**: `silencedetect −40 dB / 0.3 s`; keeps 120 ms head, 180 ms tail, 300 ms per internal pause. Stores `cuts` (ms) in the manifest. Typical gain: −15 to −25 %. Idempotent via `manifest-original.json`.
- **Without a key**: `synthetic` manifest (estimated durations), subtitled videos without a voice track + `voice/voix-off-a-generer.txt`.

## Quality check before delivery (mandatory)

1. `build.mjs` logs `marks "...": N beats` for each segment - make sure there is no `⚠ fallback`.
2. Extract frames at SRT timestamps where an action is spoken ("click X") - at the START and the END of the video (drift hits the end) - and verify the screen shows the action.
3. `volumedetect` over 2–3 s during a line (≈ −16 dB) and after the last one (silence or music only ≈ −35 dB).
4. Check the bottom-right corner of a frame: the marker dot must be invisible (delogo).

## Environment requirements

- Node ≥ 20, Playwright + Chromium (`npx playwright install chromium`).
- ffmpeg/ffprobe with: xfade, overlay, delogo, blackdetect (video); amix, adelay, loudnorm, silencedetect, atrim (audio). `build.mjs` pre-flights and lists anything missing.
- The project app reachable locally, seeded via `config.prepare` (re-run before every recording for reproducible data).
