#!/usr/bin/env python3
"""
Character Voice Mapper for Dramatic Audio Readings

Extends doc-to-audio.py VoiceMapper to support:
- Dynamic character-to-voice allocation
- CHARACTER_<name> tags beyond fixed NARRATOR/CODE/QUOTE
- Flexible voice palette management
- Character metadata (gender, age, role) → voice selection

Usage:
    from character_voice_mapper import CharacterVoiceMapper

    mapper = CharacterVoiceMapper(
        characters=['Sheriff', 'Sarah', 'Jack'],
        narrator_voice='Aman'
    )

    voice = mapper.get_voice('CHARACTER_Sheriff')  # → 'Jamie'
    voice = mapper.get_voice('NARRATOR')  # → 'Aman'
"""

from dataclasses import dataclass


@dataclass
class CharacterProfile:
    """Character metadata for voice selection"""

    name: str
    gender: str | None = None  # 'male', 'female', 'neutral'
    age: str | None = None  # 'young', 'middle', 'old'
    role: str | None = None  # 'authority', 'educator', 'service', etc.
    personality: list[str] | None = None  # ['cautious', 'direct', ...]
    voice_characteristics: str | None = None  # Free-form description
    occupation: str | None = None  # Job title
    backstory: str | None = None  # Background info


# Personality-to-voice matching rules
PERSONALITY_VOICE_AFFINITY = {
    # Personality trait → preferred voice characteristics
    "authoritative": ["authority", "broadcaster", "narrator"],
    "suspicious": ["authority", "character"],
    "direct": ["authority", "professional"],
    "cautious": ["educator", "professional"],
    "precise": ["educator", "professional"],
    "nervous": ["character", "neutral"],
    "evasive": ["character"],
    "casual": ["character", "storyteller"],
    "warm": ["storyteller", "narrator"],
    "mysterious": ["dramatic", "character"],
    "wise": ["elder", "storyteller"],
    "energetic": ["character", "narrator"],
    "melancholic": ["dramatic", "narrator"],
    "playful": ["character", "narrator"],
}

ROLE_VOICE_AFFINITY = {
    # Role → preferred voice types
    "authority": ["authority", "broadcaster"],
    "educator": ["educator", "professional", "narrator"],
    "service": ["character", "neutral"],
    "outsider": ["character", "dramatic"],
    "merchant": ["character", "professional"],
    "elder": ["elder", "storyteller"],
    "youth": ["character"],
}


