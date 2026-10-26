# Content Type: Explainer Video

An educational video that explains a concept, technology, architecture, or idea — answering
"what is X?" or "how does X work?" for an audience that may be new to the topic.

## When to Use

- Explaining a concept, protocol, or technology
- Architecture overviews and system design
- "What is X and why should you care?" content
- Onboarding or educational material
- Myth-busting or correcting misconceptions

## Story Arc

Uses the **Problem -> Tension -> Resolution** arc or the **Myth-Busting** arc from
`references/story-arcs.md`, depending on the topic.

**Use Problem -> Resolution** when introducing something new.
**Use Myth-Busting** when correcting a common misconception.

## Slide Plan (Problem -> Resolution variant)

```python
slides = [
    (slide_title,         6),   # Big question or bold statement
    (slide_context,       8),   # Why this topic matters now
    (slide_misconception, 7),   # What people get wrong (optional)
    (slide_core_concept,  9),   # The key idea, clearly explained
    (slide_diagram,       10),  # Visual explanation — architecture or flow
    (slide_example,       9),   # Concrete example or analogy
    (slide_comparison,    8),   # Before/after or with/without
    (slide_takeaways,     8),   # 3 key takeaways
    (slide_closing,       6),   # Resources and next steps
]
```

Total duration: ~71 seconds (~1:11)

## Slide Plan (Myth-Busting variant)

```python
slides = [
    (slide_title,          6),   # Provocative thesis
    (slide_common_belief,  8),   # What "everyone knows"
    (slide_evidence,       9),   # Why it's wrong or incomplete
    (slide_real_story,     9),   # The actual explanation
    (slide_implications,   7),   # What this means for you
    (slide_new_approach,   8),   # The correct way to think about it
    (slide_diagram,        9),   # Visual proof or architecture
    (slide_takeaways,      8),   # Key lessons
    (slide_closing,        6),   # Resources and CTA
]
```

## Slide Design Details

### Title Slide
- Large question mark or concept icon (120-180px) in ACCENT
- Main title as a question ("What Is Service Mesh?") or bold claim
- Subtitle providing context: regular 32px, GRAY_30
- Ambient glow centered, slightly larger intensity (0.10)

### Context Slide
- World or trend icon in ACCENT
- Headline: assertion about why this matters NOW
- 2-3 contextual points fading in
- Optional: large stat callout (e.g., "78% of teams struggle with X")

### Misconception Slide (optional, for myth-busting)
- Quote icon or thought bubble in ORANGE
- Headline: "THE COMMON BELIEF" in GRAY_30
- Body: the misconception stated clearly in WHITE
- Subtle "X" or strikethrough visual indicator
- This creates tension that the next slides resolve

### Core Concept Slide
- Lightbulb or key icon in TEAL
- Headline: the core idea in one sentence
- Body text explaining it simply — use analogies
- Info card highlighting the key insight
- Use TEAL as the accent for "aha moment" feeling

### Diagram / Architecture Slide
- Flow diagram with animated boxes and labeled arrows
- Keep to 5-7 components maximum
- Steps appear sequentially (0.8s stagger)
- Highlight the key component in ACCENT
- Caption explaining the flow below the diagram

### Example Slide
- "EXAMPLE" label in ACCENT mono
- Concrete, relatable scenario
- Can use terminal mockup if it's a technical concept
- Or use info cards with before/after scenarios
- Keep it specific — names, numbers, real situations

### Comparison Slide
- Split layout: left side muted (GRAY_90 bg), right side accent-bordered
- Left: "Without X" — the old/wrong way
- Right: "With X" — the new/correct way
- Clear visual distinction makes the comparison instant
- Use ORANGE for "without" accents, TEAL for "with"

### Takeaways Slide
- "KEY TAKEAWAYS" headline
- 3 numbered points with icons
- Each point: bold title + one-line elaboration
- Staggered reveal (1.0s between items)
- This is the slide people remember — make it count

### Closing Slide
- "LEARN MORE" or "DIVE DEEPER" headline
- Resource links in pill-shaped tags
- Optional: related topics as tags
- Accent glow with breathing effect

## Music Style

**Mood preset**: `ambient` (see `references/music.md`)
- **BPM**: 90–100, **Key**: A minor
- **Layers**: Pads only, very gentle arpeggio, no percussion
- **Energy**: 0.3–0.4 — thoughtful, non-distracting
- **Volume**: 0.18

## Example Prompts

```
Create an explainer video about what WebAssembly is and why it matters
```

```
Create a myth-busting video about common misconceptions about microservices
```
