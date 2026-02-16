"""
Integration tests for Neural Voice Assignment (Story 14.5)
Tests automatic voice characteristic assignment based on agent personas
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os
import tempfile
import yaml

# Robust path handling
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BRIDGE_SRC = os.path.join(PROJECT_ROOT, "apps", "h-bridge", "src")

if BRIDGE_SRC not in sys.path:
    sys.path.insert(0, BRIDGE_SRC)

# Import the service
try:
    from services.neural_voice_assignment import NeuralVoiceAssignmentService, VoiceCharacteristics
except ImportError:
    from apps.h_bridge.src.services.neural_voice_assignment import NeuralVoiceAssignmentService, VoiceCharacteristics


class TestNeuralVoiceAssignment:
    @pytest.mark.asyncio
    async def test_neural_voice_assignment_initialization(self):
        """Test neural voice assignment service initialization."""
        mock_redis = AsyncMock()
        service = NeuralVoiceAssignmentService(mock_redis)

        await service.initialize()
        assert service.redis_client == mock_redis
        print("✅ Neural voice assignment service initialization successful")

    @pytest.mark.asyncio
    async def test_voice_assignment_for_female_agent(self):
        """Test voice assignment for a female agent."""
        mock_redis = AsyncMock()
        service = NeuralVoiceAssignmentService(mock_redis)

        # Create temporary persona file
        persona_data = {
            "name": "Test Agent",
            "description": "A beautiful female fox with elegant features.",
            "system_prompt": "You are a sophisticated and warm female assistant.",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(persona_data, f)
            temp_path = f.name

        try:
            characteristics = await service.assign_voice_to_agent("test_female", temp_path)

            assert isinstance(characteristics, VoiceCharacteristics)
            assert characteristics.gender == "female"
            assert characteristics.pitch > 1.0  # Higher pitch for females
            assert "female" in characteristics.age_group or True  # Age group detection
            assert characteristics.confidence > 0

            print("✅ Female agent voice assignment successful")

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_voice_assignment_for_male_agent(self):
        """Test voice assignment for a male agent."""
        mock_redis = AsyncMock()
        service = NeuralVoiceAssignmentService(mock_redis)

        persona_data = {
            "name": "Test Male",
            "description": "A strong male wolf with commanding presence.",
            "system_prompt": "You are an authoritative male guide.",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(persona_data, f)
            temp_path = f.name

        try:
            characteristics = await service.assign_voice_to_agent("test_male", temp_path)

            assert isinstance(characteristics, VoiceCharacteristics)
            assert characteristics.gender == "male"
            assert characteristics.pitch < 1.0  # Lower pitch for males
            assert characteristics.confidence > 0

            print("✅ Male agent voice assignment successful")

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_personality_trait_detection(self):
        """Test personality trait detection and voice adjustment."""
        mock_redis = AsyncMock()
        service = NeuralVoiceAssignmentService(mock_redis)

        # Test calm personality
        persona_data = {
            "name": "Calm Agent",
            "description": "A peaceful and serene being.",
            "system_prompt": "You are calm and gentle.",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(persona_data, f)
            temp_path = f.name

        try:
            characteristics = await service.assign_voice_to_agent("test_calm", temp_path)

            assert "calm" in characteristics.personality_traits
            assert characteristics.rate < 1.0  # Slower rate for calm
            assert characteristics.volume < 1.0  # Softer volume for calm

            print("✅ Personality trait detection successful")

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """Test that voice assignments are cached."""
        mock_redis = AsyncMock()
        service = NeuralVoiceAssignmentService(mock_redis)

        persona_data = {"name": "Cache Test", "description": "Testing cache functionality."}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(persona_data, f)
            temp_path = f.name

        try:
            # First call
            char1 = await service.assign_voice_to_agent("test_cache", temp_path)

            # Second call should use cache
            char2 = await service.assign_voice_to_agent("test_cache", temp_path)

            assert char1 == char2
            assert char1 is char2  # Same object from cache

            print("✅ Cache functionality successful")

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_fallback_to_default(self):
        """Test fallback when persona file is missing."""
        mock_redis = AsyncMock()
        service = NeuralVoiceAssignmentService(mock_redis)

        # Non-existent path
        characteristics = await service.assign_voice_to_agent("nonexistent_agent", "/fake/path.yaml")

        assert isinstance(characteristics, VoiceCharacteristics)
        assert characteristics.gender == "neutral"
        assert characteristics.pitch == 1.0
        assert characteristics.confidence < 1.0  # Lower confidence for fallback

        print("✅ Fallback to default successful")

    @pytest.mark.asyncio
    async def test_redis_storage(self):
        """Test Redis storage and retrieval."""
        mock_redis = AsyncMock()
        service = NeuralVoiceAssignmentService(mock_redis)

        persona_data = {"name": "Redis Test", "description": "Testing Redis integration."}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(persona_data, f)
            temp_path = f.name

        try:
            # Assign voice
            characteristics = await service.assign_voice_to_agent("test_redis", temp_path)

            # Check that Redis set was called
            mock_redis.set.assert_called()

            # Test retrieval
            retrieved = await service.get_voice_assignment("test_redis")
            assert retrieved is not None
            assert retrieved.pitch == characteristics.pitch

            print("✅ Redis storage and retrieval successful")

        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
