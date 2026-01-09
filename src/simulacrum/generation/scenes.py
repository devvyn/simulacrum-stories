#!/usr/bin/env python3
"""
Scene Generator for Simulacrum Worlds

Generates dramatic scenes from world state using Claude API.

Usage:
    # Generate from world state JSON
    ./generate_scene.py --world world-state.json --template confrontation --output scene.md

    # Generate with custom characters and context
    ./generate_scene.py --characters sheriff sarah jack --context "investigating a fire" \
        --template group_discussion --output scene.md

    # Quick test generation
    ./generate_scene.py --demo --output demo-scene.md
"""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import assert_never

from simulacrum.types import (
    SceneTemplate,
    EndingType,
    is_character_dict,
    is_world_state_dict,
)

# Anthropic API
try:
    import anthropic

    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# Model configuration
MODEL_SONNET = "claude-sonnet-4-20250514"
MODEL_HAIKU = "claude-haiku-4-20250514"


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class Character:
    """Character profile for scene generation"""

    name: str
    role: str = "supporting"
    personality: list[str] = field(default_factory=list)
    secrets: list[str] = field(default_factory=list)
    knowledge: list[str] = field(default_factory=list)  # What this character knows
    voice_characteristics: str = ""
    gender: str = "unknown"
    age: str = "middle"

    def to_prompt(self) -> str:
        """Format for LLM prompt"""
        traits = ", ".join(self.personality) if self.personality else "unassuming"
        knows = ", ".join(self.knowledge) if self.knowledge else "nothing special"
        return (
            f"- **{self.name}** ({self.role}): Personality: {traits}. Knows: {knows}."
        )


@dataclass
class WorldState:
    """World state for scene generation"""

    town_name: str = "Millbrook"
    time_period: str = "1952"
    characters: list[Character] = field(default_factory=list)
    recent_events: list[str] = field(default_factory=list)
    secrets: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: dict) -> "WorldState":
        """Load from JSON data with type validation."""
        # Validate structure at boundary
        if not is_world_state_dict(data):
            raise ValueError("Invalid world state JSON structure")

        characters = []
        for char_data in data.get("characters", []):
            if not is_character_dict(char_data):
                raise ValueError(f"Invalid character data: {char_data}")
            characters.append(
                Character(
                    name=char_data["name"],
                    role=char_data.get("role", "supporting"),
                    personality=char_data.get("personality", []),
                    secrets=char_data.get("secrets", []),
                    knowledge=char_data.get("knowledge", []),
                    voice_characteristics=char_data.get("voice_characteristics", ""),
                    gender=char_data.get("gender", "unknown"),
                    age=str(char_data.get("age", "middle")),
                )
            )

        return cls(
            town_name=data.get("town", {}).get("name", "Millbrook"),
            time_period=data.get("town", {}).get("time_period", "1952"),
            characters=characters,
            recent_events=[e["description"] for e in data.get("events", [])],
            secrets=[s["description"] for s in data.get("secrets", [])],
            locations=data.get("locations", []),
        )

    @classmethod
    def demo(cls) -> "WorldState":
        """Create demo world state for testing"""
        return cls(
            town_name="Millbrook",
            time_period="1952",
            characters=[
                Character(
                    name="Sheriff",
                    role="authority",
                    personality=["authoritative", "suspicious", "direct"],
                    knowledge=["fire at bakery", "someone was seen leaving early"],
                    gender="male",
                    age="middle",
                ),
                Character(
                    name="Sarah",
                    role="educator",
                    personality=["cautious", "precise", "conflicted"],
                    secrets=["saw someone at the bakery at dawn"],
                    knowledge=["mysterious figure at dawn", "container being carried"],
                    gender="female",
                    age="young",
                ),
                Character(
                    name="Jack",
                    role="service",
                    personality=["casual", "nervous", "evasive"],
                    secrets=["also saw the figure", "knows who it was"],
                    knowledge=["figure at 5am", "Peterson had enemies"],
                    gender="male",
                    age="middle",
                ),
            ],
            recent_events=[
                "Peterson's bakery burned down at dawn",
                "No one was injured but the building was destroyed",
                "Someone was seen leaving early",
            ],
            secrets=[
                "Someone started the fire deliberately",
                "Multiple witnesses are staying quiet",
            ],
            locations=["General Store", "Bakery ruins", "Sheriff's Office", "School"],
        )


