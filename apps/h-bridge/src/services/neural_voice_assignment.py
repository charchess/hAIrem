"""
Neural Voice Assignment Service for hAIrem
Uses neural analysis to automatically assign voice characteristics to agents based on their persona
"""

import logging
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass
import yaml
import os

logger = logging.getLogger(__name__)


@dataclass
class VoiceCharacteristics:
    pitch: float
    rate: float
    volume: float
    gender: str
    age_group: str
    personality_traits: list
    confidence: float


class NeuralVoiceAssignmentService:
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self._voice_cache: Dict[str, VoiceCharacteristics] = {}

    async def initialize(self):
        logger.info("Neural voice assignment service initialized")

    async def assign_voice_to_agent(self, agent_id: str, persona_path: Optional[str] = None) -> VoiceCharacteristics:
        """Use neural analysis to assign voice characteristics to an agent based on their persona."""

        if agent_id in self._voice_cache:
            return self._voice_cache[agent_id]

        # Load persona data
        persona_data = await self._load_persona_data(agent_id, persona_path)
        if not persona_data:
            # Fallback to default
            return self._get_default_voice()

        # Analyze persona text
        characteristics = self._analyze_persona_text(persona_data)

        # Cache the result
        self._voice_cache[agent_id] = characteristics

        # Store in Redis if available
        if self.redis_client:
            await self._store_voice_assignment(agent_id, characteristics)

        logger.info(
            f"Assigned voice to agent {agent_id}: pitch={characteristics.pitch}, gender={characteristics.gender}"
        )
        return characteristics

    async def _load_persona_data(self, agent_id: str, persona_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load persona data from YAML file."""
        try:
            if not persona_path:
                # Try default path
                persona_path = f"agents/{agent_id}/persona.yaml"

            if not os.path.exists(persona_path):
                logger.warning(f"Persona file not found: {persona_path}")
                return None

            with open(persona_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            return data

        except Exception as e:
            logger.error(f"Failed to load persona data for {agent_id}: {e}")
            return None

    def _analyze_persona_text(self, persona_data: Dict[str, Any]) -> VoiceCharacteristics:
        """Analyze persona text to determine voice characteristics."""
        text_to_analyze = ""

        # Combine relevant text fields
        if "description" in persona_data:
            text_to_analyze += persona_data["description"] + " "
        if "system_prompt" in persona_data:
            text_to_analyze += persona_data["system_prompt"] + " "
        if "name" in persona_data:
            text_to_analyze += persona_data["name"] + " "

        text_to_analyze = text_to_analyze.lower()

        # Initialize base characteristics
        pitch = 1.0
        rate = 1.0
        volume = 1.0
        gender = "neutral"
        age_group = "adult"
        personality_traits = []
        confidence = 0.8

        # Gender detection
        if re.search(r"\b(female|woman|girl|she|her|féminin|femme|renarde|fox|fille)\b", text_to_analyze):
            gender = "female"
            pitch *= 1.1  # Higher pitch for females
        elif re.search(r"\b(male|man|boy|he|him|masculin|homme|garçon)\b", text_to_analyze):
            gender = "male"
            pitch *= 0.9  # Lower pitch for males

        # Age group detection
        if re.search(r"\b(young|teen|adolescent|jeune|enfant|kid|child)\b", text_to_analyze):
            age_group = "young"
            pitch *= 1.05
            rate *= 1.1
        elif re.search(r"\b(old|elderly|senior|vieux|âgé|ancient)\b", text_to_analyze):
            age_group = "elderly"
            pitch *= 0.95
            rate *= 0.9

        # Personality trait analysis
        personality_keywords = {
            "calm": ["calm", "peaceful", "serene", "tranquil", "gentle", "soft"],
            "energetic": ["energetic", "excited", "lively", "dynamic", "vibrant"],
            "wise": ["wise", "intelligent", "knowledgeable", "profound", "sagacious"],
            "mysterious": ["mysterious", "enigmatic", "secretive", "mystical"],
            "friendly": ["friendly", "warm", "welcoming", "kind", "sociable"],
            "authoritative": ["authoritative", "commanding", "powerful", "dominant"],
            "playful": ["playful", "mischievous", "funny", "humorous", "teasing"],
            "formal": ["formal", "elegant", "sophisticated", "refined", "polished"],
            "casual": ["casual", "relaxed", "informal", "laid-back"],
        }

        for trait, keywords in personality_keywords.items():
            if any(kw in text_to_analyze for kw in keywords):
                personality_traits.append(trait)

                # Adjust voice parameters based on personality
                if trait == "calm":
                    rate *= 0.9
                    volume *= 0.9
                elif trait == "energetic":
                    rate *= 1.1
                    volume *= 1.05
                elif trait == "wise":
                    rate *= 0.95
                    pitch *= 0.98
                elif trait == "playful":
                    pitch *= 1.05
                    rate *= 1.05
                elif trait == "formal":
                    rate *= 0.95
                    volume *= 0.95
                elif trait == "authoritative":
                    pitch *= 0.95
                    volume *= 1.1

        # Species-specific adjustments (for anthropomorphic characters)
        if re.search(r"\b(fox|renard|renarde|vixen)\b", text_to_analyze):
            # Foxes are often portrayed as clever and playful
            pitch *= 1.02
            rate *= 1.03
            if "playful" not in personality_traits:
                personality_traits.append("playful")

        # Ensure reasonable bounds
        pitch = max(0.7, min(1.3, pitch))
        rate = max(0.7, min(1.3, rate))
        volume = max(0.7, min(1.2, volume))

        return VoiceCharacteristics(
            pitch=pitch,
            rate=rate,
            volume=volume,
            gender=gender,
            age_group=age_group,
            personality_traits=personality_traits,
            confidence=confidence,
        )

    def _get_default_voice(self) -> VoiceCharacteristics:
        """Get default voice characteristics."""
        return VoiceCharacteristics(
            pitch=1.0,
            rate=1.0,
            volume=1.0,
            gender="neutral",
            age_group="adult",
            personality_traits=["neutral"],
            confidence=0.5,
        )

    async def _store_voice_assignment(self, agent_id: str, characteristics: VoiceCharacteristics):
        """Store voice assignment in Redis."""
        if self.redis_client:
            try:
                import json

                key = f"neural_voice:{agent_id}"
                data = {
                    "pitch": characteristics.pitch,
                    "rate": characteristics.rate,
                    "volume": characteristics.volume,
                    "gender": characteristics.gender,
                    "age_group": characteristics.age_group,
                    "personality_traits": characteristics.personality_traits,
                    "confidence": characteristics.confidence,
                }
                await self.redis_client.set(key, json.dumps(data))
            except Exception as e:
                logger.warning(f"Failed to store voice assignment: {e}")

    async def get_voice_assignment(self, agent_id: str) -> Optional[VoiceCharacteristics]:
        """Retrieve stored voice assignment."""
        if agent_id in self._voice_cache:
            return self._voice_cache[agent_id]

        if self.redis_client:
            try:
                import json

                key = f"neural_voice:{agent_id}"
                data = await self.redis_client.get(key)
                if data:
                    parsed = json.loads(data)
                    characteristics = VoiceCharacteristics(**parsed)
                    self._voice_cache[agent_id] = characteristics
                    return characteristics
            except Exception as e:
                logger.warning(f"Failed to retrieve voice assignment: {e}")

        return None

    def clear_cache(self):
        """Clear the voice assignment cache."""
        self._voice_cache.clear()


# Global service instance
neural_voice_assignment_service = NeuralVoiceAssignmentService()


async def assign_voice_to_agent(agent_id: str, persona_path: Optional[str] = None) -> VoiceCharacteristics:
    """Convenience function to assign voice to an agent."""
    return await neural_voice_assignment_service.assign_voice_to_agent(agent_id, persona_path)


async def get_agent_voice(agent_id: str) -> Optional[VoiceCharacteristics]:
    """Convenience function to get agent's voice characteristics."""
    return await neural_voice_assignment_service.get_voice_assignment(agent_id)
