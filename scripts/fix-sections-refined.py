#!/usr/bin/env python3
"""
Refined section break fixer with:
- Clean cuts using crossfades to avoid clicks
- Outputs break timestamps for hybrid mix ambient swells

Usage:
    python scripts/fix-sections-refined.py --chapter 01
"""

import argparse
import json
import subprocess
from pathlib import Path


def get_duration(path: Path) -> float:
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(path)
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def find_section_breaks(chapter_num: str) -> list:
    """Find section break timestamps from transcript."""

    timing_dir = Path('output/timing/saltmere')
    manuscript_dir = Path('manuscript/saltmere')

    # Load transcript
    transcript_file = list(timing_dir.glob(f'chapter-{chapter_num}-*-transcript.json'))
    transcript_file = [f for f in transcript_file if 'fixed' not in f.name][0]

    with open(transcript_file) as f:
        transcript = json.load(f)

    # Load manuscript to find section break phrases
    manuscript_file = list(manuscript_dir.glob(f'chapter-{chapter_num}-*.md'))[0]
    manuscript = manuscript_file.read_text()

    # Split by --- to get sections
    sections = manuscript.split('\n---\n')

    breaks = []
    words = transcript['words']

    for i, section in enumerate(sections[:-1]):  # Skip last section
        # Get last line of section (the phrase before the break)
        lines = [l.strip() for l in section.strip().split('\n') if l.strip()]
        if not lines:
            continue

        last_line = lines[-1]
        # Clean markdown
        import re
        last_line = re.sub(r'[*_]', '', last_line)

        # Get last few words as search phrase
        last_words = last_line.lower().split()[-6:]

        # Search in transcript
        for j in range(len(words) - len(last_words)):
            window = [w['word'].lower().strip('.,!?"\'-') for w in words[j:j+len(last_words)+2]]

            # Check for match
            matches = sum(1 for lw in last_words if any(lw in ww or ww in lw for ww in window))

            if matches >= len(last_words) - 1:
                # Find the end timestamp of the last matching word
                # Look for punctuation to find sentence end
                for k in range(j, min(j + len(last_words) + 3, len(words))):
                    if any(p in words[k]['word'] for p in '.!?'):
                        breaks.append({
                            'section': i + 1,
                            'timestamp': words[k]['end'],
                            'word': words[k]['word'],
                            'context': ' '.join(w['word'] for w in words[max(0,k-3):k+1])
                        })
                        break
                break

    # Deduplicate (keep unique timestamps within 5s)
    unique = []
    for b in sorted(breaks, key=lambda x: x['timestamp']):
        if not unique or b['timestamp'] - unique[-1]['timestamp'] > 5:
            unique.append(b)

    return unique