class VoicePalette:
    """Manages available TTS voices and their characteristics"""

    def __init__(self, provider: str = "macos"):
        """Initialize voice palette for specified provider"""
        self.provider = provider
        self.voices = self._init_voice_catalog()

    def _init_voice_catalog(self) -> dict[str, dict]:
        """Initialize voice catalog with metadata"""

        if self.provider == "macos":
            return {
                # Premium UK/AU voices
                "Jamie": {
                    "type": "Premium",
                    "gender": "male",
                    "accent": "UK",
                    "age": "middle",
                    "characteristics": "warm, professional, authoritative",
                },
                "Lee": {
                    "type": "Premium",
                    "gender": "male",
                    "accent": "AU",
                    "age": "middle",
                    "characteristics": "clear, engaging, casual",
                },
                "Serena": {
                    "type": "Premium",
                    "gender": "female",
                    "accent": "UK",
                    "age": "middle",
                    "characteristics": "elegant, articulate, precise",
                },
                # Siri voices (India)
                "Aman": {
                    "type": "Siri",
                    "gender": "male",
                    "accent": "India",
                    "age": "middle",
                    "characteristics": "clear, distinctive, neutral",
                },
                "Tara": {
                    "type": "Siri",
                    "gender": "female",
                    "accent": "India",
                    "age": "middle",
                    "characteristics": "calm, educational, warm",
                },
                # US voices
                "Alex": {
                    "type": "Enhanced",
                    "gender": "male",
                    "accent": "US",
                    "age": "middle",
                    "characteristics": "neutral, versatile",
                },
                "Samantha": {
                    "type": "Enhanced",
                    "gender": "female",
                    "accent": "US",
                    "age": "middle",
                    "characteristics": "friendly, clear",
                },
                # Specialized
                "Fred": {
                    "type": "Basic",
                    "gender": "male",
                    "accent": "US",
                    "age": "neutral",
                    "characteristics": "robotic, technical, monotone",
                },
            }
        if self.provider == "elevenlabs":
            return {
                # Storytellers (warm, engaging narrators)
                "George": {
                    "voice_id": "JBFqnCBsd6RMkjVDRZzb",
                    "type": "storyteller",
                    "gender": "male",
                    "accent": "british",
                    "age": "middle",
                    "characteristics": "warm, captivating storyteller",
                },
                "Brian": {
                    "voice_id": "nPczCjzI2devNBz1zQrb",
                    "type": "narrator",
                    "gender": "male",
                    "accent": "american",
                    "age": "middle",
                    "characteristics": "deep, resonant, comforting",
                },
                # Authority figures
                "Adam": {
                    "voice_id": "pNInz6obpgDQGcFmaJgB",
                    "type": "authority",
                    "gender": "male",
                    "accent": "american",
                    "age": "middle",
                    "characteristics": "dominant, firm, authoritative",
                },
                "Daniel": {
                    "voice_id": "onwK4e9ZLuTAKqWW03F9",
                    "type": "broadcaster",
                    "gender": "male",
                    "accent": "british",
                    "age": "middle",
                    "characteristics": "steady, professional",
                },
                # Female voices
                "Alice": {
                    "voice_id": "Xb7hH8MSUJpSbSDYk0k2",
                    "type": "educator",
                    "gender": "female",
                    "accent": "british",
                    "age": "middle",
                    "characteristics": "clear, engaging, educational",
                },
                "Sarah": {
                    "voice_id": "EXAVITQu4vr4xnSDxMaL",
                    "type": "narrator",
                    "gender": "female",
                    "accent": "american",
                    "age": "young",
                    "characteristics": "mature, reassuring, confident",
                },
                "Matilda": {
                    "voice_id": "XrExE9yKIg1WjnnlVkGX",
                    "type": "professional",
                    "gender": "female",
                    "accent": "american",
                    "age": "middle",
                    "characteristics": "knowledgeable, professional",
                },
                "Lily": {
                    "voice_id": "pFZP5JQG7iQjIQuC4Bku",
                    "type": "dramatic",
                    "gender": "female",
                    "accent": "british",
                    "age": "middle",
                    "characteristics": "velvety, theatrical, actress",
                },
                # Character voices (for dramatic readings)
                "Charlie": {
                    "voice_id": "IKne3meq5aSn9XLyUdCD",
                    "type": "character",
                    "gender": "male",
                    "accent": "australian",
                    "age": "young",
                    "characteristics": "deep, confident, energetic",
                },
                "Callum": {
                    "voice_id": "N2lVS1w4EtoT3dr4eOWO",
                    "type": "character",
                    "gender": "male",
                    "accent": "american",
                    "age": "middle",
                    "characteristics": "husky, trickster, mischievous",
                },
                "Harry": {
                    "voice_id": "SOYHLrjzK2X1ezoPC6cr",
                    "type": "character",
                    "gender": "male",
                    "accent": "american",
                    "age": "young",
                    "characteristics": "fierce, warrior, intense",
                },
                "Bill": {
                    "voice_id": "pqHfZKP75CvOlQylNhV4",
                    "type": "elder",
                    "gender": "male",
                    "accent": "american",
                    "age": "old",
                    "characteristics": "wise, mature, balanced",
                },
                "Jessica": {
                    "voice_id": "cgSgspJ2msm6clMCkdW9",
                    "type": "character",
                    "gender": "female",
                    "accent": "american",
                    "age": "young",
                    "characteristics": "playful, bright, warm",
                },
                "Laura": {
                    "voice_id": "FGY2WhTYpPnrIDTdsKH5",
                    "type": "character",
                    "gender": "female",
                    "accent": "american",
                    "age": "young",
                    "characteristics": "enthusiast, quirky, energetic",
                },
                # Neutral voices
                "River": {
                    "voice_id": "SAz9YHcvj6GT2YYXdXww",
                    "type": "neutral",
                    "gender": "neutral",
                    "accent": "american",
                    "age": "middle",
                    "characteristics": "relaxed, neutral, informative",
                },
            }
        # For OpenAI or other providers
        return {}

    def get_voices_by_criteria(
        self,
        gender: str | None = None,
        age: str | None = None,
        accent: str | None = None,
        exclude: set[str] | None = None,
    ) -> list[str]:
        """Get voices matching criteria"""

        exclude = exclude or set()
        matching = []

        for voice_name, metadata in self.voices.items():
            if voice_name in exclude:
                continue

            # Check criteria
            if gender and metadata.get("gender") != gender:
                continue
            if age and metadata.get("age") != age:
                continue
            if accent and metadata.get("accent") != accent:
                continue

            matching.append(voice_name)

        return matching

    def get_voice_id(self, voice_name: str) -> str | None:
        """Get the voice_id for ElevenLabs voices (returns name for macOS)"""
        if voice_name not in self.voices:
            return voice_name  # Fallback to name itself
        voice_data = self.voices[voice_name]
        return voice_data.get("voice_id", voice_name)

    def get_best_match(
        self,
        character: CharacterProfile,
        exclude: set[str] | None = None,
        prefer_accent: str | None = None,
    ) -> str | None:
        """
        Get best voice match for character using intelligent personality matching.

        Scoring system:
        - Gender match: +10 points
        - Age match: +5 points
        - Voice type matches personality: +3 points per match
        - Voice type matches role: +4 points per match
        - Accent preference: +2 points
        """
        exclude = exclude or set()

        # Score all available voices
        scores: dict[str, int] = {}

        for voice_name, metadata in self.voices.items():
            if voice_name in exclude:
                continue

            score = 0

            # Gender match (strong preference)
            if character.gender and metadata.get("gender") == character.gender:
                score += 10
            elif character.gender and metadata.get("gender") == "neutral":
                score += 5  # Neutral voices work for anyone

            # Age match
            if character.age and metadata.get("age") == character.age:
                score += 5

            # Personality → voice type affinity
            voice_type = metadata.get("type", "")
            if character.personality:
                for trait in character.personality:
                    trait_lower = trait.lower()
                    if trait_lower in PERSONALITY_VOICE_AFFINITY:
                        preferred_types = PERSONALITY_VOICE_AFFINITY[trait_lower]
                        if voice_type in preferred_types:
                            score += 3

            # Role → voice type affinity
            if character.role:
                role_lower = character.role.lower()
                if role_lower in ROLE_VOICE_AFFINITY:
                    preferred_types = ROLE_VOICE_AFFINITY[role_lower]
                    if voice_type in preferred_types:
                        score += 4

            # Accent preference
            if prefer_accent and metadata.get("accent") == prefer_accent:
                score += 2

            scores[voice_name] = score

        if not scores:
            return None

        # Return highest scoring voice
        best_voice = max(scores.keys(), key=lambda v: scores[v])
        return best_voice

    def get_best_match_legacy(
        self,
        character: CharacterProfile,
        exclude: set[str] | None = None,
        prefer_accent: str | None = None,
    ) -> str | None:
        """Legacy matching (gender + age only)"""

        # Try exact match first
        candidates = self.get_voices_by_criteria(
            gender=character.gender, age=character.age, exclude=exclude
        )

        if not candidates:
            # Relax age constraint
            candidates = self.get_voices_by_criteria(
                gender=character.gender, exclude=exclude
            )

        if not candidates:
            # Relax all constraints
            candidates = [v for v in self.voices.keys() if v not in (exclude or set())]

        if not candidates:
            return None

        # Prefer specific accents if requested
        if prefer_accent:
            preferred = [
                c for c in candidates if self.voices[c].get("accent") == prefer_accent
            ]
            if preferred:
                return preferred[0]

        # Return first match
        return candidates[0]


