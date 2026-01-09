"""
Type definitions and guards for Simulacrum Stories.

Uses Python 3.13+ typing features:
- TypedDict for JSON structure validation
- TypeIs for bidirectional type narrowing
- Literal for exhaustive matching
"""

from typing import Literal, TypedDict, TypeIs

# =============================================================================
# Literal Types for Exhaustive Matching
# =============================================================================

SceneTemplate = Literal[
    "confrontation",
    "discovery",
    "group_discussion",
    "revelation",
]

EndingType = Literal[
    "cliffhanger",
    "resolution",
    "revelation",
    "unresolved",
]

Significance = Literal["high", "medium", "low"]

CharacterRole = Literal[
    "authority",
    "educator",
    "service",
    "outsider",
    "merchant",
    "supporting",
]


# =============================================================================
# TypedDict Definitions for JSON Structures
# =============================================================================


class CharacterDict(TypedDict, total=False):
    """JSON structure for character data."""

    name: str  # Required
    role: str
    personality: list[str]
    secrets: list[str]
    knowledge: list[str]
    voice_characteristics: str
    gender: str
    age: str | int
    occupation: str
    relationships: dict[str, str]
    backstory: str


class EventDict(TypedDict, total=False):
    """JSON structure for event data."""

    description: str  # Required
    date: str
    participants: list[str]
    witnesses: list[str]
    significance: str
    consequences: list[str]


class SecretDict(TypedDict, total=False):
    """JSON structure for secret data."""

    description: str  # Required
    known_by: list[str]
    consequences_if_revealed: str
    dramatic_potential: str


class LocationDict(TypedDict, total=False):
    """JSON structure for location data."""

    name: str  # Required
    description: str
    atmosphere: str
    associated_characters: list[str]


class TownDict(TypedDict, total=False):
    """JSON structure for town metadata."""

    name: str
    time_period: str
    population: int
    economy: str
    atmosphere: str


class WorldStateDict(TypedDict, total=False):
    """JSON structure for complete world state."""

    town: TownDict
    characters: list[CharacterDict]
    events: list[EventDict]
    secrets: list[SecretDict]
    locations: list[LocationDict]
    themes: list[str]
    generated_at: str


# =============================================================================
# Type Guards (TypeIs for bidirectional narrowing)
# =============================================================================


def is_character_dict(data: dict) -> TypeIs[CharacterDict]:
    """
    Type guard for character JSON validation.

    In Python 3.13+, TypeIs provides bidirectional narrowing:
    - If True: type checker knows data is CharacterDict
    - If False: type checker knows data is NOT CharacterDict
    """
    if not isinstance(data, dict):
        return False
    # Required field
    if not isinstance(data.get("name"), str):
        return False
    # Optional fields - validate types if present
    if "personality" in data and not isinstance(data["personality"], list):
        return False
    if "secrets" in data and not isinstance(data["secrets"], list):
        return False
    if "knowledge" in data and not isinstance(data["knowledge"], list):
        return False
    return True


def is_event_dict(data: dict) -> TypeIs[EventDict]:
    """Type guard for event JSON validation."""
    if not isinstance(data, dict):
        return False
    if not isinstance(data.get("description"), str):
        return False
    if "participants" in data and not isinstance(data["participants"], list):
        return False
    if "witnesses" in data and not isinstance(data["witnesses"], list):
        return False
    return True


def is_secret_dict(data: dict) -> TypeIs[SecretDict]:
    """Type guard for secret JSON validation."""
    if not isinstance(data, dict):
        return False
    if not isinstance(data.get("description"), str):
        return False
    if "known_by" in data and not isinstance(data["known_by"], list):
        return False
    return True


def is_location_dict(data: dict) -> TypeIs[LocationDict]:
    """Type guard for location JSON validation."""
    if not isinstance(data, dict):
        return False
    if not isinstance(data.get("name"), str):
        return False
    return True


def is_world_state_dict(data: dict) -> TypeIs[WorldStateDict]:
    """Type guard for world state JSON validation."""
    if not isinstance(data, dict):
        return False
    # Validate nested structures if present
    if "characters" in data:
        if not isinstance(data["characters"], list):
            return False
        if not all(is_character_dict(c) for c in data["characters"]):
            return False
    if "events" in data:
        if not isinstance(data["events"], list):
            return False
        if not all(is_event_dict(e) for e in data["events"]):
            return False
    return True


def validate_character_data(data: dict) -> CharacterDict:
    """
    Validate and return character data, raising on invalid input.

    Use this at system boundaries (file loading, API responses).
    """
    if not is_character_dict(data):
        raise ValueError(f"Invalid character data: missing or invalid 'name' field: {data}")
    return data


def validate_world_state(data: dict) -> WorldStateDict:
    """
    Validate and return world state data, raising on invalid input.

    Use this at system boundaries (file loading, API responses).
    """
    if not is_world_state_dict(data):
        raise ValueError("Invalid world state data")
    return data
