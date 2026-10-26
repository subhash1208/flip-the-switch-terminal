# Design System Reference

This file defines the default color palettes, typography, spacing, and design rules for the
video producer skill. All values are configurable — override them to match any brand.

## Color Palettes

### Default Dark Theme (Zinc-based neutral)

A modern, neutral dark palette inspired by contemporary design systems (Tailwind, Shadcn).

| Token | RGB | Hex | Usage |
|-------|-----|-----|-------|
| black | (0, 0, 0) | #000000 | bg-primary |
| gray-95 | (10, 10, 10) | #0a0a0a | near-black background |
| gray-90 | (24, 24, 27) | #18181b | bg-secondary, card backgrounds |
| gray-80 | (39, 39, 42) | #27272a | bg-surface |
| gray-70 | (63, 63, 70) | #3f3f46 | borders, muted elements |
| gray-60 | (82, 82, 91) | #52525b | subtle borders |
| gray-50 | (113, 113, 122) | #71717a | muted text |
| gray-40 | (161, 161, 170) | #a1a1aa | labels, secondary text |
| gray-30 | (212, 212, 216) | #d4d4d8 | secondary text |
| gray-20 | (228, 228, 231) | #e4e4e7 | light borders (on light bg) |
| gray-10 | (244, 244, 245) | #f4f4f5 | light background |
| white | (255, 255, 255) | #ffffff | primary text (on dark) |

### Accent Color Presets

Choose one as the primary accent or define your own. The accent color should be used
consistently throughout the video for visual identity.

| Preset | RGB | Hex | Best For |
|--------|-----|-----|----------|
| **Blue** (default) | (59, 130, 246) | #3b82f6 | Tech, corporate, trust |
| Blue Light | (96, 165, 250) | #60a5fa | Highlights |
| Blue Dark | (29, 78, 216) | #1d4ed8 | Deep accents |
| **Cyan** | (6, 182, 212) | #06b6d4 | Modern, fresh, startup |
| Cyan Light | (34, 211, 238) | #22d3ee | Highlights |
| Cyan Dark | (14, 116, 144) | #0e7490 | Deep accents |
| **Violet** | (139, 92, 246) | #8b5cf6 | Creative, music, events |
| Violet Light | (167, 139, 250) | #a78bfa | Highlights |
| Violet Dark | (109, 40, 217) | #6d28d9 | Deep accents |
| **Amber** | (245, 158, 11) | #f59e0b | Energy, warmth, concerts |
| Amber Light | (251, 191, 36) | #fbbf24 | Highlights |
| Amber Dark | (217, 119, 6) | #d97706 | Deep accents |
| **Emerald** | (16, 185, 129) | #10b981 | Nature, growth, eco |
| Emerald Light | (52, 211, 153) | #34d399 | Highlights |
| Emerald Dark | (4, 120, 87) | #047857 | Deep accents |
| **Rose** | (244, 63, 94) | #f43f5e | Bold, fashion, music |
| Rose Light | (251, 113, 133) | #fb7185 | Highlights |
| Rose Dark | (190, 18, 60) | #be123c | Deep accents |

### Semantic Colors

These colors carry meaning and should be used consistently regardless of the accent choice.

| Purpose | RGB | Hex | When to Use |
|---------|-----|-----|-------------|
| Teal / Solution | (20, 184, 166) | #14b8a6 | "How it works", positive outcomes |
| Green / Success | (34, 197, 94) | #22c55e | Approved, passing, complete |
| Orange / Warning | (249, 115, 22) | #f97316 | Caution, attention needed |
| Red / Error | (239, 68, 68) | #ef4444 | Failure, critical, blocked |
| Purple / Info | (139, 92, 246) | #8b5cf6 | Extra info, optional highlight |

### Default Light Theme

For presentations that need a clean, bright look.

| Token | RGB | Hex | Usage |
|-------|-----|-----|-------|
| bg-primary | (255, 255, 255) | #ffffff | Main background |
| bg-secondary | (244, 244, 245) | #f4f4f5 | Cards, sections |
| bg-surface | (228, 228, 231) | #e4e4e7 | Borders, dividers |
| text-primary | (24, 24, 27) | #18181b | Main text |
| text-secondary | (82, 82, 91) | #52525b | Secondary text |
| text-muted | (113, 113, 122) | #71717a | Labels, captions |

## Typography

### Recommended Open-Source Font Stacks

All fonts below are freely available, well-designed, and suitable for professional video production.

