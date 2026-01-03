# Series Enrichment Strategy

## Making Both Series Equally Sophisticated

### Current State

- **Saltmere**: Uses real relationship signals → emotionally authentic
- **Millbrook**: Pure procedural generation → functional but less nuanced

### Goal

Make Millbrook as emotionally sophisticated as Saltmere while maintaining distinct identities.

---

## Strategy 1: Differentiated Signal Filtering

Use the SAME relationship signal extractor, but filter for different patterns:

### Saltmere (Family/Coastal/Generational)

**Filter for:**

- Long-term dormant relationships (old secrets, generational silence)
- Multi-generational group dynamics
- High warmth + high tension (family complexity)
- Deferential power dynamics (parent-child, elder-younger)

**Character mapping:**

- Dormant high-volume → "Used to be close but something happened"
- Long-term deferential → Parent/mentor relationships
- Group dynamics (3-5 people) → Family units
- Faded connections → Lost relationships that haunt

**Example extraction:**

```python
# For Saltmere: prioritize family-like patterns
signals = extractor.extract_signals(min_messages=100)
family_patterns = [s for s in signals if
    s.is_long_term and
    (s.communication_style == 'dormant' or s.balance_ratio < 0.35)]
```

### Millbrook (Small-Town/Authority/Community)

**Filter for:**

- Unequal power dynamics (authority figures)
- Group chats (community/gossip networks)
- Frequent casual contact (neighbors, small-town proximity)
- Shifting power dynamics (alliances, social maneuvering)

**Character mapping:**

- Dominant power dynamic → Sheriff, authority figures
- Frequent casual → Neighbors, regular encounters
- Group patterns → Town gossip, informal networks
- Balanced but cooling → Alliances under strain

**Example extraction:**

```python
# For Millbrook: prioritize authority/community patterns
signals = extractor.extract_signals(min_messages=50)
authority_patterns = [s for s in signals if
    s.balance_ratio > 0.65 or s.balance_ratio < 0.35 or
    s.communication_style == 'frequent_casual']
group_dynamics = extractor.extract_group_dynamics()
```

---

## Strategy 2: Enhanced World Generation Parameters

### Current world generation inputs

- Setting description
- Number of characters
- Generic themes

### Enhanced inputs (for BOTH series)

- **Relationship signal hints** (already implemented!)
- **Emotional calibration** (tension levels, warmth distribution)
- **Power structure templates** (hierarchy maps from signals)
- **Communication network topology** (who talks to whom, derived from groups)

### Implementation

```python
# In daily_production.py generate_episode()
relationship_hints = None
if args.use_real_signals:
    extractor = RelationshipSignalExtractor()
    signals = extractor.extract_signals(min_messages=50)

    # FILTER DIFFERENTLY PER SERIES
    if series_name == "saltmere":
        # Family/generational patterns
        filtered = [s for s in signals if s.is_long_term]
    elif series_name == "millbrook":
        # Authority/community patterns
        filtered = [s for s in signals if
            s.balance_ratio < 0.35 or s.balance_ratio > 0.65]

    converter = NarrativeConverter()
    relationship_hints = converter.signals_to_world_hints(filtered, count=5)

world = generator.generate(
    setting=setting,
    relationship_hints=relationship_hints,  # Inject real patterns
    ...
)
```

---

## Strategy 3: Additional Enrichment Sources

### A. Knowledge Base Integration

Extract patterns from your existing knowledge base:

**For Saltmere:**

- `knowledge-base/participants/` → Family relationship patterns
- Environmental themes from knowledge base
- Coastal history, fishing industry patterns

**For Millbrook:**

- Authority/hierarchy patterns from work relationships
- Small-town economic themes
- Industrial decline patterns

### B. Temporal Context (Period-Appropriate Details)

Generate richer period details:

**Saltmere (1970s):**

- Environmental movement emerging
- Fishing industry changes
- Generational divide (WWII generation vs Boomers)

**Millbrook (1980s):**

- Rust Belt economic collapse
- Reagan-era tensions
- Small-town vs urban divide

### C. News/Current Event Inspiration

Use historical context as narrative seeds:

