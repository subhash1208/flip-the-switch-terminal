# Dynamic Music Generation Reference

This reference defines a configurable music generation system that produces different
soundscapes based on the mood, energy, and content type of the video. All music is
synthesized procedurally with numpy — no external audio files needed.

## Architecture

```python
SAMPLE_RATE = 44100

def generate_music(duration, mood="ambient", bpm=100, key="Am", energy=0.5):
    """Generate background music matching the specified mood."""
    ...
```

The system is built on three pillars:
1. **Mood presets** — define which layers and chord progressions to use
2. **Energy level** (0.0–1.0) — controls how many layers are active and their intensity
3. **Chord progressions** — different harmonic feels for different emotions

## Note Frequencies

```python
# Octave 2 (low bass)
C2, D2, E2, F2, G2, A2, B2 = 65.41, 73.42, 82.41, 87.31, 98.00, 110.00, 123.47

# Octave 3 (bass / low mid)
C3, D3, E3, F3, G3, A3, B3 = 130.81, 146.83, 164.81, 174.61, 196.00, 220.00, 246.94

# Octave 4 (mid)
C4, D4, E4, F4, G4, A4, B4 = 261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88

# Octave 5 (high)
C5, D5, E5, F5, G5, A5 = 523.25, 587.33, 659.26, 698.46, 783.99, 880.00
```

## Mood Presets

### 1. `upbeat` — Tech Demo Videos
- **BPM**: 108–115
- **Key**: C major
- **Feel**: Confident, forward-moving, professional
- **Chord progression**: C – G – Am – F (the "pop" progression)
- **Layers**: Kick (half-time), hi-hat (8ths), sub-bass, pads, arpeggio, pluck accents
- **Energy**: 0.6–0.8

```python
UPBEAT = {
    "bpm": 112,
    "chords": [
        {"notes": [C4, E4, G4], "bass": C3},   # C major
        {"notes": [G3, B3, D4], "bass": G2},    # G major
        {"notes": [A3, C4, E4], "bass": A2},    # A minor
        {"notes": [F3, A3, C4], "bass": F2},    # F major
    ],
    "arp_notes": [C4, E4, G4, C5, G4, E4],
    "layers": ["pad", "sub_bass", "arp", "kick", "hihat", "pluck"],
    "energy": 0.7,
}
```

### 2. `ambient` — Explainer Videos
- **BPM**: 90–100
- **Key**: A minor
- **Feel**: Thoughtful, open, contemplative
- **Chord progression**: Am – Em – F – G (natural minor feel)
- **Layers**: Pads only, very gentle arpeggio, no percussion
- **Energy**: 0.3–0.4

```python
AMBIENT = {
    "bpm": 94,
    "chords": [
        {"notes": [A3, C4, E4], "bass": A2},    # Am
        {"notes": [E3, G3, B3], "bass": E2},     # Em
        {"notes": [F3, A3, C4], "bass": F2},     # F
        {"notes": [G3, B3, D4], "bass": G2},     # G
    ],
    "arp_notes": [A3, C4, E4, A4, E4, C4],
    "layers": ["pad", "sub_bass", "arp"],
    "energy": 0.35,
}
```

### 3. `energetic` — Promo Videos
- **BPM**: 122–130
- **Key**: E minor
- **Feel**: Exciting, driving, urgent
- **Chord progression**: Em – G – D – A (minor-to-major energy)
- **Layers**: Four-on-the-floor kick, active hi-hat with open hat, heavy sub-bass,
  bright arpeggio, pads, pluck accents, shaker
- **Energy**: 0.8–1.0

```python
ENERGETIC = {
    "bpm": 126,
    "chords": [
        {"notes": [E3, G3, B3], "bass": E2},     # Em
        {"notes": [G3, B3, D4], "bass": G2},      # G
        {"notes": [D3, F3+1, A3], "bass": D2},    # D (F# = F3 * 2^(1/12))
        {"notes": [A3, C4+1, E4], "bass": A2},    # A (C# = C4 * 2^(1/12))
    ],
    "arp_notes": [E4, G4, B4, E5, B4, G4],
    "layers": ["pad", "sub_bass", "arp", "kick_four", "hihat_active", "pluck", "shaker"],
    "energy": 0.85,
}
```

