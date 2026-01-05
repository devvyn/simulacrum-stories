"""Cost tracking for audio drama production"""
from dataclasses import dataclass
from typing import Literal


@dataclass
class ProductionCost:
    """Tracks costs for a single production"""
    
    # LLM costs (Anthropic)
    input_tokens: int
    output_tokens: int
    llm_cost_usd: float
    
    # TTS costs
    characters_used: int
    tts_provider: Literal["macos", "openai", "elevenlabs"]
    tts_cost_usd: float
    
    # Total
    total_cost_usd: float
    
    def __str__(self) -> str:
        """Human-readable cost summary"""
        parts = [
            f"LLM: ${self.llm_cost_usd:.4f} ({self.input_tokens:,} in, {self.output_tokens:,} out)",
            f"TTS: ${self.tts_cost_usd:.4f} ({self.characters_used:,} chars, {self.tts_provider})",
            f"Total: ${self.total_cost_usd:.4f}"
        ]
        return " | ".join(parts)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "llm": {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "cost_usd": round(self.llm_cost_usd, 4)
            },
            "tts": {
                "characters": self.characters_used,
                "provider": self.tts_provider,
                "cost_usd": round(self.tts_cost_usd, 4)
            },
            "total_usd": round(self.total_cost_usd, 4)
        }


class CostCalculator:
    """Calculate production costs based on usage metrics"""
    
    # Anthropic API pricing (as of Jan 2025)
    # https://www.anthropic.com/pricing
    ANTHROPIC_PRICING = {
        "claude-sonnet-4-20250514": {
            "input": 3.00 / 1_000_000,   # $3 per million tokens
            "output": 15.00 / 1_000_000  # $15 per million tokens
        }
    }
    
    # TTS pricing (monthly subscription equivalent per character)
    # macOS: free
    # OpenAI: $15/mo for 1M chars = $0.000015/char
    # ElevenLabs: varies by plan, using Starter ($5/mo, 30K chars) as baseline
    TTS_PRICING = {
        "macos": {
            "per_char": 0.0,
            "note": "Free (macOS built-in)"
        },
        "openai": {
            "per_char": 0.000015,
            "note": "OpenAI TTS-1-HD: $15/1M chars"
        },
        "elevenlabs": {
            "per_char": 0.00022,  # $5/mo ÷ 30K chars, conservative estimate
            "note": "ElevenLabs V3 (varies by plan)"
        }
    }
    
    def calculate(
        self,
        input_tokens: int,
        output_tokens: int,
        characters: int,
        tts_provider: str,
        model: str = "claude-sonnet-4-20250514"
    ) -> ProductionCost:
        """Calculate total production cost"""
        
        # LLM cost
        pricing = self.ANTHROPIC_PRICING.get(model, self.ANTHROPIC_PRICING["claude-sonnet-4-20250514"])
        llm_cost = (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])
        
        # TTS cost
        tts_pricing = self.TTS_PRICING.get(tts_provider, self.TTS_PRICING["openai"])
        tts_cost = characters * tts_pricing["per_char"]
        
        return ProductionCost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            llm_cost_usd=llm_cost,
            characters_used=characters,
            tts_provider=tts_provider,  # type: ignore
            tts_cost_usd=tts_cost,
            total_cost_usd=llm_cost + tts_cost
        )
