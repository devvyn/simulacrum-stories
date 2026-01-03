#!/usr/bin/env python3
"""
Relationship Signals Extractor

Extracts privacy-safe relationship dynamics from Messages.app database
and converts them to narrative-friendly descriptors for world generation.

PRIVACY BOUNDARY:
- ✅ EXTRACTS: Counts, ratios, timing patterns, frequency metrics
- ⛔ NEVER EXTRACTS: Message content, names, phone numbers, specifics

Usage:
    # Extract signals and output as JSON
    ./relationship_signals.py --output signals.json

    # Generate narrative descriptors
    ./relationship_signals.py --narrative --output relationships.json

    # Feed directly into world generator
    ./relationship_signals.py --for-world --count 5 --output world-hints.json
"""

import argparse
import hashlib
import json
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

# =============================================================================
# Privacy-Safe Signal Structures
# =============================================================================


@dataclass
class RelationshipSignal:
    """Privacy-safe relationship metrics (no PII)"""

    relationship_id: str  # Hashed, not actual contact

    # Volume metrics
    total_messages: int
    messages_sent: int
    messages_received: int

    # Ratio metrics (0.0 to 1.0)
    balance_ratio: float  # 0.5 = balanced, 0.0 = all received, 1.0 = all sent

    # Temporal metrics
    relationship_age_days: int
    days_since_last_contact: int
    avg_messages_per_month: float

    # Pattern metrics
    is_active: bool  # Contact in last 30 days
    is_long_term: bool  # > 1 year history
    is_high_volume: bool  # > 500 messages
    communication_style: str  # "balanced", "listener", "initiator", "dormant"


@dataclass
class NarrativeDescriptor:
    """Narrative-ready relationship description"""

    archetype: str  # "close_friend", "mentor", "acquaintance", etc.
    warmth: str  # "warm", "cool", "neutral", "complex"
    power_dynamic: str  # "equal", "deferential", "dominant", "shifting"
    communication_style: str  # "frequent_casual", "rare_formal", "burst_pattern"
    tension_potential: str  # "low", "medium", "high"
    narrative_hooks: list  # Potential story elements


# =============================================================================
# Signal Extractor
# =============================================================================


class RelationshipSignalExtractor:
    """Extract privacy-safe signals from Messages database"""

    APPLE_EPOCH = datetime(2001, 1, 1)

    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            db_path = Path.home() / "Library" / "Messages" / "chat.db"

        self.db_path = db_path
        if not self.db_path.exists():
            raise FileNotFoundError(f"Messages database not found: {self.db_path}")

    def _hash_contact(self, contact: str) -> str:
        """Hash contact info for privacy - one-way, non-reversible"""
        return hashlib.sha256(contact.encode()).hexdigest()[:12]

    def _convert_timestamp(self, ts: int) -> datetime:
        """Convert Apple timestamp to datetime"""
        if ts == 0:
            return self.APPLE_EPOCH
        return self.APPLE_EPOCH + timedelta(seconds=ts / 1_000_000_000)

    def extract_signals(self, min_messages: int = 10) -> list[RelationshipSignal]:
        """
        Extract relationship signals from all contacts.

        Args:
            min_messages: Minimum messages to include relationship

        Returns:
            List of RelationshipSignal objects (privacy-safe)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
        SELECT
            h.id as contact,
            COUNT(*) as total_messages,
            SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as sent,
            SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as received,
            MIN(m.date) as first_ts,
            MAX(m.date) as last_ts
        FROM message m
        JOIN handle h ON m.handle_id = h.ROWID
        WHERE m.item_type = 0
        GROUP BY h.id
        HAVING COUNT(*) >= ?
        ORDER BY COUNT(*) DESC
        """

        cursor.execute(query, (min_messages,))
        rows = cursor.fetchall()
        conn.close()

        now = datetime.now()
        signals = []

        for contact, total, sent, received, first_ts, last_ts in rows:
            first_date = self._convert_timestamp(first_ts) if first_ts else now
            last_date = self._convert_timestamp(last_ts) if last_ts else now

            age_days = max(1, (now - first_date).days)
            days_since = (now - last_date).days

            # Calculate balance ratio (0.5 = perfectly balanced)
            balance = sent / total if total > 0 else 0.5

            # Determine communication style
            if days_since > 180:
                style = "dormant"
            elif balance < 0.3:
                style = "listener"
            elif balance > 0.7:
                style = "initiator"
            else:
                style = "balanced"

            signals.append(
                RelationshipSignal(
                    relationship_id=self._hash_contact(contact),
                    total_messages=total,
                    messages_sent=sent,
                    messages_received=received,
                    balance_ratio=round(balance, 3),
                    relationship_age_days=age_days,
                    days_since_last_contact=days_since,
                    avg_messages_per_month=round(total / max(1, age_days / 30), 1),
                    is_active=days_since <= 30,
                    is_long_term=age_days > 365,
                    is_high_volume=total > 500,
                    communication_style=style,
                )
            )

        return signals

    def extract_group_dynamics(self) -> list[dict]:
        """Extract group chat dynamics (privacy-safe)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
        SELECT
            c.guid as chat_guid,
            COUNT(DISTINCT chj.handle_id) as member_count,
            COUNT(m.ROWID) as message_count
        FROM chat c
        JOIN chat_handle_join chj ON c.ROWID = chj.chat_id
        LEFT JOIN chat_message_join cmj ON c.ROWID = cmj.chat_id
        LEFT JOIN message m ON cmj.message_id = m.ROWID AND m.item_type = 0
        WHERE c.style = 43
        GROUP BY c.guid
        HAVING COUNT(m.ROWID) > 10
        """

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        groups = []
        for guid, members, messages in rows:
            groups.append(
                {
                    "group_id": self._hash_contact(guid),
                    "member_count": members,
                    "total_messages": messages,
                    "avg_per_member": round(messages / max(1, members), 1),
                    "group_size": "small"
                    if members <= 3
                    else "medium"
                    if members <= 7
                    else "large",
                }
            )

        return groups


