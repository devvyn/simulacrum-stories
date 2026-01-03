# Simulacrum Stories - Standalone Project Proposal

## Assessment: Strong Candidate for `clproj` Migration

### Current State Analysis

**Location:** Meta-project embedded (`~/devvyn-meta-project/scripts/narrative-tools/`)

**Footprint:**
- Code: 564 KB (19 files)
- Audio archive: 54 MB (16 episodes)
- Deployment cache: 28 KB
- Documentation: Comprehensive README + 2 strategy docs

**Components:**
- 9 Python modules (voice mapping, world gen, scene gen, podcast feeds)
- 4 shell scripts (automation, publishing, deployment)
- 3 documentation files
- LaunchAgent daemon (daily automation)
- Podcast RSS infrastructure
- Multi-voice TTS pipeline

**Dependencies:**
- ElevenLabs API (audio generation)
- Anthropic API (LLM for scene/world generation)
- Relationship signal extractor (meta-project component)
- Budget tracking system (meta-project component)
- doc-to-audio.py (meta-project component)

### Why This Deserves Standalone Status

#### 1. **Scope & Complexity**
- 9 specialized Python modules with distinct responsibilities
- Multi-stage pipeline (world → characters → scenes → audio → RSS)
- Sophisticated relationship modeling and emotional tracking
- Production-ready with daily automation
- Multiple deployment targets (local, web, podcast platforms)

#### 2. **Development Velocity Potential**
Current constraints in meta-project:
- Mixed with general meta-infrastructure
- Harder to iterate rapidly without affecting other systems
- Credential sharing complexity
- Storage tier confusion (generated vs. source)

Standalone benefits:
- Dedicated development environment
- Clear project boundaries
- Independent dependency management
- Faster iteration cycles for creative work

#### 3. **Distinct Domain**
- **Meta-project focus:** Coordination, infrastructure, patterns, security
- **Simulacrum focus:** Creative storytelling, audio production, narrative generation
- Minimal conceptual overlap

#### 4. **Future Growth Direction**
Planned enhancements (from roadmap):
- Writer's room multi-agent system
- Emotional modeling framework
- Adaptive storytelling pipeline
- Quality feedback loops
- Persistent story state database

These will significantly expand scope → standalone project more appropriate.

#### 5. **External Collaboration Potential**
A standalone project could:
- Be shared with collaborators without exposing meta-infrastructure
- Have its own git history focused on creative/technical evolution
- Serve as portfolio piece
- Eventually be open-sourced (if desired)

### Proposed Project Structure

```
~/Documents/GitHub/simulacrum-stories/
├── README.md
├── pyproject.toml                    # uv project config
├── .env.example                      # API key templates
├── .gitignore
│
├── src/
│   └── simulacrum/
│       ├── __init__.py
│       ├── voices/
│       │   ├── __init__.py
│       │   ├── mapper.py             # Character voice mapping
│       │   └── profiles.py           # Character profile models
│       ├── generation/
│       │   ├── __init__.py
│       │   ├── world.py              # World generation
│       │   ├── characters.py         # Character creation
│       │   ├── scenes.py             # Scene generation
│       │   ├── templates.py          # Scene templates
│       │   └── signals.py            # Relationship signal extraction
│       ├── audio/
│       │   ├── __init__.py
│       │   ├── pipeline.py           # Story → audio pipeline
│       │   └── budget.py             # Budget tracking
│       ├── publishing/
│       │   ├── __init__.py
│       │   ├── feeds.py              # RSS feed generation
│       │   └── deployment.py         # Site deployment
│       └── models/
│           ├── __init__.py
│           ├── world.py              # World data models
│           ├── character.py          # Character models
│           └── story.py              # Story state models
│
├── scripts/
│   ├── generate-episode.py          # CLI for episode generation
│   ├── publish-feeds.sh              # Deployment automation
│   ├── scheduler-daemon.py           # Daily automation
│   └── status.sh                     # Production status
│
├── config/
│   ├── series-saltmere.yaml          # Saltmere series config
│   ├── series-millbrook.yaml         # Millbrook series config
│   ├── voice-palette.yaml            # Voice selection rules
│   └── budget.yaml                   # Resource limits
│
├── data/                             # Git-ignored
│   ├── story-state/                  # Persistent character/world state
│   │   ├── saltmere.db
│   │   └── millbrook.db
│   └── cache/                        # Temporary generation artifacts
│
├── output/                           # Git-ignored
│   ├── episodes/                     # Generated audio
│   │   ├── saltmere/
│   │   └── millbrook/
│   └── deployment/                   # Web-ready files
│       ├── audio/
│       ├── feeds/
│       └── index.html
│
├── docs/
│   ├── ARCHITECTURE.md               # System design
│   ├── ENHANCEMENT_ROADMAP.md        # Future features
│   ├── SERIES_GUIDE.md               # Series differentiation
│   └── API.md                        # Module API docs
│
├── tests/
│   ├── test_voice_mapping.py
│   ├── test_scene_generation.py
│   └── test_feed_generation.py
│
└── examples/
    ├── simple-scene.md               # Example scene markup
    └── character-profiles.json       # Example profiles
```

