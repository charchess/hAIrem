import pytest
import yaml
import os
from unittest.mock import MagicMock, AsyncMock, patch
from src.infrastructure.plugin_loader import PluginLoader, AgentRegistry

# TDD: Epic 15 - Dynamic Skills
# These tests ensure skills can be loaded from persona.yaml configuration
# rather than being hardcoded in logic.py classes.


@pytest.fixture
def mock_deps():
    llm = AsyncMock()
    llm.model = "mock-model"
    llm.cache = None
    llm.get_completion = AsyncMock(return_value="ok")
    llm.get_embedding = AsyncMock(return_value=[0.1] * 768)

    surreal = AsyncMock()
    surreal.get_config = AsyncMock(return_value=None)

    redis = AsyncMock()
    redis.subscribe = AsyncMock(return_value=None)
    redis.publish_event = AsyncMock(return_value=None)

    return {"redis": redis, "llm": llm, "surreal": surreal}


@pytest.mark.asyncio
async def test_load_skills_from_persona_yaml(tmp_path, mock_deps):
    # Setup - Create a dummy agent with skills in yaml
    agent_dir = tmp_path / "skill_agent"
    agent_dir.mkdir()

    manifest = {"id": "skill_bot", "name": "SkillBot", "version": "1.0.0", "role": "tester"}

    persona = {
        "name": "SkillBot",
        "description": "A bot with skills",
        "skills": [
            {"name": "weather_lookup", "description": "Look up weather", "parameters": {"location": "string"}},
            {"name": "calculator", "description": "Calculate math", "parameters": {"expression": "string"}},
        ],
    }

    (agent_dir / "manifest.yaml").write_text(yaml.dump(manifest))
    (agent_dir / "persona.yaml").write_text(yaml.dump(persona))

    # Init Loader
    registry = AgentRegistry()
    loader = PluginLoader(str(tmp_path), registry, mock_deps["redis"], mock_deps["llm"], mock_deps["surreal"])

    await loader._initial_scan()

    agent = registry.agents.get("SkillBot")
    assert agent is not None

    # TDD Assertion: Skills should be registered as tools automatically
    # This will FAIL until implementation is done
    tools = agent.tools
    assert "weather_lookup" in tools
    assert "calculator" in tools
    assert tools["weather_lookup"]["description"] == "Look up weather"


@pytest.mark.asyncio
async def test_dynamic_skill_execution(tmp_path, mock_deps):
    # TDD: Verify the skill can actually be executed if it maps to a generic handler
    # or a python script file provided in the skill definition
    pass
