import logging
import asyncio
import json
from typing import List, Dict, Any, Optional

try:
    from surrealdb import Surreal
    SURREAL_AVAILABLE = True
except ImportError:
    SURREAL_AVAILABLE = False

logger = logging.getLogger(__name__)

class SurrealDbClient:
    def __init__(self, url: str, user: str, password: str, ns: str = "hairem", db: str = "core"):
        self.url = url
        self.user = user
        self.password = password
        self.ns = ns
        self.db = db
        self.client = None
        self._stop_event = asyncio.Event()

    async def _call(self, method_name: str, *args, **kwargs):
        """Helper to call client methods whether they are sync or async."""
        if not self.client: return None
        if not hasattr(self.client, method_name): return None
        
        func = getattr(self.client, method_name)
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    async def connect(self):
        """Connect to SurrealDB with exponential backoff."""
        global SURREAL_AVAILABLE
        if not SURREAL_AVAILABLE:
            logger.warning("SurrealDB connection skipped (library missing).")
            return

        attempt = 0
        while not self._stop_event.is_set():
            try:
                self.client = Surreal(self.url)
                await self._call('connect')
                
                # Try authenticating as root
                creds = {"user": self.user, "pass": self.password}
                try:
                    await self._call('signin', creds)
                except Exception:
                    creds = {"username": self.user, "password": self.password}
                    await self._call('signin', creds)
                
                # Only try to define if we are root
                try:
                    await self._call('query', f"DEFINE NAMESPACE {self.ns};")
                    await self._call('use', namespace=self.ns) # Set context first
                    await self._call('query', f"DEFINE DATABASE {self.db};")
                except Exception as def_e:
                    logger.warning(f"Could not define NS/DB: {def_e}")

                await self._call('use', namespace=self.ns, database=self.db)
                
                logger.info(f"Successfully connected to SurrealDB at {self.url}")
                await self.setup_schema()
                return
            except Exception as e:
                if attempt % 5 == 0: 
                    logger.error(f"SurrealDB still not connected (attempt {attempt+1}): {e}")
                attempt += 1
                await asyncio.sleep(min(60, 5 * attempt)) 
                
                if "authentication" in str(e).lower() or "permissions" in str(e).lower() or "IAM" in str(e):
                    logger.error("Auth/IAM Error detected. Keeping retries slow.")

    async def setup_schema(self):
        """Basic schema setup."""
        if not self.client: return
        try:
            await self._call('query', "DEFINE TABLE IF NOT EXISTS messages SCHEMAFULL;")
            await self._call('query', "DEFINE FIELD IF NOT EXISTS timestamp ON TABLE messages TYPE datetime;")
            await self._call('query', "DEFINE FIELD IF NOT EXISTS agent_id ON TABLE messages TYPE string;")
        except Exception as e:
            logger.error(f"Failed to setup SurrealDB schema: {e}")

    async def persist_message(self, message: Dict[str, Any]):
        """Save a message to SurrealDB."""
        if not self.client or not SURREAL_AVAILABLE: return
        try:
            data = {
                "agent_id": message.get("sender", {}).get("agent_id", "unknown"),
                "type": message.get("type", "unknown"),
                "payload": message.get("payload", {}),
                "timestamp": message.get("timestamp", datetime.utcnow().isoformat() if not message.get("timestamp") else message.get("timestamp"))
            }
            await self._call('create', "messages", data)
        except Exception as e:
            logger.error(f"Failed to persist message to SurrealDB: {e}")

    async def get_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent messages."""
        if not self.client or not SURREAL_AVAILABLE: return []
        try:
            res = await self._call('query', f"SELECT * FROM messages ORDER BY timestamp DESC LIMIT {limit};")
            if res and isinstance(res, list) and len(res) > 0:
                # Library returns a list of results for each query part
                result_data = res[0].get("result", []) if isinstance(res[0], dict) else res
                return result_data
            return []
        except Exception as e:
            logger.error(f"Failed to retrieve messages from SurrealDB: {e}")
            return []

    async def close(self):
        self._stop_event.set()
        if self.client:
            await self._call('close')