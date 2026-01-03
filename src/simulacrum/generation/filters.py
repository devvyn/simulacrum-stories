#!/usr/bin/env python3
"""
Series-Specific Signal Filtering

Extracts relationship signals from iMessage data but filters them differently
for each series to create distinct narrative feels while maintaining emotional
authenticity.

Usage:
    from series_signal_filters import get_signals_for_series

    # Get signals optimized for Saltmere (family/generational)
    saltmere_hints = get_signals_for_series("saltmere", count=5)

    # Get signals optimized for Millbrook (authority/community)
    millbrook_hints = get_signals_for_series("millbrook", count=5)
"""

import sys
from pathlib import Path

# Import relationship signal tools
try:
    from relationship_signals import (
        NarrativeConverter,
        RelationshipSignal,
        RelationshipSignalExtractor,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from relationship_signals import (
        NarrativeConverter,
        RelationshipSignal,
        RelationshipSignalExtractor,
    )


# =============================================================================
# Series-Specific Filters
# =============================================================================


def filter_for_saltmere(signals: list[RelationshipSignal]) -> list[RelationshipSignal]:
    """
    Filter signals for Saltmere: family/generational themes

    Prioritizes:
    - Long-term dormant relationships (old secrets, unresolved tensions)
    - Deferential power dynamics (generational hierarchy)
    - High warmth + high tension (family complexity)
    - Faded connections (lost relationships that haunt)
    """

    def saltmere_score(s: RelationshipSignal) -> float:
        score = 0.0

        # Prioritize long-term relationships (generational depth)
        if s.is_long_term:
            score += 8.0

        # Dormant high-volume = "What happened between us?"
        if s.communication_style == "dormant" and s.is_high_volume:
            score += 10.0

        # Deferential dynamics = parent/elder relationships
        if s.balance_ratio < 0.35:
            score += 6.0

        # Long silence after contact = unresolved history
        if s.days_since_last_contact > 180 and s.total_messages > 200:
            score += 7.0

        # Listener role = respect for elders, family deference
        if s.communication_style == "listener":
            score += 5.0

        # Moderate volume, long-term = steady family presence
        if s.is_long_term and 50 < s.total_messages < 500:
            score += 4.0

        return score

    return sorted(signals, key=saltmere_score, reverse=True)


def filter_for_millbrook(signals: list[RelationshipSignal]) -> list[RelationshipSignal]:
    """
    Filter signals for Millbrook: authority/community themes

    Prioritizes:
    - Unequal power dynamics (authority figures, social hierarchy)
    - Frequent casual contact (small-town proximity, gossip)
    - Shifting alliances (changing balance ratios)
    - Dominant patterns (those who lead/direct)
    """

    def millbrook_score(s: RelationshipSignal) -> float:
        score = 0.0

        # Dominant dynamics = authority figures, sheriff-like
        if s.balance_ratio > 0.65:
            score += 8.0

        # Highly unbalanced (either way) = power hierarchy
        if s.balance_ratio < 0.25 or s.balance_ratio > 0.75:
            score += 6.0

        # Frequent casual = neighbors, small-town encounters
        if s.communication_style in ["frequent_casual", "balanced"]:
            score += 7.0

        # Active relationships = current community dynamics
        if s.is_active:
            score += 5.0

        # Medium volume, active = regular community interaction
        if s.is_active and 100 < s.total_messages < 1000:
            score += 4.0

        # Initiator role = community leaders, organizers
        if s.communication_style == "initiator":
            score += 6.0

        # Recent contact + high volume = intense current drama
        if s.days_since_last_contact < 30 and s.is_high_volume:
            score += 3.0

        return score

    return sorted(signals, key=millbrook_score, reverse=True)


# =============================================================================
# Series Context Enrichment
# =============================================================================

SERIES_CONTEXT = {
    "saltmere": {
        "period": "1970s",
        "setting": "Coastal fishing village, Pacific Northwest",
        "themes": ["family-secrets", "generational-conflict", "environmental-mystery"],
        "social_structure": "Old families, generational ties, insularity",
        "economic_context": "Fishing industry consolidation, old ways vs new",
        "cultural_backdrop": "Post-counterculture, environmental awakening",
        "technology": "Landlines, local radio, CB radios",
        "narrative_lens": "Environmental mystery mirrors family secrets",
    },
    "millbrook": {
        "period": "1980s",
        "setting": "Small industrial town, American Midwest",
        "themes": ["authority-secrets", "economic-decay", "moral-choices"],
        "social_structure": "Formal hierarchy (sheriff, teacher, workers)",
        "economic_context": "Mill closure, unemployment, desperation",
        "cultural_backdrop": "Reagan era, traditional values under pressure",
        "technology": "Early computers, cable TV, answering machines",
        "narrative_lens": "Economic collapse reveals moral compromises",
    },
}


# =============================================================================
# Public API
# =============================================================================


def get_signals_for_series(
    series_name: str, count: int = 5, min_messages: int = 50
) -> list[dict] | None:
    """
    Get relationship signals filtered and optimized for a specific series

    Args:
        series_name: "saltmere" or "millbrook"
        count: Number of relationship hints to return
        min_messages: Minimum messages to consider a relationship

    Returns:
        List of relationship hints ready for world generation,
        or None if extraction fails
    """

    series_name = series_name.lower()

    if series_name not in ["saltmere", "millbrook"]:
        raise ValueError(
            f"Unknown series: {series_name}. Must be 'saltmere' or 'millbrook'"
        )

    try:
        # Extract raw signals
        extractor = RelationshipSignalExtractor()
        all_signals = extractor.extract_signals(min_messages=min_messages)

        if not all_signals:
            print(
                f"Warning: No relationship signals found (min_messages={min_messages})",
                file=sys.stderr,
            )
            return None

        # Filter for series-specific patterns
        if series_name == "saltmere":
            filtered_signals = filter_for_saltmere(all_signals)
        else:  # millbrook
            filtered_signals = filter_for_millbrook(all_signals)

        # Take top matches
        top_signals = filtered_signals[:count]

        # Convert to narrative hints
        converter = NarrativeConverter()
        hints = converter.signals_to_world_hints(top_signals, count=count)

        # Enrich with series context
        context = SERIES_CONTEXT[series_name]
        for hint in hints:
            hint["series_context"] = {
                "period": context["period"],
                "setting_type": context["setting"],
                "cultural_backdrop": context["cultural_backdrop"],
            }

        print(
            f"Extracted {len(hints)} relationship patterns for {series_name.title()}",
            file=sys.stderr,
        )
        print(f"  Themes: {', '.join(context['themes'])}", file=sys.stderr)

        return hints

    except FileNotFoundError as e:
        print(f"Warning: Could not access Messages database: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Warning: Signal extraction failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return None


def get_series_context(series_name: str) -> dict:
    """Get enrichment context for a series"""
    series_name = series_name.lower()
    if series_name not in SERIES_CONTEXT:
        raise ValueError(f"Unknown series: {series_name}")
    return SERIES_CONTEXT[series_name]


# =============================================================================
# CLI for Testing
# =============================================================================


def main():
    """Test the series-specific filtering"""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Test series-specific signal filtering"
    )
    parser.add_argument(
        "series", choices=["saltmere", "millbrook"], help="Series to filter for"
    )
    parser.add_argument(
        "--count", type=int, default=5, help="Number of hints to generate"
    )
    parser.add_argument(
        "--min-messages", type=int, default=50, help="Minimum messages per relationship"
    )
    parser.add_argument("--output", help="Output JSON file (default: stdout)")

    args = parser.parse_args()

    hints = get_signals_for_series(args.series, args.count, args.min_messages)

    if hints:
        output = {
            "series": args.series,
            "context": get_series_context(args.series),
            "relationship_hints": hints,
        }

        if args.output:
            with open(args.output, "w") as f:
                json.dump(output, f, indent=2)
            print(f"\nWrote {len(hints)} hints to {args.output}")
        else:
            print(json.dumps(output, indent=2))
    else:
        print("No signals could be extracted", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
