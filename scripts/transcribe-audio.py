#!/usr/bin/env python3
"""
Transcribe audio files using Whisper for timing calibration.

Generates:
- Word-level timestamps
- Segment-level timestamps
- Detected pauses (gaps between words)

Usage:
    python scripts/transcribe-audio.py --chapter 01
    python scripts/transcribe-audio.py --all
    python scripts/transcribe-audio.py --file path/to/audio.mp3
"""

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def detect_pauses(words: list, min_pause: float = 0.5) -> list:
    """
    Detect pauses between words.

    Args:
        words: List of word dicts with 'start' and 'end' times
        min_pause: Minimum gap (seconds) to consider a pause

    Returns:
        List of pause dicts with start, end, duration
    """
    pauses = []

    for i in range(len(words) - 1):
        current_end = words[i]['end']
        next_start = words[i + 1]['start']
        gap = next_start - current_end

        if gap >= min_pause:
            pauses.append({
                'after_word_index': i,
                'after_word': words[i]['word'],
                'before_word': words[i + 1]['word'],
                'start': current_end,
                'end': next_start,
                'duration': round(gap, 3),
                'is_section_break': gap >= 1.5,  # Longer pauses likely section breaks
            })

    return pauses


def transcribe_file(audio_path: Path, output_dir: Path, model: str = 'base') -> dict:
    """
    Transcribe an audio file using Whisper.

    Args:
        audio_path: Path to audio file
        output_dir: Directory for output files
        model: Whisper model to use (tiny, base, small, medium, large)

    Returns:
        Transcription result dict
    """
    print(f"Transcribing: {audio_path.name}")

    # Create temp directory for Whisper output
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run whisper with word timestamps
        cmd = [
            'whisper',
            str(audio_path),
            '--model', model,
            '--language', 'en',
            '--output_format', 'json',
            '--output_dir', tmpdir,
            '--word_timestamps', 'True',
            '--verbose', 'False',
        ]

        print(f"  Running: {' '.join(cmd[:6])}...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  Error: {result.stderr}")
            return None

        # Read the JSON output
        json_file = Path(tmpdir) / f"{audio_path.stem}.json"
        if not json_file.exists():
            print(f"  Error: Output file not found")
            return None

        with open(json_file) as f:
            whisper_output = json.load(f)

    # Extract all words with timestamps
    all_words = []
    for segment in whisper_output.get('segments', []):
        for word in segment.get('words', []):
            all_words.append({
                'word': word['word'].strip(),
                'start': round(word['start'], 3),
                'end': round(word['end'], 3),
                'segment_id': segment['id'],
            })

    # Detect pauses
    pauses = detect_pauses(all_words)

    # Classify pauses
    short_pauses = [p for p in pauses if p['duration'] < 1.0]
    medium_pauses = [p for p in pauses if 1.0 <= p['duration'] < 1.5]
    long_pauses = [p for p in pauses if p['duration'] >= 1.5]

    # Build result
    result = {
        'file': audio_path.name,
        'duration': whisper_output.get('segments', [{}])[-1].get('end', 0) if whisper_output.get('segments') else 0,
        'word_count': len(all_words),
        'segment_count': len(whisper_output.get('segments', [])),
        'pause_summary': {
            'total': len(pauses),
            'short_0.5_to_1s': len(short_pauses),
            'medium_1_to_1.5s': len(medium_pauses),
            'long_over_1.5s': len(long_pauses),
        },
        'text': whisper_output.get('text', ''),
        'segments': whisper_output.get('segments', []),
        'words': all_words,
        'pauses': pauses,
    }

    # Save output
    output_file = output_dir / f"{audio_path.stem}-transcript.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"  Duration: {result['duration']:.1f}s, Words: {len(all_words)}, Pauses: {len(pauses)} (long: {len(long_pauses)})")
    print(f"  Saved: {output_file}")

    return result


def find_audio_file(chapter: str, audio_dir: Path) -> Path | None:
    """Find the voice-only audio file for a chapter."""
    # Try different naming patterns
    patterns = [
        f"chapter-{chapter}-*.mp3",
        f"*-chapter-{chapter}-*.mp3",
        f"vignette-{chapter}*.mp3",
    ]

    for pattern in patterns:
        matches = list(audio_dir.glob(pattern))
        if matches:
            return matches[0]

    return None


def main():
    parser = argparse.ArgumentParser(description='Transcribe audio for timing calibration')
    parser.add_argument('--chapter', type=str, help='Chapter number (01-12) or vignette-a/vignette-b')
    parser.add_argument('--all', action='store_true', help='Transcribe all available chapters')
    parser.add_argument('--file', type=Path, help='Direct path to audio file')
    parser.add_argument('--audio-dir', type=Path, default=Path('output/audio/saltmere'),
                        help='Directory containing voice audio files')
    parser.add_argument('--output-dir', type=Path, default=Path('output/timing/saltmere'),
                        help='Output directory for transcript files')
    parser.add_argument('--model', type=str, default='base',
                        choices=['tiny', 'base', 'small', 'medium', 'large'],
                        help='Whisper model to use (default: base)')
    args = parser.parse_args()

    if not args.chapter and not args.all and not args.file:
        parser.print_help()
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.file:
        # Direct file transcription
        if not args.file.exists():
            print(f"Error: File not found: {args.file}")
            return
        transcribe_file(args.file, args.output_dir, args.model)
        return

    # Find audio files
    files = []
    if args.all:
        # Find all voice-only MP3s (not enhanced)
        all_mp3s = list(args.audio_dir.glob('*.mp3'))
        # Filter out enhanced versions
        files = [f for f in all_mp3s if 'enhanced' not in f.stem.lower()]
        files = sorted(files)
    else:
        audio_file = find_audio_file(args.chapter, args.audio_dir)
        if audio_file:
            files = [audio_file]
        else:
            print(f"No audio file found for chapter: {args.chapter}")
            print(f"Available files in {args.audio_dir}:")
            for f in sorted(args.audio_dir.glob('*.mp3')):
                print(f"  {f.name}")
            return

    if not files:
        print(f"No audio files found in {args.audio_dir}")
        return

    print(f"=== Transcribing {len(files)} file(s) with Whisper ({args.model} model) ===\n")

    for audio_file in files:
        transcribe_file(audio_file, args.output_dir, args.model)
        print()

    print("Done!")


if __name__ == '__main__':
    main()
