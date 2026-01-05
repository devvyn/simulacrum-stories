#!/usr/bin/env python3
"""
Launch Batch Production - Week 1 Content

Generates the 4-episode launch batch:
1. Trailer (2 min)
2. Saltmere Episode 1 (23 min)
3. Millbrook Episode 1 (23 min)
4. Bonus Vignette (7 min)

Usage:
    ./launch-batch.py --output ~/Documents/Simulacrum-Stories/
"""

import argparse
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from simulacrum.calendar import ContentCalendar, ScheduledEpisode
from simulacrum.generation.mini_episodes import MiniEpisodeGenerator
from simulacrum.generation.multipass import MultiPassSceneGenerator
from simulacrum.generation.world import WorldGenerator
from simulacrum.cost_tracker import CostCalculator


def generate_trailer(output_dir: Path) -> Path:
    """Generate 2-minute trailer"""
    print("\n" + "="*80)
    print("GENERATING TRAILER")
    print("="*80 + "\n")

    trailer_content = """# Welcome to Simulacrum Stories

<VOICE:NARRATOR>In a world where artificial intelligence meets the art of storytelling, Simulacrum Stories brings you emotionally authentic audio drama - generated through advanced narrative systems, shaped by real human relationships.

Two series. Two worlds. Countless untold stories.

Saltmere Chronicles: A 1970s coastal fishing village where tradition and change collide beneath the lighthouse's watchful gaze.

Millbrook Chronicles: A 1980s rust belt town where mill closures expose secrets that run deeper than economic hardship.

[pause]

Every week, experience literary-quality audio drama featuring dynamic characters, emotional depth, and stories that surprise even their creator.

This is Simulacrum Stories - where AI creativity serves human emotion.

Subscribe now. Your next obsession starts Monday.</VOICE:NARRATOR>
"""

    trailer_file = output_dir / "Trailer-Simulacrum-Stories.md"
    trailer_file.write_text(trailer_content)

    print(f"✅ Trailer written to: {trailer_file}")
    return trailer_file


def generate_main_episode(
    series_name: str,
    episode_num: int,
    output_dir: Path,
    provider: str = "macos"
) -> Path:
    """Generate a main episode using multi-pass system"""
    print(f"\n" + "="*80)
    print(f"GENERATING {series_name.upper()} EPISODE {episode_num}")
    print("="*80 + "\n")

    # Initialize world
    world_gen = WorldGenerator()

    # Series-specific settings
    if series_name == "saltmere":
        setting = "Coastal fishing village in Maine"
        time_period = "1970s"
        characters_data = [
            {"name": "Marcus Chen", "role": "lighthouse keeper", "traits": "observant, haunted by loss", "gender": "male"},
            {"name": "Sarah Peterson", "role": "marine biologist", "traits": "determined, idealistic", "gender": "female"},
            {"name": "Tom Morrison", "role": "fishing boat captain", "traits": "traditional, protective", "gender": "male"},
        ]
    else:  # millbrook
        setting = "Industrial town in Pennsylvania"
        time_period = "1980s"
        characters_data = [
            {"name": "Elena Rodriguez", "role": "union organizer", "traits": "fierce, compassionate", "gender": "female"},
            {"name": "Jack Morrison", "role": "mill worker", "traits": "loyal, conflicted", "gender": "male"},
            {"name": "Sheriff Frank Donovan", "role": "local sheriff", "traits": "methodical, moral", "gender": "male"},
        ]

    world = world_gen.create_from_description(
        setting=setting,
        time_period=time_period,
        characters=characters_data,
        themes=["community", "change", "secrets"]
    )

    # Generate episode with multi-pass
    multipass = MultiPassSceneGenerator()

    # Episode 1 specific contexts
    context = f"This is the pilot episode. Establish the world, introduce main characters, set up central mystery. Episode 1 of {series_name} Chronicles."

    scene, metadata = multipass.generate_episode(
        world=world,
        template_suggestion="discovery" if episode_num == 1 else "revelation",
        context=context,
        target_words=2500,
    )

    # Calculate cost
    calculator = CostCalculator()
    cost_info = calculator.calculate(
        input_tokens=metadata['total_tokens']['input'],
        output_tokens=metadata['total_tokens']['output'],
        characters=len(scene),
        tts_provider=provider
    )

    print(f"  💰 Cost: {cost_info}")

    # Save scene
    scene_file = output_dir / f"{series_name.capitalize()}-E{episode_num:02d}-scene.md"
    scene_file.write_text(scene)

    print(f"✅ Episode written to: {scene_file}")
    return scene_file


