# Branding Guide

This guide explains how to set up branded video production — applying your organization's
colors, fonts, icons, and logo consistently across all generated videos.

## Overview

The content-producer skill is brand-agnostic by default. To produce branded content, you
provide a `brand/` directory alongside the skill with your brand assets and a `brand.md`
config file. Once set up, every generated video automatically uses your brand.

```
video-skill/
  SKILL.md
  brand/                  <-- you create this
    brand.md              <-- brand configuration
    logo.png              <-- your logo
    icons/                <-- your icon set (optional)
    fonts/                <-- your font files (optional)
```

## Quick Start

### 1. Create the brand directory

```bash
cd video-skill
mkdir -p brand
```

### 2. Create `brand/brand.md`

This is the brand configuration file that the skill reads. It defines your colors,
fonts, icons, and design rules.

```markdown
# My Brand

## Colors

| Name | RGB | Hex | Usage |
|------|-----|-----|-------|
| Primary | (238, 0, 0) | #ee0000 | Brand accent, must appear on every slide |
| Primary Light | (245, 110, 110) | #f56e6e | Highlights, emphasis |
| Primary Dark | (166, 0, 0) | #a60000 | Deep accents |
| Secondary | (55, 163, 163) | #37a3a3 | Solutions, positive content |

## Color Rules

- Primary color must appear on every slide (accent bar, glow, or text)
- Never use the primary color for negative states (errors, warnings)
- Background is always dark (#000000 or #1f1f1f)

## Fonts

| Weight | File | Usage |
|--------|------|-------|
| Bold | brand/fonts/MyBrand-Bold.otf | Headlines, titles |
| Medium | brand/fonts/MyBrand-Medium.otf | Sub-headlines |
| Regular | brand/fonts/MyBrand-Regular.otf | Body text |
| Mono | brand/fonts/MyBrand-Mono.otf | Code, terminal, labels |

## Logo

- File: `brand/logo.png`
- Place on title and closing slides
- Minimum clear space: 20px on all sides

## Icons

- Directory: `brand/icons/`
- Or use a public icon set (Lucide, Tabler, etc.)

## Voice

- Preferred TTS voice: af_heart (or specify your own)
- Tone: professional, confident, clear

## Music

- Default mood: upbeat
- BPM: 110
```

### 3. Add your assets

```bash
# Copy your logo
cp /path/to/logo.png brand/logo.png

# Copy your brand fonts (if you have custom fonts)
mkdir -p brand/fonts
cp /path/to/fonts/*.otf brand/fonts/

# Clone or copy your icon set (optional)
git clone https://github.com/your-org/your-icons.git brand/icons
```

### 4. Use it

Just ask Claude to create a video — it reads `brand/brand.md` and applies your brand:

```
Create a demo video about our new API gateway
```

Claude will read `brand/brand.md`, use your colors, fonts, logo, and icons automatically.

You can also be explicit:

```
Create a demo video about our API gateway using the brand config in brand/
```

## Color Dominance Rules (When Branded)

When a `brand/brand.md` is active, the templates' default multi-color behavior changes.
Branded videos must feel cohesive and on-brand — not like a generic rainbow palette.

### Rule 1: Primary brand color on every slide

The brand's Primary color must have a **visible, intentional presence** on every slide —
not just the progress bar. At minimum, one of: accent bar, glow, headline highlight,
icon color, or card border.

### Rule 2: Primary color dominates lists and cards

When a template calls for "colored accent bars" on feature cards, benefit cards, or
similar list layouts, **use the Primary brand color for all cards by default**. Do NOT
assign a different color to each card unless the brand config explicitly defines a
multi-color card strategy.

**Unbranded (default):**
```python
# Each card gets a different color for visual variety
features = [
    ("CLI Tool",    ACCENT),
    ("Security",    TEAL),
    ("Automation",  PURPLE),
    ("Monitoring",  BLUE),
]
```

**Branded:**
```python
# All cards use the primary brand color
features = [
    ("CLI Tool",    ACCENT),
    ("Security",    ACCENT),
    ("Automation",  ACCENT),
    ("Monitoring",  ACCENT),
]
```

To avoid visual monotony with same-color cards, vary the **icon** per card (different
icon shapes provide enough differentiation) and use subtle differences in the glow
position or animation delay.

