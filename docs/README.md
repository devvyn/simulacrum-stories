# Narrative Tools for Simulacrum Stories

**Purpose**: Convert procedurally generated or LLM-generated stories into dramatic audio readings with character voices

**Status**: MVP complete (2025-10-31)

## Components

### 1. Character Voice Mapper (`character_voice_mapper.py`)

**What it does**: Intelligently maps characters to TTS voices based on metadata (gender, age, role, personality)

**Key Features**:
- Dynamic voice allocation (not hardcoded)
- Character profile support (gender, age, role, personality)
- Voice palette management (macOS/ElevenLabs/OpenAI)
- Accent diversity preference
- Extensible for new characters

**Usage**:
```python
from character_voice_mapper import CharacterVoiceMapper, CharacterProfile

# Simple: Just character names
mapper = CharacterVoiceMapper(
    characters=['Sheriff', 'Sarah', 'Jack'],
    narrator_voice='Aman'
)

voice = mapper.get_voice('CHARACTER_Sheriff')  # → 'Jamie'

# Advanced: Character profiles
characters = [
    CharacterProfile(
        name='Sheriff',
        gender='male',
        age='middle',
        role='authority',
        personality=['authoritative', 'suspicious']
    ),
    # ... more characters
]

mapper = CharacterVoiceMapper(
    characters=characters,
    narrator_voice='Aman'
)

mapper.print_mapping()
```

**Voice Palette (macOS)**:
- **Jamie** (UK Male, Premium) - Authoritative, warm
- **Lee** (AU Male, Premium) - Casual, engaging
- **Serena** (UK Female, Premium) - Precise, elegant
- **Aman** (India Male, Siri) - Clear, neutral (great for narrator)
- **Tara** (India Female, Siri) - Calm, educational
- **Alex** (US Male, Enhanced) - Versatile, neutral
- **Samantha** (US Female, Enhanced) - Friendly, clear
- **Fred** (US Male, Basic) - Robotic (for code blocks)

### 2. Story to Audio Pipeline (`story_to_audio.py`)

**What it does**: Orchestrates the full pipeline from markdown story to multi-voice audio

**Key Features**:
- Auto-detects characters from voice tags
- Validates voice tag formatting
- Integrates with doc-to-audio.py
- Supports character profiles from JSON
- Advanced mixing options

**Usage**:
```bash
# Auto-detect characters from tags
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
    --narrator Aman \
    --advanced-mixing

# Validation only (check tags without generating audio)
./story_to_audio.py \
    --input scene.md \
    --validate-only

# Show voice mapping and exit
./story_to_audio.py \
    --input scene.md \
    --characters Sheriff Sarah Jack \
    --show-mapping
```

### 3. Future Tools (Planned)

- **`generate_world.py`**: LLM-based world generation (town + characters + events)
- **`extract_narrative.py`**: Event timeline → story arc with dramatic beats
- **`generate_scenes.py`**: Story beats → scenes with dialogue using LLM
- **`simulate_world.py`**: Lightweight Talk of the Town-style simulation

## Voice Tag Format

### Standard Tags

```markdown
<VOICE:NARRATOR>Scene-setting narration goes here.</VOICE:NARRATOR>

<VOICE:CHARACTER_Sheriff>Dialogue for Sheriff Thompson.</VOICE:CHARACTER_Sheriff>

<VOICE:CHARACTER_Sarah tone="cautious">Dialogue with emotional tone hint.</VOICE:CHARACTER_Sarah>

<VOICE:CODE>Technical code or robotic voice content.</VOICE:CODE>

<VOICE:QUOTE>Block quotes (uses narrator voice).</VOICE:QUOTE>

<VOICE:HEADER>Section headers (uses narrator voice).</VOICE:HEADER>
```

### Character Naming Convention

- **Pattern**: `CHARACTER_<Name>`
- **Name**: CamelCase or snake_case, alphanumeric
- **Examples**: `CHARACTER_Sheriff`, `CHARACTER_Sarah`, `CHARACTER_Jack`

### Optional Attributes (Future)

```markdown
<VOICE:CHARACTER_Sheriff tone="stern" rate="0.9">Slow, stern delivery.</VOICE:CHARACTER_Sheriff>

<VOICE:CHARACTER_Sarah emotion="nervous" pitch="+5">Nervous, higher pitch.</VOICE:CHARACTER_Sarah>
```

Currently tone/emotion attributes are **parsed but not used** by TTS (reserved for future enhancement).

## Example Workflow

### 1. Write Story with Voice Tags

Create `my_story.md`:
```markdown
<VOICE:NARRATOR>It was a dark and stormy night.</VOICE:NARRATOR>

<VOICE:CHARACTER_Detective>I've seen worse. Much worse.</VOICE:CHARACTER_Detective>

<VOICE:CHARACTER_Witness tone="nervous">I... I didn't see anything, officer.</VOICE:CHARACTER_Witness>
```

### 2. Generate Audio

```bash
cd ~/devvyn-meta-project/scripts/narrative-tools

./story_to_audio.py \
    --input my_story.md \
    --output ../../audio-assets/my-story/ \
    --auto-detect-characters \
    --narrator Aman \
    --advanced-mixing
```

### 3. Result

Output:
```
audio-assets/my-story/
├── my_story_part001.mp3       # Multi-voice audio
└── my_story_metadata.json     # Metadata
```

Voice mapping:
- Detective → Jamie (UK Male, authoritative)
- Witness → Serena (UK Female, precise)
- Narrator → Aman (India Male, neutral)

