#!/usr/bin/env python3
"""
Analyze audio at section break points to find clean cut locations.

Uses zero-crossing detection to find optimal silence insertion points.
Extracts samples around each break for review.

Usage:
    python scripts/analyze-break-points.py --chapter 01
"""

import argparse
import json
import subprocess
import struct
import wave
from pathlib import Path


def get_samples(audio_path: Path, start_sec: float, duration_sec: float) -> tuple:
    """Extract raw audio samples from a region."""
    # Convert MP3 to WAV samples using ffmpeg
    cmd = [
        'ffmpeg', '-y',
        '-ss', str(start_sec),
        '-t', str(duration_sec),
        '-i', str(audio_path),
        '-ar', '44100',
        '-ac', '1',  # mono for analysis
        '-f', 'wav',
        '-'
    ]

    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        return None, 44100

    # Parse WAV from stdout
    import io
    wav_data = io.BytesIO(result.stdout)

    try:
        with wave.open(wav_data, 'rb') as wf:
            n_frames = wf.getnframes()
            sample_rate = wf.getframerate()
            raw = wf.readframes(n_frames)
            # Convert to signed 16-bit samples
            samples = struct.unpack(f'<{n_frames}h', raw)
            return list(samples), sample_rate
    except:
        return None, 44100


def find_zero_crossings(samples: list, sample_rate: int, window_ms: int = 100) -> list:
    """Find zero-crossing points in audio samples."""
    crossings = []
    window_samples = int(sample_rate * window_ms / 1000)

    for i in range(1, len(samples)):
        # Zero crossing: sign change
        if (samples[i-1] >= 0 and samples[i] < 0) or (samples[i-1] < 0 and samples[i] >= 0):
            # Calculate local energy (RMS) around this point
            start = max(0, i - window_samples // 2)
            end = min(len(samples), i + window_samples // 2)
            window = samples[start:end]
            rms = (sum(s*s for s in window) / len(window)) ** 0.5

            crossings.append({
                'sample': i,
                'time_offset': i / sample_rate,
                'rms': rms,
            })

    return crossings


def find_silence_regions(samples: list, sample_rate: int,
                         threshold: int = 500, min_duration_ms: int = 50) -> list:
    """Find regions of near-silence in audio."""
    min_samples = int(sample_rate * min_duration_ms / 1000)

    regions = []
    in_silence = False
    silence_start = 0

    # Use a sliding window for smoothing
    window_size = int(sample_rate * 0.01)  # 10ms window

    for i in range(0, len(samples) - window_size, window_size // 2):
        window = samples[i:i + window_size]
        peak = max(abs(s) for s in window)

        if peak < threshold:
            if not in_silence:
                silence_start = i
                in_silence = True
        else:
            if in_silence:
                silence_end = i
                duration = silence_end - silence_start
                if duration >= min_samples:
                    regions.append({
                        'start_sample': silence_start,
                        'end_sample': silence_end,
                        'start_time': silence_start / sample_rate,
                        'end_time': silence_end / sample_rate,
                        'duration': duration / sample_rate,
                    })
                in_silence = False

    return regions


def extract_sample_clip(audio_path: Path, output_path: Path,
                        start_sec: float, duration_sec: float):
    """Extract a clip from the audio file."""
    cmd = [
        'ffmpeg', '-y',
        '-ss', str(start_sec),
        '-t', str(duration_sec),
        '-i', str(audio_path),
        '-c:a', 'libmp3lame',
        '-b:a', '192k',
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True)


def analyze_chapter(chapter_num: str):
    """Analyze break points for a chapter."""

    # Paths
    audio_dir = Path('output/audio/saltmere')
    timing_dir = Path('output/timing/saltmere')
    output_dir = Path('output/timing/saltmere/samples')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find original (unfixed) audio
    audio_files = list(audio_dir.glob(f'chapter-{chapter_num}-*.mp3'))
    audio_file = [f for f in audio_files if 'fixed' not in f.name][0]

    # Load transcript for pause locations
    transcript_files = list(timing_dir.glob(f'chapter-{chapter_num}-*-transcript.json'))
    if not transcript_files:
        print(f"No transcript found for chapter {chapter_num}")
        return

    with open(transcript_files[0]) as f:
        transcript = json.load(f)

    pauses = transcript['pauses']

    # Find the longest pauses (likely section breaks)
    top_pauses = sorted(pauses, key=lambda p: p['duration'], reverse=True)[:10]

    print(f"=== Chapter {chapter_num}: Analyzing Break Points ===")
    print(f"Audio: {audio_file.name}")
    print()

    results = []

    for i, pause in enumerate(top_pauses[:5]):  # Top 5 longest pauses
        pause_start = pause['start']
        pause_end = pause['end']

        # Analyze 3 seconds around the pause
        analysis_start = max(0, pause_start - 1.5)
        analysis_duration = 3.0

        print(f"Pause {i+1}: {pause_start:.2f}s - {pause_end:.2f}s ({pause['duration']:.2f}s)")
        print(f"  After: \"{pause['after_word']}\"")
        print(f"  Before: \"{pause['before_word']}\"")

        # Get samples
        samples, sr = get_samples(audio_file, analysis_start, analysis_duration)

        if samples:
            # Find silence regions
            silences = find_silence_regions(samples, sr, threshold=800)

            print(f"  Silence regions found: {len(silences)}")

            # Find best cut point
            # Target: the middle of the pause in our analysis window
            target_offset = pause_start - analysis_start + (pause['duration'] / 2)

            best_silence = None
            best_distance = float('inf')

            for silence in silences:
                mid_time = (silence['start_time'] + silence['end_time']) / 2
                distance = abs(mid_time - target_offset)
                if distance < best_distance:
                    best_distance = distance
                    best_silence = silence

            if best_silence:
                # Optimal cut point is middle of the best silence region
                optimal_cut = analysis_start + (best_silence['start_time'] + best_silence['end_time']) / 2
                print(f"  Optimal cut point: {optimal_cut:.3f}s (silence: {best_silence['duration']*1000:.0f}ms)")

                results.append({
                    'pause_index': i,
                    'original_timestamp': pause_start,
                    'optimal_cut': optimal_cut,
                    'silence_start': analysis_start + best_silence['start_time'],
                    'silence_end': analysis_start + best_silence['end_time'],
                    'after_word': pause['after_word'],
                    'before_word': pause['before_word'],
                })
            else:
                print(f"  No clean silence found, using zero-crossings...")
                # Fall back to zero-crossing near the pause
                crossings = find_zero_crossings(samples, sr)
                target_sample = int(target_offset * sr)

                # Find crossing with lowest energy near target
                nearby = [c for c in crossings if abs(c['sample'] - target_sample) < sr * 0.2]  # within 200ms
                if nearby:
                    best = min(nearby, key=lambda c: c['rms'])
                    optimal_cut = analysis_start + best['time_offset']
                    print(f"  Zero-crossing cut point: {optimal_cut:.3f}s")
                    results.append({
                        'pause_index': i,
                        'original_timestamp': pause_start,
                        'optimal_cut': optimal_cut,
                        'after_word': pause['after_word'],
                        'before_word': pause['before_word'],
                    })

        # Extract sample clip for review (5 seconds around pause)
        clip_start = max(0, pause_start - 2.5)
        clip_path = output_dir / f"ch{chapter_num}-break{i+1}-at-{pause_start:.0f}s.mp3"
        extract_sample_clip(audio_file, clip_path, clip_start, 5.0)
        print(f"  Sample: {clip_path.name}")
        print()

    # Save results
    results_file = output_dir / f"chapter-{chapter_num}-break-analysis.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Analysis saved: {results_file}")
    print(f"Samples saved: {output_dir}/")


def main():
    parser = argparse.ArgumentParser(description='Analyze audio break points')
    parser.add_argument('--chapter', type=str, required=True, help='Chapter number')
    args = parser.parse_args()

    analyze_chapter(args.chapter.zfill(2))


if __name__ == '__main__':
    main()
