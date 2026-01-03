#!/usr/bin/env python3
"""
Extended Scene Templates for 15-30 Minute Episodes

Templates that generate substantially longer, more sophisticated episodes
while maintaining narrative quality.
"""

EXTENDED_TEMPLATES = {
    "three_act_mystery": """
Scene Template: Three-Act Mystery Episode (Target: 15-20 minutes)

STRUCTURE:

ACT I - SETUP (Target: 4-6 minutes, ~900-1350 words)

1. COLD OPEN (90-120 seconds)
   - NARRATOR: Atmospheric scene setting
     * Time of day, weather, sensory details (sound, smell, light)
     * Environmental context specific to location
     * Establish mood and tension
   - NARRATOR: POV character's current situation
     * What they're doing, why they're there
     * Internal state (worried, focused, routine)
   - Brief hint of conflict or discovery to come

2. CHARACTER INTRODUCTION (90-120 seconds)
   - NARRATOR: POV character's internal monologue
     * Recent thoughts/concerns related to episode theme
     * Reference to past events or ongoing tensions
     * Character's unique perspective on the world
   - Show character's personality through action/observation
   - Establish what's at stake for this character

3. INCITING INCIDENT (2-3 minutes)
   - Discovery, interruption, or unexpected event
   - NARRATOR: Detailed description of what happens
   - POV_CHARACTER: Immediate reaction (dialogue or thought)
   - NARRATOR: Character's decision-making process
     * Consider options
     * Reference past experiences
     * Choose course of action
   - Set episode's central question

ACT II - DEVELOPMENT (Target: 7-10 minutes, ~1575-2250 words)

4. INVESTIGATION/REACTION (3-4 minutes)
   - POV character examines situation or seeks information
   - NARRATOR: Detailed environmental observations
   - Encounter with second character:
     * Extended dialogue with subtext
     * Power dynamics visible in conversation
     * Each character has distinct voice and agenda
     * Include pauses, interruptions, realistic speech patterns
   - NARRATOR: Character's internal assessment
     * What they're noticing but not saying
     * Doubts, suspicions, concerns

5. COMPLICATION (2-3 minutes)
   - New information contradicts expectations
   - Or: Second character reveals conflicting perspective
   - NARRATOR: Tension escalation through environmental details
   - Extended dialogue sequence:
     * Multiple exchanges, not just Q&A
     * Emotional beats (defensiveness, anger, evasion)
     * Subtext about relationships and history
   - NARRATOR: POV character recognizes deeper problem

6. CONFRONTATION OR PARALLEL ACTION (2-3 minutes)
   - Either: Direct confrontation with antagonist/obstacle
   - Or: Cut to another character's parallel experience (different POV)
   - If confrontation:
     * NARRATOR: Charged atmosphere description
     * Extended tense dialogue
     * Physical/emotional reactions
   - If parallel action:
     * NARRATOR: New location/time
     * Different character's perspective on same events
     * Information asymmetry creates dramatic irony

ACT III - RESOLUTION SETUP (Target: 3-4 minutes, ~675-900 words)

7. REVELATION OR DECISION POINT (2-3 minutes)
   - Key piece of information revealed
   - Or: Character makes critical choice
   - NARRATOR: Build tension before reveal
   - CHARACTER: Emotional delivery of key line/information
   - NARRATOR: Immediate impact described
   - Other characters react:
     * Short exchanges showing different responses
     * Emotional stakes clarified

8. CLIFFHANGER OR TRANSITION (60-90 seconds)
   - NARRATOR: New question or threat emerges
   - POV character's realization or decision
   - Environmental detail that echoes emotional state
   - Final line that sets up next episode
   - NARRATOR: Ominous or unresolved ending note

VOICE TAG GUIDELINES:

- NARRATOR tags should be substantial (3-5 sentences minimum)
- Include internal monologue in narration, not just description
- Character dialogue should have tone attributes when emotionally charged
  Example: <VOICE:CHARACTER_Sarah tone="defensive">
- Use narrative beats between dialogue exchanges
- Show character thoughts/reactions through narration

PACING GUIDELINES:

- Slow down during emotional moments (more description)
- Speed up during action/tension (shorter sentences, faster exchanges)
- Use environmental details to control rhythm
- Strategic silences described in narration

**LENGTH TARGET: 2,250-3,000 words (15-20 minutes at 150 wpm)**

IMPORTANT: This length target is MANDATORY. Do not write shorter scenes. Each act should hit its word count targets:
- Act I: 900-1,350 words minimum
- Act II: 1,575-2,250 words minimum
- Act III: 675-900 words minimum

If you write less than 2,000 words total, you are failing the assignment.
""",
    "dual_perspective_investigation": """
Scene Template: Dual Perspective Investigation (Target: 18-25 minutes)

STRUCTURE:

PERSPECTIVE A - CHARACTER 1 (8-10 minutes, ~1200-1500 words)

1. Morning Routine Opening (2 minutes)
   - NARRATOR: Detailed scene setting
     * Character's home/workspace
     * Morning rituals that reveal personality
     * Internal thoughts about current concerns
   - Establish character's emotional state
   - Foreshadow day's events through subtle details

2. Discovery/Encounter (3-4 minutes)
   - Character encounters problem or makes discovery
   - NARRATOR: Detailed observation process
   - Internal debate about what to do
   - Decision to investigate or act
   - Initial interaction with second character
     * Extended dialogue with subtext
     * Each character hiding something
     * Power dynamics play out

3. First Complication (2-3 minutes)
   - Character learns something unexpected
   - NARRATOR: Character's thought process
   - Encounter with community member
   - Brief but revealing dialogue exchange
   - Character's suspicions grow

PERSPECTIVE B - CHARACTER 2 (8-10 minutes, ~1200-1500 words)

4. Parallel Morning (2 minutes)
   - NARRATOR: Different location, same timeframe
   - Character 2's very different morning
   - Their perspective on same events
   - What they know that Character 1 doesn't

5. Their Investigation (3-4 minutes)
   - Character 2 pursuing their own agenda
   - NARRATOR: Reveal their motivations
   - Encounter with third character
     * Extended dialogue revealing backstory
     * Information that complicates main plot
   - Character 2's decision point

6. Intersection Foreshadowed (2-3 minutes)
   - Character 2 approaches situation from different angle
   - NARRATOR: Building toward convergence
   - Brief encounter that almost reveals truth
   - Missed connection creates tension

CONVERGENCE (4-6 minutes, ~600-900 words)

7. Characters Meet (2-3 minutes)
   - NARRATOR: Location where paths cross
   - Both characters present with different information
   - Extended dialogue with dramatic irony
     * Reader knows more than either character
     * Each reveals piece of puzzle
     * Tension from information asymmetry

8. Revelation and New Question (2-3 minutes)
   - Shared discovery changes everything
   - NARRATOR: Impact described from both perspectives
   - Brief exchange showing shifted dynamic
   - NARRATOR: New threat or mystery emerges
   - Cliffhanger ending

**LENGTH TARGET: 3,000-3,750 words (20-25 minutes at 150 wpm)**

IMPORTANT: This length target is MANDATORY. Do not write shorter scenes. Each perspective and section should hit its targets:
- Perspective A: 1,200-1,500 words minimum
- Perspective B: 1,200-1,500 words minimum
- Convergence: 600-900 words minimum

If you write less than 2,750 words total, you are failing the assignment.
""",
    "ensemble_community_crisis": """
Scene Template: Ensemble Community Crisis (Target: 20-25 minutes)

STRUCTURE:

OPENING - COMMUNITY GATHERING (3-4 minutes, ~450-600 words)

1. Assembly
   - NARRATOR: Location description (town hall, dock, general store)
   - Who is present and why
   - Underlying tensions in the room
   - Environmental details showing community character

2. Issue Introduction
   - AUTHORITY_CHARACTER: Opens meeting/discussion
   - NARRATOR: Various reactions described
   - Multiple characters with quick interjections
     * Show personalities through brief comments
     * Establish different factions/perspectives

ACT I - POSITIONS STATED (5-6 minutes, ~750-900 words)

3. First Perspective - Traditionalist
   - ELDER_CHARACTER: Extended statement
     * References past, community history
     * Appeals to tradition and stability
   - NARRATOR: Others' reactions
   - Brief supportive and opposing comments from crowd

4. Second Perspective - Progressive
   - YOUNG_CHARACTER: Counter-argument
     * Appeals to future, change, necessity
     * Cites evidence or recent events
   - NARRATOR: Generational tension visible
   - Extended exchange with elder
     * Respectful but firm disagreement
     * Personal stakes revealed

5. Third Perspective - Pragmatist
   - MIDDLE_CHARACTER: Mediating position
     * Economic or practical concerns
     * Points out costs of both approaches
   - NARRATOR: Shifting alliances in room

ACT II - COMPLICATIONS (6-8 minutes, ~900-1200 words)

6. Personal Stakes Revealed
   - One character reveals personal connection to issue
   - NARRATOR: Emotional atmosphere shifts
   - Extended confession or revelation
   - Other characters respond with sympathy/suspicion
   - Dialogue sequence showing community bonds tested

7. Hidden Information Emerges
   - Another character forced to admit what they know
   - NARRATOR: Building tension
   - Accusatory dialogue
   - Defensive responses
   - Community member reactions
     * Some supportive, some critical
     * Social dynamics play out

8. Fracture Point
   - Disagreement becomes personal
   - NARRATOR: Alliances form and break
   - Multiple voices overlapping (shown in narration)
   - Someone walks out or confrontation escalates

ACT III - RESOLUTION ATTEMPT (5-6 minutes, ~750-900 words)

9. Attempted Reconciliation
   - Mediator character tries to bridge gap
   - NARRATOR: Describe emotional exhaustion in room
   - Appeals to community identity
   - Some characters soften, others harden

10. Temporary Resolution
   - Compromise suggested or decision made
   - NARRATOR: Show who accepts and who doesn't
   - Brief statements from key characters
   - NARRATOR: Underlying tensions remain

11. Private Aftermath (2-3 minutes)
   - Scene shifts to 2-3 characters after meeting
   - Private conversation reveals true feelings
   - Plans made in secret
   - NARRATOR: Set up consequences for future
   - Cliffhanger about what happens next

ENSEMBLE VOICE GUIDELINES:

- 5-7 distinct character voices
- Each character gets substantial speaking time (1-2 minutes minimum)
- Show character relationships through dialogue patterns
- Use NARRATOR to manage large cast (describe reactions, group dynamics)
- Environmental details show emotional state of collective

**LENGTH TARGET: 3,000-3,750 words (20-25 minutes at 150 wpm)**

IMPORTANT: This length target is MANDATORY. Do not write shorter scenes. Each act should hit its word count targets:
- Opening: 450-600 words minimum
- Act I: 750-900 words minimum
- Act II: 900-1,200 words minimum
- Act III: 750-900 words minimum

If you write less than 2,750 words total, you are failing the assignment.
""",
}

# Template selection guide
TEMPLATE_GUIDE = {
    "mystery_focus": "three_act_mystery",
    "character_depth": "dual_perspective_investigation",
    "community_drama": "ensemble_community_crisis",
}


def get_extended_template(template_name: str) -> str:
    """Get extended template by name"""
    return EXTENDED_TEMPLATES.get(
        template_name, EXTENDED_TEMPLATES["three_act_mystery"]
    )


def get_recommended_template(series_name: str, episode_themes: list[str]) -> str:
    """Recommend template based on series and themes"""
    series_name = series_name.lower()

    # Saltmere often works well with dual perspective (family dynamics)
    if series_name == "saltmere":
        if "family" in episode_themes or "generational" in episode_themes:
            return "dual_perspective_investigation"
        if "community" in episode_themes:
            return "ensemble_community_crisis"

    # Millbrook often works with mysteries and community tensions
    elif series_name == "millbrook":
        if "investigation" in episode_themes or "mystery" in episode_themes:
            return "three_act_mystery"
        if "community" in episode_themes or "town" in episode_themes:
            return "ensemble_community_crisis"

    # Default to three-act structure
    return "three_act_mystery"