## Character Profile JSON Format

Create `characters.json`:
```json
{
  "characters": [
    {
      "name": "Sheriff",
      "gender": "male",
      "age": "middle",
      "role": "authority",
      "personality": ["authoritative", "suspicious", "direct"],
      "voice_characteristics": "Deep, commanding, slight Southern accent"
    },
    {
      "name": "Sarah",
      "gender": "female",
      "age": "middle",
      "role": "educator",
      "personality": ["cautious", "precise", "moral"],
      "voice_characteristics": "Clear, articulate, measured pace"
    },
    {
      "name": "Jack",
      "gender": "male",
      "age": "middle",
      "role": "service",
      "personality": ["casual", "nervous", "evasive"],
      "voice_characteristics": "Friendly but tense, slight working-class accent"
    }
  ]
}
```

Use with:
```bash
./story_to_audio.py \
    --input scene.md \
    --character-profiles characters.json \
    --narrator Aman
```

## Integration with Existing System

### doc-to-audio.py Compatibility

The narrative tools are **fully compatible** with existing `doc-to-audio.py`:

**What works now**:
- Multi-voice TTS (`--multi-voice`)
- Advanced mixing (`--advanced-mixing`)
- Conservative pauses (`--conservative-multivoice`)
- Narrator selection (`--narrator`)
- All existing providers (macOS, ElevenLabs, OpenAI)

**What's extended**:
- CHARACTER_<name> tags (beyond 4 fixed types)
- Dynamic character-to-voice allocation
- Character profile support
- Voice validation

**What's future**:
- Tone/emotion attributes actually affecting TTS
- Voice style presets (character archetypes)
- Cross-provider voice similarity matching

## Testing

### Test 1: Character Voice Mapper

```bash
cd ~/devvyn-meta-project/scripts/narrative-tools
python3 character_voice_mapper.py
```

Expected output:
```
=== Example 1: Simple Names ===

=== Voice Mapping ===
Narrator: Aman

Characters:
  Jack                 → Lee          (AU, clear, engaging, casual)
  Sarah                → Serena       (UK, elegant, articulate, precise)
  Sheriff              → Jamie        (UK, warm, professional, authoritative)

Special:
  Code Blocks: Fred
```

### Test 2: Story to Audio (Validation)

```bash
cd ~/devvyn-meta-project/scripts/narrative-tools

./story_to_audio.py \
    --input ../../examples/simulacrum-stories/simple-dialogue-test.md \
    --validate-only
```

Expected:
```
Validating voice tags...
✓ Voice tags valid
Auto-detected 3 characters: Jack, Sarah, Sheriff
...
✓ Validation complete
```

### Test 3: Full Audio Generation

```bash
cd ~/devvyn-meta-project/scripts/narrative-tools

./story_to_audio.py \
    --input ../../examples/simulacrum-stories/simple-dialogue-test.md \
    --output ../../audio-assets/test-story/ \
    --auto-detect-characters \
    --advanced-mixing
```

Expected result: Multi-voice MP3 file in `audio-assets/test-story/`

## Design Principles

1. **Extensibility**: Easy to add new characters, voices, providers
2. **Validation**: Catch errors early (tag formatting, missing characters)
3. **Flexibility**: Support both simple (names) and advanced (profiles) workflows
4. **Integration**: Works with existing doc-to-audio.py system
5. **Transparency**: Show voice mappings, validate before generation

## Comparison to Existing System

| Feature | doc-to-audio.py (before) | Narrative Tools (now) |
|---------|------------------------|----------------------|
| Character voices | Fixed 4 types (NARRATOR, CODE, QUOTE, HEADER) | Unlimited CHARACTER_<name> |
| Voice allocation | Hardcoded in VoiceMapper | Dynamic, metadata-driven |
| Character metadata | None | Gender, age, role, personality |
| Validation | None | Tag validation, character detection |
| Workflow | Direct script call | Orchestrated pipeline |

## Performance

**Character voice allocation**: O(n × m) where n = characters, m = voice palette size
- Typically < 1ms for 10 characters

**Voice tag parsing**: O(n) where n = markdown length
- Typically < 10ms for 5000-word story

**Audio generation**: Unchanged from doc-to-audio.py
- Depends on TTS provider and story length
- macOS `say`: ~1-2x real-time
- ElevenLabs API: ~3-5s per 1000 characters

## Roadmap

### Phase 1: MVP ✅ (Complete)
- Character voice mapper
- Story to audio pipeline
- Voice tag validation
- Example test scene

### Phase 2: Scene Generation (Next)
- LLM-based scene generation from templates
- Character consistency across scenes
- Parameterized scene library (Lume-style)

### Phase 3: World Generation
- LLM-based world generation
- Character backstory generation
- Event timeline creation

### Phase 4: Full Simulation
- Talk of the Town-lite implementation
- Event extraction algorithms
- Narrative arc construction

## References

- **Design Pattern**: `knowledge-base/narrative-generation/simulacrum-to-audio-design-pattern.md`
- **Emily Short Research**: `knowledge-base/narrative-generation/emily-short-world-simulation.md`
- **Talk of the Town**: `knowledge-base/narrative-generation/talk-of-the-town-framework.md`
- **Lume System**: `knowledge-base/narrative-generation/lume-combinatorial-narrative.md`
- **LLM Techniques**: `knowledge-base/narrative-generation/llm-procedural-narrative-2025.md`

---

**Last Updated**: 2025-10-31
**Status**: MVP complete, ready for testing
**Next**: Generate first full audio story from test scene
