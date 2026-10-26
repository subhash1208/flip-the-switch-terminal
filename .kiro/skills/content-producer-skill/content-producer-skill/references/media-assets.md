# Media Assets Reference

This reference defines how to embed user-provided visual assets (screenshots, images,
screen recordings) into generated videos. Assets are auto-mapped to slides and narrated
by the TTS system.

## Workflow

```
User provides:                   Claude does:                    Script renders:
  assets/install.mp4        -->  Reads frames, understands   --> Composites into slide
  assets/dashboard.png           content, writes narration       with mockup frame
  "make a demo video"            Auto-maps to best slide         Duration = max(clip, speech)
```

### Step-by-step

1. **User provides assets** in an `assets/` directory (or as file paths in the prompt)
2. **Claude examines each asset**:
   - Images: reads them directly (multimodal)
   - Videos: extracts 3 sample frames (first, middle, last) via ffmpeg, reads those
3. **Claude understands the content** — what the asset shows, what's happening
4. **Claude writes narration** that describes or references the visual content
5. **Claude auto-maps** each asset to the most appropriate slide
6. **The generated script** composites assets into slides at render time
7. **Slide duration** auto-adjusts: `max(clip_duration, narration_duration) + padding`

## Examining Assets (Claude's Pre-generation Step)

Before writing the video script, Claude should examine the provided assets.

### For images
Just read the image file — Claude can see it directly.

### For video clips
Extract sample frames to understand the content:

```bash
# Extract first, middle, and last frame from a clip
ffmpeg -i assets/demo.mp4 -vf "select=eq(n\,0)" -frames:v 1 /tmp/frame_first.png
ffmpeg -i assets/demo.mp4 -vf "select=eq(n\,$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 assets/demo.mp4 | awk '{print int($1/2)}')" -frames:v 1 /tmp/frame_mid.png
ffmpeg -i assets/demo.mp4 -vf "reverse" -frames:v 1 /tmp/frame_last.png

# Get clip duration and frame count
ffprobe -v error -show_entries format=duration -of csv=p=0 assets/demo.mp4
ffprobe -v error -show_entries stream=r_frame_rate -of csv=p=0 assets/demo.mp4
```

Or more simply, extract a grid of frames:
```bash
# Extract one frame per second as a contact sheet
ffmpeg -i assets/demo.mp4 -vf "fps=1,scale=480:-1,tile=4x3" /tmp/contact_sheet.png
```

Read the extracted frames to understand what the clip shows.

## Slide Definition with Assets

```python
slides = [
    # (render_func, narration, min_duration, asset_config_or_None)
    (slide_title, "Welcome to...", 7, None),

    (slide_demo, "Here we can see the installation in progress...", 10, {
        "path": "assets/install-recording.mp4",
        "style": "terminal",
    }),

    (slide_features, "The dashboard provides a clear overview...", 9, {
        "path": "assets/dashboard-screenshot.png",
        "style": "browser",
    }),
]
```

## Asset Configuration

```python
{
    "path": "assets/demo.mp4",   # Path to the asset file
    "style": "browser",          # Frame mockup style (see below)
    "position": "center",        # Position on slide: "center", "right", "left"
    "size": 0.55,                # Size as fraction of slide width (0.0-1.0)
    "delay": 1.0,                # Seconds before asset appears (for animation)
}
```

All fields except `path` are optional with sensible defaults.

## Frame Mockup Styles

### `browser` — Web browser window
```python
def draw_browser_frame(draw, img, x, y, w, h, url=""):
    # Window chrome
    draw.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=(30, 30, 35))
    # Title bar
    draw.rounded_rectangle([x, y, x + w, y + 36], radius=8, fill=(42, 42, 48))
    draw.rectangle([x, y + 28, x + w, y + 36], fill=(42, 42, 48))
    # Traffic lights
    for j, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        draw.ellipse([x + 12 + j * 20, y + 10, x + 24 + j * 20, y + 22], fill=c)
    # Address bar
    bar_x = x + 80
    bar_w = w - 100
    draw.rounded_rectangle([bar_x, y + 8, bar_x + bar_w, y + 28], radius=4, fill=(24, 24, 28))
    if url:
        draw.text((bar_x + 8, y + 10), url, font=font("mono", 12), fill=GRAY_40)
    # Content area starts at y + 36
    return (x + 1, y + 36, w - 2, h - 37)  # inner content rect
```

