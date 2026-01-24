import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.infrastructure.surrealdb import SurrealDbClient
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

@pytest.fixture
def mock_surreal():
    with patch("src.infrastructure.surrealdb.Surreal", autospec=True) as mock:
        yield mock

@pytest.mark.asyncio
async def test_surreal_connect(mock_surreal):
    client = SurrealDbClient(url="ws://mock:8000/rpc")
    # Setup mock instance
    mock_instance = mock_surreal.return_value
    mock_instance.connect = AsyncMock()
    mock_instance.signin = AsyncMock()
    mock_instance.use = AsyncMock()
    
    await client.connect()
    
    mock_instance.connect.assert_called_once()
    mock_instance.signin.assert_called_once_with({"user": "root", "pass": "root"})
    mock_instance.use.assert_called_once_with("hairem", "core")

@pytest.mark.asyncio
async def test_surreal_insert_message(mock_surreal):
    client = SurrealDbClient()
    mock_instance = mock_surreal.return_value
    mock_instance.create = AsyncMock()
    client.client = mock_instance # Pretend connected
    
    msg = HLinkMessage(
        type=MessageType.NARRATIVE_TEXT,
        sender=Sender(agent_id="user", role="user"),
        recipient=Recipient(target="Renarde"),
        payload=Payload(content="Hello")
    )
    
    await client.insert_message(msg)
    
    # Check if create was called with correct record ID and data
    mock_instance.create.assert_called_once()
    args, _ = mock_instance.create.call_args
    assert args[0] == f"messages:{msg.id}"
    assert args[1]["payload"]["content"] == "Hello"

@pytest.mark.asyncio
async def test_surreal_get_messages(mock_surreal):
    client = SurrealDbClient()
    mock_instance = mock_surreal.return_value
    
    # Mock result format of surrealdb-python
    mock_query_result = [
        {
            "result": [
                {"id": "msg1", "timestamp": "2026-01-23T10:00:00Z", "payload": {"content": "First"}},
                {"id": "msg2", "timestamp": "2026-01-23T10:01:00Z", "payload": {"content": "Second"}}
            ],
            "status": "OK"
        }
    ]
    mock_instance.query = AsyncMock(return_value=mock_query_result)
    client.client = mock_instance
    
    messages = await client.get_messages(limit=2)
    
    assert len(messages) == 2
    assert messages[0]["payload"]["content"] == "First"
    assert messages[1]["payload"]["content"] == "Second"
    mock_instance.query.assert_called_once()
