# Saltmere Audio Timing Summary

**Generated:** 2026-01-10
**Status:** Section break compliance at 0%

---

## Overview

The ElevenLabs-generated narration reads through all manuscript section breaks (`---`) without adequate pauses. Section breaks should produce 1.5-2.0 second pauses to signal scene changes to the listener.

## Results by Chapter

| Chapter | Duration | Sections | Expected Breaks | Adequate Pauses | Compliance |
|---------|----------|----------|-----------------|-----------------|------------|
| 01 - The Research Station | 09:55 | 4 | 3 | 0 | 0% |
| 02 - The Harbor Master | 10:04 | 3 | 2 | 0 | 0% |
| 03 - First Samples | 11:29 | 3 | 2 | 0 | 0% |
| 04 - The Librarian's Archive | 11:52 | 3 | 2 | 0 | 0% |
| 05 - The Waterfront Discovery | 10:22 | 4 | 3 | 0 | 0% |
| 06 - The Weight of Truth | 11:07 | 3 | 2 | 0 | 0% |
| 07 - Eleanor's Warning | 11:54 | 2 | 1 | 0 | 0% |
| **Total** | **76:43** | **22** | **15** | **0** | **0%** |

## Root Cause

ElevenLabs TTS does not interpret markdown section separators (`---`) as pause markers. The narrator treats them as continuation points rather than scene breaks.

## Recommended Solutions

### Option 1: Post-Production Silence Insertion (Recommended)

Use the timing reports (`*-report.md`) to identify edit points. Insert 1.5-2.0s silence at each marked timestamp using:

```bash
# Example ffmpeg command to insert silence
ffmpeg -i input.mp3 \
  -af "asplit[a][b]; \
       [a]atrim=0:174.1[head]; \
       [b]atrim=174.1[tail]; \
       aevalsrc=0:d=1.5[silence]; \
       [head][silence][tail]concat=n=3:v=0:a=1" \
  output.mp3
```

### Option 2: Re-generate with Explicit Pause Markers

Modify the TTS pipeline to insert pause markup:
- ElevenLabs supports `<break time="1.5s"/>` in SSML mode
- Split manuscripts at section breaks before sending to TTS
- Insert silence between chunks

### Option 3: Hybrid Mix Adjustments

The hybrid mixes already have music/ambient at structural points. Consider:
- Extending crossfade durations at section boundaries
- Adding ambient swell at section breaks
- Using the timing data to automate mix decisions

## Files Generated

```
output/timing/saltmere/
├── manuscript-summary.json      # Section counts per chapter
├── chapter-01-*-sections.json   # Manuscript section data
├── chapter-01-*-transcript.json # Whisper transcription
├── chapter-01-*-timing.json     # Aligned timing metadata
├── chapter-01-*-report.md       # Human-readable edit points
└── TIMING-SUMMARY.md            # This summary
```

## Pipeline Commands

```bash
# Parse manuscript sections
python scripts/parse-manuscript-sections.py --all

# Transcribe audio (requires whisper)
python scripts/transcribe-audio.py --all

# Align timing data
python scripts/align-timing.py --all

# Generate reports
python scripts/timing-report.py --all
```

## Next Steps

1. Choose a solution approach (post-production vs re-generation)
2. Apply fixes to Chapter 1 as test case
3. Verify listener experience improves
4. Apply to remaining chapters
5. Update production pipeline to prevent future issues
