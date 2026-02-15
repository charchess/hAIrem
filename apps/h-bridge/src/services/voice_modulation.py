import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EmotionConfig:
    emotion: str
    pitch_modifier: float
    rate_modifier: float
    volume_modifier: float
    description: str


EMOTION_CONFIGS = {
    "happy": EmotionConfig(
        emotion="happy",
        pitch_modifier=1.15,
        rate_modifier=1.2,
        volume_modifier=1.1,
        description="Faster speech, higher pitch, increased volume"
    ),
    "excited": EmotionConfig(
        emotion="excited",
        pitch_modifier=1.2,
        rate_modifier=1.3,
        volume_modifier=1.15,
        description="Much faster, higher pitch, louder"
    ),
    "sad": EmotionConfig(
        emotion="sad",
        pitch_modifier=0.85,
        rate_modifier=0.75,
        volume_modifier=0.8,
        description="Slower speech, lower pitch, quieter"
    ),
    "angry": EmotionConfig(
        emotion="angry",
        pitch_modifier=0.95,
        rate_modifier=1.15,
        volume_modifier=1.2,
        description="Faster speech, lower pitch, louder"
    ),
    "fearful": EmotionConfig(
        emotion="fearful",
        pitch_modifier=1.1,
        rate_modifier=1.4,
        volume_modifier=0.9,
        description="Very fast, higher pitch, variable volume"
    ),
    "surprised": EmotionConfig(
        emotion="surprised",
        pitch_modifier=1.25,
        rate_modifier=1.1,
        volume_modifier=1.0,
        description="Higher pitch, slightly faster"
    ),
    "calm": EmotionConfig(
        emotion="calm",
        pitch_modifier=1.0,
        rate_modifier=0.85,
        volume_modifier=0.9,
        description="Slower, normal pitch, softer"
    ),
    "neutral": EmotionConfig(
        emotion="neutral",
        pitch_modifier=1.0,
        rate_modifier=1.0,
        volume_modifier=1.0,
        description="Normal speech"
    ),
    "urgent": EmotionConfig(
        emotion="urgent",
        pitch_modifier=1.05,
        rate_modifier=1.4,
        volume_modifier=1.15,
        description="Very fast, slightly higher pitch, louder"
    ),
    "gentle": EmotionConfig(
        emotion="gentle",
        pitch_modifier=1.05,
        rate_modifier=0.8,
        volume_modifier=0.85,
        description="Slower, slightly higher pitch, softer"
    ),
    "energetic": EmotionConfig(
        emotion="energetic",
        pitch_modifier=1.15,
        rate_modifier=1.25,
        volume_modifier=1.1,
        description="Faster, higher pitch, louder"
    ),
    "tired": EmotionConfig(
        emotion="tired",
        pitch_modifier=0.9,
        rate_modifier=0.7,
        volume_modifier=0.75,
        description="Much slower, lower pitch, quieter"
    ),
    "questioning": EmotionConfig(
        emotion="questioning",
        pitch_modifier=1.1,
        rate_modifier=0.95,
        volume_modifier=0.95,
        description="Slightly higher pitch, slightly slower"
    ),
    "enthusiastic": EmotionConfig(
        emotion="enthusiastic",
        pitch_modifier=1.18,
        rate_modifier=1.25,
        volume_modifier=1.1,
        description="Faster, higher pitch, louder"
    ),
    "thoughtful": EmotionConfig(
        emotion="thoughtful",
        pitch_modifier=0.95,
        rate_modifier=0.85,
        volume_modifier=0.95,
        description="Slower, lower pitch"
    )
}


class VoiceModulationService:
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self._agent_modulation_settings: Dict[str, Dict[str, Any]] = {}
        self._default_emotion = "neutral"

    async def initialize(self):
        logger.info("Voice modulation service initialized")

    def get_emotion_config(self, emotion: str) -> EmotionConfig:
        return EMOTION_CONFIGS.get(emotion.lower(), EMOTION_CONFIGS["neutral"])

    def detect_emotion_from_text(self, text: str) -> str:
        text_lower = text.lower()
        
        emotion_indicators = {
            "happy": ["happy", "joy", "great", "wonderful", "excellent", "love", "merveilleux", "super", "génial", "heureux"],
            "excited": ["excited", "amazing", "incredible", "wow", "can't wait", "supers", "incroyable", "ouf", "spam"],
            "sad": ["sad", "unfortunately", "sorry", "miss", "down", "triste", "manque", "désolé", "snif"],
            "angry": ["angry", "mad", "furious", "hate", "stupid", "fâché", "furieux", "déteste", "idiot"],
            "fearful": ["scared", "afraid", "worried", "nervous", "terrible", "peur", "inquiet", "terrible"],
            "surprised": ["wow", "surprise", "unbelievable", "imagine", "oh", "alors", "surprise", "incroyable"],
            "calm": ["calm", "relaxed", "peaceful", "quiet", "gentle", "calme", "paisible", "tranquille"],
            "urgent": ["urgent", "immediately", "hurry", "quick", "now", "urgent", "immédiat", "vite", "dépéchez"],
            "tired": ["tired", "exhausted", "sleepy", "fatigue", "épuisé", "fatigué", "sommeil"],
            "questioning": ["?", "why", "how", "what", "when", "where", "qui", "quoi", "pourquoi", "comment"]
        }
        
        scores = {}
        for emotion, keywords in emotion_indicators.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[emotion] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return self._default_emotion

    def modulate_voice(
        self,
        base_params: Dict[str, Any],
        emotion: Optional[str] = None,
        intensity: float = 1.0
    ) -> Dict[str, Any]:
        if emotion is None:
            emotion = self._default_emotion
        
        config = self.get_emotion_config(emotion)
        
        result = base_params.copy()
        
        pitch = base_params.get("pitch", 1.0)
        rate = base_params.get("rate", 1.0)
        volume = base_params.get("volume", 1.0)
        
        result["pitch"] = pitch * (1.0 + (config.pitch_modifier - 1.0) * intensity)
        result["rate"] = rate * (1.0 + (config.rate_modifier - 1.0) * intensity)
        result["volume"] = min(1.5, volume * (1.0 + (config.volume_modifier - 1.0) * intensity))
        
        result["emotion"] = emotion
        result["modulation_applied"] = True
        
        return result

    async def set_agent_modulation_settings(
        self,
        agent_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        self._agent_modulation_settings[agent_id] = settings
        return {"success": True, "agent_id": agent_id, "settings": settings}

    async def get_agent_modulation_settings(self, agent_id: str) -> Dict[str, Any]:
        return self._agent_modulation_settings.get(agent_id, {
            "default_emotion": self._default_emotion,
            "intensity": 1.0
        })

    def get_available_emotions(self) -> list:
        return list(EMOTION_CONFIGS.keys())


voice_modulation_service = VoiceModulationService()


async def modulate_voice(
    base_params: Dict[str, Any],
    emotion: Optional[str] = None,
    intensity: float = 1.0
) -> Dict[str, Any]:
    return voice_modulation_service.modulate_voice(base_params, emotion, intensity)


async def detect_emotion(text: str) -> str:
    return voice_modulation_service.detect_emotion_from_text(text)


def get_emotion_config(emotion: str) -> EmotionConfig:
    return voice_modulation_service.get_emotion_config(emotion)
