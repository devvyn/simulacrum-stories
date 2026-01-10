#!/usr/bin/env python3
"""
Generate audiobook chapter using ElevenLabs.

Strips editorial notes and generates clean narration.

Usage:
    ./generate-chapter-audio.py chapter-01 [--dry-run]
    ./generate-chapter-audio.py all [--dry-run]
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
MANUSCRIPT_DIR = PROJECT_ROOT / "manuscript" / "saltmere"
OUTPUT_DIR = PROJECT_ROOT / "output" / "audio" / "saltmere"

# Voice configuration from docs/saltmere-voice-casting.md
NARRATOR_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # George


def get_elevenlabs_key() -> str:
    """Get ElevenLabs API key from keychain."""
    result = subprocess.run(
        ["security", "find-generic-password", "-s", "elevenlabs-api-key", "-w"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def clean_chapter(text: str) -> str:
    """Strip headers, editorial notes, and metadata for clean narration."""

    # Remove chapter title header
    text = re.sub(r"^# Chapter \d+:.*$\n?", "", text, flags=re.MULTILINE)

    # Remove editorial notes section at end
    text = re.sub(r"\*\*Editorial Notes:\*\*.*$", "", text, flags=re.DOTALL)

    # Remove horizontal rules
    text = re.sub(r"^---+$\n?", "\n", text, flags=re.MULTILINE)

    # Remove "End of Chapter" marker
    text = re.sub(r"^\*End of Chapter \d+\*$\n?", "", text, flags=re.MULTILINE)

    # Remove vignette titles
    text = re.sub(r"^# Vignette.*$\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\*.*before Sarah Chen.*\*$\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\*Excerpts from.*\*$\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\*Discovered in.*\*$\n?", "", text, flags=re.MULTILINE)

    # Remove standalone asterisk lines (vignette markers)
    text = re.sub(r"^\*\*\*$\n?", "\n", text, flags=re.MULTILINE)

    # Clean up multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove markdown bold/italic
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)

    return text.strip()


def estimate_cost(text: str) -> dict:
    """Estimate ElevenLabs cost and duration."""
    char_count = len(text)
    # ElevenLabs: ~1000 chars ≈ 1 minute of audio
    estimated_minutes = char_count / 1000
    # Cost: ~$0.30 per 1000 chars on Creator plan
    estimated_cost = (char_count / 1000) * 0.30

    return {
        "characters": char_count,
        "estimated_minutes": round(estimated_minutes, 1),
        "estimated_cost_usd": round(estimated_cost, 2),
    }


MAX_CHARS_PER_REQUEST = 9500  # Stay under 10K limit with margin


def chunk_text(text: str, max_chars: int = MAX_CHARS_PER_REQUEST) -> list[str]:
    """Split text into chunks at paragraph boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    paragraphs = text.split("\n\n")
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_chars:
            current_chunk += ("\n\n" if current_chunk else "") + para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # Handle paragraphs longer than max_chars
            if len(para) > max_chars:
                # Split at sentence boundaries
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current_chunk = ""
                for sent in sentences:
                    if len(current_chunk) + len(sent) + 1 <= max_chars:
                        current_chunk += (" " if current_chunk else "") + sent
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sent
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def generate_audio(text: str, output_path: Path, voice_id: str, high_quality: bool = True) -> bool:
    """Generate audio using ElevenLabs API with automatic chunking.

    Args:
        text: Text to convert to speech
        output_path: Output file path
        voice_id: ElevenLabs voice ID
        high_quality: Use 44.1kHz 192kbps (Creator tier) vs default
    """
    try:
        from elevenlabs.client import ElevenLabs

        api_key = get_elevenlabs_key()
        client = ElevenLabs(api_key=api_key)

        # Output format: mp3_44100_192 is highest quality on Creator tier
        output_format = "mp3_44100_192" if high_quality else "mp3_44100_128"

        # Chunk if needed
        chunks = chunk_text(text)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if len(chunks) == 1:
            # Single chunk - direct generation
            print(f"  Generating audio ({len(text)} chars, {output_format})...")
            audio = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                output_format=output_format,
            )
            with open(output_path, "wb") as f:
                for chunk in audio:
                    f.write(chunk)
        else:
            # Multiple chunks - generate and concatenate
            print(f"  Generating audio ({len(text)} chars in {len(chunks)} chunks, {output_format})...")
            temp_files = []
            temp_dir = output_path.parent / "temp_chunks"
            temp_dir.mkdir(exist_ok=True)

            try:
                for i, chunk_text_part in enumerate(chunks):
                    print(f"    Chunk {i+1}/{len(chunks)} ({len(chunk_text_part)} chars)...")
                    temp_file = temp_dir / f"chunk_{i:03d}.mp3"

                    audio = client.text_to_speech.convert(
                        text=chunk_text_part,
                        voice_id=voice_id,
                        model_id="eleven_multilingual_v2",
                        output_format=output_format,
                    )
                    with open(temp_file, "wb") as f:
                        for audio_chunk in audio:
                            f.write(audio_chunk)
                    temp_files.append(temp_file)

                # Concatenate with ffmpeg
                concat_list = temp_dir / "concat.txt"
                with open(concat_list, "w") as f:
                    for tf in temp_files:
                        f.write(f"file '{tf.absolute()}'\n")

                subprocess.run(
                    ["ffmpeg", "-f", "concat", "-safe", "0", "-i", str(concat_list),
                     "-c", "copy", str(output_path), "-y"],
                    check=True, capture_output=True
                )
            finally:
                # Cleanup
                import shutil
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)

        print(f"  Saved: {output_path}")
        return True

    except ImportError:
        print("Error: elevenlabs package not installed")
        print("Run: uv pip install elevenlabs")
        return False
    except Exception as e:
        print(f"Error generating audio: {e}")
        return False