### Migration Strategy

#### Phase 1: Project Setup
1. Create new project: `clproj new simulacrum-stories`
2. Initialize uv project with pyproject.toml
3. Set up project structure (directories above)
4. Configure .gitignore (exclude data/, output/, credentials)

#### Phase 2: Code Migration
1. Move Python modules from `scripts/narrative-tools/` → `src/simulacrum/`
2. Refactor into proper package structure (remove script-style execution)
3. Extract shared dependencies:
   - **Keep in meta-project:** Relationship signal extractor (general-purpose)
   - **Duplicate if needed:** Budget manager (Simulacrum-specific fork)
   - **Keep in meta-project:** doc-to-audio.py (general audio tool)
4. Update imports and module paths
5. Create CLI entry points in `scripts/`

#### Phase 3: Dependency Management
1. Create pyproject.toml with dependencies:
   ```toml
   [project]
   name = "simulacrum-stories"
   dependencies = [
       "anthropic",
       "elevenlabs",
       "feedgen",
       "pydantic",
       # ... others
   ]
   ```
2. Set up credential access:
   - Reference meta-project credential managers via environment variables
   - Document setup in README
   - No credentials stored in project repo

#### Phase 4: Data Migration
1. Move episode archive: `~/Music/Simulacrum-Stories/` → `output/episodes/`
2. Move deployment: `~/Desktop/simulacrum-podcast-deploy/` → `output/deployment/`
3. Update LaunchAgent to point to new project location
4. Storage tier: **ICLOUD_PINNED** (multi-device, critical creative work)

#### Phase 5: Automation Migration
1. Update LaunchAgent plist:
   ```xml
   <string>/Users/devvynmurphy/.local/bin/uv</string>
   <string>run</string>
   <string>--directory</string>
   <string>/Users/devvynmurphy/Documents/GitHub/simulacrum-stories</string>
   <string>python</string>
   <string>scripts/scheduler-daemon.py</string>
   ```
2. Update logging paths
3. Test dry run
4. Verify production schedule

#### Phase 6: Documentation & Cleanup
1. Write comprehensive README for standalone project
2. Document credential setup (env vars referencing meta-project)
3. Create CLAUDE.md for project-specific agent instructions
4. Archive old location in meta-project
5. Update meta-project docs to reference new location

### Integration Points with Meta-Project

**What stays connected:**
- Credentials (via env vars pointing to `~/Secrets/`)
- Bridge messaging (if using multi-agent enhancements)
- Pattern library (reference meta-project knowledge base)

**What becomes independent:**
- Story generation logic
- Audio production pipeline
- Episode archive
- Podcast deployment
- Daily automation daemon

**Boundary Protocol:**
- Meta-project manages credentials, never duplicates
- Simulacrum project references via environment variables
- No cross-repo file dependencies
- Bridge messages for coordination if needed

### Benefits Summary

**Development:**
- ✅ Faster iteration (focused codebase)
- ✅ Proper package structure (not scripts)
- ✅ Independent version control
- ✅ Clear project scope

**Collaboration:**
- ✅ Shareable without exposing meta-infrastructure
- ✅ Clean git history
- ✅ Portfolio-quality presentation
- ✅ Potential open-source path

**Maintenance:**
- ✅ Clearer dependency management
- ✅ Isolated testing
- ✅ Better error boundaries
- ✅ Easier debugging

**Future Growth:**
- ✅ Room for writer's room expansion
- ✅ Dedicated story state database
- ✅ Quality metrics system
- ✅ Multiple series scaling

### Risks & Mitigations

**Risk 1: Credential duplication temptation**
- Mitigation: Strict env var policy, documented in README
- Never store API keys in project repo
- Reference meta-project credential managers only

**Risk 2: Loss of meta-project context**
- Mitigation: Bridge messaging for coordination
- Reference meta-project knowledge base for patterns
- Document relationship in both projects

**Risk 3: Storage tier confusion**
- Mitigation: Explicit storage manifest in project
- ICLOUD_PINNED for whole project (critical creative work)
- Clear documentation of what's cache vs. source

**Risk 4: Automation fragmentation**
- Mitigation: Single LaunchAgent, clear ownership
- Project-local automation, documented setup
- Health checks and logging

### Recommendation

**Yes, migrate Simulacrum to standalone `clproj` project.**

**Rationale:**
1. Sufficient scope and complexity to justify standalone status
2. Distinct domain from meta-project coordination focus
3. Future growth will make separation inevitable
4. Better development experience for creative/technical iteration
5. Clean separation aids collaboration and portfolio presentation

**Timeline:**
- Setup & initial migration: 2-3 hours
- Testing & validation: 1 hour
- Documentation: 1 hour
- Total: ~4-5 hours for clean migration

**Next Step:**
User approval to proceed with migration, or defer to future session?