### 4. `calm` — Tutorial Videos
- **BPM**: 84–92
- **Key**: D major
- **Feel**: Relaxed, focused, non-distracting
- **Chord progression**: D – A – Bm – G (warm, gentle)
- **Layers**: Soft pads, barely-there arpeggio, no percussion at all
- **Energy**: 0.2–0.3

```python
CALM = {
    "bpm": 88,
    "chords": [
        {"notes": [D3, F3s, A3], "bass": D2},    # D major (F#3)
        {"notes": [A3, C4s, E4], "bass": A2},     # A major (C#4)
        {"notes": [B3, D4, F4s], "bass": B2},     # Bm (F#4)
        {"notes": [G3, B3, D4], "bass": G2},      # G major
    ],
    "arp_notes": [D4, F4s, A4, D5, A4, F4s],
    "layers": ["pad", "sub_bass"],
    "energy": 0.25,
}
```

### 5. `cinematic` — Showcase Videos
- **BPM**: 100–110
- **Key**: C major
- **Feel**: Uplifting, emotional, building
- **Chord progression**: C – Am – F – G (classic cinematic)
- **Layers**: Wide pads, gentle kick (half-time), swelling dynamics,
  arpeggio that builds over time
- **Energy**: 0.5 → 0.8 (builds over the video duration)

```python
CINEMATIC = {
    "bpm": 104,
    "chords": [
        {"notes": [C4, E4, G4], "bass": C3},     # C
        {"notes": [A3, C4, E4], "bass": A2},      # Am
        {"notes": [F3, A3, C4], "bass": F2},      # F
        {"notes": [G3, B3, D4], "bass": G2},      # G
    ],
    "arp_notes": [C4, E4, G4, C5, G4, E4],
    "layers": ["pad_wide", "sub_bass", "arp", "kick_gentle"],
    "energy_curve": "build",  # energy increases over time
}
```

### 6. `dark` — Problem/Warning Focused Videos
- **BPM**: 95–105
- **Key**: D minor
- **Feel**: Serious, tension, weight
- **Chord progression**: Dm – Bb – Gm – A (minor, unresolved)
- **Layers**: Dark pads, low rumble, no arpeggio, sparse percussion
- **Energy**: 0.4–0.5

```python
DARK = {
    "bpm": 98,
    "chords": [
        {"notes": [D3, F3, A3], "bass": D2},      # Dm
        {"notes": [Bb2, D3, F3], "bass": Bb1},     # Bb
        {"notes": [G3, Bb3, D4], "bass": G2},      # Gm
        {"notes": [A3, C4s, E4], "bass": A2},      # A major (creates tension)
    ],
    "arp_notes": [D3, F3, A3, D4, A3, F3],
    "layers": ["pad_dark", "sub_bass", "rumble"],
    "energy": 0.45,
}
```

### 7. `lofi` — Casual/Informal Videos
- **BPM**: 75–85
- **Key**: F major
- **Feel**: Warm, chill, slightly nostalgic
- **Chord progression**: Fmaj7 – Em7 – Dm7 – Cmaj7 (jazzy descent)
- **Layers**: Warm pads, gentle vinyl crackle texture, soft kick, mellow arp
- **Energy**: 0.3–0.5

```python
LOFI = {
    "bpm": 80,
    "chords": [
        {"notes": [F3, A3, C4, E4], "bass": F2},    # Fmaj7
        {"notes": [E3, G3, B3, D4], "bass": E2},     # Em7
        {"notes": [D3, F3, A3, C4], "bass": D2},     # Dm7
        {"notes": [C3, E3, G3, B3], "bass": C2},     # Cmaj7
    ],
    "arp_notes": [F3, A3, C4, E4, C4, A3],
    "layers": ["pad_warm", "sub_bass", "arp_mellow", "kick_soft", "crackle"],
    "energy": 0.4,
}
```

## Content Type → Mood Mapping

