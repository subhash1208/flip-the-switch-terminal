---
name: content-producer
description: >
  Create cinematic MP4 videos using Python (Pillow) for frame-by-frame rendering piped to ffmpeg.
  Supports multiple content types: tech demos, explainers, promos, tutorials, and showcases — each
  with its own narrative structure and slide composition. Fully generic and brandable — supports
  custom color palettes, fonts, and icon sets, or works with no branding at all. Use this skill
  when the user wants to create a video, demo video, product video, explainer video, animated
  presentation, promo, tutorial, or motion graphics piece. Also trigger when the user mentions
  "demo video", "product video", "explainer video", "animated video", "MP4 presentation",
  "promo video", "event video", "tutorial video", or asks to present content as a video.
---

# Content Producer

Generate cinematic, animated MP4 videos using Python frame-by-frame rendering with Pillow and
ffmpeg encoding. Choose a content type template to match your topic, then generate.

## Before You Begin

1. **Read the shared references:**
   - `references/design-system.md` — color palettes, typography, spacing rules
   - `references/story-arcs.md` — narrative structures and slide design principles
   - `references/icons.md` — open-source icon sets and setup instructions
   - `references/media-assets.md` — how to embed user-provided images and video clips
   - `references/music.md` — dynamic music generation system
   - `references/branding-guide.md` — how to set up branded video production

2. **Check for a brand config**: If a `brand/brand.md` file exists, read it and apply
   the brand colors, fonts, logo, icons, music settings, voice, and design rules to the
   generated video.

3. **Check for user-provided assets**: If the user provides images, screenshots, or screen
   recordings (in an `assets/` directory or as file paths), examine them before generating:
   - **Images**: Read them directly (Claude is multimodal)
   - **Video clips**: Extract sample frames via ffmpeg, read those to understand the content
   - Write narration that describes or references the visual content
   - Auto-map each asset to the most appropriate slide
   - See `references/media-assets.md` for the full embedding system

4. **Ask the user** (if not already clear from their request):
   - **What content type?** (or infer from their request)
   - **What style/brand?** Custom colors and fonts, or use the generic dark theme (skip if `brand/brand.md` exists)

5. **Read the content type template** based on their choice:

| Content Type | Template | Best For |
|-------------|----------|----------|
| **Tech Demo** | `templates/demo.md` | Product demos, feature walkthroughs, tool introductions |
| **Explainer** | `templates/explainer.md` | Concepts, architectures, "what is X?" topics |
| **Promo** | `templates/promo.md` | Events, product launches, announcements, teasers |
| **Tutorial** | `templates/tutorial.md` | How-to guides, step-by-step instructions, workshops |
| **Showcase** | `templates/showcase.md` | Portfolios, highlight reels, retrospectives, recaps |

Each template defines the recommended story arc, slide plan, slide-specific design guidance,
and music style — all producing MP4 video output.

## What This Skill Produces

A Python script (e.g., `make_video.py`) that generates **three default artifacts** for every
video project — all produced in the same run unless the user explicitly opts out:

1. **MP4 video** (`<name>.mp4`) — 1920x1080 @ 30fps, H.264, with music + narration mixed in
2. **PNG slide exports** (`slides_png/slide_NN_<name>.png`) — one settled still per slide
3. **PDF deck** (`<name>.pdf`) — all slide stills combined into a single document

The generated script MUST expose a CLI supporting `video`, `narrated`, `pdf`, and `all`
modes, and `all` MUST be the default when no mode is passed (see "PDF + PNG Export" below
for the reference implementation).

Video characteristics:
- 1920x1080 resolution at 30fps
- Rendered frame-by-frame using Pillow (PIL), piped as raw RGB bytes to ffmpeg
- Encoded with H.264 (`libx264` preferred; fall back to `libopenh264`), `yuv420p` pixel format
- Animated slides with eased transitions, kinetic typography, and icon reveals
- Crossfade transitions between slides
- Background music with 7 mood presets (included by default)
- TTS narration via Kokoro (included by default)
- High-quality supersampled SVG icons via ImageMagick (`magick` required — never upscale at
  target size)
- Optional embedding of user-provided images and screen recordings
- Configurable color palette, fonts, and accent colors

## Prerequisites

- **Python 3** with `Pillow` installed
  - Fedora: `sudo dnf install python3-pillow`
  - Ubuntu: `sudo apt install python3-pil`
- **ffmpeg** installed on the system
  - Fedora: `sudo dnf install ffmpeg-free`
  - Ubuntu: `sudo apt install ffmpeg`
- **numpy** (for background music generation)
  - Fedora: `sudo dnf install python3-numpy`
  - Ubuntu: `sudo apt install python3-numpy`
- **Kokoro TTS** (for voice narration)
  ```bash
  pip install kokoro soundfile
  sudo dnf install espeak-ng        # Fedora
  sudo apt install espeak-ng        # Ubuntu
  ```
- **Fonts**: At least one font stack (see `references/design-system.md`)
  - Fedora: `sudo dnf install inter-fonts jetbrains-mono-fonts`
  - Ubuntu: `sudo apt install fonts-inter fonts-jetbrains-mono`
- **Icons** (optional): Clone one of the recommended icon sets (see `references/icons.md`)

## Rendering Pipeline

```
Python (Pillow)                    ffmpeg
+--------------+    raw RGB     +----------+
| Render frame | --stdin pipe-->| Encode   |--> output.mp4
|  as PIL Image|    bytes       | H.264    |
+--------------+                +----------+
```

Each slide is a Python function: `slide_name(frame, total_frames) -> PIL.Image`

- `frame`: current frame number within this slide (0 to total_frames-1)
- `total_frames`: total frames for this slide (duration_seconds * FPS)
- Returns a 1920x1080 RGB `Image` for that frame.

