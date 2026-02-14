import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from features.home.quality_gates import (
    QualityGatesService,
    RequestType,
    RequestPriority,
    QualityGate,
    QualityResult,
    get_quality_gate,
    is_critical_request,
    classify_request,
    CRITICAL_REQUEST_TYPES,
    QUALITY_GATES,
)
from features.home.user_relationships.models import (
    ToneModifier,
    ToneType,
    UserRelationship,
    RelationshipStatus,
)


class TestCriticalRequestTypes:
    def test_safety_is_critical(self):
        assert is_critical_request(RequestType.SAFETY) is True

    def test_medical_is_critical(self):
        assert is_critical_request(RequestType.MEDICAL) is True

    def test_emergency_is_critical(self):
        assert is_critical_request(RequestType.EMERGENCY) is True

    def test_information_is_critical(self):
        assert is_critical_request(RequestType.INFORMATION) is True

    def test_technical_support_not_critical(self):
        assert is_critical_request(RequestType.TECHNICAL_SUPPORT) is False

    def test_casual_not_critical(self):
        assert is_critical_request(RequestType.CASUAL) is False


class TestQualityGateDefinitions:
    def test_safety_gate_is_critical(self):
        gate = get_quality_gate(RequestType.SAFETY)
        assert gate.is_critical() is True
        assert gate.allow_tone_modification is False
        assert gate.min_quality_score == 1.0

    def test_medical_gate_is_critical(self):
        gate = get_quality_gate(RequestType.MEDICAL)
        assert gate.is_critical() is True
        assert gate.allow_tone_modification is False

    def test_information_gate_is_critical(self):
        gate = get_quality_gate(RequestType.INFORMATION)
        assert gate.is_critical() is True
        assert gate.allow_tone_modification is False

    def test_technical_support_allows_tone(self):
        gate = get_quality_gate(RequestType.TECHNICAL_SUPPORT)
        assert gate.is_critical() is False
        assert gate.allow_tone_modification is True

    def test_casual_allows_tone(self):
        gate = get_quality_gate(RequestType.CASUAL)
        assert gate.is_critical() is False
        assert gate.allow_tone_modification is True


class TestRequestClassification:
    def test_classify_safety_request(self):
        assert classify_request("I'm not safe") == RequestType.SAFETY
        assert classify_request("help me") == RequestType.SAFETY

    def test_classify_medical_request(self):
        assert classify_request("I have chest pain") == RequestType.MEDICAL
        assert classify_request("I'm bleeding") == RequestType.MEDICAL

    def test_classify_emergency_request(self):
        assert classify_request("emergency!") == RequestType.EMERGENCY
        assert classify_request("there's a fire") == RequestType.EMERGENCY

    def test_classify_information_request(self):
        assert classify_request("what is Python?") == RequestType.INFORMATION
        assert classify_request("how do I fix this?") == RequestType.INFORMATION

    def test_classify_technical_support(self):
        assert classify_request("there's a bug") == RequestType.TECHNICAL_SUPPORT
        assert classify_request("not working") == RequestType.TECHNICAL_SUPPORT

    def test_classify_casual(self):
        assert classify_request("hello there") == RequestType.SOCIAL
        assert classify_request("hi") == RequestType.SOCIAL


class TestQualityGatesService:
    def test_evaluate_quality_critical_no_tone_modification(self):
        service = QualityGatesService()
        result = service.evaluate_quality(RequestType.SAFETY, None)
        
        assert result.passed is True
        assert result.quality_score == 1.0
        assert result.tone_modification_applied is False

    def test_evaluate_quality_hostile_tone_reduces_score(self):
        service = QualityGatesService()
        hostile_tone = ToneModifier(
            tone=ToneType.HOSTILE,
            warmth_bonus=-0.5,
            formality_bonus=0.3,
            empathy_bonus=-0.3,
        )
        result = service.evaluate_quality(RequestType.CASUAL, hostile_tone)
        
        assert result.quality_score < 1.0
        assert result.tone_modification_applied is True

    def test_evaluate_quality_cold_tone_slight_reduction(self):
        service = QualityGatesService()
        cold_tone = ToneModifier(
            tone=ToneType.COLD,
            warmth_bonus=-0.3,
            formality_bonus=0.2,
            empathy_bonus=0.0,
        )
        result = service.evaluate_quality(RequestType.CASUAL, cold_tone)
        
        assert result.quality_score < 1.0
        assert result.quality_score >= 0.85

    def test_critical_request_ignores_tone(self):
        service = QualityGatesService()
        hostile_tone = ToneModifier(
            tone=ToneType.HOSTILE,
            warmth_bonus=-0.5,
            formality_bonus=0.3,
            empathy_bonus=-0.3,
        )
        result = service.evaluate_quality(RequestType.SAFETY, hostile_tone)
        
        assert result.passed is True
        assert result.quality_score == 1.0
        assert result.tone_modification_applied is False


