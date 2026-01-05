# Simulacrum Stories

AI-powered audio storytelling with multi-voice narration, emotional modeling, and procedural narrative generation.

## What This Is

Simulacrum generates dramatic audio stories with:
- **Multi-voice narration** using ElevenLabs API
- **Emotional depth** from real relationship signal extraction
- **Procedural worlds** with consistent characters and arcs
- **Budget-conscious production** with manual episode generation
- **Podcast delivery** via RSS feeds

Currently producing two series:
- **Saltmere Chronicles** (1970s coastal family drama)
- **Millbrook Chronicles** (1980s rust belt mystery)

## Quick Start

```bash
# Setup
cd ~/Documents/GitHub/simulacrum-stories
uv sync

# Configure credentials (see .env.example)
export ANTHROPIC_API_KEY=$(~/devvyn-meta-project/scripts/anthropic-key-manager.sh get)
export ELEVEN_LABS_API_KEY=$(~/devvyn-meta-project/scripts/elevenlabs-key-manager.sh get)

# Generate single episode (dry run - no API calls)
uv run python scripts/daily-production.py --series saltmere --dry-run

# Generate actual episode (uses ElevenLabs credits)
uv run python scripts/daily-production.py --series millbrook

# Check budget status
uv run python -c "from simulacrum.audio.budget import AudioBudgetManager; \
  bm = AudioBudgetManager(); print(bm.status_report())"
```

## Project Structure

```
simulacrum-stories/
├── src/simulacrum/           # Core package
│   ├── voices/               # Character voice mapping
│   ├── generation/           # World, scene, character generation
│   ├── audio/                # Audio production pipeline
│   ├── publishing/           # RSS feed generation
│   └── models/               # Data models
├── scripts/                  # CLI tools
│   ├── scheduler-daemon.py   # Daily automation
│   ├── daily-production.py   # Episode generation
│   ├── publish-feeds.sh      # Deployment
│   └── status.sh             # Production status
├── config/                   # Series configurations
├── output/                   # Generated content (gitignored)
│   ├── episodes/             # Audio files
│   └── deployment/           # Web-ready podcast site
└── docs/                     # Documentation
```

## Features

### Current
- Relationship signal extraction from real communication patterns
- Template-based scene generation with emotional calibration
- Multi-voice TTS with character consistency
- Budget tracking and provider management (ElevenLabs Creator plan)
- RSS feed generation for podcast platforms
- Manual production workflow for budget control

### Planned (see docs/enhancement-roadmap.md)
- Writer's room multi-agent collaboration
- Dynamic emotional state tracking across episodes
- Adaptive storytelling with quality feedback loops
- Persistent story state database
- Enhanced continuity tracking with callbacks

## Documentation

- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Series Guide**: [docs/series-enrichment-strategy.md](docs/series-enrichment-strategy.md)
- **Enhancement Roadmap**: [docs/enhancement-roadmap.md](docs/enhancement-roadmap.md)
- **Deployment**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Lint
uv run ruff check src/

# Format
uv run ruff format src/
```

## Credential Management

**IMPORTANT**: This project references credentials from the meta-project. Never store API keys in this repository.

```bash
# Get Anthropic key
~/devvyn-meta-project/scripts/anthropic-key-manager.sh get

# Get ElevenLabs key
~/devvyn-meta-project/scripts/elevenlabs-key-manager.sh get

# Test credentials
~/devvyn-meta-project/scripts/elevenlabs-key-manager.sh test
```

## Production Status

**Current Series:**
- Saltmere Chronicles: Episodes 1-8 (coastal family drama, 1970s)
- Millbrook Chronicles: Episodes 1-9 (rust belt mystery, 1980s)

**Budget Status:**
- Provider: ElevenLabs Creator Plan (100,000 chars/month)
- Annual subscription: Prepaid
- Current usage: Check with budget manager (see Quick Start)
- Cost per episode: ~$1.47 (amortized)

**Production Approach:**
- Manual episode generation for budget control
- Automated LaunchAgent disabled (was consuming budget unconsciously)
- Strategic production: 14-16 episodes/month sustainable
- Annotated archive strategy for early experimental episodes

## Production Philosophy

This project takes a **budget-conscious, quality-focused** approach:
- Manual episode generation allows strategic use of API credits
- Early episodes (E01-E09) archived as developmental work with POV annotations
- Fresh narrative restart at E10+ with refined storytelling
- Transparent about creative process and growth

## License

MIT License - Open source for the community

## Related Projects

Part of the Ludarium Behavioral Coordination Platform ecosystem:
- Meta-project: `~/devvyn-meta-project/` (coordination, patterns, infrastructure)
- Bridge: `~/infrastructure/agent-bridge/` (agent messaging)
