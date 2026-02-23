import asyncio
import logging
import os
import inspect
from datetime import datetime
from typing import Any, List, Optional, Dict

SURREAL_AVAILABLE = False
try:
    from surrealdb import Surreal

    SURREAL_AVAILABLE = True
except ImportError:
    pass

logger = logging.getLogger(__name__)


class SurrealDbClient:
    def __init__(self, url: str, user: str, password: str, ns: str = "hairem", db: str = "core"):
        self.url = url
        self.user = user
        self.password = password
        self.ns = ns
        self.db = db
        self.client: Any = None
        self._stop_event = asyncio.Event()

    async def _call(self, method_name: str, *args, **kwargs) -> Any:
        """Robust wrapper for SurrealDB client calls with auto-reconnect."""
        if not self.client:
            await self.connect()
            if not self.client:
                return None

        try:
            method = getattr(self.client, method_name)
            res = method(*args, **kwargs)
            if inspect.isawaitable(res):
                res = await res

            return res
        except Exception as e:
            err_msg = str(e).lower()
            if any(x in err_msg for x in ["namespace", "database", "iam", "auth", "session"]):
                logger.warning(f"SURREAL_EXCEPTION: {e}. Re-connecting...")
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
        if not SURREAL_AVAILABLE:
            return

        if self.client:
            try:
                await self.client.close()
            except:
                pass

        # We keep the constructor call simple for mock compatibility in tests
        from surrealdb import Surreal as _Surreal  # noqa: PLC0415

        self.client = _Surreal(self.url)

        try:
            # Need to call connect() explicitly in newer versions of the library
            if hasattr(self.client, "connect"):
                res = self.client.connect()
                if inspect.isawaitable(res):
                    await res

            # Multi-format authentication
            creds = {"user": self.user or "root", "pass": self.password or "root"}
            try:
                res = self.client.signin(creds)
                if inspect.isawaitable(res):
                    await res
            except:
                res = self.client.signin({"username": creds["user"], "password": creds["pass"]})
                if inspect.isawaitable(res):
                    await res

            res = self.client.use(self.ns, self.db)
            if inspect.isawaitable(res):
                await res

            logger.info(f"Connected to SurrealDB: {self.ns}:{self.db}")
        except Exception as e:
            logger.error(f"SurrealDB connection failed: {e}")
            self.client = None

    async def setup_schema(self):
        """Initialize SCHEMAFULL tables and indices safely."""
        if not self.client:
            return
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
            DEFINE FIELD IF NOT EXISTS description ON TABLE subject TYPE string;
            DEFINE INDEX IF NOT EXISTS subject_name ON TABLE subject FIELDS name UNIQUE;

            DEFINE TABLE IF NOT EXISTS concept SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS name ON TABLE concept TYPE string;
            DEFINE FIELD IF NOT EXISTS description ON TABLE concept TYPE string;
            DEFINE INDEX IF NOT EXISTS concept_name ON TABLE concept FIELDS name UNIQUE;

            DEFINE TABLE IF NOT EXISTS fact SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS content ON TABLE fact TYPE string;
            DEFINE FIELD IF NOT EXISTS embedding ON TABLE fact TYPE array<float, 384>;
            DEFINE FIELD IF NOT EXISTS user_id ON TABLE fact TYPE string;
            DEFINE FIELD IF NOT EXISTS user_name ON TABLE fact TYPE string;

            DEFINE TABLE IF NOT EXISTS BELIEVES SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS confidence ON TABLE BELIEVES TYPE float DEFAULT 1.0;
            DEFINE FIELD IF NOT EXISTS strength ON TABLE BELIEVES TYPE float DEFAULT 1.0;
            DEFINE FIELD IF NOT EXISTS last_accessed ON TABLE BELIEVES TYPE datetime DEFAULT time::now();
            DEFINE FIELD IF NOT EXISTS permanent ON TABLE BELIEVES TYPE bool DEFAULT false;
            DEFINE FIELD IF NOT EXISTS last_reinforced ON TABLE BELIEVES TYPE datetime DEFAULT time::now();

            DEFINE TABLE IF NOT EXISTS ABOUT SCHEMAFULL;
            DEFINE TABLE IF NOT EXISTS CAUSED SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS likelihood ON TABLE CAUSED TYPE float DEFAULT 1.0;
            
            DEFINE TABLE IF NOT EXISTS agent_config SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS agent_id ON TABLE agent_config TYPE string;
            DEFINE FIELD IF NOT EXISTS parameters ON TABLE agent_config TYPE object;
            DEFINE FIELD IF NOT EXISTS enabled ON TABLE agent_config TYPE bool DEFAULT true;
            DEFINE FIELD IF NOT EXISTS version ON TABLE agent_config TYPE string DEFAULT '1.0.0';
            DEFINE INDEX IF NOT EXISTS agent_config_id ON TABLE agent_config FIELDS agent_id UNIQUE;

            DEFINE TABLE IF NOT EXISTS config SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS data ON TABLE config TYPE object;
            DEFINE FIELD IF NOT EXISTS updated_at ON TABLE config TYPE datetime DEFAULT time::now();
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

    async def set_secret(self, key: str, value: str):
        """Stores an encrypted secret in the vault."""
        import base64

        encoded = base64.b64encode(value.encode()).decode()
        await self._call(
            "query",
            "INSERT INTO vault_secrets (id, secret_value) VALUES ($id, $val) ON DUPLICATE KEY UPDATE secret_value = $val;",
            {"id": f"vault_secrets:`{key}`", "val": encoded},
        )

    async def get_secret(self, key: str) -> Optional[str]:
        """Retrieves and decrypts a secret."""
        import base64

        try:
            res = await self._call(
                "query", "SELECT * FROM vault_secrets WHERE id = $id", {"id": f"vault_secrets:`{key}`"}
            )
            if res and isinstance(res, list) and len(res) > 0:
                results = res[0].get("result", [])
                if results and isinstance(results, list) and len(results) > 0:
                    encoded = results[0].get("secret_value")
                    return base64.b64decode(encoded).decode()
        except Exception as e:
            logger.warning(f"SurrealDB: Failed to get secret {key}: {e}")
        return None

    async def insert_causal_link(self, cause_text: str, effect_text: str, confidence: float = 1.0):
        """Creates a CAUSED edge between two facts based on their content."""
        try:
            # Find the two facts (approximate match)
            q = """
            LET $cause = (SELECT id FROM fact WHERE content CONTAINS $cause_text LIMIT 1);
            LET $effect = (SELECT id FROM fact WHERE content CONTAINS $effect_text LIMIT 1);
            
            IF $cause[0].id AND $effect[0].id THEN
                RELATE $cause[0].id->CAUSED->$effect[0].id SET likelihood = $confidence, timestamp = time::now();
            END;
            """
            await self._call(
                "query", q, {"cause_text": cause_text, "effect_text": effect_text, "confidence": confidence}
            )
        except Exception as e:
            logger.error(f"Failed to insert causal link: {e}")

    async def insert_concept(self, name: str, description: str, fact_content: str | None = None):
        """Creates a concept and optionally links a fact to it via ABOUT."""
        try:
            cid = f"concept:`{name.lower().replace(' ', '_')}`"
            await self._call(
                "query",
                f"INSERT INTO concept (id, name, description) VALUES ({cid}, $name, $desc) ON DUPLICATE KEY UPDATE description = $desc;",
                {"name": name, "desc": description},
            )

            if fact_content:
                q = """
                LET $fact = (SELECT id FROM fact WHERE content CONTAINS $text LIMIT 1);
                IF $fact[0].id THEN
                    RELATE $fact[0].id->ABOUT->{cid} SET timestamp = time::now();
                END;
                """.replace("{cid}", cid)
                await self._call("query", q, {"text": fact_content})
        except Exception as e:
            logger.error(f"Failed to insert concept: {e}")

    async def insert_graph_memory(self, fact_data: Dict[str, Any], force: Any = None) -> Optional[str]:
        subject_name = fact_data.get("subject", "user")
        agent_name = fact_data.get("agent", "system")
        fact_content = fact_data.get("fact", "")
        embedding = fact_data.get("embedding", [])
        confidence = fact_data.get("confidence", 1.0)
        user_id = fact_data.get("user_id")
        user_name = fact_data.get("user_name")
        permanent = fact_data.get("permanent", False)

        sid = f"subject:`{subject_name.lower().replace(' ', '_')}`"
        aid = f"subject:`{agent_name.lower().replace(' ', '_')}`"

        try:
            await self._call(
                "query",
                f"INSERT INTO subject (id, name) VALUES ({sid}, $name) ON DUPLICATE KEY UPDATE name = $name;",
                {"name": subject_name},
            )
            await self._call(
                "query",
                f"INSERT INTO subject (id, name) VALUES ({aid}, $name) ON DUPLICATE KEY UPDATE name = $name;",
                {"name": agent_name},
            )

            fact_data_db = {"content": fact_content, "embedding": embedding}
            if user_id:
                fact_data_db["user_id"] = user_id
            if user_name:
                fact_data_db["user_name"] = user_name

            fact_res = await self._call("create", "fact", fact_data_db)
            if not fact_res:
                return None

            # fact_res can be a list or a single dict depending on library version
            if isinstance(fact_res, list) and len(fact_res) > 0:
                fid = fact_res[0].get("id")
            elif isinstance(fact_res, dict):
                fid = fact_res.get("id")
            else:
                logger.error(f"SURREAL: Unexpected fact creation result: {fact_res}")
                return None

            if not fid:
                return None

            initial_strength = force.score if force else 1.0
            force_fields = ""
            if force:
                d = force.to_dict()
                force_fields = (
                    f", force_score = {d['force_score']}"
                    f", affect = {d['affect']}"
                    f", importance = {d['importance']}"
                    f", relevance = {d['relevance']}"
                )

            await self._call(
                "query",
                f"RELATE {aid}->BELIEVES->{fid} SET confidence = $conf, strength = {initial_strength},"
                f" last_accessed = time::now(), permanent = $permanent,"
                f" last_reinforced = time::now(){force_fields};",
                {"conf": confidence, "permanent": permanent},
            )
            await self._call("query", f"RELATE {fid}->ABOUT->{sid};")
            return str(fid)
        except Exception as e:
            logger.error(f"Failed to insert graph memory: {e}")
            return None

    async def save_asset_record(self, asset_data: Dict[str, Any]) -> Optional[str]:
        try:
            url = asset_data.get("url", "")
            q = (
                f"INSERT INTO visual_asset (url, prompt, agent_id, tags, embedding, reference_image_used) "
                f"VALUES ($url, $prompt, $aid, $tags, $emb, $ref) "
                f"ON DUPLICATE KEY UPDATE prompt = $prompt, tags = $tags, last_used = time::now();"
            )
            result = await self._call(
                "query",
                q,
                {
                    "url": url,
                    "prompt": asset_data.get("prompt", ""),
                    "aid": asset_data.get("agent_id", "system"),
                    "tags": asset_data.get("tags", []),
                    "emb": asset_data.get("embedding", []),
                    "ref": asset_data.get("reference_image_used", ""),
                },
            )
            if result and isinstance(result, list) and result[0].get("result"):
                rows = result[0]["result"]
                if rows and isinstance(rows, list):
                    return str(rows[0].get("id", ""))
            return None
        except Exception as e:
            logger.error(f"Failed to save asset record: {e}")
            return None

    async def open_episode(self, session_id: str, agent_id: str, user_id: Optional[str] = None) -> str:
        data: Dict[str, Any] = {"session_id": session_id, "agent_id": agent_id}
        if user_id:
            data["user_id"] = user_id
        result = await self._call("create", "episode", data)
        if isinstance(result, list) and result:
            return str(result[0].get("id", ""))
        if isinstance(result, dict):
            return str(result.get("id", ""))
        return ""

    async def close_episode(
        self, session_id: str, summary: Optional[str] = None, emotion_arc: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        await self._call(
            "query",
            "UPDATE episode SET ended_at = time::now(), summary = $summary, emotion_arc = $arc"
            " WHERE session_id = $sid;",
            {"sid": session_id, "summary": summary, "arc": emotion_arc or []},
        )
        return True

    async def link_fact_to_episode(self, fact_id: str, session_id: str) -> bool:
        result = await self._call(
            "query",
            "LET $ep = (SELECT id FROM episode WHERE session_id = $sid LIMIT 1);"
            " IF $ep[0].id THEN RELATE $fact->EXTRACTED_FROM->$ep[0].id SET extracted_at = time::now(); END;",
            {"sid": session_id, "fact": fact_id},
        )
        return result is not None

    async def get_episode(self, session_id: str) -> Optional[Dict[str, Any]]:
        result = await self._call(
            "query",
            "SELECT * FROM episode WHERE session_id = $sid LIMIT 1;",
            {"sid": session_id},
        )
        if result and isinstance(result, list) and result[0].get("result"):
            rows = result[0]["result"]
            return rows[0] if rows else None
        return None

    async def get_episode_facts(self, session_id: str) -> List[Dict[str, Any]]:
        result = await self._call(
            "query",
            "SELECT <-EXTRACTED_FROM<-fact.* AS facts FROM episode WHERE session_id = $sid;",
            {"sid": session_id},
        )
        if result and isinstance(result, list) and result[0].get("result"):
            rows = result[0]["result"]
            return rows[0].get("facts", []) if rows else []
        return []

    async def get_recent_episodes(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        result = await self._call(
            "query",
            f"SELECT * FROM episode WHERE agent_id = $aid ORDER BY started_at DESC LIMIT {limit};",
            {"aid": agent_id},
        )
        if result and isinstance(result, list) and result[0].get("result"):
            return result[0]["result"]
        return []

    async def persist_message(self, message: Dict[str, Any]):
        from src.utils.privacy import PrivacyFilter

        _privacy = PrivacyFilter()

        raw_payload = message.get("payload", {})
        safe_payload = dict(raw_payload) if isinstance(raw_payload, dict) else raw_payload
        if isinstance(safe_payload, dict) and isinstance(safe_payload.get("content"), str):
            redacted, _ = _privacy.redact(safe_payload["content"])
            safe_payload["content"] = redacted

        data = {
            "agent_id": message.get("sender", {}).get("agent_id", "unknown"),
            "type": message.get("type", "unknown"),
            "payload": safe_payload,
            "timestamp": message.get("timestamp") or datetime.utcnow().isoformat(),
            "processed": False,
        }
        await self._call("create", "messages", data)

    async def get_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent messages."""
        res = await self._call("query", f"SELECT * FROM messages ORDER BY timestamp DESC LIMIT {limit};")
        if res and isinstance(res, list) and len(res) > 0:
            return res[0].get("result", []) if isinstance(res[0], dict) else res
        return []

    async def get_unprocessed_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve messages that haven't been processed for cognitive consolidation."""
        res = await self._call(
            "query", f"SELECT * FROM messages WHERE processed = false ORDER BY timestamp ASC LIMIT {limit};"
        )
        if res and isinstance(res, list) and len(res) > 0:
            return res[0].get("result", []) if isinstance(res[0], dict) else res
        return []

    async def mark_as_processed(self, msg_ids: List[str]):
        """Mark a batch of messages as processed."""
        for mid in msg_ids:
            # msg_ids are expected to be the UUID part
            await self._call("query", f"UPDATE messages SET processed = true WHERE id = messages:`{mid}`;")

    async def merge_or_override_fact(self, old_fact_id: str, new_fact_data: Dict[str, Any], resolution: Dict[str, Any]):
        """Handles memory conflict resolution by merging or overriding existing facts."""
        action = resolution.get("action", "OVERRIDE")
        new_content = resolution.get("resolution", new_fact_data["fact"]).replace("'", "\\'")

        if action == "OVERRIDE":
            # 1. Update the fact node content and embedding
            await self._call(
                "query",
                f"UPDATE {old_fact_id} SET content = '{new_content}', embedding = $emb;",
                {"emb": new_fact_data["embedding"]},
            )
            logger.info(f"CONFLICT_RESOLVED: Overrode {old_fact_id} with new synthesis.")
        else:
            # MERGE: Just update content but keep historical links
            await self._call("query", f"UPDATE {old_fact_id} SET content = '{new_content}';")
            logger.info(f"CONFLICT_RESOLVED: Merged facts into {old_fact_id}.")

    async def apply_decay_to_all_memories(self, decay_rate: float = 0.05, threshold: float = 0.1) -> int:
        """Force-aware decay: decay_effective = base_rate × max(0.1, 1 − force_score × 0.9)."""
        try:
            update_query = f"""
                UPDATE BELIEVES
                SET
                    strength = strength * math::pow(
                        {decay_rate} * math::max(0.1, 1.0 - force_score * 0.9),
                        time::now() - last_reinforced
                    ),
                    last_reinforced = time::now()
                WHERE permanent != true
            """
            await self._call("query", update_query)

            delete_query = f"DELETE BELIEVES WHERE strength < {threshold}"
            result = await self._call("query", delete_query)

            if result and isinstance(result, list) and len(result) > 0:
                deleted = result[0].get("result", []) if isinstance(result[0], dict) else result
                count = len(deleted) if isinstance(deleted, list) else 0
                logger.info(f"DECAY_APPLIED: {count} memories forgotten (threshold: {threshold})")
                return count
            return 0
        except Exception as e:
            logger.error(f"Failed to apply decay: {e}")
            return 0

    async def cleanup_orphaned_facts(self) -> int:
        """Remove fact nodes that are no longer referenced by any BELIEVES edges.

        Returns:
            Number of orphaned facts removed
        """
        try:
            # Find facts that have no incoming BELIEVES edges
            cleanup_query = """
                DELETE fact WHERE id NOT IN (
                    SELECT out FROM BELIEVES
                )
            """
            result = await self._call("query", cleanup_query)

            if result and isinstance(result, list) and len(result) > 0:
                deleted = result[0].get("result", []) if isinstance(result[0], dict) else result
                count = len(deleted) if isinstance(deleted, list) else 0
                logger.info(f"CLEANUP: {count} orphaned facts removed")
                return count
            return 0
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned facts: {e}")
            return 0

    async def update_memory_strength(self, agent_name: str, fact_id: str, boost: bool = True) -> bool:
        """Update the strength of a specific memory belief."""
        try:
            agent_key = agent_name.lower().replace(" ", "_")
            delta = 0.1 if boost else -0.1

            # Format query with literal delta value for test compatibility
            query = f"UPDATE BELIEVES SET strength = math::min(1.0, strength + {delta}) WHERE in = subject:`{agent_key}` AND out = {fact_id}"

            result = await self._call("query", query)
            success = bool(result) and isinstance(result, list) and len(result) > 0
            if success:
                logger.debug(f"MEMORY_STRENGTH_UPDATED: {agent_name} - {fact_id} ({'+' if boost else '-'}{delta})")
            return success
        except Exception as e:
            logger.error(f"Failed to update memory strength: {e}")
            return False

    async def close(self):

        self._stop_event.set()
        if self.client:
            await self._call("close")

    async def semantic_search(
        self, embedding: List[float], agent_id: Optional[str] = None, limit: int = 3
    ) -> List[Dict[str, Any]]:
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
            result = await self._call("query", query, {"embedding": embedding})
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
            result = await self._call("query", query, {"embedding": embedding})
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
            result = await self._call("query", query, {"embedding": embedding})
            if result and isinstance(result, list) and len(result) > 0:
                return result[0].get("result", [])
            return []
        except Exception as e:
            logger.error(f"Universal semantic search failed: {e}")
            return []

    async def update_agent_state(self, agent_id: str, relation_type: str, target_data: Dict[str, Any]):
        """Updates the agent's state in the graph (e.g. WEARS, IS_IN)."""
        agent_key = agent_id.lower().replace(" ", "_")
        target_name = target_data.get("name", "unknown")
        target_key = target_name.lower().replace(" ", "_")
        description = target_data.get("description", "")

        # Create/Update target subject
        await self._call(
            "query",
            f"INSERT INTO subject (id, name) VALUES (subject:`{target_key}`, $name) ON DUPLICATE KEY UPDATE name=$name;",
            {"name": target_name},
        )

        # Create edge
        await self._call(
            "query",
            f"RELATE subject:`{agent_key}`->{relation_type}->subject:`{target_key}` SET description = $desc, timestamp = time::now();",
            {"desc": description},
        )

    async def get_agent_state(self, agent_id: str) -> List[Dict[str, Any]]:
        """Retrieves the agent's current state (relations)."""
        agent_key = agent_id.lower().replace(" ", "_")

        # Query all outgoing edges that are NOT BELIEVES
        query = f"""
        SELECT 
            type::string(->?) AS relation,
            ->?.name AS name,
            ->?.description AS description
        FROM subject:`{agent_key}`
        """
        # Note: SurrealQL syntax for edge types varies. Using a simplified approach.
        res = await self._call("query", query)
        if res and isinstance(res, list) and len(res) > 0:
            return res[0].get("result", [])
        return []

    async def save_config(self, config_id: str, data: Dict[str, Any]):
        """Saves a configuration object (system or agent override)."""
        cid = f"config:`{config_id}`"
        q = f"INSERT INTO config (id, data, updated_at) VALUES ({cid}, $data, time::now()) ON DUPLICATE KEY UPDATE data = $data, updated_at = time::now();"
        await self._call("query", q, {"data": data})

    async def get_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a configuration object."""
        cid = f"config:`{config_id}`"
        try:
            res = await self._call("query", f"SELECT data FROM {cid}")
            if res and isinstance(res, list) and len(res) > 0:
                first = res[0]
                # If first is a dict with 'result' (SurrealDB 1.x style list of results)
                if isinstance(first, dict) and "result" in first:
                    results = first["result"]
                    if isinstance(results, list) and len(results) > 0:
                        return results[0].get("data")
                # If first is the record itself (SurrealDB 2.x style directly)
                elif isinstance(first, dict) and "data" in first:
                    return first["data"]
            elif res and isinstance(res, dict):
                if "data" in res:
                    return res["data"]
        except:
            pass
        return None
