#!/usr/bin/env python3
"""
World Generator for Simulacrum Stories

Generates rich world states (towns, characters, events, secrets) using Claude API.

Usage:
    # Generate a 1950s American small town
    ./generate_world.py --setting "1950s American small town" --output world.json

    # Generate a noir detective setting
    ./generate_world.py --setting "1940s noir Chicago" --characters 7 --events 15 --output noir-world.json

    # Generate with specific themes
    ./generate_world.py --setting "Medieval village" --themes "plague mystery betrayal" --output village.json
"""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime

try:
    import anthropic

    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class Character:
    """A character in the world"""

    name: str
    age: int
    gender: str
    role: str
    occupation: str
    personality: list[str]
    secrets: list[str]
    knowledge: list[str]
    relationships: dict[str, str]  # character_name → relationship_type
    voice_characteristics: str
    backstory: str


@dataclass
class Event:
    """A significant event in the world's history"""

    date: str
    description: str
    participants: list[str]
    witnesses: list[str]
    significance: str  # "high", "medium", "low"
    consequences: list[str]


@dataclass
class Secret:
    """A secret that drives drama"""

    description: str
    known_by: list[str]
    consequences_if_revealed: str
    dramatic_potential: str


@dataclass
class Location:
    """A significant location"""

    name: str
    description: str
    atmosphere: str
    associated_characters: list[str]


@dataclass
class World:
    """Complete world state"""

    name: str
    time_period: str
    population: int
    economy: str
    atmosphere: str
    characters: list[Character]
    events: list[Event]
    secrets: list[Secret]
    locations: list[Location]
    themes: list[str]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "town": {
                "name": self.name,
                "time_period": self.time_period,
                "population": self.population,
                "economy": self.economy,
                "atmosphere": self.atmosphere,
            },
            "characters": [asdict(c) for c in self.characters],
            "events": [asdict(e) for e in self.events],
            "secrets": [asdict(s) for s in self.secrets],
            "locations": [asdict(l) for l in self.locations],
            "themes": self.themes,
            "generated_at": self.generated_at,
        }

    def save(self, path: str) -> None:
        """Save world to JSON file"""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


# =============================================================================
# World Generator
# =============================================================================


