import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.infrastructure.surrealdb import SurrealDbClient


@pytest.fixture
def mock_surreal():
    client = MagicMock(spec=SurrealDbClient)
    client._call = AsyncMock()
    client.persist_message = SurrealDbClient.persist_message.__get__(client, SurrealDbClient)
    return client


@pytest.mark.asyncio
async def test_persist_message_redacts_api_key_in_payload(mock_surreal):
    """Sensitive API keys in payload must be redacted before persistence."""
    msg = {
        "sender": {"agent_id": "user", "role": "user"},
        "type": "NARRATIVE_TEXT",
        "payload": {"content": "My key is AIzaSyD-abc1234567890abcdefghijklmno12345"},
        "timestamp": "2024-01-01T00:00:00",
    }

    await mock_surreal.persist_message(msg)

    call_args = mock_surreal._call.call_args
    persisted_data = call_args[0][2]
    payload = persisted_data["payload"]
    content = payload.get("content", "")
    assert "AIzaSy" not in content, "Google API key must be redacted"
    assert "[REDACTED]" in content


@pytest.mark.asyncio
async def test_persist_message_redacts_password_in_payload(mock_surreal):
    """Passwords in payload must be redacted before persistence."""
    msg = {
        "sender": {"agent_id": "user", "role": "user"},
        "type": "NARRATIVE_TEXT",
        "payload": {"content": "My password: supersecret123"},
        "timestamp": "2024-01-01T00:00:00",
    }

    await mock_surreal.persist_message(msg)

    call_args = mock_surreal._call.call_args
    persisted_data = call_args[0][2]
    payload = persisted_data["payload"]
    content = payload.get("content", "")
    assert "supersecret123" not in content, "Password must be redacted"
    assert "[REDACTED]" in content


@pytest.mark.asyncio
async def test_persist_message_passes_clean_payload_unchanged(mock_surreal):
    """Clean payloads (no sensitive data) must pass through unchanged."""
    msg = {
        "sender": {"agent_id": "lisa", "role": "agent"},
        "type": "NARRATIVE_TEXT",
        "payload": {"content": "Bonne nuit ! Le frigo est fermé."},
        "timestamp": "2024-01-01T00:00:00",
    }

    await mock_surreal.persist_message(msg)

    call_args = mock_surreal._call.call_args
    persisted_data = call_args[0][2]
    payload = persisted_data["payload"]
    assert payload.get("content") == "Bonne nuit ! Le frigo est fermé."


@pytest.mark.asyncio
async def test_persist_message_handles_non_string_payload(mock_surreal):
    """Non-string payload content (e.g. dict with no 'content' key) must not crash."""
    msg = {
        "sender": {"agent_id": "system", "role": "system"},
        "type": "EVENT",
        "payload": {"action": "reboot", "target": "all"},
        "timestamp": "2024-01-01T00:00:00",
    }

    await mock_surreal.persist_message(msg)

    assert mock_surreal._call.called
