import asyncio
import logging
import os
import inspect
from datetime import datetime
from typing import Any, List, Optional, Dict

try:
    from surrealdb import Surreal
except ImportError:
    Surreal = None

SURREAL_AVAILABLE = Surreal is not None

logger = logging.getLogger(__name__)

class SurrealDbClient:
    def __init__(self, url: str, user: str, password: str, ns: str = "hairem", db: str = "core"):
        self.url = url
        self.user = user
        self.password = password
        self.ns = ns
        self.db = db
        self.client: Optional[Surreal] = None
        self._stop_event = asyncio.Event()

    async def _call(self, method_name: str, *args, **kwargs) -> Any:
        """Robust wrapper for SurrealDB client calls with auto-reconnect."""
        if not self.client:
            await self.connect()
            if not self.client: return None
        
        try:
            method = getattr(self.client, method_name)
            res = method(*args, **kwargs)
            if inspect.isawaitable(res):
                res = await res
            
            # Detect session loss in result string
            if isinstance(res, str) and any(x in res.lower() for x in ["namespace", "database", "permissions", "iam"]):
                logger.warning(f"SURREAL_SESSION_LOSS detected. Re-connecting...")
                await self.connect()
                return await self._call(method_name, *args, **kwargs)

            return res
        except Exception as e:
            err_msg = str(e).lower()
            if any(x in err_msg for x in ["namespace", "database", "iam", "auth"]):
                logger.warning(f"SURREAL_AUTH_EXCEPTION: {e}. Re-connecting...")
                await self.connect()
                try:
                    return await self._call(method_name, *args, **kwargs)
                except Exception as retry_e:
                    logger.error(f"SURREAL_RETRY_FAILED: {retry_e}")
                    return None
            
            logger.error(f"SURREAL_ERROR: {method_name} failed: {e}")
            return None

    async def connect(self):
        """Connect to SurrealDB."""
        if not SURREAL_AVAILABLE: return

        if self.client:
            try: await self.client.close()
            except: pass
            
        # We keep the constructor call simple for mock compatibility in tests
        self.client = Surreal(self.url)
        
        try:
            # Need to call connect() explicitly in newer versions of the library
            if hasattr(self.client, "connect"):
                res = self.client.connect()
                if inspect.isawaitable(res): await res

            # Multi-format authentication
            creds = {"user": self.user or "root", "pass": self.password or "root"}
            try:
                res = self.client.signin(creds)
                if inspect.isawaitable(res): await res
            except:
                res = self.client.signin({"username": creds["user"], "password": creds["pass"]})
                if inspect.isawaitable(res): await res

            res = self.client.use(self.ns, self.db)
            if inspect.isawaitable(res): await res
            
            logger.info(f"Connected to SurrealDB: {self.ns}:{self.db}")
        except Exception as e:
            logger.error(f"SurrealDB connection failed: {e}")
            self.client = None

    async def setup_schema(self):
        """Initialize SCHEMAFULL tables and indices safely."""
        if not self.client: return
        try:
            logger.info("SYSTEM: Configuring SurrealDB Schema (SCHEMAFULL)...")
            
            setup_queries = f"""
            DEFINE NAMESPACE IF NOT EXISTS {self.ns};
            USE NAMESPACE {self.ns};
            DEFINE DATABASE IF NOT EXISTS {self.db};
            USE DATABASE {self.db};

            DEFINE TABLE IF NOT EXISTS visual_asset SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS url ON TABLE visual_asset TYPE string;
            DEFINE FIELD IF NOT EXISTS prompt ON TABLE visual_asset TYPE string;
            DEFINE FIELD IF NOT EXISTS agent_id ON TABLE visual_asset TYPE string;
            DEFINE FIELD IF NOT EXISTS tags ON TABLE visual_asset TYPE array<string>;
            DEFINE FIELD IF NOT EXISTS embedding ON TABLE visual_asset TYPE array<float, 384>;
            DEFINE FIELD IF NOT EXISTS last_used ON TABLE visual_asset TYPE datetime DEFAULT time::now();
            DEFINE INDEX IF NOT EXISTS asset_url ON TABLE visual_asset FIELDS url UNIQUE;

            DEFINE TABLE IF NOT EXISTS vault SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS agent_id ON TABLE vault TYPE string;
            DEFINE FIELD IF NOT EXISTS name ON TABLE vault TYPE string;
            DEFINE FIELD IF NOT EXISTS asset_id ON TABLE vault TYPE record<visual_asset>;
            DEFINE FIELD IF NOT EXISTS timestamp ON TABLE vault TYPE datetime DEFAULT time::now();
            DEFINE INDEX IF NOT EXISTS vault_unique ON TABLE vault FIELDS agent_id, name UNIQUE;

            DEFINE TABLE IF NOT EXISTS messages SCHEMALESS;
            DEFINE TABLE IF NOT EXISTS subject SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS name ON TABLE subject TYPE string;
            DEFINE INDEX IF NOT EXISTS subject_name ON TABLE subject FIELDS name UNIQUE;

            DEFINE TABLE IF NOT EXISTS fact SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS content ON TABLE fact TYPE string;
            DEFINE FIELD IF NOT EXISTS embedding ON TABLE fact TYPE array<float, 384>;
            DEFINE FIELD IF NOT EXISTS user_id ON TABLE fact TYPE string;
            DEFINE FIELD IF NOT EXISTS user_name ON TABLE fact TYPE string;

            DEFINE TABLE IF NOT EXISTS BELIEVES SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS confidence ON TABLE BELIEVES TYPE float DEFAULT 1.0;
            DEFINE FIELD IF NOT EXISTS strength ON TABLE BELIEVES TYPE float DEFAULT 1.0;
            DEFINE FIELD IF NOT EXISTS last_accessed ON TABLE BELIEVES TYPE datetime DEFAULT time::now();

            DEFINE TABLE IF NOT EXISTS ABOUT SCHEMAFULL;
            
            DEFINE TABLE IF NOT EXISTS agent_config SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS agent_id ON TABLE agent_config TYPE string;
            DEFINE FIELD IF NOT EXISTS parameters ON TABLE agent_config TYPE object;
            DEFINE FIELD IF NOT EXISTS enabled ON TABLE agent_config TYPE bool DEFAULT true;
            DEFINE FIELD IF NOT EXISTS version ON TABLE agent_config TYPE string DEFAULT '1.0.0';
            DEFINE INDEX IF NOT EXISTS agent_config_id ON TABLE agent_config FIELDS agent_id UNIQUE;
            """
            
            await self._call("query", setup_queries)
            
            # Load external schema file
            schema_path = os.path.join(os.path.dirname(__file__), "graph_schema.surql")
            if os.path.exists(schema_path):
                with open(schema_path) as f:
                    await self._call("query", f.read())
                logger.info("SurrealDB Graph Schema loaded.")

        except Exception as e:
            logger.error(f"Failed to setup SurrealDB schema: {e}")

    async def insert_graph_memory(self, fact_data: Dict[str, Any]):
        """Stores an atomic fact using the graph model."""
        subject_name = fact_data.get("subject", "user")
        agent_name = fact_data.get("agent", "system")
        fact_content = fact_data.get("fact", "")
        embedding = fact_data.get("embedding", [])
        confidence = fact_data.get("confidence", 1.0)
        user_id = fact_data.get("user_id")
        user_name = fact_data.get("user_name")

        sid = f"subject:`{subject_name.lower().replace(' ', '_')}`"
        aid = f"subject:`{agent_name.lower().replace(' ', '_')}`"

        try:
            await self._call('query', f"INSERT INTO subject (id, name) VALUES ({sid}, $name) ON DUPLICATE KEY UPDATE name = $name;", {"name": subject_name})
            await self._call('query', f"INSERT INTO subject (id, name) VALUES ({aid}, $name) ON DUPLICATE KEY UPDATE name = $name;", {"name": agent_name})
            
            fact_data_db = {"content": fact_content, "embedding": embedding}
            if user_id:
                fact_data_db["user_id"] = user_id
            if user_name:
                fact_data_db["user_name"] = user_name
                
            fact_res = await self._call('create', "fact", fact_data_db)
            if not fact_res: return
            fid = fact_res[0].get("id") if isinstance(fact_res, list) else fact_res.get("id")
            
            await self._call('query', f"RELATE {aid}->BELIEVES->{fid} SET confidence = $conf, strength = 1.0, last_accessed = time::now();", {"conf": confidence})
            await self._call('query', f"RELATE {fid}->ABOUT->{sid};")
        except Exception as e:
            logger.error(f"Failed to insert graph memory: {e}")

    async def persist_message(self, message: Dict[str, Any]):
        """Save a message to SurrealDB."""
        data = {
            "agent_id": message.get("sender", {}).get("agent_id", "unknown"),
            "type": message.get("type", "unknown"),
            "payload": message.get("payload", {}),
            "timestamp": message.get("timestamp") or datetime.utcnow().isoformat(),
            "processed": False
        }
        await self._call('create', "messages", data)

    async def get_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent messages."""
        res = await self._call('query', f"SELECT * FROM messages ORDER BY timestamp DESC LIMIT {limit};")
        if res and isinstance(res, list) and len(res) > 0:
            return res[0].get("result", []) if isinstance(res[0], dict) else res
        return []

    async def get_unprocessed_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve messages that haven't been processed for cognitive consolidation."""
        res = await self._call('query', f"SELECT * FROM messages WHERE processed = false ORDER BY timestamp ASC LIMIT {limit};")
        if res and isinstance(res, list) and len(res) > 0:
            return res[0].get("result", []) if isinstance(res[0], dict) else res
        return []

    async def mark_as_processed(self, msg_ids: List[str]):
        """Mark a batch of messages as processed."""
        for mid in msg_ids:
            # msg_ids are expected to be the UUID part
            await self._call('query', f"UPDATE messages SET processed = true WHERE id = messages:`{mid}`;")

    async def merge_or_override_fact(self, old_fact_id: str, new_fact_data: Dict[str, Any], resolution: Dict[str, Any]):
        """Handles memory conflict resolution by merging or overriding existing facts."""
        action = resolution.get("action", "OVERRIDE")
        new_content = resolution.get("resolution", new_fact_data["fact"]).replace("'", "\\'")
        
        if action == "OVERRIDE":
            # 1. Update the fact node content and embedding
            await self._call('query', f"UPDATE {old_fact_id} SET content = '{new_content}', embedding = $emb;", {"emb": new_fact_data['embedding']})
            logger.info(f"CONFLICT_RESOLVED: Overrode {old_fact_id} with new synthesis.")
        else:
            # MERGE: Just update content but keep historical links
            await self._call('query', f"UPDATE {old_fact_id} SET content = '{new_content}';")
            logger.info(f"CONFLICT_RESOLVED: Merged facts into {old_fact_id}.")

    async def close(self):

        self._stop_event.set()
        if self.client:
            await self._call('close')

    async def semantic_search(self, embedding: List[float], agent_id: Optional[str] = None, limit: int = 3) -> List[Dict[str, Any]]:
        """Subjective semantic search that retrieves facts based on agent's beliefs.
        
        Queries from:
        - Agent's subjective beliefs: agent:{agent_id}->BELIEVES->fact
        - Universal facts: agent:system->BELIEVES->fact
        
        Filters out faded memories (strength < 0.3).
        """
        if not agent_id:
            agent_id = "system"
        
        agent_name = agent_id.lower().replace(" ", "_")
        
        query = f"""
        SELECT * FROM (
            SELECT 
                fl.id AS fact_id,
                fl.content AS content,
                fl.embedding AS embedding,
                BELIEVES.confidence AS confidence,
                BELIEVES.strength AS strength,
                BELIEVES.last_accessed AS last_accessed,
                BELIEVES<-subject BELIEVER
            FROM subject:`{agent_name}`<-BELIEVES->fact fl
            WHERE fl.embedding <|{limit}|> $embedding AND BELIEVES.strength >= 0.3
        ) UNION (
            SELECT 
                fl.id AS fact_id,
                fl.content AS content,
                fl.embedding AS embedding,
                BELIEVES.confidence AS confidence,
                BELIEVES.strength AS strength,
                BELIEVES.last_accessed AS last_accessed,
                BELIEVES<-subject BELIEVER
            FROM subject:`system`<-BELIEVES->fact fl
            WHERE fl.embedding <|{limit}|> $embedding AND BELIEVES.strength >= 0.3
        )
        ORDER BY confidence DESC
        LIMIT {limit}
        """
        
        try:
            result = await self._call('query', query, {"embedding": embedding})
            if result and isinstance(result, list) and len(result) > 0:
                return result[0].get("result", [])
            return []
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    async def semantic_search_user(self, embedding: List[float], user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Subjective semantic search that retrieves facts specific to a user.
        
        Queries from:
        - User-specific facts: fact WHERE user_id = $user_id
        - Universal facts: fact WHERE user_id = null (system-wide knowledge)
        
        Filters out faded memories (strength < 0.3).
        """
        user_id_lower = user_id.lower().replace(" ", "_")
        
        query = f"""
        SELECT * FROM (
            SELECT 
                fl.id AS fact_id,
                fl.content AS content,
                fl.embedding AS embedding,
                fl.user_id AS user_id,
                fl.user_name AS user_name,
                BELIEVES.confidence AS confidence,
                BELIEVES.strength AS strength,
                BELIEVES.last_accessed AS last_accessed,
                BELIEVES<-subject BELIEVER
            FROM subject:`system`<-BELIEVES->fact fl
            WHERE fl.embedding <|{limit}|> $embedding AND BELIEVES.strength >= 0.3 AND fl.user_id = '{user_id_lower}'
        ) UNION (
            SELECT 
                fl.id AS fact_id,
                fl.content AS content,
                fl.embedding AS embedding,
                fl.user_id AS user_id,
                fl.user_name AS user_name,
                BELIEVES.confidence AS confidence,
                BELIEVES.strength AS strength,
                BELIEVES.last_accessed AS last_accessed,
                BELIEVES<-subject BELIEVER
            FROM subject:`system`<-BELIEVES->fact fl
            WHERE fl.embedding <|{limit}|> $embedding AND BELIEVES.strength >= 0.3 AND fl.user_id IS NONE
        )
        ORDER BY confidence DESC
        LIMIT {limit}
        """
        
        try:
            result = await self._call('query', query, {"embedding": embedding})
            if result and isinstance(result, list) and len(result) > 0:
                return result[0].get("result", [])
            return []
        except Exception as e:
            logger.error(f"User semantic search failed: {e}")
            return []

    async def semantic_search_universal(self, embedding: List[float], limit: int = 3) -> List[Dict[str, Any]]:
        """Semantic search for universal memories (not tied to any user).
        
        Retrieves system-wide knowledge that applies to all users.
        """
        query = f"""
        SELECT 
            fl.id AS fact_id,
            fl.content AS content,
            fl.embedding AS embedding,
            fl.user_id AS user_id,
            fl.user_name AS user_name,
            BELIEVES.confidence AS confidence,
            BELIEVES.strength AS strength,
            BELIEVES.last_accessed AS last_accessed,
            BELIEVES<-subject BELIEVER
        FROM subject:`system`<-BELIEVES->fact fl
        WHERE fl.embedding <|{limit}|> $embedding AND BELIEVES.strength >= 0.3 AND fl.user_id IS NONE
        ORDER BY confidence DESC
        LIMIT {limit}
        """
        
        try:
            result = await self._call('query', query, {"embedding": embedding})
            if result and isinstance(result, list) and len(result) > 0:
                return result[0].get("result", [])
            return []
        except Exception as e:
            logger.error(f"Universal semantic search failed: {e}")
            return []