class WorldGenerator:
    """Generate rich world states using Claude API"""

    def __init__(self, api_key: str | None = None):
        if not HAS_ANTHROPIC:
            raise ImportError("anthropic package required: pip install anthropic")

        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            self.api_key = self._get_api_key_from_keychain()

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        self.client = anthropic.Anthropic(api_key=self.api_key)

    def _get_api_key_from_keychain(self) -> str | None:
        """Try to get API key from macOS keychain"""
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-s", "ANTHROPIC_API_KEY", "-w"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def generate(
        self,
        setting: str = "1950s American small town",
        num_characters: int = 5,
        num_events: int = 10,
        num_secrets: int = 3,
        themes: list[str] | None = None,
        relationship_hints: list[dict] | None = None,
    ) -> World:
        """
        Generate a complete world state.

        Args:
            setting: Description of the setting (time period, location type)
            num_characters: Number of characters to generate (5-10 recommended)
            num_events: Number of historical events (10-20 recommended)
            num_secrets: Number of secrets (3-5 recommended)
            themes: Optional list of themes to incorporate
            relationship_hints: Optional relationship patterns from real signals

        Returns:
            Complete World object
        """

        prompt = self._build_prompt(
            setting=setting,
            num_characters=num_characters,
            num_events=num_events,
            num_secrets=num_secrets,
            themes=themes or ["mystery", "community", "secrets"],
            relationship_hints=relationship_hints,
        )

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse the JSON response
        response_text = response.content[0].text

        # Extract JSON from response (may be wrapped in ```json ... ```)
        import re

        json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            json_text = response_text

        data = json.loads(json_text)
        return self._parse_world(data)

    def _build_prompt(
        self,
        setting: str,
        num_characters: int,
        num_events: int,
        num_secrets: int,
        themes: list[str],
        relationship_hints: list[dict] | None = None,
    ) -> str:
        """Build the world generation prompt"""

        # Build relationship inspiration section if hints provided
        relationship_section = ""
        if relationship_hints:
            relationship_section = """

## Relationship Dynamics (REAL patterns to incorporate)

Base character relationships on these REAL relationship patterns extracted from actual communications.
These are privacy-safe signals—no names or content, just dynamics. Use them as inspiration:

"""
            for hint in relationship_hints:
                dyn = hint.get("suggested_dynamic", {})
                metrics = hint.get("metrics_inspiration", {})
                seeds = hint.get("story_seeds", ["A relationship with hidden depths"])
                relationship_section += f"""### Pattern {hint.get('relationship_template', '?')}: {hint.get('archetype', 'unknown').replace('_', ' ').title()}
- **Dynamic**: {dyn.get('warmth', 'neutral')} warmth, {dyn.get('power_balance', 'equal')} power balance
- **Communication**: {dyn.get('communication_frequency', 'regular').replace('_', ' ')}
- **Tension Level**: {dyn.get('tension_level', 'low')}
- **Story Seeds**: {'; '.join(seeds)}
- **History**: {metrics.get('years_of_history', '?')} years, {'active' if metrics.get('currently_active') else 'faded'}

"""

        return f"""You are a world-builder for dramatic audio stories. Generate a rich, interconnected world.

## Setting
{setting}

## Requirements

Generate a world with:
- {num_characters} main characters with depth and interconnected relationships
- {num_events} historical events (backstory that creates drama potential)
- {num_secrets} secrets that could drive plot
- 4-6 key locations
{relationship_section}
## Themes to Incorporate
{', '.join(themes)}

## Character Guidelines
Each character needs:
- Distinct personality (3-4 traits)
- At least 1 secret
- Specific knowledge (what they know that others don't)
- Relationships with 2-3 other characters
- Voice characteristics for audio (e.g., "deep, gravelly, measured speech")
- Brief backstory (2-3 sentences)

Ensure diverse:
- Ages (young, middle, old)
- Genders (balanced)
- Roles (authority, educator, service, outsider, etc.)
- Occupations

## Event Guidelines
Events should:
- Create causality chains (event A leads to event B)
- Involve multiple characters
- Include at least 2 "high significance" events
- Build toward dramatic potential

## Secret Guidelines
Secrets should:
- Create tension between characters
- Have high stakes if revealed
- Be known by only 1-2 characters

## Output Format
Return ONLY valid JSON in this exact structure:

```json
{{
  "town": {{
    "name": "...",
    "time_period": "...",
    "population": 300,
    "economy": "...",
    "atmosphere": "..."
  }},
  "characters": [
    {{
      "name": "...",
      "age": 45,
      "gender": "male|female",
      "role": "authority|educator|service|outsider|merchant|...",
      "occupation": "...",
      "personality": ["...", "...", "..."],
      "secrets": ["..."],
      "knowledge": ["...", "..."],
      "relationships": {{"character_name": "relationship_type"}},
      "voice_characteristics": "...",
      "backstory": "..."
    }}
  ],
  "events": [
    {{
      "date": "YYYY-MM-DD or relative like '3 months ago'",
      "description": "...",
      "participants": ["character_name"],
      "witnesses": ["character_name"],
      "significance": "high|medium|low",
      "consequences": ["..."]
    }}
  ],
  "secrets": [
    {{
      "description": "...",
      "known_by": ["character_name"],
      "consequences_if_revealed": "...",
      "dramatic_potential": "..."
    }}
  ],
  "locations": [
    {{
      "name": "...",
      "description": "...",
      "atmosphere": "...",
      "associated_characters": ["..."]
    }}
  ],
  "themes": {json.dumps(themes)}
}}
```

Generate a rich, dramatically interesting world with complex character relationships and secrets that could fuel multiple story arcs."""

    def _parse_world(self, data: dict) -> World:
        """Parse JSON data into World object"""

        town = data.get("town", {})

        characters = [
            Character(
                name=c["name"],
                age=c.get("age", 40),
                gender=c.get("gender", "unknown"),
                role=c.get("role", "supporting"),
                occupation=c.get("occupation", "unknown"),
                personality=c.get("personality", []),
                secrets=c.get("secrets", []),
                knowledge=c.get("knowledge", []),
                relationships=c.get("relationships", {}),
                voice_characteristics=c.get("voice_characteristics", ""),
                backstory=c.get("backstory", ""),
            )
            for c in data.get("characters", [])
        ]

        events = [
            Event(
                date=e.get("date", "unknown"),
                description=e["description"],
                participants=e.get("participants", []),
                witnesses=e.get("witnesses", []),
                significance=e.get("significance", "medium"),
                consequences=e.get("consequences", []),
            )
            for e in data.get("events", [])
        ]

        secrets = [
            Secret(
                description=s["description"],
                known_by=s.get("known_by", []),
                consequences_if_revealed=s.get("consequences_if_revealed", ""),
                dramatic_potential=s.get("dramatic_potential", ""),
            )
            for s in data.get("secrets", [])
        ]

        locations = [
            Location(
                name=l["name"],
                description=l.get("description", ""),
                atmosphere=l.get("atmosphere", ""),
                associated_characters=l.get("associated_characters", []),
            )
            for l in data.get("locations", [])
        ]

        return World(
            name=town.get("name", "Unknown Town"),
            time_period=town.get("time_period", "Unknown"),
            population=town.get("population", 300),
            economy=town.get("economy", ""),
            atmosphere=town.get("atmosphere", ""),
            characters=characters,
            events=events,
            secrets=secrets,
            locations=locations,
            themes=data.get("themes", []),
        )


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Generate rich world states for dramatic stories"
    )

    parser.add_argument(
        "--setting",
        default="1950s American small town with a recent mysterious fire",
        help="Setting description (time period, location type)",
    )
    parser.add_argument(
        "--characters", type=int, default=5, help="Number of characters (default: 5)"
    )
    parser.add_argument(
        "--events",
        type=int,
        default=10,
        help="Number of historical events (default: 10)",
    )
    parser.add_argument(
        "--secrets", type=int, default=3, help="Number of secrets (default: 3)"
    )
    parser.add_argument(
        "--themes",
        nargs="+",
        default=["mystery", "community", "secrets"],
        help="Themes to incorporate",
    )
    parser.add_argument(
        "--relationship-hints",
        help="JSON file with relationship hints from relationship_signals.py",
    )
    parser.add_argument(
        "--use-real-signals",
        action="store_true",
        help="Auto-extract relationship signals from Messages.app",
    )
    parser.add_argument("--output", "-o", required=True, help="Output JSON file path")

    args = parser.parse_args()

    # Load relationship hints
    relationship_hints = None
    if args.relationship_hints:
        with open(args.relationship_hints) as f:
            relationship_hints = json.load(f)
        print(f"  Loaded {len(relationship_hints)} relationship hints", file=sys.stderr)
    elif args.use_real_signals:
        try:
            from relationship_signals import RelationshipSignalExtractor, NarrativeConverter
            print("  Extracting real relationship signals...", file=sys.stderr)
            extractor = RelationshipSignalExtractor()
            signals = extractor.extract_signals(min_messages=50)
            converter = NarrativeConverter()
            relationship_hints = converter.signals_to_world_hints(signals, count=5)
            print(f"  Extracted {len(relationship_hints)} relationship patterns", file=sys.stderr)
        except Exception as e:
            print(f"  Warning: Could not extract signals: {e}", file=sys.stderr)

    print(f"Generating world: {args.setting}", file=sys.stderr)
    print(f"  Characters: {args.characters}", file=sys.stderr)
    print(f"  Events: {args.events}", file=sys.stderr)
    print(f"  Secrets: {args.secrets}", file=sys.stderr)
    print(f"  Themes: {', '.join(args.themes)}", file=sys.stderr)

    generator = WorldGenerator()
    world = generator.generate(
        setting=args.setting,
        num_characters=args.characters,
        num_events=args.events,
        num_secrets=args.secrets,
        themes=args.themes,
        relationship_hints=relationship_hints,
    )

    world.save(args.output)

    print(f"\n✅ World generated: {world.name}", file=sys.stderr)
    print(f"   Characters: {len(world.characters)}", file=sys.stderr)
    print(f"   Events: {len(world.events)}", file=sys.stderr)
    print(f"   Secrets: {len(world.secrets)}", file=sys.stderr)
    print(f"   Locations: {len(world.locations)}", file=sys.stderr)
    print(f"   Saved to: {args.output}", file=sys.stderr)

    # Print character summary
    print("\n=== Characters ===", file=sys.stderr)
    for c in world.characters:
        print(
            f"  {c.name} ({c.age}, {c.occupation}): {', '.join(c.personality[:2])}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
