import logging
import os
from typing import Optional
from cryptography.fernet import Fernet
from src.infrastructure.surrealdb import SurrealDbClient

logger = logging.getLogger(__name__)


class CredentialVaultService:
    def __init__(self, db_client: SurrealDbClient):
        self.db = db_client
        self._fernet = self._init_fernet()

    def _init_fernet(self) -> Fernet:
        raw_key = os.environ.get("VAULT_KEY")
        if raw_key:
            try:
                return Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)
            except Exception as e:
                logger.warning(f"VAULT: Invalid VAULT_KEY ({e}). Generating ephemeral key.")
        else:
            logger.warning("VAULT: VAULT_KEY not set. Generated ephemeral key — secrets will be lost on restart.")
        key = Fernet.generate_key()
        return Fernet(key)

    def _obfuscate(self, secret: str) -> str:
        if not secret:
            return ""
        return self._fernet.encrypt(secret.encode()).decode()

    def _deobfuscate(self, obfuscated: str) -> str:
        if not obfuscated:
            return ""
        try:
            return self._fernet.decrypt(obfuscated.encode()).decode()
        except Exception:
            return obfuscated

    async def save_llm_key(self, provider: str, key: str):
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
        cid = f"vault_credentials:`{provider}`"
        try:
            res = await self.db._call("query", f"SELECT key FROM {cid}")
            if res and isinstance(res, list) and len(res) > 0:
                first = res[0]
                results = first.get("result", []) if isinstance(first, dict) else first
                if results and len(results) > 0:
                    return self._deobfuscate(results[0].get("key"))
        except Exception:
            pass
        return None
