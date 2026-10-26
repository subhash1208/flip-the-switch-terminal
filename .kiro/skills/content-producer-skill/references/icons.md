# Icon Reference for Video Producer

This reference covers how to find, install, and use open-source SVG icon sets with the
video producer skill. Icons are supersampled at high density via ImageMagick (`magick`),
LANCZOS-downscaled in Pillow for crisp edges, and recolored. See SKILL.md for why the old
one-shot `ffmpeg -vf scale` approach is avoided (it upscales from the SVG's tiny intrinsic
size, producing blurry icons).

## Recommended Icon Libraries

### 1. Lucide (Recommended Default)

- **Website**: https://lucide.dev
- **GitHub**: https://github.com/lucide-icons/lucide
- **Icons**: 1,500+ clean, consistent SVG icons
- **License**: ISC (permissive, commercial use OK)
- **Style**: Clean, minimal, 24x24 base with consistent 2px stroke

**Setup:**
```bash
# Clone into project directory
git clone https://github.com/lucide-icons/lucide.git
# Icons are at: lucide/icons/*.svg
```

**Usage in script:**
```python
ICON_DIR = os.path.join(SCRIPT_DIR, "lucide/icons")
```

**Search for icons:**
```bash
ls lucide/icons/*cloud*.svg
ls lucide/icons/*music*.svg
ls lucide/icons/*shield*.svg
```

### 2. Tabler Icons

- **Website**: https://tabler.io/icons
- **GitHub**: https://github.com/tabler/tabler-icons
- **Icons**: 5,000+ SVG icons in two styles (outline, filled)
- **License**: MIT
- **Style**: Consistent 24x24, configurable stroke width

**Setup:**
```bash
git clone https://github.com/tabler/tabler-icons.git
# Outline icons: tabler-icons/icons/outline/*.svg
# Filled icons: tabler-icons/icons/filled/*.svg
```

### 3. Feather Icons

- **Website**: https://feathericons.com
- **GitHub**: https://github.com/feathericons/feather
- **Icons**: 280+ beautiful, minimal SVG icons
- **License**: MIT
- **Style**: Simple, elegant, 24x24 with 2px stroke

**Setup:**
```bash
git clone https://github.com/feathericons/feather.git
# Icons are at: feather/icons/*.svg
```

### 4. Heroicons

- **Website**: https://heroicons.com
- **GitHub**: https://github.com/tailwindlabs/heroicons
- **Icons**: 300+ icons in outline, solid, and mini styles
- **License**: MIT
- **Style**: Tailwind-friendly, 24x24

**Setup:**
```bash
git clone https://github.com/tailwindlabs/heroicons.git
# Outline: heroicons/src/24/outline/*.jsx (SVG content inside)
# Solid: heroicons/src/24/solid/*.jsx
# Optimized SVGs: heroicons/optimized/24/outline/*.svg
```

### 5. Phosphor Icons

- **Website**: https://phosphoricons.com
- **GitHub**: https://github.com/phosphor-icons/core
- **Icons**: 1,200+ icons in 6 weights (thin, light, regular, bold, fill, duotone)
- **License**: MIT
- **Style**: Flexible weight system, 256x256 viewBox

**Setup:**
```bash
git clone https://github.com/phosphor-icons/core.git
# Icons: core/assets/regular/*.svg
# Bold: core/assets/bold/*.svg
```

## Icon Loading Function

The same `load_icon()` function works with any SVG icon set. Just update `ICON_DIR`:

