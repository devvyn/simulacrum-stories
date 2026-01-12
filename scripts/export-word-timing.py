#!/usr/bin/env python3
"""
Export word-level timing from Whisper transcripts to compact JSON format.

Reads: output/timing/saltmere/*-transcript.json
Outputs: site/js/words/chapter-NN-words.json

RAW timestamps only - calibration is applied at runtime by the JS engine.
This allows timing adjustments without re-exporting.

Compact format: [[start, end, "word"], ...]
"""

import json
import re
from pathlib import Path


def extract_chapter_number(filename: str) -> int | None:
    """Extract chapter number from filename."""
    match = re.search(r"chapter-(\d+)", filename)
    return int(match.group(1)) if match else None


def process_transcript(transcript_path: Path) -> dict:
    """Extract raw word timing from transcript JSON (no calibration)."""
    with open(transcript_path) as f:
        data = json.load(f)

    raw_duration = data.get("duration", 0)

    words = []
    for segment in data.get("segments", []):
        for word_data in segment.get("words", []):
            word = word_data["word"].strip()
            if word:
                words.append([
                    round(word_data["start"], 3),
                    round(word_data["end"], 3),
                    word
                ])

    chapter_num = extract_chapter_number(transcript_path.name)

    return {
        "chapter": chapter_num,
        "raw_duration": round(raw_duration, 1),
        "word_count": len(words),
        "words": words
    }


def main():
    project_root = Path(__file__).parent.parent
    timing_dir = project_root / "output" / "timing" / "saltmere"
    output_dir = project_root / "site" / "js" / "words"

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all transcript files
    transcript_files = sorted(timing_dir.glob("*-transcript.json"))
    # Prefer fixed transcripts if they exist
    fixed_files = {f.name.replace("-fixed-transcript.json", ""): f
                   for f in timing_dir.glob("*-fixed-transcript.json")}

    processed = 0
    total_words = 0

    for transcript_path in transcript_files:
        # Skip if there's a fixed version and this isn't it
        base_name = transcript_path.name.replace("-transcript.json", "").replace("-fixed", "")
        if base_name in fixed_files and "-fixed-" not in transcript_path.name:
            continue

        chapter_num = extract_chapter_number(transcript_path.name)
        if chapter_num is None:
            print(f"  Skipped: {transcript_path.name} (no chapter number)")
            continue

        print(f"Processing: {transcript_path.name}")

        word_data = process_transcript(transcript_path)
        output_path = output_dir / f"chapter-{chapter_num:02d}-words.json"

        with open(output_path, "w") as f:
            json.dump(word_data, f)

        size_kb = output_path.stat().st_size / 1024
        print(f"  → {output_path.name} ({word_data['word_count']} words, {size_kb:.1f}KB)")
        print(f"     Raw duration: {word_data['raw_duration']}s")

        processed += 1
        total_words += word_data["word_count"]

    print(f"\nDone. Exported {processed} chapters, {total_words} total words.")
    print("Note: Timestamps are RAW - calibration applied at runtime via audio-structure.json")


if __name__ == "__main__":
    main()