class TestToneClamping:
    def test_clamp_hostile_to_cold(self):
        service = QualityGatesService()
        hostile = ToneModifier(
            tone=ToneType.HOSTILE,
            warmth_bonus=-0.5,
            formality_bonus=0.3,
            empathy_bonus=-0.3,
        )
        
        clamped = service.clamp_tone_modifier(hostile, None)
        
        assert clamped.tone == ToneType.COLD
        assert clamped.warmth_bonus >= -0.3

    def test_clamp_extreme_warmth(self):
        service = QualityGatesService()
        extreme = ToneModifier(
            tone=ToneType.COLD,
            warmth_bonus=-0.8,
            formality_bonus=0.3,
            empathy_bonus=-0.5,
        )
        
        clamped = service.clamp_tone_modifier(extreme, None)
        
        assert clamped.warmth_bonus >= -service.max_tone_delta


class TestApplyQualityGates:
    def test_apply_gates_critical_uses_neutral_tone(self):
        service = QualityGatesService()
        
        tone_mod, result = service.apply_quality_gates(
            "I need help, it's an emergency!",
            ToneModifier(tone=ToneType.HOSTILE, warmth_bonus=-0.5),
        )
        
        assert tone_mod.tone == ToneType.NEUTRAL
        assert result.passed is True
        assert result.quality_score == 1.0

    def test_apply_gates_casual_allows_tone(self):
        service = QualityGatesService()
        
        tone_mod, result = service.apply_quality_gates(
            "hello there!",
            ToneModifier(tone=ToneType.FRIENDLY, warmth_bonus=0.5),
        )
        
        assert tone_mod.tone == ToneType.FRIENDLY
        assert result.passed is True


class TestShouldModifyTone:
    def test_should_not_modify_critical(self):
        service = QualityGatesService()
        
        assert service.should_modify_tone(RequestType.SAFETY) is False
        assert service.should_modify_tone(RequestType.MEDICAL) is False

    def test_should_modify_casual(self):
        service = QualityGatesService()
        
        assert service.should_modify_tone(RequestType.CASUAL) is True


class TestValidateResponseQuality:
    def test_critical_requires_length(self):
        service = QualityGatesService()
        
        assert service.validate_response_quality("hi", RequestType.SAFETY) is False
        assert service.validate_response_quality("I can help you with that", RequestType.SAFETY) is True

    def test_casual_allows_short(self):
        service = QualityGatesService()
        
        assert service.validate_response_quality("ok", RequestType.CASUAL) is True


class TestQualityConstantAcrossRelationships:
    def test_quality_same_for_all_relationships_safety(self):
        service = QualityGatesService()
        
        enemy_rel = UserRelationship(
            agent_id="lisa",
            user_id="user1",
            score=-80.0,
            status=RelationshipStatus.ENEMY,
        )
        ally_rel = UserRelationship(
            agent_id="lisa",
            user_id="user2",
            score=80.0,
            status=RelationshipStatus.ALLY,
        )
        
        enemy_tone = ToneModifier(
            tone=ToneType.HOSTILE,
            warmth_bonus=-0.5,
            formality_bonus=0.3,
            empathy_bonus=-0.3,
        )
        
        enemy_result = service.evaluate_quality(RequestType.SAFETY, enemy_tone)
        ally_result = service.evaluate_quality(RequestType.SAFETY, None)
        
        assert enemy_result.quality_score == ally_result.quality_score == 1.0

    def test_quality_bounded_for_non_critical(self):
        service = QualityGatesService()
        
        hostile_tone = ToneModifier(
            tone=ToneType.HOSTILE,
            warmth_bonus=-0.5,
            formality_bonus=0.3,
            empathy_bonus=-0.3,
        )
        
        result = service.evaluate_quality(RequestType.CASUAL, hostile_tone)
        
        assert result.quality_score >= 0.5
        assert result.passed is True
