import asyncio
import logging
import os
from datetime import datetime
from typing import Any

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
                    await self._call('use', namespace=self.ns, database=self.db) # Set context first
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
        """Basic schema setup and graph model initialization."""
        if not self.client: return
        try:
            # 1. Base tables (Flexible Schema)
            await self._call('query', "DEFINE TABLE messages SCHEMALESS;")
            await self._call('query', "DEFINE INDEX IF NOT EXISTS msg_time ON TABLE messages FIELDS timestamp;")
            
            # 2. Load Graph Schema from file if exists
            schema_path = os.path.join(os.path.dirname(__file__), "graph_schema.surql")
            if os.path.exists(schema_path):
                with open(schema_path) as f:
                    schema_queries = f.read()
                await self._call('query', schema_queries)
                logger.info("SurrealDB Graph Schema loaded from file.")
            else:
                logger.warning(f"Graph schema file not found at {schema_path}. Skipping detailed schema.")

        except Exception as e:
            logger.error(f"Failed to setup SurrealDB schema: {e}")

    async def insert_graph_memory(self, fact_data: dict[str, Any]):
        """
        Stores an atomic fact using the graph model.
        RELATE <agent>->BELIEVES-><fact>
        RELATE <fact>->ABOUT-><subject>
        """
        if not self.client or not SURREAL_AVAILABLE: return
        
        subject_name = fact_data.get("subject", "user")
        agent_name = fact_data.get("agent", "system")
        fact_content = fact_data.get("fact", "")
        embedding = fact_data.get("embedding", [])
        confidence = fact_data.get("confidence", 1.0)
        
        try:
            # 1. Upsert subject and agent (as subject nodes)
            # We use name as unique identifier via DEFINE INDEX ... UNIQUE
            sid = f"subject:`{subject_name.lower().replace(' ', '_')}`"
            aid = f"subject:`{agent_name.lower().replace(' ', '_')}`"
            
            await self._call('query', f"INSERT INTO subject (id, name) VALUES ({sid}, '{subject_name}') ON DUPLICATE KEY UPDATE name = '{subject_name}';")
            await self._call('query', f"INSERT INTO subject (id, name) VALUES ({aid}, '{agent_name}') ON DUPLICATE KEY UPDATE name = '{agent_name}';")
            
            # 2. Create Fact node
            fact_res = await self._call('create', "fact", {
                "content": fact_content,
                "embedding": embedding
            })
            if not fact_res: return
            
            fact_node = fact_res[0] if isinstance(fact_res, list) else fact_res
            fid = fact_node.get("id")
            
            # 3. Relate Agent -> BELIEVES -> Fact
            await self._call('query', f"RELATE {aid}->BELIEVES->{fid} SET confidence = {confidence}, strength = 1.0, last_accessed = time::now();")
            
            # 4. Relate Fact -> ABOUT -> Subject
            await self._call('query', f"RELATE {fid}->ABOUT->{sid};")
            
            logger.info(f"GRAPH_MEMORY: Linked {agent_name} -> BELIEVES -> Fact('{fact_content[:30]}...') ABOUT {subject_name}")
            
        except Exception as e:
            logger.error(f"Failed to insert graph memory: {e}")

    async def persist_message(self, message: dict[str, Any]):
        """Save a message to SurrealDB."""
        if not self.client or not SURREAL_AVAILABLE: return
        try:
            from datetime import timezone
            data = {
                "agent_id": message.get("sender", {}).get("agent_id", "unknown"),
                "type": message.get("type", "unknown"),
                "payload": message.get("payload", {}),
                "timestamp": message.get("timestamp", datetime.now(timezone.utc).isoformat() if not message.get("timestamp") else message.get("timestamp")),
                "processed": False
            }
            await self._call('create', "messages", data)
        except Exception as e:
            logger.error(f"Failed to persist message to SurrealDB: {e}")

    async def get_unprocessed_messages(self, limit: int = 20) -> list[dict[str, Any]]:
        """Retrieve messages that haven't been consolidated yet."""
        if not self.client or not SURREAL_AVAILABLE: return []
        try:
            res = await self._call('query', f"SELECT * FROM messages WHERE processed = false ORDER BY timestamp ASC LIMIT {limit};")
            if res and isinstance(res, list) and len(res) > 0:
                return res[0].get("result", []) if isinstance(res[0], dict) else res
            return []
        except Exception as e:
            logger.error(f"Failed to retrieve unprocessed messages: {e}")
            return []

    async def mark_as_processed(self, msg_ids: list[str]):
        """Mark a batch of messages as processed."""
        if not self.client or not SURREAL_AVAILABLE: return
        try:
            for mid in msg_ids:
                # msg_ids are expected to be the UUID part
                await self._call('query', f"UPDATE messages:`{mid}` SET processed = true;")
        except Exception as e:
            logger.error(f"Failed to mark messages as processed: {e}")

    async def insert_memory(self, fact_data: dict[str, Any]):
        """Store an atomic fact into the memories collection."""
        if not self.client or not SURREAL_AVAILABLE: return
        try:
            await self._call('create', "memories", fact_data)
        except Exception as e:
            logger.error(f"Failed to insert memory: {e}")

    async def semantic_search(self, embedding: list[float], agent_id: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
        """
        Perform a vector search on memories.
        If agent_id is provided, only return facts believed by that agent or 'system'.
        """
        if not self.client or not SURREAL_AVAILABLE: return []
        try:
            if agent_id:
                aid = f"subject:`{agent_id.lower().replace(' ', '_')}`"
                # Simpler, more reliable SurrealDB 2.x graph traversal query
                query = f"""
                SELECT *, 
                       vector::similarity::cosine(embedding, {embedding}) AS score 
                FROM fact 
                WHERE (<-BELIEVES[WHERE in = {aid} OR in = subject:`system`]).id
                ORDER BY score DESC LIMIT {limit};
                """
            else:
                query = f"SELECT *, vector::similarity::cosine(embedding, {embedding}) AS score FROM fact ORDER BY score DESC LIMIT {limit};"
            
            res = await self._call('query', query)
            if res and isinstance(res, list) and len(res) > 0:
                return res[0].get("result", []) if isinstance(res[0], dict) else res
            return []
        except Exception as e:
            logger.error(f"Failed to perform semantic search: {e}")
            return []

    async def update_memory_strength(self, agent_id: str, fact_id: str, boost: bool = True):
        """
        Updates the strength and last_accessed timestamp of a BELIEVES relation.
        If boost is True, increases strength.
        """
        if not self.client or not SURREAL_AVAILABLE: return
        try:
            aid = f"subject:`{agent_id.lower().replace(' ', '_')}`"
            
            # Construct query to find the specific edge and update it
            # We target the BELIEVES edge between the agent and the fact
            query = f"""
            UPDATE BELIEVES 
            SET strength = math::min(1.0, strength + 0.1), 
                last_accessed = time::now() 
            WHERE in = {aid} AND out = {fact_id};
            """
            await self._call('query', query)
            logger.debug(f"STRENGTH_UPDATE: Boosted memory {fact_id} for {agent_id}")
        except Exception as e:
            logger.error(f"Failed to update memory strength: {e}")

    async def apply_decay_to_all_memories(self, decay_rate: float, threshold: float = 0.1):
        """Applies decay to all BELIEVES edges and removes those below threshold."""
        if not self.client or not SURREAL_AVAILABLE: return
        try:
            # Removed time restriction for testing/immediate manual trigger
            decay_query = f"""
            UPDATE BELIEVES SET strength = strength * math::pow(0.9, {decay_rate});
            """
            await self._call('query', decay_query)
            
            # Cleanup
            delete_query = f"DELETE BELIEVES WHERE strength < {threshold};"
            await self._call('query', delete_query)
            
            logger.info(f"DECAY: Applied decay. Threshold for deletion: {threshold}")
        except Exception as e:
            logger.error(f"Failed to apply decay: {e}")
    async def merge_or_override_fact(self, old_fact_id: str, new_fact_data: dict[str, Any], resolution: dict[str, Any]):
        """Handles memory conflict resolution by merging or overriding existing facts."""
        if not self.client or not SURREAL_AVAILABLE: return
        try:
            action = resolution.get("action", "OVERRIDE")
            new_content = resolution.get("resolution", new_fact_data["fact"]).replace("'", "\\'")
            
            if action == "OVERRIDE":
                # 1. Update the fact node content and embedding
                await self._call('query', f"UPDATE {old_fact_id} SET content = '{new_content}', embedding = {new_fact_data['embedding']};")
                logger.info(f"CONFLICT_RESOLVED: Overrode {old_fact_id} with new synthesis.")
            else:
                # MERGE: Just update content but keep historical links
                await self._call('query', f"UPDATE {old_fact_id} SET content = '{new_content}';")
                logger.info(f"CONFLICT_RESOLVED: Merged facts into {old_fact_id}.")
                
        except Exception as e:
            logger.error(f"Failed to resolve memory conflict: {e}")

    async def get_messages(self, limit: int = 50) -> list[dict[str, Any]]:
        """Retrieve recent messages in chronological order."""
        if not self.client or not SURREAL_AVAILABLE: return []
        try:
            # Query latest messages but return them in ascending order for UI reconstruction
            res = await self._call('query', f"SELECT * FROM (SELECT * FROM messages ORDER BY timestamp DESC LIMIT {limit}) ORDER BY timestamp ASC;")
            
            if not res:
                return []
                
            # Handle SurrealDB 2.x response format (list of Result objects or list of lists)
            result_data = []
            if isinstance(res, list) and len(res) > 0:
                # Part 1: Check if it's a list of results
                first_part = res[0]
                if isinstance(first_part, dict) and "result" in first_part:
                    result_data = first_part["result"]
                elif isinstance(first_part, list):
                    result_data = first_part
                else:
                    result_data = res
            
            return result_data if isinstance(result_data, list) else []
        except Exception as e:
            logger.error(f"Failed to retrieve messages from SurrealDB: {e}")
            return []

    async def close(self):
        self._stop_event.set()
        if self.client:
            await self._call('close')