| Content Type | Default Mood | BPM Range | Energy |
|-------------|-------------|-----------|--------|
| **demo** | `upbeat` | 108–115 | 0.6–0.8 |
| **explainer** | `ambient` | 90–100 | 0.3–0.4 |
| **promo** | `energetic` | 122–130 | 0.8–1.0 |
| **tutorial** | `calm` | 84–92 | 0.2–0.3 |
| **showcase** | `cinematic` | 100–110 | 0.5→0.8 |

The user can override the mood explicitly:
```
Create a tutorial video with a lofi music vibe
```

## Layer Implementations

### Pad Chords (all moods)

Sustained, smooth chords using detuned sine pairs for width:

```python
def layer_pad(mix, chords, beat, duration, sr, energy=0.5, warmth=1.0):
    beats_per_chord = 4
    chord_dur = beat * beats_per_chord
    for i in range(int(duration / chord_dur) + 1):
        chord = chords[i % len(chords)]
        start = int(i * chord_dur * sr)
        end = min(start + int(chord_dur * sr), len(mix))
        seg_t = np.arange(end - start) / sr
        for freq in chord["notes"]:
            # Detuned pair for stereo width
            detune = 1.002 + 0.002 * warmth
            mix[start:end] += energy * 0.08 * np.sin(2 * np.pi * freq * detune * seg_t)
            mix[start:end] += energy * 0.08 * np.sin(2 * np.pi * freq / detune * seg_t)
```

### Wide Pad (cinematic — extra detuning + octave doubling)

```python
def layer_pad_wide(mix, chords, beat, duration, sr, energy=0.5):
    # Same as pad but with more detuning and an octave-up layer
    beats_per_chord = 4
    chord_dur = beat * beats_per_chord
    for i in range(int(duration / chord_dur) + 1):
        chord = chords[i % len(chords)]
        start = int(i * chord_dur * sr)
        end = min(start + int(chord_dur * sr), len(mix))
        seg_t = np.arange(end - start) / sr
        for freq in chord["notes"]:
            mix[start:end] += energy * 0.06 * np.sin(2 * np.pi * freq * 1.004 * seg_t)
            mix[start:end] += energy * 0.06 * np.sin(2 * np.pi * freq * 0.996 * seg_t)
            # Octave up, quieter
            mix[start:end] += energy * 0.02 * np.sin(2 * np.pi * freq * 2.0 * seg_t)
```

### Sub Bass

```python
def layer_sub_bass(mix, chords, beat, duration, sr, energy=0.5):
    beats_per_chord = 4
    chord_dur = beat * beats_per_chord
    for i in range(int(duration / chord_dur) + 1):
        chord = chords[i % len(chords)]
        bass_freq = chord["bass"]
        start = int(i * chord_dur * sr)
        end = min(start + int(chord_dur * sr), len(mix))
        seg_t = np.arange(end - start) / sr
        env = np.exp(-seg_t * 0.3)  # gentle decay
        mix[start:end] += energy * 0.15 * np.sin(2 * np.pi * bass_freq * seg_t) * env
        # Octave harmonic for definition
        mix[start:end] += energy * 0.04 * np.sin(2 * np.pi * bass_freq * 2 * seg_t) * env
```

### Arpeggio

```python
def layer_arp(mix, arp_notes, beat, duration, sr, energy=0.5, speed=0.5):
    """speed: beats per arp note (0.5 = 8th notes, 0.25 = 16th notes)"""
    note_dur = beat * speed
    for i in range(int(duration / note_dur) + 1):
        note = arp_notes[i % len(arp_notes)]
        start = int(i * note_dur * sr)
        length = int(note_dur * sr * 0.7)  # slight gap between notes
        end = min(start + length, len(mix))
        seg_t = np.arange(end - start) / sr
        env = np.exp(-seg_t * 4.0)  # plucky decay
        mix[start:end] += energy * 0.05 * np.sin(2 * np.pi * note * seg_t) * env
```

### Mellow Arpeggio (lofi — softer attack, slower decay)