def process_chapter(chapter_file: Path, dry_run: bool = False) -> bool:
    """Process a single chapter file."""
    print(f"\nProcessing: {chapter_file.name}")

    # Read and clean
    text = chapter_file.read_text()
    cleaned = clean_chapter(text)

    # Estimate
    estimate = estimate_cost(cleaned)
    print(f"  Characters: {estimate['characters']:,}")
    print(f"  Est. duration: {estimate['estimated_minutes']} minutes")
    print(f"  Est. cost: ${estimate['estimated_cost_usd']}")

    if dry_run:
        print("  [DRY RUN - skipping generation]")
        # Show preview
        preview = cleaned[:500] + "..." if len(cleaned) > 500 else cleaned
        print(f"\n  Preview:\n  {preview[:200]}...")
        return True

    # Generate output filename
    stem = chapter_file.stem
    output_path = OUTPUT_DIR / f"{stem}.mp3"

    return generate_audio(cleaned, output_path, NARRATOR_VOICE_ID)


def main():
    parser = argparse.ArgumentParser(description="Generate audiobook chapters")
    parser.add_argument(
        "chapter",
        help="Chapter to process (e.g., 'chapter-01', 'vignette-a', or 'all')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without calling API",
    )
    args = parser.parse_args()

    # Find chapter files
    if args.chapter == "all":
        chapters = sorted(MANUSCRIPT_DIR.glob("*.md"))
    else:
        # Support partial names
        pattern = f"*{args.chapter}*.md"
        chapters = list(MANUSCRIPT_DIR.glob(pattern))

        if not chapters:
            print(f"No chapters matching: {args.chapter}")
            print(f"Available: {[f.stem for f in MANUSCRIPT_DIR.glob('*.md')]}")
            sys.exit(1)

    print(f"Found {len(chapters)} chapter(s)")

    # Process
    total_chars = 0
    for chapter in chapters:
        text = chapter.read_text()
        cleaned = clean_chapter(text)
        total_chars += len(cleaned)

        success = process_chapter(chapter, dry_run=args.dry_run)
        if not success:
            print(f"Failed to process: {chapter.name}")

    # Summary
    print(f"\n{'='*50}")
    print(f"Total characters: {total_chars:,}")
    print(f"Total est. duration: {total_chars/1000:.1f} minutes")
    print(f"Total est. cost: ${(total_chars/1000)*0.30:.2f}")

    if args.dry_run:
        print("\n[DRY RUN complete - no audio generated]")


if __name__ == "__main__":
    main()
