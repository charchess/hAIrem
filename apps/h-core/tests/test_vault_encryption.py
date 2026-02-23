import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from cryptography.fernet import Fernet

from src.services.vault.credentials import CredentialVaultService


@pytest.fixture
def mock_db():
    db = MagicMock()
    db._call = AsyncMock(return_value=[{"result": []}])
    return db


@pytest.fixture
def fernet_key():
    return Fernet.generate_key().decode()


def test_vault_encrypts_with_fernet_not_base64(mock_db, fernet_key):
    with patch.dict(os.environ, {"VAULT_KEY": fernet_key}):
        service = CredentialVaultService(mock_db)
        encrypted = service._obfuscate("my-secret-api-key")

    assert encrypted != "my-secret-api-key"
    assert "my-secret-api-key" not in encrypted
    assert "bXktc2VjcmV0LWFwaS1rZXk=" not in encrypted, "Must not be plain base64"


def test_vault_decrypt_returns_original(mock_db, fernet_key):
    with patch.dict(os.environ, {"VAULT_KEY": fernet_key}):
        service = CredentialVaultService(mock_db)
        encrypted = service._obfuscate("my-secret-api-key")
        decrypted = service._deobfuscate(encrypted)

    assert decrypted == "my-secret-api-key"


def test_vault_fallback_generates_key_if_env_missing(mock_db, caplog):
    import logging

    with patch.dict(os.environ, {}, clear=True):
        if "VAULT_KEY" in os.environ:
            del os.environ["VAULT_KEY"]
        with caplog.at_level(logging.WARNING, logger="src.services.vault.credentials"):
            service = CredentialVaultService(mock_db)

    assert service._fernet is not None
    assert "VAULT_KEY" in caplog.text or "generated" in caplog.text.lower() or "warning" in caplog.text.lower()


def test_vault_roundtrip_without_env_key(mock_db):
    with patch.dict(os.environ, {}, clear=True):
        if "VAULT_KEY" in os.environ:
            del os.environ["VAULT_KEY"]
        service = CredentialVaultService(mock_db)
        encrypted = service._obfuscate("roundtrip-test")
        decrypted = service._deobfuscate(encrypted)

    assert decrypted == "roundtrip-test"


def test_vault_empty_secret_stays_empty(mock_db, fernet_key):
    with patch.dict(os.environ, {"VAULT_KEY": fernet_key}):
        service = CredentialVaultService(mock_db)
        assert service._obfuscate("") == ""
        assert service._deobfuscate("") == ""