```python
def layer_arp_mellow(mix, arp_notes, beat, duration, sr, energy=0.5):
    note_dur = beat * 0.75  # dotted 8th feel
    for i in range(int(duration / note_dur) + 1):
        note = arp_notes[i % len(arp_notes)]
        start = int(i * note_dur * sr)
        length = int(note_dur * sr * 0.9)
        end = min(start + length, len(mix))
        seg_t = np.arange(end - start) / sr
        # Soft attack + slow decay
        attack = np.clip(seg_t * 20, 0, 1)
        decay = np.exp(-seg_t * 2.0)
        env = attack * decay
        mix[start:end] += energy * 0.04 * np.sin(2 * np.pi * note * seg_t) * env
```

### Kick Drum (half-time — beats 1 and 3)

```python
def layer_kick(mix, beat, duration, sr, energy=0.5):
    for i in range(int(duration / (beat * 2)) + 1):
        start = int(i * beat * 2 * sr)
        length = int(0.15 * sr)
        end = min(start + length, len(mix))
        seg_t = np.arange(end - start) / sr
        # Pitch drop from 150Hz to 50Hz
        freq = 150 * np.exp(-seg_t * 30) + 50
        phase = np.cumsum(freq / sr) * 2 * np.pi
        env = np.exp(-seg_t * 20)
        mix[start:end] += energy * 0.25 * np.sin(phase) * env
```

### Kick Four-on-the-floor (energetic — every beat)

```python
def layer_kick_four(mix, beat, duration, sr, energy=0.5):
    for i in range(int(duration / beat) + 1):
        start = int(i * beat * sr)
        length = int(0.12 * sr)
        end = min(start + length, len(mix))
        seg_t = np.arange(end - start) / sr
        freq = 160 * np.exp(-seg_t * 35) + 45
        phase = np.cumsum(freq / sr) * 2 * np.pi
        env = np.exp(-seg_t * 22)
        mix[start:end] += energy * 0.30 * np.sin(phase) * env
```

### Gentle Kick (cinematic — soft, felt not heard)

```python
def layer_kick_gentle(mix, beat, duration, sr, energy=0.5):
    for i in range(int(duration / (beat * 2)) + 1):
        start = int(i * beat * 2 * sr)
        length = int(0.2 * sr)
        end = min(start + length, len(mix))
        seg_t = np.arange(end - start) / sr
        freq = 100 * np.exp(-seg_t * 20) + 40
        phase = np.cumsum(freq / sr) * 2 * np.pi
        env = np.exp(-seg_t * 15)
        mix[start:end] += energy * 0.15 * np.sin(phase) * env
```

### Hi-Hat (standard 8th notes)

```python
def layer_hihat(mix, beat, duration, sr, energy=0.5):
    for i in range(int(duration / (beat * 0.5)) + 1):
        start = int(i * beat * 0.5 * sr)
        length = int(0.03 * sr)
        end = min(start + length, len(mix))
        seg_t = np.arange(end - start) / sr
        env = np.exp(-seg_t * 100)
        # Velocity variation for humanization
        velocity = 0.6 + 0.4 * (i % 2)  # alternating loud/soft
        noise = np.random.randn(end - start) * 0.03
        mix[start:end] += energy * velocity * noise * env
```

### Active Hi-Hat (energetic — with open hat accents)

```python
def layer_hihat_active(mix, beat, duration, sr, energy=0.5):
    for i in range(int(duration / (beat * 0.25)) + 1):  # 16th notes
        start = int(i * beat * 0.25 * sr)
        is_open = (i % 8 == 3) or (i % 8 == 7)  # open hat on off-beats
        decay_rate = 40 if is_open else 120
        length = int((0.08 if is_open else 0.025) * sr)
        end = min(start + length, len(mix))
        seg_t = np.arange(end - start) / sr
        env = np.exp(-seg_t * decay_rate)
        velocity = 0.5 + 0.5 * ((i % 4 == 0) or is_open)
        noise = np.random.randn(end - start) * 0.025
        mix[start:end] += energy * velocity * noise * env
```

### Pluck Accents (at section boundaries)

