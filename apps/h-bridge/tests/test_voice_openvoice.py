import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from infrastructure.voice_openvoice import OpenVoiceClient

BASE_AUDIO = b"RIFF\x24\x00\x00\x00WAVEfmt "
CLONED_AUDIO = b"RIFF\x48\x00\x00\x00WAVEfmt "


@pytest.fixture
def client():
    return OpenVoiceClient(base_url="http://localhost:8008")


@pytest.fixture
def ref_wav(tmp_path):
    ref = tmp_path / "voice_ref.wav"
    ref.write_bytes(BASE_AUDIO)
    return str(ref)


def test_clone_voice_returns_cloned_bytes(client, ref_wav):
    mock_resp = MagicMock()
    mock_resp.content = CLONED_AUDIO
    mock_resp.raise_for_status = MagicMock()

    with patch("infrastructure.voice_openvoice.httpx.post", return_value=mock_resp) as mock_post:
        result = client.clone_voice(BASE_AUDIO, ref_wav, tone=0.05, speed=1.0)

    mock_post.assert_called_once()
    assert result == CLONED_AUDIO


def test_clone_voice_returns_original_on_missing_reference(client):
    result = client.clone_voice(BASE_AUDIO, "/nonexistent/voice_ref.wav")
    assert result == BASE_AUDIO


def test_clone_voice_returns_none_on_http_error(client, ref_wav):
    with patch("infrastructure.voice_openvoice.httpx.post", side_effect=Exception("500 error")):
        result = client.clone_voice(BASE_AUDIO, ref_wav)

    assert result is None


def test_clone_voice_sends_tone_and_speed(client, ref_wav):
    mock_resp = MagicMock()
    mock_resp.content = CLONED_AUDIO
    mock_resp.raise_for_status = MagicMock()

    with patch("infrastructure.voice_openvoice.httpx.post", return_value=mock_resp) as mock_post:
        client.clone_voice(BASE_AUDIO, ref_wav, tone=0.1, speed=1.2)

    data = mock_post.call_args[1]["data"]
    assert data["tone"] == "0.1"
    assert data["speed"] == "1.2"
