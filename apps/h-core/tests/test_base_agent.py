import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.domain.agent import AgentContext, BaseAgent
from src.models.agent import AgentConfig
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender


def make_config(name="lisa", skills=None):
    return AgentConfig(
        name=name,
        role="assistant",
        skills=skills or [],
        llm_config={"model": "test/model"},
    )


def make_agent(skills=None, surreal=None):
    config = make_config(skills=skills)
    redis = MagicMock()
    redis.publish = AsyncMock()
    redis.publish_event = AsyncMock()
    redis.subscribe = AsyncMock()
    llm = MagicMock()
    llm.get_completion = AsyncMock(return_value=MagicMock(choices=[MagicMock(message=MagicMock(content="Hello"))]))
    llm.get_usage_from_response = MagicMock(return_value={"input_tokens": 5, "output_tokens": 10, "total_tokens": 15})
    llm.get_model_provider = MagicMock(return_value=("test", "model"))
    llm.cache = None
    agent = BaseAgent(config=config, redis_client=redis, llm_client=llm, surreal_client=surreal)
    return agent


def make_message(content="Hello", msg_type=MessageType.USER_MESSAGE, sender_role="user"):
    return HLinkMessage(
        type=msg_type,
        sender=Sender(agent_id="user", role=sender_role),
        recipient=Recipient(target="lisa"),
        payload=Payload(content=content),
    )


class TestAgentContext:
    def test_update_and_get_state(self):
        ctx = AgentContext("lisa")
        ctx.update_state("mood", "happy")
        assert ctx.get_state("mood") == "happy"

    def test_get_state_missing_key(self):
        ctx = AgentContext("lisa")
        assert ctx.get_state("nonexistent") is None

    def test_set_and_get_user_context(self):
        ctx = AgentContext("lisa")
        ctx.set_user_context("user_123", "Alice")
        uid, uname = ctx.get_user_context()
        assert uid == "user_123"
        assert uname == "Alice"


class TestBaseAgentSetup:
    def test_agent_initializes_with_empty_tools_no_skills(self):
        agent = make_agent()
        assert isinstance(agent.tools, dict)
        assert len(agent.tools) == 0

    def test_agent_registers_method_skill(self):
        def my_skill(self, **kwargs):
            return "result"

        config = make_config(skills=[{"name": "recall_memory", "description": "Test skill"}])
        redis = MagicMock()
        redis.publish = AsyncMock()
        redis.subscribe = AsyncMock()
        llm = MagicMock()
        llm.cache = None
        agent = BaseAgent(config=config, redis_client=redis, llm_client=llm)
        assert "recall_memory" in agent.tools

    def test_agent_registers_placeholder_for_unknown_skill(self):
        config = make_config(skills=[{"name": "unknown_skill_xyz", "description": "Unknown"}])
        redis = MagicMock()
        redis.subscribe = AsyncMock()
        llm = MagicMock()
        llm.cache = None
        agent = BaseAgent(config=config, redis_client=redis, llm_client=llm)
        assert "unknown_skill_xyz" in agent.tools

    def test_agent_skips_skill_with_missing_name(self):
        config = make_config(skills=[{"description": "No name skill"}])
        redis = MagicMock()
        redis.subscribe = AsyncMock()
        llm = MagicMock()
        llm.cache = None
        agent = BaseAgent(config=config, redis_client=redis, llm_client=llm)
        assert len(agent.tools) == 0


class TestBaseAgentTools:
    def test_get_tools_schema_returns_list(self):
        config = make_config(skills=[{"name": "recall_memory", "description": "Search"}])
        redis = MagicMock()
        redis.subscribe = AsyncMock()
        llm = MagicMock()
        llm.cache = None
        agent = BaseAgent(config=config, redis_client=redis, llm_client=llm)
        schema = agent.get_tools_schema()
        assert isinstance(schema, list)

    @pytest.mark.asyncio
    async def test_send_internal_note_publishes(self):
        agent = make_agent()
        result = await agent.send_internal_note("electra", "Hello electra!")
        agent.redis.publish.assert_called_once()
        assert "electra" in result

    @pytest.mark.asyncio
    async def test_send_internal_note_to_broadcast(self):
        agent = make_agent()
        await agent.send_internal_note("broadcast", "Hello all!")
        call_args = agent.redis.publish.call_args[0]
        assert call_args[0] == "broadcast"

    @pytest.mark.asyncio
    async def test_generate_image_no_visual_service(self):
        agent = make_agent()
        result = await agent.generate_image("a cat")
        assert "not available" in result.lower()

    @pytest.mark.asyncio
    async def test_generate_image_with_visual_service(self):
        agent = make_agent()
        agent.visual_service = MagicMock()
        agent.visual_service.generate_and_index = AsyncMock(return_value=("file:///img.png", MagicMock()))
        result = await agent.generate_image("a cat")
        assert "img.png" in result

    @pytest.mark.asyncio
    async def test_generate_image_handles_exception(self):
        agent = make_agent()
        agent.visual_service = MagicMock()
        agent.visual_service.generate_and_index = AsyncMock(side_effect=Exception("GPU error"))
        result = await agent.generate_image("a cat")
        assert "Failed" in result