### ffmpeg Command

```python
cmd = [
    "ffmpeg", "-y", "-loglevel", "warning",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", "1920x1080",
    "-pix_fmt", "rgb24",
    "-r", "30",
    "-i", "-",
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "20",
    "-pix_fmt", "yuv420p",
    OUTPUT,
]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
# For each frame:
proc.stdin.write(img.tobytes())
```

**Note**: Prefer `libx264` (broadly available, high quality at `-crf 20`). If it is missing,
fall back to `libopenh264` (no `-preset`/`-crf` flags). Detect with `ffmpeg -encoders` at
script startup or wrap the Popen in a try/except and retry with the fallback encoder.

## Design System

See `references/design-system.md` for the complete palette. Key highlights:

### Color Palette — Default Dark Theme

```python
# Backgrounds
BLACK    = (0, 0, 0)         # bg-primary
GRAY_90  = (24, 24, 27)      # bg-secondary, card backgrounds
GRAY_80  = (39, 39, 42)      # bg-surface
GRAY_70  = (63, 63, 70)      # borders, muted elements

# Text
GRAY_40  = (161, 161, 170)   # muted text, labels
GRAY_30  = (212, 212, 216)   # secondary text
WHITE    = (255, 255, 255)   # primary text

# Accents — configurable per project
ACCENT       = (59, 130, 246)   # Primary accent (blue by default)
ACCENT_LIGHT = (96, 165, 250)   # Lighter accent
ACCENT_DARK  = (29, 78, 216)    # Darker accent

# Semantic colors
TEAL     = (20, 184, 166)    # Solution, positive
GREEN    = (34, 197, 94)     # Success, approved
ORANGE   = (249, 115, 22)    # Warnings, caution
RED      = (239, 68, 68)     # Error, danger
PURPLE   = (139, 92, 246)    # Expressive accent
```

Six accent presets: Blue (default), Cyan, Violet, Amber, Emerald, Rose.

**Color rules:**
- ACCENT on every slide (accent bar, glow, progress bar, or text highlight)
- TEAL for "solution" / "how it works" content
- GREEN for success/approved states
- ORANGE for warnings and caution
- RED for errors and critical states
- Background: BLACK or GRAY_90
- Text hierarchy: WHITE > GRAY_30 > GRAY_40

### Typography

```python
def font(name, size):
    paths = {
        "bold":    "/usr/share/fonts/inter/Inter-Bold.otf",
        "medium":  "/usr/share/fonts/inter/Inter-Medium.otf",
        "regular": "/usr/share/fonts/inter/Inter-Regular.otf",
        "mono":    "/usr/share/fonts/jetbrains-mono/JetBrainsMono-Regular.ttf",
    }
    return ImageFont.truetype(paths[name], size)
```

See `references/design-system.md` for alternative font stacks (Source Sans, Noto, Outfit).

| Element | Font | Size |
|---------|------|------|
| Main title (hero) | bold | 96px |
| Slide headline | bold | 52-64px |
| Sub-headline | bold | 36-48px |
| Body text | regular | 28-36px |
| Card title | bold | 28-32px |
| Card body | regular | 22-26px |
| Small labels | mono | 16-20px |
| Tag pills | mono | 16px |
| Terminal text | mono | 20px |
| Annotations | regular | 20-24px |

### Icons

See `references/icons.md` for icon set options (Lucide, Tabler, Feather, etc.).

```python
ICON_DIR = os.path.join(SCRIPT_DIR, "icons")
_icon_cache = {}

def load_icon(name, size=96, color=WHITE):
    """High-quality SVG → raster icon loader (REQUIRED for all videos).

    Rasterizes the SVG at a high density via ImageMagick (`magick`), then
    LANCZOS-downscales in PIL. This is MUCH sharper than feeding the SVG
    straight to ffmpeg at the target size — ffmpeg rasterizes at the SVG's
    intrinsic (tiny) size and then scales up, which produces blurry edges.
    Always use this version, not the naive ffmpeg one-shot.
    """
    key = (name, size, color)
    if key in _icon_cache:
        return _icon_cache[key]

    svg_path = os.path.join(ICON_DIR, f"{name}.svg")
    if not os.path.exists(svg_path):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        _icon_cache[key] = img
        return img

    # Supersample @ 4x target size at 1024 dpi, then LANCZOS down → crisp edges
    ss = max(256, size * 4)
    cmd = [
        "magick",
        "-background", "none",
        "-density", "1024",
        svg_path,
        "-resize", f"{ss}x{ss}",
        "png:-",
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0 or not result.stdout:
        # Fallback: ffmpeg high-density raster (still better than one-shot scale)
        cmd2 = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", svg_path,
            "-vf", f"scale={ss}:{ss}:flags=lanczos",
            "-f", "image2pipe", "-vcodec", "png", "-",
        ]
        result = subprocess.run(cmd2, capture_output=True)
    img_hi = Image.open(BytesIO(result.stdout)).convert("RGBA")
    img = img_hi.resize((size, size), Image.LANCZOS)

    pixels = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]
            if a > 0:
                pixels[x, y] = (color[0], color[1], color[2], a)

    _icon_cache[key] = img
    return img
```

**Rules:** Don't guess names — list the directory. Cache icons. Sizes: 36-48px inline, 64-80px cards, 96-180px hero.

**Required dependency:** `ImageMagick` (`magick` CLI). Install:
- Fedora: `sudo dnf install ImageMagick`
- Ubuntu: `sudo apt install imagemagick`

Without `magick`, icons fall back to ffmpeg supersampling (still supersampled — not a one-shot scale). **Never** use the old `ffmpeg -vf scale={size}:{size}` one-shot pattern: it rasterizes at the SVG's intrinsic size (often 24×24) and upscales, producing visibly blurry icons. The supersampled path is mandatory for quality output.