```python
def layer_pluck(mix, chords, beat, duration, sr, energy=0.5):
    """Play pluck accent on the first beat of each chord change."""
    beats_per_chord = 4
    chord_dur = beat * beats_per_chord
    for i in range(int(duration / chord_dur) + 1):
        chord = chords[i % len(chords)]
        root = chord["notes"][0]
        start = int(i * chord_dur * sr)
        length = int(0.3 * sr)
        end = min(start + length, len(mix))
        seg_t = np.arange(end - start) / sr
        env = np.exp(-seg_t * 8)
        mix[start:end] += energy * 0.08 * np.sin(2 * np.pi * root * 2 * seg_t) * env
```

### Shaker Texture (light 16th note noise)

```python
def layer_shaker(mix, beat, duration, sr, energy=0.5):
    for i in range(int(duration / (beat * 0.25)) + 1):
        start = int(i * beat * 0.25 * sr)
        length = int(0.015 * sr)
        end = min(start + length, len(mix))
        seg_t = np.arange(end - start) / sr
        env = np.exp(-seg_t * 200)
        noise = np.random.randn(end - start) * 0.008
        mix[start:end] += energy * noise * env
```

### Low Rumble (dark — sub-frequency tension)

```python
def layer_rumble(mix, chords, beat, duration, sr, energy=0.5):
    beats_per_chord = 4
    chord_dur = beat * beats_per_chord
    for i in range(int(duration / chord_dur) + 1):
        chord = chords[i % len(chords)]
        bass = chord["bass"]
        start = int(i * chord_dur * sr)
        end = min(start + int(chord_dur * sr), len(mix))
        seg_t = np.arange(end - start) / sr
        # Very low sine with slow LFO modulation
        lfo = 1.0 + 0.3 * np.sin(2 * np.pi * 0.2 * seg_t)
        mix[start:end] += energy * 0.08 * np.sin(2 * np.pi * bass * 0.5 * seg_t) * lfo
```

### Vinyl Crackle (lofi texture)

```python
def layer_crackle(mix, duration, sr, energy=0.5):
    total_samples = int(duration * sr)
    # Sparse random clicks
    crackle = np.zeros(total_samples)
    n_clicks = int(duration * 15)  # ~15 clicks per second
    positions = np.random.randint(0, total_samples, n_clicks)
    for pos in positions:
        length = min(int(0.001 * sr), total_samples - pos)
        if length > 0:
            crackle[pos:pos + length] = np.random.randn(length) * 0.003
    mix[:total_samples] += energy * crackle
```

## Dynamic Energy Curves

For moods like `cinematic`, energy builds over the video duration:

```python
def get_energy(base_energy, t, duration, curve="flat"):
    """Return energy level at time t."""
    progress = t / duration
    if curve == "flat":
        return base_energy
    elif curve == "build":
        return base_energy * (0.5 + 0.5 * progress)  # starts at 50%, builds to 100%
    elif curve == "fade":
        return base_energy * (1.0 - 0.5 * progress)  # starts full, fades to 50%
    elif curve == "arc":
        # Peaks at 70% through, then settles
        return base_energy * (0.6 + 0.4 * math.sin(progress * math.pi * 0.9))
```

## Global Processing

### Fade In/Out

```python
fade_samples = int(2.0 * sr)
mix[:fade_samples] *= np.linspace(0, 1, fade_samples)
mix[-fade_samples:] *= np.linspace(1, 0, fade_samples)
```

### Normalization and Volume

```python
peak = np.max(np.abs(mix))
if peak > 0:
    mix = mix / peak
mix *= 0.22  # Final volume — subtle background
```

### Volume by Mood

| Mood | Volume | Rationale |
|------|--------|-----------|
| `calm` | 0.15 | Barely there — viewer is learning |
| `ambient` | 0.18 | Present but unobtrusive |
| `lofi` | 0.20 | Warm presence |
| `cinematic` | 0.22 | Emotional but not distracting |
| `upbeat` | 0.22 | Confident presence |
| `energetic` | 0.25 | Felt, not overwhelming |
| `dark` | 0.20 | Tension without distraction |

## Usage in Generated Scripts

```python
# The music mood is set based on the content type template
MUSIC_MOOD = "calm"  # Set by template: demo→upbeat, explainer→ambient, etc.

# Or override explicitly
MUSIC_MOOD = "lofi"  # User requested a specific vibe

# Generate
music = generate_music(duration_seconds, mood=MUSIC_MOOD)
```
