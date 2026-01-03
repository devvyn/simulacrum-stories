# Simulacrum Stories

AI-powered audio storytelling with multi-voice narration, emotional modeling, and procedural narrative generation.

## What This Is

Simulacrum generates dramatic audio stories with:
- **Multi-voice narration** using ElevenLabs API
- **Emotional depth** from real relationship signal extraction
- **Procedural worlds** with consistent characters and arcs
- **Daily automation** producing new episodes on schedule
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

# Generate single episode
uv run python scripts/daily-production.py --series saltmere --dry-run

# Check production status
./scripts/status.sh

# Start daily automation (see docs/DEPLOYMENT.md)
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
- Budget tracking and provider management
- RSS feed generation for podcast platforms
- Automated daily production

### Planned (see docs/enhancement-roadmap.md)
- Writer's room multi-agent collaboration
- Dynamic emotional modeling
- Multi-pass narrative generation
- Adaptive storytelling with quality feedback
- Persistent story state tracking

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

**Current Output:**
- Saltmere Chronicles: 7 episodes (23 minutes total)
- Millbrook Chronicles: 9 episodes (35 minutes total)

**Budget Status:**
- Provider: ElevenLabs v3 Alpha (multi-voice)
- Monthly: 140,013 / 150,000 chars remaining (93%)
- Daily limit: 10,000 chars

**Automation:**
- Schedule: 6:00 AM & 7:30 AM daily
- Target: 2 episodes/day
- Last run: Check `scripts/status.sh`

## License

Private project - not for distribution

## Related Projects

Part of the Ludarium Behavioral Coordination Platform ecosystem:
- Meta-project: `~/devvyn-meta-project/` (coordination, patterns, infrastructure)
- Bridge: `~/infrastructure/agent-bridge/` (agent messaging)