### Rule 3: Secondary colors only for semantic meaning

The brand's Secondary color (mapped to `TEAL`) should only appear on slides where its
**semantic meaning** applies — specifically "solution" or "how it works" content. It
should not be used as decoration on unrelated slides.

| Color Role | When to Use | When NOT to Use |
|------------|-------------|-----------------|
| Primary | Every slide — accent bars, glows, highlights | Never for negative states (unless brand allows) |
| Secondary | "Solution" slides, "how it works" diagrams | Feature cards, benefit lists, random decoration |
| Success | Checkmarks, passing states, approvals | Card accent bars |
| Warning | Caution states, attention callouts | Card accent bars |
| Expressive | Only if brand explicitly calls for it | Default card/list coloring |

### Rule 4: Solution slide uses Secondary, but Primary must also appear

On "solution" or "how it works" slides, the Secondary (TEAL) color is appropriate for
the solution content itself. But the Primary brand color must still be visually present
on that slide — for example, in the section label, accent bar, or progress indicator
(beyond just the progress bar).

### Rule 5: How It Works flow diagrams

For flow diagrams with multiple steps, use the **Primary color** for all step boxes.
Differentiate steps through icons, numbering, or labels — not through color. The only
exception is the final "result" step, which may use the Secondary color to signal
"solution reached."

**Unbranded:**
```python
steps = [("Input", ACCENT), ("Process", TEAL), ("AI", PURPLE), ("Output", GREEN)]
```

**Branded:**
```python
steps = [("Input", ACCENT), ("Process", ACCENT), ("AI", ACCENT), ("Output", TEAL)]
```

## Brand Configuration Reference

### Colors

Define your brand colors as RGB tuples. The skill maps them to the standard palette:

| Brand Config Key | Maps To | Purpose |
|-----------------|---------|---------|
| Primary | `ACCENT` | Main brand color, used on every slide |
| Primary Light | `ACCENT_LIGHT` | Highlights, emphasis |
| Primary Dark | `ACCENT_DARK` | Deep accents, CTA buttons |
| Secondary | `TEAL` | Solutions, "how it works" content |
| Success | `GREEN` | Approved, passing states |
| Warning | `ORANGE` | Caution, attention needed |
| Error | `RED` | Failures, critical (unless brand says otherwise) |
| Expressive | `PURPLE` | Optional accent for variety |

