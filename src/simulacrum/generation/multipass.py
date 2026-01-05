#!/usr/bin/env python3
"""
Multi-Pass Scene Generation for Professional Audio Drama Quality

Implements 4-pass generation:
1. Plot Pass: Structure and dramatic arc with dynamic POV decision
2. Emotional Pass: Tension curve and relationship dynamics
3. Dialogue Pass: Literary prose with character voices
4. Polish Pass: Audio optimization

Usage:
    from simulacrum.generation.multipass import MultiPassSceneGenerator

    generator = MultiPassSceneGenerator()
    scene, metadata = generator.generate_episode(
        world=world_state,
        template_suggestion="three_act_mystery",
        context="recent fire investigation",
        relationship_context=signals,
        target_words=2500,
    )
"""

import anthropic
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from .scenes import Character, WorldState

# Try to import extended templates
try:
    from .templates import EXTENDED_TEMPLATES
    HAS_EXTENDED = True
except ImportError:
    HAS_EXTENDED = False


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class GenerationPass:
    """Result of a single generation pass"""
    pass_name: str
    output: str
    validation_issues: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def token_usage(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


# =============================================================================
# Quality Validators
# =============================================================================


class QualityValidator:
    """Validate scene quality between passes"""

    def validate_plot(self, plot_outline: str) -> tuple[bool, list[str]]:
        """Ensure plot has required structure"""
        issues = []

        # Check for POV structure decision
        if "POV_STRUCTURE:" not in plot_outline.upper():
            issues.append("Missing POV structure decision")

        if "POV_CHARACTERS:" not in plot_outline.upper():
            issues.append("Missing POV characters list")

        # Check for three-act structure
        acts_found = 0
        for act in ["ACT I", "ACT II", "ACT III", "COLD OPEN"]:
            if act in plot_outline.upper():
                acts_found += 1

        if acts_found < 3:
            issues.append(f"Missing act structure (found {acts_found}/4 sections)")

        # Check for hook
        if all(keyword not in plot_outline.lower() for keyword in ["cold open", "hook", "opening"]):
            issues.append("Missing cold open/hook")

        # Check for cliffhanger/ending
        if all(keyword not in plot_outline.lower() for keyword in ["cliffhanger", "ending", "resolution"]):
            issues.append("Missing ending strategy")

        return len(issues) == 0, issues

    def validate_emotional(self, emotional_map: str) -> tuple[bool, list[str]]:
        """Ensure emotional roadmap has tension variation"""
        issues = []

        # Check for tension scores
        if "tension" not in emotional_map.lower():
            issues.append("Missing tension curve")

        # Check for character emotional states
        if "emotional state" not in emotional_map.lower() and "emotion" not in emotional_map.lower():
            issues.append("Missing character emotional tracking")

        # Check for tone attributes
        if "tone" not in emotional_map.lower():
            issues.append("Missing tone attribute recommendations")

        return len(issues) == 0, issues

    def validate_dialogue(self, scene: str, target_words: int) -> tuple[bool, list[str]]:
        """Ensure scene meets quality standards"""
        issues = []

        # Check word count
        word_count = len(scene.split())
        if word_count < target_words * 0.8:
            issues.append(f"Scene too short: {word_count} words (target: {target_words})")

        # Check for voice tags
        if "<VOICE:NARRATOR>" not in scene:
            issues.append("Missing NARRATOR voice tags")
        if "<VOICE:CHARACTER_" not in scene:
            issues.append("Missing CHARACTER voice tags")

        # Check for tone attributes (should have at least some)
        if 'tone="' not in scene:
            issues.append("No tone attributes found - add emotional delivery")

        # Check for proper tag closing
        open_tags = scene.count("<VOICE:")
        close_tags = scene.count("</VOICE:")
        if open_tags != close_tags:
            issues.append(f"Mismatched voice tags: {open_tags} open, {close_tags} close")

        return len(issues) == 0, issues

    def validate_polish(self, polished_scene: str) -> tuple[bool, list[str]]:
        """Ensure audio optimizations applied"""
        issues = []

        # Check for pause tags
        if "[pause]" not in polished_scene and "[long pause]" not in polished_scene:
            issues.append("Missing strategic pause tags")

        # Check for varied tone attributes
        tone_count = polished_scene.count('tone="')
        if tone_count < 3:
            issues.append("Insufficient tone variety (add more emotional delivery)")

        # Check for cold open strength (first 200 words)
        first_200 = " ".join(polished_scene.split()[:200])
        if "NARRATOR" not in first_200:
            issues.append("Cold open lacks narrator atmosphere")

        return len(issues) == 0, issues


# =============================================================================
# Multi-Pass Scene Generator
# =============================================================================


class MultiPassSceneGenerator:
    """Generate scenes using 4-pass pipeline with dynamic POV"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            self.api_key = self._get_api_key_from_keychain()

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.validator = QualityValidator()

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

    def generate_episode(
        self,
        world: WorldState,
        template_suggestion: str,
        context: str,
        relationship_context: dict | None = None,
        target_words: int = 2500,
    ) -> tuple[str, dict]:
        """
        Generate episode using 4-pass pipeline

        Args:
            world: World state with characters and context
            template_suggestion: Suggested template (may be overridden by AI)
            context: Scene context/prompt
            relationship_context: Relationship signals from iMessage analysis
            target_words: Target word count (default: 2500 for 15-20 min)

        Returns:
            (scene_markdown, metadata)

            Metadata includes:
            - pov_structure: "single" | "dual" | "ensemble"
            - pov_characters: list[str]
            - template_used: str
            - pass_results: list of GenerationPass objects
        """

        pass_results = []

        # Pass 1: Plot
        print("  Pass 1/4: Generating plot outline with POV decision...", file=sys.stderr)
        plot_result = self._pass_plot(
            world, template_suggestion, context, relationship_context
        )
        pass_results.append(plot_result)

        is_valid, issues = self.validator.validate_plot(plot_result.output)
        if not is_valid:
            print(f"    ⚠️  Plot issues: {issues}", file=sys.stderr)
            plot_result.validation_issues = issues

        # Extract POV structure from plot output (will extract from scene later if needed)
        pov_info = self._extract_pov_info(plot_result.output)

        # Pass 2: Emotional
        print("  Pass 2/4: Calibrating emotional trajectory...", file=sys.stderr)
        emotional_result = self._pass_emotional(
            world, plot_result.output, pov_info, relationship_context
        )
        pass_results.append(emotional_result)

        is_valid, issues = self.validator.validate_emotional(emotional_result.output)
        if not is_valid:
            print(f"    ⚠️  Emotional issues: {issues}", file=sys.stderr)
            emotional_result.validation_issues = issues

        # Pass 3: Dialogue
        print("  Pass 3/4: Writing scene with literary prose...", file=sys.stderr)
        dialogue_result = self._pass_dialogue(
            world, plot_result.output, emotional_result.output,
            pov_info, target_words
        )
        pass_results.append(dialogue_result)

        is_valid, issues = self.validator.validate_dialogue(dialogue_result.output, target_words)
        if not is_valid:
            print(f"    ⚠️  Dialogue issues: {issues}", file=sys.stderr)
            dialogue_result.validation_issues = issues

        # Pass 4: Polish
        print("  Pass 4/4: Optimizing for audio performance...", file=sys.stderr)
        polish_result = self._pass_polish(
            dialogue_result.output, emotional_result.output
        )
        pass_results.append(polish_result)

        is_valid, issues = self.validator.validate_polish(polish_result.output)
        if not is_valid:
            print(f"    ⚠️  Polish issues: {issues}", file=sys.stderr)
            polish_result.validation_issues = issues

        # Re-extract POV info from final scene if not found in plot
        if not pov_info["characters"]:
            pov_info = self._extract_pov_info(plot_result.output, polish_result.output)
            if pov_info["characters"]:
                print(f"  Extracted POV from scene: {', '.join(pov_info['characters'])}", file=sys.stderr)

        # Log token usage
        total_input = sum(p.input_tokens for p in pass_results)
        total_output = sum(p.output_tokens for p in pass_results)
        print(f"  Token usage: {total_input:,} input, {total_output:,} output", file=sys.stderr)

        # Build metadata
        metadata = {
            "pov_structure": pov_info["structure"],
            "pov_characters": pov_info["characters"],
            "template_used": template_suggestion,  # Could extract from plot if AI changed it
            "pass_results": pass_results,
            "total_tokens": {
                "input": total_input,
                "output": total_output,
            },
        }

        return polish_result.output, metadata

    def _extract_pov_info(self, plot_outline: str, scene: str = "") -> dict:
        """Extract POV structure and characters from plot outline or scene"""
        pov_info = {
            "structure": "single",  # Default
            "characters": [],
        }

        # Look for POV_STRUCTURE: line
        structure_match = re.search(r'POV_STRUCTURE:\s*(\w+)', plot_outline, re.IGNORECASE)
        if structure_match:
            pov_info["structure"] = structure_match.group(1).lower()

        # Look for POV_CHARACTERS: line
        chars_match = re.search(r'POV_CHARACTERS:\s*\[(.*?)\]', plot_outline, re.IGNORECASE | re.DOTALL)
        if chars_match:
            chars_str = chars_match.group(1)
            # Split on commas and clean up
            pov_info["characters"] = [c.strip().strip('"\'') for c in chars_str.split(',') if c.strip()]

        # Fallback: Extract from scene POV markers if plot didn't specify
        if not pov_info["characters"] and scene:
            pov_markers = re.findall(r'<VOICE:NARRATOR>POV:\s*([^<]+)</VOICE:NARRATOR>', scene)
            # Filter out non-character markers like "Dual Convergence"
            pov_chars = [pov.strip() for pov in set(pov_markers) if not any(word in pov.lower() for word in ['dual', 'convergence', 'transition'])]
            if pov_chars:
                pov_info["characters"] = pov_chars

        return pov_info

    def _pass_plot(
        self,
        world: WorldState,
        template_suggestion: str,
        context: str,
        relationship_context: dict | None,
    ) -> GenerationPass:
        """Pass 1: Generate plot outline with dynamic POV decision"""

        # Build world context
        char_descriptions = "\n".join(
            f"- **{c.name}** ({c.role}, {c.gender}, {c.age}): "
            f"Personality: {', '.join(c.personality) if c.personality else 'unassuming'}. "
            f"Knows: {', '.join(c.knowledge) if c.knowledge else 'general town knowledge'}."
            for c in world.characters
        )

        events_text = "\n".join(f"- {e}" for e in world.recent_events[:5])
        secrets_text = "\n".join(f"- {s}" for s in world.secrets[:3])

        # Add relationship signals if available
        relationship_hints = ""
        if relationship_context and relationship_context.get('signals'):
            signal = relationship_context['signals'][0]
            dynamic = signal.get('suggested_dynamic', {})
            relationship_hints = f"""
## Relationship Dynamic Context
Based on real relationship patterns, characters in this scene may exhibit:
- Warmth level: {dynamic.get('warmth', 'complex')}
- Power balance: {dynamic.get('power_balance', 'shifting')}
- Communication pattern: {dynamic.get('communication_pattern', 'nuanced')}

Use this to inform character motivations, interaction dynamics, and dramatic tension.
"""

        prompt = f"""You are a story architect for audio drama. Analyze the story needs and create a plot outline.

## Context
**Town:** {world.town_name}, {world.time_period}
**Series:** {template_suggestion}

**Characters:**
{char_descriptions}

**Recent Events:**
{events_text}

**Secrets:**
{secrets_text}
{relationship_hints}
**Additional Context:** {context or "General dramatic tension from recent events"}

## Your Task

FIRST, decide POV structure:
- **Single POV**: Use for intimate character study, mystery investigation from one perspective
- **Dual POV**: Use for parallel storylines, dramatic irony, contrasting perspectives
- **Ensemble POV**: Use for community crisis, multiple stakeholders, collective reaction

Consider:
- What creates maximum dramatic tension?
- What knowledge gaps create suspense?
- What relationship dynamics are active?

THEN, create plot outline:

1. **COLD OPEN (90-120 seconds)**
   - Hook: Immediate attention grab
   - Sensory atmosphere
   - Stakes established

2. **ACT I (4-6 minutes)**
   - Inciting incident
   - Character intro through action
   - Central question

3. **ACT II (7-10 minutes)**
   - Investigation/complication
   - POV transitions (if multi-POV)
   - Tension escalation

4. **ACT III (3-4 minutes)**
   - Revelation/decision
   - Cliffhanger setup

## Literary Techniques to Plan:
- Foreshadowing
- Dramatic irony (especially with multi-POV)
- Subtext opportunities
- Environmental symbolism

Output format:
```
POV_STRUCTURE: [single|dual|ensemble]
POV_CHARACTERS: [Name1, Name2, ...]
JUSTIFICATION: [Why this POV structure serves the story]

[Detailed outline with beats and timing]
```

BEGIN OUTLINE:"""

        # Call Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,  # Plot outline doesn't need to be huge
            messages=[{"role": "user", "content": prompt}],
        )

        return GenerationPass(
            pass_name="plot",
            output=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    def _pass_emotional(
        self,
        world: WorldState,
        plot_outline: str,
        pov_info: dict,
        relationship_context: dict | None,
    ) -> GenerationPass:
        """Pass 2: Generate emotional roadmap"""

        # Build relationship context
        relationship_hints = ""
        if relationship_context and relationship_context.get('signals'):
            signal = relationship_context['signals'][0]
            dynamic = signal.get('suggested_dynamic', {})
            relationship_hints = f"""
## Relationship Context for Emotional Calibration
- Trust level: {dynamic.get('trust_level', 'medium')}
- Warmth: {dynamic.get('warmth', 'complex')}
- Power balance: {dynamic.get('power_balance', 'shifting')}

This affects how quickly tension escalates and how characters respond to each other.
"""

        prompt = f"""You are an emotional pacing specialist for audio drama.

## Plot Outline
{plot_outline}
{relationship_hints}
## POV Structure
{pov_info['structure']} - {', '.join(pov_info['characters']) if pov_info['characters'] else 'TBD'}

## Your Task

Create emotional roadmap:

1. **Tension Curve** (1-10 at each plot beat)
   - Ensure variation (not flat, not constant high)
   - Mark peaks and valleys

2. **Per-POV Emotional States**
   For each POV character:
   - Opening state
   - Shifts during episode
   - Closing state
   - Active internal conflicts

3. **POV Transition Points** (if multi-POV)
   - When to switch POV?
   - What emotional state to leave/enter?
   - Contrast or continuity?

4. **Tone Attribute Map**
   Key dialogue moments with specific ElevenLabs tags:
   - nervous, defensive, whispers, angrily, cautiously, resigned, panicked, etc.
   - Match to character state + situation

5. **Pacing Recommendations**
   - SLOW: emotional depth needed
   - FAST: tension building
   - Strategic silence placements

Output: Structured emotional roadmap with tension scores, character states, tone tags

BEGIN EMOTIONAL ROADMAP:"""

        # Call Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,  # Emotional roadmap needs detail
            messages=[{"role": "user", "content": prompt}],
        )

        return GenerationPass(
            pass_name="emotional",
            output=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    def _pass_dialogue(
        self,
        world: WorldState,
        plot_outline: str,
        emotional_roadmap: str,
        pov_info: dict,
        target_words: int,
    ) -> GenerationPass:
        """Pass 3: Write scene with literary quality"""

        # Build character details for POV characters
        pov_chars_details = ""
        if pov_info['characters']:
            for pov_name in pov_info['characters']:
                for char in world.characters:
                    if pov_name.lower() in char.name.lower():
                        knowledge = '\n   '.join(char.knowledge) if char.knowledge else "general town knowledge"
                        secrets = '\n   '.join(char.secrets) if char.secrets else "none"
                        pov_chars_details += f"""
**{char.name} ({pov_info['structure']} POV character):**
   Knowledge: {knowledge}
   Secrets: {secrets}
   Personality: {', '.join(char.personality) if char.personality else 'unassuming'}
"""

        prompt = f"""You are a literary fiction author writing audio drama with sophisticated prose.

## Plot Outline
{plot_outline}

## Emotional Roadmap
{emotional_roadmap}

## POV Structure
{pov_info['structure']} POV - {', '.join(pov_info['characters']) if pov_info['characters'] else 'To be determined'}
{pov_chars_details}

## Your Task

Write complete scene with:

1. **SOPHISTICATED NARRATOR VOICE**
   - Literary narration, not just description
   - Character interiority (thoughts, micro-decisions, reactions)
   - Environmental mood (sensory details that foreshadow)
   - Rhythm variation (short = tension, long = reflection)
   - Metaphors for emotional states

   EXAMPLE (before):
   <VOICE:NARRATOR>Sarah walked into the sheriff's office. She was nervous.</VOICE:NARRATOR>

   EXAMPLE (after):
   <VOICE:NARRATOR>Sarah's hand trembled on the brass doorknob—cold, like the dread pooling in her stomach.
   Through the frosted glass, she could see the Sheriff's silhouette, motionless, waiting.
   She'd rehearsed this conversation a dozen times walking over, but now, standing here,
   every prepared word dissolved like morning fog over the harbor. [pause] She pushed open the door.</VOICE:NARRATOR>

2. **MULTI-POV HANDLING** (if applicable)
   - Clear POV markers for audio:
     <VOICE:NARRATOR>POV: [Character Name]</VOICE:NARRATOR>
   - Maintain POV knowledge constraints
   - Show ONLY active POV's internal monologue
   - Smooth transitions between POVs

3. **DIALOGUE WITH SUBTEXT**
   - What's SAID ≠ what's MEANT
   - Power dynamics in conversation control
   - Realistic interruptions, pauses, false starts
   - Hiding, deflecting, testing each other

   EXAMPLE (before):
   <VOICE:CHARACTER_Sarah>I saw someone at the bakery that morning.</VOICE:CHARACTER_Sarah>
   <VOICE:CHARACTER_Sheriff>Who was it?</VOICE:CHARACTER_Sheriff>

   EXAMPLE (after):
   <VOICE:CHARACTER_Sheriff>You're here about the fire.</VOICE:CHARACTER_Sheriff>
   <VOICE:NARRATOR>Not a question. He already knew.</VOICE:NARRATOR>
   <VOICE:CHARACTER_Sarah tone="cautious">I... might have information.</VOICE:CHARACTER_Sarah>
   <VOICE:CHARACTER_Sheriff>Might have. [pause] Interesting choice of words, Miss Chen.</VOICE:CHARACTER_Sheriff>
   <VOICE:NARRATOR>He was testing her. Seeing if she'd commit.</VOICE:NARRATOR>

4. **ENVIRONMENTAL STORYTELLING**
   - Weather/lighting mirrors emotion
   - Physical objects as metaphors
   - Background sounds punctuate tension

## Voice Tag Requirements
- NARRATOR: 3-5 sentence paragraphs
- CHARACTER: Include tone attributes from emotional roadmap
  Format: <VOICE:CHARACTER_Name tone="nervous">dialogue</VOICE:CHARACTER_Name>
- ElevenLabs V3 tags in narrator: [pause], [whispers], [hesitates]

## Target: {target_words} words

Follow emotional roadmap's tension curve precisely.

BEGIN SCENE:"""

        # Call Claude with higher max_tokens for the full scene
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=6000,  # Allow for full 2500-3000 word scene with voice tags
            messages=[{"role": "user", "content": prompt}],
        )

        return GenerationPass(
            pass_name="dialogue",
            output=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    def _pass_polish(
        self,
        scene: str,
        emotional_roadmap: str,
    ) -> GenerationPass:
        """Pass 4: Audio optimization pass"""

        prompt = f"""You are an audio engineer and dramaturg. Optimize for audio performance.

## Scene Draft
{scene}

## Emotional Roadmap
{emotional_roadmap}

## Your Task

1. **STRATEGIC PAUSE PLACEMENT**
   - Before/after emotional beats: [pause]
   - Dramatic moments: [long pause]
   - Rhythm variation: break up long speeches

2. **TONE ATTRIBUTE OPTIMIZATION**
   - Review all CHARACTER dialogue
   - Add/refine tone= attributes
   - Ensure variety (not repetitive)
   - Match ElevenLabs V3 tags precisely: nervous, defensive, whispers, angrily, cautiously, resigned, panicked, etc.

3. **PACING HOOKS**
   - Cold open: First 90 seconds MUST grab attention
   - Act transitions: Clear environmental beats
   - Cliffhanger ending: Unanswered question/new threat/uncertain decision

4. **POV TRANSITION CLARITY** (if multi-POV)
   - Ensure POV markers are CLEAR for audio listeners
   - Add transition beats (narrator pause, environmental shift)
   - Verify no confusion about whose perspective

5. **NARRATION RHYTHM**
   - Vary sentence length for audio flow
   - Remove awkward repetition
   - Add breathing room around intense moments

6. **CALLBACK INSERTION**
   - Reference previous episodes (if context available)
   - Plant foreshadowing
   - Reinforce series continuity

Output: Polished scene ready for doc-to-audio.py

BEGIN POLISHED SCENE:"""

        # Call Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,  # Ensure complete scene with all polish additions
            messages=[{"role": "user", "content": prompt}],
        )

        return GenerationPass(
            pass_name="polish",
            output=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )


# =============================================================================
# Main / Testing
# =============================================================================


if __name__ == "__main__":
    print("Multi-pass scene generator created successfully!")
    print("Import this module in daily-production.py to use.")
