import asyncio
import logging
import os
import inspect
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
        
        func = getattr(self.client, method_name)
        
        async def _exec():
            res = func(*args, **kwargs)
            if inspect.isawaitable(res):
                res = await res
            return res

        try:
            res = await _exec()
            
            # Detect missing scope/auth in response string
            err_msg = str(res).lower()
            if "namespace" in err_msg or "database" in err_msg or "permissions" in err_msg or "iam error" in err_msg:
                logger.warning(f"SURREAL_SESSION_LOSS: {res}. Re-connecting...")
                await self.connect()
                return await _exec()

            logger.debug(f"SURREAL_CALL: {method_name} success")
            return res
        except Exception as e:
            err_msg = str(e).lower()
            if "namespace" in err_msg or "database" in err_msg or "iam" in str(e) or "auth" in err_msg:
                logger.warning(f"SURREAL_EXCEPTION: {e}. Re-connecting...")
                await self.connect()
                try:
                    return await _exec()
                except Exception as retry_e:
                    logger.error(f"SURREAL_RETRY_FAILED: {retry_e}")
                    return None
            
            logger.error(f"SURREAL_ERROR: {method_name} failed: {e}")
            return None

    async def connect(self):
        """Connect to SurrealDB via HTTP for stability."""
        global SURREAL_AVAILABLE
        if not SURREAL_AVAILABLE: return

        # STORY 25.7: Reset connection state
        if self.client:
            try: await self.client.close()
            except: pass
            
        http_url = self.url.replace("ws://", "http://").replace("/rpc", "")
        self.client = Surreal(http_url)
        
        try:
            u = self.user or "root"
            p = self.password or "root"
            
            # Helper to try signin
            async def try_auth(creds):
                try:
                    res = self.client.signin(creds)
                    if inspect.isawaitable(res): await res
                    return True
                except Exception as e:
                    logger.debug(f"Auth failed for {creds.keys()}: {e}")
                    return False

            # Try common credential formats
            auth_success = False
            # Option A: Protocol standard
            if await try_auth({"user": u, "pass": p}):
                auth_success = True
            # Option B: Pythonic
            elif await try_auth({"username": u, "password": p}):
                auth_success = True
            # Option C: Hybrid
            elif await try_auth({"user": u, "password": p}):
                auth_success = True
            
            if not auth_success:
                raise Exception("Authentication failed with all credential formats.")

            # 2. Use (Namespace/Database)
            # Try dict first (standard)
            try:
                res = self.client.use({"namespace": self.ns, "database": self.db})
                if inspect.isawaitable(res): await res
            except:
                # Fallback to positional
                res = self.client.use(self.ns, self.db)
                if inspect.isawaitable(res): await res
            
            logger.info(f"Connected and Scoped SurrealDB: {self.ns}:{self.db} as {u}")
        except Exception as e:
            logger.error(f"SurrealDB connection failed: {e}")

    async def setup_schema(self):
        """Basic schema setup and graph model initialization."""
        if not self.client: return
        try:
            # STORY 25.1: Refresh visual_asset with correct dimensions (384 for FastEmbed/MiniLM)
            logger.info("SYSTEM: Initializing schema...")
            
            # Atomic setup queries
            setup_queries = [
                f"DEFINE NAMESPACE IF NOT EXISTS {self.ns};",
                f"USE NAMESPACE {self.ns};",
                f"DEFINE USER IF NOT EXISTS root ON NAMESPACE PASSWORD 'root' ROLES OWNER;",
                f"DEFINE DATABASE IF NOT EXISTS {self.db};",
                f"USE DATABASE {self.db};",
                f"DEFINE USER IF NOT EXISTS root ON DATABASE PASSWORD 'root' ROLES OWNER;",
                "REMOVE TABLE visual_asset;",
                "DEFINE TABLE visual_asset SCHEMAFULL PERMISSIONS FULL;",
                "DEFINE FIELD url ON TABLE visual_asset TYPE string;",
                "DEFINE FIELD prompt ON TABLE visual_asset TYPE string;",
                "DEFINE FIELD agent_id ON TABLE visual_asset TYPE string;",
                "DEFINE FIELD tags ON TABLE visual_asset TYPE array<string>;",
                "DEFINE FIELD embedding ON TABLE visual_asset TYPE array<float, 384>;",
                "DEFINE FIELD last_used ON TABLE visual_asset TYPE datetime DEFAULT time::now();",
                "DEFINE FIELD reference_image_used ON TABLE visual_asset TYPE option<string>;",
                "DEFINE INDEX asset_mt ON TABLE visual_asset FIELDS embedding MTREE DIMENSION 384 DIST COSINE;",
                "DEFINE INDEX asset_url ON TABLE visual_asset FIELDS url UNIQUE;",
                "REMOVE TABLE vault;",
                "DEFINE TABLE vault SCHEMAFULL PERMISSIONS FULL;",
                "DEFINE FIELD agent_id ON TABLE vault TYPE string;",
                "DEFINE FIELD prompt ON TABLE visual_asset TYPE string;",
                "DEFINE FIELD agent_id ON TABLE visual_asset TYPE string;",
                "DEFINE FIELD tags ON TABLE visual_asset TYPE array<string>;",
                "DEFINE FIELD embedding ON TABLE visual_asset TYPE array<float, 384>;",
                "DEFINE FIELD last_used ON TABLE visual_asset TYPE datetime DEFAULT time::now();",
                "DEFINE FIELD reference_image_used ON TABLE visual_asset TYPE string;",
                "DEFINE INDEX asset_mt ON TABLE visual_asset FIELDS embedding MTREE DIMENSION 384 DIST COSINE;",
                "DEFINE INDEX asset_url ON TABLE visual_asset FIELDS url UNIQUE;",
                "REMOVE TABLE vault;",
                "DEFINE TABLE vault SCHEMAFULL PERMISSIONS FULL;",
                "DEFINE FIELD agent_id ON TABLE vault TYPE string;",
                "DEFINE FIELD name ON TABLE vault TYPE string;",
                "DEFINE FIELD asset_id ON TABLE vault TYPE record;",
                "DEFINE FIELD uri ON TABLE vault TYPE string;",
                "DEFINE FIELD prompt ON TABLE vault TYPE string;",
                "DEFINE FIELD timestamp ON TABLE vault TYPE datetime DEFAULT time::now();",
                "DEFINE INDEX vault_unique ON TABLE vault FIELDS agent_id, name UNIQUE;",
                "DEFINE TABLE IF NOT EXISTS messages SCHEMALESS PERMISSIONS FULL;"
            ]
            
            for q in setup_queries:
                await self.client.query(q)
                
            logger.info("SYSTEM: SurrealDB Schema established.")

            # 2. Load Graph Schema from file if exists
            schema_path = os.path.join(os.path.dirname(__file__), "graph_schema.surql")
            if os.path.exists(schema_path):
                with open(schema_path) as f:
                    schema_queries = f.read()
                await self.client.query(schema_queries)
                logger.info("SurrealDB Graph Schema loaded.")

        except Exception as e:
            logger.error(f"Failed to setup SurrealDB schema: {e}")



    async def save_asset_record(self, data: dict[str, Any]) -> str | None:
        """
        Creates a visual_asset record and returns its ID.
        Uses raw query to ensure native functions like time::now() work.
        """
        q = """
        CREATE visual_asset CONTENT {
            url: $url,
            prompt: $prompt,
            embedding: $embedding,
            agent_id: $agent_id,
            tags: $tags,
            last_used: time::now(),
            reference_image_used: $ref
        };
        """
        params = {
            "url": data.get("url"),
            "prompt": data.get("prompt", ""),
            "embedding": data.get("embedding", []),
            "agent_id": data.get("agent_id", "system"),
            "tags": data.get("tags", []),
            "ref": data.get("reference_image_used", "")
        }

        try:
            res = await self._call("query", q, params)
            logger.info(f"DB_SAVE_ASSET_RES: {res}")
            
            # Parse result
            if isinstance(res, list) and len(res) > 0:
                first_item = res[0]
                
                # CASE 1: Standard 'query' response with 'result' wrapper
                if isinstance(first_item, dict) and "result" in first_item:
                    results = first_item["result"]
                # CASE 2: Direct list of records (e.g. from CREATE inside query sometimes)
                elif isinstance(first_item, dict) and "id" in first_item:
                    results = res
                # CASE 3: List of lists (rare)
                elif isinstance(first_item, list):
                    results = first_item
                else:
                    results = res # Fallback

                if results and isinstance(results, list) and len(results) > 0:
                    record = results[0]
                    # Handle RecordID object if it's not a string
                    asset_id = record.get("id")
                    if asset_id:
                        return str(asset_id)
            return None
        except Exception as e:
            logger.error(f"DB_SAVE_ASSET_FAILED: {e}")
            return None
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
            data = {
                "agent_id": message.get("sender", {}).get("agent_id", "unknown"),
                "type": message.get("type", "unknown"),
                "payload": message.get("payload", {}),
                "timestamp": message.get("timestamp", datetime.utcnow().isoformat() if not message.get("timestamp") else message.get("timestamp")),
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

    async def update_agent_state(self, agent_id: str, relation_type: str, target_data: dict[str, Any]):
        """
        Updates a transient state (like WEARS, IS_IN).
        Ensures uniqueness: Deletes old edges of this type for this agent.
        """
        if not self.client or not SURREAL_AVAILABLE: return

        try:
            aid = f"subject:`{agent_id.lower().replace(' ', '_')}`"
            
            # 1. Invalidate old state (Delete existing edges)
            await self._call('query', f"DELETE {relation_type} WHERE in = {aid};")
            
            # 2. Prepare target node
            # target_table determined by relation_type
            target_table = "outfit" if relation_type == "WEARS" else "location"
            
            # Generate a simple ID key if not provided
            raw_id = target_data.get("id", target_data.get("name", "unknown")).lower()
            # Sanitize ID
            safe_id = "".join(c for c in raw_id if c.isalnum() or c in ('_', '-'))[:30]
            if not safe_id: safe_id = f"gen_{int(datetime.now().timestamp())}"
            
            target_record_id = f"{target_table}:`{safe_id}`"
            
            # Create/Update target node
            content = target_data.get("description", target_data.get("name", "Unknown"))
            name = target_data.get("name", "Unknown")
            
            # Escape single quotes in content
            content = content.replace("'", "\\'")
            name = name.replace("'", "\\'")

            # Use UPDATE to Create or Update (upsert-ish)
            await self._call('query', f"UPDATE {target_record_id} SET description = '{content}', name = '{name}';")
            
            # 3. Create new edge
            await self._call('query', f"RELATE {aid}->{relation_type}->{target_record_id} SET timestamp = time::now();")
            
            logger.info(f"STATE_UPDATE: {agent_id} now {relation_type} {target_record_id}")
            
        except Exception as e:
            logger.error(f"Failed to update agent state: {e}")

    async def get_agent_state(self, agent_id: str) -> list[dict[str, Any]]:
        """
        Retrieves all active transient states (edges and target nodes) for an agent.
        """
        if not self.client or not SURREAL_AVAILABLE: return []
        try:
            aid = f"subject:`{agent_id.lower().replace(' ', '_')}`"
            
            # Query for WEARS and IS_IN relations
            # We want the relation type, and the target node's description/name
            query = f"""
            SELECT 
                meta::table(id) as relation,
                out.name as name,
                out.description as description
            FROM WEARS, IS_IN
            WHERE in = {aid};
            """
            res = await self._call('query', query)
            if res and isinstance(res, list) and len(res) > 0:
                return res[0].get("result", []) if isinstance(res[0], dict) else res
            return []
        except Exception as e:
            logger.error(f"Failed to get agent state: {e}")
            return []

    async def get_messages(self, limit: int = 50) -> list[dict[str, Any]]:
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