#!/usr/bin/env python3
"""
Rebuild chapter audio with foghorn sounds at correct section break positions.

Uses the corrected positions from site/public/js/audio-structure.json
(derived from HTML <hr> elements in the read pages).

Usage:
    python scripts/rebuild-with-correct-breaks.py --chapter 01
    python scripts/rebuild-with-correct-breaks.py --all --dry-run
"""

import argparse
import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent

# Audio sources
RAW_AUDIO_DIR = PROJECT_ROOT / "output/audio/saltmere"
ENHANCED_DIR = PROJECT_ROOT / "output/audio/saltmere-enhanced"
BUMPERS_DIR = PROJECT_ROOT / "output/audio/bumpers"
BUMPERS_WITH_TITLES_DIR = PROJECT_ROOT / "output/audio/bumpers-with-titles"
FINAL_OUTPUT_DIR = PROJECT_ROOT / "site/audio/saltmere-chronicles"

# Sound files
FOGHORN = Path.home() / "Music/Freesound/Saltmere-Ambient/507471-Long Distant Foghorn.aiff.aiff"
AMBIENT = Path.home() / "Music/Freesound/Saltmere-Ambient/254125-Harbor Ambience 1.wav"
MUSIC = Path.home() / "Music/Suno/Saltmere-Pallette/1. Saltmere Main - Fog and Secrets.wav"

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
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(path)
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def load_audio_structure() -> dict:
    """Load the corrected section break positions."""
    json_path = PROJECT_ROOT / "site/public/js/audio-structure.json"
    with open(json_path) as f:
        return json.load(f)


def find_raw_audio(chapter_num: int) -> Path | None:
    """Find the raw (no section breaks) audio file."""
    chapter_id = f"{chapter_num:02d}"

    # Look for files without 'fixed' in name
    for f in RAW_AUDIO_DIR.glob(f"chapter-{chapter_id}-*.mp3"):
        if "fixed" not in f.name:
            return f
    return None