#### Stack 1: Inter + JetBrains Mono (Default — Recommended)
- **Headlines**: Inter Bold — geometric, clean, excellent readability
- **Body**: Inter Regular — optimized for screens
- **Code/Mono**: JetBrains Mono Regular — developer-friendly monospace
- **Install (Fedora)**: `sudo dnf install inter-fonts jetbrains-mono-fonts`
- **Install (Ubuntu)**: `sudo apt install fonts-inter fonts-jetbrains-mono`
- **Google Fonts**: `Inter`, `JetBrains Mono`

#### Stack 2: Source Sans 3 + Source Code Pro
- **Headlines**: Source Sans 3 Bold — Adobe's open-source workhorse
- **Body**: Source Sans 3 Regular — highly legible
- **Code/Mono**: Source Code Pro Regular — clean monospace
- **Install (Fedora)**: `sudo dnf install adobe-source-sans-pro-fonts adobe-source-code-pro-fonts`
- **Google Fonts**: `Source Sans 3`, `Source Code Pro`

#### Stack 3: Noto Sans + Noto Sans Mono
- **Headlines**: Noto Sans Bold — Google's universal font, superb language coverage
- **Body**: Noto Sans Regular
- **Code/Mono**: Noto Sans Mono Regular
- **Install (Fedora)**: `sudo dnf install google-noto-sans-fonts google-noto-sans-mono-fonts`
- **Google Fonts**: `Noto Sans`, `Noto Sans Mono`

#### Stack 4: Outfit + Fira Code (Modern/Creative)
- **Headlines**: Outfit Bold — geometric, modern feel
- **Body**: Outfit Regular
- **Code/Mono**: Fira Code Regular — ligature-rich monospace
- **Install (Fedora)**: `sudo dnf install fira-code-fonts` (Outfit via Google Fonts)
- **Google Fonts**: `Outfit`, `Fira Code`

### Typography Sizing Guide

| Element | Font Weight | Size | Notes |
|---------|-------------|------|-------|
| Main title (hero) | Bold | 96px | Maximum impact |
| Slide headline | Bold | 52-64px | One line preferred |
| Sub-headline | Bold | 36-48px | Supporting context |
| Body text | Regular | 28-36px | Readable at distance |
| Card title | Bold | 28-32px | Within cards |
| Card body | Regular | 22-26px | Card descriptions |
| Small labels | Mono | 16-20px | Tags, metadata |
| Tag pills | Mono | 16px | Category labels |
| Terminal text | Mono | 20px | Code, commands |
| Annotations | Regular | 20-24px | Footnotes, captions |
| Slide numbers | Regular | 18px | Navigation aid |

### Typography Rules

- Headlines: Display/Bold weight — short, punchy, assertive
- Body text: Regular weight — legible, not dense
- Code/technical: Monospace — consistent character width
- Emphasis: Bold OR accent color, never both simultaneously
- Avoid ALL CAPS for long text (short labels only)
- Maintain consistent hierarchy throughout the video

## Spacing Scale

Based on a 4px grid, consistent with modern design systems.

| Name | Value | Usage |
|------|-------|-------|
| xs | 4px | Tight inline spacing |
| sm | 8px | Between related elements |
| md | 16px | Standard padding |
| lg | 24px | Section spacing |
| xl | 32px | Group separation |
| 2xl | 48px | Major sections |
| 3xl | 64px | Slide margins |
| 4xl | 80px | Hero spacing |
| 5xl | 96px | Large gaps |

## Design Principles

1. **Accent with intention** — use the primary accent sparingly for maximum impact
2. **Keep it simple** — generous dark space, restrained color usage
3. **Create balance** — darkest shades for backgrounds, saturated colors for small accents
4. **Accessibility** — ensure sufficient contrast (4.5:1 for small text, 3:1 for large)
5. **Consistency** — same colors, fonts, and spacing throughout the entire video
6. **Visual rhythm** — vary glow position, accent placement, and animation timing between slides

## Color Usage Rules

### Dark Theme (Default)
- Background: BLACK or GRAY_90 only
- Primary text: WHITE
- Secondary text: GRAY_30
- Muted/labels: GRAY_40
- Borders: GRAY_70
- Cards: GRAY_90 with GRAY_70 border
- Accent bar on every slide (glow, progress bar, line, or text)

### Light Theme
- Background: WHITE or GRAY_10
- Primary text: GRAY_95
- Secondary text: GRAY_60
- Muted/labels: GRAY_50
- Borders: GRAY_20
- Cards: GRAY_10 with GRAY_20 border
- Accent bar on every slide
