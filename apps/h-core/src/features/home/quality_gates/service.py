import logging
from typing import Optional

from features.home.user_relationships.models import (
    ToneType,
    ToneModifier,
    UserRelationship,
)

from .models import (
    QualityGate,
    QualityResult,
    RequestPriority,
    RequestType,
    get_quality_gate,
    is_critical_request,
    classify_request,
    MIN_QUALITY_SCORE,
    MAX_TONE_DELTA,
    ACCEPTABLE_TONE_TYPES,
)

logger = logging.getLogger(__name__)


class QualityGatesService:
    def __init__(self):
        self.min_quality_score = MIN_QUALITY_SCORE
        self.max_tone_delta = MAX_TONE_DELTA

    def classify_user_request(self, user_message: str) -> RequestType:
        return classify_request(user_message)

    def get_quality_gate_for_request(self, request_type: RequestType) -> QualityGate:
        return get_quality_gate(request_type)

    def evaluate_quality(
        self,
        request_type: RequestType,
        tone_modifier: Optional[ToneModifier] = None,
    ) -> QualityResult:
        quality_gate = get_quality_gate(request_type)
        
        quality_score = 1.0
        
        tone_modification_applied = False
        if tone_modifier and quality_gate.allow_tone_modification:
            tone_modification_applied = True
            
            if tone_modifier.tone == ToneType.HOSTILE:
                quality_score = max(quality_score - 0.3, 0.5)
            elif tone_modifier.tone == ToneType.COLD:
                quality_score = max(quality_score - 0.15, 0.7)
        
        if quality_gate.is_critical():
            quality_score = 1.0
            tone_modification_applied = False
        
        passed = quality_score >= quality_gate.min_quality_score
        
        if quality_gate.is_critical():
            message = "Critical request: quality enforced at maximum"
        elif passed:
            message = f"Quality gate passed (score: {quality_score:.2f})"
        else:
            message = f"Quality gate failed (score: {quality_score:.2f} < {quality_gate.min_quality_score:.2f})"
        
        return QualityResult(
            passed=passed,
            quality_score=quality_score,
            quality_gate=quality_gate,
            tone_modification_applied=tone_modification_applied,
            message=message,
        )

    def clamp_tone_modifier(
        self,
        tone_modifier: ToneModifier,
        relationship: Optional[UserRelationship] = None,
    ) -> ToneModifier:
        if tone_modifier.tone == ToneType.HOSTILE:
            clamped_tone = ToneType.COLD
            return ToneModifier(
                tone=clamped_tone,
                warmth_bonus=max(tone_modifier.warmth_bonus, -0.3),
                formality_bonus=tone_modifier.formality_bonus,
                empathy_bonus=max(tone_modifier.empathy_bonus, 0.0),
            )
        
        if tone_modifier.warmth_bonus < -self.max_tone_delta:
            return ToneModifier(
                tone=tone_modifier.tone,
                warmth_bonus=-self.max_tone_delta,
                formality_bonus=tone_modifier.formality_bonus,
                empathy_bonus=max(tone_modifier.empathy_bonus, 0.0),
            )
        
        if tone_modifier.empathy_bonus < -self.max_tone_delta:
            return ToneModifier(
                tone=tone_modifier.tone,
                warmth_bonus=tone_modifier.warmth_bonus,
                formality_bonus=tone_modifier.formality_bonus,
                empathy_bonus=-self.max_tone_delta,
            )
        
        return tone_modifier

    def apply_quality_gates(
        self,
        user_message: str,
        tone_modifier: Optional[ToneModifier] = None,
        relationship: Optional[UserRelationship] = None,
    ) -> tuple[ToneModifier, QualityResult]:
        request_type = self.classify_user_request(user_message)
        quality_gate = get_quality_gate(request_type)
        
        if quality_gate.is_critical():
            quality_result = self.evaluate_quality(request_type, None)
            neutral_tone = ToneModifier(
                tone=ToneType.NEUTRAL,
                warmth_bonus=0.0,
                formality_bonus=0.0,
                empathy_bonus=0.0,
            )
            return neutral_tone, quality_result
        
        final_tone_modifier = tone_modifier
        if tone_modifier and relationship:
            clamped_modifier = self.clamp_tone_modifier(tone_modifier, relationship)
            final_tone_modifier = clamped_modifier
        
        quality_result = self.evaluate_quality(request_type, final_tone_modifier)
        
        return final_tone_modifier, quality_result

    def ensure_quality_for_critical(
        self,
        response: str,
        request_type: RequestType,
    ) -> tuple[str, QualityResult]:
        if not is_critical_request(request_type):
            return response, QualityResult(
                passed=True,
                quality_score=1.0,
                quality_gate=get_quality_gate(request_type),
                tone_modification_applied=False,
                message="Non-critical request",
            )
        
        quality_gate = get_quality_gate(request_type)
        
        response = response.strip()
        if len(response) < 10:
            response = "I need more information to help you properly. Could you please provide more details?"
        
        return response, QualityResult(
            passed=True,
            quality_score=1.0,
            quality_gate=quality_gate,
            tone_modification_applied=False,
            message="Critical request: full quality ensured",
        )

    def validate_response_quality(
        self,
        response: str,
        request_type: RequestType,
        minimum_length: int = 10,
    ) -> bool:
        quality_gate = get_quality_gate(request_type)
        
        if quality_gate.require_full_response:
            if len(response.strip()) < minimum_length:
                logger.warning(
                    f"Response too short for {request_type.value}: "
                    f"{len(response)} < {minimum_length}"
                )
                return False
        
        return True

    def get_effective_quality_score(
        self,
        request_type: RequestType,
        tone_modifier: Optional[ToneModifier] = None,
    ) -> float:
        quality_result = self.evaluate_quality(request_type, tone_modifier)
        return quality_result.quality_score

    def should_modify_tone(
        self,
        request_type: RequestType,
        relationship: Optional[UserRelationship] = None,
    ) -> bool:
        quality_gate = get_quality_gate(request_type)
        
        if not quality_gate.allow_tone_modification:
            return False
        
        if quality_gate.is_critical():
            return False
        
        return True
