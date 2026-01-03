#!/usr/bin/env python3
"""
Story to Audio Pipeline

Integrates character voice mapping with doc-to-audio.py for dramatic readings.

Usage:
    # Test the example scene
    ./story_to_audio.py \
        --input ../../examples/simulacrum-stories/simple-dialogue-test.md \
        --output ../../audio-assets/stories/ \
        --auto-detect-characters

    # Specify characters explicitly
    ./story_to_audio.py \
        --input scene.md \
        --output audio/ \
        --characters Sheriff Sarah Jack \
        --narrator Aman

    # Use character profiles from JSON
    ./story_to_audio.py \
        --input scene.md \
        --output audio/ \
        --character-profiles characters.json \
        --narrator Aman
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Import character voice mapper
try:
    from character_voice_mapper import CharacterProfile, CharacterVoiceMapper
except ImportError:
    # Try relative import if running as script
    import os

    sys.path.insert(0, os.path.dirname(__file__))
    from character_voice_mapper import CharacterProfile, CharacterVoiceMapper


class StoryParser:
    """Parse story markdown to extract characters and validate voice tags"""

    def __init__(self, markdown_text: str):
        self.text = markdown_text
        self.characters: set[str] = set()
        self.voice_tags: set[str] = set()

    def extract_characters(self) -> list[str]:
        """Extract all CHARACTER_<name> tags from markdown"""

        # Pattern: <VOICE:CHARACTER_Name> or <VOICE:CHARACTER_Name tone="...">
        # The attributes group is optional (note the ? after the group)
        pattern = r"<VOICE:CHARACTER_(\w+)(?:\s+[^>]*)?>"

        matches = re.findall(pattern, self.text)
        self.characters = set(matches)

        return sorted(self.characters)

    def extract_all_voice_tags(self) -> list[str]:
        """Extract all voice tags (NARRATOR, CHARACTER_*, etc.)"""

        pattern = r"<VOICE:(\w+)(?:\s+[^>]*)>"

        matches = re.findall(pattern, self.text)
        self.voice_tags = set(matches)

        return sorted(self.voice_tags)

    def validate_tags(self) -> bool:
        """Check if all voice tags are properly formatted"""

        # Find all <VOICE:...> tags
        tags = re.findall(r"<VOICE:([^>]+)>", self.text)

        for tag in tags:
            # Check for properly formatted content type
            if not re.match(
                r"^(NARRATOR|CHARACTER_\w+|CODE|QUOTE|HEADER)(\s+\w+=.+)?$", tag
            ):
                print(f"Warning: Potentially malformed voice tag: <VOICE:{tag}>")
                return False

        # Check for matching closing tags
        opening_tags = re.findall(r"<VOICE:(\w+)", self.text)
        closing_tags = re.findall(r"</VOICE:(\w+)>", self.text)

        if len(opening_tags) != len(closing_tags):
            print(
                f"Warning: Mismatched voice tags ({len(opening_tags)} opening, {len(closing_tags)} closing)"
            )
            return False

        return True


def load_character_profiles(json_path: str) -> list[CharacterProfile]:
    """Load character profiles from JSON file"""

    with open(json_path) as f:
        data = json.load(f)

    profiles = []
    for char_data in data.get("characters", []):
        profile = CharacterProfile(
            name=char_data["name"],
            gender=char_data.get("gender"),
            age=char_data.get("age"),
            role=char_data.get("role"),
            personality=char_data.get("personality"),
            voice_characteristics=char_data.get("voice_characteristics"),
        )
        profiles.append(profile)

    return profiles


def main():
    parser = argparse.ArgumentParser(
        description="Convert story markdown to audio with character voices"
    )

    # Input/output
    parser.add_argument("--input", required=True, help="Input markdown file")
    parser.add_argument(
        "--output", default="audio", help="Output directory for audio files"
    )

    # Character specification
    char_group = parser.add_mutually_exclusive_group()
    char_group.add_argument(
        "--auto-detect-characters",
        action="store_true",
        help="Auto-detect characters from voice tags",
    )
    char_group.add_argument(
        "--characters", nargs="+", help="Character names (e.g., Sheriff Sarah Jack)"
    )
    char_group.add_argument(
        "--character-profiles", help="JSON file with character profiles"
    )

    # Voice configuration
    parser.add_argument(
        "--narrator",
        default="Aman",
        help="Narrator voice (default: Aman)",
    )

    parser.add_argument(
        "--provider",
        default="macos",
        choices=["macos", "elevenlabs", "openai"],
        help="TTS provider (default: macos)",
    )

    # Audio options
    parser.add_argument(
        "--advanced-mixing",
        action="store_true",
        help="Enable crossfading and normalization",
    )

    parser.add_argument(
        "--conservative-pauses",
        action="store_true",
        help="Use 2.5s pauses for voice changes",
    )

    # Validation
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate tags, don't generate audio",
    )

    parser.add_argument(
        "--show-mapping",
        action="store_true",
        help="Show character-to-voice mapping and exit",
    )

    args = parser.parse_args()

    # Read input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    with open(input_path) as f:
        markdown_text = f.read()

    # Parse story
    parser_obj = StoryParser(markdown_text)

    # Validate tags
    print("Validating voice tags...")
    if not parser_obj.validate_tags():
        print("Error: Voice tag validation failed")
        sys.exit(1)
    print("✓ Voice tags valid")

    # Extract characters
    if args.auto_detect_characters:
        characters = parser_obj.extract_characters()
        print(f"Auto-detected {len(characters)} characters: {', '.join(characters)}")
    elif args.character_profiles:
        character_profiles = load_character_profiles(args.character_profiles)
        characters = character_profiles
        print(f"Loaded {len(characters)} character profiles from JSON")
    elif args.characters:
        characters = args.characters
        print(f"Using {len(characters)} specified characters: {', '.join(characters)}")
    else:
        # Default: auto-detect
        characters = parser_obj.extract_characters()
        print(f"Auto-detected {len(characters)} characters: {', '.join(characters)}")

    # Create voice mapper
    print("\nAllocating voices...")
    mapper = CharacterVoiceMapper(
        characters=characters, narrator_voice=args.narrator, provider=args.provider
    )

    # Show mapping
    mapper.print_mapping()

    if args.show_mapping or args.validate_only:
        print("\n✓ Validation complete")
        sys.exit(0)

    # Generate audio
    print("\n" + "=" * 60)
    print("GENERATING AUDIO")
    print("=" * 60)

    # Build doc-to-audio.py command
    import subprocess

    # Find doc-to-audio.py
    script_dir = Path(__file__).parent.parent
    doc_to_audio = script_dir / "doc-to-audio.py"

    if not doc_to_audio.exists():
        print(f"Error: doc-to-audio.py not found at {doc_to_audio}")
        sys.exit(1)

    # Build command
    cmd = [
        str(doc_to_audio),
        "--input",
        str(input_path),
        "--output",
        args.output,
        "--provider",
        args.provider,
        "--multi-voice",
        "--narrative",  # Strip headers/metadata for drama content
        "--narrator",
        args.narrator,
    ]

    if args.advanced_mixing:
        cmd.append("--advanced-mixing")

    if args.conservative_pauses:
        cmd.append("--conservative-multivoice")

    print(f"\nRunning: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=True)
        print("\n✓ Audio generation complete!")
        print(f"Output directory: {args.output}")
    except subprocess.CalledProcessError as e:
        print(f"\nError: Audio generation failed with code {e.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
