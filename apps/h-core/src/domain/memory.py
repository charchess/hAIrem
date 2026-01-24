import asyncio
import logging
import json
from typing import List, Optional
from src.infrastructure.surrealdb import SurrealDbClient
from src.infrastructure.llm import LlmClient
from src.infrastructure.redis import RedisClient
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

logger = logging.getLogger(__name__)

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
        for m in messages:
            sender = m.get('sender', {}).get('agent_id', 'unknown')
            content = m.get('payload', {}).get('content', '')
            if isinstance(content, dict):
                content = content.get('content') or json.dumps(content)
            convo_lines.append(f"{sender}: {content}")
            msg_ids.append(m.get('id').split(':')[-1].strip('`')) # Extract UUID from messages:`uuid`

        conversation_text = "\n".join(convo_lines)

        # 3. Call LLM to extract facts
        prompt = self.CONSOLIDATION_PROMPT.format(conversation=conversation_text)
        try:
            response = await self.llm.get_completion([{"role": "system", "content": prompt}], stream=False)
            
            # Clean response if it contains markdown code blocks
            clean_json = response.strip()
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
                # Generate embedding for the fact
                embedding = await self.llm.get_embedding(fact_data['fact'])
                fact_data['embedding'] = embedding
                
                await self.surreal.insert_memory(fact_data)

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

    async def _broadcast_log(self, content: str, level: str = "info"):
        """Utility to send a system log message."""
        msg = HLinkMessage(
            type=MessageType.SYSTEM_LOG,
            sender=Sender(agent_id="system", role="orchestrator"),
            recipient=Recipient(target="broadcast"),
            payload=Payload(content=f"[{level.upper()}] {content}")
        )
        await self.redis.publish("broadcast", msg)
