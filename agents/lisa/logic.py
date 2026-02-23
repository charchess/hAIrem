import logging
from src.domain.agent import BaseAgent
from src.skills.home_assistant import get_state

logger = logging.getLogger(__name__)


class Agent(BaseAgent):
    def setup(self):
        super().setup()

    async def get_fridge_status(self) -> str:
        ha = getattr(self, "ha_client", None)
        temp = await get_state("sensor.fridge_temperature", ha_client=ha)
        door = await get_state("binary_sensor.fridge_door", ha_client=ha)
        return f"Frigo — Température: {temp} | Porte: {door}"

    async def get_house_status(self) -> str:
        ha = getattr(self, "ha_client", None)
        lights = await get_state("light.all_lights", ha_client=ha)
        temp = await get_state("sensor.living_room_temperature", ha_client=ha)
        return f"Maison — Lumières: {lights} | Température: {temp}"

    async def add_reminder(self, memo: str) -> str:
        if not hasattr(self, "_reminders"):
            self._reminders = []
        self._reminders.append(memo)
        return f"Rappel enregistré: {memo}"