# =============================================================================
# Narrative Converter
# =============================================================================


class NarrativeConverter:
    """Convert raw signals to narrative-ready descriptors"""

    def signal_to_narrative(self, signal: RelationshipSignal) -> NarrativeDescriptor:
        """Convert a relationship signal to narrative descriptor"""

        # Determine archetype
        if signal.is_high_volume and signal.is_long_term and signal.is_active:
            archetype = "close_confidant"
        elif signal.is_high_volume and signal.is_active:
            archetype = "active_friend"
        elif signal.is_long_term and signal.is_active:
            archetype = "steady_presence"
        elif signal.is_long_term and not signal.is_active:
            archetype = "faded_connection"
        elif signal.avg_messages_per_month > 50:
            archetype = "intense_bond"
        elif signal.avg_messages_per_month < 5:
            archetype = "distant_acquaintance"
        else:
            archetype = "casual_contact"

        # Determine warmth from volume and balance
        if signal.is_high_volume and 0.3 < signal.balance_ratio < 0.7:
            warmth = "warm"
        elif signal.communication_style == "dormant":
            warmth = "cool"
        elif signal.balance_ratio < 0.2 or signal.balance_ratio > 0.8:
            warmth = "complex"
        else:
            warmth = "neutral"

        # Determine power dynamic from balance
        if 0.4 < signal.balance_ratio < 0.6:
            power = "equal"
        elif signal.balance_ratio < 0.35:
            power = "deferential"  # They talk more, you listen
        elif signal.balance_ratio > 0.65:
            power = "dominant"  # You talk more
        else:
            power = "shifting"

        # Determine communication pattern
        if signal.avg_messages_per_month > 100:
            comm_style = "constant_contact"
        elif signal.avg_messages_per_month > 30:
            comm_style = "frequent_casual"
        elif signal.avg_messages_per_month > 10:
            comm_style = "regular_check_ins"
        elif signal.is_long_term:
            comm_style = "rare_but_meaningful"
        else:
            comm_style = "sporadic"

        # Determine tension potential
        if signal.communication_style == "dormant" and signal.is_long_term:
            tension = "high"  # Unresolved history
        elif signal.balance_ratio < 0.2 or signal.balance_ratio > 0.8:
            tension = "medium"  # Imbalanced dynamic
        elif not signal.is_active and signal.is_high_volume:
            tension = "high"  # Relationship cooling
        else:
            tension = "low"

        # Generate narrative hooks
        hooks = []
        if signal.communication_style == "dormant" and signal.is_high_volume:
            hooks.append("What caused the silence after years of closeness?")
        if signal.balance_ratio < 0.25:
            hooks.append("Why do they reach out so much more than you respond?")
        if signal.balance_ratio > 0.75:
            hooks.append("Are they pulling away, or just busy?")
        if signal.is_long_term and signal.avg_messages_per_month < 3:
            hooks.append("A friendship maintained by ritual rather than passion")
        if signal.is_active and signal.is_high_volume:
            hooks.append("The kind of bond where nothing is off-limits")
        if not hooks:
            hooks.append("A relationship in equilibrium—for now")

        return NarrativeDescriptor(
            archetype=archetype,
            warmth=warmth,
            power_dynamic=power,
            communication_style=comm_style,
            tension_potential=tension,
            narrative_hooks=hooks,
        )

    def signals_to_world_hints(
        self, signals: list[RelationshipSignal], count: int = 5
    ) -> list[dict]:
        """
        Convert signals to world generation hints.

        Returns character relationship templates inspired by real patterns
        but completely fictionalized.
        """

        # Sort by narrative interest (high tension, unusual patterns)
        def interest_score(s: RelationshipSignal) -> float:
            score = 0
            if s.communication_style == "dormant" and s.is_high_volume:
                score += 10  # Dramatic potential
            if s.balance_ratio < 0.25 or s.balance_ratio > 0.75:
                score += 5  # Power imbalance
            if s.is_long_term:
                score += 3  # History
            if s.is_active:
                score += 2  # Current relevance
            return score

        sorted_signals = sorted(signals, key=interest_score, reverse=True)[:count]

        hints = []
        for i, signal in enumerate(sorted_signals):
            narrative = self.signal_to_narrative(signal)

            # Generate fictional character relationship hint
            hints.append(
                {
                    "relationship_template": i + 1,
                    "archetype": narrative.archetype,
                    "suggested_dynamic": {
                        "warmth": narrative.warmth,
                        "power_balance": narrative.power_dynamic,
                        "communication_frequency": narrative.communication_style,
                        "tension_level": narrative.tension_potential,
                    },
                    "story_seeds": narrative.narrative_hooks,
                    "metrics_inspiration": {
                        "years_of_history": signal.relationship_age_days // 365,
                        "contact_frequency": "high"
                        if signal.avg_messages_per_month > 30
                        else "medium"
                        if signal.avg_messages_per_month > 10
                        else "low",
                        "currently_active": signal.is_active,
                        "communication_style": signal.communication_style,
                    },
                }
            )

        return hints


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Extract privacy-safe relationship signals for narrative generation"
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--raw", action="store_true", help="Output raw signals (default)")
    mode.add_argument(
        "--narrative", action="store_true", help="Output narrative descriptors"
    )
    mode.add_argument(
        "--for-world", action="store_true", help="Output world generation hints"
    )

    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of relationships to include (default: 10)",
    )
    parser.add_argument(
        "--min-messages",
        type=int,
        default=20,
        help="Minimum messages for inclusion (default: 20)",
    )
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument(
        "--include-groups", action="store_true", help="Include group chat dynamics"
    )

    args = parser.parse_args()

    print("Extracting relationship signals...", file=sys.stderr)
    extractor = RelationshipSignalExtractor()
    signals = extractor.extract_signals(min_messages=args.min_messages)

    print(f"  Found {len(signals)} relationships", file=sys.stderr)

    # Limit to count
    signals = signals[: args.count]

    if args.narrative:
        converter = NarrativeConverter()
        output = [asdict(converter.signal_to_narrative(s)) for s in signals]
        print(f"  Converted to {len(output)} narrative descriptors", file=sys.stderr)

    elif args.for_world:
        converter = NarrativeConverter()
        output = converter.signals_to_world_hints(signals, count=args.count)
        print(f"  Generated {len(output)} world hints", file=sys.stderr)

    else:
        output = [asdict(s) for s in signals]

    # Add group dynamics if requested
    if args.include_groups:
        groups = extractor.extract_group_dynamics()
        if isinstance(output, list):
            output = {"relationships": output, "groups": groups}
        print(f"  Added {len(groups)} group dynamics", file=sys.stderr)

    # Output
    result = json.dumps(output, indent=2, default=str)

    if args.output:
        Path(args.output).write_text(result)
        print(f"✅ Written to: {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
