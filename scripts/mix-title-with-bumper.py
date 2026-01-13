#!/usr/bin/env python3
"""
Mix title cards with intro bumpers.

Creates combined intro bumpers by crossfading the spoken title
over the music bumper (title starts around 6s into music).

Usage:
    python scripts/mix-title-with-bumper.py [--dry-run]
"""

import argparse
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
BUMPERS_DIR = PROJECT_ROOT / "output/audio/bumpers"
TITLES_DIR = PROJECT_ROOT / "output/audio/chapter-titles"
OUTPUT_DIR = PROJECT_ROOT / "output/audio/bumpers-with-titles"

# Timing configuration
TITLE_START_OFFSET = 5.5   # When title audio starts (seconds into bumper)
MUSIC_DUCK_DB = -8         # How much to duck music during speech
CROSSFADE_IN = 0.3         # Title fade in duration
CROSSFADE_OUT = 1.0        # Title fade out duration
OUTPUT_DURATION = 12       # Total output duration


def get_duration(path: Path) -> float:
    """Get audio duration in seconds."""
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(path)
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def mix_title_with_bumper(chapter_num: int, dry_run: bool = False) -> dict:
    """Mix a title card with its corresponding bumper."""

    bumper_file = BUMPERS_DIR / f"intro-chapter-{chapter_num:02d}.wav"
    title_file = TITLES_DIR / f"chapter-{chapter_num:02d}-title.mp3"
    output_file = OUTPUT_DIR / f"intro-chapter-{chapter_num:02d}.wav"

    if not bumper_file.exists():
        return {"error": f"Bumper not found: {bumper_file}"}
    if not title_file.exists():
        return {"error": f"Title not found: {title_file}"}

    title_duration = get_duration(title_file)
    bumper_duration = get_duration(bumper_file)

    # Calculate timing
    title_end = TITLE_START_OFFSET + title_duration

    result = {
        "chapter": chapter_num,
        "bumper": str(bumper_file.name),
        "title": str(title_file.name),
        "title_duration": round(title_duration, 1),
        "output": str(output_file.name),
        "output_duration": OUTPUT_DURATION,
    }

    if dry_run:
        result["status"] = "dry_run"
        return result

    # FFmpeg filter:
    # 1. Lower music volume slightly
    # 2. Delay title to start at offset, add fades
    # 3. Mix together and trim to output duration

    delay_ms = int(TITLE_START_OFFSET * 1000)
    filter_complex = (
        f"[0:a]volume=-3dB[music];"
        f"[1:a]adelay={delay_ms}|{delay_ms},"
        f"afade=t=in:d={CROSSFADE_IN},"
        f"afade=t=out:st={title_duration - CROSSFADE_OUT}:d={CROSSFADE_OUT},"
        f"volume=3dB[title];"
        f"[music][title]amix=inputs=2:duration=first:normalize=0,"
        f"atrim=0:{OUTPUT_DURATION},"
        f"afade=t=out:st={OUTPUT_DURATION - 2}:d=2[out]"
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        'ffmpeg', '-y',
        '-i', str(bumper_file),
        '-i', str(title_file),
        '-filter_complex', filter_complex.replace('\n', '').strip(),
        '-map', '[out]',
        '-c:a', 'pcm_s16le',
        str(output_file)
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode == 0:
        actual_duration = get_duration(output_file)
        result["status"] = "success"
        result["actual_duration"] = round(actual_duration, 1)
    else:
        result["status"] = "failed"
        result["error"] = proc.stderr[-500:] if proc.stderr else "Unknown error"

    return result


def main():
    parser = argparse.ArgumentParser(description='Mix title cards with bumpers')
    parser.add_argument('--dry-run', action='store_true', help='Show plan without executing')
    parser.add_argument('--chapter', type=int, help='Process single chapter')
    args = parser.parse_args()

    chapters = [args.chapter] if args.chapter else range(1, 8)  # Chapters 1-7 have audio

    print("=== Mixing Title Cards with Bumpers ===")
    print(f"Title start offset: {TITLE_START_OFFSET}s")
    print(f"Music duck: {MUSIC_DUCK_DB}dB during speech")
    print(f"Output duration: {OUTPUT_DURATION}s")
    print()

    results = []
    for ch in chapters:
        print(f"Chapter {ch}...")
        result = mix_title_with_bumper(ch, dry_run=args.dry_run)
        results.append(result)

        if result.get("error"):
            print(f"  ERROR: {result['error']}")
        elif result["status"] == "dry_run":
            print(f"  Title: {result['title']} ({result['title_duration']}s)")
            print(f"  Output: {result['output']} ({result['output_duration']}s)")
        else:
            print(f"  Created: {result['output']} ({result['actual_duration']}s)")

    print()
    if args.dry_run:
        print("[DRY RUN - no files created]")
    else:
        print(f"Done! Output: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
