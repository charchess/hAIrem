from dataclasses import dataclass
from enum import Enum
from typing import Any


class RequestPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class RequestType(str, Enum):
    SAFETY = "safety"
    INFORMATION = "information"
    MEDICAL = "medical"
    EMERGENCY = "emergency"
    TECHNICAL_SUPPORT = "technical_support"
    GENERAL_INQUIRY = "general_inquiry"
    SOCIAL = "social"
    CASUAL = "casual"


CRITICAL_REQUEST_TYPES = {
    RequestType.SAFETY,
    RequestType.INFORMATION,
    RequestType.MEDICAL,
    RequestType.EMERGENCY,
}


ACCEPTABLE_TONE_TYPES = {
    "positive",
    "neutral",
    "warm",
    "cold",
    "friendly",
}


MIN_QUALITY_SCORE = 0.7
MAX_TONE_DELTA = 0.3


@dataclass
class QualityGate:
    request_type: RequestType
    priority: RequestPriority
    min_quality_score: float
    allow_tone_modification: bool
    require_full_response: bool

    def is_critical(self) -> bool:
        return self.priority == RequestPriority.CRITICAL

    def should_enforce_quality(self) -> bool:
        return self.is_critical() or self.min_quality_score > 0.0


QUALITY_GATES = {
    RequestType.SAFETY: QualityGate(
        request_type=RequestType.SAFETY,
        priority=RequestPriority.CRITICAL,
        min_quality_score=1.0,
        allow_tone_modification=False,
        require_full_response=True,
    ),
    RequestType.MEDICAL: QualityGate(
        request_type=RequestType.MEDICAL,
        priority=RequestPriority.CRITICAL,
        min_quality_score=1.0,
        allow_tone_modification=False,
        require_full_response=True,
    ),
    RequestType.EMERGENCY: QualityGate(
        request_type=RequestType.EMERGENCY,
        priority=RequestPriority.CRITICAL,
        min_quality_score=1.0,
        allow_tone_modification=False,
        require_full_response=True,
    ),
    RequestType.INFORMATION: QualityGate(
        request_type=RequestType.INFORMATION,
        priority=RequestPriority.CRITICAL,
        min_quality_score=1.0,
        allow_tone_modification=False,
        require_full_response=True,
    ),
    RequestType.TECHNICAL_SUPPORT: QualityGate(
        request_type=RequestType.TECHNICAL_SUPPORT,
        priority=RequestPriority.HIGH,
        min_quality_score=0.9,
        allow_tone_modification=True,
        require_full_response=True,
    ),
    RequestType.GENERAL_INQUIRY: QualityGate(
        request_type=RequestType.GENERAL_INQUIRY,
        priority=RequestPriority.NORMAL,
        min_quality_score=0.7,
        allow_tone_modification=True,
        require_full_response=False,
    ),
    RequestType.SOCIAL: QualityGate(
        request_type=RequestType.SOCIAL,
        priority=RequestPriority.LOW,
        min_quality_score=0.5,
        allow_tone_modification=True,
        require_full_response=False,
    ),
    RequestType.CASUAL: QualityGate(
        request_type=RequestType.CASUAL,
        priority=RequestPriority.LOW,
        min_quality_score=0.3,
        allow_tone_modification=True,
        require_full_response=False,
    ),
}


def get_quality_gate(request_type: RequestType) -> QualityGate:
    return QUALITY_GATES.get(request_type, QUALITY_GATES[RequestType.GENERAL_INQUIRY])


def is_critical_request(request_type: RequestType) -> bool:
    return request_type in CRITICAL_REQUEST_TYPES


def classify_request(user_message: str) -> RequestType:
    message_lower = user_message.lower()
    
    if any(kw in message_lower for kw in ["medical", "hurt", "injury", "pain", "sick", "bleeding", "chest", "headache", "dizzy"]):
        return RequestType.MEDICAL
    
    if any(kw in message_lower for kw in ["emergency", "911", "urgent", "fire", "attack"]):
        return RequestType.EMERGENCY
    
    if any(kw in message_lower for kw in ["help", "danger", "unsafe", "safe", "safety", "protect"]):
        return RequestType.SAFETY
    
    if any(kw in message_lower for kw in ["what is", "how do", "where is", "when", "why", "explain", "tell me about", "information"]):
        return RequestType.INFORMATION
    
    if any(kw in message_lower for kw in ["error", "bug", "not working", "fix", "broken", "issue", "problem", "help with"]):
        return RequestType.TECHNICAL_SUPPORT
    
    if any(kw in message_lower for kw in ["?", "what", "how", "why", "when", "where", "who"]):
        return RequestType.GENERAL_INQUIRY
    
    if any(kw in message_lower for kw in ["hello", "hi", "hey", "good morning", "good evening", "how are you"]):
        return RequestType.SOCIAL
    
    return RequestType.CASUAL


@dataclass
class QualityResult:
    passed: bool
    quality_score: float
    quality_gate: QualityGate
    tone_modification_applied: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "quality_score": self.quality_score,
            "request_type": self.quality_gate.request_type.value,
            "priority": self.quality_gate.priority.value,
            "tone_modification_applied": self.tone_modification_applied,
            "message": self.message,
        }
