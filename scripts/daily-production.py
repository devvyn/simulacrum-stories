#!/usr/bin/env python3
"""
Daily Episode Production System

Generates daily audio drama episodes from simulacrum worlds.

Usage:
    # Generate next episode for a series
    ./daily_production.py --series millbrook --output ~/Music/Simulacrum-Stories/

    # Generate for all active series
    ./daily_production.py --all --output ~/Music/Simulacrum-Stories/

    # Initialize a new series
    ./daily_production.py --init "Saltmere" --setting "1970s coastal fishing village" --output ~/Music/

    # List active series
    ./daily_production.py --list
"""

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

# Import our tools
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from simulacrum.generation.scenes import SceneGenerator, WorldState
from simulacrum.generation.world import WorldGenerator
from simulacrum.generation.signals import NarrativeConverter, RelationshipSignalExtractor

# Import multi-pass generator
try:
    from simulacrum.generation.multipass import MultiPassSceneGenerator
    HAS_MULTIPASS = True
except ImportError:
    HAS_MULTIPASS = False
    MultiPassSceneGenerator = None

# Import cost tracking
try:
    from simulacrum.cost_tracker import CostCalculator
    HAS_COST_TRACKING = True
except ImportError:
    HAS_COST_TRACKING = False
    CostCalculator = None

# Import series-specific signal filtering
try:
    from simulacrum.generation.filters import get_series_context, get_signals_for_series
except ImportError:
    # Graceful fallback if filter module not available
    get_signals_for_series = None
    get_series_context = None


# =============================================================================
# Configuration
# =============================================================================

SERIES_REGISTRY = project_root / "data" / "simulacrum-series.json"
ARTIST_NAME = "Simulacrum Stories"
GENRE = "Audio Drama"


@dataclass
class SeriesState:
    """Tracks state of an ongoing series"""

    name: str
    setting: str
    world_file: str
    episode_count: int
    current_arc: str
    pov_rotation: list[str]  # Characters to rotate POV through
    last_pov_index: int
    scene_templates: list[str]
    themes: list[str]
    created_at: str
    last_episode_at: str | None = None


# =============================================================================
# Series Manager
# =============================================================================


class SeriesManager:
    """Manage multiple ongoing series"""

    def __init__(self, registry_path: Path = SERIES_REGISTRY):
        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.series = self._load_registry()

    def _load_registry(self) -> dict[str, SeriesState]:
        if self.registry_path.exists():
            with open(self.registry_path) as f:
                data = json.load(f)
                return {name: SeriesState(**state) for name, state in data.items()}
        return {}

    def _save_registry(self) -> None:
        with open(self.registry_path, "w") as f:
            json.dump(
                {name: asdict(state) for name, state in self.series.items()},
                f,
                indent=2,
            )

    def create_series(
        self,
        name: str,
        setting: str,
        world_file: str,
        characters: list[str],
        themes: list[str],
    ) -> SeriesState:
        """Create a new series"""
        state = SeriesState(
            name=name,
            setting=setting,
            world_file=world_file,
            episode_count=0,
            current_arc="Season 1",
            pov_rotation=characters,
            last_pov_index=-1,
            scene_templates=[
                "confrontation",
                "discovery",
                "revelation",
                "group_discussion",
            ],
            themes=themes,
            created_at=datetime.now().isoformat(),
        )
        self.series[name.lower()] = state
        self._save_registry()
        return state

    def get_series(self, name: str) -> SeriesState | None:
        return self.series.get(name.lower())

    def list_series(self) -> list[SeriesState]:
        return list(self.series.values())

    def update_episode_count(self, name: str) -> None:
        state = self.series.get(name.lower())
        if state:
            state.episode_count += 1
            state.last_pov_index = (state.last_pov_index + 1) % len(state.pov_rotation)
            state.last_episode_at = datetime.now().isoformat()
            self._save_registry()


# =============================================================================
# Episode Producer
# =============================================================================