**Brand-specific color rules**: Some brands have specific rules (e.g., "never use the
primary color for negative things"). Document these in your `brand.md` and the skill
will follow them.

### Fonts

You can provide fonts in three ways:

**Option A: Brand font files in `brand/fonts/`**
```markdown
## Fonts
| Weight | File |
|--------|------|
| Bold | brand/fonts/BrandDisplay-Bold.otf |
| Medium | brand/fonts/BrandDisplay-Medium.otf |
| Regular | brand/fonts/BrandText-Regular.otf |
| Mono | brand/fonts/BrandMono-Regular.otf |
```

**Option B: System-installed fonts**
```markdown
## Fonts
| Weight | File |
|--------|------|
| Bold | /usr/share/fonts/brand/BrandDisplay-Bold.otf |
| Regular | /usr/share/fonts/brand/BrandText-Regular.otf |
| Mono | /usr/share/fonts/brand/BrandMono-Regular.otf |
```

**Option C: Google Fonts (loaded at video render time)**
```markdown
## Fonts
Use Google Fonts: Inter (headlines), Inter (body), JetBrains Mono (code)
```

### Logo

- Place as `brand/logo.png` (transparent PNG recommended)
- The skill overlays it on title and closing slides
- Specify placement rules in `brand.md` if needed

```markdown
## Logo
- File: brand/logo.png
- Title slide: top-left breadcrumb area, small (height: 28px)
- Closing slide: centered, large (height: 60px)
- Never distort, recolor, or place on busy backgrounds
```

### Icons

**Option A: Custom icon set**
```bash
# Clone your organization's icon repo
git clone https://github.com/your-org/your-icons.git brand/icons
```

```markdown
## Icons
- Directory: brand/icons/src/standard/
- Use standard set for slide pictograms
- Don't guess names — list the directory
```

**Option B: Use a public icon set (default)**

No configuration needed — the skill defaults to Lucide icons. You can specify a
different set in `brand.md`:

```markdown
## Icons
Use Tabler Icons (already cloned at tabler-icons/)
```

### Music

Background music is **always included** by default. The brand config overrides the
content type template's default mood. The music is generated procedurally using the
implementation from `references/music.md`.

If the brand does not specify music settings, the content type template's defaults apply
(e.g., tutorial → `calm`, demo → `upbeat`). The user can also request a specific mood
or BPM in their prompt, which takes priority over both the brand and template defaults.

```markdown
## Music
- Default mood: upbeat
- BPM: 112
- Demo videos: upbeat (BPM 112)
- Explainers: ambient (BPM 94)
- Promos: energetic (BPM 126)
- Tutorials: calm (BPM 88)
- Showcases: cinematic (BPM 104)
```

**Priority order**: user request > brand config > content type template default.

### Voice

Voice narration is **always included** by default. The brand config specifies the preferred
voice and speed. If the brand does not specify a voice, the default `af_heart` is used.
The user can also request a specific voice in their prompt, which takes priority.

```markdown
## Voice
- Voice: am_michael (authoritative male)
- Speed: 1.0
- Language: en (American English)
```

Or provide a custom voice tensor for voice cloning:

```markdown
## Voice
- Custom voice: brand/voice.pt
- Speed: 1.0
```

**Priority order**: user request > brand config > default (`af_heart`).

## Combining with Existing Brand Skills

If your organization already has a brand skill (e.g., a slide deck skill with brand
guidelines), you can reference it from `brand/brand.md`:

```markdown
# My Brand

See also: the brand reference at `path/to/other-brand-skill/references/brand.md`
for the complete color palette and typography rules.

## Colors
(copy or reference the relevant colors)

## Fonts
(copy or reference the font paths)
```

Or simply copy the brand reference files into your `brand/` directory:

```bash
# Example: copying brand references from another skill
cp other-skill/references/brand-colors.md brand/
cp other-skill/references/brand-typography.md brand/
```

The skill reads everything in `brand/` and applies it consistently.

## Example: Setting Up a Brand

Here's a complete example of setting up a fictional "Acme Corp" brand:

### 1. Create the brand directory

```bash
mkdir -p brand/fonts brand/icons
```

### 2. Write `brand/brand.md`

```markdown
# Acme Corp Brand

## Colors

| Name | RGB | Hex | Usage |
|------|-----|-----|-------|
| Acme Blue | (0, 102, 204) | #0066cc | Primary accent |
| Acme Blue Light | (51, 153, 255) | #3399ff | Highlights |
| Acme Blue Dark | (0, 71, 153) | #004799 | Deep accents |
| Acme Green | (0, 153, 76) | #00994c | Success, solutions |

## Color Rules

- Acme Blue must appear on every slide
- Use Acme Green for positive outcomes and solutions
- Background: always dark (#0a0a0a)

## Fonts

| Weight | File |
|--------|------|
| Bold | /usr/share/fonts/inter/Inter-Bold.otf |
| Medium | /usr/share/fonts/inter/Inter-Medium.otf |
| Regular | /usr/share/fonts/inter/Inter-Regular.otf |
| Mono | brand/fonts/FiraCode-Regular.ttf |

## Logo

- File: brand/logo.png
- Title slide: top-left, height 28px
- Closing slide: centered, height 60px

## Icons

Use Lucide icons (default)

## Voice

- Voice: af_heart
- Tone: friendly, professional

## Music

- Default mood: upbeat
```

### 3. Add the logo

```bash
cp ~/company-assets/acme-logo-white.png brand/logo.png
```

### 4. Generate branded videos

```
Create a demo video about our new Acme Dashboard
```

Every video will use Acme Blue accents, the Acme logo on title/closing slides,
and the configured fonts and voice.

## Tips

- **Start simple**: Just a `brand.md` with colors and a logo is enough to get started.
  You can add fonts, icons, and detailed rules later.
- **Test with a short video**: Generate a quick 30-second video to verify your brand
  looks right before producing longer content.
- **Keep brand.md concise**: The skill reads the entire file. Focus on what's different
  from the defaults — you don't need to redefine everything.
- **Version your brand config**: Commit `brand/brand.md` and `brand/logo.png` to your
  repo so your team stays consistent.
- **Don't commit fonts**: Large font files bloat the repo. Use system-installed fonts
  or document the install command instead.
