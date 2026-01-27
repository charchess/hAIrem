import random
import logging
from src.domain.agent import BaseAgent
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

logger = logging.getLogger(__name__)

class Agent(BaseAgent):
    """
    The 'Dieu' Agent. 
    It doesn't talk to the user directly but whispers to other agents.
    """
    
    async def on_message(self, message: HLinkMessage):
        # 1. Listen for inactivity signals from H-Core
        if message.type == "system.inactivity":
            logger.info("Dieu detected inactivity. Preparing a whisper...")
            await self._trigger_spark()
            return # Don't process further
        
        # 2. Dieu does NOT respond to regular narrative text from users
        if message.type == MessageType.NARRATIVE_TEXT and message.sender.agent_id == "user":
            # Just store in history but don't call LLM
            self.ctx.history.append(message)
            return

        # Call base for standard processing (internal notes, status updates, etc)
        await super().on_message(message)

    async def _trigger_spark(self):
        """Select a random agent and whisper a thought."""
        targets = ["Renarde", "Expert-Domotique"]
        target = random.choice(targets)
        
        # Construct a whisper
        whisper_text = (
            "Le silence dure depuis trop longtemps. "
            "Relance la conversation de manière naturelle. "
            "Tu peux peut-être demander des nouvelles ou partager une pensée liée à tes souvenirs."
        )
        
        logger.info(f"Dieu is whispering to {target}...")
        
        whisper_msg = HLinkMessage(
            type="system.whisper",
            sender=Sender(agent_id=self.config.name, role=self.config.role),
            recipient=Recipient(target=target),
            payload=Payload(content=whisper_text)
        )
        
        # Publish to the specific agent's channel
        await self.redis.publish(f"agent:{target}", whisper_msg)
