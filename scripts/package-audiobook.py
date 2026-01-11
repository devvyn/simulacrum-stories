#!/usr/bin/env python3
"""
Package Saltmere Chronicles audio into distributable formats.

Creates:
- Tagged MP3s for Apple Music (with cover art, metadata)
- M4B audiobook for Apple Books (chapters combined with markers)
- Updated podcast RSS feed

Usage:
    python scripts/package-audiobook.py --mp3      # Create tagged MP3s
    python scripts/package-audiobook.py --m4b      # Create M4B audiobook
    python scripts/package-audiobook.py --all      # Create all formats
"""

import argparse
import json
import subprocess
from pathlib import Path


# Chapter metadata
CHAPTERS = [
    {"num": "01", "title": "The Research Station"},
    {"num": "02", "title": "The Harbor Master"},
    {"num": "03", "title": "First Samples"},
    {"num": "04", "title": "The Librarian's Archive"},
    {"num": "05", "title": "The Waterfront Discovery"},
    {"num": "06", "title": "The Weight of Truth"},
    {"num": "07", "title": "Eleanor's Warning"},
    {"num": "08", "title": "The Old Cannery"},
    {"num": "09", "title": "The Reckoning"},
    {"num": "10", "title": "What Rises"},
    {"num": "11", "title": "What Surfaces"},
    {"num": "12", "title": "The Tide Goes Out"},
]