## Animation System

### Easing Functions

```python
def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def ease_in_out(t):
    return 3 * t * t - 2 * t * t * t

def clamp01(v):
    return max(0.0, min(1.0, v))

def anim_progress(frame, start_frame, duration_frames):
    if frame < start_frame:
        return 0.0
    t = clamp01((frame - start_frame) / max(1, duration_frames))
    return ease_out_cubic(t)
```

### Animation Patterns

**Staggered reveal:**
```python
items = [("Title", 0.5), ("Body", 1.0), ("Card", 2.0)]
for text, delay_seconds in items:
    p = anim_progress(frame, int(delay_seconds * FPS), 15)
    if p > 0:
        draw.text((100, y), text, font=f, fill=WHITE)
```

**Slide-in from left:**
```python
p = anim_progress(frame, start, duration)
x = -300 + int(400 * p)
```

**Fade-in (use for body text — avoids partial text artifacts):**
```python
p = anim_progress(frame, start, duration)
if p > 0:
    draw.text((x, y), text, font=f, fill=color)
```

**Scale-up + fade-in (for icons):**
```python
def paste_icon_animated(img, icon_img, x, y, progress):
    if progress <= 0:
        return
    p = clamp01(progress)
    scale = 0.5 + 0.5 * p
    new_size = (int(icon_img.width * scale), int(icon_img.height * scale))
    scaled = icon_img.resize(new_size, Image.LANCZOS)
    r, g, b, a = scaled.split()
    a = a.point(lambda v: int(v * p))
    scaled = Image.merge("RGBA", (r, g, b, a))
    offset_x = x + (icon_img.width - new_size[0]) // 2
    offset_y = y + (icon_img.height - new_size[1]) // 2
    img.paste(scaled, (offset_x, offset_y), scaled)
```

**Typing effect (for terminal windows):**
```python
chars = int(len(text) * clamp01((frame - start_frame) / (FPS * 0.6)))
visible = text[:chars]
draw.text((x, y), visible, font=f_mono, fill=color)
```

### Crossfade Transitions

Between slides, render 20 frames (~0.67s) of crossfade:

```python
transition_frames = 20
last_frame = current_slide_func(slide_frames - 1, slide_frames)
for t in range(transition_frames):
    alpha = ease_in_out(t / transition_frames)
    first_frame = next_slide_func(0, next_total)
    blended = Image.blend(last_frame, first_frame, alpha)
    proc.stdin.write(blended.tobytes())
```

### Ambient Glow

```python
def draw_ambient_glow(img, cx, cy, radius, color=ACCENT, intensity=0.08):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    steps = 40
    for i in range(steps):
        r = int(radius * (1 - i / steps))
        alpha = int(255 * intensity * (i / steps))
        c = (*color, alpha)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))
```

Breathing effect:
```python
breathe = 1.0 + 0.15 * math.sin(frame / (FPS * 1.5))
draw_ambient_glow(img, glow_x, glow_y, 500, ACCENT, intensity * breathe)
```

## Visual Components

### Progress Bar
```python
def draw_progress_bar(img, current_slide, total_slides, frame, total_frames):
    draw = ImageDraw.Draw(img)
    progress = (current_slide + frame / total_frames) / total_slides
    bar_w = int(W * progress)
    draw.rectangle([0, H - 4, bar_w, H], fill=ACCENT)
    draw.rectangle([bar_w, H - 4, W, H], fill=GRAY_70)
```

### Accent Bars
```python
p_bar = anim_progress(frame, start, duration)
draw.rectangle([100, y, 100 + int(300 * p_bar), y + 4], fill=accent_color)
```

### Info Cards
```python
draw.rounded_rectangle([80, y, 900, y + 200], radius=6, fill=GRAY_90)
draw.rectangle([80, y, 86, y + 200], fill=TEAL)  # left accent
```

### Terminal Mockup
```python
def draw_terminal(draw, img, x, y, w, h, lines, frame, start_delay):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=(20, 20, 25))
    draw.rounded_rectangle([x, y, x + w, y + 30], radius=8, fill=(35, 35, 42))
    draw.rectangle([x, y + 20, x + w, y + 30], fill=(35, 35, 42))
    for j, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        draw.ellipse([x + 12 + j * 20, y + 8, x + 24 + j * 20, y + 20], fill=c)
    f_mono = font("mono", 20)
    for i, (text, color) in enumerate(lines):
        line_delay = start_delay + i * 0.4
        p = anim_progress(frame, int(line_delay * FPS), 10)
        if p <= 0:
            continue
        chars = int(len(text) * clamp01((frame - int(line_delay * FPS)) / (FPS * 0.6)))
        draw.text((x + 15, y + 40 + i * 28), text[:chars], font=f_mono, fill=color)
```

### Tag Pills

Use **20px minimum** for pill text. Always vertically center text using `textbbox` —
never hardcode a y-offset, as it breaks with different fonts (especially CJK).

```python
def draw_pill(draw, x, y, text, ft, pill_h=36, pad_x=16,
              outline=GRAY_70, fill_color=None, text_color=GRAY_40):
    """Draw a pill with properly vertically-centered text."""
    text_w = text_width(draw, text, ft)
    pill_w = text_w + pad_x * 2
    if fill_color:
        draw.rounded_rectangle([x, y, x + pill_w, y + pill_h],
                               radius=pill_h // 2, fill=fill_color)
    else:
        draw.rounded_rectangle([x, y, x + pill_w, y + pill_h],
                               radius=pill_h // 2, outline=outline, width=1)
    # Vertically center using textbbox (handles all font metrics correctly)
    bb = draw.textbbox((0, 0), text, font=ft)
    text_h = bb[3] - bb[1]
    text_y_offset = bb[1]  # top bearing offset
    text_y = y + (pill_h - text_h) // 2 - text_y_offset
    draw.text((x + pad_x, text_y), text, font=ft, fill=text_color)
    return pill_w
```