```python
# Contextual enrichment for period authenticity
SALTMERE_CONTEXT_1970s = {
    "environmental_tensions": "Early EPA, pollution concerns",
    "economic_shifts": "Fishing industry consolidation",
    "social_changes": "Counterculture aftermath, return to tradition",
    "technology": "CB radios, early environmentalism"
}

MILLBROOK_CONTEXT_1980s = {
    "economic_tensions": "Factory closures, unemployment",
    "social_changes": "Drug crisis, rural decline",
    "political_backdrop": "Conservative shift, traditional values",
    "technology": "Early computers, VCRs, cable TV"
}
```

---

## Strategy 4: Narrative Structure Sophistication

### Current: Random scene templates

```python
scene_templates = ["confrontation", "discovery", "revelation", "investigation"]
```

### Enhanced: Emotional arc templates

```python
# Based on real story structure
MILLBROOK_ARC_TEMPLATES = [
    {
        "type": "slow_burn_tension",
        "beats": ["routine", "anomaly", "investigation", "resistance", "revelation"],
        "emotional_progression": "calm → unease → tension → conflict → release"
    },
    {
        "type": "community_fracture",
        "beats": ["gathering", "disagreement", "alliance_formation", "confrontation", "consequences"],
        "emotional_progression": "unity → division → polarization → conflict → new_normal"
    }
]

SALTMERE_ARC_TEMPLATES = [
    {
        "type": "generational_reckoning",
        "beats": ["present_calm", "past_surfaces", "confrontation", "revelation", "legacy_question"],
        "emotional_progression": "normal → discomfort → tension → truth → uncertainty"
    },
    {
        "type": "environmental_metaphor",
        "beats": ["discovery", "investigation", "resistance", "natural_event", "human_parallel"],
        "emotional_progression": "curiosity → concern → denial → crisis → connection"
    }
]
```

---

## Strategy 5: Character Voice Differentiation

### Current: Voice mapping by gender/age

### Enhanced: Voice mapping by relationship archetype + emotional state

```python
# Map relationship archetypes to voice characteristics
VOICE_PROFILES = {
    "close_confidant": {
        "tone": "warm, familiar, knowing",
        "pace": "natural, comfortable silences",
        "typical_emotions": ["concern", "support", "gentle_challenge"]
    },
    "authority_figure": {
        "tone": "measured, deliberate, commanding",
        "pace": "slower, emphatic",
        "typical_emotions": ["suspicion", "duty", "burden"]
    },
    "faded_connection": {
        "tone": "cautious, nostalgic, guarded",
        "pace": "hesitant, careful word choice",
        "typical_emotions": ["regret", "wariness", "longing"]
    }
}
```

---

## Implementation Priorities

### Phase 1: Immediate (This Week)

✅ Enable `--use-real-signals` for both series
✅ Implement differentiated filtering (Saltmere vs Millbrook)
✅ Test with manual generation

### Phase 2: Short-term (Next 2 Weeks)

- Add period-appropriate context enrichment
- Implement emotional arc templates
- Enhance character voice profiles

### Phase 3: Medium-term (Month 1)

- Knowledge base integration
- Callback/continuity tracking across episodes
- Sophisticated tension calibration

### Phase 4: Long-term (Month 2+)

- Cross-series learnings (what works in Saltmere → Millbrook)
- Automated quality metrics
- Listener feedback integration

---

## Success Metrics

**Emotional Authenticity:**

- Characters feel like real people with history
- Relationships have complexity and nuance
- Tensions feel earned, not arbitrary

**Narrative Coherence:**

- Episodes build on each other
- Character arcs progress naturally
- World feels lived-in

**Distinctiveness:**

- Saltmere and Millbrook feel different but equally rich
- Settings influence relationship expressions
- Themes emerge naturally from patterns

---

## Quick Win: Enable Signals for Millbrook NOW

Modify `budget-driven-scheduler.py` to pass signal flags:

```python
def _generate_episode(self, series_name: str):
    # ...

    # Always use real signals for emotional authenticity
    self.logger.info(f"Extracting relationship signals for {series_name}...")

    # This makes BOTH series sophisticated
    audio_file = self.episode_producer.produce_episode(
        state,
        album_dir,
        use_real_signals=True  # ← Enable for both series
    )
```

This single change will immediately make Millbrook as emotionally nuanced as Saltmere.