# =============================================================================
# Scene Templates
# =============================================================================

# Import extended templates
try:
    from extended_templates import (
        EXTENDED_TEMPLATES,
        get_extended_template,
        get_recommended_template,
    )

    HAS_EXTENDED = True
except ImportError:
    HAS_EXTENDED = False
    EXTENDED_TEMPLATES = {}

def get_template_text(template: SceneTemplate) -> str:
    """
    Get template text with exhaustive matching.

    Uses assert_never to ensure all SceneTemplate values are handled.
    If a new template is added to the Literal type but not here,
    the type checker will report an error.
    """
    match template:
        case "confrontation":
            return SCENE_TEMPLATES["confrontation"]
        case "discovery":
            return SCENE_TEMPLATES["discovery"]
        case "group_discussion":
            return SCENE_TEMPLATES["group_discussion"]
        case "revelation":
            return SCENE_TEMPLATES["revelation"]
        case _:
            assert_never(template)


SCENE_TEMPLATES = {
    "confrontation": """
Scene Template: Private Confrontation
Dramatic Function: Rising action, revelation
Participants: 2-3 characters (confronter, confronted, optional witness)

Structure:
1. NARRATOR: Location description, atmospheric setup
2. CONFRONTER: Opening accusation or question
3. CONFRONTED: Defensive response (evasive)
4. NARRATOR: Body language description
5. CONFRONTER: Pressing harder, citing specific evidence
6. CONFRONTED: Emotional response (confession or further denial)
7. (Optional) WITNESS: Third perspective
8. NARRATOR: Resolution setup or cliffhanger
""",
    "discovery": """
Scene Template: Evidence Discovery
Dramatic Function: Inciting incident, complication
Participants: 1-2 characters (discoverer, optional companion)

Structure:
1. NARRATOR: Time of day, location, what character was doing
2. DISCOVERER: Surprised internal monologue or exclamation
3. NARRATOR: Object/evidence description, why it matters
4. DISCOVERER: Decision about what to do next
5. (Optional) COMPANION: Reaction or advice
6. NARRATOR: Ominous close
""",
    "group_discussion": """
Scene Template: Group Discussion
Dramatic Function: Exposition, debate, rising tension
Participants: 3+ characters with different perspectives

Structure:
1. NARRATOR: Gathering description, who is present
2. CHARACTER_1: Opening statement about the topic
3. CHARACTER_2: Agreement or disagreement (personality-driven)
4. CHARACTER_3: Third perspective or complication
5. NARRATOR: Tension escalation or consensus building
6. CHARACTER_1: Concluding statement or decision
7. NARRATOR: What happens next setup
""",
    "revelation": """
Scene Template: Secret Revelation
Dramatic Function: Climax, turning point
Participants: 2-3 characters (revealer, recipient, optional witness)

Structure:
1. NARRATOR: Charged atmosphere, stakes
2. REVEALER: Building to confession
3. RECIPIENT: Prompting or waiting
4. REVEALER: The secret revealed (emotional)
5. RECIPIENT: Reaction (shock, anger, understanding)
6. NARRATOR: Impact of revelation on relationships
7. (Optional) WITNESS: External perspective
8. NARRATOR: New status quo
""",
}


# =============================================================================
# Scene Generator
# =============================================================================


