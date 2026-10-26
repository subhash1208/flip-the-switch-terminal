# Content Type: Showcase Video

A highlight reel or retrospective that celebrates achievements, showcases work, or recaps
an event or project. Emphasizes visual impact, results, and emotional resonance.

## When to Use

- Project retrospectives and post-mortems
- Event recaps and highlight reels
- Portfolio or capability showcases
- Year-in-review or milestone celebrations
- Community contribution summaries
- Release notes as a visual summary

## Story Arc

Uses the **Journey** arc from `references/story-arcs.md`.

## Slide Plan

```python
slides = [
    (slide_destination,   6),   # Start with where we ended up (the win)
    (slide_origin,        8),   # Where it all started
    (slide_challenge,     8),   # The first big obstacle
    (slide_breakthrough,  7),   # The turning point
    (slide_momentum,      9),   # Building on success — montage of progress
    (slide_results,       9),   # Metrics and outcomes
    (slide_highlights,    10),  # Key moments or features (card gallery)
    (slide_lessons,       8),   # What we learned
    (slide_whats_next,    7),   # Future direction
    (slide_closing,       6),   # Thank you / credits / CTA
]
```

Total duration: ~78 seconds (~1:18)

## Slide Plan (Event Recap variant)

```python
slides = [
    (slide_title,         6),   # Event name and hero stat
    (slide_scale,         7),   # The numbers — attendees, talks, etc.
    (slide_highlight_1,   8),   # Best moment #1
    (slide_highlight_2,   8),   # Best moment #2
    (slide_highlight_3,   8),   # Best moment #3
    (slide_community,     8),   # Community and collaboration
    (slide_testimonials,  8),   # Quotes from participants
    (slide_stats,         7),   # Final stats summary
    (slide_next_event,    6),   # Next event or CTA
]
```

## Slide Design Details

### Destination Slide (opening)
- Start with the payoff — the final result, the big number, the achievement
- Large stat or achievement: bold 96px in ACCENT
- Subtitle: what this represents, regular 32px, GRAY_30
- Trophy, rocket, or star icon (180px)
- Strong ambient glow (0.10), centered
- This hooks the viewer: "how did we get here?"

### Origin Slide
- "WHERE IT STARTED" label in GRAY_40 mono
- Headline: the initial state — humble, messy, or ambitious
- Body: 2-3 lines describing the starting point
- Use muted colors: GRAY_30 for text, subtle glow
- Optional: small icon representing the early stage

### Challenge Slide
- Mountain or barrier icon in ORANGE
- Headline: the obstacle or problem encountered
- Body: what made it hard — be specific
- Dark info card with ORANGE left accent
- Creates tension: the audience empathizes with the struggle

### Breakthrough Slide
- Lightning or lightbulb icon in TEAL
- Headline: the key insight or turning point
- Body: what changed — the "aha" moment
- Shift accent color to TEAL for this slide
- Brighter glow, shifted position — visual relief after tension

### Momentum Slide
- "BUILDING MOMENTUM" label in ACCENT mono
- Montage-style: 4-6 small cards or milestones
- Each card: date/version + one-line achievement
- Staggered reveal, faster pacing (0.5s between items)
- Accent bar growing across the slide as cards appear
- Conveys acceleration and progress

### Results Slide
- Large stat callouts: 2-3 key metrics
- Each metric: large number (bold 80px, ACCENT) + label (regular 24px, GRAY_30)
- Arranged horizontally or in a grid
- GREEN accents for positive metrics
- Staggered reveal with scale-up animation

### Highlights Slide
- "HIGHLIGHTS" label in ACCENT mono
- Gallery of 3-4 feature/moment cards:
  - Icon (64px) + bold title + one-line description
  - Left accent bars for visual structure
- Staggered reveal (0.8s between cards)
- **Unbranded**: Vary card accent colors (ACCENT, TEAL, PURPLE, GREEN) for variety
- **Branded**: All cards use Primary brand color (see `references/branding-guide.md` Color Dominance Rules)
- This is the richest visual slide — take time (10s)

### Lessons Slide
- Book or brain icon in PURPLE
- "WHAT WE LEARNED" headline
- 3 key lessons as numbered items:
  - Bold title: the lesson
  - Body: one-line elaboration
- Staggered fade-in (1.0s between items)
- Reflective tone — slower animations

### What's Next Slide
- Rocket or arrow icon in ACCENT
- "WHAT'S NEXT" headline
- 2-3 forward-looking items
- Tag pills for upcoming features/events
- Creates anticipation for the future

### Closing Slide
- "THANK YOU" or project name: bold 72px, centered
- Subtitle: bold ACCENT 48px
- Credits or contributor acknowledgments in GRAY_40
- Links in pill-shaped tags
- Large accent glow with breathing effect
- Optional: small icons representing the team/tools

## Music Style

**Mood preset**: `cinematic` (see `references/music.md`)
- **BPM**: 100–110, **Key**: C major
- **Layers**: Wide pads, gentle kick (half-time), swelling arpeggio
- **Energy**: 0.5 → 0.8 (uses `build` energy curve — grows over the video)
- **Volume**: 0.22
- The music should mirror the emotional arc: restrained at origin, building at momentum,
  peaking at results, settling at lessons/closing

## Design Notes

- **Emotional arc**: Start with the win, go back to the struggle, build to the payoff
- **Varied glow colors**: Use ACCENT for wins, TEAL for breakthroughs, ORANGE for challenges
- **Stats are heroes**: Give big numbers room to breathe — don't crowd them
- **Pacing variety**: Momentum slide is faster; lessons slide is slower
- **Credits matter**: If this celebrates a team effort, acknowledge contributors

## Example Prompts

```
Create a showcase video recapping our open source project's first year — 50 contributors,
2000 stars, 15 releases
```

```
Create a highlight reel of PyCon 2025 — 500 attendees, 30 talks, 3 days
```

```
Create a retrospective video about migrating our infrastructure to the cloud
```
