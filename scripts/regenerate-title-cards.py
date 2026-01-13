#!/usr/bin/env python3
"""
Regenerate chapter title cards with new subtitle.

Generates spoken title announcements:
"The Saltmere Chronicles: The Bay Remembers. Chapter N: [Title]"

Usage:
    ./regenerate-title-cards.py [--dry-run]
"""

import argparse
import subprocess
from pathlib import Path


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "audio" / "chapter-titles"

# Voice configuration (same as main narration)
NARRATOR_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # George

# Chapter titles
CHAPTERS = {
    1: "The Research Station",
    2: "The Harbor Master",
    3: "First Samples",
    4: "The Librarian's Archive",
    5: "The Waterfront Discovery",
    6: "The Weight of Truth",
    7: "Eleanor's Warning",
}


def get_elevenlabs_key() -> str:
    """Get ElevenLabs API key from keychain."""
    result = subprocess.run(
        ["security", "find-generic-password", "-s", "elevenlabs-api-key", "-w"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def generate_title_text(chapter_num: int, chapter_title: str) -> str:
    """Generate the spoken title announcement text."""
    return f"The Saltmere Chronicles: The Bay Remembers. Chapter {chapter_num}: {chapter_title}"


def generate_audio(text: str, output_path: Path, voice_id: str) -> bool:
    """Generate audio using ElevenLabs API."""
    try:
        from elevenlabs.client import ElevenLabs

        api_key = get_elevenlabs_key()
        client = ElevenLabs(api_key=api_key)

        print(f"  Generating: {text}")
        print(f"  Characters: {len(text)}")

        audio = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_192",
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        print(f"  Saved: {output_path}")
        return True

    except ImportError:
        print("Error: elevenlabs package not installed")
        print("Run: uv pip install elevenlabs")
        return False
    except Exception as e:
        print(f"Error generating audio: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Regenerate chapter title cards")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without calling API",
    )
    args = parser.parse_args()

    print("Regenerating title cards with new subtitle...")
    print("=" * 60)

    total_chars = 0
    for chapter_num, chapter_title in CHAPTERS.items():
        title_text = generate_title_text(chapter_num, chapter_title)
        total_chars += len(title_text)

        print(f"\nChapter {chapter_num}:")
        output_path = OUTPUT_DIR / f"chapter-{chapter_num:02d}-title.mp3"

        if args.dry_run:
            print(f"  Text: \"{title_text}\"")
            print(f"  Characters: {len(title_text)}")
            print(f"  Output: {output_path}")
            print("  [DRY RUN - skipping generation]")
        else:
            success = generate_audio(title_text, output_path, NARRATOR_VOICE_ID)
            if not success:
                print(f"  FAILED to generate title for chapter {chapter_num}")

    print("\n" + "=" * 60)
    print(f"Total characters: {total_chars}")
    print(f"Est. cost: ${(total_chars / 1000) * 0.30:.2f}")

    if args.dry_run:
        print("\n[DRY RUN complete - no audio generated]")
    else:
        print("\nTitle cards regenerated successfully!")
        print(f"Files saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
