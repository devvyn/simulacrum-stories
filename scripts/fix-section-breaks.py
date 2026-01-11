#!/usr/bin/env python3
"""
Fix section breaks by inserting silence at break points.

Analyzes transcript to find section boundaries and inserts
1.5s of silence at each break point.

Usage:
    python scripts/fix-section-breaks.py --chapter 02
    python scripts/fix-section-breaks.py --all
"""

import argparse
import json
import re
import subprocess
from pathlib import Path


def find_section_breaks(transcript_path: Path, sections_path: Path) -> list:
    """
    Find timestamps where section breaks should occur.

    Returns list of timestamps where silence should be inserted.
    """
    with open(transcript_path) as f:
        transcript = json.load(f)

    with open(sections_path) as f:
        sections = json.load(f)

    words = transcript['words']

    # Build searchable text with word indices
    word_texts = [w['word'].lower().strip() for w in words]

    breaks = []

    for section in sections['sections']:
        if not section['expected_pause_after']:
            continue

        # Get last ~20 words of section preview to find end
        preview = section['text_preview'].replace('...', '')
        preview_words = preview.lower().split()[-20:]

        # Search for this sequence in transcript
        search_str = ' '.join(preview_words[-10:])

        # Find approximate location by word matching
        best_match_idx = None
        best_score = 0

        for i in range(len(words) - 5):
            window = ' '.join(word_texts[i:i+10])
            # Simple overlap score
            matches = sum(1 for w in preview_words[-5:] if w in window)
            if matches > best_score:
                best_score = matches
                best_match_idx = i + 5  # End of match window

        if best_match_idx and best_score >= 2:
            # Find the actual pause near this location
            for pause in transcript['pauses']:
                pause_word_idx = pause['after_word_index']
                if abs(pause_word_idx - best_match_idx) < 20:
                    breaks.append({
                        'section': section['id'],
                        'timestamp': pause['start'],
                        'duration': pause['duration'],
                        'after_word': pause['after_word'],
                    })
                    break

    # Deduplicate and sort
    seen = set()
    unique_breaks = []
    for b in sorted(breaks, key=lambda x: x['timestamp']):
        ts = round(b['timestamp'], 1)
        if ts not in seen:
            seen.add(ts)
            unique_breaks.append(b)

    return unique_breaks


def find_breaks_by_manuscript(chapter_num: str, transcript_path: Path, manuscript_path: Path) -> list:
    """
    Find section breaks by matching manuscript section endings to transcript.
    """
    with open(transcript_path) as f:
        transcript = json.load(f)

    with open(manuscript_path) as f:
        manuscript = f.read()

    words = transcript['words']
    pauses = transcript['pauses']

    # Split manuscript by ---
    sections = re.split(r'\n---\n', manuscript)

    breaks = []

    for i, section in enumerate(sections[:-1]):  # Skip last section
        # Get last sentence of section
        lines = [l.strip() for l in section.strip().split('\n') if l.strip()]
        if not lines:
            continue

        last_line = lines[-1]
        # Clean markdown
        last_line = re.sub(r'\*+', '', last_line)
        last_line = re.sub(r'_+', '', last_line)

        # Get last few words
        last_words = last_line.lower().split()[-8:]

        # Search in transcript pauses for matching context
        for pause in pauses:
            after_word = pause['after_word'].lower().strip('.,!?')
            # Check if this pause word matches end of section
            if any(after_word in w or w in after_word for w in last_words[-3:]):
                # Verify by checking surrounding words
                idx = pause['after_word_index']
                if idx > 2:
                    context = ' '.join(w['word'].lower() for w in words[idx-3:idx+1])
                    if any(w in context for w in last_words[-5:]):
                        breaks.append({
                            'section': i + 1,
                            'timestamp': pause['end'],  # Insert after the pause
                            'current_pause': pause['duration'],
                            'after_word': pause['after_word'],
                            'before_word': pause['before_word'],
                        })
                        break

    # Sort and deduplicate
    breaks = sorted(breaks, key=lambda x: x['timestamp'])

    # Remove duplicates within 5 seconds
    filtered = []
    for b in breaks:
        if not filtered or b['timestamp'] - filtered[-1]['timestamp'] > 5:
            filtered.append(b)

    return filtered


