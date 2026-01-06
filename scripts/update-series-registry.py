#!/usr/bin/env python3
"""
Update series registry after episode generation.

Usage:
    ./update-series-registry.py <series-name>

This increments episode_count, rotates POV index, and updates last_episode_at.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

REGISTRY_PATH = Path(__file__).parent.parent / "data" / "simulacrum-series.json"


def main():
    if len(sys.argv) < 2:
        print("Usage: update-series-registry.py <series-name>", file=sys.stderr)
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

    # Store old values for reporting
    old_count = series["episode_count"]
    old_pov_index = series["last_pov_index"]
    pov_rotation = series["pov_rotation"]

    # Update
    series["episode_count"] = old_count + 1
    series["last_pov_index"] = (old_pov_index + 1) % len(pov_rotation)
    series["last_episode_at"] = datetime.now().isoformat()

    # Save
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)

    # Report
    new_pov = pov_rotation[series["last_pov_index"]]
    print(f"Updated {series_name}:", file=sys.stderr)
    print(f"  Episode: {old_count} → {series['episode_count']}", file=sys.stderr)
    print(f"  Next POV: {new_pov}", file=sys.stderr)


if __name__ == "__main__":
    main()
