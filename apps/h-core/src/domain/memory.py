import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from src.domain.memory_force import MemoryForce, MemoryForceEvaluator
from src.infrastructure.llm import LlmClient
from src.infrastructure.redis import RedisClient
from src.infrastructure.surrealdb import SurrealDbClient
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender

logger = logging.getLogger(__name__)


class ConflictResolver:
    RESOLUTION_PROMPT = """
    You are the Memory Conflict Resolver for hAIrem.
    Fact A (Existing): "{old_fact}" | force={old_force:.2f} | age={old_age_days}d
    Fact B (New): "{new_fact}" | force={new_force:.2f} | age=0d

    Are these facts contradictory?
    - If YES: synthesize a resolution. Higher force takes precedence.
    - If NO: return "COMPLEMENTARY".

    Output JSON:
    {{
      "is_conflict": true/false,
      "resolution": "Synthesized fact or COMPLEMENTARY",
      "action": "OVERRIDE" or "MERGE",
      "winner": "A" or "B" or "MERGE",
      "confidence": 0.0-1.0
    }}
    """

    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    async def resolve(
        self,
        old_fact: str,
        new_fact: str,
        old_force: float = 0.5,
        new_force: float = 0.5,
        old_age_days: float = 0.0,
    ) -> dict[str, Any]:
        prompt = self.RESOLUTION_PROMPT.format(
            old_fact=old_fact,
            new_fact=new_fact,
            old_force=old_force,
            new_force=new_force,
            old_age_days=old_age_days,
        )
        response = await self.llm.get_completion([{"role": "system", "content": prompt}], stream=False)

        clean_json = response.strip()  # type: ignore
        if clean_json.startswith("```json"):
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif clean_json.startswith("```"):
            clean_json = clean_json.split("```")[1].split("```")[0].strip()

        return json.loads(clean_json)


