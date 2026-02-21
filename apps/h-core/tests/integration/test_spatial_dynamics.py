import pytest
import datetime
import os
from unittest.mock import MagicMock, AsyncMock

# TDD: Epic 9 - Spatial Dynamics
# Tests for World Themes and Location State tracking.
# Requirements: FR50 (Exterior Space), FR51 (World Themes)


class TestSpatialDynamics:
    @pytest.mark.asyncio
    async def test_world_theme_cascade(self):
        # FR51: World Themes
        # When a global theme is set (e.g. "Cyberpunk"), it should cascade to all agents
        # modifying their prompt context or visual generation parameters.

        # Mock dependencies
        redis = MagicMock()
        surreal = MagicMock()
        surreal.get_agent_state = AsyncMock(return_value=[])

        # Hypothetical SpatialManager
        from src.services.spatial.manager import SpatialManager

        manager = SpatialManager(redis, surreal)

        # Action: Set Theme
        await manager.set_global_theme("Cyberpunk 2077")

        # Assert: Theme is stored
        assert manager.current_theme == "Cyberpunk 2077"

        # Assert: Broadcast event sent via system_stream (UI) and agent:broadcast (Internal)
        assert redis.publish_event.called or redis.publish.called

    @pytest.mark.asyncio
    async def test_location_cohabitation(self):
        # FR48: Location Tracking
        # If two agents are in the same location, they should be aware of each other.

        redis = MagicMock()
        surreal = MagicMock()

        # Mock DB state: Lisa and Electra are in "Living Room"
        surreal.get_location_occupants = AsyncMock(return_value=["Lisa", "Electra"])

        from src.services.spatial.manager import SpatialManager

        manager = SpatialManager(redis, surreal)

        # Action: Check cohabitation
        occupants = await manager.get_location_occupants("Living Room")

        # Assert
        assert "Lisa" in occupants
        assert "Electra" in occupants
        assert len(occupants) == 2

    @pytest.mark.asyncio
    async def test_exterior_weather_impact(self):
        # FR50: Exterior Space
        # Weather changes should impact agent context.

        redis = MagicMock()
        surreal = MagicMock()

        from src.services.spatial.weather import WeatherService

        weather = WeatherService(redis)

        # Action: Update weather
        await weather.set_weather("Stormy")

        # Assert: Context string generation
        context = weather.get_context_string()
        assert "Stormy" in context


@pytest.mark.asyncio
async def test_world_theme_affects_bible_prompts():
    """Verify that setting a global theme changes the Visual Bible output."""
    from src.services.spatial.manager import SpatialManager
    from src.services.visual.bible import build_prompt, bible

    # 1. Setup paths
    os.environ["VISUAL_CONFIG_DIR"] = "/home/charchess/hairem/config/visual"
    bible.load_all()

    # 2. Mock deps
    redis = MagicMock()
    surreal = MagicMock()
    manager = SpatialManager(redis, surreal)

    # 3. Action: Set Theme
    await manager.set_global_theme("Cyberpunk")

    # 4. Verify prompt contains cyberpunk elements
    # Using 'system' to check background style
    prompt = build_prompt("system", "A quiet street")
    assert "cyberpunk" in prompt.lower()
    assert "neon" in prompt.lower()

    # 5. Reset to Default
    await manager.set_global_theme("Default")
    prompt_default = build_prompt("system", "A quiet street")
    assert "cyberpunk" not in prompt_default.lower()


@pytest.mark.asyncio
async def test_agent_reacts_to_theme_change_data_driven():
    """Verify that an agent cascades visual changes using config from persona."""
    from src.domain.agent import BaseAgent
    from src.models.agent import AgentConfig
    from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

    # 1. Setup Agent with theme_responses
    config = AgentConfig(
        name="Lisa",
        role="Companion",
        theme_responses={"Cyberpunk": {"outfit": "Neon Suit", "internal_thought": "Cyber logic"}},
    )
    redis = AsyncMock()
    llm = AsyncMock()
    surreal = AsyncMock()
    agent = BaseAgent(config, redis, llm, surreal_client=surreal)

    # 2. Trigger message (simulated broadcast)
    msg = HLinkMessage(
        type=MessageType.SYSTEM_STATUS_UPDATE,
        sender=Sender(agent_id="spatial", role="system"),
        recipient=Recipient(target="broadcast"),
        payload=Payload(content={"event": "world_theme_change", "theme": "Cyberpunk"}),
    )

    # 3. Process
    await agent.on_message(msg)

    # 4. Assert: Agent should have called change_outfit logic with "Neon Suit"
    assert surreal.update_agent_state.called
    args = surreal.update_agent_state.call_args[0]
    assert args[2]["description"] == "Neon Suit"

    # 5. Check internal note added to history
    assert any(
        "Cyber logic" in m.payload.content for m in agent.ctx.history if m.type == MessageType.AGENT_INTERNAL_NOTE
    )
