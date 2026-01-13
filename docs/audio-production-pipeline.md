# Audio Production Pipeline

## Overview

The Saltmere Chronicles audiobook production has three main stages:
1. **Raw narration** - TTS-generated voice-only audio
2. **Hybrid mix** - Narration + ambient bed + music + section breaks
3. **Final chapter** - Hybrid mix + intro/outro bumpers

## Directory Structure

```
output/audio/
├── saltmere/                    # Raw TTS narration files
│   ├── chapter-01-the-research-station.mp3
│   └── chapter-*-fixed*.mp3     # Old versions with inserted silence
│
├── saltmere-enhanced/           # Hybrid mixes (narration + ambient + music)
│   ├── chapter-01-hybrid-v10.mp3  # Current version (correct section breaks)
│   ├── chapter-01-hybrid-v9.mp3   # Previous version
│   └── ...
│
├── bumpers/                     # Plain intro/outro bumpers (no titles)
│   ├── intro-chapter-01.wav
│   └── outro-chapter-01.wav
│
└── bumpers-with-titles/         # Intro bumpers with spoken chapter titles
    └── intro-chapter-01.wav

site/audio/saltmere-chronicles/  # Final deployed chapter files
└── 01 - The Research Station.mp3
```

## Key Files

### Configuration
- `site/public/js/audio-structure.json` - Timing calibration for word-highlight sync
  - `raw_duration` - Duration of raw TTS narration
  - `intro_duration` - Duration of intro bumper (typically 24s)
  - `section_breaks` - Positions where foghorn sounds are inserted
  - `final_duration` - Total duration of final chapter file

### Source Audio (in ~/Music/)
- `Freesound/Saltmere-Ambient/507471-Long Distant Foghorn.aiff.aiff` - Section break sound
- `Freesound/Saltmere-Ambient/254125-Harbor Ambience 1.wav` - Ambient bed
- `Suno/Saltmere-Pallette/1. Saltmere Main - Fog and Secrets.wav` - Music bed

## Scripts

### `scripts/rebuild-with-correct-breaks.py`
Creates hybrid-v10 files with foghorn sounds at correct section break positions.

```bash
# Dry run to see what would happen
python scripts/rebuild-with-correct-breaks.py --all --dry-run

# Rebuild single chapter
python scripts/rebuild-with-correct-breaks.py --chapter 1

# Rebuild all chapters
python scripts/rebuild-with-correct-breaks.py --all
```

**What it does:**
1. Takes raw narration from `output/audio/saltmere/`
2. Reads section break positions from `audio-structure.json`
3. Inserts foghorn sound at each break position
4. Mixes with ambient bed (looped, -24dB)
5. Adds music (fade in at start, fade out at end)
6. Outputs to `output/audio/saltmere-enhanced/chapter-XX-hybrid-v10.mp3`

### `scripts/reassemble-chapters.py`
Creates final chapter files by adding intro/outro bumpers to hybrid mix.

```bash
# Dry run
python scripts/reassemble-chapters.py --dry-run

# Reassemble all chapters
python scripts/reassemble-chapters.py

# Reassemble single chapter
python scripts/reassemble-chapters.py --chapter 1
```

**What it does:**
1. Finds best hybrid file (prefers v10, falls back to v9, v8, etc.)
2. Concatenates: intro bumper + hybrid mix + outro bumper
3. Outputs to `site/audio/saltmere-chronicles/`

## Section Break Positions

Section breaks mark narrative scene transitions (represented by `<hr>` in HTML).
The correct positions are derived from word timing data, not manuscript text matching.

To recalculate section break positions:
1. HTML pages have `<hr>` elements at scene transitions
2. Each `<hr>` follows a word span with a `data-i` attribute
3. Look up that word index in the words JSON to get the timestamp

The positions in `audio-structure.json` should match where foghorn sounds
are actually inserted in the hybrid audio files.

## Timing Calibration

The word-highlight system uses `audio-structure.json` to convert raw
transcript timestamps to final audio time:

```
final_time = raw_time + intro_duration + cumulative_break_duration
```

Where `cumulative_break_duration` is the sum of all section break durations
that occur before the current timestamp.

## Fixing Foghorn Timing

If foghorns play at wrong times:

1. **Update section break positions** in `audio-structure.json`
   - Positions should match actual `<hr>` locations in HTML
   - Can calculate from word timing JSON files

2. **Rebuild hybrid files** with correct positions:
   ```bash
   python scripts/rebuild-with-correct-breaks.py --all
   ```

3. **Reassemble final chapters**:
   ```bash
   python scripts/reassemble-chapters.py
   ```

4. **Update final_duration** values in `audio-structure.json`

## Version History

- **v10** - Correct section break positions (2026-01-13)
- **v9** - Previous production version
- **v8, v7** - Earlier iterations