### `terminal` — Terminal window (already exists in the skill)

### `monitor` — Simple screen with subtle bezel
```python
def draw_monitor_frame(draw, img, x, y, w, h):
    # Outer bezel
    draw.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=(20, 20, 24))
    # Inner screen area
    inset = 3
    return (x + inset, y + inset, w - inset * 2, h - inset * 2)
```

### `phone` — Mobile device frame
```python
def draw_phone_frame(draw, img, x, y, w, h):
    # Device body
    draw.rounded_rectangle([x, y, x + w, y + h], radius=24, fill=(30, 30, 35))
    # Screen inset
    inset = 6
    draw.rounded_rectangle(
        [x + inset, y + inset, x + w - inset, y + h - inset],
        radius=18, fill=(0, 0, 0)
    )
    # Notch
    notch_w = 80
    draw.rounded_rectangle(
        [x + w // 2 - notch_w // 2, y, x + w // 2 + notch_w // 2, y + 20],
        radius=10, fill=(30, 30, 35)
    )
    return (x + inset, y + inset, w - inset * 2, h - inset * 2)
```

### `plain` — Rounded corners + drop shadow, no chrome
```python
def draw_plain_frame(draw, img, x, y, w, h):
    # Shadow
    for i in range(4):
        alpha = 20 - i * 4
        draw.rounded_rectangle(
            [x + i, y + i + 2, x + w + i, y + h + i + 2],
            radius=8, fill=(0, 0, 0, alpha)
        )
    return (x, y, w, h)
```

## Embedding Static Images

```python
def embed_image_asset(img, asset_path, x, y, w, h, frame, start_delay, style="plain"):
    """Embed a static image into a slide frame with animation."""
    draw = ImageDraw.Draw(img)

    # Draw the frame mockup and get the inner content rect
    if style == "browser":
        cx, cy, cw, ch = draw_browser_frame(draw, img, x, y, w, h)
    elif style == "monitor":
        cx, cy, cw, ch = draw_monitor_frame(draw, img, x, y, w, h)
    elif style == "phone":
        cx, cy, cw, ch = draw_phone_frame(draw, img, x, y, w, h)
    else:
        cx, cy, cw, ch = (x, y, w, h)

    # Load and resize the asset image
    asset = Image.open(asset_path).convert("RGB")
    # Fit within content area, maintaining aspect ratio
    asset_ratio = asset.width / asset.height
    content_ratio = cw / ch
    if asset_ratio > content_ratio:
        new_w = cw
        new_h = int(cw / asset_ratio)
    else:
        new_h = ch
        new_w = int(ch * asset_ratio)
    asset = asset.resize((new_w, new_h), Image.LANCZOS)

    # Center within content area
    paste_x = cx + (cw - new_w) // 2
    paste_y = cy + (ch - new_h) // 2

    # Animate: fade in
    p = anim_progress(frame, int(start_delay * FPS), 20)
    if p > 0:
        img.paste(asset, (paste_x, paste_y))
```

## Embedding Video Clips

```python
def load_clip_frames(clip_path, target_fps=30):
    """Extract all frames from a video clip at target FPS."""
    cmd = [
        "ffmpeg", "-i", clip_path,
        "-vf", f"fps={target_fps}",
        "-f", "image2pipe", "-vcodec", "png", "-"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    frames = []
    buf = b""
    PNG_HEADER = b"\x89PNG\r\n\x1a\n"
    PNG_END = b"IEND\xaeB`\x82"

    while True:
        chunk = proc.stdout.read(65536)
        if not chunk:
            break
        buf += chunk
        while True:
            start = buf.find(PNG_HEADER)
            end = buf.find(PNG_END, start)
            if start == -1 or end == -1:
                break
            end += len(PNG_END)
            frame_data = buf[start:end]
            buf = buf[end:]
            frame_img = Image.open(BytesIO(frame_data)).convert("RGB")
            frames.append(frame_img)

    proc.wait()
    return frames