def rebuild_chapter(chapter_num: int, dry_run: bool = False) -> dict:
    """
    Rebuild a chapter with foghorn sounds at correct section breaks.

    Steps:
    1. Take raw narration audio
    2. Insert foghorn + silence at each section break position
    3. Mix with ambient bed and music
    4. Add intro/outro bumpers
    """

    chapter_id = f"{chapter_num:02d}"
    title = CHAPTERS.get(chapter_num, f"Chapter {chapter_num}")

    result = {"chapter": chapter_num, "title": title}

    # Load section data (section-centric model: transitions occur BETWEEN sections)
    audio_struct = load_audio_structure()
    chapter_data = audio_struct.get("chapters", {}).get(str(chapter_num), {})
    sections = chapter_data.get("sections", [])

    # Extract breaks from sections that have transitions (all but last section)
    section_breaks = [
        {"raw_position": s["end"], "duration": s["transition"]}
        for s in sections if "transition" in s
    ]

    if not section_breaks:
        result["error"] = "No section transitions defined"
        return result

    # Find source files
    raw_audio = find_raw_audio(chapter_num)
    if not raw_audio:
        result["error"] = "No raw audio file found"
        return result

    intro = BUMPERS_WITH_TITLES_DIR / f"intro-chapter-{chapter_id}.wav"
    outro = BUMPERS_DIR / f"outro-chapter-{chapter_id}.wav"

    if not intro.exists():
        result["error"] = f"Missing intro: {intro}"
        return result
    if not outro.exists():
        result["error"] = f"Missing outro: {outro}"
        return result
    if not FOGHORN.exists():
        result["error"] = f"Missing foghorn: {FOGHORN}"
        return result

    raw_dur = get_duration(raw_audio)
    foghorn_dur = get_duration(FOGHORN)
    intro_dur = get_duration(intro)
    outro_dur = get_duration(outro)

    result.update({
        "raw_audio": raw_audio.name,
        "raw_duration": round(raw_dur, 1),
        "break_count": len(section_breaks),
        "break_positions": [b["raw_position"] for b in section_breaks],
        "foghorn_duration": round(foghorn_dur, 1),
    })

    if dry_run:
        # Calculate estimated final duration
        total_break_dur = sum(b["duration"] for b in section_breaks)
        est_dur = intro_dur + raw_dur + total_break_dur + outro_dur
        result["status"] = "dry_run"
        result["estimated_duration"] = round(est_dur, 1)
        return result

    # Build the audio with ffmpeg
    ENHANCED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = ENHANCED_DIR / f"chapter-{chapter_id}-hybrid-v10.mp3"

    # Strategy: Split raw audio at break points, insert foghorn+silence, concat
    n_breaks = len(section_breaks)
    break_positions = sorted(section_breaks, key=lambda x: x["raw_position"])

    # Build filter_complex
    filters = []

    # Input labels:
    # 0 = raw narration
    # 1 = foghorn
    # 2 = ambient
    # 3 = music

    # Split raw audio into segments
    split_labels = "".join(f"[seg{i}]" for i in range(n_breaks + 1))
    filters.append(f"[0:a]asplit={n_breaks + 1}{split_labels}")

    # Trim each segment
    prev_pos = 0
    for i, brk in enumerate(break_positions):
        pos = brk["raw_position"]
        filters.append(f"[seg{i}]atrim={prev_pos}:{pos},asetpts=PTS-STARTPTS[s{i}]")
        prev_pos = pos

    # Last segment (from last break to end)
    filters.append(f"[seg{n_breaks}]atrim={prev_pos},asetpts=PTS-STARTPTS[s{n_breaks}]")

    # Create foghorn+silence for each break
    for i, brk in enumerate(break_positions):
        break_dur = brk["duration"]
        # Foghorn at start of break, padded with silence
        # apad adds silence after foghorn to reach break_dur
        filters.append(
            f"[1:a]apad=whole_dur={break_dur},afade=t=in:d=0.3,afade=t=out:st={break_dur-0.5}:d=0.5[brk{i}]"
        )

    # Concatenate: seg0, brk0, seg1, brk1, ..., segN
    concat_inputs = ""
    for i in range(n_breaks):
        concat_inputs += f"[s{i}][brk{i}]"
    concat_inputs += f"[s{n_breaks}]"

    concat_n = n_breaks * 2 + 1
    filters.append(f"{concat_inputs}concat=n={concat_n}:v=0:a=1[voice_with_breaks]")

    # Calculate total voice duration after breaks added
    total_break_dur = sum(b["duration"] for b in break_positions)
    voice_total_dur = raw_dur + total_break_dur

    # Add ambient bed (looped, low volume)
    filters.append(
        f"[2:a]aloop=loop=-1:size=2e+09,atrim=duration={voice_total_dur},"
        f"volume=-24dB[ambient_bed]"
    )

    # Add music (fade in at start, fade out at end)
    music_close_start = int(voice_total_dur) - 90
    filters.append(
        f"[3:a]atrim=0:90,afade=t=in:d=5,afade=t=out:st=60:d=30,volume=-20dB[music_open]"
    )
    filters.append(
        f"[3:a]atrim=0:90,afade=t=in:d=30,afade=t=out:st=85:d=5,volume=-20dB,"
        f"adelay={music_close_start}000|{music_close_start}000[music_close]"
    )

    # Mix voice, ambient, music
    filters.append(
        f"[voice_with_breaks][ambient_bed][music_open][music_close]"
        f"amix=inputs=4:duration=first:normalize=0[mixed]"
    )

    filter_complex = ";\n".join(filters)

    # Run ffmpeg
    cmd = [
        'ffmpeg', '-y',
        '-i', str(raw_audio),
        '-i', str(FOGHORN),
        '-i', str(AMBIENT),
        '-i', str(MUSIC),
        '-filter_complex', filter_complex,
        '-map', '[mixed]',
        '-c:a', 'libmp3lame',
        '-b:a', '192k',
        str(output_path)
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode != 0:
        result["status"] = "failed"
        result["error"] = proc.stderr[-500:] if proc.stderr else "Unknown error"
        return result

    # Verify output
    if output_path.exists():
        result["status"] = "success"
        result["output"] = output_path.name
        result["output_duration"] = round(get_duration(output_path), 1)
    else:
        result["status"] = "failed"
        result["error"] = "Output file not created"

    return result


def main():
    parser = argparse.ArgumentParser(description='Rebuild chapters with correct section breaks')
    parser.add_argument('--chapter', type=int, help='Process single chapter (1-7)')
    parser.add_argument('--all', action='store_true', help='Process all chapters')
    parser.add_argument('--dry-run', action='store_true', help='Show plan without executing')
    args = parser.parse_args()

    if not args.chapter and not args.all:
        parser.print_help()
        return

    chapters = list(range(1, 8)) if args.all else [args.chapter]

    print("=== Rebuilding Chapters with Correct Section Breaks ===")
    print(f"Foghorn: {FOGHORN}")
    print(f"Output: {ENHANCED_DIR}/")
    print()

    for ch in chapters:
        print(f"Chapter {ch}: {CHAPTERS.get(ch, 'Unknown')}...")
        result = rebuild_chapter(ch, dry_run=args.dry_run)

        if result.get("error"):
            print(f"  ERROR: {result['error']}")
        elif result["status"] == "dry_run":
            print(f"  Raw: {result['raw_audio']} ({result['raw_duration']}s)")
            print(f"  Breaks at: {result['break_positions']}")
            print(f"  Est. output: ~{result['estimated_duration']}s")
        else:
            print(f"  Created: {result['output']}")
            print(f"  Duration: {result['output_duration']}s")
        print()

    if args.dry_run:
        print("[DRY RUN - no files created]")


if __name__ == "__main__":
    main()