## Custom Branding

For a complete guide on setting up branded video production — including brand directories,
config files, fonts, logos, icons, music, and voice — see `references/branding-guide.md`.

The quick version: create a `brand/` directory with a `brand.md` config file and your
logo. The skill reads it automatically and applies your brand to every video.

**Important — Color Dominance**: When a brand is active, the Primary brand color must
dominate. Do NOT assign rainbow colors to feature/benefit cards. Use the Primary color
for all cards and differentiate with icons instead. See the "Color Dominance Rules"
section in `references/branding-guide.md` for the full rules.

### Generated Script Variables

Override these values in the generated script to apply any brand:

```python
# === BRAND CONFIGURATION ===
BRAND_NAME = "My Project"
ACCENT       = (59, 130, 246)
ACCENT_LIGHT = (96, 165, 250)
ACCENT_DARK  = (29, 78, 216)

FONT_PATHS = {
    "bold":    "/path/to/YourFont-Bold.otf",
    "medium":  "/path/to/YourFont-Medium.otf",
    "regular": "/path/to/YourFont-Regular.otf",
    "mono":    "/path/to/MonoFont-Regular.ttf",
}

ICON_DIR = os.path.join(SCRIPT_DIR, "icons")
LOGO_PATH = None  # e.g., "/path/to/logo.png"
```

## Media Assets (Optional)

Embed user-provided screenshots, images, and screen recordings directly into slides.
See `references/media-assets.md` for the full reference.

### Pre-generation: Examining Assets

Before generating the script, Claude must examine the provided assets:

```bash
# For video clips: extract a contact sheet to understand the content
ffmpeg -i assets/demo.mp4 -vf "fps=1,scale=480:-1,tile=4x3" /tmp/contact_sheet.png

# Get clip duration
ffprobe -v error -show_entries format=duration -of csv=p=0 assets/demo.mp4
```

Read the extracted frames or images to understand what they show, then write
narration and auto-assign to the best slide.

### Slide Definition with Assets

```python
slides = [
    (slide_title, "Narration...", 7, None),
    (slide_demo, "Here we see the install...", 10, {
        "path": "assets/demo.mp4",
        "style": "terminal",   # browser | terminal | monitor | phone | plain
    }),
    (slide_ui, "The dashboard shows...", 9, {
        "path": "assets/screenshot.png",
        "style": "browser",
    }),
]
```

### Duration with Video Assets

```python
clip_duration = get_clip_duration(asset["path"])
narration_duration = len(narration_audio) / TTS_SAMPLE_RATE
slide_duration = max(clip_duration, narration_duration) + NARRATION_PADDING
```

### Embedding in Slide Functions

Video clips: extract frames once, then composite the right frame per slide frame.
Images: load once, composite with fade-in animation.

```python
# Pre-load clip frames
clip_frames = load_clip_frames("assets/demo.mp4", target_fps=FPS)

# In the slide render function, for each frame:
clip_idx = max(0, frame - int(delay * FPS))
embed_video_asset(img, clip_frames, clip_idx, x, y, w, h, style="terminal")
```

## Narration with TTS

Voice narration is **included by default** in all generated videos using **Kokoro TTS** —
an open-weight, Apache 2.0 licensed text-to-speech model with 82M parameters and 54 voices
across 8 languages. On first run, Kokoro downloads model weights from Hugging Face (~300MB).

**Defaults and overrides:**
- Voice narration is generated for every slide unless the user explicitly requests no narration
  (e.g., "create a video without narration" or "no voice-over")
- The default voice is `af_heart` (warm female), but the user can request a specific voice
  (e.g., "use a male voice", "use am_michael") or the brand config may specify one
- The user can request a specific language (e.g., "narrate in Spanish")
- If `brand/brand.md` specifies a voice, use that voice instead of the default

### Architecture

Each slide gets a `narration_text` string. The rendering pipeline becomes:

1. **Generate narration**: Kokoro generates a WAV per slide
2. **Auto-calculate durations**: Slide duration = max(speech_length + padding, min_duration)
3. **Render video**: Frames rendered using the calculated durations
4. **Mix audio**: Narration + background music mixed together (music auto-ducks during speech)
5. **Mux**: Final audio muxed with video via ffmpeg

### Slide Definition with Narration

```python
slides = [
    (slide_title, "In this video, you'll learn how to...", 7),
    (slide_problem, "The challenge many teams face is...", 9),
    # (render_function, narration_text, min_duration_seconds)
]
```

### TTS Configuration

```python
TTS_VOICE = "af_heart"       # Kokoro voice ID (see list below)
TTS_LANG = "a"               # 'a' = American English, 'b' = British, etc.
TTS_SPEED = 1.0              # Speech speed multiplier
TTS_SAMPLE_RATE = 24000      # Kokoro native sample rate
NARRATION_PADDING = 1.5      # Extra seconds per slide (before + after speech)
MIN_SLIDE_DURATION = 5       # Minimum slide duration in seconds
```

### Generating Narration

```python
from kokoro import KPipeline

pipeline = KPipeline(lang_code='a')  # American English
audio_chunks = []
for gs, ps, audio in pipeline(narration_text, voice='af_heart', speed=1.0):
    audio_chunks.append(audio)
full_audio = np.concatenate(audio_chunks)  # numpy array at 24kHz
```

### Audio Ducking

Background music automatically reduces volume when narration is active:

```python
# Compute speech envelope
envelope = np.abs(narration_track)
# Smooth with running average
kernel = np.ones(window) / window
envelope = np.convolve(envelope, kernel, mode='same')
# Duck: reduce music to 30% during speech
duck_factor = 1.0 - 0.7 * np.clip(envelope * 5, 0, 1)
music_ducked = music_track * duck_factor
# Mix
final = narration_track * 0.95 + music_ducked
```

