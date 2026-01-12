#!/usr/bin/env python3
"""
Export word-level timing from Whisper transcripts to compact JSON format.

Reads: output/timing/saltmere/*-transcript.json
       site/js/audio-manifest.json (for section break calibration)
Outputs: site/js/words/chapter-NN-words.json

Timestamps are adjusted to match final mixed audio (intro + section breaks).
Compact format: [[start, end, "word"], ...]
"""

import json
import re
from pathlib import Path


def extract_chapter_number(filename: str) -> int | None:
    """Extract chapter number from filename."""
    match = re.search(r"chapter-(\d+)", filename)
    return int(match.group(1)) if match else None


def load_manifest(project_root: Path) -> dict:
    """Load audio manifest for calibration data."""
    manifest_path = project_root / "site" / "js" / "audio-manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return {}


def get_chapter_calibration(manifest: dict, chapter_num: int) -> dict:
    """Get calibration parameters for a chapter."""
    key = f"chapter-{chapter_num:02d}-"
    for k, v in manifest.items():
        if k.startswith(key) and v:
            return {
                "intro_offset": v.get("intro_offset", 0),
                "final_duration": v.get("duration", 0),
                "sections": v.get("sections", [])
            }
    return {"intro_offset": 0, "final_duration": 0, "sections": []}


def process_transcript(transcript_path: Path, calibration: dict) -> dict:
    """Extract word timing from transcript JSON with calibration."""
    with open(transcript_path) as f:
        data = json.load(f)

    raw_duration = data.get("duration", 0)
    final_duration = calibration.get("final_duration", raw_duration)
    intro_offset = calibration.get("intro_offset", 0)
    sections = calibration.get("sections", [])

    # Calculate section break time (final - raw - intro)
    section_break_total = max(0, final_duration - raw_duration - intro_offset)
    num_sections = len(sections)

    # Calculate section boundaries in raw audio (approximate)
    # Sections in manifest are final audio times, work backwards
    section_raw_starts = []
    if num_sections > 0 and raw_duration > 0:
        # Estimate where sections start in raw audio
        # by subtracting cumulative section break time
        for i, s in enumerate(sections):
            final_time = s.get("timestamp", 0)
            # Subtract intro and accumulated section breaks
            breaks_before = i  # number of breaks before this section
            break_time_each = section_break_total / num_sections if num_sections > 0 else 0
            raw_time = final_time - intro_offset - (breaks_before * break_time_each)
            section_raw_starts.append(max(0, raw_time))

    def calc_offset(raw_time: float) -> float:
        """Calculate total offset (intro + section breaks) for a raw timestamp."""
        offset = intro_offset

        if num_sections > 0 and section_break_total > 0:
            # Add section break time proportionally
            break_time_each = section_break_total / num_sections

            # Count how many section breaks we've passed
            breaks_passed = 0
            for raw_start in section_raw_starts:
                if raw_time >= raw_start:
                    breaks_passed += 1

            offset += breaks_passed * break_time_each

        return offset

    words = []
    for segment in data.get("segments", []):
        for word_data in segment.get("words", []):
            word = word_data["word"].strip()
            if word:
                raw_start = word_data["start"]
                raw_end = word_data["end"]
                offset = calc_offset(raw_start)

                words.append([
                    round(raw_start + offset, 3),
                    round(raw_end + offset, 3),
                    word
                ])

    chapter_num = extract_chapter_number(transcript_path.name)

    return {
        "chapter": chapter_num,
        "duration": final_duration or data.get("duration"),
        "word_count": len(words),
        "calibration": {
            "intro_offset": intro_offset,
            "section_break_total": round(section_break_total, 1),
            "num_sections": num_sections
        },
        "words": words
    }


def main():
    project_root = Path(__file__).parent.parent
    timing_dir = project_root / "output" / "timing" / "saltmere"
    output_dir = project_root / "site" / "js" / "words"

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load manifest for calibration
    manifest = load_manifest(project_root)

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

        # Get calibration for this chapter
        calibration = get_chapter_calibration(manifest, chapter_num)
        word_data = process_transcript(transcript_path, calibration)
        output_path = output_dir / f"chapter-{chapter_num:02d}-words.json"

        with open(output_path, "w") as f:
            json.dump(word_data, f)

        size_kb = output_path.stat().st_size / 1024
        cal = word_data.get("calibration", {})
        print(f"  → {output_path.name} ({word_data['word_count']} words, {size_kb:.1f}KB)")
        print(f"     Calibration: intro={cal.get('intro_offset', 0)}s, sections={cal.get('num_sections', 0)}, break_total={cal.get('section_break_total', 0)}s")

        processed += 1
        total_words += word_data["word_count"]

    print(f"\nDone. Exported {processed} chapters, {total_words} total words.")


if __name__ == "__main__":
    main()
