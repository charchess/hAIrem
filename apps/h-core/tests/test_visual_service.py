import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.visual.service import VisualImaginationService


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.generate = AsyncMock(return_value="http://example.com/image.png")
    return provider


@pytest.fixture
def mock_manager():
    manager = MagicMock()
    manager.save_asset = AsyncMock(return_value=("file:///media/generated/image.png", "asset_123"))
    manager.get_asset_by_prompt = AsyncMock(return_value=None)
    return manager


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.get_embedding = AsyncMock(return_value=[0.1] * 1536)
    return llm


@pytest.fixture
def mock_redis():
    redis = MagicMock()
    redis.publish = AsyncMock()
    return redis


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    """Setup environment variables for tests."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    monkeypatch.setenv("AGENTS_DIR", os.path.join(root, "agents"))
    monkeypatch.setenv("VISUAL_CONFIG_DIR", os.path.join(root, "config/visual"))


@pytest.fixture
def visual_service(mock_provider, mock_manager, mock_llm, mock_redis):
    return VisualImaginationService(
        mock_provider, mock_manager, mock_llm, mock_redis, agents_base_path="tests/mock_agents"
    )


def test_get_agent_reference_image_missing(visual_service):
    with patch("src.services.visual.service.bible") as mock_bible:
        mock_bible.get_reference_images.return_value = []
        ref = visual_service.get_agent_reference_image("lisa")
        assert ref is None


def test_get_agent_reference_image_exists(visual_service):
    with patch("src.services.visual.service.bible") as mock_bible:
        mock_bible.get_reference_images.return_value = ["tests/mock_agents/lisa/media/character_sheet_neutral.png"]

        # Create mock file
        os.makedirs("tests/mock_agents/lisa/media", exist_ok=True)
        with open("tests/mock_agents/lisa/media/character_sheet_neutral.png", "wb") as f:
            f.write(b"fake image content")

        ref = visual_service.get_agent_reference_image("lisa")
        assert ref is not None
        assert ref.startswith("data:image/png;base64,")

        # Clean up
        os.remove("tests/mock_agents/lisa/media/character_sheet_neutral.png")


@pytest.mark.asyncio
async def test_generate_for_agent_with_reference(visual_service, mock_provider):
    """Test that generate_for_agent passes reference_image to provider when available."""
    # Mock get_agent_reference_image to return a reference
    with patch.object(visual_service, "get_agent_reference_image", return_value="data:image/png;base64,fakebase64"):
        await visual_service.generate_for_agent("lisa", "A portrait of Lisa")

    # Check if provider was called with reference_image
    mock_provider.generate.assert_called_once()
    kwargs = mock_provider.generate.call_args[1]
    assert "reference_image" in kwargs
    assert kwargs["reference_image"] == "data:image/png;base64,fakebase64"


@pytest.mark.asyncio
async def test_index_generated_asset(visual_service, mock_manager, mock_llm):
    ref_path = "tests/mock_agents/lisa/media/character_sheet_neutral.png"

    await visual_service.index_generated_asset(
        "/tmp/test.png", "lisa", "A portrait of Lisa", reference_image_used=ref_path
    )

    mock_manager.save_asset.assert_called_once()
    metadata = mock_manager.save_asset.call_args[0][1]
    assert metadata["reference_image_used"] == ref_path
    assert metadata["agent_id"] == "lisa"
    assert metadata["embedding"] == [0.1] * 1536


@pytest.mark.asyncio
async def test_generate_and_index_with_reference_persistence(visual_service, mock_provider, mock_manager, mock_llm):
    ref_path = "tests/mock_agents/lisa/media/character_sheet_neutral.png"

    with patch("src.services.visual.service.bible") as mock_bible:
        mock_bible.get_reference_images.return_value = [ref_path]

        # Mock provider returning a file path (like Google provider)
        mock_provider.generate.return_value = "file:///tmp/generated.png"

        # Mock file existence for the generated file
        with patch("os.path.exists", return_value=True):
            await visual_service.generate_and_index("lisa", "A portrait of Lisa")

    # Verify that save_asset was called with the reference path from bible
    mock_manager.save_asset.assert_called_once()
    metadata = mock_manager.save_asset.call_args[0][1]
    assert metadata["reference_image_used"] == ref_path


@pytest.mark.asyncio
async def test_visual_service_injects_state_from_db(visual_service, mock_manager, mock_provider):
    """Verify that current outfit/location are fetched from DB and injected into prompts."""
    # 1. Setup mock DB state on the manager's db
    mock_manager.db = AsyncMock()
    mock_manager.db.get_agent_state.return_value = [
        {"relation": "WEARS", "description": "a bikini"},
        {"relation": "IS_IN", "description": "the beach"},
    ]
    mock_manager.get_asset_by_prompt.return_value = []
    mock_provider.generate.return_value = "file:///tmp/img.png"

    # 2. Mock build_prompt to see what it receives
    with patch("src.services.visual.service.build_prompt") as mock_build:
        mock_build.return_value = "Final Prompt"

        with patch("os.path.exists", return_value=True):
            await visual_service.generate_and_index("Lisa", "Smiling")

        # 3. Assert build_prompt was called with outfit and location
        # It's called inside generate_for_agent which is called by generate_and_index
        assert mock_build.called
        args, kwargs = mock_build.call_args
        assert kwargs["outfit"] == "a bikini"
        assert kwargs["location"] == "the beach"
        assert kwargs["description"] == "Smiling"
        assert kwargs["agent_id"] == "Lisa"
