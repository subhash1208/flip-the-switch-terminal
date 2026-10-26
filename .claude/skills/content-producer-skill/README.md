# Content Producer Skill

A Claude Code skill for generating cinematic, animated MP4 videos — fully generic, brandable, and open source. Supports multiple content types, each with its own narrative structure, slide composition, and music style.

https://github.com/user-attachments/assets/88ecd7db-c93f-4d1c-9d2d-cc35cf5a6a30

## What It Does

When triggered, this skill instructs Claude Code to generate a Python script that renders an MP4 video frame-by-frame using **Pillow** (PIL) and pipes raw RGB frames to **ffmpeg** for encoding. The resulting videos feature:

- 1920x1080 resolution at 30fps
- Configurable color palettes with multiple presets (blue, cyan, violet, amber, emerald, rose)
- Support for any TTF/OTF fonts (ships with Inter + JetBrains Mono defaults)
- Compatible with any open-source SVG icon set (Lucide, Tabler, Feather, etc.)
- Animated slides with kinetic typography, icon reveals, and eased transitions
- Crossfade transitions between slides
- Terminal mockups with typing animations
- Ambient glow effects with breathing animation
- Dynamic background music with 7 mood presets (upbeat, ambient, energetic, calm, cinematic, dark, lofi)
- Optional AI voice narration via Kokoro TTS (54 voices, 8 languages, voice cloning)
- Auto-ducking: background music volume reduces during narration
- Auto-duration: slide timing adjusts to match narration length
- Progress bar throughout the video
- Custom branding support (colors, fonts, logos)

## Content Types

Choose the right template for your video:

| Type | Template | Best For | Duration | Music |
|------|----------|----------|----------|-------|
| **Tech Demo** | `templates/demo.md` | Product demos, feature walkthroughs | ~74s | Upbeat electronic (110 BPM) |
| **Explainer** | `templates/explainer.md` | Concepts, architectures, "what is X?" | ~71s | Ambient, thoughtful (90-100 BPM) |
| **Promo** | `templates/promo.md` | Events, launches, announcements | ~55s | High energy (120-130 BPM) |
| **Tutorial** | `templates/tutorial.md` | Step-by-step guides, how-to content | ~71s | Calm, focused (85-95 BPM) |
| **Showcase** | `templates/showcase.md` | Retrospectives, recaps, highlight reels | ~78s | Uplifting, cinematic (100-110 BPM) |

## When It Triggers

Claude Code activates this skill when you ask to create a:
- Demo video, product video, or explainer video
- Animated presentation or motion graphics piece
- Event promo, teaser, or announcement video
- Tutorial or how-to video
- Showcase, retrospective, or highlight reel
- MP4 presentation of any content

## Prerequisites

- **Python 3** with `Pillow` installed
  - Fedora: `sudo dnf install python3-pillow`
  - Ubuntu: `sudo apt install python3-pil`
- **ffmpeg** installed on the system (uses `libopenh264` codec)
  - Fedora: `sudo dnf install ffmpeg-free`
  - Ubuntu: `sudo apt install ffmpeg`
- **numpy** (optional, for background music generation)
  - Fedora: `sudo dnf install python3-numpy`
  - Ubuntu: `sudo apt install python3-numpy`
- **Kokoro TTS** (optional, for AI voice narration)
  ```bash
  pip install kokoro soundfile
  sudo dnf install espeak-ng   # Fedora
  sudo apt install espeak-ng   # Ubuntu
  ```
- **Fonts** (at least one stack):
  - Fedora: `sudo dnf install inter-fonts jetbrains-mono-fonts`
  - Ubuntu: `sudo apt install fonts-inter fonts-jetbrains-mono`
- **Icons** — clone one of the recommended icon sets:
  ```bash
  git clone https://github.com/lucide-icons/lucide.git
  ```

## Skill Structure

```
video-skill/
  SKILL.md                    # Main skill: rendering pipeline, animation, components, branding
  README.md                   # This file
  LICENSE                     # MIT License
  templates/
    demo.md                   # Tech demo / product video template
    explainer.md              # Explainer / educational video template
    promo.md                  # Event / product promo template
    tutorial.md               # Step-by-step tutorial template
    showcase.md               # Showcase / retrospective template
  references/
    design-system.md          # Color palettes, typography, spacing rules
    story-arcs.md             # Narrative structures for storytelling
    icons.md                  # Open-source icon libraries guide
    music.md                  # Dynamic music generation system (7 mood presets)
    media-assets.md           # Embedding images and screen recordings
    branding-guide.md         # How to set up branded video production
```

## How It Works

1. Claude reads the shared references (design system, story arcs, icons, media assets)
2. If the user provides assets (images, screen recordings), Claude examines them to understand their content
3. Based on your topic, it selects the appropriate content type template
4. Reads the template for slide structure, design guidance, and music style
5. Auto-maps provided assets to the most appropriate slides and writes matching narration
6. Optionally applies your custom brand colors, fonts, and logo
7. Generates a self-contained Python script (`make_video.py`) that:
   - Defines slide functions, each returning a PIL Image for a given frame
   - Renders all frames sequentially with crossfade transitions
   - Pipes raw RGB bytes to ffmpeg via stdin
   - Optionally generates and muxes background music
   - Optionally generates TTS narration per slide (auto-adjusting durations)

## Usage

```
Create a demo video about how our CLI tool simplifies database migrations
```

```
Create an explainer video about what WebAssembly is and why it matters
```

```
Create a promo video for "Open Source Summit 2025" happening October 10-12 in Dublin
```

```
Create a tutorial video on setting up SSH key authentication
```

```
Create a showcase video recapping our open source project's first year
```

With custom branding:

```
Create a demo video about our monitoring tool using amber accent colors and Outfit font
```

With narration:

```
Create a narrated tutorial video about setting up Docker on Linux
```

With user-provided assets:

```
Create a demo video about our new dashboard. I have these assets:
- assets/install-recording.mp4 (screen recording of the setup process)
- assets/dashboard-overview.png (screenshot of the main UI)
- assets/metrics-page.png (screenshot of the metrics panel)
```

## Custom Branding

Produce on-brand videos by creating a `brand/` directory with your organization's assets:

```
brand/
  brand.md              # Brand config: colors, fonts, rules, voice
  logo.png              # Your logo (transparent PNG)
  fonts/                # Custom font files (optional)
  icons/                # Custom icon set (optional)
```

Just create `brand/brand.md` with your colors and logo, and every generated video
will automatically use your brand. Example:

```
Create a demo video about our new API gateway
```

Claude reads `brand/brand.md`, applies your brand colors, fonts, and logo — no
extra flags or configuration needed.

The skill also works alongside existing brand skills. If your organization already has
brand reference files (color palettes, typography guides), you can copy or reference
them from your `brand/` directory.

See `references/branding-guide.md` for the full setup guide, configuration reference,
and examples.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

This skill builds upon the work of:

- **Brian Smith** — *red-hat-video-skill*, the original video generation skill whose rendering pipeline, animation system, and visual component patterns served as the foundation for this project.
- **Todd Wardzinski** — [red-hat-quick-deck](https://github.com/toddward/red-hat-quick-deck), whose story arc structures, slide design principles, and design system patterns were adapted and extended here.

Both projects are MIT licensed. The brand-specific elements were replaced with a generic, configurable design system to make this skill usable by anyone.
