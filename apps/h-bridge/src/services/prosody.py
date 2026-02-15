import logging
import re
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IntonationType(Enum):
    STATEMENT = "statement"
    QUESTION = "question"
    EXCLAMATION = "exclamation"
    COMMAND = "command"
    LIST = "list"


@dataclass
class ProsodyConfig:
    intonation: IntonationType
    pitch_modifier: float
    rate_modifier: float
    emphasis: str = "balanced"


PUNCTUATION_INTONATION = {
    ".": IntonationType.STATEMENT,
    "?": IntonationType.QUESTION,
    "!": IntonationType.EXCLAMATION,
    ",": IntonationType.STATEMENT,
    ";": IntonationType.STATEMENT,
    ":": IntonationType.STATEMENT
}

INTONATION_CONFIGS = {
    IntonationType.STATEMENT: ProsodyConfig(
        intonation=IntonationType.STATEMENT,
        pitch_modifier=0.95,
        rate_modifier=1.0,
        emphasis="balanced"
    ),
    IntonationType.QUESTION: ProsodyConfig(
        intonation=IntonationType.QUESTION,
        pitch_modifier=1.15,
        rate_modifier=0.95,
        emphasis="rising"
    ),
    IntonationType.EXCLAMATION: ProsodyConfig(
        intonation=IntonationType.EXCLAMATION,
        pitch_modifier=1.25,
        rate_modifier=1.15,
        emphasis="strong"
    ),
    IntonationType.COMMAND: ProsodyConfig(
        intonation=IntonationType.COMMAND,
        pitch_modifier=1.0,
        rate_modifier=1.1,
        emphasis="strong"
    ),
    IntonationType.LIST: ProsodyConfig(
        intonation=IntonationType.LIST,
        pitch_modifier=1.05,
        rate_modifier=1.0,
        emphasis="moderate"
    )
}


QUESTION_STARTERS = [
    "qui", "quoi", "où", "quand", "comment", "pourquoi", "est-ce que",
    "who", "what", "where", "when", "how", "why", "is", "are", "do", "does",
    "can", "could", "would", "will", "should", "may", "might"
]


class ProsodyService:
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self._agent_prosody_settings: Dict[str, Dict[str, Any]] = {}
        self._default_style = "default"

    async def initialize(self):
        logger.info("Prosody service initialized")

    def detect_sentence_type(self, text: str) -> IntonationType:
        text = text.strip()
        
        if not text:
            return IntonationType.STATEMENT
        
        last_char = text[-1] if text else "."
        if last_char in PUNCTUATION_INTONATION:
            punctuation_type = PUNCTUATION_INTONATION[last_char]
            if punctuation_type == IntonationType.QUESTION:
                return IntonationType.QUESTION
            elif punctuation_type == IntonationType.EXCLAMATION:
                return IntonationType.EXCLAMATION
        
        text_lower = text.lower()
        
        if text_lower.startswith(tuple(QUESTION_STARTERS)):
            return IntonationType.QUESTION
        
        if text_lower.startswith(("s'il vous plaît", "please", "faire", "aller", "venir")):
            return IntonationType.COMMAND
        
        if re.search(r',\s*\w+.*,\s*\w+', text):
            return IntonationType.LIST
        
        if text.endswith("?") or " ?" in text:
            return IntonationType.QUESTION
        
        if text.endswith("!") or " !" in text:
            return IntonationType.EXCLAMATION
        
        return IntonationType.STATEMENT

    def get_prosody_config(self, intonation: IntonationType) -> ProsodyConfig:
        return INTONATION_CONFIGS.get(intonation, INTONATION_CONFIGS[IntonationType.STATEMENT])

    def split_into_sentences(self, text: str) -> List[Dict[str, Any]]:
        sentences = []
        sentence_pattern = r'[^.!?]+[.!?]+'
        matches = re.findall(sentence_pattern, text)
        
        for match in matches:
            match = match.strip()
            if match:
                sentence_type = self.detect_sentence_type(match)
                sentences.append({
                    "text": match,
                    "type": sentence_type.value,
                    "prosody": self.get_prosody_config(sentence_type)
                })
        
        if not sentences and text.strip():
            sentences.append({
                "text": text.strip(),
                "type": self.detect_sentence_type(text).value,
                "prosody": self.get_prosody_config(IntonationType.STATEMENT)
            })
        
        return sentences

    def apply_prosody(
        self,
        base_params: Dict[str, Any],
        text: Optional[str] = None,
        intonation: Optional[IntonationType] = None,
        style: str = "default"
    ) -> Dict[str, Any]:
        if intonation is None:
            if text:
                intonation = self.detect_sentence_type(text)
            else:
                intonation = IntonationType.STATEMENT
        
        config = self.get_prosody_config(intonation)
        
        result = base_params.copy()
        
        pitch = base_params.get("pitch", 1.0)
        rate = base_params.get("rate", 1.0)
        
        style_modifiers = self._get_style_modifiers(style)
        
        result["pitch"] = pitch * config.pitch_modifier * style_modifiers.get("pitch", 1.0)
        result["rate"] = rate * config.rate_modifier * style_modifiers.get("rate", 1.0)
        result["intonation"] = intonation.value
        result["emphasis"] = config.emphasis
        result["prosody_applied"] = True
        
        return result

    def _get_style_modifiers(self, style: str) -> Dict[str, float]:
        styles = {
            "default": {"pitch": 1.0, "rate": 1.0},
            "formal": {"pitch": 0.95, "rate": 0.9},
            "casual": {"pitch": 1.05, "rate": 1.1},
            "dramatic": {"pitch": 1.15, "rate": 1.05},
            "monotone": {"pitch": 1.0, "rate": 1.0},
            "expressive": {"pitch": 1.2, "rate": 1.1}
        }
        return styles.get(style, styles["default"])

    async def set_agent_prosody_settings(
        self,
        agent_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        self._agent_prosody_settings[agent_id] = settings
        return {"success": True, "agent_id": agent_id, "settings": settings}

    async def get_agent_prosody_settings(self, agent_id: str) -> Dict[str, Any]:
        return self._agent_prosody_settings.get(agent_id, {
            "style": self._default_style,
            "default_intonation": IntonationType.STATEMENT.value
        })

    def get_available_styles(self) -> list:
        return ["default", "formal", "casual", "dramatic", "monotone", "expressive"]

    def analyze_text_prosody(self, text: str) -> Dict[str, Any]:
        sentences = self.split_into_sentences(text)
        
        types = [s["type"] for s in sentences]
        
        return {
            "text": text,
            "sentence_count": len(sentences),
            "sentences": sentences,
            "dominant_type": max(set(types), key=types.count) if types else "statement",
            "has_questions": IntonationType.QUESTION.value in types,
            "has_exclamations": IntonationType.EXCLAMATION.value in types
        }


prosody_service = ProsodyService()


async def apply_prosody(
    base_params: Dict[str, Any],
    text: Optional[str] = None,
    intonation: Optional[str] = None,
    style: str = "default"
) -> Dict[str, Any]:
    intonation_type = IntonationType[intonation.upper()] if intonation else None
    return prosody_service.apply_prosody(base_params, text, intonation_type, style)


def detect_sentence_type(text: str) -> str:
    return prosody_service.detect_sentence_type(text).value


def analyze_text_prosody(text: str) -> Dict[str, Any]:
    return prosody_service.analyze_text_prosody(text)