class TestBaseAgentMessageHandling:
    @pytest.mark.asyncio
    async def test_on_message_inactive_agent_returns(self):
        agent = make_agent()
        agent.is_active = False
        msg = make_message("Hello")
        agent.generate_response = AsyncMock()
        await agent.on_message(msg)
        agent.generate_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_message_dict_validates_to_hlink(self):
        agent = make_agent()
        agent.generate_response = AsyncMock()
        raw = {
            "type": "user_message",
            "sender": {"agent_id": "user", "role": "user"},
            "recipient": {"target": "lisa"},
            "payload": {"content": "Hi"},
        }
        await agent.on_message(raw)
        agent.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_message_invalid_dict_returns_early(self):
        agent = make_agent()
        agent.generate_response = AsyncMock()
        await agent.on_message({"bad": "data"})
        agent.generate_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_message_internal_note_adds_to_history(self):
        agent = make_agent()
        msg = make_message(content="secret", msg_type=MessageType.AGENT_INTERNAL_NOTE)
        await agent.on_message(msg)
        assert msg in agent.ctx.history

    @pytest.mark.asyncio
    async def test_on_message_user_message_generates_response(self):
        agent = make_agent()
        agent.generate_response = AsyncMock()
        msg = make_message("Hello!", msg_type=MessageType.USER_MESSAGE)
        await agent.on_message(msg)
        agent.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_message_error_loop_protection(self):
        agent = make_agent()
        agent.generate_response = AsyncMock()
        msg = make_message("Erreur de communication avec mon cerveau: timeout")
        await agent.on_message(msg)
        agent.generate_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_message_world_theme_changed(self):
        agent = make_agent()
        agent.handle_theme_change = AsyncMock()
        msg = make_message(
            content={"theme": "night"},
            msg_type=MessageType.WORLD_THEME_CHANGED,
        )
        await agent.on_message(msg)
        agent.handle_theme_change.assert_called_once_with("night")

    @pytest.mark.asyncio
    async def test_on_message_expert_command_dispatched(self):
        agent = make_agent()
        agent._handle_command = AsyncMock()
        msg = make_message(content="cmd", msg_type=MessageType.EXPERT_COMMAND)
        await agent.on_message(msg)
        agent._handle_command.assert_called_once()


class TestBaseAgentMemory:
    @pytest.mark.asyncio
    async def test_recall_memory_no_surreal(self):
        agent = make_agent()
        agent.llm.get_embedding = AsyncMock(return_value=[0.1, 0.2])
        result = await agent.recall_memory("what did I eat yesterday")
        assert "unavailable" in result.lower()

    @pytest.mark.asyncio
    async def test_recall_memory_no_embedding(self):
        agent = make_agent()
        agent.surreal = MagicMock()
        agent.surreal.get_agent_state = AsyncMock(return_value=[])
        agent.llm.get_embedding = AsyncMock(return_value=[])
        result = await agent.recall_memory("test")
        assert "Failed" in result

    @pytest.mark.asyncio
    async def test_recall_memory_with_results(self):
        agent = make_agent()
        agent.surreal = MagicMock()
        agent.surreal.get_agent_state = AsyncMock(return_value=[])
        agent.surreal.semantic_search = AsyncMock(return_value=[{"content": "User likes pasta", "user_id": None}])
        agent.surreal.update_memory_strength = AsyncMock()
        agent.llm.get_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        result = await agent.recall_memory("pasta")
        assert "pasta" in result.lower()

    @pytest.mark.asyncio
    async def test_get_burning_memory_no_surreal(self):
        agent = make_agent()
        result = await agent._get_burning_memory_context()
        assert result == ""

    @pytest.mark.asyncio
    async def test_get_burning_memory_with_states(self):
        agent = make_agent()
        agent.surreal = MagicMock()
        agent.surreal.get_agent_state = AsyncMock(
            return_value=[{"relation": "sitting_at", "description": "dining table"}]
        )
        result = await agent._get_burning_memory_context()
        assert "dining table" in result

    @pytest.mark.asyncio
    async def test_get_burning_memory_empty_states(self):
        agent = make_agent()
        agent.surreal = MagicMock()
        agent.surreal.get_agent_state = AsyncMock(return_value=[])
        result = await agent._get_burning_memory_context()
        assert result == ""

    @pytest.mark.asyncio
    async def test_get_burning_memory_exception_returns_empty(self):
        agent = make_agent()
        agent.surreal = MagicMock()
        agent.surreal.get_agent_state = AsyncMock(side_effect=Exception("db error"))
        result = await agent._get_burning_memory_context()
        assert result == ""


class TestBaseAgentApplySkillGrants:
    @pytest.mark.asyncio
    async def test_apply_skill_grants_no_surreal(self):
        agent = make_agent()
        agent.surreal = None
        await agent._apply_skill_grants()

    @pytest.mark.asyncio
    async def test_apply_skill_grants_revokes_inactive_skill(self):
        agent = make_agent()
        agent.tools["play_music"] = {"description": "play", "function": AsyncMock(), "skill_package": "music"}
        agent.surreal = MagicMock()

        with patch("src.features.admin.skill_management.service.SkillGrantService") as MockGrant:
            instance = MagicMock()
            instance.is_active = AsyncMock(return_value=False)
            MockGrant.return_value = instance
            await agent._apply_skill_grants()
            assert "play_music" not in agent.tools

    @pytest.mark.asyncio
    async def test_apply_skill_grants_keeps_active_skill(self):
        agent = make_agent()
        agent.tools["play_music"] = {"description": "play", "function": AsyncMock(), "skill_package": "music"}
        agent.surreal = MagicMock()

        with patch("src.features.admin.skill_management.service.SkillGrantService") as MockGrant:
            instance = MagicMock()
            instance.is_active = AsyncMock(return_value=True)
            MockGrant.return_value = instance
            await agent._apply_skill_grants()
            assert "play_music" in agent.tools
