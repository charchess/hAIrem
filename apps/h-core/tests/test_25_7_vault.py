import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.visual.wardrobe import WardrobeService
from src.services.chat.commands import CommandHandler
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender


@pytest.fixture
def mock_db():
    db = MagicMock()
    db._call = AsyncMock()
    db.update_agent_state = AsyncMock()
    return db


@pytest.fixture
def mock_visual(mock_db):
    visual = MagicMock()
    visual.wardrobe = WardrobeService(mock_db)
    visual.generate_and_index = AsyncMock(return_value="file:///tmp/new.png")
    visual.notify_visual_asset = AsyncMock()
    return visual


@pytest.fixture
def mock_redis():
    redis = MagicMock()
    redis.publish = AsyncMock()
    return redis


@pytest.mark.asyncio
async def test_wardrobe_service_save_and_get(mock_db):
    service = WardrobeService(mock_db)

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


class TestWardrobeServiceEdgeCases:
    @pytest.mark.asyncio
    async def test_save_item_resolves_asset_id_via_query_when_missing(self):
        db = MagicMock()
        db._call = AsyncMock()
        db._call.return_value = [{"result": [{"id": "visual_asset:xyz"}]}]
        service = WardrobeService(db)

        result = await service.save_item("lisa", "summer_dress", "file:///tmp/img.png", "a summer dress")
        assert result == "visual_asset:xyz"

    @pytest.mark.asyncio
    async def test_save_item_returns_none_when_asset_id_unresolvable(self):
        db = MagicMock()
        db._call = AsyncMock(return_value=[{"result": []}])
        service = WardrobeService(db)

        result = await service.save_item("lisa", "mystery", "file:///tmp/x.png", "unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_save_item_returns_none_on_db_error_in_upsert(self):
        db = MagicMock()
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [{"result": [{"id": "visual_asset:abc"}]}]
            return [{"status": "ERR", "detail": "DB error"}]

        db._call = AsyncMock(side_effect=side_effect)
        service = WardrobeService(db)

        result = await service.save_item("lisa", "dress", "file:///tmp/img.png", "a dress")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_item_returns_none_on_empty_result(self):
        db = MagicMock()
        db._call = AsyncMock(return_value=[{"result": []}])
        service = WardrobeService(db)

        result = await service.get_item("lisa", "nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_item_with_category_filter(self):
        db = MagicMock()
        db._call = AsyncMock(return_value=[{"result": [{"name": "dress", "category": "garment"}]}])
        service = WardrobeService(db)

        result = await service.get_item("lisa", "dress", category="garment")
        assert result is not None
        call_args = db._call.call_args
        assert "category" in str(call_args)

    @pytest.mark.asyncio
    async def test_get_item_returns_none_on_exception(self):
        db = MagicMock()
        db._call = AsyncMock(side_effect=Exception("db offline"))
        service = WardrobeService(db)

        result = await service.get_item("lisa", "dress")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_items_returns_empty_on_no_results(self):
        db = MagicMock()
        db._call = AsyncMock(return_value=[{"result": []}])
        service = WardrobeService(db)

        result = await service.list_items("lisa")
        assert result == []

    @pytest.mark.asyncio
    async def test_list_items_with_category_filter(self):
        db = MagicMock()
        db._call = AsyncMock(return_value=[{"result": [{"name": "bg1", "category": "background"}]}])
        service = WardrobeService(db)

        result = await service.list_items("lisa", category="background")
        assert len(result) == 1
        call_args = db._call.call_args
        assert "background" in str(call_args)

    @pytest.mark.asyncio
    async def test_list_items_returns_empty_on_exception(self):
        db = MagicMock()
        db._call = AsyncMock(side_effect=Exception("db offline"))
        service = WardrobeService(db)

        result = await service.list_items("lisa")
        assert result == []
