import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../apps/h-core/src"))

from src.features.home.social_arbiter.arbiter import SocialArbiter
from src.features.home.social_arbiter.models import AgentProfile
from src.features.home.social_arbiter.scoring import ScoringEngine


class TestScoringEngine:
    """FR18-FR19: Scoring Engine pour UTS"""

    @pytest.mark.asyncio
    async def test_calculate_uts_score_llm(self):
        """Should use LLM to calculate UTS score"""
        mock_llm = Mock()
        mock_llm.get_completion = AsyncMock(return_value='{"lisa": 0.9, "renarde": 0.2}')

        engine = ScoringEngine(llm_client=mock_llm)
        agents = [
            AgentProfile(agent_id="lisa", name="Lisa", role="assistant"),
            AgentProfile(agent_id="renarde", name="Renarde", role="coordinator"),
        ]

        scores = await engine.calculate_relevance_llm("hello", agents)
        assert scores["lisa"] == 0.9
        assert scores["renarde"] == 0.2

    def test_repetition_penalty(self):
        """Should penalize agents who just spoke"""
        engine = ScoringEngine()
        score = 1.0
        # Just spoke 5 seconds ago
        penalized = engine.apply_repetition_penalty(score, 5.0)
        assert penalized < 0.5
        # Spoke 10 minutes ago
        fresh = engine.apply_repetition_penalty(score, 600.0)
        assert fresh > 0.9


class TestSocialArbiterUTS:
    """Epic 18: UTS logic integration"""

    @pytest.mark.asyncio
    async def test_determine_responder_cascade(self):
        """Should return multiple agents if UTS > 0.75"""
        mock_llm = Mock()
        # Both Lisa and Renarde are very relevant
        mock_llm.get_completion = AsyncMock(return_value='{"lisa": 0.9, "renarde": 0.8}')

        arbiter = SocialArbiter(llm_client=mock_llm)
        lisa = AgentProfile(agent_id="lisa", name="Lisa", role="assistant", is_active=True)
        renarde = AgentProfile(agent_id="renarde", name="Renarde", role="coordinator", is_active=True)

        arbiter.register_agent(lisa)
        arbiter.register_agent(renarde)

        # Mock time_since_last_spoke to be large
        with patch.object(arbiter.suppressor, "get_time_since_last_spoke", return_value=1000.0):
            responders = await arbiter.determine_responder_async("urgent message")
            assert len(responders) == 2
            assert any(a.agent_id == "lisa" for a in responders)
            assert any(a.agent_id == "renarde" for a in responders)

    @pytest.mark.asyncio
    async def test_collective_greeting_random_spokesperson(self):
        """Should pick only one agent for collective greeting"""
        arbiter = SocialArbiter()
        arbiter.register_agent(AgentProfile(agent_id="lisa", name="Lisa", role="assistant", is_active=True))
        arbiter.register_agent(AgentProfile(agent_id="renarde", name="Renarde", role="coordinator", is_active=True))

        responders = await arbiter.determine_responder_async("bonjour les filles")
        assert len(responders) == 1
        assert responders[0].agent_id in ["lisa", "renarde"]

    @pytest.mark.asyncio
    async def test_named_mention_priority(self):
        """Should prioritize named agent with UTS 1.0"""
        arbiter = SocialArbiter()
        lisa = AgentProfile(agent_id="lisa", name="Lisa", role="assistant", is_active=True)
        arbiter.register_agent(lisa)
        arbiter.register_agent(AgentProfile(agent_id="renarde", name="Renarde", role="coordinator", is_active=True))

        responders = await arbiter.determine_responder_async("Lisa, une question")
        assert len(responders) == 1
        assert responders[0].agent_id == "lisa"