class CharacterVoiceMapper:
    """Maps characters to TTS voices for dramatic readings"""

    def __init__(
        self,
        characters: list[str] | list[CharacterProfile] | None = None,
        narrator_voice: str = "Aman",
        provider: str = "macos",
        voice_palette: VoicePalette | None = None,
        prefer_accent_diversity: bool = True,
    ):
        """
        Initialize character voice mapper

        Args:
            characters: List of character names or CharacterProfile objects
            narrator_voice: Voice to use for narrator
            provider: TTS provider ('macos', 'elevenlabs', 'openai')
            voice_palette: Custom voice palette (auto-created if None)
            prefer_accent_diversity: Try to use different accents for variety
        """
        self.provider = provider
        self.narrator_voice = narrator_voice
        self.prefer_accent_diversity = prefer_accent_diversity

        # Initialize voice palette
        self.palette = voice_palette or VoicePalette(provider)

        # Initialize character mapping
        # For CODE voice: use Fred on macOS, River (neutral) on ElevenLabs
        code_voice = "Fred" if provider == "macos" else "River"
        self.voice_map: dict[str, str] = {
            "NARRATOR": narrator_voice,
            "HEADER": narrator_voice,  # Headers use narrator voice
            "CODE": code_voice,  # Code blocks use distinct/neutral voice
            "QUOTE": narrator_voice,  # Quotes use narrator by default
        }

        # Track used voices to ensure diversity
        self.used_voices: set[str] = {narrator_voice, code_voice}

        # Allocate voices for characters
        if characters:
            self._allocate_character_voices(characters)

    def _allocate_character_voices(
        self, characters: list[str] | list[CharacterProfile]
    ) -> None:
        """Allocate voices to characters"""

        for char in characters:
            # Convert string to CharacterProfile if needed
            if isinstance(char, str):
                char_profile = CharacterProfile(name=char)
            else:
                char_profile = char

            # Get best voice match
            voice = self.palette.get_best_match(char_profile, exclude=self.used_voices)

            if voice is None:
                # No unused voices left, reuse from palette
                # Prefer voices not used as narrator
                available = [
                    v for v in self.palette.voices.keys() if v != self.narrator_voice
                ]
                voice = available[0] if available else "Alex"

            # Map CHARACTER_<name> → voice
            char_tag = f"CHARACTER_{char_profile.name}"
            self.voice_map[char_tag] = voice
            self.used_voices.add(voice)

    def get_voice(self, content_type: str) -> str:
        """Get voice for content type (NARRATOR, CHARACTER_<name>, etc.)"""

        # Direct lookup
        if content_type in self.voice_map:
            return self.voice_map[content_type]

        # Fallback to narrator
        return self.narrator_voice

    def add_character(
        self, character: str | CharacterProfile, voice: str | None = None
    ) -> str:
        """
        Add character after initialization

        Args:
            character: Character name or profile
            voice: Specific voice to use (auto-allocated if None)

        Returns:
            Allocated voice name
        """

        # Convert to profile if string
        if isinstance(character, str):
            char_profile = CharacterProfile(name=character)
        else:
            char_profile = character

        char_tag = f"CHARACTER_{char_profile.name}"

        # Check if already mapped
        if char_tag in self.voice_map:
            return self.voice_map[char_tag]

        # Use specified voice or auto-allocate
        if voice:
            allocated_voice = voice
        else:
            allocated_voice = self.palette.get_best_match(
                char_profile, exclude=self.used_voices
            )
            if not allocated_voice:
                # Reuse voices if necessary
                available = [
                    v for v in self.palette.voices.keys() if v != self.narrator_voice
                ]
                allocated_voice = available[0] if available else "Alex"

        # Add mapping
        self.voice_map[char_tag] = allocated_voice
        self.used_voices.add(allocated_voice)

        return allocated_voice

    def get_character_mapping(self) -> dict[str, str]:
        """Get all character-to-voice mappings (excludes NARRATOR, etc.)"""

        return {
            tag: voice
            for tag, voice in self.voice_map.items()
            if tag.startswith("CHARACTER_")
        }

    def print_mapping(self) -> None:
        """Print voice mapping (for debugging)"""

        print("\n=== Voice Mapping ===")
        print(f"Narrator: {self.voice_map['NARRATOR']}")
        print("\nCharacters:")

        char_mappings = self.get_character_mapping()
        for char_tag, voice in sorted(char_mappings.items()):
            char_name = char_tag.replace("CHARACTER_", "")
            voice_info = self.palette.voices.get(voice, {})
            print(
                f"  {char_name:20s} → {voice:12s} ({voice_info.get('accent', '?')}, {voice_info.get('characteristics', '?')})"
            )

        print("\nSpecial:")
        print(f"  Code Blocks: {self.voice_map['CODE']}")