class EpisodeProducer:
    """Produce individual episodes"""

    def __init__(self, output_base: Path):
        self.output_base = output_base
        self.scene_gen = SceneGenerator()

    def get_next_pov(self, state: SeriesState) -> str:
        """Get the next POV character in rotation"""
        next_index = (state.last_pov_index + 1) % len(state.pov_rotation)
        return state.pov_rotation[next_index]

    def get_next_template(self, state: SeriesState) -> str:
        """Get scene template based on episode number for variety"""
        templates = state.scene_templates
        return templates[state.episode_count % len(templates)]

    def generate_episode_context(self, state: SeriesState, pov: str) -> str:
        """Generate context for the next episode"""
        contexts = [
            f"{pov} discovers something that changes everything",
            f"A confrontation forces {pov} to make a difficult choice",
            f"{pov} overhears a conversation they weren't meant to hear",
            f"The past catches up with {pov} in an unexpected way",
            f"{pov} must decide whether to reveal what they know",
            f"A visitor arrives with questions about {pov}'s secrets",
            f"{pov} finds evidence that implicates someone they trust",
            f"An old wound reopens for {pov}",
        ]
        return contexts[state.episode_count % len(contexts)]

    def produce_episode(
        self, state: SeriesState, output_dir: Path, use_real_signals: bool = True,
        use_multipass: bool = True, provider: str = "macos"
    ) -> Path:
        """Produce a complete episode

        Args:
            state: Series state
            output_dir: Output directory for episode files
            use_real_signals: Extract relationship signals from iMessage
            use_multipass: Use multi-pass generation for professional quality
            provider: TTS provider (macos, openai, elevenlabs)
        """

        # Load world
        with open(state.world_file) as f:
            world_data = json.load(f)
        world = WorldState.from_json(world_data)

        # Extract series-specific relationship signals for emotional depth
        relationship_context = None
        if use_real_signals and get_signals_for_series:
            try:
                print(
                    f"  Extracting {state.name.lower()} relationship patterns...",
                    file=sys.stderr,
                )
                signals = get_signals_for_series(
                    state.name.lower(), count=3, min_messages=50
                )
                series_context = get_series_context(state.name.lower())

                if signals:
                    relationship_context = {
                        "signals": signals,
                        "period": series_context["period"],
                        "cultural_backdrop": series_context["cultural_backdrop"],
                    }
                    print(
                        f"  Applied {len(signals)} real relationship patterns",
                        file=sys.stderr,
                    )
            except Exception as e:
                print(f"  Warning: Could not extract signals: {e}", file=sys.stderr)

        episode_num = state.episode_count + 1

        # Generate scene with multi-pass or fallback to single-pass
        if use_multipass and HAS_MULTIPASS:
            # Multi-pass generation with dynamic POV
            template = self.get_next_template(state)

            # Get a suggested POV for context generation
            # (multipass will decide actual POV structure)
            suggested_pov = self.get_next_pov(state)
            base_context = self.generate_episode_context(state, suggested_pov)

            print(
                f"  Episode {episode_num}: Multi-pass generation (template suggestion: {template})",
                file=sys.stderr,
            )

            multipass_gen = MultiPassSceneGenerator()
            scene, metadata = multipass_gen.generate_episode(
                world=world,
                template_suggestion=template,
                context=base_context,
                relationship_context=relationship_context,
                target_words=2500,
            )

            # Extract POV info from metadata
            pov_structure = metadata['pov_structure']
            pov_characters = metadata['pov_characters']
            primary_pov = pov_characters[0] if pov_characters else suggested_pov

            print(f"  Generated {pov_structure} POV episode", file=sys.stderr)
            print(f"  POV characters: {', '.join(pov_characters)}", file=sys.stderr)

        else:
            # Fallback to single-pass
            pov = self.get_next_pov(state)
            template = self.get_next_template(state)

            # Enhance context with relationship patterns if available
            base_context = self.generate_episode_context(state, pov)
            if relationship_context and relationship_context["signals"]:
                # Inject a relationship pattern hint into the context
                signal_hint = relationship_context["signals"][0]  # Use first signal
                context = f"{base_context}. Emotional dynamics: {signal_hint.get('suggested_dynamic', {}).get('warmth', 'complex')} warmth, {signal_hint.get('suggested_dynamic', {}).get('power_balance', 'shifting')} power dynamic"
            else:
                context = base_context

            print(
                f"  Episode {episode_num}: POV={pov}, Template={template}", file=sys.stderr
            )

            # Generate scene (use extended templates if supported)
            scene = self.scene_gen.generate(
                world=world,
                template=template,
                pov_character=pov,
                context=context,
                emotional_tone="dramatic" if episode_num % 3 == 0 else "tense",
                ending_type="cliffhanger" if episode_num % 2 == 1 else "revelation",
                use_extended=True,  # Enable extended templates for 15-25 min episodes
            )

            primary_pov = pov
            pov_structure = "single"
            pov_characters = [pov]
            metadata = {}

        # Extract title from scene (first # heading)
        title = "Untitled Episode"
        for line in scene.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Save scene markdown
        scene_file = output_dir / f"E{episode_num:02d}-scene.md"
        scene_file.write_text(scene)

        # Calculate production costs
        cost_info = None
        if HAS_COST_TRACKING and metadata.get('total_tokens'):
            calculator = CostCalculator()
            cost_info = calculator.calculate(
                input_tokens=metadata['total_tokens']['input'],
                output_tokens=metadata['total_tokens']['output'],
                characters=len(scene),  # Scene character count for TTS
                tts_provider=provider
            )
            print(f"  💰 Cost: {cost_info}", file=sys.stderr)

        # Generate audio
        # Note: Advanced mixing disabled for macOS provider due to ffmpeg compatibility issues
        use_mixing = use_multipass and provider != "macos"
        audio_file = self._generate_audio(
            scene_file=scene_file,
            output_dir=output_dir,
            series_name=state.name,
            episode_num=episode_num,
            title=title,
            arc=state.current_arc,
            pov=primary_pov,
            world=world,
            use_advanced_mixing=use_mixing,
            provider=provider,
            cost_info=cost_info,
        )

        return audio_file

    def _select_narrator_voice(self, pov_name: str, world: WorldState, provider: str) -> str:
        """Select narrator voice based on POV character gender and provider"""
        pov_char = next((c for c in world.characters if c.name == pov_name), None)
        is_female = pov_char and pov_char.gender == "female"

        # Provider-specific voice mapping
        if provider == "elevenlabs":
            return "Sarah" if is_female else "George"
        elif provider == "openai":
            return "nova" if is_female else "fable"  # nova=warm female, fable=narrator male
        elif provider == "macos":
            return "Serena" if is_female else "Jamie"  # Serena=UK female, Jamie=UK male
        else:
            return "Jamie"  # Default fallback

    def _generate_audio(
        self,
        scene_file: Path,
        output_dir: Path,
        series_name: str,
        episode_num: int,
        title: str,
        arc: str,
        pov: str,
        world: WorldState,
        use_advanced_mixing: bool = False,
        provider: str = "macos",
        cost_info=None,
    ) -> Path:
        """Generate audio with proper metadata, artwork, and lyrics"""

        # Run doc-to-audio
        temp_dir = output_dir / "temp"
        temp_dir.mkdir(exist_ok=True)

        # Select narrator voice based on POV gender and provider
        narrator_voice = self._select_narrator_voice(pov, world, provider)

        # Build doc-to-audio command with optional advanced mixing
        doc_to_audio_cmd = [
            sys.executable,
            str(project_root / "scripts" / "doc-to-audio.py"),
            "--input",
            str(scene_file),
            "--output",
            str(temp_dir),
            "--provider",
            provider,
            "--multi-voice",
            "--narrator",
            narrator_voice,
            "--narrative",  # Strip metadata for cleaner audio
        ]

        # Add advanced mixing if enabled
        if use_advanced_mixing:
            doc_to_audio_cmd.extend([
                "--advanced-mixing",
                "--crossfade", "0.2",  # Subtle crossfade for music fades only
                # Note: normalization is enabled by default with --advanced-mixing
            ])

        subprocess.run(doc_to_audio_cmd, capture_output=True, check=True)

        # Find generated file
        raw_audio = list(temp_dir.glob("*.mp3"))[0]

        # Extract lyrics (scene text without voice tags)
        scene_text = scene_file.read_text()
        lyrics = self._extract_lyrics(scene_text)

        # Save lyrics to temp file for embedding
        lyrics_file = temp_dir / "lyrics.txt"
        lyrics_file.write_text(lyrics)

        # Get or create album artwork
        artwork_file = self._get_artwork(output_dir, series_name)

        # Re-encode with full metadata including artwork and lyrics
        album_name = f"{series_name} Chronicles: {arc}"
        final_name = f"E{episode_num:02d} - {title}.mp3"
        final_path = output_dir / final_name

        # Build ffmpeg command
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(raw_audio),
        ]

        # Add artwork if available
        if artwork_file and artwork_file.exists():
            cmd.extend(["-i", str(artwork_file)])

        cmd.extend(
            [
                "-acodec",
                "libmp3lame",
                "-b:a",
                "192k",
                "-ar",
                "44100",
                "-ac",
                "2",
            ]
        )

        # Map streams (audio + artwork if present)
        if artwork_file and artwork_file.exists():
            cmd.extend(
                [
                    "-map",
                    "0:a",
                    "-map",
                    "1:v",
                    "-c:v",
                    "copy",
                    "-id3v2_version",
                    "3",
                    "-metadata:s:v",
                    "title=Album cover",
                    "-metadata:s:v",
                    "comment=Cover (front)",
                ]
            )

        cmd.extend(
            [
                "-metadata",
                f"title={title}",
                "-metadata",
                f"artist={ARTIST_NAME}",
                "-metadata",
                f"album={album_name}",
                "-metadata",
                f"album_artist={ARTIST_NAME}",
                "-metadata",
                f"track={episode_num}",
                "-metadata",
                f"genre={GENRE}",
                "-metadata",
                "date=2025",
                "-metadata",
                f"comment=POV: {pov}",
                "-metadata",
                f"lyrics={lyrics[:3000]}",  # Truncate if too long
            ]
        )

        # Add cost information to metadata
        if cost_info:
            cmd.extend([
                "-metadata",
                f"copyright=Production Cost: ${cost_info.total_cost_usd:.4f} (LLM: ${cost_info.llm_cost_usd:.4f}, TTS: ${cost_info.tts_cost_usd:.4f})",
            ])

        cmd.append(str(final_path))

        subprocess.run(cmd, capture_output=True, check=True)

        # Cleanup temp
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        return final_path

    def _extract_lyrics(self, scene_text: str) -> str:
        """Extract readable lyrics from scene markdown"""
        import re

        lines = []
        for line in scene_text.split("\n"):
            # Skip metadata lines
            if line.startswith("**") or line.startswith("---") or line.startswith("#"):
                continue

            # Extract content from voice tags
            # <VOICE:NARRATOR>text</VOICE:NARRATOR> -> [Narrator] text
            narrator_match = re.search(r"<VOICE:NARRATOR>(.*?)</VOICE:NARRATOR>", line)
            if narrator_match:
                lines.append(f"[Narrator] {narrator_match.group(1)}")
                continue

            # <VOICE:CHARACTER_Name tone="x">text</VOICE> -> [Name] text
            char_match = re.search(
                r'<VOICE:CHARACTER_(\w+)(?:\s+tone="([^"]*)")?>(.*?)</VOICE:CHARACTER_\1>',
                line,
            )
            if char_match:
                name = char_match.group(1)
                tone = char_match.group(2)
                text = char_match.group(3)
                if tone:
                    lines.append(f"[{name}, {tone}] {text}")
                else:
                    lines.append(f"[{name}] {text}")
                continue

            # Keep non-empty lines
            if line.strip():
                lines.append(line.strip())

        return "\n".join(lines)

    def _get_artwork(self, output_dir: Path, series_name: str) -> Path | None:
        """Get or create album artwork"""
        # Check for existing artwork
        artwork_patterns = [
            "cover.jpg",
            "cover.png",
            "artwork.jpg",
            "artwork.png",
            "folder.jpg",
        ]
        for pattern in artwork_patterns:
            artwork = output_dir / pattern
            if artwork.exists():
                return artwork

        # Check in series data directory
        data_dir = Path.home() / "devvyn-meta-project" / "data" / "artwork"
        series_artwork = data_dir / f"{series_name.lower()}.jpg"
        if series_artwork.exists():
            return series_artwork

        # Generate placeholder artwork (simple colored square with text)
        placeholder = self._generate_placeholder_artwork(output_dir, series_name)
        return placeholder

    def _generate_placeholder_artwork(self, output_dir: Path, series_name: str) -> Path:
        """Generate simple placeholder artwork using ImageMagick or ffmpeg"""
        artwork_path = output_dir / "cover.jpg"

        # Try to create with ffmpeg (generates solid color with text overlay)
        try:
            # Generate a 500x500 dark gradient background with series name
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=0x1a1a2e:s=500x500:d=1",
                    "-vf",
                    f"drawtext=text='{series_name}':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
                    "-frames:v",
                    "1",
                    str(artwork_path),
                ],
                capture_output=True,
                check=True,
            )
            return artwork_path
        except Exception:
            pass

        return None


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Daily episode production for simulacrum series"
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--series", help="Generate next episode for series")
    mode.add_argument(
        "--all", action="store_true", help="Generate for all active series"
    )
    mode.add_argument("--init", metavar="NAME", help="Initialize a new series")
    mode.add_argument("--list", action="store_true", help="List active series")

    parser.add_argument("--setting", help="Setting for new series (with --init)")
    parser.add_argument("--world", help="Existing world JSON file (with --init)")
    parser.add_argument(
        "--use-real-signals", action="store_true", help="Use real relationship signals"
    )
    parser.add_argument(
        "--provider",
        choices=["macos", "openai", "elevenlabs"],
        default="macos",
        help="TTS provider: macos (free, testing), openai ($11/mo, good quality), elevenlabs (premium, $22+/mo). Default: macos",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=str(Path.home() / "Music" / "Simulacrum-Stories"),
        help="Output directory for audio files",
    )

    args = parser.parse_args()

    manager = SeriesManager()
    output_base = Path(args.output)
    output_base.mkdir(parents=True, exist_ok=True)

    if args.list:
        series_list = manager.list_series()
        if not series_list:
            print("No active series. Use --init to create one.")
            return

        print("=== Active Series ===")
        for s in series_list:
            print(f"\n{s.name} ({s.current_arc})")
            print(f"  Episodes: {s.episode_count}")
            print(f"  Setting: {s.setting}")
            print(f"  POV Rotation: {', '.join(s.pov_rotation)}")
            print(f"  Last Episode: {s.last_episode_at or 'Never'}")

    elif args.init:
        name = args.init
        setting = args.setting or f"Mysterious {name}"

        print(f"Initializing series: {name}", file=sys.stderr)

        # Generate or use existing world
        if args.world:
            world_file = args.world
            with open(world_file) as f:
                world_data = json.load(f)
        else:
            # Generate new world with real signals
            print("  Generating world...", file=sys.stderr)
            generator = WorldGenerator()

            relationship_hints = None
            if args.use_real_signals:
                try:
                    extractor = RelationshipSignalExtractor()
                    signals = extractor.extract_signals(min_messages=50)
                    converter = NarrativeConverter()
                    relationship_hints = converter.signals_to_world_hints(
                        signals, count=5
                    )
                    print(
                        f"  Using {len(relationship_hints)} real relationship patterns",
                        file=sys.stderr,
                    )
                except Exception as e:
                    print(f"  Warning: Could not extract signals: {e}", file=sys.stderr)

            world = generator.generate(
                setting=setting,
                num_characters=5,
                num_events=8,
                num_secrets=3,
                themes=["mystery", "secrets", "community", "redemption"],
                relationship_hints=relationship_hints,
            )

            # Save world
            world_dir = Path.home() / "devvyn-meta-project" / "data" / "worlds"
            world_dir.mkdir(parents=True, exist_ok=True)
            world_file = str(world_dir / f"{name.lower()}-world.json")
            world.save(world_file)

            world_data = world.to_dict()

        # Extract character names for POV rotation
        characters = [c["name"] for c in world_data.get("characters", [])]
        themes = world_data.get("themes", ["mystery"])

        # Create series
        state = manager.create_series(
            name=name,
            setting=setting,
            world_file=world_file,
            characters=characters,
            themes=themes,
        )

        # Create album directory
        album_dir = output_base / f"{name} Chronicles"
        album_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n✅ Series initialized: {name}", file=sys.stderr)
        print(f"   World: {world_file}", file=sys.stderr)
        print(f"   Characters: {', '.join(characters)}", file=sys.stderr)
        print(f"   Album: {album_dir}", file=sys.stderr)

    elif args.series:
        state = manager.get_series(args.series)
        if not state:
            print(f"Series not found: {args.series}")
            print("Use --list to see active series or --init to create one.")
            return

        print(f"Producing episode for: {state.name}", file=sys.stderr)

        album_dir = output_base / f"{state.name} Chronicles"
        album_dir.mkdir(parents=True, exist_ok=True)

        producer = EpisodeProducer(output_base)
        audio_file = producer.produce_episode(state, album_dir, provider=args.provider)

        manager.update_episode_count(state.name.lower())

        print(f"\n✅ Episode produced: {audio_file.name}", file=sys.stderr)
        print(f"   Location: {audio_file}", file=sys.stderr)

    elif args.all:
        series_list = manager.list_series()
        if not series_list:
            print("No active series. Use --init to create one.")
            return

        producer = EpisodeProducer(output_base)

        for state in series_list:
            print(f"\n=== {state.name} ===", file=sys.stderr)

            album_dir = output_base / f"{state.name} Chronicles"
            album_dir.mkdir(parents=True, exist_ok=True)

            audio_file = producer.produce_episode(state, album_dir, provider=args.provider)
            manager.update_episode_count(state.name.lower())

            print(f"  ✅ {audio_file.name}", file=sys.stderr)


if __name__ == "__main__":
    main()
