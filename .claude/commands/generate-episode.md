# Generate Episode

Generate the next episode for a Simulacrum Stories series using Claude Code directly (no API costs).

## Usage

```
/generate-episode <series-name> [--dry-run] [--no-audio]
```

**Arguments:**
- `series-name`: Either `saltmere` or `millbrook`
- `--dry-run`: Generate markdown only, don't produce audio
- `--no-audio`: Same as --dry-run

## Implementation Steps

When this skill is invoked:

### Step 1: Get Episode Context

Run the helper script to get all context:

```bash
python ~/Documents/Code/simulacrum-stories/scripts/get-next-episode-context.py <series-name>
```

This returns JSON with:
- Series info (name, setting, themes)
- Next episode details (number, POV character, context prompt, template)
- Full world state (characters, events, locations, secrets)
- Output path for the episode file

### Step 2: Write the Episode

**YOU (Claude Code) write the episode directly.** This is the key cost savings - no API call needed.

#### Voice Tag Format (CRITICAL)

Use EXACTLY this format for audio generation compatibility:

```markdown
<VOICE:NARRATOR>Narrator text here. Can include [pause] and [long pause] tags.</VOICE:NARRATOR>

<VOICE:CHARACTER_Name tone="emotional-state">Character dialogue here.</VOICE:CHARACTER_Name>
```

**Tone attributes** (use liberally for emotional delivery):
- `nervous`, `defensive`, `cautious`, `resigned`
- `angry`, `whispered`, `urgent`, `bitter`
- `warm`, `gentle`, `hopeful`, `weary`

#### Episode Structure

**Target: 2,500-3,000 words** (15-20 minutes audio)

```markdown
# [Episode Title]

**Episode [N]** | **Series**: [Name] Chronicles | **POV**: [Character]

---

[COLD OPEN - 90 seconds, immediate hook]

<VOICE:NARRATOR>Atmospheric opening that grabs attention...</VOICE:NARRATOR>

[ACT I - 4-6 minutes, inciting incident]

<VOICE:NARRATOR>Scene-setting, character introduction through action...</VOICE:NARRATOR>

<VOICE:CHARACTER_Name tone="state">Dialogue...</VOICE:CHARACTER_Name>

[ACT II - 7-10 minutes, escalation and complications]

<VOICE:NARRATOR>POV character's internal perspective, observations, reactions...</VOICE:NARRATOR>

[ACT III - 3-4 minutes, revelation and cliffhanger]

<VOICE:NARRATOR>Resolution setup, unanswered question, tension...</VOICE:NARRATOR>

---

**Next Episode Preview**: [One-line teaser]
```

#### POV Writing Requirements

The episode is told from the POV character's perspective:

1. **Narrator = POV's internal voice**
   - Show their observations, suspicions, fears
   - Only describe what they can perceive
   - Include internal reactions to others' words

2. **Limited Knowledge**
   - POV can only reference things in their `knowledge` list
   - Show confusion/curiosity when others mention unknown things
   - Create dramatic irony (audience may know more)

3. **Personality Filter**
   - All observations colored by POV's personality traits
   - Suspicious character notices threats
   - Lonely character notices connections

#### Literary Quality

**Narrator prose** should be sophisticated:
```markdown
<VOICE:NARRATOR>Sarah's hand trembled on the brass doorknob—cold, like the dread pooling in her stomach. Through the frosted glass, she could see the Sheriff's silhouette, motionless, waiting. She'd rehearsed this conversation a dozen times walking over, but now, standing here, every prepared word dissolved like morning fog over the harbor. [pause] She pushed open the door.</VOICE:NARRATOR>
```

**Dialogue with subtext**:
```markdown
<VOICE:CHARACTER_Sheriff>You're here about the fire.</VOICE:CHARACTER_Sheriff>
<VOICE:NARRATOR>Not a question. He already knew.</VOICE:NARRATOR>
<VOICE:CHARACTER_Sarah tone="cautious">I... might have information.</VOICE:CHARACTER_Sarah>
<VOICE:CHARACTER_Sheriff tone="measured">Might have. [pause] Interesting choice of words, Miss Chen.</VOICE:CHARACTER_Sheriff>
```

### Step 3: Save Episode

Save the episode markdown to:

```
~/Documents/Code/simulacrum-stories/output/episodes/[series]/E[NN]-scene.md
```

Create the directory if needed:
```bash
mkdir -p ~/Documents/Code/simulacrum-stories/output/episodes/[series]
```

### Step 4: Update Series Registry

After successful generation, run the registry update script:

```bash
python ~/Documents/Code/simulacrum-stories/scripts/update-series-registry.py <series-name>
```

This increments episode count, rotates POV index, and updates timestamp.

### Step 5: Generate Audio (unless --dry-run)

If audio generation is requested:

```bash
uv run python ~/Documents/Code/simulacrum-stories/scripts/doc-to-audio.py \
  --input [episode-markdown-path] \
  --output ~/Music/Simulacrum-Stories/[Series]\ Chronicles/ \
  --provider elevenlabs \
  --multi-voice \
  --narrator [narrator-voice] \
  --narrative
```

Narrator voice selection:
- Female POV → `Sarah` (ElevenLabs) / `Serena` (macOS)
- Male POV → `George` (ElevenLabs) / `Jamie` (macOS)

## Example Session

**User**: `/generate-episode saltmere`

**Claude Code**:
1. Reads series registry → Saltmere is at episode 7, last POV was Margaret Holloway (index 1)
2. Next POV: Thomas Breck (index 2)
3. Context: "The past catches up with Thomas in an unexpected way"
4. Loads Saltmere world JSON
5. **Writes the episode directly** (2,500+ words with voice tags)
6. Saves to `output/episodes/saltmere/E08-scene.md`
7. Updates registry (episode_count=8, last_pov_index=2)
8. Runs audio generation

**User**: `/generate-episode millbrook --dry-run`

Same as above, but skips audio generation step.

## Series Reference

### Saltmere (1970s Pacific Northwest coastal)
- **Themes**: Family secrets, coastal isolation, environmental mystery
- **Central Mystery**: What lies beneath the waterfront?
- **POV Rotation**: Sarah Chen → Margaret Holloway → Thomas Breck → Eleanor Cross

### Millbrook (1980s Midwest industrial)
- **Themes**: Small-town secrets, moral choices, community
- **POV Rotation**: Sheriff Frank Donovan → Margaret Holloway → Old Pete Anderson → Jack Morrison

## Cost Comparison

| Method | LLM Cost | Audio Cost | Total |
|--------|----------|------------|-------|
| API (old) | ~$0.21 | ~$0.02 | ~$0.23 |
| Claude Code | $0 | ~$0.02 | ~$0.02 |

**91% cost reduction per episode.**
