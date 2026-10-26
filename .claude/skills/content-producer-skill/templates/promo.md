# Content Type: Promo Video

A high-energy promotional video for events, product launches, announcements, or teasers.
Prioritizes mood, excitement, and visual impact over detailed information.

## When to Use

- Event announcements and promos
- Product launches and release teasers
- Conference or meetup promotions
- Brand awareness campaigns
- Announcement teasers ("coming soon")

## Story Arc

Uses the **Showcase** arc from `references/story-arcs.md`, adapted for promotion.

## Slide Plan

```python
slides = [
    (slide_teaser,        5),   # Bold hook — one line, maximum impact
    (slide_title,         7),   # Event/product name with date and branding
    (slide_vibe,          6),   # Set the mood — what makes this special
    (slide_highlights,    9),   # Lineup, features, or key attractions
    (slide_experience,    7),   # What to expect — immersive description
    (slide_social_proof,  7),   # Past success, testimonials, numbers
    (slide_details,       8),   # Dates, locations, pricing, logistics
    (slide_cta,           6),   # Strong call to action
]
```

Total duration: ~55 seconds (~0:55)

**Note**: Promo videos are shorter and punchier than other types. Every second counts.

## Slide Design Details

### Teaser Slide
- Minimal: just one bold line of text, centered
- Large bold 96px, WHITE text, key word in ACCENT
- Strong ambient glow (intensity 0.12), centered
- No icons, no decorations — pure typography impact
- Hold for 5 seconds to build anticipation

### Title Slide
- Event/product name: bold 96px, ACCENT
- Date and location (if event): bold 36px, WHITE
- Or version/tagline (if product): regular 32px, GRAY_30
- Large icon or logo placement (180px)
- Tag pills: category tags with staggered reveal
- Intense ambient glow (0.10) in ACCENT

### Vibe Slide
- Atmospheric: subdued text, strong visual mood
- One-line headline capturing the essence: bold 64px
- 2-3 evocative descriptors fading in (e.g., "Live Music", "Open Source", "Community")
- Icons for each descriptor (music, code, users)
- Accent bars between descriptors
- Glow shifted to a different position for variety

### Highlights Slide
- "FEATURING" or "HIGHLIGHTS" label in ACCENT mono
- 3-4 items with large icons (80px) and names
- If event: speaker/artist names + topics
- If product: key features or capabilities
- Staggered reveal with faster timing (0.6s between items)
- Cards with accent left borders

### Experience Slide
- Immersive description: what it feels like to be there / use it
- Split into 2-3 short, punchy statements
- Each fades in with an icon
- Use varied accent colors: ACCENT, TEAL, PURPLE for visual energy
- Glow shifted to bottom-left for contrast

### Social Proof Slide
- Large stat callout: "500+ Attendees" or "10K+ Downloads"
- Big number in ACCENT (bold 120px)
- Supporting context in GRAY_30
- Optional: 2-3 testimonial snippets in info cards
- Or: logos/names of past participants

### Details Slide
- Clean, scannable layout
- Info cards with icons for each detail:
  - Calendar icon + Date
  - Map pin icon + Location/Platform
  - Ticket icon + Price/Registration
  - Clock icon + Schedule
- Cards have ACCENT left borders
- Staggered reveal

### CTA Slide
- Strong, urgent call to action
- Headline: bold 72px, ACCENT ("Register Now" / "Get Started" / "Join Us")
- URL or action in a large pill-shaped tag
- Countdown or urgency text: "Limited Spots" / "Early Bird Ends Soon"
- Large accent glow, breathing effect
- Social handles in small mono at bottom

## Music Style

**Mood preset**: `energetic` (see `references/music.md`)
- **BPM**: 122–130, **Key**: E minor
- **Layers**: Four-on-the-floor kick, active hi-hat with open hat accents, heavy sub-bass,
  bright arpeggio, pads, pluck accents, shaker
- **Energy**: 0.8–1.0 — driving and exciting
- **Volume**: 0.25

## Design Notes

- **Shorter slides**: Promo videos are fast-paced. No slide over 9 seconds.
- **Less text**: Prioritize mood and impact over information density.
- **Bolder visuals**: Stronger glow (0.10-0.12), more accent color usage.
- **Faster animations**: Reduce stagger delays to 0.5-0.6s between elements.
- **Color variety**: Use ACCENT + TEAL + PURPLE across slides for energy.

## Example Prompts

```
Create a promo video for "Open Source Summit 2025" happening October 10-12 in Dublin
```

```
Create a teaser video announcing the launch of our new CLI tool "FluxDeploy"
```

```
Create an event promo for a community open source hackathon
```
