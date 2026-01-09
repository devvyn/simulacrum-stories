"""Tests for simulacrum.types module."""

import pytest

from simulacrum.types import (
    is_character_dict,
    is_event_dict,
    is_secret_dict,
    is_location_dict,
    is_world_state_dict,
    validate_character_data,
    validate_world_state,
)


class TestIsCharacterDict:
    """Tests for is_character_dict type guard."""

    def test_valid_minimal(self):
        """Minimal valid character has just a name."""
        data = {"name": "Sheriff"}
        assert is_character_dict(data) is True

    def test_valid_full(self):
        """Full character with all fields."""
        data = {
            "name": "Sarah",
            "role": "educator",
            "personality": ["cautious", "precise"],
            "secrets": ["saw something at dawn"],
            "knowledge": ["mysterious figure"],
            "voice_characteristics": "soft, measured",
            "gender": "female",
            "age": "young",
        }
        assert is_character_dict(data) is True

    def test_invalid_missing_name(self):
        """Character without name is invalid."""
        data = {"role": "authority", "personality": ["stern"]}
        assert is_character_dict(data) is False

    def test_invalid_name_not_string(self):
        """Name must be a string."""
        data = {"name": 123}
        assert is_character_dict(data) is False

    def test_invalid_personality_not_list(self):
        """Personality must be a list if present."""
        data = {"name": "Jack", "personality": "nervous"}
        assert is_character_dict(data) is False

    def test_invalid_secrets_not_list(self):
        """Secrets must be a list if present."""
        data = {"name": "Jack", "secrets": "a secret"}
        assert is_character_dict(data) is False

    def test_invalid_not_dict(self):
        """Non-dict input is invalid."""
        assert is_character_dict("not a dict") is False
        assert is_character_dict(None) is False
        assert is_character_dict([]) is False


class TestIsEventDict:
    """Tests for is_event_dict type guard."""

    def test_valid_minimal(self):
        """Minimal valid event has just a description."""
        data = {"description": "The bakery burned down"}
        assert is_event_dict(data) is True

    def test_valid_full(self):
        """Full event with all fields."""
        data = {
            "description": "Fire at Peterson's bakery",
            "date": "1952-03-15",
            "participants": ["Sheriff", "Peterson"],
            "witnesses": ["Sarah", "Jack"],
            "significance": "high",
            "consequences": ["Investigation opened", "Town tension rises"],
        }
        assert is_event_dict(data) is True

    def test_invalid_missing_description(self):
        """Event without description is invalid."""
        data = {"date": "1952-03-15", "participants": ["Sheriff"]}
        assert is_event_dict(data) is False

    def test_invalid_participants_not_list(self):
        """Participants must be a list if present."""
        data = {"description": "Something happened", "participants": "Sheriff"}
        assert is_event_dict(data) is False


class TestIsSecretDict:
    """Tests for is_secret_dict type guard."""

    def test_valid_minimal(self):
        """Minimal valid secret has just a description."""
        data = {"description": "Someone started the fire deliberately"}
        assert is_secret_dict(data) is True

    def test_valid_full(self):
        """Full secret with all fields."""
        data = {
            "description": "The fire was arson",
            "known_by": ["Sarah"],
            "consequences_if_revealed": "Town scandal",
            "dramatic_potential": "high",
        }
        assert is_secret_dict(data) is True

    def test_invalid_missing_description(self):
        """Secret without description is invalid."""
        data = {"known_by": ["Sarah"]}
        assert is_secret_dict(data) is False

    def test_invalid_known_by_not_list(self):
        """known_by must be a list if present."""
        data = {"description": "A secret", "known_by": "Sarah"}
        assert is_secret_dict(data) is False


class TestIsLocationDict:
    """Tests for is_location_dict type guard."""

    def test_valid_minimal(self):
        """Minimal valid location has just a name."""
        data = {"name": "General Store"}
        assert is_location_dict(data) is True

    def test_valid_full(self):
        """Full location with all fields."""
        data = {
            "name": "Peterson's Bakery",
            "description": "A charred ruin on Main Street",
            "atmosphere": "haunting, acrid smell of smoke",
            "associated_characters": ["Peterson", "Sarah"],
        }
        assert is_location_dict(data) is True

    def test_invalid_missing_name(self):
        """Location without name is invalid."""
        data = {"description": "A place"}
        assert is_location_dict(data) is False


class TestIsWorldStateDict:
    """Tests for is_world_state_dict type guard."""

    def test_valid_empty(self):
        """Empty dict is valid (all fields optional at top level)."""
        data = {}
        assert is_world_state_dict(data) is True

    def test_valid_with_characters(self):
        """World with valid characters."""
        data = {
            "characters": [
                {"name": "Sheriff"},
                {"name": "Sarah", "role": "educator"},
            ]
        }
        assert is_world_state_dict(data) is True

    def test_valid_full(self):
        """Full world state."""
        data = {
            "town": {"name": "Millbrook", "time_period": "1952"},
            "characters": [{"name": "Sheriff"}],
            "events": [{"description": "Fire at bakery"}],
            "secrets": [{"description": "Arson"}],
            "locations": [{"name": "General Store"}],
        }
        assert is_world_state_dict(data) is True

    def test_invalid_characters_not_list(self):
        """Characters must be a list."""
        data = {"characters": {"name": "Sheriff"}}
        assert is_world_state_dict(data) is False

    def test_invalid_character_in_list(self):
        """Invalid character in list fails validation."""
        data = {"characters": [{"role": "authority"}]}  # Missing name
        assert is_world_state_dict(data) is False

    def test_invalid_events_not_list(self):
        """Events must be a list."""
        data = {"events": {"description": "Something"}}
        assert is_world_state_dict(data) is False

    def test_invalid_event_in_list(self):
        """Invalid event in list fails validation."""
        data = {"events": [{"date": "1952-03-15"}]}  # Missing description
        assert is_world_state_dict(data) is False


class TestValidateCharacterData:
    """Tests for validate_character_data helper."""

    def test_valid_returns_data(self):
        """Valid data is returned unchanged."""
        data = {"name": "Sheriff", "role": "authority"}
        result = validate_character_data(data)
        assert result == data

    def test_invalid_raises(self):
        """Invalid data raises ValueError."""
        with pytest.raises(ValueError, match="Invalid character data"):
            validate_character_data({"role": "authority"})


class TestValidateWorldState:
    """Tests for validate_world_state helper."""

    def test_valid_returns_data(self):
        """Valid data is returned unchanged."""
        data = {"characters": [{"name": "Sheriff"}]}
        result = validate_world_state(data)
        assert result == data

    def test_invalid_raises(self):
        """Invalid data raises ValueError."""
        with pytest.raises(ValueError, match="Invalid world state"):
            validate_world_state({"characters": [{"role": "authority"}]})