```python
ICON_DIR = os.path.join(SCRIPT_DIR, "lucide/icons")  # or your chosen set
_icon_cache = {}

def load_icon(name, size=96, color=WHITE):
    key = (name, size, color)
    if key in _icon_cache:
        return _icon_cache[key]

    svg_path = os.path.join(ICON_DIR, f"{name}.svg")
    if not os.path.exists(svg_path):
        # Try common alternative paths
        for alt_dir in ["outline", "solid", "regular"]:
            alt_path = os.path.join(ICON_DIR, "..", alt_dir, f"{name}.svg")
            if os.path.exists(alt_path):
                svg_path = alt_path
                break
        else:
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            _icon_cache[key] = img
            return img

    # Supersample at high density via ImageMagick, then LANCZOS-downscale → crisp edges.
    # Never feed the SVG to ffmpeg at the target size: it rasterizes at the SVG's intrinsic
    # (often 24x24) size and upscales, producing blurry icons.
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
        # Fallback: ffmpeg high-density raster (still supersampled, not a one-shot scale)
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", svg_path,
            "-vf", f"scale={ss}:{ss}:flags=lanczos",
            "-f", "image2pipe", "-vcodec", "png", "-",
        ]
        result = subprocess.run(cmd, capture_output=True)
    img = Image.open(BytesIO(result.stdout)).convert("RGBA").resize((size, size), Image.LANCZOS)

    # Recolor all non-transparent pixels
    pixels = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]
            if a > 0:
                pixels[x, y] = (color[0], color[1], color[2], a)

    _icon_cache[key] = img
    return img
```

## Common Icon Names by Topic

Icon names vary between sets. **Always list the directory** before using an icon.

### General / Universal
| Concept | Lucide | Tabler | Feather |
|---------|--------|--------|---------|
| Search | `search` | `search` | `search` |
| Settings | `settings` | `settings` | `settings` |
| Home | `home` | `home` | `home` |
| User | `user` | `user` | `user` |
| Mail | `mail` | `mail` | `mail` |
| Calendar | `calendar` | `calendar` | `calendar` |
| Clock | `clock` | `clock` | `clock` |
| Check | `check` | `check` | `check` |
| X / Close | `x` | `x` | `x` |
| Alert | `alert-triangle` | `alert-triangle` | `alert-triangle` |
| Info | `info` | `info-circle` | `info` |

### Tech / Development
| Concept | Lucide | Tabler | Feather |
|---------|--------|--------|---------|
| Code | `code` | `code` | `code` |
| Terminal | `terminal` | `terminal` | `terminal` |
| Database | `database` | `database` | `database` |
| Server | `server` | `server` | `server` |
| Cloud | `cloud` | `cloud` | `cloud` |
| Shield | `shield` | `shield` | `shield` |
| Lock | `lock` | `lock` | `lock` |
| Git Branch | `git-branch` | `git-branch` | `git-branch` |
| CPU | `cpu` | `cpu` | `cpu` |
| Network | `network` | `network` | `wifi` |

### Music / Events / Concerts
| Concept | Lucide | Tabler | Feather |
|---------|--------|--------|---------|
| Music | `music` | `music` | `music` |
| Headphones | `headphones` | `headphones` | `headphones` |
| Mic | `mic` | `microphone` | `mic` |
| Speaker | `speaker` | `speaker` | `speaker` |
| Ticket | `ticket` | `ticket` | `n/a` |
| Star | `star` | `star` | `star` |
| Heart | `heart` | `heart` | `heart` |
| Camera | `camera` | `camera` | `camera` |
| Video | `video` | `video` | `video` |
| Map Pin | `map-pin` | `map-pin` | `map-pin` |

### Business / Product
| Concept | Lucide | Tabler | Feather |
|---------|--------|--------|---------|
| Trending Up | `trending-up` | `trending-up` | `trending-up` |
| Bar Chart | `bar-chart-3` | `chart-bar` | `bar-chart-2` |
| Dollar | `dollar-sign` | `currency-dollar` | `dollar-sign` |
| Rocket | `rocket` | `rocket` | `n/a` |
| Target | `target` | `target` | `target` |
| Award | `award` | `award` | `award` |
| Zap | `zap` | `bolt` | `zap` |
| Package | `package` | `package` | `package` |

## Tips

- **Don't guess icon names** — always list the directory first:
  ```bash
  ls lucide/icons/*.svg | head -30
  ls lucide/icons/*key-word*.svg
  ```
- **Cache loaded icons** — the `load_icon()` function includes caching by default
- **Icon sizes**: 36-48px inline, 64-80px for cards, 96-180px for hero placement
- **Recoloring**: The load function recolors all non-transparent pixels to the target color
- Some icon sets use different viewBox sizes — ffmpeg handles scaling automatically
- If an icon renders poorly at small sizes, try a simpler icon from the same set