# Example usage
if __name__ == "__main__":
    # Example 1: Simple character names
    print("=== Example 1: Simple Names ===")
    mapper = CharacterVoiceMapper(
        characters=["Sheriff", "Sarah", "Jack"], narrator_voice="Aman"
    )
    mapper.print_mapping()

    # Example 2: Character profiles with metadata
    print("\n=== Example 2: Character Profiles ===")
    characters = [
        CharacterProfile(
            name="Sheriff",
            gender="male",
            age="middle",
            role="authority",
            personality=["authoritative", "suspicious"],
        ),
        CharacterProfile(
            name="Sarah",
            gender="female",
            age="middle",
            role="educator",
            personality=["cautious", "precise"],
        ),
        CharacterProfile(
            name="Jack",
            gender="male",
            age="middle",
            role="service",
            personality=["casual", "nervous"],
        ),
    ]

    mapper2 = CharacterVoiceMapper(characters=characters, narrator_voice="Aman")
    mapper2.print_mapping()

    # Example 3: Dynamic character addition
    print("\n=== Example 3: Dynamic Addition ===")
    mapper3 = CharacterVoiceMapper(narrator_voice="Aman")
    mapper3.add_character("Deputy")
    mapper3.add_character(CharacterProfile(name="Stranger", gender="male", age="old"))
    mapper3.print_mapping()

    # Test voice retrieval
    print("\n=== Voice Retrieval ===")
    print(f"Sheriff speaks with: {mapper2.get_voice('CHARACTER_Sheriff')}")
    print(f"Sarah speaks with: {mapper2.get_voice('CHARACTER_Sarah')}")
    print(f"Narrator uses: {mapper2.get_voice('NARRATOR')}")
    print(f"Unknown character defaults to: {mapper2.get_voice('CHARACTER_Unknown')}")