# Album metadata
ALBUM_METADATA = {
    "album": "The Saltmere Chronicles",
    "artist": "Simulacrum Stories",
    "album_artist": "Simulacrum Stories",
    "genre": "Audiobook",
    "date": "2026",
    "comment": "A marine biologist returns to the town where her grandmother vanished fifty years ago.",
    "copyright": "© 2026 Simulacrum Stories",
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


def create_tagged_mp3(input_path: Path, output_path: Path, chapter: dict,
                      cover_path: Path, total_tracks: int) -> bool:
    """Create MP3 with full metadata and cover art."""

    track_num = int(chapter['num'])
    title = f"Chapter {track_num}: {chapter['title']}"

    cmd = [
        'ffmpeg', '-y',
        '-i', str(input_path),
        '-i', str(cover_path),
        '-map', '0:a',
        '-map', '1:v',
        '-c:a', 'libmp3lame',
        '-b:a', '192k',
        '-c:v', 'mjpeg',
        '-disposition:v', 'attached_pic',
        '-id3v2_version', '3',
        '-metadata', f"title={title}",
        '-metadata', f"album={ALBUM_METADATA['album']}",
        '-metadata', f"artist={ALBUM_METADATA['artist']}",
        '-metadata', f"album_artist={ALBUM_METADATA['album_artist']}",
        '-metadata', f"track={track_num}/{total_tracks}",
        '-metadata', f"genre={ALBUM_METADATA['genre']}",
        '-metadata', f"date={ALBUM_METADATA['date']}",
        '-metadata', f"comment={ALBUM_METADATA['comment']}",
        '-metadata', f"copyright={ALBUM_METADATA['copyright']}",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def create_m4b_audiobook(input_files: list, output_path: Path, cover_path: Path) -> bool:
    """Create M4B audiobook with chapter markers."""

    # First, create chapter metadata file
    chapters_file = output_path.parent / 'chapters.txt'
    concat_file = output_path.parent / 'concat.txt'

    current_time = 0
    chapter_lines = [";FFMETADATA1"]
    concat_lines = []

    for i, (input_file, chapter) in enumerate(input_files):
        duration = get_duration(input_file)

        # Chapter marker
        start_ms = int(current_time * 1000)
        end_ms = int((current_time + duration) * 1000)

        chapter_lines.extend([
            "",
            "[CHAPTER]",
            "TIMEBASE=1/1000",
            f"START={start_ms}",
            f"END={end_ms}",
            f"title=Chapter {chapter['num']}: {chapter['title']}"
        ])

        # Concat list - use absolute paths
        concat_lines.append(f"file '{input_file.resolve()}'")

        current_time += duration

    chapters_file.write_text('\n'.join(chapter_lines))
    concat_file.write_text('\n'.join(concat_lines))

    # Create intermediate M4A with chapters
    temp_m4a = output_path.parent / 'temp_audiobook.m4a'

    # Concatenate all audio files
    cmd1 = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_file),
        '-c:a', 'aac',
        '-b:a', '128k',
        str(temp_m4a)
    ]

    result = subprocess.run(cmd1, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error concatenating: {result.stderr}")
        return False

    # Add chapters and cover
    cmd2 = [
        'ffmpeg', '-y',
        '-i', str(temp_m4a),
        '-i', str(chapters_file),
        '-i', str(cover_path),
        '-map', '0:a',
        '-map', '2:v',
        '-map_metadata', '1',
        '-c:a', 'copy',
        '-c:v', 'mjpeg',
        '-disposition:v', 'attached_pic',
        '-metadata', f"title={ALBUM_METADATA['album']}",
        '-metadata', f"artist={ALBUM_METADATA['artist']}",
        '-metadata', f"album={ALBUM_METADATA['album']}",
        '-metadata', f"genre={ALBUM_METADATA['genre']}",
        '-metadata', f"date={ALBUM_METADATA['date']}",
        '-metadata', f"comment={ALBUM_METADATA['comment']}",
        str(output_path)
    ]

    result = subprocess.run(cmd2, capture_output=True, text=True)

    # Cleanup
    temp_m4a.unlink(missing_ok=True)
    chapters_file.unlink(missing_ok=True)
    concat_file.unlink(missing_ok=True)

    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description='Package Saltmere Chronicles audiobook')
    parser.add_argument('--mp3', action='store_true', help='Create tagged MP3s')
    parser.add_argument('--m4b', action='store_true', help='Create M4B audiobook')
    parser.add_argument('--all', action='store_true', help='Create all formats')
    parser.add_argument('--use-fixed', action='store_true', default=True,
                        help='Use fixed audio files with section breaks (default)')
    args = parser.parse_args()

    if not args.mp3 and not args.m4b and not args.all:
        parser.print_help()
        return

    # Paths
    source_dir = Path('output/audio/saltmere-enhanced')
    output_dir = Path('output/distribution')
    cover_path = Path('output/deployment/audio/saltmere-chronicles/cover.jpg')

    output_dir.mkdir(parents=True, exist_ok=True)
    mp3_dir = output_dir / 'mp3'
    mp3_dir.mkdir(exist_ok=True)

    # Find available chapters
    available = []
    for chapter in CHAPTERS:
        # Try fixed hybrid first, then regular hybrid
        fixed_file = source_dir / f"chapter-{chapter['num']}-hybrid-fixed.mp3"
        regular_file = source_dir / f"chapter-{chapter['num']}-hybrid.mp3"

        if fixed_file.exists():
            available.append((fixed_file, chapter))
        elif regular_file.exists():
            available.append((regular_file, chapter))

    print(f"Found {len(available)} chapters")

    if args.mp3 or args.all:
        print("\n=== Creating Tagged MP3s ===")

        for input_file, chapter in available:
            output_file = mp3_dir / f"{chapter['num']} - {chapter['title']}.mp3"
            print(f"  {chapter['num']}: {chapter['title']}...")

            if create_tagged_mp3(input_file, output_file, chapter, cover_path, len(available)):
                duration = get_duration(output_file)
                print(f"       Created: {output_file.name} ({duration/60:.1f} min)")
            else:
                print(f"       Failed!")

        print(f"\nMP3s saved to: {mp3_dir}/")

    if args.m4b or args.all:
        print("\n=== Creating M4B Audiobook ===")

        m4b_file = output_dir / "The Saltmere Chronicles.m4b"
        print(f"  Combining {len(available)} chapters...")

        if create_m4b_audiobook(available, m4b_file, cover_path):
            duration = get_duration(m4b_file)
            size_mb = m4b_file.stat().st_size / (1024 * 1024)
            print(f"  Created: {m4b_file.name}")
            print(f"  Duration: {duration/60:.1f} minutes")
            print(f"  Size: {size_mb:.1f} MB")
        else:
            print("  Failed to create M4B!")

    print("\n=== Done ===")
    print(f"Output directory: {output_dir}/")


if __name__ == '__main__':
    main()
