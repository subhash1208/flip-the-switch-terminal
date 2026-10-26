# Content Type: Tech Demo Video

A product demo or feature walkthrough video that introduces a tool, technology, or capability
and shows it in action.

## When to Use

- Introducing a new tool, product, or feature
- Walking through a specific workflow or use case
- Showing before/after with a real terminal demo
- Technical product marketing

## Story Arc

Uses the **Problem -> Tension -> Resolution** arc from `references/story-arcs.md`.

## Slide Plan

```python
slides = [
    (slide_title,         7),   # Hero title with product icon and tagline
    (slide_problem,       9),   # The pain point being solved
    (slide_why_now,       7),   # Why this matters now
    (slide_solution,      7),   # Introduce the product/feature
    (slide_how_it_works,  9),   # Architecture or flow diagram
    (slide_demo,          10),  # Terminal mockup with real commands
    (slide_features,      10),  # Feature cards with icons
    (slide_benefits,      9),   # Key benefits summary
    (slide_closing,       6),   # CTA with repo link or next steps
]
```

Total duration: ~74 seconds (~1:14)

## Slide Design Details

### Title Slide
- Large hero icon (120-180px) in ACCENT, top-right with ambient glow
- Product name label in small bold mono, slides in from left
- Accent bar animates across under the label
- Main title: bold 96px, key word highlighted in ACCENT
- Subtitle: regular 32px, GRAY_30
- Tag pills with staggered reveal (e.g., "Open Source", "CLI", "Linux")

### Problem Slide
- Alert icon in ORANGE (e.g., `alert-triangle`)
- Headline: "THE PROBLEM" or a specific pain statement
- Body text fading in — describe the pain concretely
- Dark panel showing a dangerous or tedious command with orange left accent
- Warning annotation at bottom

### Why Now Slide
- Trend or change icon in ACCENT
- Headline asserting urgency: "X Has Changed Everything"
- 2-3 key points fading in with stagger
- Optional stat callout (large number + label)

### Solution Slide
- Shield or lightbulb icon in TEAL (Secondary color)
- Two-line headline: context in GRAY_30, key concept in TEAL
- Info card with the core value proposition
- Bold emphasis on the key differentiator
- **Branded**: Primary brand color must still appear (e.g., in the emphasis line)

### How It Works Slide
- Flow diagram with animated boxes and arrow connectors
- 3-5 steps appearing sequentially with slide-in animation
- Color-coded result panels: GREEN for success, ORANGE for rejection
- Caption explaining the flow
- **Branded**: Use Primary color for all step boxes; only the final "result" step may use Secondary (TEAL)

### Demo Slide
- "LIVE DEMO" label in ACCENT mono
- Terminal mockup (full-width, ~60% of slide height)
- Typing animation showing a realistic command
- Output appearing line by line
- Result indicator: green checkmark or status message
- Annotation callout below terminal

### Features Slide
- "KEY FEATURES" label in ACCENT mono
- 3-4 cards with left accent bars
- Each card: icon (64px) + bold title + one-line description
- Staggered reveal: 0.8s between cards
- Optional summary callout on the right
- **Unbranded**: Each card may use a different semantic color for variety
- **Branded**: All cards use the Primary brand color; differentiate with icons only (see `references/branding-guide.md` Color Dominance Rules)

### Benefits Slide
- "WHY IT MATTERS" headline
- 3 benefit cards sliding in from left with stagger
- Each: icon + bold title + one-line description
- Optional accent-bordered summary box
- **Branded**: All cards use Primary brand color (same rule as Features Slide)

### Closing Slide
- Large centered icon (180px) in ACCENT with breathing glow
- Accent line animates outward from center
- Product name: bold 72px
- Subtitle: bold ACCENT 56px
- Tagline: regular GRAY_30 28px
- Repo/URL in a pill-shaped tag
- Small icons row at bottom

## Music Style

**Mood preset**: `upbeat` (see `references/music.md`)
- **BPM**: 108–115, **Key**: C major
- **Layers**: Kick (half-time), hi-hat (8ths), sub-bass, pads, arpeggio, pluck accents
- **Energy**: 0.6–0.8 — confident but not overwhelming
- **Volume**: 0.22

## Example Prompt

```
Create a demo video about how our CLI tool simplifies database migrations
```
