import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from src.infrastructure.redis import RedisClient


@pytest.fixture
def client():
    return RedisClient(host="localhost", port=6379)


@pytest.mark.asyncio
async def test_connect_success(client):
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock()
    with patch("redis.asyncio.from_url", return_value=mock_redis):
        result = await client.connect(timeout=5)
    assert result is True
    assert client.client is mock_redis


@pytest.mark.asyncio
async def test_connect_sets_stop_on_disconnect(client):
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock()
    mock_redis.aclose = AsyncMock()
    with patch("redis.asyncio.from_url", return_value=mock_redis):
        await client.connect(timeout=5)
    await client.disconnect()
    assert client._stop_event.is_set()


@pytest.mark.asyncio
async def test_publish_event_serializes_payload(client):
    mock_redis = AsyncMock()
    mock_redis.xadd = AsyncMock()
    client.client = mock_redis

    await client.publish_event("test_stream", {"type": "test", "data": {"key": "value"}})

    assert mock_redis.xadd.called
    call_kwargs = mock_redis.xadd.call_args[0]
    payload = call_kwargs[1]
    assert "type" in payload
    assert payload["type"] == "test"
    assert "data" in payload
    decoded = json.loads(payload["data"])
    assert decoded == {"key": "value"}


@pytest.mark.asyncio
async def test_publish_event_reconnects_if_no_client(client):
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock()
    mock_redis.xadd = AsyncMock()

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        await client.publish_event("stream", {"type": "evt"})

    assert mock_redis.xadd.called


@pytest.mark.asyncio
async def test_publish_hlink_message(client):
    mock_redis = AsyncMock()
    mock_redis.publish = AsyncMock()
    client.client = mock_redis

    msg = MagicMock()
    msg.model_dump_json = MagicMock(return_value='{"type": "test"}')

    await client.publish("channel", msg)

    mock_redis.publish.assert_called_once_with("channel", '{"type": "test"}')


@pytest.mark.asyncio
async def test_publish_dict_message(client):
    mock_redis = AsyncMock()
    mock_redis.publish = AsyncMock()
    client.client = mock_redis

    await client.publish("channel", {"key": "value"})

    call_args = mock_redis.publish.call_args[0]
    assert call_args[0] == "channel"
    assert json.loads(call_args[1]) == {"key": "value"}


@pytest.mark.asyncio
async def test_disconnect_closes_client(client):
    mock_redis = AsyncMock()
    mock_redis.aclose = AsyncMock()
    client.client = mock_redis

    await client.disconnect()

    mock_redis.aclose.assert_called_once()
    assert client._stop_event.is_set()


@pytest.mark.asyncio
async def test_subscribe_calls_handler(client):
    received = []

    async def handler(data):
        received.append(data)
        client._stop_event.set()

    mock_pubsub = AsyncMock()
    mock_pubsub.__aenter__ = AsyncMock(return_value=mock_pubsub)
    mock_pubsub.__aexit__ = AsyncMock(return_value=None)
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.get_message = AsyncMock(
        side_effect=[
            {"type": "message", "data": json.dumps({"event": "test"})},
            None,
        ]
    )

    mock_redis = AsyncMock()
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)
    client.client = mock_redis

    await client.subscribe("test_channel", handler)

    assert len(received) == 1
    assert received[0] == {"event": "test"}


@pytest.mark.asyncio
async def test_connect_times_out_if_redis_always_fails(client):
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=Exception("refused"))
        mock_from_url.return_value = mock_redis
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await client.connect(timeout=0)
    assert result is False


@pytest.mark.asyncio
async def test_publish_event_handles_exception(client):
    mock_redis = AsyncMock()
    mock_redis.xadd = AsyncMock(side_effect=Exception("stream error"))
    client.client = mock_redis
    await client.publish_event("stream", {"type": "test"})


@pytest.mark.asyncio
async def test_publish_string_message(client):
    mock_redis = AsyncMock()
    mock_redis.publish = AsyncMock()
    client.client = mock_redis

    await client.publish("channel", "raw string")
    call_args = mock_redis.publish.call_args[0]
    assert call_args[1] == "raw string"


@pytest.mark.asyncio
async def test_publish_reconnects_if_no_client(client):
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock()
    mock_redis.publish = AsyncMock()

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        await client.publish("channel", {"key": "value"})

    assert mock_redis.publish.called


@pytest.mark.asyncio
async def test_publish_handles_exception(client):
    mock_redis = AsyncMock()
    mock_redis.publish = AsyncMock(side_effect=Exception("publish error"))
    client.client = mock_redis
    await client.publish("channel", {"key": "val"})


@pytest.mark.asyncio
async def test_listen_stream_processes_message(client):
    received = []

    async def handler(data):
        received.append(data)
        client._stop_event.set()

    mock_redis = AsyncMock()
    mock_redis.xgroup_create = AsyncMock()
    mock_redis.xack = AsyncMock()

    call_count = 0

    async def xreadgroup_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return [("stream", [("1-0", {"type": "test", "data": '{"key":"val"}'})])]
        return []

    mock_redis.xreadgroup = AsyncMock(side_effect=xreadgroup_side_effect)
    client.client = mock_redis

    await client.listen_stream("stream", "group", "consumer", handler)

    assert len(received) == 1
    mock_redis.xack.assert_called_once()


@pytest.mark.asyncio
async def test_listen_stream_group_already_exists(client):
    async def handler(data):
        client._stop_event.set()

    mock_redis = AsyncMock()
    import redis.asyncio as redis_async

    mock_redis.xgroup_create = AsyncMock(
        side_effect=redis_async.ResponseError("BUSYGROUP Consumer Group name already exists")
    )
    mock_redis.xreadgroup = AsyncMock(return_value=[])
    client.client = mock_redis
    client._stop_event.set()

    await client.listen_stream("stream", "group", "consumer", handler)
    mock_redis.xreadgroup.assert_not_called()


@pytest.mark.asyncio
async def test_listen_stream_unwraps_nested_dict(client):
    received = []

    async def handler(data):
        received.append(data)
        client._stop_event.set()

    mock_redis = AsyncMock()
    mock_redis.xgroup_create = AsyncMock()
    mock_redis.xack = AsyncMock()

    call_count = 0

    async def xreadgroup_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            nested = json.dumps({"nested_key": "nested_val"})
            return [("stream", [("1-0", {"type": "msg_type", "data": nested})])]
        return []

    mock_redis.xreadgroup = AsyncMock(side_effect=xreadgroup_side_effect)
    client.client = mock_redis

    await client.listen_stream("stream", "group", "consumer", handler)

    assert received[0] == {"nested_key": "nested_val"}