def get_clip_duration(clip_path):
    """Get duration of a video clip in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", clip_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def embed_video_asset(img, clip_frames, clip_frame_idx, x, y, w, h, style="plain"):
    """Embed a single frame from a video clip into the slide."""
    draw = ImageDraw.Draw(img)

    # Draw frame mockup
    if style == "browser":
        cx, cy, cw, ch = draw_browser_frame(draw, img, x, y, w, h)
    elif style == "terminal":
        cx, cy, cw, ch = draw_terminal_frame(draw, img, x, y, w, h)
    elif style == "monitor":
        cx, cy, cw, ch = draw_monitor_frame(draw, img, x, y, w, h)
    elif style == "phone":
        cx, cy, cw, ch = draw_phone_frame(draw, img, x, y, w, h)
    else:
        cx, cy, cw, ch = (x, y, w, h)

    # Get the right frame (hold last frame if clip is shorter than slide)
    idx = min(clip_frame_idx, len(clip_frames) - 1)
    frame = clip_frames[idx]

    # Resize to fit content area
    ratio = frame.width / frame.height
    content_ratio = cw / ch
    if ratio > content_ratio:
        new_w = cw
        new_h = int(cw / ratio)
    else:
        new_h = ch
        new_w = int(ch * ratio)
    frame = frame.resize((new_w, new_h), Image.LANCZOS)

    paste_x = cx + (cw - new_w) // 2
    paste_y = cy + (ch - new_h) // 2
    img.paste(frame, (paste_x, paste_y))
```

## Duration Calculation with Assets

When a slide has a video clip asset, the slide duration is:

```python
clip_duration = get_clip_duration(asset["path"])
narration_duration = len(narration_audio) / TTS_SAMPLE_RATE
slide_duration = max(clip_duration, narration_duration) + NARRATION_PADDING
```

This ensures the clip plays fully AND the narration completes.

## Slide Render Function with Asset

A slide function that embeds an asset follows this pattern:

```python
def slide_demo(frame, total_frames, asset=None):
    img = Image.new("RGB", (W, H), BLACK)
    draw = ImageDraw.Draw(img)

    # ... draw headline, accent bars, etc ...

    # Embed asset (positioned in the main content area)
    if asset:
        delay = 1.0  # seconds before asset appears
        if asset.get("type") == "video":
            # Calculate which clip frame to show
            clip_frame_idx = max(0, frame - int(delay * FPS))
            embed_video_asset(img, asset["frames"], clip_frame_idx,
                            x=200, y=250, w=1520, h=600, style=asset.get("style", "plain"))
        else:
            embed_image_asset(img, asset["path"],
                            x=200, y=250, w=1520, h=600,
                            frame=frame, start_delay=delay, style=asset.get("style", "plain"))

    draw_progress_bar(img, ...)
    return img
```

## Auto-mapping Logic

Claude auto-assigns assets to slides by:

1. **Filename matching**: `install-demo.mp4` → install/setup slide
2. **Content analysis**: Claude reads the image/frames and matches to slide topics
3. **Sequential fallback**: if no clear match, assets go in order on content slides
   (skipping title and closing slides)

The auto-mapping happens at **script generation time** (Claude decides), not at render time.

## Supported Formats

| Type | Formats | Notes |
|------|---------|-------|
| Images | PNG, JPG, WebP | Converted to RGB via Pillow |
| Videos | MP4, WebM, MOV | Frames extracted via ffmpeg |
| Animated | GIF | Treated as video (frames extracted) |

## Quality Checklist

- [ ] All assets load without errors (paths verified)
- [ ] Video clips play at correct speed (frame rate matched)
- [ ] Asset fits within mockup frame (no overflow)
- [ ] Aspect ratio preserved (no stretching)
- [ ] Narration describes or references the visual content shown
- [ ] Slide duration accommodates both the clip length and narration
- [ ] Frame mockup style matches the content (browser for web, terminal for CLI)
- [ ] Asset appears with animation (fade-in or similar), not instant pop