def generate_vignette(
    series_name: str,
    character_name: str,
    moment: str,
    output_dir: Path,
    provider: str = "macos"
) -> Path:
    """Generate a bonus character vignette"""
    print(f"\n" + "="*80)
    print(f"GENERATING BONUS VIGNETTE: {character_name}")
    print("="*80 + "\n")

    # Initialize world (simplified for vignette)
    world_gen = WorldGenerator()

    if series_name == "saltmere":
        setting = "Coastal fishing village in Maine"
        time_period = "1970s"
        characters_data = [
            {"name": "Marcus Chen", "role": "lighthouse keeper", "traits": "observant, haunted by loss, poetic", "gender": "male"},
        ]
    else:
        setting = "Industrial town in Pennsylvania"
        time_period = "1980s"
        characters_data = [
            {"name": "Elena Rodriguez", "role": "union organizer", "traits": "fierce, compassionate, determined", "gender": "female"},
        ]

    world = world_gen.create_from_description(
        setting=setting,
        time_period=time_period,
        characters=characters_data,
        themes=["memory", "belonging", "identity"]
    )

    # Generate vignette with mini-episode system
    mini_gen = MiniEpisodeGenerator()

    scene, metadata = mini_gen.generate_vignette(
        character_name=character_name,
        moment_description=moment,
        world=world,
        context="This is a bonus episode - intimate character study, standalone story",
        target_chars=2500,
    )

    # Calculate cost
    calculator = CostCalculator()
    cost_info = calculator.calculate(
        input_tokens=metadata['total_tokens']['input'],
        output_tokens=metadata['total_tokens']['output'],
        characters=len(scene),
        tts_provider=provider
    )

    print(f"  💰 Cost: {cost_info}")

    # Save scene
    scene_file = output_dir / f"BONUS-{character_name.replace(' ', '-')}-scene.md"
    scene_file.write_text(scene)

    print(f"✅ Vignette written to: {scene_file}")
    return scene_file


def main():
    parser = argparse.ArgumentParser(description="Generate Week 1 launch batch")
    parser.add_argument(
        "--output",
        default="~/Documents/Simulacrum-Stories/Launch-Batch",
        help="Output directory for generated content"
    )
    parser.add_argument(
        "--provider",
        choices=["macos", "openai", "elevenlabs"],
        default="macos",
        help="TTS provider (default: macos for testing)"
    )
    parser.add_argument(
        "--skip-trailer",
        action="store_true",
        help="Skip trailer generation"
    )

    args = parser.parse_args()

    output_dir = Path(args.output).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"LAUNCH BATCH PRODUCTION")
    print(f"Output: {output_dir}")
    print(f"Provider: {args.provider}")
    print(f"{'='*80}\n")

    total_cost = 0.0

    # 1. Generate Trailer
    if not args.skip_trailer:
        generate_trailer(output_dir)
        total_cost += 0.02  # Estimated trailer cost

    # 2. Generate Saltmere Episode 1
    generate_main_episode("saltmere", 1, output_dir, args.provider)
    total_cost += 0.27

    # 3. Generate Millbrook Episode 1
    generate_main_episode("millbrook", 1, output_dir, args.provider)
    total_cost += 0.27

    # 4. Generate Bonus Vignette
    generate_vignette("saltmere", "Marcus Chen", "First Time Seeing the Ocean", output_dir, args.provider)
    total_cost += 0.07

    print(f"\n{'='*80}")
    print(f"LAUNCH BATCH COMPLETE!")
    print(f"Total Estimated Cost: ${total_cost:.2f}")
    print(f"Files saved to: {output_dir}")
    print(f"{'='*80}\n")

    print("\nNext Steps:")
    print("1. Generate audio: ./scripts/doc-to-audio.py --input <scene-file> --provider", args.provider)
    print("2. Publish to RSS feed: ./scripts/publish-feeds.sh")
    print("3. Update content calendar: Mark episodes as 'produced'")


if __name__ == "__main__":
    main()
