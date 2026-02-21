import pytest
from unittest.mock import MagicMock

# TDD: Epic 5 - Voice Modulation
# Tests for emotional impact on TTS generation.
# Requirement: FR40 (Voice Modulation)


class TestVoiceModulation:
    def test_emotion_to_ssml_mapping(self):
        # FR40: Voice Modulation
        # Emotional state should map to SSML tags or specific voice presets.

        from src.services.voice.modulator import VoiceModulator

        modulator = VoiceModulator()

        # Case: Joy
        ssml_joy = modulator.apply_emotion("Hello world", "joy")
        assert '<prosody rate="fast" pitch="high">' in ssml_joy

        # Case: Sadness
        ssml_sad = modulator.apply_emotion("Goodbye world", "sadness")
        assert '<prosody rate="slow" pitch="low">' in ssml_sad

    def test_voice_switching_based_on_role(self):
        # FR41: Prosody/Intonation (Role based)
        from src.services.voice.modulator import VoiceModulator

        modulator = VoiceModulator()

        voice_id_lisa = modulator.get_voice_for_role("companion")
        voice_id_butler = modulator.get_voice_for_role("butler")

        assert voice_id_lisa != voice_id_butler