class SceneGenerator:
    """Generate dramatic scenes using Claude API"""

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
        world: WorldState,
        template: str = "confrontation",
        participants: list[str] | None = None,
        location: str = "",
        context: str = "",
        emotional_tone: str = "tense",
        ending_type: str = "cliffhanger",
        pov_character: str | None = None,
        use_extended: bool = False,
    ) -> str:
        """
        Generate a scene from world state.

        Args:
            world: World state with characters and context
            template: Scene template type
            participants: Character names to include (defaults to all)
            location: Scene location
            context: Additional context for the scene
            emotional_tone: Emotional tone (tense, warm, mysterious, etc.)
            ending_type: How to end (cliffhanger, resolution, revelation)
            pov_character: Character name for POV narration (filters through their knowledge)
            use_extended: Use extended templates for longer episodes (15-25 min)

        Returns:
            Markdown scene with voice tags
        """

        # Get template (extended if requested and available)
        if use_extended and HAS_EXTENDED:
            # Try to map short template name to extended version
            extended_map = {
                "confrontation": "three_act_mystery",
                "discovery": "three_act_mystery",
                "investigation": "dual_perspective_investigation",
                "group_discussion": "ensemble_community_crisis",
                "revelation": "three_act_mystery",
            }
            extended_name = extended_map.get(template, "three_act_mystery")
            template_text = EXTENDED_TEMPLATES.get(
                extended_name,
                SCENE_TEMPLATES.get(template, SCENE_TEMPLATES["group_discussion"]),
            )
            print(f"Using extended template: {extended_name}", file=sys.stderr)
        else:
            template_text = SCENE_TEMPLATES.get(
                template, SCENE_TEMPLATES["group_discussion"]
            )

        # Select participants
        if participants:
            chars = [c for c in world.characters if c.name in participants]
        else:
            chars = world.characters

        # Find POV character if specified
        pov_char = None
        if pov_character:
            for c in world.characters:
                if pov_character.lower() in c.name.lower():
                    pov_char = c
                    break

        # Build prompt
        prompt = self._build_prompt(
            world=world,
            characters=chars,
            template_text=template_text,
            location=location
            or (world.locations[0] if world.locations else "the town square"),
            context=context,
            emotional_tone=emotional_tone,
            ending_type=ending_type,
            pov_char=pov_char,
            use_extended=use_extended,
        )

        # Call Claude with higher max_tokens for extended scenes (2250-3750 words)
        # User priority: max audio budget > optimize LLM token usage
        response = self.client.messages.create(
            model=MODEL_SONNET,
            max_tokens=5000,  # Allows for 3000+ word scenes (increased from 2000)
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def _build_prompt(
        self,
        world: WorldState,
        characters: list[Character],
        template_text: str,
        location: str,
        context: str,
        emotional_tone: str,
        ending_type: str,
        pov_char: Character | None = None,
        use_extended: bool = False,
    ) -> str:
        """Build the scene generation prompt"""

        char_descriptions = "\n".join(c.to_prompt() for c in characters)
        events_text = "\n".join(f"- {e}" for e in world.recent_events[:5])
        secrets_text = "\n".join(f"- {s}" for s in world.secrets[:3])

        # POV-specific instructions
        pov_instructions = ""
        if pov_char:
            pov_knowledge = (
                "\n".join(f"- {k}" for k in pov_char.knowledge)
                if pov_char.knowledge
                else "- General town knowledge only"
            )
            pov_secrets = (
                "\n".join(f"- {s}" for s in pov_char.secrets)
                if pov_char.secrets
                else "- None"
            )
            pov_instructions = f"""
## POINT OF VIEW: {pov_char.name}

**THIS IS CRITICAL**: This scene is told from {pov_char.name}'s perspective.

### What {pov_char.name} KNOWS:
{pov_knowledge}

### {pov_char.name}'s SECRET(S) (influences behavior, internal conflict):
{pov_secrets}

### POV Narration Requirements:
1. **Narrator voice = {pov_char.name}'s internal perspective**
   - Use NARRATOR tags but write as if we're inside {pov_char.name}'s head
   - Show their observations, reactions, suspicions, fears
   - They can only describe what they perceive (not others' thoughts)

2. **Limited Knowledge**:
   - {pov_char.name} can ONLY know/reference things in their knowledge list
   - If others discuss things {pov_char.name} doesn't know, show confusion/curiosity
   - Dramatic irony: audience may know more than the POV character

3. **Internal Reactions**:
   - Include {pov_char.name}'s internal thoughts in narrator sections
   - Show their emotional reactions to others' words
   - Their secrets create internal tension even when not speaking

4. **Personality Filter**: {", ".join(pov_char.personality)}
   - All observations colored by these traits
   - A suspicious character notices threats; a lonely character notices connections

"""

        return f"""You are a dramatic scene writer for audio stories. Generate a scene with multi-voice dialogue.
{pov_instructions}

## World Context
**Town**: {world.town_name}
**Time Period**: {world.time_period}
**Location**: {location}

## Recent Events
{events_text}

## Underlying Secrets (not all characters know these)
{secrets_text}

## Characters in This Scene
{char_descriptions}

## Scene Template
{template_text}

**CRITICAL**: Follow the scene template's structure and length targets precisely. Extended templates specify 2,250-3,000 words minimum - this is a hard requirement for proper pacing and audio runtime.

## Requirements

1. **Voice Tags** (CRITICAL - use EXACTLY this format):
   - Narrator: `<VOICE:NARRATOR>text</VOICE:NARRATOR>`
   - Characters: `<VOICE:CHARACTER_Name>text</VOICE:CHARACTER_Name>` (MUST include CHARACTER_ prefix!)
   - Emotional tone hints: `<VOICE:CHARACTER_Name tone="nervous">text</VOICE:CHARACTER_Name>`
   - Example: Sheriff speaks → `<VOICE:CHARACTER_Sheriff>dialogue</VOICE:CHARACTER_Sheriff>`
   - Example: Sarah with tone → `<VOICE:CHARACTER_Sarah tone="cautious">dialogue</VOICE:CHARACTER_Sarah>`

2. **Character Consistency**:
   - Each character speaks according to their personality
   - Characters can ONLY reference things they know (check their knowledge)
   - Secrets influence behavior but aren't revealed unless dramatically appropriate

3. **Scene Structure**:
   - Start with NARRATOR setting the scene
   - Alternate dialogue with brief narrator beats
   - Include physical/atmospheric descriptions
   - End with: {ending_type}

4. **Tone**: {emotional_tone}

5. **Context**: {context or 'General dramatic tension from recent events'}

## Output

Generate the scene in Markdown format with voice tags. Include:
1. A title (# heading)
2. Brief metadata (characters, setting, tone)
3. The scene itself with voice tags
4. (Optional) A "---" separator and brief scene metadata at the end

Begin:"""


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Generate dramatic scenes from world state"
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--world", help="World state JSON file")
    input_group.add_argument("--demo", action="store_true", help="Use demo world state")

    # Scene options
    parser.add_argument(
        "--template",
        default="confrontation",
        choices=list(SCENE_TEMPLATES.keys()),
        help="Scene template (default: confrontation)",
    )
    parser.add_argument("--participants", nargs="+", help="Character names to include")
    parser.add_argument("--location", default="", help="Scene location")
    parser.add_argument(
        "--context", default="", help="Additional context for the scene"
    )
    parser.add_argument(
        "--tone", default="tense", help="Emotional tone (tense, warm, mysterious, etc.)"
    )
    parser.add_argument(
        "--ending",
        default="cliffhanger",
        choices=["cliffhanger", "resolution", "revelation", "unresolved"],
        help="How to end the scene",
    )
    parser.add_argument(
        "--pov",
        help="Character name for point-of-view narration (filters world through their knowledge)",
    )

    # Output
    parser.add_argument(
        "--output", "-o", default="-", help="Output file (default: stdout)"
    )

    args = parser.parse_args()

    # Load world state
    if args.demo:
        world = WorldState.demo()
        print("Using demo world state...", file=sys.stderr)
    else:
        with open(args.world) as f:
            data = json.load(f)
        world = WorldState.from_json(data)
        print(f"Loaded world: {world.town_name}", file=sys.stderr)

    # Generate scene
    pov_msg = f" (POV: {args.pov})" if args.pov else ""
    print(f"Generating {args.template} scene{pov_msg}...", file=sys.stderr)

    generator = SceneGenerator()
    scene = generator.generate(
        world=world,
        template=args.template,
        participants=args.participants,
        location=args.location,
        context=args.context,
        emotional_tone=args.tone,
        ending_type=args.ending,
        pov_character=args.pov,
    )

    # Output
    if args.output == "-":
        print(scene)
    else:
        Path(args.output).write_text(scene)
        print(f"Scene written to: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