### Voice Cloning

To use a custom voice (e.g., your own), provide a `.pt` voice tensor:

```python
import torch
voice_tensor = torch.load('my_voice.pt', weights_only=True)
for gs, ps, audio in pipeline(text, voice=voice_tensor):
    ...
```

### Supported Languages

| Code | Language |
|------|----------|
| `a` | American English |
| `b` | British English |
| `e` | Spanish |
| `f` | French |
| `h` | Hindi |
| `i` | Italian |
| `j` | Japanese (requires `pip install misaki[ja]`) |
| `p` | Brazilian Portuguese |
| `z` | Mandarin Chinese (requires `pip install misaki[zh]`) |

### Popular Voices

Use any of Kokoro's 54 built-in voices. Some popular ones:
- `af_heart` — warm, clear female voice (default)
- `af_bella` — expressive female voice
- `am_adam` — neutral male voice
- `am_michael` — authoritative male voice
- `bf_emma` — British female voice
- `bm_george` — British male voice

## Background Music

Background music is **included by default** in all generated videos. The music system
dynamically generates different soundscapes based on the content type and mood of the video.
See `references/music.md` for the full reference with all layer implementations, chord
progressions, and mood presets.

**Defaults and overrides:**
- Music is always generated unless the user explicitly requests no music
  (e.g., "create a video without music" or "no background music")
- The mood is auto-set by the content type template (e.g., tutorial → `calm`)
- The user can request a specific mood (e.g., "use lofi music", "make it energetic")
- If `brand/brand.md` specifies music settings, use those instead of the template defaults
- The user can request a specific BPM (e.g., "use 120 BPM")

### Mood Presets

| Mood | BPM | Key | Feel | Content Type |
|------|-----|-----|------|-------------|
| `upbeat` | 108–115 | C major | Confident, forward-moving | demo |
| `ambient` | 90–100 | A minor | Thoughtful, contemplative | explainer |
| `energetic` | 122–130 | E minor | Exciting, driving | promo |
| `calm` | 84–92 | D major | Relaxed, focused | tutorial |
| `cinematic` | 100–110 | C major | Uplifting, building | showcase |
| `dark` | 95–105 | D minor | Serious, tension | problem-focused |
| `lofi` | 75–85 | F major | Warm, chill, nostalgic | casual/informal |

### Usage

```python
MUSIC_MOOD = "calm"  # Auto-set by content type, or overridden by user

music = generate_music(duration_seconds, mood=MUSIC_MOOD)
```

Each mood defines its own:
- **Chord progression** — different harmonic feel (major vs minor, resolved vs tense)
- **Active layers** — which instruments play (pads, bass, kick, hi-hat, arp, etc.)
- **Energy level** (0.0–1.0) — controls intensity and layer volume
- **BPM** — tempo matching the content pacing

### Available Layers

| Layer | Description | Used By |
|-------|-------------|---------|
| `pad` | Sustained detuned sine chords | All moods |
| `pad_wide` | Extra detuning + octave doubling | cinematic |
| `sub_bass` | Low sine following chord roots | All moods |
| `arp` | Plucky repeating note pattern | upbeat, ambient, cinematic |
| `arp_mellow` | Soft attack, slow decay arp | lofi |
| `kick` | Half-time punchy kick (beats 1, 3) | upbeat |
| `kick_four` | Four-on-the-floor kick | energetic |
| `kick_gentle` | Soft, felt-not-heard kick | cinematic |
| `hihat` | 8th note pattern with velocity variation | upbeat |
| `hihat_active` | 16th notes with open hat accents | energetic |
| `pluck` | Accent hits at chord changes | upbeat, energetic |
| `shaker` | Very light 16th note filtered noise | energetic |
| `rumble` | Sub-frequency LFO tension | dark |
| `crackle` | Sparse vinyl crackle texture | lofi |

### Dynamic Energy Curves

For moods like `cinematic`, energy builds over the video:

```python
def get_energy(base_energy, t, duration, curve="flat"):
    progress = t / duration
    if curve == "flat":
        return base_energy
    elif curve == "build":
        return base_energy * (0.5 + 0.5 * progress)
    elif curve == "arc":
        return base_energy * (0.6 + 0.4 * math.sin(progress * math.pi * 0.9))
```

### Volume by Mood

| Mood | Volume | Why |
|------|--------|-----|
| `calm` | 0.15 | Barely there — viewer is learning |
| `ambient` | 0.18 | Present but unobtrusive |
| `lofi` | 0.20 | Warm presence |
| `cinematic` | 0.22 | Emotional but not distracting |
| `upbeat` | 0.22 | Confident presence |
| `energetic` | 0.25 | Felt, not overwhelming |
| `dark` | 0.20 | Tension without distraction |

### Muxing

```python
cmd = [
    "ffmpeg", "-y", "-loglevel", "warning",
    "-i", VIDEO_IN, "-i", AUDIO_WAV,
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
    "-shortest", VIDEO_OUT,
]
```

## Quality Verification

After generating the video script, **always verify quality before delivering the final
video**. The skill provides two complementary verification modes:

- `--validate` — **automated checks** that catch font size violations, element overlaps,
  and out-of-bounds elements programmatically (fast, deterministic, catches most bugs)
