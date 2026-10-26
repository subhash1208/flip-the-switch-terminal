# Content Type: Tutorial Video

A step-by-step instructional video that teaches the viewer how to accomplish a specific task.
Heavy on terminal mockups, code examples, and sequential demonstrations.

## When to Use

- "How to do X" guides
- Step-by-step technical instructions
- Workshop or lab walkthroughs
- Configuration or setup guides
- Practical, hands-on learning content

## Story Arc

Uses the **How-To** arc from `references/story-arcs.md`.

## Slide Plan

```python
slides = [
    (slide_title,         6),   # What you'll learn
    (slide_why,           7),   # Why this skill matters
    (slide_prereqs,       7),   # What you need before starting
    (slide_step1,         10),  # Step 1 with terminal demo
    (slide_step2,         10),  # Step 2 with terminal demo
    (slide_step3,         10),  # Step 3 with terminal demo
    (slide_pitfalls,      8),   # Common mistakes to avoid
    (slide_result,        7),   # Final result — what success looks like
    (slide_next_steps,    6),   # Resources and further learning
]
```

Total duration: ~71 seconds (~1:11)

**Note**: For complex topics, add more step slides. Each step should be one focused action.

## Slide Design Details

### Title Slide
- "HOW TO" label in ACCENT mono, slides in from left
- Main title: bold 72px, describing the goal (e.g., "Set Up a Git Hook")
- Subtitle: regular 32px, GRAY_30, the benefit
- Book or graduation-cap icon (120px) in ACCENT
- Tag pills: difficulty level, tools used, time estimate

### Why Slide
- Lightbulb icon in TEAL
- Headline: why learning this matters — make it personal
- 2-3 concrete benefits fading in
- Info card with a motivating stat or quote
- Keep this brief — the audience wants to learn, not be sold

### Prerequisites Slide
- Checklist icon in ACCENT
- "BEFORE YOU START" label in ACCENT mono
- List of prerequisites as cards with check icons:
  - Tool versions needed
  - Packages to install
  - Access/permissions required
- Each card fades in with stagger
- Terminal mockup showing install commands (optional)

### Step Slides (1, 2, 3, ...)
Each step slide follows the same structure:

- Step counter: "STEP N" in ACCENT mono, top-left
- Headline: what this step accomplishes (bold 52px)
- Brief explanation: 1-2 lines, regular 28px, GRAY_30
- **Terminal mockup** (primary focus — takes ~60% of slide)
  - Shows the exact command to run
  - Typing animation for the command
  - Output appears line by line after command completes
  - Color-coded output: GREEN for success, ORANGE for warnings
- Annotation below terminal: what to look for in the output

**Step slide design rules:**
- Terminal is the star — make it large and centered
- One command per step (avoid cramming multiple commands)
- If output is long, show only the relevant lines
- Use the step counter consistently across all step slides
- Accent bar color matches step theme (ACCENT for actions, TEAL for verification)

### Pitfalls Slide
- Warning icon in ORANGE
- "COMMON MISTAKES" or "WATCH OUT FOR" headline
- 2-3 pitfall cards with ORANGE left accent:
  - Bold title: the mistake
  - Body: why it happens and how to avoid it
- Staggered reveal
- This slide prevents frustration — don't skip it

### Result Slide
- Celebration icon in GREEN (check, trophy, or rocket)
- "SUCCESS" or "FINAL RESULT" headline
- Terminal mockup showing the final successful state
- Or screenshot/mockup of the completed result
- GREEN accent throughout this slide
- Annotation: what to verify to confirm it worked

### Next Steps Slide
- "KEEP LEARNING" or "NEXT STEPS" headline
- Resource links in pill-shaped tags
- Related topics as numbered suggestions
- Community links (forums, chat, docs)
- Accent glow with breathing effect

## Music Style

**Mood preset**: `calm` (see `references/music.md`)
- **BPM**: 84–92, **Key**: D major
- **Layers**: Soft pads only, barely-there arpeggio, no percussion at all
- **Energy**: 0.2–0.3 — minimal, the viewer is trying to learn
- **Volume**: 0.15
- Alternative: `lofi` mood for a warmer, more casual tutorial feel

## Design Notes

- **Terminal-heavy**: Most slides should feature a terminal mockup
- **Sequential numbering**: Every step slide shows "STEP N" consistently
- **One action per step**: Don't combine multiple commands
- **Verification after action**: Show what success looks like after each step
- **Slower pacing**: Step slides get 10s each; give viewers time to read commands
- **Consistent layout**: All step slides use the same layout for predictability

## Example Prompts

```
Create a tutorial video showing how to set up a Python virtual environment and install dependencies
```

```
Create a how-to video for configuring SSH key authentication on Linux
```

```
Create a step-by-step video tutorial on creating a Dockerfile for a Flask app
```
