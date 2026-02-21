import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.visual.vault import VaultService
from src.services.chat.commands import CommandHandler
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender


@pytest.fixture
def mock_db():
    db = MagicMock()
    db._call = AsyncMock()
    # Mock update_agent_state
    db.update_agent_state = AsyncMock()
    return db


@pytest.fixture
def mock_visual(mock_db):
    visual = MagicMock()
    visual.vault = VaultService(mock_db)
    visual.generate_and_index = AsyncMock(return_value="file:///tmp/new.png")
    visual.notify_visual_asset = AsyncMock()
    return visual


@pytest.fixture
def mock_redis():
    redis = MagicMock()
    redis.publish = AsyncMock()
    return redis


@pytest.mark.asyncio
async def test_vault_service_save_and_get(mock_db):
    service = VaultService(mock_db)

    # Mocking successful upsert (SurrealDB query result format)
    mock_db._call.return_value = [{"result": []}]

    success = await service.save_item(
        "lisa", "cool_dress", "visual_asset:abc", prompt="a cool dress", category="garment", asset_id="visual_asset:abc"
    )
    assert success == "visual_asset:abc"
    assert mock_db._call.called

    # Mocking successful get
    mock_db._call.return_value = [
        {"result": [{"name": "cool_dress", "category": "garment", "asset": {"url": "file:///tmp/cool.png"}}]}
    ]

    item = await service.get_item("lisa", "cool_dress")
    assert item is not None
    assert item["name"] == "cool_dress"
    assert item["asset"]["url"] == "file:///tmp/cool.png"


@pytest.mark.asyncio
async def test_command_handler_vault_hit_outfit(mock_redis, mock_visual, mock_db):
    handler = CommandHandler(mock_redis, mock_visual, mock_db)

    # Mock vault hit
    mock_db._call.return_value = [
        {"result": [{"name": "red_dress", "category": "garment", "asset": {"url": "file:///tmp/red.png"}}]}
    ]

    msg = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="broadcast"),
        payload=Payload(content="/outfit Lisa red_dress"),
    )

    await handler.execute("/outfit Lisa red_dress", msg)

    # Should NOT call generate_and_index
    assert not mock_visual.generate_and_index.called
    # Should call notify_visual_asset with the vaulted URL
    mock_visual.notify_visual_asset.assert_called_with("file:///tmp/red.png", "red_dress", "Lisa", "pose")


@pytest.mark.asyncio
async def test_command_handler_vault_miss_outfit(mock_redis, mock_visual, mock_db):
    handler = CommandHandler(mock_redis, mock_visual, mock_db)

    # Mock vault miss
    mock_db._call.return_value = [{"result": []}]

    msg = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="broadcast"),
        payload=Payload(content="/outfit Lisa unknown_outfit"),
    )

    await handler.execute("/outfit Lisa unknown_outfit", msg)

    # Should call generate_and_index because it was not in vault
    assert mock_visual.generate_and_index.called


@pytest.mark.asyncio
async def test_command_handler_vault_list(mock_redis, mock_visual, mock_db):
    handler = CommandHandler(mock_redis, mock_visual, mock_db)

    # Mock vault contents
    mock_db._call.return_value = [
        {"result": [{"name": "dress1", "category": "garment"}, {"name": "beach", "category": "background"}]}
    ]

    msg = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="broadcast"),
        payload=Payload(content="/vault Lisa"),
    )

    await handler.execute("/vault Lisa", msg)

    # Verify Redis broadcast contains the list
    assert mock_redis.publish.called
    call_args = mock_redis.publish.call_args_list[-1]
    text = call_args[0][1].payload.content
    assert "Vault de Lisa" in text
    assert "dress1" in text
    assert "beach" in text
