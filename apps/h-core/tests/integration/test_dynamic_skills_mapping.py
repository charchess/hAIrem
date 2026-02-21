import pytest
from src.domain.agent import BaseAgent
from src.models.agent import AgentConfig
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_dynamic_skill_registration():
    # Setup mock dependencies
    redis = MagicMock()
    llm = MagicMock()

    # Define a custom config with specific skills
    config = AgentConfig(
        name="TestAgent",
        role="Tester",
        skills=[
            {"name": "recall_memory", "description": "Custom memory description"},
            {"name": "unimplemented_skill", "description": "This should be a placeholder"},
        ],
    )

    # Create agent
    agent = BaseAgent(config=config, redis_client=redis, llm_client=llm)

    # Verify tools registration
    assert "recall_memory" in agent.tools
    assert agent.tools["recall_memory"]["description"] == "Custom memory description"
    # recall_memory should map to the native method
    assert agent.tools["recall_memory"]["function"] == agent.recall_memory

    assert "unimplemented_skill" in agent.tools
    assert agent.tools["unimplemented_skill"]["description"] == "This should be a placeholder"
    # unimplemented_skill should be a placeholder (we check the name assigned)
    assert agent.tools["unimplemented_skill"]["function"].__name__ == "unimplemented_skill"

    # Verify tool schema for LLM
    schema = agent.get_tools_schema()
    assert len(schema) == 2
    tool_names = [t["function"]["name"] for t in schema]
    assert "recall_memory" in tool_names
    assert "unimplemented_skill" in tool_names
