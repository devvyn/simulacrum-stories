#!/usr/bin/env python3
"""
Get context for the next episode of a series.

Usage:
    ./get-next-episode-context.py <series-name>

Outputs JSON with all context needed to generate the next episode.
"""

import json
import sys
from pathlib import Path

REGISTRY_PATH = Path(__file__).parent.parent / "data" / "simulacrum-series.json"

CONTEXT_PROMPTS = [
    "{pov} discovers something that changes everything",
    "A confrontation forces {pov} to make a difficult choice",
    "{pov} overhears a conversation they weren't meant to hear",
    "The past catches up with {pov} in an unexpected way",
    "{pov} must decide whether to reveal what they know",
    "A visitor arrives with questions about {pov}'s secrets",
    "{pov} finds evidence that implicates someone they trust",
    "An old wound reopens for {pov}",
]


def main():
    if len(sys.argv) < 2:
        print("Usage: get-next-episode-context.py <series-name>", file=sys.stderr)
        sys.exit(1)

    series_name = sys.argv[1].lower()

    # Load registry
    with open(REGISTRY_PATH) as f:
        registry = json.load(f)

    if series_name not in registry:
        print(f"Series not found: {series_name}", file=sys.stderr)
        print(f"Available series: {', '.join(registry.keys())}", file=sys.stderr)
        sys.exit(1)

    series = registry[series_name]

    # Calculate next episode info
    next_episode = series["episode_count"] + 1
    next_pov_index = (series["last_pov_index"] + 1) % len(series["pov_rotation"])
    next_pov = series["pov_rotation"][next_pov_index]

    # Get context prompt
    context_prompt = CONTEXT_PROMPTS[next_episode % len(CONTEXT_PROMPTS)]
    context = context_prompt.format(pov=next_pov)

    # Load world
    world_path = Path(series["world_file"])
    if world_path.exists():
        with open(world_path) as f:
            world = json.load(f)
    else:
        world = None
        print(f"Warning: World file not found: {world_path}", file=sys.stderr)

    # Build output
    output = {
        "series": {
            "name": series["name"],
            "setting": series["setting"],
            "current_arc": series["current_arc"],
            "themes": series["themes"],
        },
        "next_episode": {
            "number": next_episode,
            "pov_character": next_pov,
            "pov_index": next_pov_index,
            "context": context,
            "template": series["scene_templates"][next_episode % len(series["scene_templates"])],
        },
        "world": world,
        "output_path": f"output/episodes/{series_name}/E{next_episode:02d}-scene.md",
    }

    # Output as JSON
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