class MemoryConsolidator:
    """Service to periodically consolidate conversation history into atomic facts."""

    CONSOLIDATION_PROMPT = """
    You are the Cognitive Consolidation service for hAIrem.
    Your task is to analyze the following conversation chunk and extract 'Atomic Facts', 'Causal Links', and 'Concepts'.
    
    Guidelines:
    - Extract short, declarative facts (e.g., "User likes green tea", "User is a software engineer").
    - Extract causal links if one event led to another (e.g., "User is sad BECAUSE it is raining").
    - Identify key concepts mentioned (e.g., "Quantum Physics", "Veganism").
    - Focus on preferences, recurring topics, personality traits, and important life events.
    - For each item, assign a confidence score (0.0 to 1.0). 
    
    Output MUST be a JSON object with three lists:
    {{
      "facts": [
        {{"fact": "...", "subject": "user", "agent": "AgentName", "confidence": 0.9}}
      ],
      "causal_links": [
        {{"cause": "fact_content_A", "effect": "fact_content_B", "confidence": 0.8}}
      ],
      "concepts": [
        {{"name": "ConceptName", "description": "...", "confidence": 0.9}}
      ]
    }}
    
    Conversation Chunk:
    ---
    {conversation}
    ---
    """

    def __init__(
        self,
        surreal_client: SurrealDbClient,
        llm_client: LlmClient,
        redis_client: RedisClient,
        session_id: Optional[str] = None,
    ):
        self.surreal = surreal_client
        self.llm = llm_client
        self.redis = redis_client
        self.resolver = ConflictResolver(llm_client)
        self.session_id = session_id
        self._force_evaluator = MemoryForceEvaluator()

    async def consolidate(self, limit: int = 20) -> int:
        logger.info("Starting Cognitive Consolidation cycle...")

        messages = await self.surreal.get_unprocessed_messages(limit=limit)
        if not messages:
            logger.info("No new messages to consolidate.")
            return 0

        convo_lines = []
        msg_ids = []
        user_ids_in_batch: list[str] = []
        seen_user_ids: set[str] = set()
        for m in messages:
            sender = m.get("sender", {}).get("agent_id", "unknown")
            content = m.get("payload", {}).get("content", "")
            if isinstance(content, dict):
                content = content.get("content") or json.dumps(content)
            convo_lines.append(f"{sender}: {content}")
            msg_ids.append((m.get("id") or "").split(":")[-1].strip("`"))

            payload = m.get("payload", {})
            if isinstance(payload, dict):
                msg_user_id = payload.get("user_id") or payload.get("session_user_id")
                if msg_user_id and msg_user_id not in seen_user_ids:
                    user_ids_in_batch.append(msg_user_id)
                    seen_user_ids.add(msg_user_id)

        primary_user_id = user_ids_in_batch[0] if user_ids_in_batch else None
        conversation_text = "\n".join(convo_lines)

        prompt = self.CONSOLIDATION_PROMPT.format(conversation=conversation_text)
        try:
            response = await self.llm.get_completion([{"role": "system", "content": prompt}], stream=False)

            clean_json = response.strip()  # type: ignore
            if clean_json.startswith("```json"):
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif clean_json.startswith("```"):
                clean_json = clean_json.split("```")[1].split("```")[0].strip()

            data = json.loads(clean_json)
            extracted_facts = data.get("facts", [])
            causal_links = data.get("causal_links", [])
            concepts = data.get("concepts", [])
            logger.info(f"Extracted {len(extracted_facts)} facts from {len(messages)} messages.")

            for fact_data in extracted_facts:
                fact_data["source_ids"] = msg_ids
                if fact_data.get("subject") == "user" and not fact_data.get("agent"):
                    fact_data["agent"] = "system"

                if primary_user_id:
                    fact_data["user_id"] = primary_user_id

                embedding = await self.llm.get_embedding(fact_data["fact"])
                fact_data["embedding"] = embedding

                agent_id = fact_data.get("agent", "system")
                force = self._force_evaluator.evaluate(fact_data["fact"], embedding, agent_id)

                conflicts = await self.surreal.semantic_search(embedding, limit=1)
                if conflicts and conflicts[0].get("score", 0) > 0.85:
                    old_fact_rec = conflicts[0]
                    old_force_score = old_fact_rec.get("force_score", 0.5)
                    old_last_reinforced = old_fact_rec.get("last_reinforced")
                    old_age_days = 0.0
                    if old_last_reinforced:
                        try:
                            ts = datetime.fromisoformat(str(old_last_reinforced).replace("Z", "+00:00"))
                            old_age_days = (datetime.now(timezone.utc) - ts).days
                        except (ValueError, TypeError):
                            pass
                    resolution = await self.resolver.resolve(
                        old_fact_rec["content"],
                        fact_data["fact"],
                        old_force=old_force_score,
                        new_force=force.score,
                        old_age_days=old_age_days,
                    )
                    if resolution.get("is_conflict"):
                        logger.info(
                            f"CONFLICT detected: {old_fact_rec['content']} vs {fact_data['fact']}."
                            f" Action: {resolution['action']}"
                        )
                        await self.surreal.merge_or_override_fact(old_fact_rec["id"], fact_data, resolution)
                        continue

                fact_id = await self.surreal.insert_graph_memory(fact_data, force=force)
                if fact_id and self.session_id:
                    await self.surreal.link_fact_to_episode(fact_id, self.session_id)

            # 4b. Store Causal Links
            for link in causal_links:
                await self.surreal.insert_causal_link(link["cause"], link["effect"], link.get("confidence", 1.0))

            # 4c. Store Concepts
            for concept in concepts:
                await self.surreal.insert_concept(concept["name"], concept.get("description", ""))

            # Mark all messages in this batch as processed
            await self.surreal.mark_as_processed(msg_ids)

            # 5. Notify system
            learned_count = len(extracted_facts) + len(causal_links) + len(concepts)
            summary = f"Sleep Cycle complete: Learned {learned_count} cognitive elements from {len(messages)} messages."
            await self._broadcast_log(summary)

            return learned_count

        except Exception as e:
            logger.error(f"Consolidation failed: {e}")
            await self._broadcast_log(f"Consolidation failed: {e}", level="error")
            return 0

    async def apply_decay(self, decay_rate: float | None = None, threshold: float = 0.1):
        """Manually trigger memory decay."""
        if decay_rate is None:
            # Default to 0.9 reduction (10% decay) if not in environment
            import os

            decay_rate = float(os.getenv("DECAY_RATE", "0.9"))

        logger.info(f"Applying memory decay (rate={decay_rate}, threshold={threshold})...")
        removed_count = await self.surreal.apply_decay_to_all_memories(decay_rate, threshold)

        # Also clean up orphaned fact nodes
        orphaned_count = await self.surreal.cleanup_orphaned_facts()

        await self._broadcast_log(
            f"Memory decay applied (rate={decay_rate}). {removed_count} memories faded, {orphaned_count} orphaned facts cleaned."
        )

    async def _broadcast_log(self, content: str, level: str = "info"):
        """Utility to send a system log message."""
        import os

        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        level_map = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
        current_level = level_map.get(level.upper(), 20)
        min_level = level_map.get(log_level, 20)

        if current_level < min_level:
            return

        msg = HLinkMessage(
            type=MessageType.SYSTEM_LOG,
            sender=Sender(agent_id="system", role="orchestrator"),
            recipient=Recipient(target="broadcast"),
            payload=Payload(content=f"[{level.upper()}] {content}"),
        )
        await self.redis.publish("broadcast", msg)

    async def generate_backstory(self, agent_name: str, agent_role: str):
        """
        FR18.1: Backstory Generator (Epic 18).
        Generates consistent past memories for an agent at startup.
        """
        logger.info(f"MEMORY: Generating backstory for {agent_name}...")

        prompt = f"""
        You are the Backstory Generator for hAIrem.
        Create 5 short, atomic past memories for an AI character named {agent_name} (Role: {agent_role}).
        These memories should be consistent with their personality and role.
        
        Output format: JSON list of facts.
        Example: ["I remember helping the user with their first python script", "I feel a strong bond with the other crew members"]
        """

        try:
            response = await self.llm.get_completion([{"role": "system", "content": prompt}], stream=False)
            clean_json = str(response).strip() if isinstance(response, str) else ""
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()

            memories = json.loads(clean_json)
            for m in memories:
                fact_data = {
                    "fact": m,
                    "subject": agent_name,
                    "agent": agent_name,
                    "confidence": 1.0,
                    "permanent": True,  # Backstory doesn't decay
                }
                embedding = await self.llm.get_embedding(m)
                fact_data["embedding"] = embedding
                await self.surreal.insert_graph_memory(fact_data)
            logger.info(f"MEMORY: {agent_name} now has a past.")
        except Exception as e:
            logger.error(f"Backstory generation failed for {agent_name}: {e}")
