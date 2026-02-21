import random
import logging
from src.domain.agent import BaseAgent
from src.models.hlink import HLinkMessage, MessageType, Sender, Recipient, Payload

logger = logging.getLogger(__name__)

WHISPER_PROMPTS = [
    "Le silence dure depuis trop longtemps. Relance la conversation naturellement.",
    "Partage une pensée liée à tes derniers souvenirs avec l'utilisateur.",
    "Propose quelque chose de nouveau ou d'inattendu pour briser la routine.",
    "Demande des nouvelles de l'utilisateur d'une façon qui te ressemble.",
    "Murmure un fait intéressant ou une observation sur l'ambiance actuelle.",
]


class Agent(BaseAgent):
    def setup(self):
        super().setup()
        from src.services.spatial.world_state import WorldStateService

        self.world_state = WorldStateService(self.surreal, self.redis)

    async def change_world_theme(self, theme_name: str) -> str:
        await self.world_state.set_theme(theme_name)
        return f"Thème du monde changé en '{theme_name}'."

    async def on_message(self, message: HLinkMessage):
        if message.type == MessageType.SYSTEM_INACTIVITY:
            logger.info("Dieu: inactivity detected, preparing whisper.")
            await self._trigger_spark()
            return

        if message.type == MessageType.NARRATIVE_TEXT and message.sender.agent_id == "user":
            self.ctx.history.append(message)
            return

        await super().on_message(message)

    async def _trigger_spark(self):
        targets = ["Renarde", "lisa"]
        if self.registry:
            active = [aid for aid, a in self.registry.agents.items() if a.is_active and aid != self.config.name]
            if active:
                targets = active

        target = random.choice(targets)
        whisper_text = random.choice(WHISPER_PROMPTS)

        logger.info(f"Dieu: whispering to {target}.")

        whisper_msg = HLinkMessage(
            type=MessageType.SYSTEM_WHISPER,
            sender=Sender(agent_id=self.config.name, role=self.config.role),
            recipient=Recipient(target=target),
            payload=Payload(content=whisper_text),
        )

        await self.redis.publish(f"agent:{target}", whisper_msg)