- `--preview` — **visual inspection** via rendered PNG frames that Claude reads as images
  (catches aesthetic issues that code can't detect)

**Always run `--validate` first**, then `--preview`. Automated checks eliminate entire
categories of bugs before visual inspection even begins.

### Layout Registry

Every generated script must include a layout tracking system that records element
bounding boxes per slide. This enables automated overlap detection and bounds checking.

```python
# ── Layout tracking ──────────────────────────────────────────────────
_slide_elements = {}  # slide_name -> [(label, x, y, w, h), ...]

def track(slide_name, label, x, y, w, h):
    """Register an element's bounding box for validation."""
    _slide_elements.setdefault(slide_name, []).append((label, x, y, w, h))

def clear_tracking(slide_name):
    """Clear tracked elements for a slide (call at start of each slide fn)."""
    _slide_elements[slide_name] = []
```

Use `track()` after drawing any positioned element — cards, terminals, text blocks,
info boxes, pill rows, diagrams:

```python
def slide_example(frame, total):
    img = Image.new("RGB", (W, H), BLACK)
    clear_tracking("slide_example")

    # After drawing a card:
    draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], ...)
    track("slide_example", "feature_card_1", cx, cy, cw, ch)

    # After drawing a terminal:
    th = terminal(draw, tx, ty, tw_val, lines, frame, sd)
    track("slide_example", "terminal", tx, ty, tw_val, th)

    # After drawing a text block with known bounds:
    track("slide_example", "headline", 100, 110, text_w, 60)
```

**What to track**: Cards, terminals, info boxes, pill rows, diagram boxes, large text
blocks, and any element group that could overlap with another. You do NOT need to track
individual animation frames or the progress bar.

### Font Size Enforcement

Every generated script must use a `safe_font()` wrapper instead of calling `font()`
directly for content text. This enforces the 20px minimum at render time:

```python
MIN_FONT_SIZE = 20

def safe_font(name, size, label=""):
    """Font wrapper that enforces minimum size for readability."""
    if size < MIN_FONT_SIZE:
        raise ValueError(
            f"Font size {size}px below {MIN_FONT_SIZE}px minimum"
            f"{f' for: {label}' if label else ''}"
        )
    return font(name, size)
```

**When to use `safe_font()` vs `font()`**:
- `safe_font()` — all visible content text: body, labels, descriptions, pills, terminal
  text, card titles, annotations, captions
- `font()` — only for elements exempt from the minimum: slide numbers in small circles,
  decorative elements that aren't meant to be read as text

### Validate Mode

Every generated script must include a `--validate` mode that runs **programmatic checks**
without rendering the full video. Add this block in `main()`, before narration generation,
after the `--preview` block:

```python
if "--validate" in sys.argv:
    print("Running validation checks...")
    errors = []
    warnings = []

    # Step 1: Render each slide at steady-state to populate layout tracking
    for idx, (fn, narration, min_dur) in enumerate(slides_def):
        total_f = int(max(min_dur, 30) * FPS)
        fn(total_f - 1, total_f)

    # Step 2: Check for element overlaps
    for slide_name, elements in _slide_elements.items():
        for i, (label_a, ax, ay, aw, ah) in enumerate(elements):
            for j, (label_b, bx, by, bw, bh) in enumerate(elements):
                if j <= i:
                    continue
                # Check rectangle overlap
                if (ax < bx + bw and ax + aw > bx and
                        ay < by + bh and ay + ah > by):
                    errors.append(
                        f"  OVERLAP in {slide_name}: "
                        f"'{label_a}' ({ax},{ay},{aw}x{ah}) overlaps "
                        f"'{label_b}' ({bx},{by},{bw}x{bh})"
                    )

    # Step 3: Check canvas bounds (1920x1080)
    for slide_name, elements in _slide_elements.items():
        for label, x, y, w, h in elements:
            if x < 0 or y < 0 or x + w > W or y + h > H - 4:  # -4 for progress bar
                errors.append(
                    f"  OUT OF BOUNDS in {slide_name}: "
                    f"'{label}' ({x},{y},{w}x{h}) exceeds canvas {W}x{H}"
                )

    # Step 4: Report
    if errors:
        print(f"\n{len(errors)} ERROR(S) FOUND:")
        for e in errors:
            print(e)
    if warnings:
        print(f"\n{len(warnings)} WARNING(S):")
        for w in warnings:
            print(w)
    if not errors and not warnings:
        print("  All checks passed.")
    sys.exit(1 if errors else 0)
```

Font size violations are caught at render time by `safe_font()` — if a slide function
uses a size below 20px, the script crashes with a clear error message during validation.

### Preview Mode

Every generated script must include a `--preview` mode. When invoked with `--preview`,
the script renders one sample frame per slide and saves them as PNG files.

**Critical**: Use `max(min_dur, 30)` for the frame count — NOT `min_dur` alone. During
actual playback, narration stretches slides to 20-35 seconds. Using `min_dur` (often 7-10s)
produces a preview at a different total frame count than the real render. While animations
complete well within `min_dur`, the preview should match the actual viewing experience as
closely as possible to avoid any discrepancy.

```python
if "--preview" in sys.argv:
    print("Rendering preview frames...")
    for idx, (fn, narration, min_dur) in enumerate(slides_def):
        total_f = int(max(min_dur, 30) * FPS)
        img = fn(total_f - 1, total_f)
        path = f"/tmp/slide_preview_{idx+1:02d}_{fn.__name__}.png"
        img.save(path)
        print(f"  [{idx+1}] {path}")
    print("Preview complete. Inspect frames before full render.")
    sys.exit(0)
```

Add this block at the start of the `main()` function, before narration generation.

### Inspection Workflow

1. **Generate the script** as usual
2. **Run `--validate` first**: `python3 make_video.py --validate`
   - If errors are reported, fix them before proceeding
   - Font size violations crash immediately with a clear message
   - Overlap and bounds errors are listed with slide name, element labels, and coordinates
3. **Run `--preview`**: `python3 make_video.py --preview`
4. **Read each preview image** — Claude is multimodal — and inspect at three levels:

#### Level 1: Layout & Bounds (macro view)
- Text overflow, truncation, or clipping at slide edges
- Overlapping elements (icons over text, cards over cards)
- Elements placed outside the visible 1920x1080 canvas
- Cards or terminals extending beyond slide margins
- Misaligned connection lines, arrows, or flow diagram connectors
- Missing or broken icons (blank spaces where icons should appear)

**Most Level 1 issues should already be caught by `--validate`.** If you find one
visually that validation missed, add tracking for that element so it's caught
automatically next time.

#### Level 2: Text Readability (critical — most common issue)
- **Minimum text size**: No text in the video should be below **20px** at 1080p.
  At 14-16px, text becomes blurry and unreadable when the video is viewed at
  typical sizes (embedded players, mobile). Apply this rule strictly:
  - Tag pills / labels: **20px minimum** (mono or regular)
  - Card body text: **22px minimum** (regular)
  - Card titles: **26px minimum** (bold)
  - Pipeline/diagram box descriptions: **22px minimum**
  - Data table rows (BPM, stats): **20px minimum**
  - Terminal/code text: **20px minimum** (mono)
  - Annotations, captions, footnotes: **22px minimum**
  - Slide headlines: **48-64px** (bold)
  - Hero titles: **72-96px** (bold)
- **Stat labels** next to large callout numbers (e.g. "of web traffic is video"
  under "82%"): use **28px minimum** so they read clearly alongside the big number
- If any text appears small or hard to read in the preview image, increase its size

**Most Level 2 issues should already be caught by `safe_font()`.** If a font size
violation slips through, it means `font()` was used instead of `safe_font()` — fix
the call site.

#### Level 3: Component Quality (detail view)
- **Pill / tag vertical centering**: Text inside rounded pill shapes must be
  vertically centered. Hardcoding a y-offset (e.g. `y + 5`) breaks across fonts
  because different fonts have different ascent/descent metrics. **Always use
  `textbbox` to compute vertical centering**:
  ```python
  bb = draw.textbbox((0, 0), text, font=ft)
  text_h = bb[3] - bb[1]
  text_y_offset = bb[1]  # top bearing
  text_y = pill_y + (pill_h - text_h) // 2 - text_y_offset
  ```
  This is especially critical for CJK fonts (Japanese, Chinese, Korean) which have
  different metrics than Latin fonts. A pill that looks fine with Inter will have
  misaligned text with Noto Sans CJK.
- **Pill sizing**: The pill height should be `text_height + 12-16px` padding. Too
  tall makes the text look lost; too short clips ascenders/descenders.
- **Card internal spacing**: Ensure title, body, and tag pill don't overlap within
  cards. Leave at least 8px between elements.
- **Icon-to-text alignment**: Icons placed next to text should be vertically
  aligned to the text's visual center, not its top.
- **Consistent spacing**: Similar elements (card rows, list items, table rows)
  should have uniform vertical gaps.
- **Color contrast**: Text on colored backgrounds must have sufficient contrast.
  WHITE on ACCENT is fine; GRAY_40 on GRAY_90 may be too subtle for small text.

5. **Fix any issues** found in the slide functions
6. **Re-validate and re-preview** the fixed slides to confirm the fix
7. **Full render**: Once all checks pass, run the full video render

### When to Skip Preview

Preview can be skipped only if the video uses exclusively standard components (terminal
mockups, info cards, tag pills) with no custom layouts like flow diagrams, multi-element
arrangements, or connection lines. When in doubt, preview.

**Never skip `--validate`** — it's fast and catches the most common bugs automatically.

### Non-Latin Font Considerations

When generating videos in Japanese, Chinese, Korean, Arabic, or other non-Latin scripts:
- CJK fonts (Noto Sans CJK, etc.) use TTC (TrueType Collection) files — specify the
  correct `index` parameter (e.g., `index=0` for JP, `index=1` for KR)
- CJK characters are wider than Latin — leave extra horizontal space in cards and pills
- Pill and tag vertical centering is **especially prone to bugs** with CJK fonts due to
  different ascent/descent metrics — always use `textbbox`-based centering
- Test with preview before full render — never assume Latin-tested layouts work for CJK
## PDF + PNG Export (Default Artifacts)

Every generated script MUST produce PNG slide stills and a combined PDF deck alongside the
MP4 video. These are first-class default artifacts — not optional extras — because users
frequently need the slides as a printable/sharable deck in addition to the video.

### Output paths (declare at top of script)

```python
SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
OUTPUT           = os.path.join(SCRIPT_DIR, "presentation.mp4")
OUTPUT_NARRATED  = os.path.join(SCRIPT_DIR, "presentation_narrated.mp4")
OUTPUT_PDF       = os.path.join(SCRIPT_DIR, "presentation.pdf")
OUTPUT_PNG_DIR   = os.path.join(SCRIPT_DIR, "slides_png")
```

### Render a settled still for each slide

For PDF/PNG output, render each slide at ~85% through its duration so staggered reveals have
settled and nothing is mid-animation. Never use frame 0 — it is pre-animation. Never use the
final frame — it may be mid-crossfade in some designs.

```python
def render_still_for_slide(slide_func, duration_seconds):
    """Render a single settled frame ~85% through the slide."""
    total_frames = int(duration_seconds * FPS)
    settled_frame = int(total_frames * 0.85)
    return slide_func(settled_frame, total_frames)
```

### PNG + PDF export function

```python
def render_pdf():
    """Render PNG stills for each slide and combine them into a single PDF."""
    os.makedirs(OUTPUT_PNG_DIR, exist_ok=True)
    print(f"Rendering {len(slides)} slide stills...")

    stills = []
    for i, slide_entry in enumerate(slides):
        slide_func = slide_entry[0]
        duration   = slide_entry[2]  # (func, narration, duration[, asset])

        img = render_still_for_slide(slide_func, duration)
        # Strip any alpha — PDF requires RGB
        if img.mode != "RGB":
            img = img.convert("RGB")

        name = slide_func.__name__.replace("slide_", "")
        png_path = os.path.join(OUTPUT_PNG_DIR, f"slide_{i+1:02d}_{name}.png")
        img.save(png_path, "PNG", optimize=True)
        stills.append(img)
        print(f"  [{i+1:02d}/{len(slides)}] {png_path}")

    # Combine into a single PDF
    if stills:
        stills[0].save(
            OUTPUT_PDF, "PDF",
            save_all=True,
            append_images=stills[1:],
            resolution=150.0,
        )
        print(f"PDF written: {OUTPUT_PDF}")
```

### CLI wiring

The generated script must accept these modes, with `all` as the default:

```python
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode == "video":
        render_video()
    elif mode == "narrated":
        render_narrated()      # video + music + narration, muxed
    elif mode == "pdf":
        render_pdf()           # PNGs + combined PDF
    elif mode == "all":
        render_video()
        render_narrated()
        render_pdf()
    else:
        print(f"Unknown mode: {mode}. Use one of: video | narrated | pdf | all")
        sys.exit(1)
```

### When to skip

- **User explicitly opts out** ("just the mp4", "no pdf", "skip the pngs") — respect it,
  but still mention in the summary that PDF/PNGs are available via `python make_video.py pdf`.
- **Silent video** (no narration requested) — still produce PDF + PNGs. They are independent
  of narration.

## Quality Checklist

### Automated (enforced by `--validate` and `safe_font()`)
- [ ] `--validate` passes with zero errors
- [ ] **No text below 20px** — enforced by `safe_font()` at render time
- [ ] **No overlapping elements** — enforced by layout registry overlap detection
- [ ] **All elements within canvas bounds** — enforced by bounds checking
- [ ] Script runs without `safe_font()` crashes

### Visual (verified by `--preview` inspection)
- [ ] All text uses configured fonts (graceful fallback if missing)
- [ ] **Pill/tag text is vertically centered** — uses `textbbox`, not hardcoded y-offset
- [ ] ACCENT color appears on every slide
- [ ] Color palette is consistent throughout
- [ ] Background is dark with ambient glow
- [ ] Glow position varies between slides
- [ ] Callout boxes sized to content
- [ ] Icons are cached and filenames verified (don't guess)
- [ ] Icons use supersampled `magick` path (crisp, not blurry)
- [ ] Video is 1920x1080 at 30fps
- [ ] Preview frames inspected — no layout, alignment, or readability issues

### Animation & Transitions
- [ ] Headlines tell a complete story in sequence
- [ ] Body text fades in (not slides in)
- [ ] All animations use eased timing, no linear motion
- [ ] Staggered reveals have 0.5-1.5s delays
- [ ] Crossfade transitions between all slides
- [ ] Progress bar visible at bottom

### Audio
- [ ] Background music included at mood-appropriate volume (see Volume by Mood table)
- [ ] Voice narration included with narration text for every slide
- [ ] Audio ducking: music volume reduces during narration
- [ ] Narrative follows a clear story arc

### Output Artifacts
- [ ] PNG slide stills written to `slides_png/` (one per slide, settled frame)
- [ ] Combined PDF deck written alongside the MP4
- [ ] Script CLI supports `video | narrated | pdf | all` with `all` as default

## Common Pitfalls

1. **Sliding text shows partial characters**: Use fade-in for body text
2. **Icons overlap text**: Calculate text width first
3. **Callout boxes too large**: Size to content
4. **libx264 not available**: Fall back to `libopenh264` (detect or try/except at startup)
5. **Icon names wrong**: List the directory, don't guess
6. **Music too loud**: Use mood-appropriate volume (see Volume by Mood table)
7. **Font not found**: Fall back to system default
8. **Missing music or narration**: Both are included by default — only omit if user explicitly opts out
9. **Wrong voice**: Check `brand/brand.md` for voice preference, then user request, then default to `af_heart`
10. **Misaligned connectors in diagrams**: Always preview slides with flow diagrams or connection lines — route through a horizontal bus line for clean tree layouts
11. **Skipping validation**: Always run `--validate` before `--preview` — it catches overlaps and font violations that visual inspection easily misses
12. **Text too small in pills/tags**: Font sizes of 14-16px are unreadable at 1080p — use 20px minimum for all pill and tag text. Use `safe_font()` to enforce this automatically
13. **Pill text not vertically centered**: Never hardcode `y + 5` offsets — use `textbbox` to compute proper centering. CJK fonts have different metrics than Latin fonts and will misalign with hardcoded offsets
14. **Small description text in cards/boxes**: Pipeline boxes, info cards, and data tables need 22px minimum for descriptions — 18px is too small when viewed at typical video player sizes
15. **Preview at wrong duration**: Always use `max(min_dur, 30)` for preview frame count — using `min_dur` alone produces previews at shorter durations than actual playback, which can mask timing-dependent layout issues
16. **Using `font()` instead of `safe_font()`**: All content text must go through `safe_font()` to enforce the 20px minimum. Only use `font()` directly for decorative elements exempt from the minimum (e.g., tiny step numbers inside circles)
17. **Not tracking elements for validation**: When adding custom layouts (diagrams, multi-column arrangements, flow charts), always call `track()` for each positioned element so `--validate` can detect overlaps automatically
18. **Blurry icons**: Never use `ffmpeg -vf scale={size}:{size}` one-shot — always use the ImageMagick supersample path in `load_icon`
19. **PDF missing or MP4-only delivery**: PNG + PDF are default artifacts. Run `all` mode by default; only skip on explicit user opt-out
20. **PNG at frame 0 or last frame**: Render stills at ~85% through the slide so reveals have settled and no mid-crossfade artifact appears
