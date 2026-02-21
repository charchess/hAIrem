import logging
import base64
from typing import Any, Optional
from src.infrastructure.surrealdb import SurrealDbClient

logger = logging.getLogger(__name__)


class CredentialVaultService:
    """
    EPIC 7.5: Secure Credential Storage.
    Manages sensitive keys and tokens in a dedicated secured table.
    """

    def __init__(self, db_client: SurrealDbClient):
        self.db = db_client

    def _obfuscate(self, secret: str) -> str:
        """Simple obfuscation layer (Dette technique: replace with AES)."""
        if not secret:
            return ""
        return base64.b64encode(secret.encode()).decode()

    def _deobfuscate(self, obfuscated: str) -> str:
        """Simple de-obfuscation layer."""
        if not obfuscated:
            return ""
        try:
            return base64.b64decode(obfuscated.encode()).decode()
        except:
            return obfuscated

    async def save_llm_key(self, provider: str, key: str):
        """Saves an LLM API key securely."""
        logger.info(f"VAULT: Storing credential for provider '{provider}'")

        obfuscated_key = self._obfuscate(key)

        q = """
        INSERT INTO vault_credentials {
            id: $id,
            provider: $provider,
            key: $key,
            updated_at: time::now()
        } ON DUPLICATE KEY UPDATE 
            key = $key,
            updated_at = time::now();
        """
        params = {"id": f"vault_credentials:`{provider}`", "provider": provider, "key": obfuscated_key}
        await self.db._call("query", q, params)

    async def get_llm_key(self, provider: str) -> Optional[str]:
        """Retrieves and de-obfuscates an LLM API key."""
        cid = f"vault_credentials:`{provider}`"
        try:
            res = await self.db._call("query", f"SELECT key FROM {cid}")
            if res and isinstance(res, list) and len(res) > 0:
                first = res[0]
                results = first.get("result", []) if isinstance(first, dict) else first
                if results and len(results) > 0:
                    return self._deobfuscate(results[0].get("key"))
        except:
            pass
        return None