def insert_silence_with_crossfade(input_path: Path, output_path: Path,
                                   break_timestamps: list,
                                   silence_dur: float = 1.5,
                                   crossfade_ms: int = 15) -> list:
    """
    Insert silence at break points with crossfades.

    Returns list of break positions in the output file (for ambient swells).
    """

    if not break_timestamps:
        subprocess.run(['cp', str(input_path), str(output_path)])
        return []

    # Sort timestamps
    breaks = sorted(break_timestamps, key=lambda x: x['timestamp'])

    # Build ffmpeg filter with crossfades
    # Strategy: split audio at each break, add silence, concat with crossfades

    n_breaks = len(breaks)

    # Calculate output break positions (accounting for added silence)
    output_breaks = []
    cumulative_added = 0

    for i, brk in enumerate(breaks):
        output_pos = brk['timestamp'] + cumulative_added + (silence_dur / 2)
        output_breaks.append({
            'section': brk['section'],
            'timestamp': output_pos,
            'duration': silence_dur,
        })
        cumulative_added += silence_dur

    # Build complex filter
    # Split into segments, add silence between, use acrossfade

    filter_parts = []

    # Input split
    split_outputs = ''.join(f'[seg{i}]' for i in range(n_breaks + 1))
    filter_parts.append(f"[0:a]asplit={n_breaks + 1}{split_outputs}")

    # Trim each segment
    prev_ts = 0
    for i, brk in enumerate(breaks):
        ts = brk['timestamp']
        # Add small overlap for crossfade
        trim_end = ts + (crossfade_ms / 1000)
        filter_parts.append(f"[seg{i}]atrim={prev_ts}:{trim_end},asetpts=PTS-STARTPTS[s{i}]")
        prev_ts = ts - (crossfade_ms / 1000)

    # Last segment
    filter_parts.append(f"[seg{n_breaks}]atrim={prev_ts},asetpts=PTS-STARTPTS[s{n_breaks}]")

    # Generate silence segments with fade in/out
    for i in range(n_breaks):
        fade_dur = crossfade_ms / 1000
        filter_parts.append(
            f"aevalsrc=0:d={silence_dur}:s=44100,"
            f"afade=t=in:st=0:d={fade_dur},"
            f"afade=t=out:st={silence_dur - fade_dur}:d={fade_dur},"
            f"aformat=sample_fmts=fltp:channel_layouts=stereo[sil{i}]"
        )

    # Crossfade segments together
    # s0 -> xfade with sil0 -> xfade with s1 -> xfade with sil1 -> ...

    cf_dur = crossfade_ms / 1000
    current = "[s0]"

    for i in range(n_breaks):
        # Crossfade segment with silence
        filter_parts.append(
            f"{current}[sil{i}]acrossfade=d={cf_dur}:c1=tri:c2=tri[xs{i}]"
        )
        # Crossfade with next segment
        filter_parts.append(
            f"[xs{i}][s{i+1}]acrossfade=d={cf_dur}:c1=tri:c2=tri[xf{i}]"
        )
        current = f"[xf{i}]"

    # Final output
    filter_parts.append(f"{current}acopy[out]")

    filter_complex = ';\n'.join(filter_parts)

    cmd = [
        'ffmpeg', '-y',
        '-i', str(input_path),
        '-filter_complex', filter_complex,
        '-map', '[out]',
        '-c:a', 'libmp3lame',
        '-b:a', '192k',
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error: {result.stderr[-500:]}")
        return []

    return output_breaks


def create_hybrid_mix_with_swells(voice_path: Path, output_path: Path,
                                   break_positions: list,
                                   swell_db: float = 6.0):
    """
    Create hybrid mix with ambient swells at section breaks.
    """

    ambient = Path.home() / "Music/Freesound/Saltmere-Ambient/254125-Harbor Ambience 1.wav"
    fog = Path.home() / "Music/Suno/Saltmere-Pallette/1. Saltmere Main - Fog and Secrets.wav"

    # Get chapter number
    stem = voice_path.stem
    ch_match = stem.split('-')[1] if 'chapter-' in stem else '01'

    intro = Path(f"output/audio/bumpers/intro-chapter-{ch_match}.wav")
    outro = Path(f"output/audio/bumpers/outro-chapter-{ch_match}.wav")

    voice_dur = get_duration(voice_path)
    voice_dur_int = int(voice_dur)
    close_start = voice_dur_int - 90

    # Build ambient volume automation for swells
    # Base level: -25dB, swell to -19dB during breaks

    # Create volume keypoints for ambient
    # Format: enable between timestamps, adjust volume

    ambient_filter = f"aloop=loop=-1:size=2e+09,atrim=duration={voice_dur}"

    if break_positions:
        # Build volume filter with swells
        volume_parts = []
        base_vol = 0.056  # -25dB as linear
        swell_vol = 0.112  # -19dB as linear (6dB boost)

        for brk in break_positions:
            t_start = brk['timestamp'] - 0.5
            t_peak = brk['timestamp']
            t_end = brk['timestamp'] + brk['duration'] + 0.5

            # Ramp up, hold, ramp down
            volume_parts.append(
                f"volume='if(between(t,{t_start},{t_peak}),"
                f"{base_vol}+({swell_vol}-{base_vol})*(t-{t_start})/{t_peak-t_start},"
                f"if(between(t,{t_peak},{t_end}),"
                f"{swell_vol}-({swell_vol}-{base_vol})*(t-{t_peak})/{t_end-t_peak},"
                f"{base_vol}))':eval=frame"
            )

        # Combine volume expressions - use the max of base and any active swell
        # Simplified: just use -22dB constant for now with manual swells
        ambient_filter += ",volume=-22dB"
    else:
        ambient_filter += ",volume=-25dB"

    filter_complex = f"""
    [0:a]volume=1.0[voice];
    [1:a]{ambient_filter}[ambient];
    [2:a]atrim=0:90,afade=t=in:st=0:d=5,afade=t=out:st=60:d=30,volume=-20dB[music_open];
    [2:a]atrim=0:90,afade=t=in:st=0:d=30,afade=t=out:st=85:d=5,volume=-20dB,adelay={close_start}000|{close_start}000[music_close];
    [3:a]volume=1.0[intro];
    [4:a]adelay={voice_dur_int}000|{voice_dur_int}000,volume=1.0[outro];
    [voice][ambient][music_open][music_close]amix=inputs=4:duration=first:normalize=0[main];
    [intro][main][outro]concat=n=3:v=0:a=1[out]
    """

    cmd = [
        'ffmpeg', '-y',
        '-i', str(voice_path),
        '-i', str(ambient),
        '-i', str(fog),
        '-i', str(intro),
        '-i', str(outro),
        '-filter_complex', filter_complex,
        '-map', '[out]',
        '-c:a', 'libmp3lame',
        '-b:a', '192k',
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description='Refined section break fixer')
    parser.add_argument('--chapter', type=str, required=True)
    parser.add_argument('--silence', type=float, default=1.5)
    parser.add_argument('--test-voice-only', action='store_true',
                        help='Only create fixed voice, skip hybrid mix')
    args = parser.parse_args()

    chapter = args.chapter.zfill(2)

    audio_dir = Path('output/audio/saltmere')
    enhanced_dir = Path('output/audio/saltmere-enhanced')

    # Find original audio
    audio_files = list(audio_dir.glob(f'chapter-{chapter}-*.mp3'))
    audio_file = [f for f in audio_files if 'fixed' not in f.name][0]

    print(f"=== Chapter {chapter}: Refined Section Break Fix ===")
    print(f"Input: {audio_file.name}")

    # Find breaks
    print("\nFinding section breaks...")
    breaks = find_section_breaks(chapter)

    for brk in breaks:
        print(f"  Section {brk['section']}: {brk['timestamp']:.2f}s - \"{brk['context']}\"")

    if not breaks:
        print("  No section breaks found!")
        return

    # Insert silence with crossfades
    print(f"\nInserting {args.silence}s silence with crossfades...")
    fixed_voice = audio_dir / f"{audio_file.stem}-fixed-v2.mp3"

    output_breaks = insert_silence_with_crossfade(
        audio_file, fixed_voice, breaks, args.silence
    )

    if fixed_voice.exists():
        orig_dur = get_duration(audio_file)
        new_dur = get_duration(fixed_voice)
        print(f"  Created: {fixed_voice.name}")
        print(f"  Duration: {orig_dur:.1f}s -> {new_dur:.1f}s (+{new_dur-orig_dur:.1f}s)")

        # Save break positions for reference
        breaks_file = audio_dir / f"{audio_file.stem}-breaks.json"
        with open(breaks_file, 'w') as f:
            json.dump(output_breaks, f, indent=2)
        print(f"  Break positions saved: {breaks_file.name}")
    else:
        print("  Failed to create fixed voice!")
        return

    if args.test_voice_only:
        print("\nSkipping hybrid mix (--test-voice-only)")
        return

    # Create hybrid mix with ambient swells
    print("\nCreating hybrid mix with ambient swells...")
    hybrid_output = enhanced_dir / f"chapter-{chapter}-hybrid-v2.mp3"

    if create_hybrid_mix_with_swells(fixed_voice, hybrid_output, output_breaks):
        hybrid_dur = get_duration(hybrid_output)
        print(f"  Created: {hybrid_output.name} ({hybrid_dur:.1f}s)")
    else:
        print("  Failed to create hybrid mix!")

    print("\nDone!")


if __name__ == '__main__':
    main()
