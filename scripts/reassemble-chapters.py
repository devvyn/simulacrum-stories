#!/usr/bin/env python3
"""
Reassemble chapter audio with new intro bumpers (including titles).

Takes the narration + section breaks audio and combines with:
- New intro bumpers (with spoken titles)
- Ambient beds
- Music beds
- Outro bumpers

Usage:
    python scripts/reassemble-chapters.py [--dry-run] [--chapter N]
"""

import argparse
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent

# Audio sources
BUMPERS_WITH_TITLES_DIR = PROJECT_ROOT / "output/audio/bumpers-with-titles"
PLAIN_BUMPERS_DIR = PROJECT_ROOT / "output/audio/bumpers"
ENHANCED_DIR = PROJECT_ROOT / "output/audio/saltmere-enhanced"
OUTPUT_DIR = PROJECT_ROOT / "site/audio/saltmere-chronicles"

# Chapter metadata
CHAPTERS = {
    1: "The Research Station",
    2: "The Harbor Master",
    3: "First Samples",
    4: "The Librarian's Archive",
    5: "The Waterfront Discovery",
    6: "The Weight of Truth",
    7: "Eleanor's Warning",
}


def get_duration(path: Path) -> float:
    """Get audio duration in seconds."""
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(path)
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def find_narration_file(chapter_num: int) -> Path | None:
    """Find the best narration file for a chapter (hybrid-v10 preferred)."""
    patterns = [
        f"chapter-{chapter_num:02d}-hybrid-v10.mp3",  # Correct section break positions
        f"chapter-{chapter_num:02d}-hybrid-v9.mp3",
        f"chapter-{chapter_num:02d}-hybrid-v8.mp3",
        f"chapter-{chapter_num:02d}-hybrid-v7.mp3",
        f"chapter-{chapter_num:02d}-hybrid.mp3",
    ]
    for pattern in patterns:
        path = ENHANCED_DIR / pattern
        if path.exists():
            return path
    return None


def reassemble_chapter(chapter_num: int, dry_run: bool = False) -> dict:
    """Reassemble a chapter with new intro bumper."""

    title = CHAPTERS.get(chapter_num, f"Chapter {chapter_num}")

    # Find source files
    narration = find_narration_file(chapter_num)
    intro = BUMPERS_WITH_TITLES_DIR / f"intro-chapter-{chapter_num:02d}.wav"
    outro = PLAIN_BUMPERS_DIR / f"outro-chapter-{chapter_num:02d}.wav"
    output = OUTPUT_DIR / f"{chapter_num:02d} - {title}.mp3"

    result = {
        "chapter": chapter_num,
        "title": title,
    }

    # Check files exist
    if not narration:
        return {**result, "error": "No narration file found"}
    if not intro.exists():
        return {**result, "error": f"No intro bumper: {intro}"}
    if not outro.exists():
        return {**result, "error": f"No outro bumper: {outro}"}

    narration_dur = get_duration(narration)
    intro_dur = get_duration(intro)
    outro_dur = get_duration(outro)

    result.update({
        "narration": narration.name,
        "narration_dur": round(narration_dur, 1),
        "intro_dur": round(intro_dur, 1),
        "outro_dur": round(outro_dur, 1),
        "output": output.name,
    })

    if dry_run:
        result["status"] = "dry_run"
        result["est_duration"] = round(intro_dur + narration_dur + outro_dur, 1)
        return result

    # Simple concat using filter_complex (handles mixed formats)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        'ffmpeg', '-y',
        '-i', str(intro),
        '-i', str(narration),
        '-i', str(outro),
        '-filter_complex', '[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]',
        '-map', '[out]',
        '-codec:a', 'libmp3lame',
        '-b:a', '192k',
        str(output)
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode == 0:
        actual_dur = get_duration(output)
        size_mb = output.stat().st_size / (1024 * 1024)
        result["status"] = "success"
        result["duration"] = round(actual_dur, 1)
        result["size_mb"] = round(size_mb, 1)
    else:
        result["status"] = "failed"
        result["error"] = proc.stderr[-300:] if proc.stderr else "Unknown error"

    return result


def main():
    parser = argparse.ArgumentParser(description='Reassemble chapter audio with new intros')
    parser.add_argument('--dry-run', action='store_true', help='Show plan without executing')
    parser.add_argument('--chapter', type=int, help='Process single chapter')
    args = parser.parse_args()

    chapters = [args.chapter] if args.chapter else list(CHAPTERS.keys())

    print("=== Reassembling Chapters with New Title Intros ===")
    print(f"Intro source: {BUMPERS_WITH_TITLES_DIR}/")
    print(f"Output: {OUTPUT_DIR}/")
    print()

    for ch in chapters:
        print(f"Chapter {ch}: {CHAPTERS.get(ch, 'Unknown')}...")
        result = reassemble_chapter(ch, dry_run=args.dry_run)

        if result.get("error"):
            print(f"  ERROR: {result['error']}")
        elif result["status"] == "dry_run":
            print(f"  Narration: {result['narration']} ({result['narration_dur']}s)")
            print(f"  Est output: {result['output']} (~{result['est_duration']}s)")
        else:
            print(f"  Created: {result['output']}")
            print(f"  Duration: {result['duration']}s ({result['size_mb']}MB)")

    print()
    if args.dry_run:
        print("[DRY RUN - no files created]")
    else:
        print("Done! Chapters reassembled with new title intros.")


if __name__ == "__main__":
    main()
