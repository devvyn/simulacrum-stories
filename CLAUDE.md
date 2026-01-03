# Simulacrum Stories - Agent Instructions

## Project Context

**What**: AI-powered audio storytelling system with multi-voice narration
**Purpose**: Generate daily dramatic audio episodes with emotional depth
**Series**: Saltmere Chronicles (1970s coastal), Millbrook Chronicles (1980s rust belt)

## Key Constraints

### Credential Access
- **NEVER** store API keys in this repository
- Reference meta-project credential managers via environment variables
- Anthropic: `~/devvyn-meta-project/scripts/anthropic-key-manager.sh`
- ElevenLabs: `~/devvyn-meta-project/scripts/elevenlabs-key-manager.sh`

### Budget Management
- Monthly limit: 150,000 characters (ElevenLabs)
- Daily limit: 10,000 characters
- Always check budget before generation
- Track usage in budget manager

### Quality Standards
- Character voice consistency across episodes
- Emotional authenticity from relationship signals
- Scene pacing: 15-20 minutes target per episode
- Podcast-ready RSS feeds with proper metadata

## Common Tasks

### Generate Episode
```bash
uv run python scripts/daily-production.py --series <saltmere|millbrook>
```

### Check Status
```bash
./scripts/status.sh
```

### Publish Feeds
```bash
./scripts/publish-feeds.sh https://your-netlify-url.app
```

### Test Generation (dry run)
```bash
uv run python scripts/scheduler-daemon.py --dry-run
```

## Development Guidelines

### Code Changes
- Maintain package structure (`src/simulacrum/`)
- Update tests when adding features
- Run `uv run ruff check` before committing
- Document emotional modeling enhancements

### Future Enhancements (see docs/enhancement-roadmap.md)
When implementing writer's room or emotional modeling:
- Use bridge messaging for multi-agent coordination
- Store persistent story state in `data/story-state/`
- Quality metrics go to `data/cache/` (regenerable)
- Document new emotional models thoroughly

## Storage Tier

**Project tier**: ICLOUD_PINNED
- Critical creative work
- Multi-device access needed
- Generated audio is valuable output

**Exceptions**:
- `data/cache/`: Regenerable artifacts (OFFLINE if needed)
- `output/`: Can be ICLOUD_SYNC (backed by git + deployment)

## Integration Points

### Meta-Project Dependencies
- Relationship signal extractor (imported from meta-project)
- Credential managers (never duplicated)
- Bridge (if using multi-agent features)
- Knowledge base (for pattern reference)

### Independent Components
- Voice mapping logic
- Scene generation
- Audio production pipeline
- Podcast RSS infrastructure

## Automation

Daily LaunchAgent runs at 6:00 AM and 7:30 AM:
- Checks budget availability
- Generates 2 episodes (alternating series)
- Updates RSS feeds
- Logs to `~/Library/Logs/simulacrum-*.log`

## Troubleshooting

### "Operation not permitted" errors
- LaunchAgent needs to use `uv run --directory` (not system python)
- Check plist configuration

### Budget exceeded
- Check `scripts/status.sh` for current usage
- Wait for daily/monthly reset
- Consider fallback to macOS TTS for testing

### Voice inconsistency
- Verify character profiles in voice mapper
- Check emotional calibration in scene templates
- Review relationship signal extraction

## Reference

Full documentation: `docs/` directory
Enhancement roadmap: `docs/enhancement-roadmap.md`
Series strategies: `docs/series-enrichment-strategy.md`
