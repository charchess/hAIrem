import pytest
from unittest.mock import MagicMock, patch
from infrastructure.tts_melotts import MeloTTSClient

WAV_BYTES = b"RIFF\x24\x00\x00\x00WAVEfmt "


@pytest.fixture
def client():
    return MeloTTSClient(base_url="http://localhost:8008")


def test_synthesize_returns_bytes_on_success(client):
    mock_resp = MagicMock()
    mock_resp.content = WAV_BYTES
    mock_resp.raise_for_status = MagicMock()

    with patch("infrastructure.tts_melotts.httpx.post", return_value=mock_resp) as mock_post:
        result = client.synthesize("Bonjour le monde", language="FR", speed=1.0)

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert call_kwargs[1]["json"]["text"] == "Bonjour le monde"
    assert call_kwargs[1]["json"]["language"] == "FR"
    assert result == WAV_BYTES


def test_synthesize_returns_none_on_http_error(client):
    with patch("infrastructure.tts_melotts.httpx.post", side_effect=Exception("Connection refused")):
        result = client.synthesize("test")

    assert result is None


def test_synthesize_respects_speed_parameter(client):
    mock_resp = MagicMock()
    mock_resp.content = WAV_BYTES
    mock_resp.raise_for_status = MagicMock()

    with patch("infrastructure.tts_melotts.httpx.post", return_value=mock_resp) as mock_post:
        client.synthesize("hello", speed=1.2)

    assert mock_post.call_args[1]["json"]["speed"] == 1.2


def test_health_check_returns_true_on_200(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("infrastructure.tts_melotts.httpx.get", return_value=mock_resp):
        assert client.health_check() is True


def test_health_check_returns_false_on_error(client):
    with patch("infrastructure.tts_melotts.httpx.get", side_effect=Exception("timeout")):
        assert client.health_check() is False