def insert_silence(input_path: Path, output_path: Path, break_points: list, silence_dur: float = 1.5) -> bool:
    """
    Insert silence at specified break points.
    """
    if not break_points:
        print(f"  No break points found, copying original")
        subprocess.run(['cp', str(input_path), str(output_path)])
        return True

    # Sort break points
    break_points = sorted(break_points, key=lambda x: x['timestamp'])

    # Build ffmpeg filter
    n_breaks = len(break_points)
    n_parts = n_breaks + 1

    # Create split outputs
    split_labels = ''.join(f'[p{i}]' for i in range(n_parts))

    # Build atrim filters
    filters = [f"[0:a]asplit={n_parts}{split_labels}"]

    prev_ts = 0
    for i, bp in enumerate(break_points):
        ts = bp['timestamp']
        filters.append(f"[p{i}]atrim={prev_ts}:{ts}[s{i}]")
        prev_ts = ts

    # Last segment
    filters.append(f"[p{n_breaks}]atrim={prev_ts}[s{n_breaks}]")

    # Create silence segments
    for i in range(n_breaks):
        filters.append(f"aevalsrc=0:d={silence_dur}:s=44100,aformat=sample_fmts=fltp:channel_layouts=stereo[sil{i}]")

    # Concatenate all
    concat_inputs = ''.join(f'[s{i}][sil{i}]' for i in range(n_breaks)) + f'[s{n_breaks}]'
    concat_n = n_breaks * 2 + 1
    filters.append(f"{concat_inputs}concat=n={concat_n}:v=0:a=1[out]")

    filter_complex = ';\n'.join(filters)

    cmd = [
        'ffmpeg', '-y',
        '-i', str(input_path),
        '-filter_complex', filter_complex,
        '-map', '[out]',
        '-codec:a', 'libmp3lame',
        '-b:a', '192k',
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def create_hybrid_mix(voice_path: Path, output_path: Path) -> bool:
    """Create hybrid mix with ambient and music."""
    ambient = Path.home() / "Music/Freesound/Saltmere-Ambient/254125-Harbor Ambience 1.wav"
    fog = Path.home() / "Music/Suno/Saltmere-Pallette/1. Saltmere Main - Fog and Secrets.wav"

    # Get chapter number from filename
    stem = voice_path.stem
    if 'chapter-' in stem:
        ch_num = stem.split('-')[1]
    else:
        ch_num = '01'

    intro = Path(f"output/audio/bumpers/intro-chapter-{ch_num}.wav")
    outro = Path(f"output/audio/bumpers/outro-chapter-{ch_num}.wav")

    # Get voice duration
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(voice_path)
    ], capture_output=True, text=True)
    voice_dur = float(result.stdout.strip())
    voice_dur_int = int(voice_dur)
    close_start = voice_dur_int - 90

    filter_complex = f"""
    [0:a]volume=1.0[voice];
    [1:a]aloop=loop=-1:size=2e+09,atrim=duration={voice_dur},volume=-25dB[ambient];
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
        '-codec:a', 'libmp3lame',
        '-b:a', '192k',
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def get_duration(path: Path) -> float:
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(path)
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def main():
    parser = argparse.ArgumentParser(description='Fix section breaks in audio')
    parser.add_argument('--chapter', type=str, help='Chapter number (01-12)')
    parser.add_argument('--all', action='store_true', help='Fix all chapters')
    parser.add_argument('--silence', type=float, default=1.5, help='Silence duration (default: 1.5s)')
    parser.add_argument('--skip-hybrid', action='store_true', help='Skip hybrid mix creation')
    args = parser.parse_args()

    if not args.chapter and not args.all:
        parser.print_help()
        return

    audio_dir = Path('output/audio/saltmere')
    timing_dir = Path('output/timing/saltmere')
    manuscript_dir = Path('manuscript/saltmere')
    enhanced_dir = Path('output/audio/saltmere-enhanced')

    # Find chapters to process
    if args.all:
        chapters = ['02', '03', '04', '05', '06', '07']
    else:
        chapters = [args.chapter.zfill(2)]

    for ch in chapters:
        print(f"\n=== Chapter {ch} ===")

        # Find files
        audio_files = list(audio_dir.glob(f'chapter-{ch}-*.mp3'))
        if not audio_files:
            print(f"  No audio file found for chapter {ch}")
            continue

        audio_file = [f for f in audio_files if 'fixed' not in f.name][0]

        transcript_file = list(timing_dir.glob(f'chapter-{ch}-*-transcript.json'))
        if not transcript_file:
            print(f"  No transcript found for chapter {ch}")
            continue
        transcript_file = transcript_file[0]

        manuscript_file = list(manuscript_dir.glob(f'chapter-{ch}-*.md'))
        if not manuscript_file:
            print(f"  No manuscript found for chapter {ch}")
            continue
        manuscript_file = manuscript_file[0]

        # Find section breaks
        print(f"  Finding section breaks...")
        breaks = find_breaks_by_manuscript(ch, transcript_file, manuscript_file)

        if not breaks:
            print(f"  No breaks found, trying alternate method...")
            sections_file = list(timing_dir.glob(f'chapter-{ch}-*-sections.json'))
            if sections_file:
                breaks = find_section_breaks(transcript_file, sections_file[0])

        print(f"  Found {len(breaks)} section break(s):")
        for b in breaks:
            print(f"    Section {b['section']}: {b['timestamp']:.1f}s after \"{b['after_word']}\"")

        # Insert silence
        fixed_file = audio_dir / f"{audio_file.stem}-fixed.mp3"
        print(f"  Inserting {args.silence}s silence at each break...")

        orig_dur = get_duration(audio_file)

        if insert_silence(audio_file, fixed_file, breaks, args.silence):
            new_dur = get_duration(fixed_file)
            print(f"  Created: {fixed_file.name}")
            print(f"  Duration: {orig_dur:.1f}s -> {new_dur:.1f}s (+{new_dur-orig_dur:.1f}s)")
        else:
            print(f"  Failed to create fixed audio")
            continue

        # Create hybrid mix
        if not args.skip_hybrid:
            hybrid_file = enhanced_dir / f"chapter-{ch}-hybrid-fixed.mp3"
            print(f"  Creating hybrid mix...")

            if create_hybrid_mix(fixed_file, hybrid_file):
                hybrid_dur = get_duration(hybrid_file)
                print(f"  Created: {hybrid_file.name} ({hybrid_dur:.1f}s)")
            else:
                print(f"  Failed to create hybrid mix")

    print("\n=== Done ===")


if __name__ == '__main__':
    main()
