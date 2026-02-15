import json
import logging
from typing import Any

from src.infrastructure.llm import LlmClient
from src.infrastructure.redis import RedisClient
from src.infrastructure.surrealdb import SurrealDbClient
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender

logger = logging.getLogger(__name__)

class ConflictResolver:
    """Handles resolution of contradictory facts using LLM synthesis."""
    
    RESOLUTION_PROMPT = """
    You are the Memory Conflict Resolver for hAIrem.
    You have two facts that might be contradictory.
    
    Fact A (Existing): "{old_fact}"
    Fact B (New): "{new_fact}"
    
    Are these facts contradictory? 
    - If YES, provide a synthesized fact that resolves the contradiction.
    - If NO (they are complementary or unrelated), return "COMPLEMENTARY".
    
    Output format: JSON
    {{
      "is_conflict": true/false,
      "resolution": "Synthesized fact or 'COMPLEMENTARY'",
      "action": "OVERRIDE" (if new replaces old) or "MERGE" (if both integrated)
    }}
    """

    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    async def resolve(self, old_fact: str, new_fact: str) -> dict[str, Any]:
        prompt = self.RESOLUTION_PROMPT.format(old_fact=old_fact, new_fact=new_fact)
        response = await self.llm.get_completion([{"role": "system", "content": prompt}], stream=False)
        
        # Clean response
        clean_json = response.strip() # type: ignore
        if clean_json.startswith("```json"):
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif clean_json.startswith("```"):
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
        return json.loads(clean_json)

class MemoryConsolidator:
    """Service to periodically consolidate conversation history into atomic facts."""

    CONSOLIDATION_PROMPT = """
    You are the Cognitive Consolidation service for hAIrem.
    Your task is to analyze the following conversation chunk and extract 'Atomic Facts' about the user or the environment.
    
    Guidelines:
    - Extract short, declarative facts (e.g., "User likes green tea", "User is a software engineer").
    - Focus on preferences, recurring topics, personality traits, and important life events.
    - Ignore technical logs or system status updates unless they contain user context.
    - For each fact, assign a confidence score (0.0 to 1.0). 
    
    Output MUST be a JSON list of objects:
    [
      {{"fact": "...", "subject": "user", "agent": "AgentName", "confidence": 0.9}},
      ...
    ]
    
    Conversation Chunk:
    ---
    {conversation}
    ---
    """

    def __init__(self, surreal_client: SurrealDbClient, llm_client: LlmClient, redis_client: RedisClient):
        self.surreal = surreal_client
        self.llm = llm_client
        self.redis = redis_client
        self.resolver = ConflictResolver(llm_client)

    async def consolidate(self, limit: int = 20) -> int:
        """Run a consolidation cycle."""
        logger.info("Starting Cognitive Consolidation cycle...")
        
        # 1. Fetch unprocessed messages
        messages = await self.surreal.get_unprocessed_messages(limit=limit)
        if not messages:
            logger.info("No new messages to consolidate.")
            return 0

        # 2. Format conversation for LLM
        convo_lines = []
        msg_ids = []
        user_ids_in_batch = []  # Use list to preserve order
        seen_user_ids = set()   # Track seen to avoid duplicates
        for m in messages:
            sender = m.get('sender', {}).get('agent_id', 'unknown')
            content = m.get('payload', {}).get('content', '')
            if isinstance(content, dict):
                content = content.get('content') or json.dumps(content)
            convo_lines.append(f"{sender}: {content}")
            msg_ids.append(m.get('id').split(':')[-1].strip('`'))
            
            payload = m.get('payload', {})
            if isinstance(payload, dict):
                msg_user_id = payload.get('user_id') or payload.get('session_user_id')
                if msg_user_id and msg_user_id not in seen_user_ids:
                    user_ids_in_batch.append(msg_user_id)
                    seen_user_ids.add(msg_user_id)
        
        primary_user_id = user_ids_in_batch[0] if user_ids_in_batch else None

        conversation_text = "\n".join(convo_lines)

        # 3. Call LLM to extract facts
        prompt = self.CONSOLIDATION_PROMPT.format(conversation=conversation_text)
        try:
            response = await self.llm.get_completion([{"role": "system", "content": prompt}], stream=False)
            
            # Clean response if it contains markdown code blocks
            clean_json = response.strip() # type: ignore
            if clean_json.startswith("```json"):
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif clean_json.startswith("```"):
                clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
            facts = json.loads(clean_json)
            logger.info(f"Extracted {len(facts)} facts from {len(messages)} messages.")

            # 4. Store facts and mark messages as processed
            for fact_data in facts:
                # Add source metadata
                fact_data['source_ids'] = msg_ids
                # If subject is user, default belief to 'system' (Universal)
                if fact_data.get('subject') == 'user' and not fact_data.get('agent'):
                    fact_data['agent'] = 'system'
                
                # STORY 6.2: Associate user_id with the fact
                if primary_user_id:
                    fact_data['user_id'] = primary_user_id
                
                # Generate embedding for the fact
                embedding = await self.llm.get_embedding(fact_data['fact'])
                fact_data['embedding'] = embedding
                
                # STORY 13.4: Conflict Check
                conflicts = await self.surreal.semantic_search(embedding, limit=1)
                if conflicts and conflicts[0].get('score', 0) > 0.85:
                    old_fact = conflicts[0]
                    resolution = await self.resolver.resolve(old_fact['content'], fact_data['fact'])
                    if resolution.get('is_conflict'):
                        logger.info(f"CONFLICT detected: {old_fact['content']} vs {fact_data['fact']}. Action: {resolution['action']}")
                        await self.surreal.merge_or_override_fact(old_fact['id'], fact_data, resolution)
                        continue # Fact handled by resolver
                
                await self.surreal.insert_graph_memory(fact_data)

            # Mark all messages in this batch as processed
            await self.surreal.mark_as_processed(msg_ids)

            # 5. Notify system
            summary = f"Sleep Cycle complete: {len(facts)} new facts learned from {len(messages)} messages."
            await self._broadcast_log(summary)
            
            return len(facts)

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
        await self._broadcast_log(f"Memory decay applied (rate={decay_rate}). {removed_count} memories faded.")

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
            payload=Payload(content=f"[{level.upper()}] {content}")
        )
        await self.redis.publish("broadcast", msg)